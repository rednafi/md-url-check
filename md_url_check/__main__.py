from __future__ import annotations

import argparse
import concurrent.futures as confu
import itertools
import socket
import subprocess
import sys
from collections.abc import Generator
from enum import Enum
from http import HTTPStatus
from typing import NoReturn

import regex as re


class Color(str, Enum):
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


# NOTE: https://stackoverflow.com/a/67942420/8963300
INLINE_LINK_RE = re.compile(r"\[([^][]+)\](\(((?:[^()]+|(?2))+)\))")

# NOTE: https://stackoverflow.com/a/30738268/8963300
FOOTNOTE_URL_TEXT_RE = re.compile(r"\[([^\]]+)\]\[(\d+)\]")
FOOTNOTE_URL_RE = re.compile(r"\[(\d+)\]:\s+(\S+)")

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

    links = [(i[0], i[2]) for i in INLINE_LINK_RE.findall(chunk)]
    footnote_url_texts = dict(FOOTNOTE_URL_TEXT_RE.findall(chunk))
    footnote_urls = dict(FOOTNOTE_URL_RE.findall(chunk))

    for k, v in footnote_url_texts.items():
        links.append((k, footnote_urls[v]))

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

    process = subprocess.run(
        f'curl -s -o /dev/null --head -A "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36" -w "%{{http_code}}" -X GET "{url}"',
        shell=True,
        capture_output=True,
    )

    status_code = int(process.stdout)

    if status_code in HTTP_STATUS_TO_DESCRIPTION:
        return status_code
    else:
        return HTTPStatus.INTERNAL_SERVER_ERROR


def _log_request(*, url: str, suppress: bool = False) -> int | NoReturn:
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
        if status_code < HTTPStatus.BAD_REQUEST
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

    if not suppress:
        print(row_fancy)

    if status_code >= HTTPStatus.BAD_REQUEST:
        raise Exception(
            f"url '{url_fancy}' is unreachable, returned {status_code_fancy} 😞. "
        )


def verify_links(
    *,
    markdown_path: str,
    thread_count: int = 8,
    suppress: bool = False,
) -> None:
    links = _find_links_from_markdown(markdown_path=markdown_path)

    print(f"{Color.CYAN}Checking URL health...{Color.RESET}\n")

    with confu.ThreadPoolExecutor(max_workers=thread_count) as executor:
        futures = [
            executor.submit(
                _log_request,
                url=link,
                suppress=suppress,
            )
            for link in links
        ]

        for future in futures:
            if exc := future.exception():
                raise exc

    print(f"{Color.GREEN}All checks succeeded{Color.RESET} 🎉")


def cli(argv: list[str] | None = None) -> None:

    parser = argparse.ArgumentParser(
        add_help=False,
        usage=f"""

    md-url-check [-h] -f FILE_PATH [-t THREAD_COUNT] [-s]

    {Color.GREEN}Examples{Color.RESET}
    {Color.YELLOW}========={Color.RESET}

    {Color.GREEN}Check URLs in a Single File{Color.RESET}
    {Color.BLUE}---------------------------{Color.RESET}
    md-url-check -f file.md -t 4

    {Color.GREEN}Check URLs in Multiple Files{Color.RESET}
    {Color.BLUE}----------------------------{Color.RESET}
    echo 'file1.md file2.md' | xargs -n 1 md-url-check -f -t 32 -s

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
    parser.add_argument(
        "-t",
        "--thread_count",
        default=8,
        required=False,
        help="number of os threads to be used while making the requests",
    )
    parser.add_argument(
        "-s",
        "--suppress_output",
        action="store_true",
        required=False,
        help="suppress intermediate outputs",
    )

    if not argv:
        parser.parse_args(args=None if sys.argv[1:] else ["--help"])
        args = parser.parse_args()
    else:
        args = parser.parse_args(argv)

    args = parser.parse_args()

    # Header.
    print(
        f"{Color.BOLD}{Color.PURPLE}\n=== Markdown File: {args.file_path.split('/')[-1]}  ===\n{Color.RESET}"
    )

    verify_links(
        markdown_path=args.file_path,
        thread_count=int(args.thread_count),
        suppress=args.suppress_output,
    )


if __name__ == "__main__":
    cli()
