from __future__ import annotations

import argparse
import concurrent.futures as confu
import itertools
import re
import socket
import sys
import urllib.request
from collections.abc import Generator
from enum import Enum
from http import HTTPStatus
from typing import NoReturn


class Color(str, Enum):
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


INLINE_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
FOOTNOTE_LINK_TEXT_RE = re.compile(r"\[([^\]]+)\]\[(\d+)\]")
FOOTNOTE_LINK_URL_RE = re.compile(r"\[(\d+)\]:\s+(\S+)")

HTTP_STATUS_TO_DESCRIPTION = {v.value: v.description for v in HTTPStatus}

# Set default timeout.
socket.setdefaulttimeout(10)


def _read_chunk(
    *,
    file_path: str,
    line_count: int = 100,  # Number of chunked line.
) -> Generator[str, None, None]:

    with open(file_path, "r") as f:
        while True:
            next_chunk = list(itertools.islice(f, line_count))
            yield "\n".join(next_chunk)
            if not next_chunk:
                break


def _find_links_from_chunk(*, chunk: str) -> list[tuple[str, str]]:
    """Return list of links in markdown."""

    links = list(INLINE_LINK_RE.findall(chunk))
    footnote_links = dict(FOOTNOTE_LINK_TEXT_RE.findall(chunk))
    footnote_urls = dict(FOOTNOTE_LINK_URL_RE.findall(chunk))

    for key, val in footnote_links.items():
        links.append((footnote_links[key], footnote_urls[val]))

    return links


def _find_links_from_markdown(*, markdown_path: str) -> list[str]:
    links = []
    for chunk in _read_chunk(file_path=markdown_path):
        ll = _find_links_from_chunk(chunk=chunk)

        for elem in ll:
            if elem[1].startswith("http"):
                links.append(elem[1])
    return links


def _make_request(*, url: str) -> int | NoReturn:
    user_agent = "Mozilla/5.0 (Linux; x64)"
    headers = {"User-Agent": user_agent}
    req = urllib.request.Request(url, headers=headers)
    try:
        res = urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        return e.code

    return res.code


def _log_request(*, url: str) -> int | NoReturn:
    status_code = _make_request(url=url)

    # Stylize.

    # URL.
    url_title_fancy = f"{Color.BOLD}{Color.PURPLE}URL{Color.RESET}: "
    url_fancy = f"{Color.GREEN}{url}{Color.RESET}"

    # Status Code.
    status_title_fancy = f"{Color.BOLD}{Color.YELLOW}Status Code{Color.RESET}: "
    status_code_fancy = f"{Color.BLUE}{status_code}{Color.RESET}"
    status_fancy = (
        f" {status_code_fancy} ✅"
        if status_code == HTTPStatus.OK
        else f"{status_code_fancy} ❌"
    )

    # Status Description.
    status_description_title_fancy = (
        f"{Color.BOLD}{Color.CYAN}Status Description{Color.RESET}: "
    )

    row_fancy = (
        "\n"
        f"{url_title_fancy}{url_fancy}\n"
        f"{status_title_fancy}{status_fancy}\n"
        f"{status_description_title_fancy}{HTTP_STATUS_TO_DESCRIPTION[status_code]}"
        "\n"
    )
    print(row_fancy)

    if status_code >= HTTPStatus.BAD_REQUEST:
        raise Exception(
            f"url '{url_fancy}' is unreachable, returned {status_code_fancy} 😞. "
        )


def verify_links(*, markdown_path: str) -> None:
    links = _find_links_from_markdown(markdown_path=markdown_path)

    with confu.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(_log_request, url=link) for link in links]

        for future in futures:
            if exc := future.exception():
                raise exc

    print(f"{Color.GREEN}All checks succeeded{Color.RESET} 🎉")


def cli(argv: list[str] | None = None) -> None:

    parser = argparse.ArgumentParser(
        add_help=False,
        usage=f"""
    [-h] -f FILE_PATH

    {Color.GREEN}Examples{Color.RESET}
    {Color.YELLOW}========={Color.RESET}

    {Color.GREEN}Check URLs in a Single File{Color.RESET}
    {Color.BLUE}---------------------------{Color.RESET}
    md-url-check -f file.md

    {Color.GREEN}Check URLs in Multiple Files{Color.RESET}
    {Color.BLUE}----------------------------{Color.RESET}
    echo 'file1.md file2.md' | xargs -n 1 md-url-check -f

    {Color.GREEN}Check URLs in Multiple Files in a Folder{Color.RESET}
    {Color.BLUE}----------------------------------------{Color.RESET}
    find . -name '*.md' | xargs -n 1 --no-run-if-empty md-url-check -f
    """,
    )

    # Add arguments.
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="show this help message and exit",
    )
    required = parser.add_argument_group("required arguments")

    required.add_argument(
        "-f",
        "--file_path",
        required=True,
        help="markdown file path",
    )

    print(
        f"{Color.BOLD}{Color.PURPLE}\nSimple CLI tool to check URL health in markdown files\n{Color.RESET}"
    )

    if not argv:
        parser.parse_args(args=None if sys.argv[1:] else ["--help"])
        args = parser.parse_args()
    else:
        args = parser.parse_args(argv)

    args = parser.parse_args()
    verify_links(markdown_path=args.file_path)


if __name__ == "__main__":
    cli()
