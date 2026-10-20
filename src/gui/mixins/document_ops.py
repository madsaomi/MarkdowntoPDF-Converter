"""Автоматически перенесено из main_window.py (PLAN-010).

Перенос вербатим — тела методов не изменены.
"""


class DocumentOpsMixin:
    """Миксин MainWindow. См. src/gui/mixins/__init__.py."""

    def autosave_draft(self):
        document_tools.autosave_draft(self)

    def save_current_workspace_file(self):
        file_manager.save_current_workspace_file(self)

    def save_revision(self):
        document_tools.save_revision(self)

    def show_revision_history(self):
        document_tools.show_revision_history(self)

    def goto_editor_line(self, line_num: int):
        cursor = self.live_editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        for _ in range(line_num - 1):
            cursor.movePosition(cursor.MoveOperation.Down)
        
        # Select full line
        cursor.movePosition(cursor.MoveOperation.StartOfLine)
        cursor.movePosition(cursor.MoveOperation.EndOfLine, cursor.MoveMode.KeepAnchor)
        
        self.live_editor.setTextCursor(cursor)
        self.live_editor.setFocus()

    def show_document_audit(self):
        document_tools.show_document_audit(self)

    def auto_fix_document_issues(self):
        document_tools.auto_fix_document_issues(self)

    def show_doc_templates_dialog(self):
        from src.gui.templates_data import get_template_list, get_template_content
        templates = get_template_list()
        names = [name for _, name in templates]
        chosen, ok = QInputDialog.getItem(
            self,
            self.tr_msg("doc_templates_title"),
            self.tr_msg("doc_templates_label"),
            names, 0, False
        )
        if ok and chosen:
            for key, name in templates:
                if name == chosen:
                    content = get_template_content(key)
                    if content:
                        self.live_editor.setPlainText(content)
                        self.update_preview_from_editor()
                    break

