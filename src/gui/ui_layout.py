from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QProgressBar, QComboBox, QLineEdit, QGroupBox,
    QTabWidget, QTextBrowser, QSplitter, QListWidget,
    QCheckBox, QDialog, QFormLayout, QDialogButtonBox,
    QFrame, QMenu, QScrollArea
)
from PyQt6.QtCore import Qt


def setup_ui(window):
    menubar = window.menuBar()

    # ── File Menu ──
    file_menu = menubar.addMenu("File")
    window.recent_menu = QMenu("Recent", window)
    file_menu.addMenu(window.recent_menu)
    file_menu.addAction("Save as .md", window.export_as_markdown)

    # ── Tools Menu ──
    tools = menubar.addMenu("Tools")
    _a = lambda text, slot, shortcut=None: tools.addAction(text, slot, shortcut) if shortcut else tools.addAction(text, slot)
    _a("Export Selection", window.export_selection)
    _a("Export History", window.show_conversion_history)
    tools.addSeparator()
    _a("Update TOC", window.update_markdown_toc_in_editor)
    _a("Document Audit", window.show_document_audit)
    _a("Smart Format", window.format_markdown_document)
    _a("Compare Files", window.show_diff_dialog)
    tools.addSeparator()
    _a("Templates", window.show_doc_templates_dialog)
    _a("Snippets", window.show_snippets_dialog)
    _a("Table Generator", window.show_table_generator_dialog)
    _a("Markdown Linter", window.run_linter)
    tools.addSeparator()
    _a("LaTeX Preview", window.show_latex_preview)
    _a("Graph View", window.show_graph_view)
    _a("Wiki Links", window.process_wikilinks)
    tools.addSeparator()
    _a("TTS (Text-to-Speech)", window.text_to_speech_speak)
    _a("OCR (Image to Text)", window.ocr_image_to_text)
    _a("PDF to Markdown", window.pdf_to_markdown_convert)
    _a("HTML to Markdown", window.html_to_markdown_convert)
    tools.addSeparator()
    _a("Flashcards", window.generate_flashcards)
    _a("Quiz Generator", window.generate_quiz)
    _a("Glossary Builder", window.build_glossary)
    _a("Citation Manager", window.show_citation_manager)
    tools.addSeparator()
    _a("CSV Editor", window.show_csv_editor)
    _a("Excalidraw Drawing", window.show_excalidraw)
    _a("Calendar Notes", window.show_calendar_notes)
    _a("Pomodoro Timer", window.show_pomodoro)
    tools.addSeparator()
    _a("Watermark Designer", window.show_watermark_designer)
    _a("Reading Analytics", window.show_reading_analytics)
    _a("Tag Cloud", window.show_tag_cloud)
    _a("GitHub Sync", window.show_github_sync_dialog)
    _a("Plugin Manager", window.show_plugin_manager)
    _a("Multi-Export", window.show_multi_export)
    _a("Template Variables", window.apply_template_vars)
    tools.addSeparator()
    _a("Version Save", window.save_version)
    _a("Version Restore", window.restore_version)
    _a("Typewriter Mode", window.toggle_typewriter_mode)
    _a("Focus Mode", window.toggle_focus_mode)
    _a("Spell Check", window.run_spell_check)

    # ── Language & Help ──
    lang_menu = menubar.addMenu("Language")
    lang_menu.addAction("Русский", lambda: window.change_lang("ru"))
    lang_menu.addAction("English", lambda: window.change_lang("en"))

    help_menu = menubar.addMenu("Help")
    help_menu.addAction("About", window.show_about)
    help_menu.addAction("Welcome Tour", window.show_welcome_tour)

    # ── Central Layout ──
    central = QWidget()
    window.setCentralWidget(central)
    root = QVBoxLayout(central)
    root.setContentsMargins(0, 0, 0, 0)
    root.setSpacing(0)

    # ── Main Content Area ──
    content = QWidget()
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(16, 8, 16, 8)
    content_layout.setSpacing(6)

    # ── Top Bar: title + theme toggle ──
    top_bar = QHBoxLayout()
    top_bar.setSpacing(8)

    window.label_title = QLabel("Markdown to PDF Converter")
    window.label_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #e2e8f0;")
    top_bar.addWidget(window.label_title)
    top_bar.addStretch()

    window.btn_advanced_settings = QPushButton("⚙")
    window.btn_advanced_settings.setFixedSize(32, 32)
    window.btn_advanced_settings.setToolTip("Settings")
    window.btn_advanced_settings.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_advanced_settings.setStyleSheet("""
        QPushButton { background: transparent; border: 1px solid rgba(255,255,255,0.1);
                      border-radius: 6px; font-size: 16px; color: #94a3b8; }
        QPushButton:hover { background: rgba(255,255,255,0.06); color: #e2e8f0; }
    """)
    top_bar.addWidget(window.btn_advanced_settings)

    window.btn_theme = QPushButton("🌙")
    window.btn_theme.setFixedSize(32, 32)
    window.btn_theme.setToolTip("Toggle theme (Ctrl+D)")
    window.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_theme.clicked.connect(window.toggle_theme)
    window.btn_theme.setStyleSheet("""
        QPushButton { background: transparent; border: 1px solid rgba(255,255,255,0.1);
                      border-radius: 6px; font-size: 16px; color: #94a3b8; }
        QPushButton:hover { background: rgba(255,255,255,0.06); color: #e2e8f0; }
    """)
    top_bar.addWidget(window.btn_theme)

    content_layout.addLayout(top_bar)

    # ── Settings Dialog (minimal) ──
    _setup_settings_dialog(window)

    # ── File Info + Convert Row ──
    action_row = QHBoxLayout()
    action_row.setSpacing(6)

    window.file_label = QLabel("Open a .md file or start typing...")
    window.file_label.setStyleSheet("font-size: 11px; color: #64748b; padding: 0 4px;")
    action_row.addWidget(window.file_label, 1)

    btn_style = """
        QPushButton { background: transparent; border: 1px solid rgba(255,255,255,0.08);
                      border-radius: 6px; padding: 5px 12px; font-size: 11px; color: #94a3b8; }
        QPushButton:hover { background: rgba(255,255,255,0.06); border-color: rgba(99,102,241,0.3); color: #e2e8f0; }
    """

    window.btn_select = QPushButton("Open")
    window.btn_select.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_select.setStyleSheet(btn_style)
    window.btn_select.clicked.connect(window.select_files)
    action_row.addWidget(window.btn_select)

    window.btn_select_folder = QPushButton("Folder")
    window.btn_select_folder.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_select_folder.setStyleSheet(btn_style)
    window.btn_select_folder.clicked.connect(window.select_folder)
    action_row.addWidget(window.btn_select_folder)

    window.format_combo = QComboBox()
    for fmt in ["PDF", "DOCX", "HTML", "EPUB", "PNG", "JPG", "PPTX", "REVEAL"]:
        window.format_combo.addItem(fmt, fmt)
    window.format_combo.setFixedWidth(90)
    window.format_combo.setStyleSheet("""
        QComboBox { padding: 5px 8px; font-size: 11px; border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 6px; color: #e2e8f0; background: rgba(255,255,255,0.04); }
        QComboBox:hover { border-color: rgba(99,102,241,0.3); }
        QComboBox::drop-down { border: none; width: 20px; }
    """)
    action_row.addWidget(window.format_combo)

    window.btn_convert = QPushButton("Convert")
    window.btn_convert.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_convert.setEnabled(False)
    window.btn_convert.setStyleSheet("""
        QPushButton { background: #3b82f6; color: white; font-weight: 600; padding: 5px 18px;
                      border: none; border-radius: 6px; font-size: 12px; }
        QPushButton:hover { background: #2563eb; }
        QPushButton:disabled { background: rgba(59,130,246,0.3); color: #64748b; }
    """)
    window.btn_convert.clicked.connect(window.convert_files)
    action_row.addWidget(window.btn_convert)

    window.btn_watch = QPushButton("Watch")
    window.btn_watch.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_watch.setToolTip("Auto-convert on file change")
    window.btn_watch.setEnabled(False)
    window.btn_watch.setStyleSheet("""
        QPushButton { background: transparent; border: 1px solid rgba(255,255,255,0.08);
                      border-radius: 6px; padding: 5px 12px; font-size: 11px; color: #94a3b8; }
        QPushButton:hover { background: rgba(255,255,255,0.06); border-color: rgba(59,130,246,0.3); color: #e2e8f0; }
        QPushButton:disabled { color: #475569; }
    """)
    window.btn_watch.clicked.connect(window.toggle_watch)
    action_row.addWidget(window.btn_watch)

    window.btn_cancel = QPushButton("Cancel")
    window.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
    window.btn_cancel.hide()
    window.btn_cancel.setStyleSheet("""
        QPushButton { background: #ef4444; color: white; font-weight: 600; padding: 5px 18px;
                      border: none; border-radius: 6px; font-size: 12px; }
        QPushButton:hover { background: #dc2626; }
    """)
    window.btn_cancel.clicked.connect(window.cancel_conversion)
    action_row.addWidget(window.btn_cancel)

    def _update_convert_button_text(idx):
        fmt = window.format_combo.currentText()
        window.btn_convert.setText(f"Convert to {fmt}")
    window.format_combo.currentIndexChanged.connect(_update_convert_button_text)

    content_layout.addLayout(action_row)

    # ── Progress Bar ──
    window.progress_bar = QProgressBar()
    window.progress_bar.setValue(0)
    window.progress_bar.setTextVisible(False)
    window.progress_bar.setFixedHeight(3)
    window.progress_bar.setStyleSheet("""
        QProgressBar { border: none; background: rgba(255,255,255,0.04); }
        QProgressBar::chunk { background: #3b82f6; border-radius: 2px; }
    """)
    content_layout.addWidget(window.progress_bar)

    # ── Formatting Toolbar (minimal) ──
    window.format_toolbar = QWidget()
    toolbar_layout = QHBoxLayout(window.format_toolbar)
    toolbar_layout.setContentsMargins(0, 0, 0, 0)
    toolbar_layout.setSpacing(2)

    tb_style = """
        QPushButton { background: transparent; border: 1px solid rgba(255,255,255,0.06);
                      border-radius: 4px; padding: 3px 8px; font-size: 11px; color: #94a3b8;
                      min-width: 24px; }
        QPushButton:hover { background: rgba(99,102,241,0.1); border-color: rgba(99,102,241,0.2); color: #e2e8f0; }
    """

    def _tb(text, tooltip, slot):
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(tb_style)
        btn.clicked.connect(slot)
        return btn

    toolbar_layout.addWidget(_tb("B", "Bold (Ctrl+B)", window.format_bold))
    toolbar_layout.addWidget(_tb("I", "Italic (Ctrl+I)", window.format_italic))
    toolbar_layout.addWidget(_tb("H1", "Heading 1", lambda: window.format_header(1)))
    toolbar_layout.addWidget(_tb("H2", "Heading 2", lambda: window.format_header(2)))
    toolbar_layout.addWidget(_tb("<>", "Code", window.format_code))
    toolbar_layout.addWidget(_tb('"', "Quote", window.format_quote))
    toolbar_layout.addWidget(_tb("•", "List", window.format_list))
    toolbar_layout.addWidget(_tb("⎘", "Page break", window.insert_page_break))
    sep = QFrame(); sep.setFrameShape(QFrame.Shape.VLine); sep.setStyleSheet("color: rgba(255,255,255,0.06);")
    toolbar_layout.addWidget(sep)
    toolbar_layout.addWidget(_tb("Lint", "Markdown linter", window.run_linter))
    toolbar_layout.addWidget(_tb("TOC", "Table of Contents", window.show_toc_generator))
    toolbar_layout.addWidget(_tb("Format", "Auto-format", window.format_markdown_document))
    toolbar_layout.addWidget(_tb("Snippets", "Insert snippet (Ctrl+Space)", window.show_snippets_dialog))
    sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.VLine); sep2.setStyleSheet("color: rgba(255,255,255,0.06);")
    toolbar_layout.addWidget(sep2)
    toolbar_layout.addWidget(_tb("Print", "Print (Ctrl+P)", window.print_document))
    toolbar_layout.addWidget(_tb("HTML", "Copy as HTML", window.copy_styled_html))
    toolbar_layout.addStretch()

    content_layout.addWidget(window.format_toolbar)

    # ── Stats Label ──
    window.stats_label = QLabel("")
    window.stats_label.setStyleSheet("font-size: 10px; color: #475569; padding: 0 4px;")
    content_layout.addWidget(window.stats_label)

    # ── Editor + Preview Split ──
    window.editor_splitter = QSplitter(Qt.Orientation.Horizontal)
    window.editor_splitter.setHandleWidth(1)
    window.editor_splitter.setStyleSheet("QSplitter::handle { background: rgba(255,255,255,0.04); }")

    # Left: Editor
    editor_container = QWidget()
    editor_layout = QVBoxLayout(editor_container)
    editor_layout.setContentsMargins(0, 0, 0, 0)
    editor_layout.setSpacing(0)

    window.live_editor = QTextEdit()
    window.live_editor.setPlaceholderText("Start typing Markdown here...\n\n# Heading\n\nParagraph text\n\n- list item\n\n**bold** *italic*")
    window.live_editor.setStyleSheet("""
        QTextEdit { background-color: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255,255,255,0.06);
                    border-radius: 6px; padding: 12px; font-family: 'JetBrains Mono', 'Cascadia Code', monospace;
                    font-size: 13px; color: #e2e8f0; selection-background-color: #3b82f6; }
        QTextEdit:focus { border: 1px solid rgba(59,130,246,0.3); }
    """)
    editor_layout.addWidget(window.live_editor)

    # Search panel (hidden by default)
    window.search_panel = QWidget()
    sp = QHBoxLayout(window.search_panel)
    sp.setContentsMargins(4, 4, 4, 4)
    window.search_panel.setStyleSheet("background: rgba(15,23,42,0.9); border: 1px solid rgba(255,255,255,0.06); border-radius: 4px;")
    window.label_search_find = QLabel("Find:")
    window.label_search_find.setStyleSheet("font-size: 10px; color: #64748b;")
    window.search_find_input = QLineEdit()
    window.search_find_input.setPlaceholderText("Search...")
    window.search_find_input.setStyleSheet("background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); border-radius: 3px; padding: 2px 6px; font-size: 11px; color: #e2e8f0;")
    window.btn_search_next = QPushButton("Next")
    window.btn_search_next.setStyleSheet("QPushButton { background: #3b82f6; color: white; border: none; border-radius: 3px; padding: 2px 8px; font-size: 10px; } QPushButton:hover { background: #2563eb; }")
    window.btn_replace_all = QPushButton("Replace All")
    window.btn_replace_all.setStyleSheet("QPushButton { background: transparent; border: 1px solid rgba(255,255,255,0.1); border-radius: 3px; padding: 2px 8px; font-size: 10px; color: #94a3b8; } QPushButton:hover { background: rgba(255,255,255,0.06); }")
    window.btn_search_close = QPushButton("✕")
    window.btn_search_close.setStyleSheet("QPushButton { background: transparent; border: none; font-size: 11px; color: #64748b; } QPushButton:hover { color: #ef4444; }")
    window.search_replace_input = QLineEdit()
    window.search_replace_input.setPlaceholderText("Replace...")
    window.search_replace_input.setStyleSheet("background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); border-radius: 3px; padding: 2px 6px; font-size: 11px; color: #e2e8f0;")
    window.label_search_replace = QLabel("Replace:")
    window.label_search_replace.setStyleSheet("font-size: 10px; color: #64748b;")
    window.search_regex_checkbox = QCheckBox("RegEx")
    window.search_regex_checkbox.setStyleSheet("font-size: 10px; color: #64748b;")

    sp.addWidget(window.label_search_find)
    sp.addWidget(window.search_find_input, 1)
    sp.addWidget(window.btn_search_next)
    sp.addWidget(window.label_search_replace)
    sp.addWidget(window.search_replace_input, 1)
    sp.addWidget(window.btn_replace_all)
    sp.addWidget(window.search_regex_checkbox)
    sp.addWidget(window.btn_search_close)
    window.search_panel.hide()
    editor_layout.addWidget(window.search_panel)

    window.editor_splitter.addWidget(editor_container)

    # Right: Preview
    window.preview_output = QTextBrowser()
    window.preview_output.setOpenExternalLinks(True)
    window.preview_output.setStyleSheet("""
        QTextBrowser { background-color: rgba(15, 23, 42, 0.5); border: 1px solid rgba(255,255,255,0.06);
                       border-radius: 6px; padding: 12px; font-size: 13px; color: #e2e8f0; }
    """)
    window.editor_splitter.addWidget(window.preview_output)
    window.editor_splitter.setSizes([400, 400])

    content_layout.addWidget(window.editor_splitter, 1)

    # ── Log (collapsible at bottom) ──
    window.tabs = QTabWidget()
    window.tabs.setTabBarAutoHide(True)
    window.tabs.setStyleSheet("""
        QTabWidget::pane { border: 1px solid rgba(255,255,255,0.04); border-radius: 4px; background: rgba(15,23,42,0.4); }
        QTabBar::tab { background: transparent; border: none; padding: 4px 12px; font-size: 10px; color: #64748b; }
        QTabBar::tab:selected { color: #e2e8f0; border-bottom: 1px solid #3b82f6; }
    """)

    log_container = QWidget()
    log_layout = QVBoxLayout(log_container)
    log_layout.setContentsMargins(0, 0, 0, 0)

    window.log_output = QTextBrowser()
    window.log_output.setReadOnly(True)
    window.log_output.setOpenExternalLinks(True)
    window.log_output.setMaximumHeight(120)
    window.log_output.setStyleSheet("""
        QTextBrowser { background: rgba(15,23,42,0.6); border: none; padding: 8px;
                       font-family: monospace; font-size: 11px; color: #94a3b8; }
    """)
    log_layout.addWidget(window.log_output)
    window.tabs.addTab(log_container, "Log")

    content_layout.addWidget(window.tabs)

    # ── Workspace Explorer (hidden by default) ──
    window.explorer_group = QGroupBox("Explorer")
    window.explorer_group.hide()
    window.explorer_group.setStyleSheet("""
        QGroupBox { font-weight: 600; border: 1px solid rgba(255,255,255,0.06); border-radius: 6px;
                    margin-top: 8px; padding-top: 14px; color: #94a3b8;
                    background: rgba(15,23,42,0.3); }
        QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
    """)
    explorer_layout = QVBoxLayout(window.explorer_group)
    explorer_layout.setContentsMargins(6, 6, 6, 6)
    window.explorer_search = QLineEdit()
    window.explorer_search.setPlaceholderText("Search files...")
    window.explorer_search.setStyleSheet("background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); border-radius: 4px; padding: 4px 8px; font-size: 11px; color: #e2e8f0;")
    explorer_layout.addWidget(window.explorer_search)
    window.explorer_list = QListWidget()
    window.explorer_list.setStyleSheet("""
        QListWidget { background: transparent; border: none; font-size: 11px; color: #94a3b8; }
        QListWidget::item { padding: 4px 8px; border-radius: 3px; }
        QListWidget::item:hover { background: rgba(255,255,255,0.04); }
        QListWidget::item:selected { background: rgba(59,130,246,0.15); color: #e2e8f0; }
    """)
    explorer_layout.addWidget(window.explorer_list)

    content_layout.addWidget(window.explorer_group)

    root.addWidget(content, 1)

    # ── Connections ──
    window.explorer_search.textChanged.connect(lambda t: window.filter_workspace_explorer(t))
    window.explorer_list.itemDoubleClicked.connect(lambda item: window.load_workspace_file(item))
    window.btn_search_next.clicked.connect(window.search_next)
    window.btn_replace_all.clicked.connect(window.replace_all_occurrences)
    window.btn_search_close.clicked.connect(window.search_panel.hide)
    window.search_find_input.returnPressed.connect(window.search_next)


