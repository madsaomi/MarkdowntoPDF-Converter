import os
import re
import json
import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTextEdit, QMessageBox, QListWidget, QListWidgetItem, QFileDialog, QGroupBox,
    QSpinBox, QFormLayout, QDialogButtonBox, QComboBox, QColorDialog,
    QLineEdit, QTabWidget, QCheckBox, QWidget
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QTextBrowser
from src.gui.translations import TRANSLATIONS

logger = logging.getLogger("MarkdownToPDF.dialogs")

class GitHubSyncDialog(QDialog):
    """GitHub Sync dialog for push/pull/commit operations."""

    def __init__(self, parent=None, folder: str = "", lang="ru"):
        super().__init__(parent)
        self.lang = lang
        self.folder = folder
        self.setWindowTitle("🐙 GitHub Sync")
        self.setMinimumSize(520, 420)

        layout = QVBoxLayout(self)

        # Status
        self.status_label = QLabel(f"📁 {folder}")
        self.status_label.setStyleSheet("font-weight: bold; color: #e2e8f0; padding: 5px;")
        layout.addWidget(self.status_label)

        # Git status output
        self.status_output = QTextBrowser()
        self.status_output.setStyleSheet("font-family: monospace; font-size: 12px;")
        layout.addWidget(self.status_output)

        # Commit message
        msg_layout = QHBoxLayout()
        self.commit_input = QLineEdit()
        self.commit_input.setPlaceholderText("Commit message...")
        msg_layout.addWidget(self.commit_input)
        layout.addLayout(msg_layout)

        # Buttons
        btn_layout = QHBoxLayout()

        btn_status = QPushButton("🔄 Status")
        btn_status.clicked.connect(self._git_status)
        btn_layout.addWidget(btn_status)

        btn_init = QPushButton("📁 git init")
        btn_init.clicked.connect(self._git_init)
        btn_layout.addWidget(btn_init)

        btn_commit = QPushButton("✅ Commit All")
        btn_commit.setStyleSheet("QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #059669,stop:1 #10b981); color: white; font-weight: bold; border: none; padding: 4px 12px; border-radius: 6px; } QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #047857,stop:1 #059669); }")
        btn_commit.clicked.connect(self._git_commit)
        btn_layout.addWidget(btn_commit)

        btn_push = QPushButton("⬆ Push")
        btn_push.setStyleSheet("QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2563eb,stop:1 #60a5fa); color: white; font-weight: bold; border: none; padding: 4px 12px; border-radius: 6px; } QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1d4ed8,stop:1 #2563eb); }")
        btn_push.clicked.connect(self._git_push)
        btn_layout.addWidget(btn_push)

        btn_pull = QPushButton("⬇ Pull")
        btn_pull.clicked.connect(self._git_pull)
        btn_layout.addWidget(btn_pull)

        layout.addLayout(btn_layout)

        # Log
        btn_log = QPushButton("📜 Show Log")
        btn_log.clicked.connect(self._git_log)
        layout.addWidget(btn_log)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

        self._git_status()

    def _git_status(self):
        from src.core.github_sync import git_status, is_git_repo
        if not is_git_repo(self.folder):
            self.status_output.setHtml("<p style='color:#e74c3c;'>Not a git repository. Click 'git init' first.</p>")
            return
        status = git_status(self.folder)
        lines = [f"<b>Git Status:</b><br>"]
        if status["staged"]:
            lines.append(f"<span style='color:#27ae60;'>Staged:</span> {', '.join(status['staged'])}<br>")
        if status["modified"]:
            lines.append(f"<span style='color:#e67e22;'>Modified:</span> {', '.join(status['modified'])}<br>")
        if status["untracked"]:
            lines.append(f"<span style='color:#95a5a6;'>Untracked:</span> {', '.join(status['untracked'])}<br>")
        if not any([status["staged"], status["modified"], status["untracked"]]):
            lines.append("<span style='color:#27ae60;'>Working tree clean</span>")
        self.status_output.setHtml("".join(lines))

    def _git_init(self):
        from src.core.github_sync import git_init
        result = git_init(self.folder)
        if result["success"]:
            self.status_output.setHtml(f"<span style='color:#27ae60;'>✅ {result['output']}</span>")
        else:
            self.status_output.setHtml(f"<span style='color:#e74c3c;'>❌ {result.get('error', 'Failed')}</span>")

    def _git_commit(self):
        from src.core.github_sync import git_commit
        msg = self.commit_input.text().strip()
        if not msg:
            msg = "Update from MarkdownToPDF Converter"
        result = git_commit(self.folder, msg)
        if result["success"]:
            self.status_output.setHtml(f"<span style='color:#27ae60;'>✅ Committed: {msg}</span>")
        else:
            self.status_output.setHtml(f"<span style='color:#e74c3c;'>❌ {result.get('error', 'Failed')}</span>")
        self._git_status()

    def _git_push(self):
        from src.core.github_sync import git_push
        result = git_push(self.folder)
        if result["success"]:
            self.status_output.setHtml(f"<span style='color:#27ae60;'>✅ Pushed successfully</span>")
        else:
            self.status_output.setHtml(f"<span style='color:#e74c3c;'>❌ {result.get('error', 'Failed')}</span>")

    def _git_pull(self):
        from src.core.github_sync import git_pull
        result = git_pull(self.folder)
        if result["success"]:
            self.status_output.setHtml(f"<span style='color:#27ae60;'>✅ Pulled successfully</span>")
        else:
            self.status_output.setHtml(f"<span style='color:#e74c3c;'>❌ {result.get('error', 'Failed')}</span>")

    def _git_log(self):
        from src.core.github_sync import git_log
        commits = git_log(self.folder)
        if not commits:
            self.status_output.setHtml("No commits found")
            return
        lines = ["<b>Recent Commits:</b><br>"]
        for c in commits:
            lines.append(f"<code>{c['hash']}</code> {c['message']} <span style='color:#999'>({c['date'][:10]})</span><br>")
        self.status_output.setHtml("".join(lines))


