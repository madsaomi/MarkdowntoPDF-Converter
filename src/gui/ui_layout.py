from PyQt6.QtWidgets import (
    QFormLayout, QCheckBox,
    QDialog, QDialogButtonBox,
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, 
    QProgressBar, QComboBox, QLineEdit, QGroupBox, QGridLayout, QMenu,
    QTabWidget, QTextBrowser
)
from PyQt6.QtCore import Qt


def setup_ui(window):
    # ── Menu bar ──
    menubar = window.menuBar()
    file_menu = menubar.addMenu("Файл")

    window.recent_menu = QMenu("🕐 Недавние файлы", window)
    file_menu.addMenu(window.recent_menu)

    window.action_export_selection = file_menu.addAction("📋 Экспорт выделенного")
    window.action_export_selection.setShortcut("Ctrl+Shift+E")
    window.action_export_selection.triggered.connect(window.export_selection)

    window.action_export_md = file_menu.addAction("💾 Сохранить как .md")
    window.action_export_md.setShortcut("Ctrl+Shift+S")
    window.action_export_md.triggered.connect(window.export_as_markdown)

    window.action_history = file_menu.addAction("📜 История конвертаций")
    window.action_history.setShortcut("Ctrl+H")
    window.action_history.triggered.connect(window.show_conversion_history)

    # Tools Menu
    window.tools_menu = menubar.addMenu("🛠️ Инструменты" if window.current_lang == "ru" else "🛠️ Tools")
    window.action_update_toc = window.tools_menu.addAction("🔄 Обновить оглавление" if window.current_lang == "ru" else "🔄 Update TOC")
    window.action_update_toc.setShortcut("Ctrl+Shift+T")
    window.action_update_toc.triggered.connect(window.update_markdown_toc_in_editor)

    window.action_audit = window.tools_menu.addAction("🔍 Аудит документа" if window.current_lang == "ru" else "🔍 Document Audit")
    window.action_audit.setShortcut("Ctrl+Shift+A")
    window.action_audit.triggered.connect(window.show_document_audit)

    window.action_format = window.tools_menu.addAction("✨ Умное форматирование" if window.current_lang == "ru" else "✨ Smart Formatting")
    window.action_format.setShortcut("Ctrl+Shift+F")
    window.action_format.triggered.connect(window.format_markdown_document)

    window.action_diff = window.tools_menu.addAction("📊 Сравнение файлов" if window.current_lang == "ru" else "📊 Compare Files")
    window.action_diff.setShortcut("Ctrl+Shift+D")
    window.action_diff.triggered.connect(window.show_diff_dialog)

    window.action_version_save = window.tools_menu.addAction("📌 Сохранить версию")
    window.action_version_save.setShortcut("Ctrl+Shift+V")
    window.action_version_save.triggered.connect(window.save_version)

    window.action_version_restore = window.tools_menu.addAction("📥 Восстановить версию")
    window.action_version_restore.triggered.connect(window.restore_version)

    window.action_focus = window.tools_menu.addAction("🎯 Режим фокуса")
    window.action_focus.setShortcut("F11")
    window.action_focus.triggered.connect(window.toggle_focus_mode)

    window.action_spell = window.tools_menu.addAction("📖 Spell Check")
    window.action_spell.triggered.connect(window.run_spell_check)

    window.action_graph = window.tools_menu.addAction("🕸️ Graph View")
    window.action_graph.triggered.connect(window.show_graph_view)

    window.action_tags = window.tools_menu.addAction("🏷️ Облако тегов")
    window.action_tags.triggered.connect(window.show_tag_cloud)

    window.action_analytics = window.tools_menu.addAction("📊 Reading Analytics")
    window.action_analytics.triggered.connect(window.show_reading_analytics)

    window.action_taskboard = window.tools_menu.addAction("📋 Task Board")
    window.action_taskboard.triggered.connect(window.export_task_board)

    window.action_apidocs = window.tools_menu.addAction("📚 API Docs Generator")
    window.action_apidocs.triggered.connect(window.generate_api_docs)

    window.action_wikilinks = window.tools_menu.addAction("🔗 Обработать [[ссылки]]")
    window.action_wikilinks.triggered.connect(window.process_wikilinks)

    window.action_typewriter = window.tools_menu.addAction("⌨️ Typewriter Mode")
    window.action_typewriter.triggered.connect(window.toggle_typewriter_mode)

    window.action_pdf_to_md = window.tools_menu.addAction("📄 PDF → Markdown")
    window.action_pdf_to_md.triggered.connect(window.pdf_to_markdown_convert)

    window.action_github_sync = window.tools_menu.addAction("🐙 GitHub Sync")
    window.action_github_sync.triggered.connect(window.show_github_sync_dialog)

    window.action_plugin_manager = window.tools_menu.addAction("🧩 Plugin Manager")
    window.action_plugin_manager.triggered.connect(window.show_plugin_manager)

    window.action_csv_editor = window.tools_menu.addAction("📊 CSV Editor")
    window.action_csv_editor.triggered.connect(window.show_csv_editor)

    window.action_template_vars = window.tools_menu.addAction("🔧 Template Variables")
    window.action_template_vars.triggered.connect(window.apply_template_vars)

    window.action_calendar = window.tools_menu.addAction("📅 Calendar Notes")
    window.action_calendar.triggered.connect(window.show_calendar_notes)

    window.action_pomodoro = window.tools_menu.addAction("🍅 Pomodoro")
    window.action_pomodoro.triggered.connect(window.show_pomodoro)

    window.action_ocr = window.tools_menu.addAction("🖼 Image → Text (OCR)")
    window.action_ocr.triggered.connect(window.ocr_image_to_text)

    window.action_latex_preview = window.tools_menu.addAction("📐 LaTeX Preview")
    window.action_latex_preview.triggered.connect(window.show_latex_preview)

    window.action_multi_export = window.tools_menu.addAction("📦 Multi-Export")
    window.action_multi_export.triggered.connect(window.show_multi_export)

    window.action_tts = window.tools_menu.addAction("🔊 Text-to-Speech")
    window.action_tts.triggered.connect(window.text_to_speech_speak)

    window.action_html2md = window.tools_menu.addAction("🔄 HTML → Markdown")
    window.action_html2md.triggered.connect(window.html_to_markdown_convert)

    window.action_watermark = window.tools_menu.addAction("🎨 Watermark Designer")
    window.action_watermark.triggered.connect(window.show_watermark_designer)

    window.action_flashcards = window.tools_menu.addAction("🃏 Flashcards")
    window.action_flashcards.triggered.connect(window.generate_flashcards)

    window.action_citations = window.tools_menu.addAction("📚 Citation Manager")
    window.action_citations.triggered.connect(window.show_citation_manager)

    window.action_glossary = window.tools_menu.addAction("📖 Glossary Builder")
    window.action_glossary.triggered.connect(window.build_glossary)

    window.action_quiz = window.tools_menu.addAction("📝 Quiz Generator")
    window.action_quiz.triggered.connect(window.generate_quiz)

    window.lang_menu = menubar.addMenu("🌐 Язык (Language)")
    window.action_lang_ru = window.lang_menu.addAction("Русский")
    window.action_lang_en = window.lang_menu.addAction("English")

    # Help Menu
    window.help_menu = menubar.addMenu("❓ Help" if window.current_lang == "ru" else "❓ Help")
    window.action_about = window.help_menu.addAction("ℹ️ About" if window.current_lang == "ru" else "ℹ️ About MarkdownToPDF")
    window.action_about.triggered.connect(window.show_about)

    window.action_welcome_tour = window.help_menu.addAction("🚀 Welcome Tour" if window.current_lang == "ru" else "🚀 Welcome Tour")
    window.action_welcome_tour.triggered.connect(window.show_welcome_tour)

    # ── Central layout ──
    central = QWidget()
    window.setCentralWidget(central)
    root = QVBoxLayout(central)
    root.setContentsMargins(20, 10, 20, 15)
    root.setSpacing(12)

    # ── Settings Group (hidden in Zen mode) ──
    window.settings_group = QWidget()
    settings_group_layout = QVBoxLayout(window.settings_group)
    settings_group_layout.setContentsMargins(0, 0, 0, 0)
    settings_group_layout.setSpacing(10)

    # ── Title row + dark-mode toggle ──
    title_row = QHBoxLayout()
    window.label_title = QLabel("📄 Markdown → PDF Converter Pro")
    window.label_title.setStyleSheet("font-size: 18px; font-weight: bold;")
    title_row.addWidget(window.label_title)
    title_row.addStretch()

    window.btn_advanced_settings = QPushButton("\u2699 Settings")
    window.btn_advanced_settings.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_advanced_settings.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e293b, stop:1 #334155);
            color: white; font-weight: 600; padding: 8px 16px; border-radius: 10px; font-size: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f172a, stop:1 #1e293b); }
    """)
    title_row.addWidget(window.btn_advanced_settings)

    window.btn_theme = QPushButton("\U0001F319 Theme")
    window.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_theme.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #a78bfa);
            color: white; font-weight: 600; padding: 8px 16px; border-radius: 10px; font-size: 12px;
            border: 1px solid rgba(255, 255, 255, 0.15);
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6d28d9, stop:1 #7c3aed); }
    """)
    window.btn_theme.clicked.connect(window.toggle_theme)
    title_row.addWidget(window.btn_theme)
    settings_group_layout.addLayout(title_row)

    # ── Advanced Settings Dialog ──
    window.advanced_dialog = QDialog(window)
    window.advanced_dialog.setWindowTitle("⚙️ Расширенные настройки")
    window.advanced_dialog.setMinimumWidth(550)
    
    window.btn_advanced_settings.clicked.connect(window.advanced_dialog.exec)
    
    dialog_layout = QVBoxLayout(window.advanced_dialog)
    
    tabs = QTabWidget()
    
    # -- Tab 1: Appearance --
    tab_appearance = QWidget()
    form_app = QFormLayout(tab_appearance)
    
    window.doc_theme_combo = QComboBox()
    window.doc_theme_combo.addItem("Modern", "theme_modern.css")
    window.doc_theme_combo.addItem("Classic Book", "theme_classic.css")
    window.doc_theme_combo.addItem("🌙 Dark PDF", "theme_dark_pdf.css")
    window.label_doc_style = QLabel("Стиль документа:")
    form_app.addRow(window.label_doc_style, window.doc_theme_combo)

    window.code_theme_combo = QComboBox()
    window.code_theme_combo.addItem("Светлый / Tango", "pygments.css")
    window.code_theme_combo.addItem("Тёмный / Monokai", "pygments_dark.css")
    window.label_code_style = QLabel("Стиль кода:")
    code_theme_layout = QHBoxLayout()
    code_theme_layout.addWidget(window.code_theme_combo)
    window.btn_preview_code_theme = QPushButton("👁")
    window.btn_preview_code_theme.setFixedSize(28, 28)
    window.btn_preview_code_theme.setToolTip("Предпросмотр темы кода")
    window.btn_preview_code_theme.clicked.connect(window.preview_code_theme)
    code_theme_layout.addWidget(window.btn_preview_code_theme)
    form_app.addRow(window.label_code_style, code_theme_layout)

    css_layout = QHBoxLayout()
    window.custom_css_input = QLineEdit()
    window.custom_css_input.setPlaceholderText("Путь к вашему .css файлу")
    window.btn_select_css = QPushButton("Обзор...")
    window.btn_select_css.clicked.connect(window.select_custom_css)
    
    window.btn_design_style = QPushButton("🎨 Настроить")
    window.btn_design_style.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_design_style.setStyleSheet("""
        QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2563eb,stop:1 #60a5fa); color: white; font-weight: bold; border: none; padding: 6px 14px; border-radius: 6px; }
        QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1d4ed8,stop:1 #2563eb); }
    """)
    window.btn_design_style.clicked.connect(window.show_design_style_dialog)
    
    css_layout.addWidget(window.custom_css_input)
    css_layout.addWidget(window.btn_select_css)
    css_layout.addWidget(window.btn_design_style)
    
    window.label_custom_css = QLabel("Кастомный CSS:")
    form_app.addRow(window.label_custom_css, css_layout)
    tabs.addTab(tab_appearance, "🎨 Оформление")

    # -- Tab 2: Page --
    tab_page = QWidget()
    form_page = QFormLayout(tab_page)
    
    window.paper_combo = QComboBox()
    window.paper_combo.addItems(["A4", "Letter", "Legal", "A3", "A5"])
    window.label_paper_size = QLabel("Размер бумаги:")
    form_page.addRow(window.label_paper_size, window.paper_combo)

    window.margins_input = QLineEdit()
    window.margins_input.setPlaceholderText("Пример: 20mm 15mm 20mm 15mm")
    window.label_margins = QLabel("Поля PDF (в, п, н, л):")
    form_page.addRow(window.label_margins, window.margins_input)

    window.chk_page_numbers = QCheckBox("Включить нумерацию страниц")
    form_page.addRow("", window.chk_page_numbers)

    window.combo_page_format = QComboBox()
    window.combo_page_format.addItem("Простая (1)", "simple")
    window.combo_page_format.addItem("Дробь (1 / 5)", "slash")
    window.combo_page_format.addItem("Текст (Стр. 1 из 5)", "text")
    window.label_page_format = QLabel("Формат нумерации:")
    form_page.addRow(window.label_page_format, window.combo_page_format)

    window.chk_presentation_mode = QCheckBox("Режим презентации (слайдов)")
    form_page.addRow("", window.chk_presentation_mode)

    window.chk_compress = QCheckBox("Сжать PDF (уменьшить размер)")
    window.chk_compress.setToolTip("Сжимает содержимое PDF для уменьшения размера файла")
    form_page.addRow("", window.chk_compress)

    tabs.addTab(tab_page, "📄 Страница")

    # -- Tab 3: Security & Meta --
    tab_sec = QWidget()
    form_sec = QFormLayout(tab_sec)

    window.watermark_input = QLineEdit()
    window.watermark_input.setPlaceholderText("Например: Черновик")
    window.label_watermark = QLabel("Водяной знак:")
    form_sec.addRow(window.label_watermark, window.watermark_input)

    window.footer_input = QLineEdit()
    window.footer_input.setPlaceholderText("Текст внизу каждой страницы")
    window.label_footer = QLabel("Нижний колонтитул:")
    form_sec.addRow(window.label_footer, window.footer_input)

    window.pdf_password_input = QLineEdit()
    window.pdf_password_input.setPlaceholderText("Пусто для открытого PDF")
    window.pdf_password_input.setEchoMode(QLineEdit.EchoMode.Password)
    window.label_pdf_password = QLabel("Пароль для PDF:")
    form_sec.addRow(window.label_pdf_password, window.pdf_password_input)
    tabs.addTab(tab_sec, "🛡️ Защита и Данные")

    # -- Tab 4: Advanced --
    tab_adv = QWidget()
    form_adv = QFormLayout(tab_adv)
    
    docx_layout = QHBoxLayout()
    window.docx_template_input = QLineEdit()
    window.docx_template_input.setPlaceholderText("Путь к .docx шаблону")
    window.btn_select_docx = QPushButton("Обзор...")
    window.btn_select_docx.clicked.connect(window.select_docx_template)
    docx_layout.addWidget(window.docx_template_input)
    docx_layout.addWidget(window.btn_select_docx)
    window.label_docx_template = QLabel("Шаблон DOCX:")
    form_adv.addRow(window.label_docx_template, docx_layout)

    preset_layout = QHBoxLayout()
    window.preset_combo = QComboBox()
    window.preset_combo.addItem("(по умолчанию)")
    window.btn_save_preset = QPushButton("Сохранить")
    window.btn_save_preset.clicked.connect(window.save_preset)
    window.btn_delete_preset = QPushButton("Удалить")
    window.btn_delete_preset.clicked.connect(window.delete_preset)
    preset_layout.addWidget(window.preset_combo, stretch=1)
    preset_layout.addWidget(window.btn_save_preset)
    preset_layout.addWidget(window.btn_delete_preset)
    window.label_preset = QLabel("Пресет настроек:")
    form_adv.addRow(window.label_preset, preset_layout)
    tabs.addTab(tab_adv, "⚙️ Дополнительно")

    dialog_layout.addWidget(tabs)

    btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
    if window.current_lang == "ru":
        btn_box.button(QDialogButtonBox.StandardButton.Ok).setText("Сохранить и Закрыть")
    btn_box.accepted.connect(window.advanced_dialog.accept)
    dialog_layout.addWidget(btn_box)

    # ── File selection ──
    file_layout = QHBoxLayout()
    window.file_label = QLabel("Файл не выбран (или перетащите .md файлы сюда)")
    window.file_label.setStyleSheet("font-size: 13px; color: #94a3b8;")

    # Outline/Clean style buttons
    btn_style = """
        QPushButton { 
            background-color: transparent; 
            color: #e2e8f0; 
            font-weight: 500;
            padding: 8px 15px; 
            border: 1px solid rgba(255, 255, 255, 0.15); 
            border-radius: 6px; 
            font-size: 13px; 
        }
        QPushButton:hover { 
            background-color: rgba(51, 65, 85, 0.6); 
            border-color: rgba(99, 102, 241, 0.4);
        }
    """
    dark_btn_style = """
        QPushButton { 
            background-color: transparent; 
            color: #64748b; 
            font-weight: 500;
            padding: 8px 15px; 
            border: 1px solid #cbd5e1; 
            border-radius: 6px; 
            font-size: 13px; 
        }
        QPushButton:hover { 
            background-color: rgba(51, 65, 85, 0.08); 
            border-color: #94a3b8;
        }
    """

    window.btn_select = QPushButton("➕ Добавить файлы")
    window.btn_select.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_select.setProperty("clean_style", True)
    window.btn_select.setStyleSheet(btn_style)
    window.btn_select.clicked.connect(window.select_files)

    window.btn_select_folder = QPushButton("📁 Открыть папку")
    window.btn_select_folder.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_select_folder.setProperty("clean_style", True)
    window.btn_select_folder.setStyleSheet(btn_style)
    window.btn_select_folder.clicked.connect(window.select_folder)

    window.btn_merge_files = QPushButton("📖 Собрать книгу")
    window.btn_merge_files.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_merge_files.setProperty("clean_style", True)
    window.btn_merge_files.setStyleSheet(btn_style)
    window.btn_merge_files.clicked.connect(window.show_merge_dialog)

    window.btn_out_folder = QPushButton("📂 Куда сохранять")
    window.btn_out_folder.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_out_folder.setProperty("clean_style", True)
    window.btn_out_folder.setStyleSheet(btn_style)
    window.btn_out_folder.clicked.connect(window.open_output_folder)

    file_layout.addWidget(window.file_label, stretch=1)
    file_layout.addWidget(window.btn_select)
    file_layout.addWidget(window.btn_select_folder)
    file_layout.addWidget(window.btn_merge_files)
    file_layout.addWidget(window.btn_out_folder)
    settings_group_layout.addLayout(file_layout)

    # ── Buttons row: Convert + Watch ──
    btn_row = QHBoxLayout()

    window.format_combo = QComboBox()
    window.format_combo.addItem("PDF", "PDF")
    window.format_combo.addItem("DOCX (Word)", "DOCX")
    window.format_combo.addItem("HTML", "HTML")
    window.format_combo.addItem("EPUB", "EPUB")
    window.format_combo.addItem("PNG (изображение)", "PNG")
    window.format_combo.addItem("JPG (изображение)", "JPG")
    window.format_combo.addItem("PPTX (презентация)", "PPTX")
    window.format_combo.addItem("Reveal.js (слайды)", "REVEAL")
    window.format_combo.setStyleSheet("""
        QComboBox { padding: 10px; font-size: 14px; font-weight: bold; border: 1px solid rgba(255,255,255,0.15); border-radius: 6px; color: #e2e8f0; background: rgba(51, 65, 85, 0.6); }
        QComboBox:hover { border: 1px solid rgba(99, 102, 241, 0.4); }
        QComboBox::drop-down { border: none; }
    """)
    btn_row.addWidget(window.format_combo, stretch=1)

    window.btn_convert = QPushButton("\u26A1 Convert")
    window.btn_convert.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_convert.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #3b82f6);
            color: white; font-weight: 700; padding: 12px 24px; border-radius: 12px; font-size: 15px;
            border: 1px solid rgba(255, 255, 255, 0.15);
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1d4ed8, stop:1 #2563eb); }
        QPushButton:disabled { background: #94a3b8; border: none; }
    """)
    window.btn_convert.clicked.connect(window.convert_files)
    window.btn_convert.setEnabled(False)
    btn_row.addWidget(window.btn_convert, stretch=3)

    window.btn_cancel = QPushButton("\U0001F6D1 Cancel")
    window.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_cancel.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #dc2626, stop:1 #ef4444);
            color: white; font-weight: 700; padding: 12px 24px; border-radius: 12px; font-size: 15px;
            border: 1px solid rgba(255, 255, 255, 0.15);
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #b91c1c, stop:1 #dc2626); }
        QPushButton:disabled { background: #94a3b8; border: none; }
    """)
    window.btn_cancel.clicked.connect(window.cancel_conversion)
    window.btn_cancel.hide()
    btn_row.addWidget(window.btn_cancel, stretch=3)

    window.btn_watch = QPushButton("\U0001F441 Watch")
    window.btn_watch.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_watch.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #64748b, stop:1 #94a3b8);
            color: white; font-weight: 600; padding: 12px 16px; border-radius: 12px; font-size: 13px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #475569, stop:1 #64748b); }
        QPushButton:disabled { background: #94a3b8; border: none; }
    """)
    window.btn_watch.clicked.connect(window.toggle_watch)
    window.btn_watch.setEnabled(False)
    btn_row.addWidget(window.btn_watch, stretch=1)

    settings_group_layout.addLayout(btn_row)

    # ── Dynamic button text based on format ──
    def _update_convert_button_text(index: int):
        fmt = window.format_combo.currentData()
        window.btn_convert.setText(f"⚡ Конвертировать в {fmt}")
    window.format_combo.currentIndexChanged.connect(_update_convert_button_text)

    # ── Progress ──
    window.progress_bar = QProgressBar()
    window.progress_bar.setValue(0)
    window.progress_bar.setTextVisible(False)
    window.progress_bar.setStyleSheet("""
        QProgressBar { border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 5px;
                       background-color: rgba(51, 65, 85, 0.4); height: 10px; }
        QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #22d3ee); border-radius: 5px; }
    """)
    settings_group_layout.addWidget(window.progress_bar)

    root.addWidget(window.settings_group)

    # ── Tabs (Log & Preview) ──
    window.tabs = QTabWidget()
    root.addWidget(window.tabs)

    # ── Log Tab with Export History ──
    log_container = QWidget()
    log_layout = QVBoxLayout(log_container)
    log_layout.setContentsMargins(0, 0, 0, 0)
    log_layout.setSpacing(8)

    window.log_output = QTextBrowser()
    window.log_output.setReadOnly(True)
    window.log_output.setOpenExternalLinks(True)
    window.log_output.setStyleSheet("""
        QTextEdit { background-color: rgba(30, 41, 59, 0.85); border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 8px; padding: 10px;
                    font-family: monospace; font-size: 12px; color: #e2e8f0; selection-background-color: #4f46e5; }
        QTextEdit:focus { border: 1px solid rgba(99, 102, 241, 0.4); }
    """)
    log_layout.addWidget(window.log_output, stretch=3)

    # Successful Export History Panel
    window.history_group = QGroupBox("📁 Журнал успешного экспорта (последние 5)")
    window.history_group.setStyleSheet("""
        QGroupBox { font-weight: bold; border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 8px; margin-top: 5px; padding-top: 15px; color: #94a3b8; background-color: rgba(30, 41, 59, 0.5); }
        QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 10px; padding: 0 3px; }
    """)
    window.history_layout = QVBoxLayout(window.history_group)
    window.history_layout.setContentsMargins(10, 10, 10, 10)
    window.history_layout.setSpacing(6)

    window.history_placeholder = QLabel("Журнал экспорта пуст")
    window.history_placeholder.setStyleSheet("color: #94a3b8; font-style: italic; font-size: 11px; padding: 5px;")
    window.history_layout.addWidget(window.history_placeholder)

    log_layout.addWidget(window.history_group, stretch=1)
    window.tabs.addTab(log_container, "📝 Лог")

    # ── Live Editor Tab ──
    from PyQt6.QtWidgets import QSplitter
    editor_splitter = QSplitter(Qt.Orientation.Horizontal)
    
    # Left container for editor, search panel and stats
    editor_container = QWidget()
    editor_container_layout = QVBoxLayout(editor_container)
    editor_container_layout.setContentsMargins(0, 0, 0, 0)
    editor_container_layout.setSpacing(6)

    # ── Formatting Toolbar (Glassmorphism) ──
    window.format_toolbar = QWidget()
    toolbar_layout = QHBoxLayout(window.format_toolbar)
    toolbar_layout.setContentsMargins(6, 4, 6, 4)
    toolbar_layout.setSpacing(3)
    window.format_toolbar.setStyleSheet("""
        QWidget {
            background-color: rgba(255, 255, 255, 0.45);
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.4);
        }
        QPushButton {
            background: rgba(255, 255, 255, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.35);
            border-radius: 8px;
            padding: 5px 10px;
            font-size: 12px;
            font-weight: 600;
            color: #374151;
            min-width: 30px;
        }
        QPushButton:hover {
            background: rgba(99, 102, 241, 0.12);
            border-color: rgba(99, 102, 241, 0.3);
            color: #4338ca;
        }
        QPushButton:pressed {
            background: rgba(99, 102, 241, 0.2);
        }
    """)

    window.btn_format_bold = QPushButton("B")
    window.btn_format_bold.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_format_bold.clicked.connect(window.format_bold)

    window.btn_format_italic = QPushButton("I")
    window.btn_format_italic.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_format_italic.clicked.connect(window.format_italic)

    window.btn_format_h1 = QPushButton("H1")
    window.btn_format_h1.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_format_h1.clicked.connect(lambda: window.format_header(1))

    window.btn_format_h2 = QPushButton("H2")
    window.btn_format_h2.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_format_h2.clicked.connect(lambda: window.format_header(2))

    window.btn_format_code = QPushButton("<>")
    window.btn_format_code.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_format_code.clicked.connect(window.format_code)

    window.btn_format_quote = QPushButton("\u201c\u201d")
    window.btn_format_quote.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_format_quote.clicked.connect(window.format_quote)

    window.btn_format_list = QPushButton("\u2022")
    window.btn_format_list.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_format_list.clicked.connect(window.format_list)

    window.btn_format_pagebreak = QPushButton("\U0001F4C4 Split")
    window.btn_format_pagebreak.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_format_pagebreak.clicked.connect(window.insert_page_break)
    window.btn_format_pagebreak.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #a78bfa);
            color: white; border: none; font-weight: 600; padding: 5px 12px; border-radius: 8px;
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #8b5cf6); }
    """)



    window.btn_copy_html = QPushButton("\U0001F4CB Copy HTML")
    window.btn_copy_html.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_copy_html.clicked.connect(window.copy_styled_html)
    window.btn_copy_html.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #34d399);
            color: white; border: none; font-weight: 600; padding: 5px 12px; border-radius: 8px;
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981); }
    """)

    window.btn_print = QPushButton("🖨 Печать")
    window.btn_print.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_print.clicked.connect(window.print_document)
    window.btn_print.setStyleSheet("""
        QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #ea580c,stop:1 #f97316); color: white; border: none; font-weight: bold; padding: 4px 10px; border-radius: 6px; }
        QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #c2410c,stop:1 #ea580c); }
    """)

    window.btn_snippets = QPushButton("\U0001F9E9 Snippets")
    window.btn_snippets.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_snippets.clicked.connect(window.show_snippets_dialog)
    window.btn_snippets.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #334155, stop:1 #475569);
            color: white; border: none; font-weight: 600; padding: 5px 12px; border-radius: 8px;
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e293b, stop:1 #334155); }
    """)

    window.btn_doc_templates = QPushButton("\U0001F4CB Docs")
    window.btn_doc_templates.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_doc_templates.clicked.connect(window.show_doc_templates_dialog)
    window.btn_doc_templates.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #a78bfa);
            color: white; border: none; font-weight: 600; padding: 5px 12px; border-radius: 8px;
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6d28d9, stop:1 #7c3aed); }
    """)

    window.btn_zen = QPushButton("\U0001F9D8 Zen")
    window.btn_zen.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_zen.clicked.connect(window.toggle_zen_mode)
    window.btn_zen.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ea580c, stop:1 #f97316);
            color: white; border: none; font-weight: 600; padding: 5px 12px; border-radius: 8px;
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #c2410c, stop:1 #ea580c); }
    """)

    window.btn_format = QPushButton("\u2728 Format")
    window.btn_format.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_format.clicked.connect(window.format_markdown_document)
    window.btn_format.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0d9488, stop:1 #14b8a6);
            color: white; border: none; font-weight: 600; padding: 5px 12px; border-radius: 8px;
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f766e, stop:1 #0d9488); }
    """)

    window.btn_history = QPushButton("\U0001F552 History")
    window.btn_history.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_history.clicked.connect(window.show_revision_history)
    window.btn_history.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #64748b, stop:1 #94a3b8);
            color: white; border: none; font-weight: 600; padding: 5px 12px; border-radius: 8px;
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #475569, stop:1 #64748b); }
    """)

    window.btn_audit = QPushButton("\U0001F6E1 Audit")
    window.btn_audit.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_audit.clicked.connect(window.show_document_audit)
    window.btn_audit.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e293b, stop:1 #334155);
            color: white; border: none; font-weight: 600; padding: 5px 12px; border-radius: 8px;
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f172a, stop:1 #1e293b); }
    """)

    window.btn_toc = QPushButton("\U0001F4CB TOC")
    window.btn_toc.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_toc.clicked.connect(window.show_toc_generator)
    window.btn_toc.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981);
            color: white; border: none; font-weight: 600; padding: 5px 12px; border-radius: 8px;
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669); }
    """)

    toolbar_layout.addWidget(window.btn_format_bold)
    toolbar_layout.addWidget(window.btn_format_italic)
    toolbar_layout.addWidget(window.btn_format_h1)
    toolbar_layout.addWidget(window.btn_format_h2)
    toolbar_layout.addWidget(window.btn_format_code)
    toolbar_layout.addWidget(window.btn_format_quote)
    toolbar_layout.addWidget(window.btn_format_list)
    toolbar_layout.addWidget(window.btn_format_pagebreak)
    toolbar_layout.addWidget(window.btn_print)
    toolbar_layout.addWidget(window.btn_copy_html)

    window.btn_lint = QPushButton("\U0001F50D Lint")
    window.btn_lint.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_lint.setToolTip("Markdown linter")
    window.btn_lint.clicked.connect(window.run_linter)
    window.btn_lint.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #dc2626, stop:1 #f87171);
            color: white; border: none; font-weight: 600; padding: 5px 12px; border-radius: 8px;
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #b91c1c, stop:1 #dc2626); }
    """)
    toolbar_layout.addWidget(window.btn_lint)

    toolbar_layout.addWidget(window.btn_snippets)
    toolbar_layout.addWidget(window.btn_doc_templates)
    toolbar_layout.addWidget(window.btn_format)

    window.btn_cloud_templates = QPushButton("\u2601 Cloud")
    window.btn_cloud_templates.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_cloud_templates.setToolTip("Cloud Templates")
    window.btn_cloud_templates.clicked.connect(window.show_cloud_templates)
    window.btn_cloud_templates.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #60a5fa);
            color: white; border: none; font-weight: 600; padding: 5px 12px; border-radius: 8px;
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1d4ed8, stop:1 #2563eb); }
    """)
    toolbar_layout.addWidget(window.btn_cloud_templates)

    window.btn_focus = QPushButton("\U0001F3AF Focus")
    window.btn_focus.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_focus.setToolTip("Focus Mode")
    window.btn_focus.clicked.connect(window.toggle_focus_mode)
    window.btn_focus.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #a78bfa);
            color: white; border: none; font-weight: 600; padding: 5px 12px; border-radius: 8px;
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6d28d9, stop:1 #7c3aed); }
    """)
    toolbar_layout.addWidget(window.btn_focus)

    window.btn_emoji = QPushButton("\U0001F600")
    window.btn_emoji.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_emoji.setToolTip("Emoji Shortcodes")
    window.btn_emoji.clicked.connect(window.convert_emoji_shortcodes)
    window.btn_emoji.setStyleSheet("""
        QPushButton {
            background: rgba(255, 255, 255, 0.5); border: 1px solid rgba(255, 255, 255, 0.35);
            border-radius: 8px; font-size: 15px; padding: 3px 8px;
        }
        QPushButton:hover { background: rgba(255, 255, 255, 0.75); }
    """)
    toolbar_layout.addWidget(window.btn_emoji)

    window.btn_version = QPushButton("\U0001F4CC")
    window.btn_version.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_version.setToolTip("Save Version")
    window.btn_version.clicked.connect(window.save_version)
    window.btn_version.setStyleSheet("""
        QPushButton {
            background: rgba(255, 255, 255, 0.5); border: 1px solid rgba(255, 255, 255, 0.35);
            border-radius: 8px; font-size: 15px; padding: 3px 8px;
        }
        QPushButton:hover { background: rgba(255, 255, 255, 0.75); }
    """)
    toolbar_layout.addWidget(window.btn_version)

    window.btn_spell = QPushButton("\U0001F4D6")
    window.btn_spell.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_spell.setToolTip("Spell Check")
    window.btn_spell.clicked.connect(window.run_spell_check)
    window.btn_spell.setStyleSheet("""
        QPushButton {
            background: rgba(255, 255, 255, 0.5); border: 1px solid rgba(255, 255, 255, 0.35);
            border-radius: 8px; font-size: 15px; padding: 3px 8px;
        }
        QPushButton:hover { background: rgba(255, 255, 255, 0.75); }
    """)
    toolbar_layout.addWidget(window.btn_spell)

    window.btn_wysiwyg = QPushButton("\u2728 WYSIWYG")
    window.btn_wysiwyg.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_wysiwyg.setToolTip("WYSIWYG Mode")
    window.btn_wysiwyg.clicked.connect(window.toggle_wysiwyg)
    window.btn_wysiwyg.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ea580c, stop:1 #f97316);
            color: white; border: none; font-weight: 600; padding: 5px 12px; border-radius: 8px;
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #c2410c, stop:1 #ea580c); }
    """)
    toolbar_layout.addWidget(window.btn_wysiwyg)

    window.btn_split_view = QPushButton("\U0001F4CF Split")
    window.btn_split_view.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_split_view.setToolTip("Toggle Split View")
    window.btn_split_view.clicked.connect(window.toggle_split_view)
    window.btn_split_view.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0d9488, stop:1 #14b8a6);
            color: white; border: none; font-weight: 600; padding: 5px 12px; border-radius: 8px;
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f766e, stop:1 #0d9488); }
    """)
    toolbar_layout.addWidget(window.btn_split_view)

    window.btn_pdf2md = QPushButton("\U0001F4C4\u2192MD")
    window.btn_pdf2md.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_pdf2md.setToolTip("PDF to Markdown")
    window.btn_pdf2md.clicked.connect(window.pdf_to_markdown_convert)
    window.btn_pdf2md.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #a78bfa);
            color: white; border: none; font-weight: 600; padding: 5px 12px; border-radius: 8px;
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6d28d9, stop:1 #7c3aed); }
    """)
    toolbar_layout.addWidget(window.btn_pdf2md)

    window.btn_github = QPushButton("\U0001F419 Git")
    window.btn_github.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_github.setToolTip("GitHub Sync")
    window.btn_github.clicked.connect(window.show_github_sync_dialog)
    window.btn_github.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e293b, stop:1 #334155);
            color: white; border: none; font-weight: 600; padding: 5px 12px; border-radius: 8px;
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f172a, stop:1 #1e293b); }
    """)
    toolbar_layout.addWidget(window.btn_github)

    window.btn_excalidraw = QPushButton("\U0001F3A8 Draw")
    window.btn_excalidraw.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_excalidraw.setToolTip("Excalidraw Diagram")
    window.btn_excalidraw.clicked.connect(window.show_excalidraw)
    window.btn_excalidraw.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #dc2626, stop:1 #f87171);
            color: white; border: none; font-weight: 600; padding: 5px 12px; border-radius: 8px;
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #b91c1c, stop:1 #dc2626); }
    """)
    toolbar_layout.addWidget(window.btn_excalidraw)

    window.btn_csv = QPushButton("\U0001F4CA CSV")
    window.btn_csv.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_csv.setToolTip("CSV Table Editor")
    window.btn_csv.clicked.connect(window.show_csv_editor)
    window.btn_csv.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0d9488, stop:1 #14b8a6);
            color: white; border: none; font-weight: 600; padding: 5px 12px; border-radius: 8px;
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f766e, stop:1 #0d9488); }
    """)
    toolbar_layout.addWidget(window.btn_csv)

    window.btn_pomodoro = QPushButton("🍅")
    window.btn_pomodoro.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_pomodoro.setToolTip("Pomodoro Timer")
    window.btn_pomodoro.clicked.connect(window.show_pomodoro)
    window.btn_pomodoro.setStyleSheet("QPushButton { font-size: 16px; padding: 2px 6px; }")
    toolbar_layout.addWidget(window.btn_pomodoro)

    window.btn_multi_cursor = QPushButton("\U0001F5B1 MC")
    window.btn_multi_cursor.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_multi_cursor.setToolTip("Multi-Cursor")
    window.btn_multi_cursor.clicked.connect(window.add_multi_cursor)
    window.btn_multi_cursor.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #64748b, stop:1 #94a3b8);
            color: white; border: none; font-weight: 600; padding: 5px 12px; border-radius: 8px;
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #475569, stop:1 #64748b); }
    """)
    toolbar_layout.addWidget(window.btn_multi_cursor)

    window.btn_ocr = QPushButton("\U0001F5BC OCR")
    window.btn_ocr.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_ocr.setToolTip("Image to Text (OCR)")
    window.btn_ocr.clicked.connect(window.ocr_image_to_text)
    window.btn_ocr.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #a78bfa);
            color: white; border: none; font-weight: 600; padding: 5px 12px; border-radius: 8px;
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6d28d9, stop:1 #7c3aed); }
    """)
    toolbar_layout.addWidget(window.btn_ocr)

    window.btn_tts = QPushButton("\U0001F50A TTS")
    window.btn_tts.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_tts.setToolTip("Text-to-Speech")
    window.btn_tts.clicked.connect(window.text_to_speech_speak)
    window.btn_tts.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ea580c, stop:1 #f97316);
            color: white; border: none; font-weight: 600; padding: 5px 12px; border-radius: 8px;
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #c2410c, stop:1 #ea580c); }
    """)
    toolbar_layout.addWidget(window.btn_tts)

    window.btn_watermark = QPushButton("\U0001F4A7")
    window.btn_watermark.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_watermark.setToolTip("Watermark Designer")
    window.btn_watermark.clicked.connect(window.show_watermark_designer)
    window.btn_watermark.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0ea5e9, stop:1 #38bdf8);
            color: white; border: none; font-weight: 600; padding: 5px 10px; border-radius: 8px; font-size: 14px;
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #0ea5e9); }
    """)
    toolbar_layout.addWidget(window.btn_watermark)

    window.btn_quiz = QPushButton("\U0001F4DD Quiz")
    window.btn_quiz.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_quiz.setToolTip("Generate Quiz")
    window.btn_quiz.clicked.connect(window.generate_quiz)
    window.btn_quiz.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0d9488, stop:1 #14b8a6);
            color: white; border: none; font-weight: 600; padding: 5px 12px; border-radius: 8px;
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f766e, stop:1 #0d9488); }
    """)
    toolbar_layout.addWidget(window.btn_quiz)

    toolbar_layout.addWidget(window.btn_zen)
    toolbar_layout.addWidget(window.btn_history)
    toolbar_layout.addWidget(window.btn_audit)
    toolbar_layout.addWidget(window.btn_toc)
    toolbar_layout.addStretch(1)

    editor_container_layout.addWidget(window.format_toolbar)

    window.live_editor = QTextEdit()
    window.live_editor.setPlaceholderText(
        "# Добро пожаловать!\n\n"
        "Начните писать Markdown здесь...\n\n"
        "## Быстрый старт\n"
        "- **Ctrl+B** — жирный\n"
        "- **Ctrl+I** — курсив\n"
        "- **Ctrl+/** — все клавиши\n\n"
        "Перетащите .md файл или нажмите ➕ Добавить файлы"
    )
    window.live_editor.setStyleSheet("""
        QTextEdit { background-color: rgba(30, 41, 59, 0.85); border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 8px; padding: 10px; font-family: monospace; font-size: 14px;
                    color: #e2e8f0; selection-background-color: #4f46e5; }
        QTextEdit:focus { border: 1px solid rgba(99, 102, 241, 0.4); }
    """)
    editor_container_layout.addWidget(window.live_editor, stretch=1)

    # Search & Replace Panel (Ctrl+F)
    window.search_panel = QWidget()
    search_layout = QGridLayout(window.search_panel)
    search_layout.setContentsMargins(8, 8, 8, 8)
    search_layout.setSpacing(6)
    window.search_panel.setStyleSheet("""
        QWidget { background-color: rgba(30, 41, 59, 0.85); border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1); }
        QLabel { border: none; font-size: 11px; font-weight: bold; color: #94a3b8; }
        QCheckBox { border: none; font-size: 11px; font-weight: bold; color: #94a3b8; }
        QLineEdit { background: rgba(51, 65, 85, 0.6); border: 1px solid rgba(255, 255, 255, 0.15); padding: 4px;
                    border-radius: 3px; color: #e2e8f0; selection-background-color: #4f46e5; }
        QLineEdit:focus { border: 1px solid rgba(99, 102, 241, 0.5); }
        QPushButton { background: rgba(99, 102, 241, 0.6); color: white; padding: 4px 8px; border-radius: 3px;
                      font-size: 11px; font-weight: bold; border: none; }
        QPushButton:hover { background: rgba(99, 102, 241, 0.8); }
    """)
    
    window.label_search_find = QLabel("Найти:")
    window.search_find_input = QLineEdit()
    window.label_search_replace = QLabel("Заменить на:")
    window.search_replace_input = QLineEdit()
    
    window.btn_search_next = QPushButton("Найти далее")
    window.btn_search_next.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_replace_all = QPushButton("Заменить все")
    window.btn_replace_all.setCursor(Qt.CursorShape.PointingHandCursor)
    
    window.btn_search_close = QPushButton("✕")
    window.btn_search_close.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_search_close.setStyleSheet("QPushButton { background: rgba(239, 68, 68, 0.7); color: white; font-weight: bold; border-radius: 3px; padding: 4px 8px; } QPushButton:hover { background: rgba(239, 68, 68, 0.9); }")
    
    window.search_regex_checkbox = QCheckBox("RegEx")
    
    search_layout.addWidget(window.label_search_find, 0, 0)
    search_layout.addWidget(window.search_find_input, 0, 1)
    search_layout.addWidget(window.btn_search_next, 0, 2)
    search_layout.addWidget(window.btn_search_close, 0, 3)
    search_layout.addWidget(window.label_search_replace, 1, 0)
    search_layout.addWidget(window.search_replace_input, 1, 1)
    search_layout.addWidget(window.btn_replace_all, 1, 2)
    search_layout.addWidget(window.search_regex_checkbox, 1, 3)
    
    window.search_panel.hide()  # Hidden by default
    editor_container_layout.addWidget(window.search_panel)

    # Goal Progress Bar
    window.goal_progress = QProgressBar()
    window.goal_progress.setValue(0)
    window.goal_progress.setTextVisible(False)
    window.goal_progress.setFixedHeight(4)
    window.goal_progress.setStyleSheet("""
        QProgressBar { border: none; background-color: rgba(51, 65, 85, 0.4); border-radius: 2px; }
        QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ef4444, stop:1 #22c55e); border-radius: 2px; }
    """)
    window.goal_progress.hide()
    editor_container_layout.addWidget(window.goal_progress)

    # Statistics Bar
    window.stats_label = QLabel("Слов: 0 | Символов: 0 | ⏱ Время чтения: ~0 мин")
    window.stats_label.setCursor(Qt.CursorShape.PointingHandCursor)
    window.stats_label.mousePressEvent = lambda event: window.show_stats_menu()
    window.stats_label.setStyleSheet("""
        QLabel { background-color: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 6px;
                 padding: 4px 8px; font-size: 11px; color: #94a3b8; font-family: sans-serif; }
        QLabel:hover { background-color: rgba(51, 65, 85, 0.7); color: #cbd5e1; }
    """)
    editor_container_layout.addWidget(window.stats_label)
    
    window.preview_output = QTextBrowser()
    window.preview_output.setOpenExternalLinks(True)
    window.preview_output.setHtml("""
    <html><body style="display:flex; align-items:center; justify-content:center; height:100vh; margin:0;
                       font-family:'Segoe UI',sans-serif; color:#64748b; text-align:center;">
    <div>
        <div style="font-size:48px; margin-bottom:16px; opacity:0.4;">📄</div>
        <div style="font-size:16px; font-weight:600; color:#94a3b8; margin-bottom:8px;">Превью документа</div>
        <div style="font-size:13px; line-height:1.6;">
            Начните печатать в редакторе слева,<br>
            и здесь появится Live Preview<br><br>
            <span style="font-size:11px; color:#475569;">Поддержка: Markdown, таблицы, код, диаграммы Mermaid</span>
        </div>
    </div>
    </body></html>
    """)
    window.preview_output.setStyleSheet("""
        QTextBrowser { background-color: rgba(30, 41, 59, 0.85); border: 1px solid rgba(255, 255, 255, 0.1);
                       border-radius: 8px; padding: 10px; color: #e2e8f0; selection-background-color: #4f46e5; }
        QTextBrowser:focus { border: 1px solid rgba(99, 102, 241, 0.4); }
    """)
    
    from PyQt6.QtWidgets import QListWidget
    window.explorer_group = QGroupBox("📁 Проводник проекта")
    window.explorer_group.setStyleSheet("""
        QGroupBox { font-weight: bold; border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 8px; margin-top: 5px; padding-top: 15px; color: #94a3b8; background-color: rgba(30, 41, 59, 0.5); }
        QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 10px; padding: 0 3px; }
    """)
    explorer_layout = QVBoxLayout(window.explorer_group)
    explorer_layout.setContentsMargins(8, 8, 8, 8)
    explorer_layout.setSpacing(6)
    
    window.explorer_search = QLineEdit()
    window.explorer_search.setPlaceholderText("Поиск файлов...")
    window.explorer_search.setStyleSheet("""
        QLineEdit { background: rgba(51, 65, 85, 0.6); border: 1px solid rgba(255, 255, 255, 0.15); padding: 5px;
                    border-radius: 3px; color: #e2e8f0; selection-background-color: #4f46e5; }
        QLineEdit:focus { border: 1px solid rgba(99, 102, 241, 0.5); }
    """)
    window.explorer_search.textChanged.connect(window.filter_workspace_explorer)
    explorer_layout.addWidget(window.explorer_search)
    
    window.explorer_list = QListWidget()
    window.explorer_list.setStyleSheet("""
        QListWidget { background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.1);
                      border-radius: 3px; color: #e2e8f0; font-size: 12px; }
        QListWidget::item { padding: 6px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
        QListWidget::item:hover { background-color: rgba(51, 65, 85, 0.7); color: #f1f5f9; }
        QListWidget::item:selected { background-color: rgba(99, 102, 241, 0.6); color: white; font-weight: bold; }
    """)
    window.explorer_list.itemClicked.connect(window.load_workspace_file)
    explorer_layout.addWidget(window.explorer_list)
    
    window.explorer_group.hide() # Hidden by default, shown when folder is active
    
    editor_splitter.addWidget(window.explorer_group)
    editor_splitter.addWidget(editor_container)
    editor_splitter.addWidget(window.preview_output)
    editor_splitter.setSizes([200, 400, 400])
    window.editor_splitter = editor_splitter
    window._split_view_mode = 'both'  # 'both', 'editor', 'preview'

    window.tabs.addTab(editor_splitter, "✍️ Живой редактор")
