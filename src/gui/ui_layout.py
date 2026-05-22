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

    window.lang_menu = menubar.addMenu("🌐 Язык (Language)")
    window.action_lang_ru = window.lang_menu.addAction("Русский")
    window.action_lang_en = window.lang_menu.addAction("English")

    # ── Central layout ──
    central = QWidget()
    window.setCentralWidget(central)
    root = QVBoxLayout(central)
    root.setContentsMargins(20, 10, 20, 15)
    root.setSpacing(12)

    # ── Title row + dark-mode toggle ──
    title_row = QHBoxLayout()
    window.label_title = QLabel("📄 Markdown → PDF Converter Pro")
    window.label_title.setStyleSheet("font-size: 18px; font-weight: bold;")
    title_row.addWidget(window.label_title)
    title_row.addStretch()

    window.btn_advanced_settings = QPushButton("⚙️ Настройки")
    window.btn_advanced_settings.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_advanced_settings.setStyleSheet("""
        QPushButton { background: #34495e; color: white; font-weight: bold;
                      padding: 6px 12px; border-radius: 4px; font-size: 12px; }
        QPushButton:hover { background: #2c3e50; }
    """)
    title_row.addWidget(window.btn_advanced_settings)

    window.btn_theme = QPushButton("🌙 Тёмная тема")
    window.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_theme.setStyleSheet("""
        QPushButton { background: #9b59b6; color: white; font-weight: bold;
                      padding: 6px 12px; border-radius: 4px; font-size: 12px; }
        QPushButton:hover { background: #8e44ad; }
    """)
    window.btn_theme.clicked.connect(window.toggle_theme)
    title_row.addWidget(window.btn_theme)
    root.addLayout(title_row)

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
    window.label_doc_style = QLabel("Стиль документа:")
    form_app.addRow(window.label_doc_style, window.doc_theme_combo)

    window.code_theme_combo = QComboBox()
    window.code_theme_combo.addItem("Светлый / Tango", "pygments.css")
    window.code_theme_combo.addItem("Тёмный / Monokai", "pygments_dark.css")
    window.label_code_style = QLabel("Стиль кода:")
    form_app.addRow(window.label_code_style, window.code_theme_combo)

    css_layout = QHBoxLayout()
    window.custom_css_input = QLineEdit()
    window.custom_css_input.setPlaceholderText("Путь к вашему .css файлу")
    window.btn_select_css = QPushButton("Обзор...")
    window.btn_select_css.clicked.connect(window.select_custom_css)
    
    window.btn_design_style = QPushButton("🎨 Настроить")
    window.btn_design_style.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_design_style.setStyleSheet("""
        QPushButton { background-color: #3498db; color: white; font-weight: bold; }
        QPushButton:hover { background-color: #2980b9; }
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
    window.file_label.setStyleSheet("font-size: 13px; color: #7f8c8d;")

    # Outline/Clean style buttons
    btn_style = """
        QPushButton { 
            background-color: transparent; 
            color: #2c3e50; 
            font-weight: 500;
            padding: 8px 15px; 
            border: 1px solid #bdc3c7; 
            border-radius: 4px; 
            font-size: 13px; 
        }
        QPushButton:hover { 
            background-color: #ecf0f1; 
            border-color: #95a5a6;
        }
    """
    dark_btn_style = """
        QPushButton { 
            background-color: transparent; 
            color: #ecf0f1; 
            font-weight: 500;
            padding: 8px 15px; 
            border: 1px solid #7f8c8d; 
            border-radius: 4px; 
            font-size: 13px; 
        }
        QPushButton:hover { 
            background-color: #34495e; 
            border-color: #95a5a6;
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
    root.addLayout(file_layout)

    # ── Buttons row: Convert + Watch ──
    btn_row = QHBoxLayout()

    window.format_combo = QComboBox()
    window.format_combo.addItem("PDF", "PDF")
    window.format_combo.addItem("DOCX (Word)", "DOCX")
    window.format_combo.addItem("HTML", "HTML")
    window.format_combo.setStyleSheet("""
        QComboBox { padding: 10px; font-size: 14px; font-weight: bold; border: 1px solid #bdc3c7; border-radius: 5px; }
    """)
    btn_row.addWidget(window.format_combo, stretch=1)

    window.btn_convert = QPushButton("⚡ Конвертировать в PDF")
    window.btn_convert.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_convert.setStyleSheet("""
        QPushButton { background-color: #3498db; color: white; font-weight: bold;
                      padding: 12px; border-radius: 5px; font-size: 15px; }
        QPushButton:hover { background-color: #2980b9; }
        QPushButton:disabled { background-color: #bdc3c7; }
    """)
    window.btn_convert.clicked.connect(window.convert_files)
    window.btn_convert.setEnabled(False)
    btn_row.addWidget(window.btn_convert, stretch=3)

    window.btn_cancel = QPushButton("🛑 Отмена")
    window.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_cancel.setStyleSheet("""
        QPushButton { background-color: #e74c3c; color: white; font-weight: bold;
                      padding: 12px; border-radius: 5px; font-size: 15px; }
        QPushButton:hover { background-color: #c0392b; }
        QPushButton:disabled { background-color: #bdc3c7; }
    """)
    window.btn_cancel.clicked.connect(window.cancel_conversion)
    window.btn_cancel.hide()
    btn_row.addWidget(window.btn_cancel, stretch=3)

    window.btn_watch = QPushButton("👁 Watch: ВЫКЛ")
    window.btn_watch.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_watch.setStyleSheet("""
        QPushButton { background-color: #95a5a6; color: white; font-weight: bold;
                      padding: 12px; border-radius: 5px; font-size: 13px; }
        QPushButton:hover { background-color: #7f8c8d; }
        QPushButton:disabled { background-color: #bdc3c7; }
    """)
    window.btn_watch.clicked.connect(window.toggle_watch)
    window.btn_watch.setEnabled(False)
    btn_row.addWidget(window.btn_watch, stretch=1)

    root.addLayout(btn_row)

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
        QProgressBar { border: 1px solid #ecf0f1; border-radius: 5px;
                       background-color: #ecf0f1; height: 10px; }
        QProgressBar::chunk { background-color: #2ecc71; border-radius: 5px; }
    """)
    root.addWidget(window.progress_bar)

    # ── Tabs (Log & Preview) ──
    window.tabs = QTabWidget()
    root.addWidget(window.tabs)

    # ── Log Tab with Export History ──
    log_container = QWidget()
    log_layout = QVBoxLayout(log_container)
    log_layout.setContentsMargins(0, 0, 0, 0)
    log_layout.setSpacing(8)

    window.log_output = QTextEdit()
    window.log_output.setReadOnly(True)
    window.log_output.setStyleSheet("""
        QTextEdit { background-color: #f8f9fa; border: 1px solid #ecf0f1;
                    border-radius: 5px; padding: 10px;
                    font-family: monospace; font-size: 12px; color: #34495e; }
    """)
    log_layout.addWidget(window.log_output, stretch=3)

    # Successful Export History Panel
    window.history_group = QGroupBox("📁 Журнал успешного экспорта (последние 5)")
    window.history_group.setStyleSheet("""
        QGroupBox { font-weight: bold; border: 1px solid #dfe4ea; border-radius: 5px; margin-top: 5px; padding-top: 15px; }
        QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 10px; padding: 0 3px; }
    """)
    window.history_layout = QVBoxLayout(window.history_group)
    window.history_layout.setContentsMargins(10, 10, 10, 10)
    window.history_layout.setSpacing(6)

    window.history_placeholder = QLabel("Журнал экспорта пуст")
    window.history_placeholder.setStyleSheet("color: #7f8c8d; font-style: italic; font-size: 11px; padding: 5px;")
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

    # ── Formatting Toolbar ──
    window.format_toolbar = QWidget()
    toolbar_layout = QHBoxLayout(window.format_toolbar)
    toolbar_layout.setContentsMargins(2, 2, 2, 2)
    toolbar_layout.setSpacing(4)
    window.format_toolbar.setStyleSheet("""
        QWidget { background-color: #f1f2f6; border-radius: 4px; border: 1px solid #dfe4ea; }
        QPushButton { background: white; border: 1px solid #ced6e0; border-radius: 3px;
                      padding: 4px 8px; font-size: 11px; font-weight: bold; color: #2c3e50; min-width: 28px; }
        QPushButton:hover { background: #e1e2e6; }
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

    window.btn_format_quote = QPushButton("“”")
    window.btn_format_quote.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_format_quote.clicked.connect(window.format_quote)

    window.btn_format_list = QPushButton("•")
    window.btn_format_list.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_format_list.clicked.connect(window.format_list)

    window.btn_format_pagebreak = QPushButton("📄 Разрыв")
    window.btn_format_pagebreak.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_format_pagebreak.clicked.connect(window.insert_page_break)
    window.btn_format_pagebreak.setStyleSheet("""
        QPushButton { background: #9b59b6; color: white; border: none; font-weight: bold; padding: 4px 10px; }
        QPushButton:hover { background: #8e44ad; }
    """)

    window.btn_print = QPushButton("🖨 Печать")
    window.btn_print.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_print.clicked.connect(window.print_document)
    window.btn_print.setStyleSheet("""
        QPushButton { background: #e67e22; color: white; border: none; font-weight: bold; padding: 4px 10px; }
        QPushButton:hover { background: #d35400; }
    """)

    window.btn_copy_html = QPushButton("📋 Копировать HTML")
    window.btn_copy_html.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_copy_html.clicked.connect(window.copy_styled_html)
    window.btn_copy_html.setStyleSheet("""
        QPushButton { background: #2ecc71; color: white; border: none; font-weight: bold; padding: 4px 10px; }
        QPushButton:hover { background: #27ae60; }
    """)

    window.btn_snippets = QPushButton("🧩 Шаблоны")
    window.btn_snippets.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_snippets.clicked.connect(window.show_snippets_dialog)
    window.btn_snippets.setStyleSheet("""
        QPushButton { background: #34495e; color: white; border: none; font-weight: bold; padding: 4px 10px; }
        QPushButton:hover { background: #2c3e50; }
    """)

    window.btn_zen = QPushButton("🧘 Дзен")
    window.btn_zen.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_zen.clicked.connect(window.toggle_zen_mode)
    window.btn_zen.setStyleSheet("""
        QPushButton { background: #d35400; color: white; border: none; font-weight: bold; padding: 4px 10px; }
        QPushButton:hover { background: #e67e22; }
    """)

    window.btn_format = QPushButton("✨ Формат")
    window.btn_format.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_format.clicked.connect(window.format_markdown_document)
    window.btn_format.setStyleSheet("""
        QPushButton { background: #16a085; color: white; border: none; font-weight: bold; padding: 4px 10px; }
        QPushButton:hover { background: #1abc9c; }
    """)

    window.btn_history = QPushButton("🕒 История")
    window.btn_history.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_history.clicked.connect(window.show_revision_history)
    window.btn_history.setStyleSheet("""
        QPushButton { background: #7f8c8d; color: white; border: none; font-weight: bold; padding: 4px 10px; }
        QPushButton:hover { background: #95a5a6; }
    """)

    window.btn_audit = QPushButton("🛡️ Аудит")
    window.btn_audit.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_audit.clicked.connect(window.show_document_audit)
    window.btn_audit.setStyleSheet("""
        QPushButton { background: #2c3e50; color: white; border: none; font-weight: bold; padding: 4px 10px; }
        QPushButton:hover { background: #34495e; }
    """)

    window.btn_toc = QPushButton("📋 Оглавление")
    window.btn_toc.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_toc.clicked.connect(window.show_toc_generator)
    window.btn_toc.setStyleSheet("""
        QPushButton { background: #27ae60; color: white; border: none; font-weight: bold; padding: 4px 10px; }
        QPushButton:hover { background: #2ecc71; }
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
    toolbar_layout.addWidget(window.btn_snippets)
    toolbar_layout.addWidget(window.btn_format)
    toolbar_layout.addWidget(window.btn_zen)
    toolbar_layout.addWidget(window.btn_history)
    toolbar_layout.addWidget(window.btn_audit)
    toolbar_layout.addWidget(window.btn_toc)
    toolbar_layout.addStretch(1)

    editor_container_layout.addWidget(window.format_toolbar)

    window.live_editor = QTextEdit()
    window.live_editor.setPlaceholderText("Пишите Markdown здесь...\n\n# Заголовок\n\nТекст...")
    window.live_editor.setStyleSheet("""
        QTextEdit { background-color: #ffffff; border: 1px solid #ecf0f1;
                    border-radius: 5px; padding: 10px; font-family: monospace; color: #333333; }
    """)
    editor_container_layout.addWidget(window.live_editor, stretch=1)

    # Search & Replace Panel (Ctrl+F)
    window.search_panel = QWidget()
    search_layout = QGridLayout(window.search_panel)
    search_layout.setContentsMargins(8, 8, 8, 8)
    search_layout.setSpacing(6)
    window.search_panel.setStyleSheet("""
        QWidget { background-color: #f1f2f6; border-radius: 4px; border: 1px solid #dfe4ea; }
        QLabel { border: none; font-size: 11px; font-weight: bold; color: #2c3e50; }
        QCheckBox { border: none; font-size: 11px; font-weight: bold; color: #2c3e50; }
        QLineEdit { background: white; border: 1px solid #ced6e0; padding: 4px; border-radius: 3px; color: #2c3e50; }
        QPushButton { background: #57606f; color: white; padding: 4px 8px; border-radius: 3px; font-size: 11px; font-weight: bold; border: none; }
        QPushButton:hover { background: #2f3542; }
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
    window.btn_search_close.setStyleSheet("QPushButton { background: #ff4757; color: white; font-weight: bold; } QPushButton:hover { background: #ff6b81; }")
    
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
        QProgressBar { border: none; background-color: #dfe4ea; border-radius: 2px; }
        QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff4757, stop:1 #2ed573); border-radius: 2px; }
    """)
    window.goal_progress.hide()
    editor_container_layout.addWidget(window.goal_progress)

    # Statistics Bar
    window.stats_label = QLabel("Слов: 0 | Символов: 0 | ⏱ Время чтения: ~0 мин")
    window.stats_label.setCursor(Qt.CursorShape.PointingHandCursor)
    window.stats_label.mousePressEvent = lambda event: window.show_stats_menu()
    window.stats_label.setStyleSheet("""
        QLabel { background-color: #f1f2f6; border: 1px solid #ecf0f1; border-radius: 4px;
                 padding: 4px 8px; font-size: 11px; color: #2c3e50; font-family: sans-serif; }
        QLabel:hover { background-color: #e1e2e6; }
    """)
    editor_container_layout.addWidget(window.stats_label)
    
    window.preview_output = QTextBrowser()
    window.preview_output.setOpenExternalLinks(True)
    window.preview_output.setStyleSheet("""
        QTextBrowser { background-color: #ffffff; border: 1px solid #ecf0f1;
                       border-radius: 5px; padding: 10px; color: #333333; }
    """)
    
    from PyQt6.QtWidgets import QListWidget
    window.explorer_group = QGroupBox("📁 Проводник проекта")
    window.explorer_group.setStyleSheet("""
        QGroupBox { font-weight: bold; border: 1px solid #dfe4ea; border-radius: 5px; margin-top: 5px; padding-top: 15px; }
        QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 10px; padding: 0 3px; }
    """)
    explorer_layout = QVBoxLayout(window.explorer_group)
    explorer_layout.setContentsMargins(8, 8, 8, 8)
    explorer_layout.setSpacing(6)
    
    window.explorer_search = QLineEdit()
    window.explorer_search.setPlaceholderText("Поиск файлов...")
    window.explorer_search.setStyleSheet("""
        QLineEdit { background: white; border: 1px solid #ced6e0; padding: 5px; border-radius: 3px; color: #2c3e50; }
    """)
    window.explorer_search.textChanged.connect(window.filter_workspace_explorer)
    explorer_layout.addWidget(window.explorer_search)
    
    window.explorer_list = QListWidget()
    window.explorer_list.setStyleSheet("""
        QListWidget { background: white; border: 1px solid #ced6e0; border-radius: 3px; color: #2c3e50; font-size: 12px; }
        QListWidget::item { padding: 6px; border-bottom: 1px solid #f1f2f6; }
        QListWidget::item:hover { background-color: #f1f2f6; color: #2c3e50; }
        QListWidget::item:selected { background-color: #3498db; color: white; font-weight: bold; }
    """)
    window.explorer_list.itemClicked.connect(window.load_workspace_file)
    explorer_layout.addWidget(window.explorer_list)
    
    window.explorer_group.hide() # Hidden by default, shown when folder is active
    
    editor_splitter.addWidget(window.explorer_group)
    editor_splitter.addWidget(editor_container)
    editor_splitter.addWidget(window.preview_output)
    editor_splitter.setSizes([200, 400, 400])
    
    window.tabs.addTab(editor_splitter, "✍️ Живой редактор")
