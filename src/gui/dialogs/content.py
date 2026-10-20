"""Диалоги работы с содержимым: конструктор книги, TOC, таблицы, сниппеты.

``DocumentBuilderDialog``, ``MarkdownTOCDialog``, ``MarkdownTableDialog``,
``SnippetsDialog``, ``SnippetsManagerDialog``. Выделено из
``src/gui/dialogs.py`` (TASK-011/PLAN-011), тела перенесены вербатим.
"""

import os

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox,
    QListWidget, QListWidgetItem, QFileDialog, QSpinBox, QFormLayout,
    QDialogButtonBox, QComboBox, QLineEdit, QCheckBox, QTextBrowser,
)
from PyQt6.QtCore import Qt
from src.gui.translations import TRANSLATIONS


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


