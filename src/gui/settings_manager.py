"""Settings persistence and preset management."""

import json
import logging
from PyQt6.QtWidgets import QApplication, QInputDialog, QMessageBox
from src.gui.translations import TRANSLATIONS
from src.gui.models import ExportFormat

logger = logging.getLogger("MarkdownToPDF.settings_manager")


def load_settings(window):
    window.doc_theme_combo.setCurrentIndex(window.settings.value("doc_theme", 0, int))
    window.code_theme_combo.setCurrentIndex(window.settings.value("code_theme", 0, int))
    window.paper_combo.setCurrentIndex(window.settings.value("paper_size", 0, int))

    if not window.settings.contains("dark_mode"):
        window.is_dark = (window.get_windows_theme() == "dark")
    else:
        window.is_dark = window.settings.value("dark_mode", False, bool)

    window.last_output_dir = window.settings.value("last_output_dir", "", str)
    window.custom_css_input.setText(window.settings.value("custom_css", "", str))
    window.format_combo.setCurrentIndex(window.settings.value("export_format", 0, int))
    window.chk_page_numbers.setChecked(window.settings.value("page_numbers", False, bool))
    window.combo_page_format.setCurrentIndex(window.settings.value("page_num_format", 0, int))
    window.combo_page_format.setEnabled(window.chk_page_numbers.isChecked())
    window.chk_presentation_mode.setChecked(window.settings.value("presentation_mode", False, bool))
    if window.is_dark:
        QApplication.instance().setStyleSheet(window.__class__._dark_style if hasattr(window.__class__, '_dark_style') else "")
        window.btn_theme.setText("☀️ Светлая тема")
    else:
        QApplication.instance().setStyleSheet(window.__class__._light_style if hasattr(window.__class__, '_light_style') else "")
        window.btn_theme.setText("🌙 Тёмная тема")
    window.update_recent_menu()


def save_settings(window):
    window.settings.setValue("doc_theme", window.doc_theme_combo.currentIndex())
    window.settings.setValue("code_theme", window.code_theme_combo.currentIndex())
    window.settings.setValue("paper_size", window.paper_combo.currentIndex())
    window.settings.setValue("dark_mode", window.is_dark)
    window.settings.setValue("last_output_dir", window.last_output_dir)
    window.settings.setValue("custom_css", window.custom_css_input.text().strip())
    window.settings.setValue("export_format", window.format_combo.currentIndex())
    window.settings.setValue("page_numbers", window.chk_page_numbers.isChecked())
    window.settings.setValue("page_num_format", window.combo_page_format.currentIndex())
    window.settings.setValue("presentation_mode", window.chk_presentation_mode.isChecked())


def load_presets(window):
    window.preset_combo.blockSignals(True)
    window.preset_combo.clear()

    presets_str = window.settings.value("presets", "{}", str)
    try:
        window.presets = json.loads(presets_str)
    except Exception:
        window.presets = {}

    default_label = "(по умолчанию)" if window.current_lang == "ru" else "(default)"
    window.preset_combo.addItem(default_label)

    for name in sorted(window.presets.keys()):
        window.preset_combo.addItem(name)

    window.preset_combo.blockSignals(False)


def save_preset(window):
    t = lambda k: TRANSLATIONS[window.current_lang].get(k, k)
    title = t("preset_prompt_title")
    desc = t("preset_prompt_desc")
    name, ok = QInputDialog.getText(window, title, desc)
    name = name.strip()
    if not ok or not name:
        return

    from src.gui.main_window import _get_options
    opt = _get_options(window)
    preset_data = {
        "doc_theme": window.doc_theme_combo.currentIndex(),
        "code_theme": window.code_theme_combo.currentIndex(),
        "paper_size": window.paper_combo.currentIndex(),
        "watermark": opt.watermark,
        "footer_text": opt.footer_text,
        "custom_css": opt.custom_css,
        "export_format": window.format_combo.currentIndex(),
        "margins": opt.margins,
        "docx_template": opt.docx_template,
        "page_numbers": opt.page_numbers,
        "page_num_format": window.combo_page_format.currentIndex(),
        "presentation_mode": opt.is_presentation,
    }

    window.presets[name] = preset_data
    window.settings.setValue("presets", json.dumps(window.presets))

    load_presets(window)
    idx = window.preset_combo.findText(name)
    if idx >= 0:
        window.preset_combo.setCurrentIndex(idx)

    QMessageBox.information(window, t("msg_done_title"), t("msg_preset_saved", name))


def delete_preset(window):
    idx = window.preset_combo.currentIndex()
    if idx <= 0:
        return
    t = lambda k: TRANSLATIONS[window.current_lang].get(k, k)
    name = window.preset_combo.currentText()
    if name in window.presets:
        del window.presets[name]
        window.settings.setValue("presets", json.dumps(window.presets))
        load_presets(window)
        QMessageBox.information(window, t("msg_done_title"), t("msg_preset_deleted", name))


def on_preset_changed(window, idx):
    if idx <= 0:
        return
    name = window.preset_combo.currentText()
    preset = window.presets.get(name)
    if not preset:
        return

    window.doc_theme_combo.setCurrentIndex(preset.get("doc_theme", 0))
    window.code_theme_combo.setCurrentIndex(preset.get("code_theme", 0))
    window.paper_combo.setCurrentIndex(preset.get("paper_size", 0))
    window.watermark_input.setText(preset.get("watermark", ""))
    window.footer_input.setText(preset.get("footer_text", ""))
    window.custom_css_input.setText(preset.get("custom_css", ""))
    window.format_combo.setCurrentIndex(preset.get("export_format", 0))
    window.margins_input.setText(preset.get("margins", ""))
    window.docx_template_input.setText(preset.get("docx_template", ""))
    window.chk_page_numbers.setChecked(preset.get("page_numbers", False))
    window.combo_page_format.setCurrentIndex(preset.get("page_num_format", 0))
    window.combo_page_format.setEnabled(window.chk_page_numbers.isChecked())
    window.chk_presentation_mode.setChecked(preset.get("presentation_mode", False))