class PluginManagerDialog(QDialog):
    """Plugin manager dialog."""

    def __init__(self, parent=None, lang="ru"):
        super().__init__(parent)
        self.lang = lang
        self.setWindowTitle("🧩 Plugin Manager")
        self.setMinimumSize(480, 360)

        layout = QVBoxLayout(self)

        info = QLabel("Plugins are loaded from the <code>plugins/</code> directory.")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.plugin_list = QListWidget()
        self.plugin_list.setStyleSheet("""
            QListWidget { background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: #e2e8f0; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.05); }
            QListWidget::item:hover { background-color: rgba(51, 65, 85, 0.6); }
            QListWidget::item:selected { background-color: rgba(99, 102, 241, 0.6); color: white; }
        """)
        layout.addWidget(self.plugin_list)

        self._refresh_list()

        btn_layout = QHBoxLayout()
        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.clicked.connect(self._refresh_list)
        btn_layout.addWidget(btn_refresh)

        btn_open_dir = QPushButton("📂 Open plugins/ folder")
        btn_open_dir.clicked.connect(self._open_plugins_dir)
        btn_layout.addWidget(btn_open_dir)

        btn_layout.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _refresh_list(self):
        self.plugin_list.clear()
        from src.core.plugin_system import get_all_plugins, get_all_hooks
        plugins = get_all_plugins()
        hooks = get_all_hooks()

        if plugins:
            for name, info in plugins.items():
                self.plugin_list.addItem(f"🔌 {name} v{info['version']} by {info['author']}")
        else:
            self.plugin_list.addItem("No plugins registered")

        self.plugin_list.addItem("---")
        for hook_name, handlers in hooks.items():
            self.plugin_list.addItem(f"🪝 {hook_name}: {len(handlers)} handler(s)")

    def _open_plugins_dir(self):
        import subprocess
        from src.config import AppConfig
        plugins_dir = os.path.join(AppConfig.base_path(), "plugins")
        os.makedirs(plugins_dir, exist_ok=True)
        subprocess.run(["explorer", os.path.normpath(plugins_dir)])


