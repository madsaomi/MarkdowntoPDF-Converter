"""Поведенческие тесты gui/dialogs/export.py.

``MultiExportDialog`` — выбор форматов (валидация «хотя бы один»),
``PDFStyleEditorDialog`` — значения по умолчанию всех трёх вкладок и кнопки.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QDialog, QDialogButtonBox

app = QApplication.instance() or QApplication([])

from src.gui.dialogs import export as export_mod
from src.gui.dialogs.export import MultiExportDialog, PDFStyleEditorDialog
from src.gui.dialogs.common import ColorButton


class _FakeMessageBox:
    """Запоминает warning-вызовы вместо модального окна."""

    warnings = []

    @classmethod
    def warning(cls, parent, title, text, *args, **kwargs):
        cls.warnings.append((title, text))


def _patch_message_box():
    _FakeMessageBox.warnings = []
    export_mod.QMessageBox = _FakeMessageBox


def _restore():
    import PyQt6.QtWidgets as qtw
    export_mod.QMessageBox = qtw.QMessageBox


# ─── MultiExportDialog ──────────────────────────────────────────────────────

def test_multi_export_defaults():
    """Семь форматов, по умолчанию выбран только PDF."""
    d = MultiExportDialog()
    assert d.windowTitle() == "📦 Multi-Export"
    assert list(d.format_checks) == ["pdf", "docx", "html", "epub", "pptx", "png", "jpg"]
    assert d.format_checks["pdf"].isChecked() is True
    for fmt in ("docx", "html", "epub", "pptx", "png", "jpg"):
        assert d.format_checks[fmt].isChecked() is False, fmt
    assert d.format_checks["pdf"].text() == "PDF"
    assert d.format_checks["jpg"].text() == "JPG"
    assert d.selected_formats == []
    print("[PASS] test_multi_export_defaults")


def test_multi_export_accept_with_pdf():
    """Принятие с одним PDF отдаёт список ["pdf"] и закрывает диалог."""
    _patch_message_box()
    try:
        d = MultiExportDialog()
        d.accept()
        assert d.selected_formats == ["pdf"]
        assert d.result() == QDialog.DialogCode.Accepted
        assert _FakeMessageBox.warnings == []
    finally:
        _restore()
    print("[PASS] test_multi_export_accept_with_pdf")


def test_multi_export_accept_requires_a_format():
    """Пустой выбор: предупреждение и диалог не закрывается."""
    _patch_message_box()
    try:
        d = MultiExportDialog()
        d.format_checks["pdf"].setChecked(False)
        d.accept()
        assert d.selected_formats == []
        assert d.result() != QDialog.DialogCode.Accepted
        assert len(_FakeMessageBox.warnings) == 1
        title, text = _FakeMessageBox.warnings[0]
        assert title == "Multi-Export"
        assert "format" in text.lower()
    finally:
        _restore()
    print("[PASS] test_multi_export_accept_requires_a_format")


def test_multi_export_accept_multiple_formats():
    """Порядок форматов соответствует порядку чекбоксов, а не кликов."""
    _patch_message_box()
    try:
        d = MultiExportDialog()
        d.format_checks["png"].setChecked(True)
        d.format_checks["docx"].setChecked(True)
        d.accept()
        assert d.selected_formats == ["pdf", "docx", "png"]
        assert d.result() == QDialog.DialogCode.Accepted
    finally:
        _restore()
    print("[PASS] test_multi_export_accept_multiple_formats")


def test_multi_export_accept_after_empty_attempt():
    """После предупреждения можно отметить формат и подтвердить."""
    _patch_message_box()
    try:
        d = MultiExportDialog()
        d.format_checks["pdf"].setChecked(False)
        d.accept()
        assert len(_FakeMessageBox.warnings) == 1
        d.format_checks["epub"].setChecked(True)
        d.accept()
        assert d.selected_formats == ["epub"]
        assert d.result() == QDialog.DialogCode.Accepted
    finally:
        _restore()
    print("[PASS] test_multi_export_accept_after_empty_attempt")


def test_multi_export_cancel_closes_without_selection():
    """«Cancel» закрывает диалог, не заполняя selected_formats."""
    d = MultiExportDialog()
    d.show()
    app.processEvents()
    # Кнопку ищем по тексту — она не сохранена в атрибуте
    from PyQt6.QtWidgets import QPushButton
    btn = [b for b in d.findChildren(QPushButton) if b.text() == "Cancel"][0]
    btn.click()
    assert d.isVisible() is False
    assert d.selected_formats == []
    print("[PASS] test_multi_export_cancel_closes_without_selection")


# ─── PDFStyleEditorDialog: вкладки ──────────────────────────────────────────

def test_style_dialog_has_three_tabs():
    """Три вкладки с локализованными названиями."""
    d = PDFStyleEditorDialog(lang="ru")
    assert d.tabs.count() == 3
    assert d.tabs.tabText(0) == "📖 Макет страницы"
    assert d.tabs.tabText(1) == "✍️ Типографика"
    assert d.tabs.tabText(2) == "🎨 Цвета"
    assert d.tabs.widget(0) is d.tab_layout
    assert d.tabs.widget(1) is d.tab_typography
    assert d.tabs.widget(2) is d.tab_colors
    print("[PASS] test_style_dialog_has_three_tabs")


def test_style_dialog_titles_localized():
    """Заголовок окна и кнопок зависит от языка."""
    ru = PDFStyleEditorDialog(lang="ru")
    en = PDFStyleEditorDialog(lang="en")
    assert ru.windowTitle() == "🎨 Редактор стиля PDF"
    assert en.windowTitle() == "🎨 PDF Layout & Style Designer"
    ok_ru = ru.button_box.button(QDialogButtonBox.StandardButton.Ok)
    cancel_ru = ru.button_box.button(QDialogButtonBox.StandardButton.Cancel)
    ok_en = en.button_box.button(QDialogButtonBox.StandardButton.Ok)
    cancel_en = en.button_box.button(QDialogButtonBox.StandardButton.Cancel)
    assert ok_ru.text() == "Сохранить тему"
    assert cancel_ru.text() == "Отмена"
    assert ok_en.text() == "Save Theme"
    assert cancel_en.text() == "Cancel"
    assert ru.isModal() is True
    print("[PASS] test_style_dialog_titles_localized")


# ─── PDFStyleEditorDialog: макет страницы ───────────────────────────────────

def test_style_dialog_margins_default_to_20mm():
    """Все четыре поля = 20 мм, диапазон 0…100, суффикс mm."""
    d = PDFStyleEditorDialog()
    for spin in (d.margin_top, d.margin_right, d.margin_bottom, d.margin_left):
        assert spin.value() == 20
        assert spin.minimum() == 0
        assert spin.maximum() == 100
        assert spin.suffix() == " mm"
    d.margin_left.setValue(37)
    assert d.margin_left.value() == 37
    assert d.margin_top.value() == 20
    print("[PASS] test_style_dialog_margins_default_to_20mm")


def test_style_dialog_paper_presets():
    """Список форматов бумаги и текущее значение A4."""
    d = PDFStyleEditorDialog()
    items = [d.paper_combo.itemText(i) for i in range(d.paper_combo.count())]
    assert items == ["A4", "Letter", "A5"]
    assert d.paper_combo.currentText() == "A4"
    d.paper_combo.setCurrentText("A5")
    assert d.paper_combo.currentText() == "A5"
    print("[PASS] test_style_dialog_paper_presets")


# ─── PDFStyleEditorDialog: типографика ──────────────────────────────────────

def test_style_dialog_typography_defaults():
    """Шрифт Inter, размер 14 px, интервал 1.5, выравнивание по ширине."""
    d = PDFStyleEditorDialog()
    fonts = [d.font_combo.itemText(i) for i in range(d.font_combo.count())]
    assert fonts == ["Inter", "Outfit", "Arial", "Times New Roman", "Georgia", "Courier New"]
    assert d.font_combo.currentText() == "Inter"
    assert d.font_size_spin.value() == 14
    assert d.font_size_spin.minimum() == 8
    assert d.font_size_spin.maximum() == 36
    assert d.font_size_spin.suffix() == " px"
    heights = [d.line_height_combo.itemText(i) for i in range(d.line_height_combo.count())]
    assert heights == ["1.0", "1.15", "1.3", "1.5", "1.8", "2.0"]
    assert d.line_height_combo.currentText() == "1.5"
    print("[PASS] test_style_dialog_typography_defaults")


def test_style_dialog_alignment_options():
    """Выравнивание: два пункта, по ширине выбран по умолчанию."""
    d = PDFStyleEditorDialog(lang="ru")
    assert d.align_combo.count() == 2
    assert d.align_combo.itemText(0) == "По ширине"
    assert d.align_combo.itemData(0) == "justify"
    assert d.align_combo.itemText(1) == "По левому краю"
    assert d.align_combo.itemData(1) == "left"
    assert d.align_combo.currentData() == "justify"

    en = PDFStyleEditorDialog(lang="en")
    assert en.align_combo.itemText(0) == "Justify"
    assert en.align_combo.itemText(1) == "Left"
    print("[PASS] test_style_dialog_alignment_options")


# ─── PDFStyleEditorDialog: цвета и кнопки ───────────────────────────────────

def test_style_dialog_color_buttons():
    """Три кнопки цвета с ожидаемыми значениями и подсветкой."""
    d = PDFStyleEditorDialog()
    assert isinstance(d.h_color_btn, ColorButton)
    assert isinstance(d.quote_color_btn, ColorButton)
    assert isinstance(d.code_bg_btn, ColorButton)
    assert d.h_color_btn.color.name() == "#2c3e50"
    assert d.quote_color_btn.color.name() == "#16a085"
    assert d.code_bg_btn.color.name() == "#f1f2f6"
    assert "#2c3e50" in d.h_color_btn.styleSheet()
    assert "#16a085" in d.quote_color_btn.styleSheet()
    assert "#f1f2f6" in d.code_bg_btn.styleSheet()
    print("[PASS] test_style_dialog_color_buttons")


def test_style_dialog_ok_accepts():
    """OK закрывает диалог с результатом Accepted."""
    d = PDFStyleEditorDialog()
    d.show()
    app.processEvents()
    d.button_box.button(QDialogButtonBox.StandardButton.Ok).click()
    assert d.result() == QDialog.DialogCode.Accepted
    print("[PASS] test_style_dialog_ok_accepts")


def test_style_dialog_cancel_rejects():
    """Cancel закрывает диалог с результатом Rejected."""
    d = PDFStyleEditorDialog()
    d.show()
    app.processEvents()
    d.button_box.button(QDialogButtonBox.StandardButton.Cancel).click()
    assert d.result() == QDialog.DialogCode.Rejected
    assert d.isVisible() is False
    print("[PASS] test_style_dialog_cancel_rejects")


def main():
    tests = [
        test_multi_export_defaults,
        test_multi_export_accept_with_pdf,
        test_multi_export_accept_requires_a_format,
        test_multi_export_accept_multiple_formats,
        test_multi_export_accept_after_empty_attempt,
        test_multi_export_cancel_closes_without_selection,
        test_style_dialog_has_three_tabs,
        test_style_dialog_titles_localized,
        test_style_dialog_margins_default_to_20mm,
        test_style_dialog_paper_presets,
        test_style_dialog_typography_defaults,
        test_style_dialog_alignment_options,
        test_style_dialog_color_buttons,
        test_style_dialog_ok_accepts,
        test_style_dialog_cancel_rejects,
    ]
    for t in tests:
        t()
    print("\nAll export dialog tests passed!")


if __name__ == "__main__":
    main()
