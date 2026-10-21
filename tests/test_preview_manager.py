"""Поведенческие тесты менеджера превью (gui/preview_manager).

Проверяет рендер живого превью (обычный режим, режим презентации, ошибка),
синхронизацию прокрутки и операции масштаба.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication

app = QApplication.instance() or QApplication([])

from src.gui import preview_manager


class _FakeScrollBar:
    def __init__(self, maximum=0, value=0):
        self._max = maximum
        self._value = value

    def maximum(self):
        return self._max

    def value(self):
        return self._value

    def setValue(self, v):
        self._value = v


class _FakeEditor:
    def __init__(self, text=""):
        self._text = text
        self.scroll = _FakeScrollBar(100, 0)
        self.zoom = 0

    def toPlainText(self):
        return self._text

    def verticalScrollBar(self):
        return self.scroll

    def zoomIn(self, n=1):
        self.zoom += n

    def zoomOut(self, n=1):
        self.zoom -= n


class _FakePreview:
    def __init__(self):
        self.html = ""
        self.scroll = _FakeScrollBar(200, 0)
        self.zoom = 0

    def setHtml(self, h):
        self.html = h

    def toHtml(self):
        return self.html

    def verticalScrollBar(self):
        return self.scroll

    def zoomIn(self, n=1):
        self.zoom += n

    def zoomOut(self, n=1):
        self.zoom -= n


class _FakeCheckbox:
    def __init__(self, checked=False):
        self._checked = checked

    def isChecked(self):
        return self._checked


class _FakeWindow:
    def __init__(self, text="# Заголовок\n\nТекст", presentation=False):
        self.live_editor = _FakeEditor(text)
        self.preview_output = _FakePreview()
        self.chk_presentation_mode = _FakeCheckbox(presentation)
        self.kroki_available = False
        self.is_dark = False
        self.zoom_level = 0
        self.current_lang = "ru"
        self.current_document_title = "Док"

    def get_current_document_dir(self):
        return os.getcwd()


def test_render_live_preview_sets_html():
    """render_live_preview помещает HTML в preview_output."""
    w = _FakeWindow()
    preview_manager.render_live_preview(w)
    assert w.preview_output.html, "HTML должен быть установлен"
    assert "<html" in w.preview_output.html.lower()
    assert "Заголовок" in w.preview_output.html
    print("[PASS] test_render_live_preview_sets_html")


def test_render_live_preview_empty_text_noop():
    """Пустой текст не вызывает рендер (HTML остаётся прежним)."""
    w = _FakeWindow(text="")
    preview_manager.render_live_preview(w)
    assert w.preview_output.html == ""
    print("[PASS] test_render_live_preview_empty_text_noop")


def test_render_live_preview_presentation_mode():
    """В режиме презентации используется тёмный слайд-шаблон."""
    w = _FakeWindow(presentation=True)
    preview_manager.render_live_preview(w)
    html = w.preview_output.html
    assert ".slide" in html
    assert "#111827" in html
    print("[PASS] test_render_live_preview_presentation_mode")


def test_render_live_preview_handles_error():
    """При исключении показывается сообщение об ошибке, а не падение."""
    import logging

    w = _FakeWindow()

    class _Boom:
        def isChecked(self):
            raise RuntimeError("boom")

    w.chk_presentation_mode = _Boom()
    # Ожидаемая ошибка логируется модулем — временно глушим логгер.
    logger = logging.getLogger("MarkdownToPDF.preview_manager")
    prev_disabled = logger.disabled
    logger.disabled = True
    try:
        preview_manager.render_live_preview(w)
    finally:
        logger.disabled = prev_disabled
    assert "Preview error" in w.preview_output.html
    print("[PASS] test_render_live_preview_handles_error")


def test_sync_scroll_preview_maps_percentage():
    """sync_scroll_preview переносит процент прокрутки на превью."""
    w = _FakeWindow()
    w.live_editor.scroll = _FakeScrollBar(100, 50)
    w.preview_output.scroll = _FakeScrollBar(200, 0)
    preview_manager.sync_scroll_preview(w, 50)
    assert w.preview_output.scroll.value() == 100
    print("[PASS] test_sync_scroll_preview_maps_percentage")


def test_sync_scroll_preview_noop_when_editor_empty():
    """Если у редактора нет прокрутки — синхронизация не выполняется."""
    w = _FakeWindow()
    w.live_editor.scroll = _FakeScrollBar(0, 0)
    preview_manager.sync_scroll_preview(w, 50)
    assert w.preview_output.scroll.value() == 0
    print("[PASS] test_sync_scroll_preview_noop_when_editor_empty")


def test_zoom_in_out_and_reset():
    """zoom_in/zoom_out/zoom_reset корректно меняют уровень и масштаб."""
    w = _FakeWindow()
    preview_manager.zoom_in(w)
    assert w.zoom_level == 1
    assert w.live_editor.zoom == 1
    assert w.preview_output.zoom == 1

    preview_manager.zoom_out(w)
    assert w.zoom_level == 0
    assert w.live_editor.zoom == 0

    preview_manager.zoom_in(w)
    preview_manager.zoom_in(w)
    assert w.zoom_level == 2
    preview_manager.zoom_reset(w)
    assert w.zoom_level == 0
    assert w.live_editor.zoom == 0
    assert w.preview_output.zoom == 0
    print("[PASS] test_zoom_in_out_and_reset")


def test_zoom_reset_from_negative():
    """zoom_reset возвращает отрицательный масштаб к нулю."""
    w = _FakeWindow()
    preview_manager.zoom_out(w)
    preview_manager.zoom_out(w)
    assert w.zoom_level == -2
    preview_manager.zoom_reset(w)
    assert w.zoom_level == 0
    assert w.live_editor.zoom == 0
    assert w.preview_output.zoom == 0
    print("[PASS] test_zoom_reset_from_negative")


def main():
    tests = [
        test_render_live_preview_sets_html,
        test_render_live_preview_empty_text_noop,
        test_render_live_preview_presentation_mode,
        test_render_live_preview_handles_error,
        test_sync_scroll_preview_maps_percentage,
        test_sync_scroll_preview_noop_when_editor_empty,
        test_zoom_in_out_and_reset,
        test_zoom_reset_from_negative,
    ]
    for t in tests:
        t()
    print("\nAll preview_manager tests passed!")


if __name__ == "__main__":
    main()