class MultiExportDialog(QDialog):
    """Dialog for selecting multiple export formats."""

    def __init__(self, parent=None, lang="ru"):
        super().__init__(parent)
        self.lang = lang
        self.setWindowTitle("📦 Multi-Export")
        self.setMinimumSize(380, 300)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Select formats to export:"))

        self.format_checks = {}
        formats = [("PDF", "pdf"), ("DOCX", "docx"), ("HTML", "html"), ("EPUB", "epub"), ("PPTX", "pptx"), ("PNG", "png"), ("JPG", "jpg")]
        for label, fmt in formats:
            from PyQt6.QtWidgets import QCheckBox
            chk = QCheckBox(label)
            if fmt == "pdf":
                chk.setChecked(True)
            self.format_checks[fmt] = chk
            layout.addWidget(chk)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Export")
        btn_ok.setStyleSheet("QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #059669,stop:1 #10b981); color: white; font-weight: bold; padding: 8px 16px; border: none; border-radius: 6px; } QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #047857,stop:1 #059669); }")
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.close)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        self.selected_formats = []

    def accept(self):
        self.selected_formats = [fmt for fmt, chk in self.format_checks.items() if chk.isChecked()]
        if not self.selected_formats:
            QMessageBox.warning(self, "Multi-Export", "Select at least one format")
            return
        super().accept()


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