def _setup_settings_dialog(window):
    dlg = QDialog(window)
    dlg.setWindowTitle("Settings")
    dlg.setMinimumWidth(420)
    window.btn_advanced_settings.clicked.connect(dlg.exec)

    layout = QVBoxLayout(dlg)
    tabs = QTabWidget()

    # ── Page Tab ──
    page_tab = QWidget()
    form = QFormLayout(page_tab)
    form.setSpacing(6)

    window.doc_theme_combo = QComboBox()
    window.doc_theme_combo.addItem("Modern", "theme_modern.css")
    window.doc_theme_combo.addItem("Classic Book", "theme_classic.css")
    window.doc_theme_combo.addItem("Dark PDF", "theme_dark_pdf.css")
    form.addRow("Theme:", window.doc_theme_combo)

    window.code_theme_combo = QComboBox()
    window.code_theme_combo.addItem("Light (Tango)", "pygments.css")
    window.code_theme_combo.addItem("Dark (Monokai)", "pygments_dark.css")
    form.addRow("Code style:", window.code_theme_combo)

    window.paper_combo = QComboBox()
    window.paper_combo.addItems(["A4", "Letter", "Legal", "A3", "A5"])
    form.addRow("Paper:", window.paper_combo)

    window.margins_input = QLineEdit()
    window.margins_input.setPlaceholderText("e.g. 20mm 15mm")
    form.addRow("Margins:", window.margins_input)

    window.chk_page_numbers = QCheckBox("Page numbers")
    form.addRow("", window.chk_page_numbers)

    window.combo_page_format = QComboBox()
    window.combo_page_format.addItem("Simple (1)", "simple")
    window.combo_page_format.addItem("Slash (1/5)", "slash")
    window.combo_page_format.addItem("Text (Page 1 of 5)", "text")
    form.addRow("Numbering:", window.combo_page_format)

    window.chk_presentation_mode = QCheckBox("Presentation mode")
    form.addRow("", window.chk_presentation_mode)

    window.chk_compress = QCheckBox("Compress PDF")
    form.addRow("", window.chk_compress)

    tabs.addTab(page_tab, "Page")

    # ── Security Tab ──
    sec_tab = QWidget()
    form_sec = QFormLayout(sec_tab)
    form_sec.setSpacing(6)

    window.watermark_input = QLineEdit()
    window.watermark_input.setPlaceholderText("e.g. Draft")
    form_sec.addRow("Watermark:", window.watermark_input)

    window.footer_input = QLineEdit()
    window.footer_input.setPlaceholderText("{date} {filename} {title}")
    form_sec.addRow("Footer:", window.footer_input)

    window.pdf_password_input = QLineEdit()
    window.pdf_password_input.setPlaceholderText("Password (leave empty for none)")
    form_sec.addRow("PDF password:", window.pdf_password_input)

    css_row = QHBoxLayout()
    window.custom_css_input = QLineEdit()
    window.custom_css_input.setPlaceholderText("Path to .css file")
    window.btn_select_css = QPushButton("Browse")
    window.btn_select_css.clicked.connect(window.select_custom_css)
    css_row.addWidget(window.custom_css_input)
    css_row.addWidget(window.btn_select_css)
    form_sec.addRow("Custom CSS:", css_row)

    tabs.addTab(sec_tab, "Security")

    # ── Advanced Tab ──
    adv_tab = QWidget()
    form_adv = QFormLayout(adv_tab)
    form_adv.setSpacing(6)

    docx_row = QHBoxLayout()
    window.docx_template_input = QLineEdit()
    window.docx_template_input.setPlaceholderText("Path to .docx template")
    window.btn_select_docx = QPushButton("Browse")
    window.btn_select_docx.clicked.connect(window.select_docx_template)
    docx_row.addWidget(window.docx_template_input)
    docx_row.addWidget(window.btn_select_docx)
    form_adv.addRow("DOCX template:", docx_row)

    preset_row = QHBoxLayout()
    window.preset_combo = QComboBox()
    window.btn_save_preset = QPushButton("Save")
    window.btn_save_preset.clicked.connect(window.save_preset)
    window.btn_delete_preset = QPushButton("Delete")
    window.btn_delete_preset.clicked.connect(window.delete_preset)
    preset_row.addWidget(window.preset_combo, 1)
    preset_row.addWidget(window.btn_save_preset)
    preset_row.addWidget(window.btn_delete_preset)
    form_adv.addRow("Presets:", preset_row)

    tabs.addTab(adv_tab, "Advanced")

    layout.addWidget(tabs)

    btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
    btn_box.accepted.connect(dlg.accept)
    layout.addWidget(btn_box)
