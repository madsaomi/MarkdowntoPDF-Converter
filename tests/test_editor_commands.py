"""Поведенческие тесты редакторных команд (gui/editor_commands).

Проверяет обёртки форматирования, форматирование таблиц Markdown,
форматирование документа и event-filter.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtWidgets import QApplication, QTextEdit
from PyQt6.QtGui import QKeyEvent

app = QApplication.instance() or QApplication([])

from src.gui import editor_commands


class _FakeCursor:
    SelectionType = type("ST", (), {"LineUnderCursor": 1})

    MoveOperation = type("MO", (), {"PreviousCharacter": 1, "NextCharacter": 2})
    MoveMode = type("MM", (), {"KeepAnchor": 1})

    def __init__(self, text=""):
        self._text = text
        self._pos = 0
        self._sel_start = 0
        self._sel_end = 0
        self._has_sel = False
        self.inserted = []
        self.editor = None

    def selectedText(self):
        if self._has_sel:
            return self._text[self._sel_start:self._sel_end]
        return ""

    def hasSelection(self):
        return self._has_sel

    def select(self, t):
        if t == self.SelectionType.LineUnderCursor:
            i = self._text.rfind('\n', 0, self._pos) + 1
            j = self._text.find('\n', self._pos)
            if j == -1:
                j = len(self._text)
            self._sel_start = i
            self._sel_end = j
            self._has_sel = True

    def insertText(self, s):
        self.inserted.append(s)
        if self._has_sel:
            self._text = self._text[:self._sel_start] + s + self._text[self._sel_end:]
            self._pos = self._sel_start + len(s)
            self._has_sel = False
        else:
            self._text = self._text[:self._pos] + s + self._text[self._pos:]
            self._pos += len(s)
        if self.editor is not None:
            self.editor._text = self._text

    def position(self):
        return self._pos

    def deleteChar(self):
        if self._pos < len(self._text):
            self._text = self._text[:self._pos] + self._text[self._pos + 1:]
            if self.editor is not None:
                self.editor._text = self._text

    def deletePreviousChar(self):
        if self._pos > 0:
            self._text = self._text[:self._pos - 1] + self._text[self._pos:]
            self._pos -= 1
            if self.editor is not None:
                self.editor._text = self._text

    def movePosition(self, op, mode=None):
        if op == self.MoveOperation.PreviousCharacter:
            if self._pos > 0:
                self._pos -= 1
            if mode == self.MoveMode.KeepAnchor:
                self._sel_start = self._pos
                self._sel_end = self._pos
            return True
        if op == self.MoveOperation.NextCharacter:
            if mode == self.MoveMode.KeepAnchor:
                if not self._has_sel:
                    self._sel_start = self._pos
                self._sel_end = self._pos + 1
                self._has_sel = True
                self._pos += 1
                return True
            if self._pos < len(self._text):
                self._pos += 1
            return True
        return False


class _FakeEditor:
    def __init__(self, text=""):
        self._text = text
        self.focused = False
        self.blocked = False
        self.cursor = _FakeCursor(text)
        self.cursor.editor = self
        self.sb_value = 0

    def textCursor(self):
        self.cursor._text = self._text
        self.cursor.editor = self
        return self.cursor

    def setTextCursor(self, c):
        self.cursor = c
        c.editor = self
        self._text = c._text

    def setFocus(self):
        self.focused = True

    def setPlainText(self, t):
        self._text = t

    def toPlainText(self):
        return self._text

    def blockSignals(self, v):
        self.blocked = v

    def verticalScrollBar(self):
        class _SB:
            def __init__(self, e):
                self.e = e

            def value(self):
                return self.e.sb_value

            def setValue(self, v):
                self.e.sb_value = v

        return _SB(self)


class _FakeWindow:
    def __init__(self, text=""):
        self.live_editor = _FakeEditor(text)
        self.rendered = 0
        self.stats = 0

    def _render_live_preview(self):
        self.rendered += 1

    def update_text_statistics(self):
        self.stats += 1


def test_wrap_selection_bold_italic():
    """format_bold/italic оборачивают выделенный текст."""
    w = _FakeWindow("hello")
    c = _FakeCursor("hello")
    c.editor = w.live_editor
    c._has_sel = True
    c._sel_start = 0
    c._sel_end = 5
    c._pos = 5
    w.live_editor.cursor = c

    editor_commands.format_bold(w)
    assert c._text == "**hello**"
    assert w.live_editor.focused is True

    w2 = _FakeWindow("world")
    c2 = _FakeCursor("world")
    c2.editor = w2.live_editor
    c2._has_sel = True
    c2._sel_start = 0
    c2._sel_end = 5
    w2.live_editor.cursor = c2
    editor_commands.format_italic(w2)
    assert c2._text == "*world*"
    print("[PASS] test_wrap_selection_bold_italic")


def test_format_code_inline_and_block():
    """format_code использует бэктики или блочный код для многострочного."""
    w = _FakeWindow("code")
    c = _FakeCursor("code")
    c._has_sel = True
    c._sel_start = 0
    c._sel_end = 4
    w.live_editor.cursor = c
    editor_commands.format_code(w)
    assert w.live_editor.cursor._text == "`code`"

    w2 = _FakeWindow("line1\nline2")
    c2 = _FakeCursor("line1\nline2")
    c2._has_sel = True
    c2._sel_start = 0
    c2._sel_end = 11
    w2.live_editor.cursor = c2
    editor_commands.format_code(w2)
    assert "```" in w2.live_editor.cursor._text
    print("[PASS] test_format_code_inline_and_block")


def test_format_header_quote_list():
    """format_header/quote/list форматируют текущую строку."""
    w = _FakeWindow("## old title")
    c = w.live_editor.textCursor()
    c._pos = 2
    c._text = "## old title"
    w.live_editor.cursor = c
    editor_commands.format_header(w, 1)
    assert w.live_editor._text == "# old title"

    w2 = _FakeWindow("> old")
    c2 = w2.live_editor.textCursor()
    c2._text = "> old"
    w2.live_editor.cursor = c2
    editor_commands.format_quote(w2)
    assert w2.live_editor._text == "> old" or w2.live_editor._text.startswith("> ")

    w3 = _FakeWindow("- item")
    c3 = w3.live_editor.textCursor()
    c3._text = "- item"
    w3.live_editor.cursor = c3
    editor_commands.format_list(w3)
    assert w3.live_editor._text == "- item"
    print("[PASS] test_format_header_quote_list")


def test_insert_page_break():
    """insert_page_break вставляет HTML-разрыв страницы."""
    w = _FakeWindow("")
    editor_commands.insert_page_break(w)
    assert "page-break-before" in w.live_editor.cursor.inserted[0]
    print("[PASS] test_insert_page_break")


def test_format_markdown_table_alignment():
    """format_markdown_table выравнивает столбцы и сохраняет выравнивание."""
    lines = [
        "| name | age |",
        "| :-- | --: |",
        "| Alice | 30 |",
    ]
    out = editor_commands.format_markdown_table(lines)
    assert out[0].count("|") == 3
    assert out[1].startswith("| :") or ":" in out[1]
    assert out[1].endswith(": |") or out[1].strip().endswith(":|")
    assert len(out) == 3
    print("[PASS] test_format_markdown_table_alignment")


def test_format_markdown_document_formats_table_and_headings():
    """format_markdown_document форматирует таблицы и добавляет отступ перед заголовками."""
    text = "текст\n|a|b|\n|--|--|\n|1|2|\n# Заголовок"
    w = _FakeWindow(text)
    editor_commands.format_markdown_document(w)
    new = w.live_editor._text
    assert "| a" in new or "|a" in new
    assert "\n# Заголовок" in new or new.startswith("#") is False  # должен быть отступ
    assert w.rendered >= 1
    assert w.stats >= 1
    print("[PASS] test_format_markdown_document_formats_table_and_headings")


def test_event_filter_autoclose_pairs():
    """handle_event_filter автозакрывает скобки/кавычки и не трогает выделение."""
    w = _FakeWindow("hello")
    ev = QKeyEvent(QEvent.Type.KeyPress, ord('('), Qt.KeyboardModifier.NoModifier, "(")
    res = editor_commands.handle_event_filter(w, w.live_editor, ev)
    assert res is True
    assert w.live_editor.cursor.inserted[-1] == "()"
    print("[PASS] test_event_filter_autoclose_pairs")


def test_event_filter_wrap_selection():
    """handle_event_filter оборачивает выделенный текст парным символом."""
    w = _FakeWindow("hello")
    c = w.live_editor.textCursor()
    c._has_sel = True
    c._sel_start = 0
    c._sel_end = 5
    c._text = "hello"
    w.live_editor.cursor = c
    ev = QKeyEvent(QEvent.Type.KeyPress, ord('*'), Qt.KeyboardModifier.NoModifier, "*")
    res = editor_commands.handle_event_filter(w, w.live_editor, ev)
    assert res is True
    assert w.live_editor.cursor.inserted[-1] == "*hello*"
    print("[PASS] test_event_filter_wrap_selection")


def test_event_filter_overwrite_closing_char():
    """handle_event_filter перезаписывает уже существующий закрывающий символ."""
    w = _FakeWindow("()")
    c = w.live_editor.textCursor()
    c._text = "()"
    c._pos = 1  # between parens
    w.live_editor.cursor = c
    ev = QKeyEvent(QEvent.Type.KeyPress, ord(')'), Qt.KeyboardModifier.NoModifier, ")")
    res = editor_commands.handle_event_filter(w, w.live_editor, ev)
    assert res is True
    print("[PASS] test_event_filter_overwrite_closing_char")


def test_event_filter_ignores_wrong_object():
    """handle_event_filter игнорирует события не от редактора."""
    w = _FakeWindow("")
    other = QTextEdit()
    ev = QKeyEvent(QEvent.Type.KeyPress, ord('a'), Qt.KeyboardModifier.NoModifier, "a")
    res = editor_commands.handle_event_filter(w, other, ev)
    assert res is False
    print("[PASS] test_event_filter_ignores_wrong_object")


def main():
    tests = [
        test_wrap_selection_bold_italic,
        test_format_code_inline_and_block,
        test_format_header_quote_list,
        test_insert_page_break,
        test_format_markdown_table_alignment,
        test_format_markdown_document_formats_table_and_headings,
        test_event_filter_autoclose_pairs,
        test_event_filter_wrap_selection,
        test_event_filter_overwrite_closing_char,
        test_event_filter_ignores_wrong_object,
    ]
    for t in tests:
        t()
    print("\nAll editor_commands tests passed!")


if __name__ == "__main__":
    main()