class DocumentBuilderDialog(QDialog):
    def __init__(self, parent=None, lang="ru"):
        super().__init__(parent)
        self.parent_window = parent
        self.lang = lang
        t = lambda k, *a: TRANSLATIONS[lang].get(k, k).format(*a) if a else TRANSLATIONS[lang].get(k, k)
        self.t = t
        self.setWindowTitle(t('merge_dialog_title'))
        self.setModal(True)
        self.setMinimumSize(560, 480)

        layout = QVBoxLayout(self)

        # Book title
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel(t('merge_dialog_lbl_title')))
        self.book_title_input = QLineEdit()
        self.book_title_input.setPlaceholderText("My Book" if lang == "en" else "Моя Книга")
        title_layout.addWidget(self.book_title_input)
        layout.addLayout(title_layout)

        # File list label
        self.lbl = QLabel(t('merge_dialog_files_lbl'))
        layout.addWidget(self.lbl)

        # Content area: list + buttons
        content_layout = QHBoxLayout()
        self.list_widget = QListWidget()
        content_layout.addWidget(self.list_widget, stretch=4)

        btn_layout = QVBoxLayout()
        self.btn_add_folder = QPushButton(t('merge_dialog_btn_add_folder'))
        self.btn_add = QPushButton(t('merge_dialog_btn_add'))
        self.btn_remove = QPushButton(t('merge_dialog_btn_remove'))
        self.btn_up = QPushButton(t('merge_dialog_btn_up'))
        self.btn_down = QPushButton(t('merge_dialog_btn_down'))

        self.btn_add_folder.clicked.connect(self.add_folder)
        self.btn_add.clicked.connect(self.add_files)
        self.btn_remove.clicked.connect(self.remove_file)
        self.btn_up.clicked.connect(self.move_up)
        self.btn_down.clicked.connect(self.move_down)

        self.btn_add_folder.setStyleSheet("""
            QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2563eb,stop:1 #60a5fa); color: white; font-weight: bold; padding: 8px; border: none; border-radius: 6px; }
            QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1d4ed8,stop:1 #2563eb); }
        """)

        btn_layout.addWidget(self.btn_add_folder)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.btn_up)
        btn_layout.addWidget(self.btn_down)

        content_layout.addLayout(btn_layout, stretch=1)
        layout.addLayout(content_layout)

        # Options
        from PyQt6.QtWidgets import QCheckBox
        opts_layout = QHBoxLayout()
        self.chk_toc = QCheckBox(t('merge_dialog_chk_toc'))
        self.chk_toc.setChecked(True)
        self.chk_pagebreak = QCheckBox(t('merge_dialog_chk_pagebreak'))
        self.chk_pagebreak.setChecked(True)
        self.chk_pagenum = QCheckBox(t('merge_dialog_chk_pagenum'))
        self.chk_pagenum.setChecked(True)
        opts_layout.addWidget(self.chk_toc)
        opts_layout.addWidget(self.chk_pagebreak)
        opts_layout.addWidget(self.chk_pagenum)
        layout.addLayout(opts_layout)

        # Build button
        self.btn_build = QPushButton(t('merge_dialog_btn_build'))
        self.btn_build.setStyleSheet("""
            QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #059669,stop:1 #10b981); color: white; font-weight: bold; padding: 12px; border: none; border-radius: 8px; font-size: 14px; }
            QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #047857,stop:1 #059669); }
        """)
        self.btn_build.clicked.connect(self.build_merged_document)
        layout.addWidget(self.btn_build)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Выберите папку с заметками" if self.lang == "ru" else "Select notes folder"
        )
        if not folder:
            return
        self.load_folder(folder)

    def load_folder(self, folder: str):
        md_files = []
        for root, dirs, files in os.walk(folder):
            dirs.sort()
            for fname in sorted(files):
                if fname.lower().endswith('.md'):
                    md_files.append(os.path.join(root, fname))
        if not md_files:
            QMessageBox.warning(self, "!", self.t('msg_folder_empty'))
            return
        for f in md_files:
            self.list_widget.addItem(os.path.abspath(f))
        if self.parent_window:
            self.parent_window.append_log(self.t('merge_dialog_found_files', len(md_files)))

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Markdown files", "", "Markdown files (*.md)"
        )
        if files:
            for f in files:
                self.list_widget.addItem(os.path.abspath(f))

    def remove_file(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            self.list_widget.takeItem(row)

    def move_up(self):
        row = self.list_widget.currentRow()
        if row > 0:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row - 1, item)
            self.list_widget.setCurrentRow(row - 1)

    def move_down(self):
        row = self.list_widget.currentRow()
        if row >= 0 and row < self.list_widget.count() - 1:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row + 1, item)
            self.list_widget.setCurrentRow(row + 1)

    def build_merged_document(self):
        count = self.list_widget.count()
        if count == 0:
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить книгу PDF" if self.lang == "ru" else "Save Book PDF",
            "",
            "PDF files (*.pdf)"
        )
        if not save_path:
            return

        self.parent_window.log_output.clear()
        self.parent_window.append_log(f"\n📚 Building book ({count} chapters) → {save_path}")

        try:
            import re as _re

            book_title = self.book_title_input.text().strip()
            add_toc = self.chk_toc.isChecked()
            add_pagebreak = self.chk_pagebreak.isChecked()

            # ── Collect all chapters ──
            chapters = []  # list of (chapter_title, md_content, base_dir)
            for i in range(count):
                filepath = self.list_widget.item(i).text()
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                # Extract chapter title from first H1, or fallback to filename
                h1_match = _re.search(r'^#\s+(.+)', content, _re.MULTILINE)
                title = h1_match.group(1).strip() if h1_match else os.path.splitext(os.path.basename(filepath))[0]
                base_dir = os.path.dirname(os.path.abspath(filepath))
                chapters.append((title, content, base_dir))
                self.parent_window.append_log(f"  📖 Chapter {i+1}: {title}")

            # ── Build merged markdown ──
            merged_md = ""

            # Title page
            if book_title:
                merged_md += f"# {book_title}\n\n"

            # Auto-generated Table of Contents
            if add_toc:
                toc_title = "## Оглавление\n\n" if self.lang == "ru" else "## Table of Contents\n\n"
                merged_md += toc_title
                for idx, (title, _, _) in enumerate(chapters, 1):
                    anchor = _re.sub(r'[^\w\s-]', '', title.lower()).strip().replace(' ', '-')
                    merged_md += f"{idx}. [{title}](#{anchor})\n"
                merged_md += "\n"
                if add_pagebreak:
                    merged_md += '\n<div style="page-break-before: always;"></div>\n\n'

            # Append each chapter
            for idx, (title, content, base_dir) in enumerate(chapters):
                if add_pagebreak and idx > 0:
                    merged_md += '\n<div style="page-break-before: always;"></div>\n\n'
                merged_md += content
                merged_md += "\n\n"

            # Disable build button
            self.btn_build.setEnabled(False)
            self.btn_build.setText("Сборка..." if self.lang == "ru" else "Building...")

            from src.gui.threads import BookBuilderThread
            
            template_dir = self.parent_window._get_template_dir()
            wp_exe = self.parent_window._get_weasyprint_path()
            first_base = chapters[0][2] if chapters else "."
            kroki = getattr(self.parent_window, 'kroki_available', True)
            
            doc_theme = self.parent_window.doc_theme_combo.currentData() or 'theme_modern.css'
            code_theme = self.parent_window.code_theme_combo.currentData() or 'pygments.css'
            paper_size = self.parent_window.paper_combo.currentText() or 'A4'
            watermark = self.parent_window.watermark_input.text()
            footer = self.parent_window.footer_input.text()
            custom_css = self.parent_window.custom_css_input.text()
            margins = self.parent_window.margins_input.text()
            password = self.parent_window.pdf_password_input.text()
            
            self._book_thread = BookBuilderThread(
                merged_md=merged_md,
                base_dir=first_base,
                save_path=save_path,
                book_title=book_title,
                template_dir=template_dir,
                wp_executable=wp_exe,
                doc_theme=doc_theme,
                code_theme=code_theme,
                paper_size=paper_size,
                watermark=watermark,
                footer=footer,
                custom_css=custom_css,
                margins=margins,
                password=password,
                page_numbers=self.chk_pagenum.isChecked(),
                lang=self.lang,
                kroki_available=kroki
            )
            
            def on_log(msg):
                self.parent_window.append_log(msg)
                
            def on_finished(success, result_msg):
                self.btn_build.setEnabled(True)
                self.btn_build.setText("📖 Собрать книгу в PDF 🚀" if self.lang == "ru" else "📖 Build Book as PDF 🚀")
                if success:
                    self.parent_window.append_log(f"\n✅ Книга собрана успешно! ({count} глав)" if self.lang == "ru" else f"\n✅ Book built successfully! ({count} chapters)")
                    self.parent_window.add_to_export_history(result_msg)
                    self.parent_window.update_export_history_ui()
                    QMessageBox.information(
                        self,
                        "Готово!" if self.lang == "ru" else "Done!",
                        (f"Книга собрана!\nГлав: {count}\nСохранено: {result_msg}" if self.lang == "ru"
                         else f"Book built!\nChapters: {count}\nSaved to: {result_msg}")
                    )
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error", f"Failed to build book:\n{result_msg}")
            
            self._book_thread.log.connect(on_log)
            self._book_thread.finished_task.connect(on_finished)
            self._book_thread.start()
            
        except Exception as e:
            self.parent_window.append_log(f"  ❌ Error: {e}")
            QMessageBox.critical(self, "Error", f"Failed to setup book builder:\n{e}")
            import traceback
            traceback.print_exc()


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


