"""Диалоги версий: история ревизий и сравнение (diff).

``RevisionHistoryDialog``, ``DiffDialog``. Выделено из
``src/gui/dialogs.py`` (TASK-011/PLAN-011), тела перенесены вербатим.
"""

import os
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox,
    QListWidget, QListWidgetItem, QFileDialog, QDialogButtonBox, QLineEdit,
    QTextBrowser,
)
from PyQt6.QtCore import Qt

from src.gui.translations import TRANSLATIONS


class RevisionHistoryDialog(QDialog):
    def __init__(self, file_backup_dir, parent=None, lang="ru"):
        super().__init__(parent)
        self.lang = lang
        self.file_backup_dir = file_backup_dir
        self.selected_content = None
        
        t = lambda k: TRANSLATIONS[lang].get(k, k)
        self.setWindowTitle(t('history_dialog_title'))
        self.setMinimumSize(650, 450)
        self.setModal(True)
        
        main_layout = QVBoxLayout(self)
        
        # Splitter-like layout for list and preview
        content_layout = QHBoxLayout()
        
        # Left: List of versions
        self.list_widget = QListWidget()
        self.list_widget.setFixedWidth(240)
        self.list_widget.currentItemChanged.connect(self.on_item_changed)
        content_layout.addWidget(self.list_widget)
        
        # Right: Preview
        self.preview_browser = QTextBrowser()
        self.preview_browser.setPlaceholderText(t('history_empty'))
        content_layout.addWidget(self.preview_browser)
        
        main_layout.addLayout(content_layout)
        
        # Bottom controls
        self.button_box = QDialogButtonBox()
        self.btn_restore = self.button_box.addButton(t('history_btn_restore'), QDialogButtonBox.ButtonRole.AcceptRole)
        self.btn_restore.setEnabled(False)
        self.btn_restore.setStyleSheet("""
            QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #059669,stop:1 #10b981); color: white; font-weight: bold; padding: 6px 15px; border: none; border-radius: 6px; }
            QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #047857,stop:1 #059669); }
            QPushButton:disabled { background: rgba(100, 116, 139, 0.4); color: #94a3b8; }
        """)
        
        self.btn_cancel = self.button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        self.btn_cancel.setText(TRANSLATIONS[lang].get('theme_builder_btn_cancel', 'Cancel'))
        
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        main_layout.addWidget(self.button_box)
        
        self.load_revisions()
        
    def load_revisions(self):
        if not os.path.exists(self.file_backup_dir):
            return
            
        backups = sorted(os.listdir(self.file_backup_dir), reverse=True)
        for b in backups:
            if not b.endswith('.md'):
                continue
            parts = b.replace('.md', '').split('_')
            if len(parts) >= 3:
                # Format: YYYYMMDD_HHMMSS_words
                date_str, time_str, words = parts[0], parts[1], parts[2]
                try:
                    dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                    display_time = dt.strftime("%d.%m.%Y %H:%M:%S")
                except Exception:
                    display_time = b
                words_lbl = f" ({words} сл.)" if self.lang == "ru" else f" ({words} words)"
                label = f"{display_time}{words_lbl}"
            else:
                label = b
                
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, os.path.join(self.file_backup_dir, b))
            self.list_widget.addItem(item)
            
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
            
    def on_item_changed(self, current, previous):
        if not current:
            self.preview_browser.clear()
            self.btn_restore.setEnabled(False)
            self.selected_content = None
            return
            
        filepath = current.data(Qt.ItemDataRole.UserRole)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                self.selected_content = f.read()
            self.preview_browser.setPlainText(self.selected_content)
            self.btn_restore.setEnabled(True)
        except Exception as e:
            self.preview_browser.setHtml(f"<p style='color:red;'>Error loading preview: {e}</p>")
            self.btn_restore.setEnabled(False)
            self.selected_content = None


