"""Диалоги анализа документа: читаемость, аудит, цитаты, облачные шаблоны.

``ReadabilityDashboardDialog``, ``DocumentAuditorDialog``,
``CitationManagerDialog``, ``CloudTemplatesDialog``. Выделено из
``src/gui/dialogs.py`` (TASK-011/PLAN-011), тела перенесены вербатим.
"""

import os
import re

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox,
    QListWidget, QListWidgetItem, QGroupBox, QSpinBox, QFormLayout,
    QDialogButtonBox, QLineEdit, QTextBrowser,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from src.gui.translations import TRANSLATIONS


class ReadabilityDashboardDialog(QDialog):
    def __init__(self, text: str, parent=None, lang="ru"):
        super().__init__(parent)
        t = lambda k: TRANSLATIONS[lang].get(k, k)
        self.setWindowTitle(t('dashboard_title'))
        self.setModal(True)
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)

        stats_group = QGroupBox(t('dashboard_stats_group'))
        stats_layout = QFormLayout(stats_group)

        words = text.split()
        char_count = len(text)
        char_no_spaces = len(text.replace(" ", "").replace("\n", "").replace("\r", ""))
        paragraphs = len([p for p in text.split('\n') if p.strip()])
        
        import re
        sentences = [s for s in re.split(r'[.!?]+', text) if s.strip()]
        total_sentences = max(len(sentences), 1)
        total_words = max(len(words), 1)
        
        unique_words = len(set(w.lower().strip(",.!?()") for w in words if w.strip()))
        avg_sentence = round(total_words / total_sentences, 1)
        
        score, level = estimate_readability(text, lang)

        stats_layout.addRow(t('stats_words').format(""), QLabel(str(total_words)))
        stats_layout.addRow(t('stats_chars').format(""), QLabel(str(char_count)))
        stats_layout.addRow(t('dashboard_lbl_paragraphs'), QLabel(str(paragraphs)))
        stats_layout.addRow(t('dashboard_lbl_sentences'), QLabel(str(len(sentences))))
        stats_layout.addRow(t('dashboard_lbl_unique_words'), QLabel(str(unique_words)))
        stats_layout.addRow(t('dashboard_lbl_avg_sentence'), QLabel(f"{avg_sentence} слов"))
        stats_layout.addRow(t('dashboard_lbl_readability'), QLabel(f"<b>{level}</b>"))
        stats_layout.addRow(t('dashboard_lbl_readability_desc'), QLabel(f"{score} / 100"))

        layout.addWidget(stats_group)

        density_group = QGroupBox(t('dashboard_density_group'))
        density_layout = QVBoxLayout(density_group)

        exclude = {"и", "в", "во", "на", "с", "со", "но", "а", "к", "у", "о", "об", "обо", "под", "над", "из", "до", "без", "для", "от", "the", "a", "an", "and", "or", "but", "to", "of", "in", "on", "at", "for", "with", "is", "are", "was", "were", "that", "this", "it"}
        words_cleaned = [w.lower().strip(",.!?()\"';:-*#`") for w in text.split() if w.strip()]
        words_filtered = [w for w in words_cleaned if w not in exclude and len(w) > 2]
        from collections import Counter
        top_5 = Counter(words_filtered).most_common(5)

        if top_5:
            for word, freq in top_5:
                density = round((freq / total_words) * 100, 1)
                density_layout.addWidget(QLabel(f"🔑 <b>{word}</b>: {freq} раз ({density}%)"))
        else:
            density_layout.addWidget(QLabel("—"))

        layout.addWidget(density_group)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.button_box.accepted.connect(self.accept)
        layout.addWidget(self.button_box)