class MarkdownTOCDialog(QDialog):
    def __init__(self, parent=None, lang="ru"):
        super().__init__(parent)
        t = lambda k: TRANSLATIONS[lang].get(k, k)
        
        self.setWindowTitle(t('toc_dialog_title'))
        self.setMinimumWidth(380)
        self.setModal(True)
        
        from PyQt6.QtWidgets import QFormLayout, QComboBox, QCheckBox, QDialogButtonBox
        layout = QFormLayout(self)
        
        self.depth_combo = QComboBox()
        self.depth_combo.addItem("H1", 1)
        self.depth_combo.addItem("H1 - H2", 2)
        self.depth_combo.addItem("H1 - H3", 3)
        self.depth_combo.setCurrentIndex(1)
        layout.addRow(t('toc_lbl_depth'), self.depth_combo)
        
        self.style_combo = QComboBox()
        self.style_combo.addItem(t('toc_style_bullet'), "bullet")
        self.style_combo.addItem(t('toc_style_numbered'), "numbered")
        layout.addRow(t('toc_lbl_style'), self.style_combo)
        
        self.anchors_chk = QCheckBox(t('toc_lbl_anchors'))
        self.anchors_chk.setChecked(True)
        layout.addRow("", self.anchors_chk)
        
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        if lang == "ru":
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Сгенерировать")
        else:
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Generate")
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(t('theme_builder_btn_cancel'))
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        layout.addRow(self.button_box)


class SnippetsDialog(QDialog):
    def __init__(self, parent=None, lang="ru"):
        super().__init__(parent)
        t = lambda k: TRANSLATIONS[lang].get(k, k)
        self.setWindowTitle(t('snippet_dialog_title'))
        self.setModal(True)
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        
        # Add snippets to the list
        self.snippets = {
            t('snippet_chk_list'): "- [ ] Шаг 1\n- [ ] Шаг 2\n- [ ] Шаг 3\n",
            t('snippet_callout_note'): "> [!NOTE]\n> Это информационная плашка с важным примечанием.\n",
            t('snippet_callout_warning'): "> [!WARNING]\n> Это предупреждающая плашка! Будьте аккуратны.\n",
            t('snippet_code_python'): "```python\ndef hello_world():\n    print(\"Hello World!\")\n\nhello_world()\n```\n",
            t('snippet_table'): "| Заголовок 1 | Заголовок 2 |\n| ----------- | ----------- |\n| Ячейка 1    | Ячейка 2    |\n| Ячейка 3    | Ячейка 4    |\n",
            t('snippet_image'): "![Описание картинки](https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600)\n*Подпись под изображением*\n"
        }

        for key in self.snippets.keys():
            self.list_widget.addItem(key)

        layout.addWidget(self.list_widget)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(t('theme_builder_btn_save'))
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(t('theme_builder_btn_cancel'))
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout.addWidget(self.button_box)

    def get_selected_snippet(self) -> str:
        current_item = self.list_widget.currentItem()
        if current_item:
            return self.snippets.get(current_item.text(), "")
        return ""


