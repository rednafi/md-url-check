
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
        print(chunk)

    out, err = capsys.readouterr()
    "Content line 1" in out
    "Content line 2" in out