class DocumentAuditorDialog(QDialog):
    def __init__(self, issues, parent=None, lang="ru"):
        super().__init__(parent)
        self.lang = lang
        self.issues = issues
        self.selected_line = None
        
        t = lambda k: TRANSLATIONS[lang].get(k, k)
        self.setWindowTitle(t('audit_dialog_title'))
        self.setMinimumSize(600, 400)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        if not issues:
            lbl = QLabel(t('audit_empty'))
            lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #10b981; padding: 20px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(lbl)
            
            self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
            self.button_box.accepted.connect(self.accept)
            layout.addWidget(self.button_box)
        else:
            from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
            from PyQt6.QtGui import QColor
            
            self.table = QTableWidget()
            self.table.setColumnCount(3)
            self.table.setHorizontalHeaderLabels([t('audit_col_line'), t('audit_col_type'), t('audit_col_desc')])
            self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
            self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            
            header = self.table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            
            self.table.setRowCount(len(issues))
            for idx, issue in enumerate(issues):
                item_line = QTableWidgetItem(str(issue["line"]))
                item_line.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(idx, 0, item_line)
                
                item_type = QTableWidgetItem(issue["type"])
                item_type.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                if "Struct" in issue["type"] or "Структур" in issue["type"]:
                    item_type.setForeground(QColor("#d35400"))
                elif "Typo" in issue["type"] or "Типограф" in issue["type"]:
                    item_type.setForeground(QColor("#2980b9"))
                else:
                    item_type.setForeground(QColor("#c0392b"))
                self.table.setItem(idx, 1, item_type)
                
                item_desc = QTableWidgetItem(issue["desc"])
                self.table.setItem(idx, 2, item_desc)
                
            self.table.doubleClicked.connect(self.on_row_double_clicked)
            layout.addWidget(self.table)
            
            lbl_tip = QLabel("💡 Дважды кликните на любую строку, чтобы мгновенно перейти к ней в редакторе." if lang == "ru" else "💡 Double-click any row to jump to that line in the editor.")
            lbl_tip.setStyleSheet("font-size: 11px; color: #94a3b8; padding-top: 5px;")
            layout.addWidget(lbl_tip)
            
            self.button_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Close
            )
            self.button_box.rejected.connect(self.reject)
            
            from PyQt6.QtWidgets import QPushButton
            self.btn_autofix = QPushButton(t('btn_audit_autofix'))
            self.btn_autofix.setStyleSheet("QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #059669,stop:1 #10b981); color: white; font-weight: bold; padding: 4px 10px; border: none; border-radius: 6px; } QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #047857,stop:1 #059669); }")
            self.btn_autofix.clicked.connect(self.on_autofix_clicked)
            self.button_box.addButton(self.btn_autofix, QDialogButtonBox.ButtonRole.ActionRole)
            
            layout.addWidget(self.button_box)
            
    def on_row_double_clicked(self, model_index):
        row = model_index.row()
        try:
            line_str = self.table.item(row, 0).text()
            self.selected_line = int(line_str)
            self.accept()
        except Exception:
            self.reject()

    def on_autofix_clicked(self):
        parent = self.parent()
        if parent and hasattr(parent, 'auto_fix_document_issues'):
            parent.auto_fix_document_issues()
        self.accept()


class CitationManagerDialog(QDialog):
    """Citation/bibliography manager."""

    def __init__(self, parent=None, lang="ru"):
        super().__init__(parent)
        self.lang = lang
        self.setWindowTitle("📚 Citation Manager")
        self.setMinimumSize(550, 420)

        from src.config import AppConfig
        self.citations_file = os.path.join(AppConfig.data_dir(), "citations.json")

        layout = QVBoxLayout(self)

        # Citation list
        self.citation_list = QListWidget()
        self.citation_list.setStyleSheet("""
            QListWidget { background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: #e2e8f0; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.05); }
            QListWidget::item:hover { background-color: rgba(51, 65, 85, 0.6); }
            QListWidget::item:selected { background-color: rgba(99, 102, 241, 0.6); color: white; }
        """)
        layout.addWidget(self.citation_list)

        self._refresh_list()

        # Add form
        form = QFormLayout()
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("e.g., smith2024")
        form.addRow("Key:", self.key_input)

        self.authors_input = QLineEdit()
        self.authors_input.setPlaceholderText("e.g., Smith, J.")
        form.addRow("Authors:", self.authors_input)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Paper title")
        form.addRow("Title:", self.title_input)

        self.year_input = QLineEdit()
        self.year_input.setPlaceholderText("2024")
        form.addRow("Year:", self.year_input)

        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Journal name (optional)")
        form.addRow("Source:", self.source_input)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://... (optional)")
        form.addRow("URL:", self.url_input)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Add Citation")
        btn_add.setStyleSheet("QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #059669,stop:1 #10b981); color: white; font-weight: bold; border: none; padding: 4px 12px; border-radius: 6px; } QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #047857,stop:1 #059669); }")
        btn_add.clicked.connect(self._add_citation)
        btn_layout.addWidget(btn_add)

        btn_remove = QPushButton("➖ Remove")
        btn_remove.clicked.connect(self._remove_citation)
        btn_layout.addWidget(btn_remove)

        btn_bib = QPushButton("📋 Generate Bibliography")
        btn_bib.setStyleSheet("QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2563eb,stop:1 #60a5fa); color: white; font-weight: bold; border: none; padding: 4px 12px; border-radius: 6px; } QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1d4ed8,stop:1 #2563eb); }")
        btn_bib.clicked.connect(self._generate_bibliography)
        btn_layout.addWidget(btn_bib)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _refresh_list(self):
        self.citation_list.clear()
        from src.core.citation_manager import get_citations
        for c in get_citations(self.citations_file):
            self.citation_list.addItem(f"[{c['key']}] {c['authors']} ({c['year']}) — {c['title']}")

    def _add_citation(self):
        key = self.key_input.text().strip()
        authors = self.authors_input.text().strip()
        title = self.title_input.text().strip()
        year = self.year_input.text().strip()
        if not key or not title:
            QMessageBox.warning(self, "Citation", "Key and Title are required")
            return
        from src.core.citation_manager import add_citation
        add_citation(self.citations_file, key, authors, title, year,
                     self.source_input.text().strip(), self.url_input.text().strip())
        self._refresh_list()
        self.key_input.clear()
        self.authors_input.clear()
        self.title_input.clear()
        self.year_input.clear()
        self.source_input.clear()
        self.url_input.clear()

    def _remove_citation(self):
        item = self.citation_list.currentItem()
        if not item:
            return
        text = item.text()
        key = text.split("]")[0].replace("[", "")
        from src.core.citation_manager import remove_citation
        remove_citation(self.citations_file, key)
        self._refresh_list()

    def _generate_bibliography(self):
        from src.core.citation_manager import generate_bibliography
        bib = generate_bibliography(self.citations_file)
        dlg = QDialog(self)
        dlg.setWindowTitle("Bibliography")
        dlg.setMinimumSize(500, 350)
        layout = QVBoxLayout(dlg)
        browser = QTextBrowser()
        browser.setHtml(bib.replace("\n", "<br>"))
        layout.addWidget(browser)
        btn = QPushButton("Close")
        btn.clicked.connect(dlg.close)
        layout.addWidget(btn)
        dlg.exec()


