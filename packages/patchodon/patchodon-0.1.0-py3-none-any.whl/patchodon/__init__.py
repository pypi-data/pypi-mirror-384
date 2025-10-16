"""Functions and main() for patchodon command."""

__version__ = "0.1.0"

import os
import re
import sys
import time

from pathlib import Path
import argparse
import configparser
import hashlib

import html2text
import requests

DPASTE_URL = "https://dpaste.com"  # TODO any good way to parametrize this?

STATUS_LENGTH_LIMIT = 400  # TODO obtain from instance

html2text.config.IGNORE_ANCHORS = True


def trace(x):
    """
    Helper function for printing out progress
    """
    sys.stderr.write(sys.argv[0] + ": " + x + "\n")


def api_token(args):
    """
    Get the applicable API token out of args
    """
    if args.debug_api_token:
        return args.debug_api_token
    if args.env_api_token:
        return os.environ["PATCHODON_API_TOKEN"]
    if args.config_api_token:
        return args.config_api_token
    raise ValueError("API token not specified")


def auth_headers(args):
    """
    Get a headers structure for `requests` with the Authorization set properly
    """
    if not args.instance_url:
        raise ValueError("mastodon instance not specified")

    token = api_token(args)

    return {"Authorization": f"Bearer {token}"}


def post_visibility(args, is_head):
    """
    choose the status visibility based on args and head-ness
    """
    if args.direct:
        return "direct"
    if args.private:
        return "private"
    if args.unlisted:
        return "unlisted"
    if args.public:
        return "public" if is_head else "unlisted"
    if args.all_public:
        return "public"
    return "public" if is_head else "unlisted"


def do_post_status(args, body, is_head, parent=None, optional=None):
    """
    POST a new status with body, optionally in reply-to `parent` post ID, and
    with attached `optional` contents to body.
    """
    if len(body) > STATUS_LENGTH_LIMIT:
        raise ValueError("required status body too long")

    st = body + (
        "\n" + optional[0 : (STATUS_LENGTH_LIMIT - len(body) - 1)]
        if optional
        else ""
    )
    data = {"status": st, "visibility": post_visibility(args, is_head)}
    # visibility options: public head+unlisted, all unlisted, all private, all direct
    if parent:
        data["in_reply_to_id"] = parent

    r = requests.post(
        args.instance_url + "/api/v1/statuses",
        data=data,
        headers=auth_headers(args),
        timeout=args.timeout,
    )

    if r.status_code != 200:
        raise RuntimeError(f"mastodon status posting failed ({r.status_code})")

    rj = r.json()
    return (rj["id"], rj["url"])


def do_pastebin_file(args):
    """
    Send the `file` to dpaste, returning URL for the raw file.
    """

    def f(file):
        # DPASTE API USE RULES:
        # - user-agent must be set properly
        # - 1 second between requests
        trace(f"sending `{file}' to dpaste...")
        r = requests.post(
            DPASTE_URL + "/api/v2/",
            data={
                "content": Path(file).read_text(),
                "syntax": "diff",
                "title": os.path.basename(file),
                "expiry_days": args.paste_expire_days,
            },
            headers={"User-agent": f"patchodon v{__version__}"},
            timeout=args.timeout,
        )
        time.sleep(1.1)
        if r.status_code != 201:
            raise RuntimeError("dpaste POST failed for `{file}'")
        return r.headers["location"] + ".txt"

    return f


def split_off_diff(s):
    """
    try to split off the diff part out of a git .patch
    """
    return s.split("\ndiff --git ")[0]


def mapl(f, xs):
    """
    helper that listifies the generator out of map
    """
    return list(map(f, xs))


def mayline(s):
    """
    if the argument string is non-empty, make it a line, otherwise return empty
    string
    """
    if s:
        return s + "\n"

    return ""


def do_post(args):
    """
    implementation of the `patchodon post` subcommand
    """
    files = args.patchfile
    if not files:
        trace("reading patchfile series from stdin")
        files = mapl(lambda x: x.rstrip("\n"), sys.stdin.readlines())
    n_patches = len(files)
    hashes = mapl(
        lambda x: hashlib.sha1(Path(x).read_text().encode()).hexdigest(), files
    )
    short_hashes = mapl(lambda x: x[0:8], hashes)
    full_hash = hashlib.sha1(" ".join(hashes).encode()).hexdigest()
    paste_raw_urls = mapl(do_pastebin_file(args), files)
    trace("posting the header...")
    parent_post_id, url = do_post_status(
        args,
        f"{mayline(args.recipient)}{mayline(args.subject)}"
        f"[patchodon: {full_hash} / {' '.join(short_hashes)}]",
        True,
    )
    for fn, pst, hsh, series in zip(
        files, paste_raw_urls, hashes, range(n_patches)
    ):
        trace(f"posting patch {series+1}/{n_patches}...")
        parent_post_id, _ = do_post_status(
            args,
            f"{mayline(args.recipient)}"
            f"[patchodon {series+1}/{n_patches} {hsh}]\n"
            f"{pst}\n",
            False,
            parent=parent_post_id,
            optional=split_off_diff(Path(fn).read_text()),
        )
    print(url)


