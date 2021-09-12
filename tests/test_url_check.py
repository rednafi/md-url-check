from http import HTTPStatus
from unittest.mock import create_autospec, patch

import md_url_check.__main__ as url_check


def test_color(capsys):
    color = url_check.Color

    s = f"{color.YELLOW}hello{color.RESET}"

    print(s)
    out, err = capsys.readouterr()

    assert err == ""
    assert "\x1b[93mhello\x1b[0m\n" in out


def test_read_chunk(tmp_path, capsys):
    d = tmp_path / "dest"
    d.mkdir()
    p = d / "file.md"

    md_content = """
    Content line 1
    Conetent line 2
    Content line 3
    Content line 4
    """

    p.write_text(md_content)

    chunks = url_check._read_chunk(file_path=str(p), line_count=2)

    for chunk in chunks:
        assert len(chunk.strip().split("\n")) == 1 or 2
        print(chunk)

    out, err = capsys.readouterr()

    assert err == ""
    assert "Content line 1" in out
    assert "Conetent line 2" in out


def test_find_links_from_chunk():
    chunk = """
    [hello](https://hello-world.com)
    This is an [inline](http://inline.com) URL.
    """

    links = url_check._find_links_from_chunk(chunk=chunk)

    assert links == [
        ("hello", "https://hello-world.com"),
        ("inline", "http://inline.com"),
    ]


def test_find_links_from_markdown(tmp_path, markdown_text):
    d = tmp_path / "dest"
    d.mkdir()
    p = d / "file.md"

    p.write_text(markdown_text)

    links = url_check._find_links_from_markdown(markdown_path=str(p))
    assert links == [
        "https://arxiv.org/pdf/1901.01973.pdf",
        "https://www.guru99.com/database-normalization.html",
        "https://www.guru99.com/oltp-vs-olap.html",
        "https://www.postgresql.org/docs/13/tutorial-transactions.html",
        "https://devcenter.heroku.com/articles/postgresql-concurrency",
    ]


def test_make_request():
    # Lame mock function.
    mock_make_request = create_autospec(url_check._make_request, return_value=200)
    status_code = mock_make_request(url="https://httpbin.org/get")
    assert status_code == HTTPStatus.OK


def test_log_request(capsys):
    # Mocking the internally called _make_request function.
    with patch("md_url_check.__main__._make_request", lambda url: 200):
        url_check._log_request(url="https://httpbin.org/get")

    out, err = capsys.readouterr()
    assert err == ""
    assert (
        """\n\x1b[1m\x1b[95mURL\x1b[0m: \x1b[92mhttps://httpbin.org/get\x1b[0m\n\x1b[1m\x1b[93m"""
        in out
    )
    assert "Status Code\x1b[0m:  \x1b[94m200\x1b[0m ✅\n\x1b[1m\x1b[96m" in out
    assert "Status Description\x1b[0m: Request fulfilled, document follows\n\n" in out


def test_verify_links(tmp_path, capsys, markdown_text):
    d = tmp_path / "dest"
    d.mkdir()
    p = d / "file.md"
    p.write_text(markdown_text)

    with patch("md_url_check.__main__._make_request", lambda url: 200):
        url_check.verify_links(markdown_path=str(p), thread_count=16, suppress=False)
    out, err = capsys.readouterr()

    assert err == ""
    assert "\x1b[92mAll checks succeeded\x1b[0m 🎉\n" in out