# ─── Table Generator Dialog ───

class MarkdownTableDialog(QDialog):
    def __init__(self, parent=None, lang="ru"):
        super().__init__(parent)
        t = lambda k: TRANSLATIONS[lang].get(k, k)
        self.setWindowTitle(t('table_gen_title'))
        self.setModal(True)
        self.setMinimumWidth(300)

        layout = QFormLayout(self)
        
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 50)
        self.rows_spin.setValue(3)
        
        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 20)
        self.cols_spin.setValue(3)
        
        layout.addRow(t('table_gen_rows'), self.rows_spin)
        layout.addRow(t('table_gen_cols'), self.cols_spin)
        
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(t('table_gen_btn'))
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(t('table_gen_cancel'))
        
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        layout.addRow(self.button_box)





# ─── Custom Theme Builder Dialog ───

from PyQt6.QtWidgets import QDialog, QFormLayout, QPushButton, QComboBox, QDialogButtonBox, QColorDialog
from PyQt6.QtGui import QColor

class ColorButton(QPushButton):
    def __init__(self, color_hex="#ffffff", parent=None):
        super().__init__(parent)
        self.color = QColor(color_hex)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_style()
        self.clicked.connect(self.choose_color)

    def update_style(self):
        self.setStyleSheet(f"background-color: {self.color.name()}; border: 1px solid rgba(255,255,255,0.15); border-radius: 6px; height: 24px;")

    def choose_color(self):
        dlg = QColorDialog(self.color, self)
        if dlg.exec() == QColorDialog.DialogCode.Accepted:
            self.color = dlg.selectedColor()
            self.update_style()


class PDFStyleEditorDialog(QDialog):
    def __init__(self, parent=None, lang="ru"):
        super().__init__(parent)
        self.lang = lang
        t = lambda k: TRANSLATIONS[lang].get(k, k)
        
        self.setWindowTitle(t('style_dialog_title'))
        self.setMinimumSize(420, 360)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Tabs
        self.tabs = QTabWidget()
        
        # Tab 1: Layout
        self.tab_layout = QWidget()
        self.init_layout_tab(t)
        self.tabs.addTab(self.tab_layout, t('style_tab_layout'))
        
        # Tab 2: Typography
        self.tab_typography = QWidget()
        self.init_typography_tab(t)
        self.tabs.addTab(self.tab_typography, t('style_tab_typography'))
        
        # Tab 3: Colors
        self.tab_colors = QWidget()
        self.init_colors_tab(t)
        self.tabs.addTab(self.tab_colors, t('style_tab_colors'))
        
        layout.addWidget(self.tabs)
        
        # OK / Cancel Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(t('theme_builder_btn_save'))
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(t('theme_builder_btn_cancel'))
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
    def init_layout_tab(self, t):
        lay = QFormLayout(self.tab_layout)
        
        # Margins (Top, Right, Bottom, Left)
        self.margin_top = QSpinBox()
        self.margin_top.setRange(0, 100)
        self.margin_top.setValue(20)
        self.margin_top.setSuffix(" mm")
        
        self.margin_right = QSpinBox()
        self.margin_right.setRange(0, 100)
        self.margin_right.setValue(20)
        self.margin_right.setSuffix(" mm")
        
        self.margin_bottom = QSpinBox()
        self.margin_bottom.setRange(0, 100)
        self.margin_bottom.setValue(20)
        self.margin_bottom.setSuffix(" mm")
        
        self.margin_left = QSpinBox()
        self.margin_left.setRange(0, 100)
        self.margin_left.setValue(20)
        self.margin_left.setSuffix(" mm")
        
        lay.addRow(t('style_lbl_margins'), QLabel(""))
        lay.addRow("  Top (Верхнее):", self.margin_top)
        lay.addRow("  Right (Правое):", self.margin_right)
        lay.addRow("  Bottom (Нижнее):", self.margin_bottom)
        lay.addRow("  Left (Левое):", self.margin_left)
        
        # Paper preset
        self.paper_combo = QComboBox()
        self.paper_combo.addItems(["A4", "Letter", "A5"])
        lay.addRow(t('label_paper_size'), self.paper_combo)
        
    def init_typography_tab(self, t):
        lay = QFormLayout(self.tab_typography)
        
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Inter", "Outfit", "Arial", "Times New Roman", "Georgia", "Courier New"])
        lay.addRow(t('style_lbl_font'), self.font_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 36)
        self.font_size_spin.setValue(14)
        self.font_size_spin.setSuffix(" px")
        lay.addRow(t('style_lbl_font_size'), self.font_size_spin)
        
        self.line_height_combo = QComboBox()
        self.line_height_combo.addItems(["1.0", "1.15", "1.3", "1.5", "1.8", "2.0"])
        self.line_height_combo.setCurrentText("1.5")
        lay.addRow(t('style_lbl_line_height'), self.line_height_combo)
        
        self.align_combo = QComboBox()
        self.align_combo.addItem(t('style_align_justify'), "justify")
        self.align_combo.addItem(t('style_align_left'), "left")
        lay.addRow(t('style_lbl_align'), self.align_combo)
        
    def init_colors_tab(self, t):
        lay = QFormLayout(self.tab_colors)
        
        self.h_color_btn = ColorButton("#2c3e50", self)
        lay.addRow(t('style_lbl_color_h1'), self.h_color_btn)
        
        self.quote_color_btn = ColorButton("#16a085", self)
        lay.addRow(t('style_lbl_color_quote'), self.quote_color_btn)
        
        self.code_bg_btn = ColorButton("#f1f2f6", self)
        lay.addRow(t('style_lbl_color_code'), self.code_bg_btn)


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