class CloudTemplatesDialog(QDialog):
    """Browse and download community Markdown templates."""
    def __init__(self, parent=None, lang="ru"):
        super().__init__(parent)
        self.lang = lang
        self.selected_content = None
        self.setWindowTitle("Облако шаблонов" if lang == "ru" else "Cloud Templates")
        self.setMinimumSize(600, 500)
        layout = QVBoxLayout(self)

        # Search
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск шаблонов..." if lang == "ru" else "Search templates...")
        self.search_input.textChanged.connect(self.filter_templates)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Template list
        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self.on_select)
        layout.addWidget(self.template_list)

        # Preview
        self.preview = QTextBrowser()
        self.preview.setMaximumHeight(200)
        layout.addWidget(self.preview)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_insert = QPushButton("Вставить" if lang == "ru" else "Insert")
        self.btn_insert.clicked.connect(self.insert_template)
        self.btn_insert.setStyleSheet("QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #059669,stop:1 #10b981); color: white; padding: 6px 16px; border: none; border-radius: 6px; } QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #047857,stop:1 #059669); }")
        btn_layout.addWidget(self.btn_insert)

        self.btn_refresh = QPushButton("🔄 Обновить")
        self.btn_refresh.clicked.connect(self.load_templates)
        btn_layout.addWidget(self.btn_refresh)

        btn_layout.addStretch()
        self.btn_close = QPushButton("Закрыть")
        self.btn_close.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

        self.templates = []
        self.load_templates()

    def load_templates(self):
        from src.core.cloud_templates import get_cloud_templates_index
        self.templates = get_cloud_templates_index(self.lang)
        self.refresh_list()

    def refresh_list(self):
        self.template_list.clear()
        for t in self.templates:
            item = QListWidgetItem(f"{t['name']}  [{', '.join(t.get('tags', []))}]")
            item.setData(Qt.ItemDataRole.UserRole, t)
            self.template_list.addItem(item)

    def filter_templates(self, text):
        for i in range(self.template_list.count()):
            item = self.template_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def on_select(self, current, previous):
        if current:
            t = current.data(Qt.ItemDataRole.UserRole)
            content = t.get('content', t.get('description', ''))
            escaped = content[:1000].replace('&', '&amp;').replace('<', '&lt;')
            self.preview.setHtml(f"<b>{t['name']}</b><br><pre>{escaped}</pre>")

    def insert_template(self):
        current = self.template_list.currentItem()
        if current:
            t = current.data(Qt.ItemDataRole.UserRole)
            self.selected_content = t.get('content', '')
            self.accept()


