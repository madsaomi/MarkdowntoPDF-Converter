"""Режимы отображения редактора: split/zen/focus/typewriter/WYSIWYG, зум.

Выделено из ``src/gui/window_tools.py`` (TASK-012/PLAN-012), тела вербатим.
"""


class EditorViewModesMixin:
    def toggle_split_view(self):
        """Переключение режимов editor/preview.

        Сплиттер содержит ровно 2 виджета (editor_container, preview_output),
        поэтому «скрытие» делается через setVisible — иначе setSizes игнорируется Qt.
        """
        modes = ['both', 'editor', 'preview']
        current = getattr(self, '_split_view_mode', 'both')
        idx = (modes.index(current) + 1) % len(modes)
        self._split_view_mode = modes[idx]

        if self._split_view_mode == 'both':
            self.preview_output.show()
            self.live_editor.show()
            self.editor_splitter.setSizes([500, 500])
        elif self._split_view_mode == 'editor':
            self.preview_output.hide()
            self.live_editor.show()
        else:
            self.preview_output.show()
            self.live_editor.hide()

    def toggle_zen_mode(self):
        is_zen = not getattr(self, '_zen_mode', False)
        self._zen_mode = is_zen
        if hasattr(self, 'format_toolbar'):
            self.format_toolbar.setVisible(not is_zen)
        if hasattr(self, 'tabs'):
            self.tabs.setVisible(not is_zen)
        self.statusBar().setVisible(not is_zen)
        if is_zen:
            self.showFullScreen()
        else:
            self.showNormal()

    def toggle_focus_mode(self):
        is_focus = not getattr(self, '_focus_mode', False)
        self._focus_mode = is_focus
        if hasattr(self, 'format_toolbar'):
            self.format_toolbar.setVisible(not is_focus)
        if is_focus:
            self.live_editor.setStyleSheet(self.live_editor.styleSheet() + " QTextEdit { font-size: 16px; }")
        else:
            self.live_editor.setStyleSheet(self.live_editor.styleSheet().replace(" QTextEdit { font-size: 16px; }", ""))

    def toggle_typewriter_mode(self):
        self._typewriter_mode = not getattr(self, '_typewriter_mode', False)
        if self._typewriter_mode:
            cursor = self.live_editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self.live_editor.setTextCursor(cursor)
            self.live_editor.setStyleSheet(self.live_editor.styleSheet() + " QTextEdit { font-size: 16px; line-height: 2.0; }")
        else:
            self.live_editor.setStyleSheet(self.live_editor.styleSheet().replace(" QTextEdit { font-size: 16px; line-height: 2.0; }", ""))
        self.toast("Typewriter: " + ("ON" if self._typewriter_mode else "OFF"), "info")

    def toggle_wysiwyg(self):
        self._wysiwyg = not getattr(self, '_wysiwyg', False)
        if self._wysiwyg:
            self.preview_output.show()
            self.live_editor.hide()
        else:
            self.preview_output.hide()
            self.live_editor.show()
        self.toast("WYSIWYG: " + ("ON" if self._wysiwyg else "OFF"), "info")

    def zoom_in(self):
        from src.gui.preview_manager import zoom_in
        zoom_in(self)

    def zoom_out(self):
        from src.gui.preview_manager import zoom_out
        zoom_out(self)

    def zoom_reset(self):
        from src.gui.preview_manager import zoom_reset
        zoom_reset(self)

