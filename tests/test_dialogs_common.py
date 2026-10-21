"""Поведенческие тесты общих диалогов (gui/dialogs/common).

Покрывает ``ColorButton`` (цвет, стиль, диалог выбора) и ``ShortcutsDialog``
(список горячих клавиш, заголовок, локализация).
"""
import os
import sys
import types

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication

app = QApplication.instance() or QApplication([])

import src.gui.dialogs.common as c
from src.gui.dialogs.common import ColorButton, ShortcutsDialog


def test_color_button_initial_color():
    """ColorButton создаётся с заданным цветом и применяет стиль."""
    b = ColorButton("#ff8800")
    assert b.color.name() == "#ff8800", b.color.name()
    style = b.styleSheet()
    assert "#ff8800" in style.lower(), style
    assert "border-radius" in style
    b.deleteLater()
    print("[PASS] test_color_button_initial_color")


def test_color_button_update_style_reflects_color():
    """update_style отражает текущий цвет в таблице стилей."""
    b = ColorButton("#000000")
    b.color = b.color.__class__("#00ff00")
    b.update_style()
    assert "#00ff00" in b.styleSheet().lower()
    b.deleteLater()
    print("[PASS] test_color_button_update_style_reflects_color")


def test_color_button_choose_color_applies_selection():
    """choose_color применяет выбранный в диалоге цвет."""
    b = ColorButton("#123456")
    orig = c.QColorDialog

    class _FakeDialog:
        DialogCode = type("DC", (), {"Accepted": 1, "Rejected": 0})

        def __init__(self, color, parent=None):
            self._color = color

        def exec(self):
            return self.DialogCode.Accepted

        def selectedColor(self):
            return self._color.__class__("#abcdef")

    c.QColorDialog = _FakeDialog
    try:
        b.choose_color()
    finally:
        c.QColorDialog = orig
    assert b.color.name() == "#abcdef", b.color.name()
    assert "#abcdef" in b.styleSheet().lower()
    b.deleteLater()
    print("[PASS] test_color_button_choose_color_applies_selection")


def test_color_button_choose_color_cancel_keeps_color():
    """При отмене диалога цвет не меняется."""
    b = ColorButton("#123456")
    orig = c.QColorDialog

    class _FakeDialog:
        DialogCode = type("DC", (), {"Accepted": 1, "Rejected": 0})

        def __init__(self, color, parent=None):
            pass

        def exec(self):
            return self.DialogCode.Rejected

    c.QColorDialog = _FakeDialog
    try:
        b.choose_color()
    finally:
        c.QColorDialog = orig
    assert b.color.name() == "#123456", b.color.name()
    b.deleteLater()
    print("[PASS] test_color_button_choose_color_cancel_keeps_color")


def test_shortcuts_data_is_consistent():
    """Список горячих клавиш непустой, уникальный и корректно структурирован."""
    assert len(ShortcutsDialog.SHORTCUTS) > 10
    keys = [k for k, _ in ShortcutsDialog.SHORTCUTS]
    assert len(keys) == len(set(keys)), "дублирующиеся клавиши"
    for k, desc in ShortcutsDialog.SHORTCUTS:
        assert isinstance(k, str) and k
        assert isinstance(desc, str) and desc
    print("[PASS] test_shortcuts_data_is_consistent")


def test_shortcuts_dialog_titles_by_lang():
    """Заголовок диалога зависит от языка."""
    d_ru = ShortcutsDialog(lang="ru")
    d_en = ShortcutsDialog(lang="en")
    assert "Горячие клавиши" in d_ru.windowTitle()
    assert "Shortcuts" in d_en.windowTitle()
    d_ru.close()
    d_en.close()
    print("[PASS] test_shortcuts_dialog_titles_by_lang")


def test_shortcuts_dialog_renders_table():
    """Диалог строит HTML-таблицу со всеми сочетаниями."""
    d = ShortcutsDialog(lang="ru")
    from PyQt6.QtWidgets import QTextBrowser
    browsers = d.findChildren(QTextBrowser)
    assert browsers, "не найден QTextBrowser"
    html = browsers[0].toHtml()
    assert "<table" in html
    assert "Ctrl+N" in html
    assert "F11" in html
    d.close()
    print("[PASS] test_shortcuts_dialog_renders_table")


def main():
    tests = [
        test_color_button_initial_color,
        test_color_button_update_style_reflects_color,
        test_color_button_choose_color_applies_selection,
        test_color_button_choose_color_cancel_keeps_color,
        test_shortcuts_data_is_consistent,
        test_shortcuts_dialog_titles_by_lang,
        test_shortcuts_dialog_renders_table,
    ]
    for t in tests:
        t()
    print("\nAll common-dialogs tests passed!")


if __name__ == "__main__":
    main()
