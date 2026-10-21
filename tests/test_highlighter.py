"""Поведенческие тесты синтаксического хайлайтера Markdown (gui/highlighter).

Проверяет инициализацию, переключение светлой/тёмной темы, перегенерацию правил
и работу highlightBlock без падений.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QTextEdit

app = QApplication.instance() or QApplication([])

from src.gui.highlighter import MarkdownHighlighter, _compile_regex


def test_compile_regex_cached():
    """_compile_regex кэшируется и возвращает QRegularExpression."""
    from PyQt6.QtCore import QRegularExpression

    r1 = _compile_regex(r"^#.*$")
    r2 = _compile_regex(r"^#.*$")
    assert isinstance(r1, QRegularExpression)
    assert r1 is r2, "должен использоваться lru_cache"
    print("[PASS] test_compile_regex_cached")


def test_highlighter_initial_state():
    """MarkdownHighlighter создаётся с правилами и is_dark=False."""
    h = MarkdownHighlighter()
    assert h.is_dark is False
    assert isinstance(h.rules, list)
    assert len(h.rules) == 15
    for expr, fmt in h.rules:
        assert fmt is not None
    print("[PASS] test_highlighter_initial_state")


def test_set_theme_switches_and_rehighlights():
    """set_theme переключает тему, перегенерирует правила и вызывает rehighlight."""
    h = MarkdownHighlighter()
    calls = []
    h.rehighlight = lambda: calls.append("rehighlight")
    h.set_theme(True)
    assert h.is_dark is True
    assert len(h.rules) == 15
    assert calls == ["rehighlight"]
    h.set_theme(False)
    assert h.is_dark is False
    print("[PASS] test_set_theme_switches_and_rehighlights")


def test_highlight_block_runs_without_errors():
    """highlightBlock обрабатывает различные Markdown-блоки без исключений."""
    edit = QTextEdit()
    h = MarkdownHighlighter(edit)
    samples = [
        "# Заголовок",
        "## Подзаголовок",
        "**жирный** и __жирный__",
        "*курсив* и _курсив_",
        "> цитата",
        "- пункт списка",
        "* пункт",
        "+ пункт",
        "1. нумерованный",
        "[ссылка](http://example.com)",
        "![картинка](img.png)",
        "`код`",
        "```python",
        "```mermaid",
        "$x+y$",
        "$$E=mc^2$$",
        "текст без форматирования",
        "",
    ]
    for s in samples:
        h.highlightBlock(s)
    print("[PASS] test_highlight_block_runs_without_errors")


def test_highlight_block_with_dark_theme():
    """Тёмная тема также работает на всех образцах."""
    edit = QTextEdit()
    h = MarkdownHighlighter(edit)
    h.set_theme(True)
    for s in ["# Title", "**bold**", "`code`", "> quote", "- item"]:
        h.highlightBlock(s)
    print("[PASS] test_highlight_block_with_dark_theme")


def main():
    tests = [
        test_compile_regex_cached,
        test_highlighter_initial_state,
        test_set_theme_switches_and_rehighlights,
        test_highlight_block_runs_without_errors,
        test_highlight_block_with_dark_theme,
    ]
    for t in tests:
        t()
    print("\nAll highlighter tests passed!")


if __name__ == "__main__":
    main()