class SnippetsManagerDialog(QDialog):
    """Code snippets library manager."""
    def __init__(self, parent=None, lang="ru"):
        super().__init__(parent)
        self.lang = lang
        self.selected_code = None
        self.setWindowTitle("Библиотека сниппетов" if lang == "ru" else "Snippet Library")
        self.setMinimumSize(600, 500)
        layout = QVBoxLayout(self)

        from src.core.snippets import SnippetLibrary
        self.library = SnippetLibrary()

        # Search
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск..." if lang == "ru" else "Search...")
        self.search_input.textChanged.connect(self.filter_snippets)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Snippet list
        self.snippet_list = QListWidget()
        self.snippet_list.currentItemChanged.connect(self.on_select)
        layout.addWidget(self.snippet_list)

        # Preview
        self.preview = QTextBrowser()
        self.preview.setMaximumHeight(200)
        layout.addWidget(self.preview)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_insert = QPushButton("Вставить" if lang == "ru" else "Insert")
        self.btn_insert.clicked.connect(self.insert_snippet)
        self.btn_insert.setStyleSheet("QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #059669,stop:1 #10b981); color: white; padding: 6px 16px; border: none; border-radius: 6px; } QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #047857,stop:1 #059669); }")
        btn_layout.addWidget(self.btn_insert)

        self.btn_add = QPushButton("Добавить текущий код")
        self.btn_add.clicked.connect(self.add_current_code)
        btn_layout.addWidget(self.btn_add)

        self.btn_delete = QPushButton("Удалить")
        self.btn_delete.clicked.connect(self.delete_snippet)
        btn_layout.addWidget(self.btn_delete)

        btn_layout.addStretch()
        self.btn_close = QPushButton("Закрыть")
        self.btn_close.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

        self.refresh_list()

    def refresh_list(self):
        self.snippet_list.clear()
        for s in self.library.get_all():
            item = QListWidgetItem(f"[{s.language}] {s.name}")
            item.setData(Qt.ItemDataRole.UserRole, s)
            self.snippet_list.addItem(item)

    def filter_snippets(self, text):
        for i in range(self.snippet_list.count()):
            item = self.snippet_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def on_select(self, current, previous):
        if current:
            snippet = current.data(Qt.ItemDataRole.UserRole)
            escaped = snippet.code.replace('&', '&amp;').replace('<', '&lt;')
            self.preview.setHtml(f"<b>{snippet.name}</b> ({snippet.language})<br><pre>{escaped}</pre>")

    def insert_snippet(self):
        current = self.snippet_list.currentItem()
        if current:
            snippet = current.data(Qt.ItemDataRole.UserRole)
            self.selected_code = snippet.code
            self.accept()

    def add_current_code(self):
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Имя сниппета", "Название:")
        if ok and name:
            lang, ok2 = QInputDialog.getText(self, "Язык", "Язык (python, js, html...):")
            if ok2 and lang:
                code = self.parent().live_editor.textCursor().selectedText() if self.parent() else ""
                if not code:
                    code = self.parent().live_editor.toPlainText()[:500] if self.parent() else ""
                self.library.add(name, lang, code)
                self.refresh_list()

    def delete_snippet(self):
        current = self.snippet_list.currentItem()
        if current:
            row = self.snippet_list.row(current)
            self.library.remove(row)
            self.refresh_list()


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


