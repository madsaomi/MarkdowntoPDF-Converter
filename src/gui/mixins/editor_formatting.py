"""Форматирование редактора: bold/italic/header/code/quote/list, линтер, TOC.

Выделено из ``src/gui/window_tools.py`` (TASK-012/PLAN-012), тела вербатим.
"""

from PyQt6.QtWidgets import QMessageBox


class EditorFormattingMixin:
    def run_spell_check(self):
        import re
        text = self.live_editor.toPlainText()
        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]+\b', text)
        if not words:
            QMessageBox.information(self, "Spell Check", "No words found")
            return
        issues_count = 0
        for w in words[:100]:
            if len(w) > 20:
                issues_count += 1
        QMessageBox.information(self, "Spell Check",
            f"Checked {len(words)} words.{' Found ' + str(issues_count) + ' potential issues.' if issues_count else ' No issues found.'}")

    def convert_emoji_shortcodes(self):
        text = self.live_editor.toPlainText()
        import re
        emoji_map = {
            ":smile:": "\U0001F604", ":sad:": "\U0001F622", ":heart:": "\u2764\uFE0F",
            ":fire:": "\U0001F525", ":rocket:": "\U0001F680", ":check:": "\u2705",
            ":x:": "\u274C", ":warning:": "\u26A0\uFE0F", ":bulb:": "\U0001F4A1",
            ":star:": "\u2B50", ":thumbsup:": "\U0001F44D", ":clap:": "\U0001F44F",
            ":wave:": "\U0001F44B", ":100:": "\U0001F4AF",
        }
        result = re.sub(r':\w+:', lambda m: emoji_map.get(m.group(), m.group()), text)
        self.live_editor.setPlainText(result)
        self._render_live_preview()
        self.toast("Emoji shortcodes converted", "success")

    def add_multi_cursor(self):
        if hasattr(self, 'multi_cursor'):
            self.multi_cursor.add_cursor_at_current()
            self.toast("Multi-cursor added", "info")

    def run_linter(self):
        from src.core.linter import lint_markdown
        from src.gui.document_tools import show_document_audit
        text = self.live_editor.toPlainText()
        issues = lint_markdown(text, self.current_lang)
        show_document_audit(self)

    def format_markdown_document(self):
        from src.gui.editor_commands import format_markdown_document
        format_markdown_document(self)

    def format_bold(self):
        from src.gui.editor_commands import format_bold
        format_bold(self)

    def format_italic(self):
        from src.gui.editor_commands import format_italic
        format_italic(self)

    def format_header(self, level):
        from src.gui.editor_commands import format_header
        format_header(self, level)

    def format_code(self):
        from src.gui.editor_commands import format_code
        format_code(self)

    def format_quote(self):
        from src.gui.editor_commands import format_quote
        format_quote(self)

    def format_list(self):
        from src.gui.editor_commands import format_list
        format_list(self)

    def insert_page_break(self):
        from src.gui.editor_commands import insert_page_break
        insert_page_break(self)

    def update_markdown_toc_in_editor(self):
        from src.gui.document_tools import update_markdown_toc_in_editor
        update_markdown_toc_in_editor(self)

