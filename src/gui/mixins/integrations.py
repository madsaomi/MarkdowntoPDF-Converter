"""Интеграции: watermark, цитаты, CSV, Excalidraw, календарь, помодоро, GitHub.

Также генераторы TOC/таблиц/стилей и менеджер плагинов. Выделено из
``src/gui/window_tools.py`` (TASK-012/PLAN-012), тела вербатим.
"""

import os

from PyQt6.QtWidgets import QMessageBox


class IntegrationsMixin:
    def show_watermark_designer(self):
        from src.gui.watermark_designer import WatermarkDesignerDialog
        dlg = WatermarkDesignerDialog(self, self.current_lang)
        if dlg.exec():
            # Текст — в поле «Watermark», сгенерированный CSS — в скрытый носитель,
            # который передаётся в рендерер (иначе стили дизайнера терялись).
            self.footer_input.setText(dlg.text_input.text())
            if hasattr(self, 'watermark_css_input'):
                self.watermark_css_input.setText(dlg.result_css.strip())
            self.append_log("Watermark applied (text + custom styles)")

    def show_citation_manager(self):
        from src.gui.dialogs import CitationManagerDialog
        dlg = CitationManagerDialog(self, self.current_lang)
        dlg.exec()

    def show_csv_editor(self):
        from src.gui.csv_editor import CSVEditorDialog
        dlg = CSVEditorDialog(self, self.current_lang)
        if dlg.exec():
            md = dlg.selected_markdown
            if md:
                cursor = self.live_editor.textCursor()
                cursor.insertText(md)
                self._render_live_preview()

    def show_excalidraw(self):
        from src.gui.excalidraw_canvas import ExcalidrawDialog
        dlg = ExcalidrawDialog(self, self.current_lang)
        if dlg.exec():
            md = dlg.selected_markdown
            if md:
                cursor = self.live_editor.textCursor()
                cursor.insertText(md)
                self._render_live_preview()

    def show_calendar_notes(self):
        from src.gui.calendar_view import CalendarNotesDialog
        folder = getattr(self, 'active_workspace_folder', None) or os.getcwd()
        dlg = CalendarNotesDialog(self, self.current_lang, folder)
        dlg.exec()

    def show_pomodoro(self):
        from src.gui.pomodoro import PomodoroDialog
        dlg = PomodoroDialog(self, self.current_lang)
        dlg.exec()

    def show_github_sync_dialog(self):
        if not self.selected_files:
            QMessageBox.information(self, "GitHub Sync", "Open a folder first")
            return
        folder = self.active_workspace_folder or os.path.dirname(self.selected_files[0])
        from src.gui.dialogs import GitHubSyncDialog
        dlg = GitHubSyncDialog(self, folder, self.current_lang)
        dlg.exec()

    def show_plugin_manager(self):
        from src.gui.dialogs import PluginManagerDialog
        dlg = PluginManagerDialog(self, self.current_lang)
        dlg.exec()

    def show_toc_generator(self):
        from src.gui.document_tools import show_toc_generator
        show_toc_generator(self)

    def show_table_generator_dialog(self):
        from src.gui.document_tools import show_table_generator_dialog
        show_table_generator_dialog(self)

    def show_design_style_dialog(self):
        from src.gui.document_tools import show_design_style_dialog
        show_design_style_dialog(self)