def find_head_post(args):
    """
    Find a post ID in the configured mastodon instave via the search API
    ("internalizing" it in the process), returning some extra metadata
    """
    r = requests.get(
        args.instance_url + "/api/v2/search",
        headers=auth_headers(args),
        params={"resolve": "true", "limit": "10", "q": args.patch_url},
        timeout=args.timeout,
    )
    if r.status_code != 200:
        raise RuntimeError("status URL search failed!")

    sts = list(
        filter(lambda x: x["url"] == args.patch_url, r.json()["statuses"])
    )

    if len(sts) < 1:
        raise RuntimeError("status URL not found")

    if len(sts) > 1:
        raise RuntimeError("ambiguous status URL")

    st = sts[0]
    return (st["id"], st["account"]["id"], st["content"])


def get_descendant_statuses(args, parent):
    """
    retrieve replies to a given parent status
    """
    r = requests.get(
        args.instance_url + f"/api/v1/statuses/{parent}/context",
        headers=auth_headers(args),
        timeout=args.timeout,
    )
    if r.status_code != 200:
        raise RuntimeError(f"retrieval of context failed for {parent}")
    rj = r.json()
    return rj["descendants"] if "descendants" in rj else []


re_head = re.compile(
    r"^\[patchodon: ([0-9a-f]{40}) /(( +[0-9a-f]{8})+)\]$", re.MULTILINE
)

re_patch = re.compile(
    r"^\[patchodon ([0-9]+)/([0-9]+) ([0-9a-f]{40})\]"
    r" *\n(https://dpaste.com/[a-zA-Z0-9]+\.txt)$",
    re.MULTILINE,
)


def parse_matching_status(args, st, parent, account, n, total_n, short_hash):
    """
    If the status in `st` satisfies the expected conditions, parse out its id
    and text; if not, return None.
    """

    if st["in_reply_to_id"] != parent:
        # Descendants are also transitive, which includes all subsequent
        # patches. Thus we just don't trace anything here to avoid excessive
        # warnings.
        return None
    if st["account"]["id"] != account:
        trace(f"bad account in status {st['id']}")
        return None
    st_content = html2text.html2text(st["content"])
    match = re_patch.search(st_content)
    if not match:
        return None
    gs = match.groups()
    if gs[0] != str(n) or gs[1] != str(total_n):
        trace(f"patch mis-ordered in status {st['id']}")
        return None
    long_hash = gs[2]
    if long_hash[0:8] != short_hash:
        trace(f"patch hash mismatch in status {st['id']}")
        return None
    url = gs[3]
    r = requests.get(
        url,
        timeout=args.timeout,
        headers={"User-agent": f"patchodon v{__version__}"},
    )
    time.sleep(1.1)  # dpaste ToS!
    if r.status_code != 200:
        trace(f"could not get patch from status {st['id']} via {url}")
        return None
    if long_hash != hashlib.sha1(r.text.encode()).hexdigest():
        trace(f"patch hash differs from file in status {st['id']}")
        return None
    return (st["id"], r.text)


def do_get(args):
    """
    implementation of `patchodon get` subcommand
    """
    st_id, st_acct_id, st_content_html = find_head_post(args)
    st_content = html2text.html2text(st_content_html)
    # parse out the hash and subhashes
    match = re_head.search(st_content)
    if not match:
        raise RuntimeError("no patchodon header found")
    full_hash = match.groups()[0]
    short_hashes = list(
        filter(lambda x: len(x) > 0, match.groups()[1].split(" "))
    )
    patches = [None for _ in short_hashes]
    n_patches = len(patches)
    assert n_patches > 0
    parent = st_id
    for i, short_hash in enumerate(short_hashes):
        trace(f"getting patch {i+1} ({short_hash})...")
        sts = get_descendant_statuses(args, parent)
        ok_sts = list(
            filter(
                lambda x: x is not None,
                map(
                    lambda x: parse_matching_status(
                        args,
                        x,
                        parent,
                        st_acct_id,
                        i + 1,
                        n_patches,
                        short_hash,
                    ),
                    sts,
                ),
            )
        )
        if len(ok_sts) == 0:
            raise RuntimeError(
                f"no suitable patches found for {i+1} ({short_hash})"
            )
        if len(ok_sts) > 1:
            raise RuntimeError(
                f"ambiguous statuses for patch {i+1} ({short_hash})"
            )
        ok_st_id, ok_st_patch = ok_sts[0]
        parent = ok_st_id
        patches[i] = ok_st_patch

    # verify the full hash
    hashes = list(map(lambda x: hashlib.sha1(x.encode()).hexdigest(), patches))
    computed_full_hash = hashlib.sha1(" ".join(hashes).encode()).hexdigest()
    if computed_full_hash != full_hash:
        raise RuntimeError("hash checksums do not match!")

    # print out stuff
    if args.out_prefix:
        for i, patch in enumerate(patches):
            path = args.out_prefix + f"{i+1:04d}.patch"
            if not args.overwrite and os.path.exists(path):
                raise RuntimeError(f"refusing to overwrite {path}")
            Path(path).write_text(patch)
    else:
        for patch in patches:
            sys.stdout.write(patch)
            sys.stdout.write("\n")  # be nice


