"""Воркспейс: проводник, черновики, wikilinks, папка вывода, resize.

Выделено из ``src/gui/window_tools.py`` (TASK-012/PLAN-012), тела вербатим.
"""

import os


class WorkspaceMixin:
    def process_wikilinks(self):
        from src.core.wikilinks import WikiLinkProcessor
        base_dir = self.active_workspace_folder or (os.path.dirname(self.selected_files[0]) if self.selected_files else os.getcwd())
        proc = WikiLinkProcessor(base_dir)
        text = self.live_editor.toPlainText()
        processed = proc.resolve_links(text)
        self.live_editor.setPlainText(processed)
        self._render_live_preview()
        self.append_log("Wiki links resolved")

    def apply_template_vars(self):
        from src.core.template_vars import process_document_vars
        text = self.live_editor.toPlainText()
        result = process_document_vars(text)
        self.live_editor.setPlainText(result)
        self._render_live_preview()
        self.toast("Template variables applied", "success")

    def update_workspace_explorer(self):
        from src.gui.file_manager import update_workspace_explorer
        update_workspace_explorer(self)

    def restore_draft_if_exists(self):
        from src.gui.document_tools import restore_draft_if_exists
        restore_draft_if_exists(self)

    def open_output_folder(self):
        from src.gui.file_manager import open_output_folder
        open_output_folder(self)

    def filter_workspace_explorer(self, text):
        from src.gui.file_manager import filter_workspace_explorer
        filter_workspace_explorer(self, text)

    def load_workspace_file(self, item):
        from src.gui.file_manager import load_workspace_file
        load_workspace_file(self, item)

    def resizeEvent(self, event):
        from PyQt6.QtWidgets import QWidget
        QWidget.resizeEvent(self, event)
        if hasattr(self, '_glow') and self._glow.isVisible():
            self._glow.setGeometry(0, 0, self.width(), self.height())
        if hasattr(self, '_titlebar') and self._titlebar.isVisible():
            self._titlebar.setGeometry(0, 0, self.width(), 42)

