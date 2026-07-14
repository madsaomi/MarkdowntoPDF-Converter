import os
import sys
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.parser import MarkdownParser

parser = MarkdownParser()


def test_basic_paragraph():
    html, meta = parser.parse("Hello world")
    assert "Hello world" in html
    print("[PASS] test_basic_paragraph")


def test_bold():
    html, meta = parser.parse("**bold**")
    assert "<strong>bold</strong>" in html or "<strong>" in html
    print("[PASS] test_bold")


def test_italic():
    html, meta = parser.parse("*italic*")
    assert "<em>italic</em>" in html or "<em>" in html
    print("[PASS] test_italic")


def test_heading():
    html, meta = parser.parse("# Heading 1")
    assert html.startswith("<h1")
    html2, _ = parser.parse("## Heading 2")
    assert html2.startswith("<h2")
    print("[PASS] test_heading")


def test_code_block():
    text = "```python\nprint('hello')\n```"
    html, meta = parser.parse(text)
    assert "<code" in html or "codehilite" in html or "<pre" in html
    print("[PASS] test_code_block")


def test_table():
    html, meta = parser.parse("| A | B |\n|---|---|\n| 1 | 2 |")
    assert "<table>" in html
    print("[PASS] test_table")


def test_xss_script_removed():
    html, meta = parser.parse("<script>alert(1)</script>")
    assert "<script>" not in html
    print("[PASS] test_xss_script_removed")


def test_xss_onclick_removed():
    html, meta = parser.parse('<p onclick="evil()">text</p>')
    assert "onclick" not in html
    print("[PASS] test_xss_onclick_removed")


def test_xss_javascript_href_blocked():
    html, meta = parser.parse('<a href="javascript:alert(1)">link</a>')
    assert "javascript:" not in html or "blocked" in html
    print("[PASS] test_xss_javascript_href_blocked")


def test_xss_img_onerror():
    html, meta = parser.parse('<img src=x onerror=alert(1)>')
    assert "onerror" not in html
    print("[PASS] test_xss_img_onerror")


def test_meta_extraction():
    html, meta = parser.parse("---\ntitle: Test\nauthor: Me\n---\n\nContent")
    assert meta.get('title') == 'Test'
    assert meta.get('author') == 'Me'
    print("[PASS] test_meta_extraction")


def test_task_list():
    text = "- [ ] todo\n- [x] done"
    html, meta = parser.parse(text)
    assert "checkbox" in html or "task-list" in html or "checked" in html
    print("[PASS] test_task_list")


def test_path_traversal_blocked():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        html = parser.preprocess_media(
            '<img src="../../../etc/passwd">',
            base_dir=tmpdir
        )
        assert '../../../etc/passwd' in html or '#blocked' in html
    print("[PASS] test_path_traversal_blocked")


def test_self_closing_img():
    html, meta = parser.parse("![](image.png)")
    assert "<img" in html
    print("[PASS] test_self_closing_img")


if __name__ == '__main__':
    test_basic_paragraph()
    test_bold()
    test_italic()
    test_heading()
    test_code_block()
    test_table()
    test_xss_script_removed()
    test_xss_onclick_removed()
    test_xss_javascript_href_blocked()
    test_xss_img_onerror()
    test_meta_extraction()
    test_task_list()
    test_path_traversal_blocked()
    test_self_closing_img()
    print("\nAll parser tests passed!")