def main():
    """
    parse commandline arguments and run either `do_post` or `do_get`
    """
    ap = argparse.ArgumentParser(
        prog=sys.argv[0],
        epilog="patchodon.py version " + __version__ + " is a free software.",
        description="Publicly send and receive git patch series via Mastodon.",
    )

    group = ap.add_mutually_exclusive_group()
    group.add_argument(
        "--debug-api-token",
        help=(
            "specify the API token on command line (not very secure,"
            " good for debugging only)"
        ),
    )
    group.add_argument(
        "-e",
        "--env-api-token",
        action="store_true",
        help="get the API token from environment PATCHODON_API_TOKEN",
    )

    ap.add_argument(
        "-i",
        "--instance-url",
        help=(
            "mastodon instance URL to use, such as `https://mastodon.example/'"
        ),
    )

    cmds = ap.add_subparsers(required=True, dest="command")

    post = cmds.add_parser("post")
    post.add_argument(
        "-r",
        "--recipient",
        default=None,
        help=(
            "user tag to prepend to all posted statuses (required esp. for"
            " direct sending of statuses)"
        ),
    )
    post.add_argument(
        "-s",
        "--subject",
        default=None,
        help=(
            "opening text of the initial post, ideally used to specify the"
            " target project and patch topic"
        ),
    )
    post.add_argument(
        "-x",
        "--paste-expire-days",
        default=14,
        help="how many days should dpaste.com hold the patches (default: 14)",
    )
    post.add_argument(
        "patchfile",
        nargs="*",
        help=(
            "filenames of the patch series; taken from stdin if none are"
            " specified (useful for piping the output of git-format-patch"
            " into patchodon)"
        ),
    )
    visibility = post.add_mutually_exclusive_group()
    visibility.add_argument(
        "--all-public",
        action="store_true",
        help="post head status and all patches publicly",
    )
    visibility.add_argument(
        "--public",
        action="store_true",
        help=(
            "post head status publicly, patches unlisted (this is the default)"
        ),
    )
    visibility.add_argument(
        "--unlisted",
        action="store_true",
        help=(
            "post all statuses as unlisted"
        ),
    )
    visibility.add_argument(
        "--private",
        action="store_true",
        help=(
            "post statuses as private (visible by followers and recipients only)"
        ),
    )
    visibility.add_argument(
        "--direct",
        action="store_true",
        help="post statuses as direct (visible only by the tagged recipients)",
    )

    get = cmds.add_parser("get")
    get.add_argument(
        "patch_url",
        help=(
            "root URL of the status where the patch was posted (the status"
            " should contain the patch hash)"
        ),
    )
    get.add_argument(
        "-C",
        "--out-prefix",
        help=(
            "instead of writing to stdout (for piping to git-am), write"
            " the numbered patchfiles to files with a given prefix"
            " (specifying `./patchodon-' will produce files like"
            " `./patchodon-0001.patch')"
        ),
    )
    get.add_argument(
        "--overwrite",
        action="store_true",
        help="overwrite existing patch files instead of failing",
    )

    ap.add_argument(
        "-c",
        "--config",
        default=os.environ["HOME"] + "/.patchodon.ini",
        help=(
            "specify a custom config INI file that may specify a section"
            " [patchodon] with keys instance_url and api_token; defaults to"
            " `$HOME/.patchodon.ini', specify `/dev/null' to avoid config"
            " loading"
        ),
    )
    ap.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="timeout for HTTP API requests in seconds (default: 300)",
    )
    args = ap.parse_args()

    if os.path.exists(args.config):
        cp = configparser.ConfigParser()
        cp.read(args.config)
        if "patchodon" in cp:
            if "instance_url" in cp["patchodon"] and args.instance_url is None:
                args.instance_url = cp["patchodon"]["instance_url"]
            if "api_token" in cp["patchodon"]:
                args.config_api_token = cp["patchodon"]["api_token"]
    else:
        trace(f"ignoring non-existent config: {args.config}")

    if args.command == "post":
        do_post(args)
    elif args.command == "get":
        do_get(args)
    else:
        raise ValueError("fatal: args borked")