class ShortcutsDialog(QDialog):
    """Glassmorphism keyboard shortcuts overlay."""

    SHORTCUTS = [
        ("Ctrl+N", "Новый файл / New file"),
        ("Ctrl+O", "Открыть файл / Open file"),
        ("Ctrl+S", "Сохранить / Save"),
        ("Ctrl+Shift+S", "Сохранить как / Save as"),
        ("Ctrl+Z", "Отменить / Undo"),
        ("Ctrl+Y", "Повторить / Redo"),
        ("Ctrl+F", "Поиск и замена / Search & Replace"),
        ("Ctrl+H", "Замена / Replace"),
        ("Ctrl+P", "Печать / Print"),
        ("Ctrl+B", "Жирный / Bold"),
        ("Ctrl+I", "Курсив / Italic"),
        ("Ctrl+K", "Ссылка / Link"),
        ("Ctrl+Shift+K", "Код / Code"),
        ("Ctrl+Shift+Q", "Цитата / Quote"),
        ("Ctrl+Shift+L", "Список / List"),
        ("Ctrl+Shift+X", "Зачёркнутый / Strikethrough"),
        ("Ctrl+E", "Эмодзи / Emoji"),
        ("Ctrl+=", "Zoom in"),
        ("Ctrl+-", "Zoom out"),
        ("Ctrl+0", "Сброс зума / Reset zoom"),
        ("Ctrl+M", "Мерmaid / Mermaid"),
        ("Ctrl+D", "Диаграмма / Diagram"),
        ("Ctrl+Tab", "Следующая вкладка / Next tab"),
        ("F11", "Zen режим / Zen mode"),
        ("Ctrl+Shift+F", "Фокус / Focus mode"),
    ]

    def __init__(self, parent=None, lang="ru"):
        super().__init__(parent)
        self.setWindowTitle("⌨️ Shortcuts" if lang == "en" else "⌨️ Горячие клавиши")
        self.setMinimumSize(520, 480)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("⌨️ Горячие клавиши" if lang == "ru" else "⌨️ Keyboard Shortcuts")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #e2e8f0; border: none;")
        layout.addWidget(title)

        html_parts = ['<table style="width:100%; border-collapse:collapse; font-size:13px;">']
        for i, (key, desc) in enumerate(self.SHORTCUTS):
            bg = "rgba(51, 65, 85, 0.3)" if i % 2 == 0 else "transparent"
            html_parts.append(
                f'<tr style="background:{bg};">'
                f'<td style="padding:8px 12px; border-bottom:1px solid rgba(255,255,255,0.05);">'
                f'<kbd style="background:rgba(99,102,241,0.2); color:#a5b4fc; padding:3px 8px; '
                f'border-radius:4px; font-family:monospace; font-size:12px;">{key}</kbd></td>'
                f'<td style="padding:8px 12px; color:#cbd5e1; border-bottom:1px solid rgba(255,255,255,0.05);">{desc}</td>'
                f'</tr>'
            )
        html_parts.append('</table>')

        browser = QTextBrowser()
        browser.setHtml(''.join(html_parts))
        browser.setStyleSheet("""
            QTextBrowser { background: transparent; border: none; color: #e2e8f0; }
        """)
        layout.addWidget(browser)

        btn_close = QPushButton("Закрыть" if lang == "ru" else "Close")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton { background: rgba(99, 102, 241, 0.5); color: white; padding: 8px 20px;
                          border: none; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background: rgba(99, 102, 241, 0.7); }
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)



