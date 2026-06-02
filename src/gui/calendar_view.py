import os
import re
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QCalendarWidget, QSplitter,
    QTextBrowser, QWidget
)
from PyQt6.QtCore import Qt, QDate


class CalendarNotesDialog(QDialog):
    """Calendar view for notes sorted by file modification date."""

    def __init__(self, parent=None, lang="ru", folder: str = None):
        super().__init__(parent)
        self.lang = lang
        self.folder = folder or os.getcwd()
        self.setWindowTitle("📅 Calendar Notes")
        self.setMinimumSize(800, 550)

        layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Calendar
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setStyleSheet("""
            QCalendarWidget { background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: #e2e8f0; }
            QCalendarWidget QToolButton { color: #e2e8f0; font-weight: bold; }
            QCalendarWidget QToolButton:hover { background-color: rgba(99, 102, 241, 0.3); border-radius: 4px; }
        """)
        self.calendar.selectionChanged.connect(self._on_date_selected)
        splitter.addWidget(self.calendar)

        # Right panel
        right = QWidget()
        right_layout = QVBoxLayout(right)

        self.date_label = QLabel("Select a date")
        self.date_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #e2e8f0; padding: 5px;")
        right_layout.addWidget(self.date_label)

        self.notes_list = QListWidget()
        self.notes_list.setStyleSheet("""
            QListWidget { background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: #e2e8f0; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.05); }
            QListWidget::item:hover { background-color: rgba(51, 65, 85, 0.6); }
            QListWidget::item:selected { background-color: rgba(99, 102, 241, 0.6); color: white; }
        """)
        self.notes_list.itemDoubleClicked.connect(self._open_note)
        right_layout.addWidget(self.notes_list)

        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)
        right_layout.addWidget(self.preview)

        splitter.addWidget(right)
        splitter.setSizes([350, 450])
        layout.addWidget(splitter)

        # Scan folder for .md files
        self._file_dates: dict[QDate, list[str]] = {}
        self._scan_folder()

        # Bottom
        btn_row = QHBoxLayout()
        btn_rescan = QPushButton("🔄 Rescan Folder")
        btn_rescan.clicked.connect(self._scan_folder)
        btn_row.addWidget(btn_rescan)
        btn_row.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def _scan_folder(self):
        self._file_dates.clear()
        self.notes_list.clear()

        for root, dirs, files in os.walk(self.folder):
            for fname in files:
                if not fname.endswith(".md"):
                    continue
                fpath = os.path.join(root, fname)
                mtime = os.path.getmtime(fpath)
                date = QDate.fromDateTime(datetime.fromtimestamp(mtime))
                if date not in self._file_dates:
                    self._file_dates[date] = []
                self._file_dates[date].append(fpath)

            # Don't recurse into hidden dirs
            dirs[:] = [d for d in dirs if not d.startswith(".")]

        self._highlight_dates()

    def _highlight_dates(self):
        fmt = self.calendar.dateTextFormat(QDate.currentDate())
        for date in self._file_dates:
            self.calendar.setDateTextFormat(date, fmt)

    def _on_date_selected(self):
        date = self.calendar.selectedDate()
        self.date_label.setText(date.toString("dd MMMM yyyy"))
        self.notes_list.clear()

        files = self._file_dates.get(date, [])
        for fpath in sorted(files, key=os.path.getmtime, reverse=True):
            fname = os.path.basename(fpath)
            mtime = datetime.fromtimestamp(os.path.getmtime(fpath)).strftime("%H:%M")
            item = QListWidgetItem(f"📝 {fname}  ({mtime})")
            item.setData(Qt.ItemDataRole.UserRole, fpath)
            self.notes_list.addItem(item)

        if not files:
            self.notes_list.addItem(QListWidgetItem("No notes on this date"))
            self.preview.setHtml("")

    def _open_note(self, item: QListWidgetItem):
        fpath = item.data(Qt.ItemDataRole.UserRole)
        if fpath and os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()

            # Show first 3000 chars in preview
            preview_text = content[:3000]
            if len(content) > 3000:
                preview_text += "\n\n... (truncated)"

            self.preview.setHtml(f"<pre style='font-family: sans-serif; white-space: pre-wrap;'>{preview_text}</pre>")
