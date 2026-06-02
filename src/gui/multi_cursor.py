import logging
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor

logger = logging.getLogger("MarkdownToPDF.multi_cursor")


class MultiCursorManager:
    """Multi-cursor editing support for QTextEdit."""

    def __init__(self, editor: QTextEdit):
        self.editor = editor
        self.cursors: list[QTextCursor] = []
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active and len(self.cursors) > 0

    def add_cursor_at_line(self, line_number: int):
        """Add a cursor at the specified line number (0-indexed)."""
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        for _ in range(line_number):
            cursor.movePosition(QTextCursor.MoveOperation.Down)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        self.cursors.append(cursor)
        self._active = True
        self._highlight_cursors()

    def add_cursor_at_current(self):
        """Add a new cursor at the current cursor position."""
        cursor = self.editor.textCursor()
        new_cursor = QTextCursor(cursor)
        self.cursors.append(new_cursor)
        self._active = True
        self._highlight_cursors()

    def remove_last_cursor(self):
        """Remove the last added cursor."""
        if self.cursors:
            self.cursors.pop()
            if not self.cursors:
                self._active = False
            self._highlight_cursors()

    def clear_cursors(self):
        """Remove all secondary cursors."""
        self.cursors.clear()
        self._active = False

    def select_all_occurrences(self, text: str):
        """Select all occurrences of text, creating a cursor for each."""
        self.clear_cursors()
        doc = self.editor.document()
        cursor = QTextCursor(doc)
        cursor.movePosition(QTextCursor.MoveOperation.Start)

        while True:
            cursor = self.editor.document().find(text, cursor)
            if cursor.isNull():
                break
            self.cursors.append(QTextCursor(cursor))
            self.editor.setTextCursor(cursor)

        if self.cursors:
            self._active = True
            self._highlight_cursors()

    def type_at_all_cursors(self, text: str):
        """Insert text at all cursor positions (in reverse order to preserve positions)."""
        for cursor in reversed(self.cursors):
            cursor.insertText(text)

    def _highlight_cursors(self):
        """Visually indicate multi-cursor positions."""
        extra = []
        fmt = QTextCharFormat()
        fmt.setBackground(QColor(52, 152, 219, 100))
        fmt.setForeground(QColor(255, 255, 255))

        for cursor in self.cursors:
            from PyQt6.QtWidgets import QTextEdit
            selection = QTextEdit.ExtraSelection()
            selection.format = fmt
            selection.cursor = QTextCursor(cursor)
            extra.append(selection)

        self.editor.setExtraSelections(extra)