class DiffDialog(QDialog):
    """Side-by-side diff viewer for two Markdown files."""
    def __init__(self, parent=None, lang="ru"):
        super().__init__(parent)
        self.lang = lang
        self.setWindowTitle("Сравнение документов" if lang == "ru" else "Compare Documents")
        self.setMinimumSize(900, 600)
        layout = QVBoxLayout(self)

        # File selection
        file_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Файл A:" if lang == "ru" else "File A:"))
        self.left_path = QLineEdit()
        self.left_path.setReadOnly(True)
        left_layout.addWidget(self.left_path)
        self.btn_left = QPushButton("Обзор...")
        self.btn_left.clicked.connect(lambda: self._select_file('left'))
        left_layout.addWidget(self.btn_left)
        file_layout.addLayout(left_layout)

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Файл B:" if lang == "ru" else "File B:"))
        self.right_path = QLineEdit()
        self.right_path.setReadOnly(True)
        right_layout.addWidget(self.right_path)
        self.btn_right = QPushButton("Обзор...")
        self.btn_right.clicked.connect(lambda: self._select_file('right'))
        right_layout.addWidget(self.btn_right)
        file_layout.addLayout(right_layout)
        layout.addLayout(file_layout)

        # Compare button
        self.btn_compare = QPushButton("Сравнить" if lang == "ru" else "Compare")
        self.btn_compare.clicked.connect(self.do_compare)
        self.btn_compare.setStyleSheet("QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2563eb,stop:1 #60a5fa); color: white; padding: 6px 16px; font-weight: bold; border: none; border-radius: 6px; } QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1d4ed8,stop:1 #2563eb); }")
        layout.addWidget(self.btn_compare)

        # Diff output
        self.diff_browser = QTextBrowser()
        self.diff_browser.setOpenExternalLinks(False)
        layout.addWidget(self.diff_browser)

        # Stats
        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)

        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

    def _select_file(self, side):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите Markdown файл", "",
            "Markdown (*.md);;All Files (*)"
        )
        if path:
            if side == 'left':
                self.left_path.setText(path)
            else:
                self.right_path.setText(path)

    def do_compare(self):
        left = self.left_path.text()
        right = self.right_path.text()
        if not left or not right:
            QMessageBox.warning(self, "Ошибка", "Выберите оба файла для сравнения")
            return

        try:
            with open(left, 'r', encoding='utf-8') as f:
                left_lines = f.readlines()
            with open(right, 'r', encoding='utf-8') as f:
                right_lines = f.readlines()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка чтения файлов: {e}")
            return

        import difflib
        diff = list(difflib.unified_diff(
            left_lines, right_lines,
            fromfile=os.path.basename(left),
            tofile=os.path.basename(right),
            lineterm=''
        ))

        if not diff:
            self.diff_browser.setHtml("<p style='color: green; font-size: 14px;'>✅ Файлы идентичны</p>")
            self.stats_label.setText("Файлы идентичны")
            return

        # Build HTML diff
        html_parts = ['<pre style="font-family: monospace; font-size: 12px; padding: 10px;">']
        added = removed = 0
        for line in diff:
            escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            if line.startswith('+++') or line.startswith('---'):
                html_parts.append(f'<span style="font-weight: bold; color: #3498db;">{escaped}</span>')
            elif line.startswith('@@'):
                html_parts.append(f'<span style="color: #9b59b6; font-weight: bold;">{escaped}</span>')
            elif line.startswith('+'):
                added += 1
                html_parts.append(f'<span style="background: #d5f5e3; color: #27ae60;">{escaped}</span>')
            elif line.startswith('-'):
                removed += 1
                html_parts.append(f'<span style="background: #fadbd8; color: #e74c3c;">{escaped}</span>')
            else:
                html_parts.append(escaped)
        html_parts.append('</pre>')

        self.diff_browser.setHtml('\n'.join(html_parts))
        self.stats_label.setText(f"Добавлено: {added} | Удалено: {removed}")


