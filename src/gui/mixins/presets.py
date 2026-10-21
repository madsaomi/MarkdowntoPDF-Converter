"""Автоматически перенесено из main_window.py (PLAN-010).

Перенос вербатим — тела методов не изменены.
"""

import json

from PyQt6.QtWidgets import QInputDialog, QMessageBox


class PresetsMixin:
    """Миксин MainWindow. См. src/gui/mixins/__init__.py."""

    def load_presets(self):
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        
        # Load presets dict from settings
        presets_str = self.settings.value("presets", "{}", str)
        try:
            self.presets = json.loads(presets_str)
        except Exception:
            self.presets = {}
            
        default_label = "(по умолчанию)" if self.current_lang == "ru" else "(default)"
        self.preset_combo.addItem(default_label)
        
        for name in sorted(self.presets.keys()):
            self.preset_combo.addItem(name)
            
        self.preset_combo.blockSignals(False)

    def save_preset(self):
        title = self.tr_msg("preset_prompt_title")
        desc = self.tr_msg("preset_prompt_desc")
        name, ok = QInputDialog.getText(self, title, desc)
        name = name.strip()
        if not ok or not name:
            return
            
        # Capture current settings (password excluded for security)
        opt = self._get_options()
        preset_data = {
            "doc_theme": self.doc_theme_combo.currentIndex(),
            "code_theme": self.code_theme_combo.currentIndex(),
            "paper_size": self.paper_combo.currentIndex(),
            "watermark": opt.watermark,
            "footer_text": opt.footer_text,
            "custom_css": opt.custom_css,
            "export_format": self.format_combo.currentIndex(),
            "margins": opt.margins,
            "docx_template": opt.docx_template,
            "page_numbers": opt.page_numbers,
            "page_num_format": self.combo_page_format.currentIndex(),
            "presentation_mode": opt.is_presentation,
        }
        
        self.presets[name] = preset_data
        self.settings.setValue("presets", json.dumps(self.presets))
        
        self.load_presets()
        # Select newly created preset
        idx = self.preset_combo.findText(name)
        if idx >= 0:
            self.preset_combo.setCurrentIndex(idx)
            
        QMessageBox.information(self, self.tr_msg("msg_done_title"), self.tr_msg("msg_preset_saved", name))

    def delete_preset(self):
        idx = self.preset_combo.currentIndex()
        if idx <= 0: # Cannot delete default
            return
        name = self.preset_combo.currentText()
        if name in self.presets:
            del self.presets[name]
            self.settings.setValue("presets", json.dumps(self.presets))
            self.load_presets()
            QMessageBox.information(self, self.tr_msg("msg_done_title"), self.tr_msg("msg_preset_deleted", name))

    def on_preset_changed(self, idx: int):
        if idx <= 0:
            # Load factory default settings or just keep current
            return
        name = self.preset_combo.currentText()
        preset = self.presets.get(name)
        if not preset:
            return
            
        # Apply preset to UI elements
        self.doc_theme_combo.setCurrentIndex(preset.get("doc_theme", 0))
        self.code_theme_combo.setCurrentIndex(preset.get("code_theme", 0))
        self.paper_combo.setCurrentIndex(preset.get("paper_size", 0))
        self.watermark_input.setText(preset.get("watermark", ""))
        self.footer_input.setText(preset.get("footer_text", ""))
        self.custom_css_input.setText(preset.get("custom_css", ""))
        self.format_combo.setCurrentIndex(preset.get("export_format", 0))
        self.margins_input.setText(preset.get("margins", ""))
        self.docx_template_input.setText(preset.get("docx_template", ""))
        self.chk_page_numbers.setChecked(preset.get("page_numbers", False))
        self.combo_page_format.setCurrentIndex(preset.get("page_num_format", 0))
        self.combo_page_format.setEnabled(self.chk_page_numbers.isChecked())
        self.chk_presentation_mode.setChecked(preset.get("presentation_mode", False))

