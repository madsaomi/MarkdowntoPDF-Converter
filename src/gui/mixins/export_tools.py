"""Экспорт: мульти-экспорт, версии, облачные шаблоны, печать, HTML.

Выделено из ``src/gui/window_tools.py`` (TASK-012/PLAN-012), тела вербатим.
"""

import os

from PyQt6.QtWidgets import QFileDialog, QInputDialog, QMessageBox


class ExportToolsMixin:
    def show_multi_export(self):
        if not self.selected_files:
            QMessageBox.information(self, "Multi-Export", "Select a file first")
            return

        from src.gui.dialogs import MultiExportDialog
        dlg = MultiExportDialog(self, self.current_lang)
        if dlg.exec():
            from src.core.multi_export import multi_export, export_summary
            out_dir = QFileDialog.getExistingDirectory(self, "Output Directory")
            if not out_dir:
                return
            results = multi_export(
                self.selected_files[0], out_dir, dlg.selected_formats,
                self._get_template_dir(), self._get_options()
            )
            summary = export_summary(results)
            QMessageBox.information(self, "Multi-Export", summary)
            self.append_log(f"Multi-export completed: {len(results)} formats")

    def export_selection(self):
        cursor = self.live_editor.textCursor()
        text = cursor.selectedText()
        if not text:
            QMessageBox.information(self, "Export", "Select text first")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Selection", "selection.md", "Markdown (*.md)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self.append_log(f"Selection saved: {os.path.basename(path)}")

    def export_as_markdown(self):
        text = self.live_editor.toPlainText()
        path, _ = QFileDialog.getSaveFileName(self, "Save as Markdown", "document.md", "Markdown (*.md)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self.append_log(f"Saved as Markdown: {os.path.basename(path)}")

    def save_version(self):
        from src.gui.document_tools import save_revision
        save_revision(self)
        self.toast("Version saved", "success")

    def restore_version(self):
        from src.gui.document_tools import show_revision_history
        show_revision_history(self)
        self.update_preview_from_editor()

    def show_cloud_templates(self):
        from src.core.cloud_templates import get_cloud_templates_index, download_template, save_local_template
        templates = get_cloud_templates_index(self.current_lang)

        names = [t.get("name", "Template") for t in templates]
        if not names:
            QMessageBox.information(self, "Templates", "No templates available")
            return

        chosen, ok = QInputDialog.getItem(self, "Cloud Templates", "Choose template:", names, 0, False)
        if ok and chosen:
            for t in templates:
                if t.get("name") == chosen:
                    content = t.get("content", "")
                    if not content and t.get("url"):
                        content = download_template(t["url"])
                    if content:
                        self.live_editor.setPlainText(content)
                        self._render_live_preview()
                        self.append_log(f"Template loaded: {chosen}")
                    return

    def print_document(self):
        from src.gui.preview_manager import print_document
        print_document(self)

    def copy_styled_html(self):
        from src.gui.preview_manager import copy_styled_html
        copy_styled_html(self)

