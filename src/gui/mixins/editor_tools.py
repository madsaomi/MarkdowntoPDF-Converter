"""Автоматически перенесено из main_window.py (PLAN-010).

Перенос вербатим — тела методов не изменены.
"""


class EditorToolsMixin:
    """Миксин MainWindow. См. src/gui/mixins/__init__.py."""

    def on_editor_changed(self):
        self.is_welcome_doc_active = False
        self.preview_timer.start()
        self.update_text_statistics()

    def update_text_statistics(self):
        text = self.live_editor.toPlainText()
        char_count = len(text)
        words = [w for w in text.split() if w.strip()]
        word_count = len(words)
        
        reading_time = max(1, round(word_count / 180))
        if word_count == 0:
            reading_time = 0
            
        t = lambda k: TRANSLATIONS[self.current_lang].get(k, k)
        stats_text = (
            f"{t('stats_words').format(word_count)} | "
            f"{t('stats_chars').format(char_count)} | "
            f"{t('stats_reading').format(reading_time)}"
        )
        
        if self.writing_goal > 0:
            pct = min(100, int((word_count / self.writing_goal) * 100))
            stats_text += f" | 🎯 {pct}% ({word_count}/{self.writing_goal} {t('stats_words').format('').strip()})"
            
            if pct >= 100 and not self.goal_celebrated:
                self.goal_celebrated = True
                QMessageBox.information(
                    self,
                    t('goal_celebrate_title'),
                    t('goal_celebrate_desc').format(self.writing_goal)
                )
            
        self.stats_label.setText(stats_text)

    def toggle_search_panel(self):
        if self.search_panel.isVisible():
            self.search_panel.hide()
            self.live_editor.setFocus()
        else:
            self.search_panel.show()
            self.search_find_input.setFocus()
            self.search_find_input.selectAll()

    def search_next(self):
        query = self.search_find_input.text()
        if not query:
            return
        
        regex_mode = self.search_regex_checkbox.isChecked()
        if regex_mode:
            expr = QRegularExpression(query)
            found = self.live_editor.find(expr)
            if not found:
                cursor = self.live_editor.textCursor()
                cursor.movePosition(cursor.MoveOperation.Start)
                self.live_editor.setTextCursor(cursor)
                self.live_editor.find(expr)
        else:
            found = self.live_editor.find(query)
            if not found:
                cursor = self.live_editor.textCursor()
                cursor.movePosition(cursor.MoveOperation.Start)
                self.live_editor.setTextCursor(cursor)
                self.live_editor.find(query)

    def replace_all_occurrences(self):
        query = self.search_find_input.text()
        replace_text = self.search_replace_input.text()
        if not query:
            return
            
        cursor = self.live_editor.textCursor()
        scroll_pos = self.live_editor.verticalScrollBar().value()
        text = self.live_editor.toPlainText()
        
        regex_mode = self.search_regex_checkbox.isChecked()
        if regex_mode:
            import re
            try:
                new_text = re.sub(query, replace_text, text)
            except Exception as e:
                QMessageBox.critical(self, "RegEx Error", f"Invalid regular expression:\n{e}")
                return
        else:
            new_text = text.replace(query, replace_text)
        
        self.live_editor.blockSignals(True)
        self.live_editor.setPlainText(new_text)
        self.live_editor.blockSignals(False)
        
        self.live_editor.setTextCursor(cursor)
        self.live_editor.verticalScrollBar().setValue(scroll_pos)
        self._render_live_preview()
        self.update_text_statistics()

