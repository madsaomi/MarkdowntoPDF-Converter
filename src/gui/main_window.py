import sys
import os
import re
import logging
import json
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QTextEdit, QProgressBar,
    QMessageBox, QComboBox, QLineEdit, QGroupBox, QGridLayout, QMenu,
    QTabWidget, QTextBrowser, QInputDialog, QListWidgetItem, QListWidget,
    QSpinBox, QFormLayout, QDialog, QDialogButtonBox, QColorDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings, QFileSystemWatcher, QMutex, QTimer, QEvent, QRegularExpression
from PyQt6.QtGui import QIcon, QAction, QShortcut, QKeySequence, QCursor, QColor

from src.config import AppConfig
from src.core.parser import MarkdownParser
from src.core.renderer import PDFRenderer
from src.core.docx_renderer import DOCXRenderer
from src.core.pdf_encrypt import encrypt_pdf
from src.gui.ui_layout import setup_ui
from src.__version__ import __version__
from src.gui.translations import TRANSLATIONS
from src.gui.translator import Translator
from src.gui.welcome_docs import WELCOME_RU, WELCOME_EN

# ──────────────────────── Logging setup ────────────────────────

LOG_DIR = AppConfig.log_dir()
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "app.log"), encoding="utf-8"),
    ],
)
logger = logging.getLogger("MarkdownToPDF")




from src.gui.models import ExportFormat, DocTheme, CodeTheme, ConversionOptions
from src.gui.threads import ConversionThread, KrokiCheckThread
from src.gui.dialogs import (
    DocumentBuilderDialog, ReadabilityDashboardDialog, DocumentAuditorDialog,
    MarkdownTOCDialog, SnippetsDialog, MarkdownTableDialog, ColorButton,
    PDFStyleEditorDialog, RevisionHistoryDialog
)
from src.gui import editor_commands, file_manager, preview_manager, document_tools, settings_manager
from src.gui.multi_cursor import MultiCursorManager
from src.core.template_vars import process_document_vars
from src.core.plugin_system import load_plugins_from_dir, emit_hook
from src.core.latex_preview import find_latex_expressions, render_latex_in_html
from src.core.html_to_markdown import html_to_markdown
from src.core.flashcards import extract_flashcards
from src.core.citation_manager import get_citations, generate_bibliography, add_citation
from src.core.glossary import extract_definitions
from src.core.quiz_generator import generate_quiz_from_text
from src.core.tts_engine import strip_markdown_for_tts
from src.gui.toast import ToastNotification
from src.gui.about_dialog import AboutDialog
from src.gui.custom_titlebar import CustomTitleBar
from src.gui.ambient_glow import AmbientGlowWidget

# ──────────────────────── Dark / Light stylesheets ────────────────────────

LIGHT_STYLE = """
/* ── Glassmorphism Light Theme (2026) ── */
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #e8eaf6, stop:0.3 #f3e5f5, stop:0.6 #e0f7fa, stop:1 #e8f5e9);
}
QWidget {
    background-color: transparent;
    color: #1a1a2e;
    font-family: 'Segoe UI', 'SF Pro Display', -apple-system, sans-serif;
}
QLabel {
    color: #1a1a2e;
    font-size: 13px;
}
QLabel[styleSheet*="font-size: 18px"] {
    color: #1a1a2e;
}
/* ── Glassmorphism inputs ── */
QLineEdit, QTextEdit, QTextBrowser {
    background-color: rgba(255, 255, 255, 0.72);
    border: 1px solid rgba(255, 255, 255, 0.5);
    border-radius: 10px;
    padding: 8px 12px;
    color: #1a1a2e;
    selection-background-color: rgba(99, 102, 241, 0.3);
}
QLineEdit:focus, QTextEdit:focus {
    border: 1.5px solid rgba(99, 102, 241, 0.5);
    background-color: rgba(255, 255, 255, 0.85);
}
/* ── Glassmorphism ComboBox ── */
QComboBox {
    background-color: rgba(255, 255, 255, 0.72);
    border: 1px solid rgba(255, 255, 255, 0.5);
    border-radius: 10px;
    padding: 6px 12px;
    color: #1a1a2e;
    font-weight: 500;
}
QComboBox:hover {
    background-color: rgba(255, 255, 255, 0.85);
    border-color: rgba(99, 102, 241, 0.3);
}
QComboBox QAbstractItemView {
    background-color: rgba(255, 255, 255, 0.95);
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 8px;
    padding: 4px;
    selection-background-color: rgba(99, 102, 241, 0.15);
    selection-color: #1a1a2e;
    outline: none;
}
/* ── Glassmorphism GroupBox ── */
QGroupBox {
    font-weight: 600;
    border: 1px solid rgba(255, 255, 255, 0.4);
    border-radius: 12px;
    margin-top: 14px;
    padding-top: 18px;
    color: #1a1a2e;
    background-color: rgba(255, 255, 255, 0.35);
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 8px;
    color: #4a4a6a;
}
/* ── Progress bar ── */
QProgressBar {
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 6px;
    background-color: rgba(255, 255, 255, 0.5);
    height: 8px;
    text-align: center;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366f1, stop:1 #8b5cf6);
    border-radius: 5px;
}
/* ── Menu bar ── */
QMenuBar {
    background-color: rgba(255, 255, 255, 0.6);
    color: #1a1a2e;
    border-bottom: 1px solid rgba(0, 0, 0, 0.06);
    font-weight: 500;
}
QMenuBar::item {
    padding: 6px 10px;
    border-radius: 6px;
}
QMenuBar::item:selected {
    background-color: rgba(99, 102, 241, 0.1);
}
QMenu {
    background-color: rgba(255, 255, 255, 0.92);
    color: #1a1a2e;
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 10px;
    padding: 6px;
}
QMenu::item {
    padding: 7px 24px 7px 12px;
    border-radius: 6px;
}
QMenu::item:selected {
    background-color: rgba(99, 102, 241, 0.12);
}
/* ── Tab widget ── */
QTabWidget::pane {
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 10px;
    background-color: rgba(255, 255, 255, 0.4);
    top: -1px;
}
QTabBar::tab {
    background-color: rgba(255, 255, 255, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.3);
    padding: 8px 18px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    color: #6b7280;
    font-weight: 500;
}
QTabBar::tab:selected {
    background-color: rgba(255, 255, 255, 0.85);
    color: #1a1a2e;
    font-weight: 600;
    border-bottom: 2px solid #6366f1;
}
QTabBar::tab:hover:!selected {
    background-color: rgba(255, 255, 255, 0.7);
}
/* ── Scrollbar ── */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: rgba(0, 0, 0, 0.15);
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(0, 0, 0, 0.25);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: transparent;
    height: 8px;
}
QScrollBar::handle:horizontal {
    background: rgba(0, 0, 0, 0.15);
    border-radius: 4px;
    min-width: 30px;
}
/* ── Tooltips ── */
QToolTip {
    background-color: rgba(26, 26, 46, 0.9);
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12px;
}
/* ── Splitter ── */
QSplitter::handle {
    background-color: rgba(0, 0, 0, 0.06);
    width: 2px;
}
QSplitter::handle:hover {
    background-color: rgba(99, 102, 241, 0.3);
}
"""

DARK_STYLE = """
/* ── Dark Glassmorphism Theme (2026) ── */
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0f0f1a, stop:0.25 #1a0f2e, stop:0.5 #0f1a2e, stop:0.75 #0f2e1a, stop:1 #1a1a2e);
}
QWidget {
    background-color: transparent;
    color: #e2e8f0;
    font-family: 'Segoe UI', 'SF Pro Display', -apple-system, sans-serif;
}
QLabel {
    color: #e2e8f0;
    font-size: 13px;
}
/* ── Dark glassmorphism inputs ── */
QLineEdit, QTextEdit, QTextBrowser {
    background-color: rgba(30, 30, 50, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 8px 12px;
    color: #e2e8f0;
    selection-background-color: rgba(139, 92, 246, 0.35);
}
QLineEdit:focus, QTextEdit:focus {
    border: 1.5px solid rgba(139, 92, 246, 0.5);
    background-color: rgba(30, 30, 50, 0.8);
}
/* ── Dark glassmorphism ComboBox ── */
QComboBox {
    background-color: rgba(30, 30, 50, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 6px 12px;
    color: #e2e8f0;
    font-weight: 500;
}
QComboBox:hover {
    background-color: rgba(40, 40, 65, 0.8);
    border-color: rgba(139, 92, 246, 0.3);
}
QComboBox QAbstractItemView {
    background-color: rgba(20, 20, 35, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    padding: 4px;
    color: #e2e8f0;
    selection-background-color: rgba(139, 92, 246, 0.2);
    selection-color: #f0f0ff;
    outline: none;
}
/* ── Dark glassmorphism GroupBox ── */
QGroupBox {
    font-weight: 600;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
    margin-top: 14px;
    padding-top: 18px;
    color: #e2e8f0;
    background-color: rgba(30, 30, 50, 0.35);
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 8px;
    color: #a0a0c0;
}
/* ── Dark progress bar ── */
QProgressBar {
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 6px;
    background-color: rgba(30, 30, 50, 0.5);
    height: 8px;
    text-align: center;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #8b5cf6, stop:1 #06b6d4);
    border-radius: 5px;
}
/* ── Dark menu bar ── */
QMenuBar {
    background-color: rgba(15, 15, 26, 0.7);
    color: #e2e8f0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    font-weight: 500;
}
QMenuBar::item {
    padding: 6px 10px;
    border-radius: 6px;
}
QMenuBar::item:selected {
    background-color: rgba(139, 92, 246, 0.12);
}
QMenu {
    background-color: rgba(20, 20, 35, 0.92);
    color: #e2e8f0;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    padding: 6px;
}
QMenu::item {
    padding: 7px 24px 7px 12px;
    border-radius: 6px;
}
QMenu::item:selected {
    background-color: rgba(139, 92, 246, 0.15);
}
/* ── Dark tab widget ── */
QTabWidget::pane {
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    background-color: rgba(20, 20, 35, 0.4);
    top: -1px;
}
QTabBar::tab {
    background-color: rgba(30, 30, 50, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.06);
    padding: 8px 18px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    color: #6b7280;
    font-weight: 500;
}
QTabBar::tab:selected {
    background-color: rgba(30, 30, 50, 0.8);
    color: #e2e8f0;
    font-weight: 600;
    border-bottom: 2px solid #8b5cf6;
}
QTabBar::tab:hover:!selected {
    background-color: rgba(40, 40, 65, 0.6);
}
/* ── Dark scrollbar ── */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(255, 255, 255, 0.2);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: transparent;
    height: 8px;
}
QScrollBar::handle:horizontal {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    min-width: 30px;
}
/* ── Dark tooltips ── */
QToolTip {
    background-color: rgba(30, 30, 50, 0.95);
    color: #e2e8f0;
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12px;
}
/* ── Dark splitter ── */
QSplitter::handle {
    background-color: rgba(255, 255, 255, 0.04);
    width: 2px;
}
QSplitter::handle:hover {
    background-color: rgba(139, 92, 246, 0.3);
}
"""

APP_NAME = "MarkdownToPDF_Pro"




# ──────────────────────── Main Window ────────────────────────

class MainWindow(QMainWindow):
    MAX_RECENT = 10

    def __init__(self):
        super().__init__()
        self.setMinimumSize(720, 620)
        self.setAcceptDrops(True)
        self.is_dark = False
        self.selected_files: list[str] = []
        self.last_output_dir = ""
        self.thread: ConversionThread | None = None
        self.presets = {}
        self.zoom_level = 0
        self.active_workspace_folder = None
        self.current_workspace_file = None
        self.writing_goal = 0
        self.goal_celebrated = False
        self.kroki_available = True
        self._last_revision_time = 0
        self.translator = Translator(self.settings.value("language", "ru", str) if hasattr(self, 'settings') else "ru")

        # Start Kroki.io connectivity check
        self.kroki_thread = KrokiCheckThread()
        self.kroki_thread.finished.connect(self.on_kroki_check_finished)
        self.kroki_thread.start()

        # Settings persistence
        self.settings = QSettings(AppConfig.APP_NAME, AppConfig.APP_NAME)
        self.current_lang = self.settings.value("language", "ru", str)
        self.translator.set_lang(self.current_lang)
        self.export_history = self.settings.value("export_history", [], list)

        # File watcher for auto-regenerate mode
        self.watcher = QFileSystemWatcher(self)
        self.watcher.fileChanged.connect(self.on_file_changed)
        self.watch_active = False
        self.watch_output_dir = ""

        # App icon
        icon_path = AppConfig.icon_path()
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        setup_ui(self)

        # Custom title bar (optional - uncomment to enable)
        # self._setup_custom_titlebar()

        # Status bar
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background: rgba(15, 15, 26, 0.6);
                color: #94a3b8;
                border-top: 1px solid rgba(255, 255, 255, 0.04);
                font-size: 11px;
                padding: 2px 8px;
            }
        """)
        self.statusBar().showMessage("Ready")

        # Ambient glow (optional - uncomment to enable)
        # self._setup_ambient_glow()

        # Connect Page Numbering toggled state
        self.combo_page_format.setEnabled(self.chk_page_numbers.isChecked())
        self.chk_page_numbers.toggled.connect(self.combo_page_format.setEnabled)
        
        # Connect Language actions
        self.action_lang_ru.triggered.connect(lambda: self.change_lang("ru"))
        self.action_lang_en.triggered.connect(lambda: self.change_lang("en"))
        
        self._setup_shortcuts()
        self.load_settings()
        self.load_presets()
        self.preset_combo.currentIndexChanged.connect(self.on_preset_changed)
        
        self.retranslate_ui()

        # Connect search panel actions
        self.btn_search_next.clicked.connect(self.search_next)
        self.btn_replace_all.clicked.connect(self.replace_all_occurrences)
        self.btn_search_close.clicked.connect(self.search_panel.hide)
        self.search_find_input.returnPressed.connect(self.search_next)

        # Markdown syntax highlighting in editor
        from src.gui.highlighter import MarkdownHighlighter
        self.highlighter = MarkdownHighlighter(self.live_editor.document())
        self.highlighter.set_theme(self.is_dark)

        # Setup Auto-Save draft path
        from PyQt6.QtCore import QStandardPaths
        self.app_data_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        if not os.path.exists(self.app_data_dir):
            os.makedirs(self.app_data_dir, exist_ok=True)
        self.draft_path = os.path.join(self.app_data_dir, "draft.md")

        # Auto-Save timer (every 10 seconds)
        self.autosave_timer = QTimer(self)
        self.autosave_timer.setInterval(10000)
        self.autosave_timer.timeout.connect(self.autosave_draft)
        self.autosave_timer.start()

        # Load default welcome document or restore draft
        self.is_welcome_doc_active = False
        if not self.selected_files:
            if os.path.exists(self.draft_path) and os.path.getsize(self.draft_path) > 0:
                self.restore_draft_if_exists()
            else:
                self.load_welcome_document()

        # Multi-cursor manager
        self.multi_cursor = MultiCursorManager(self.live_editor)

        # Plugin system - load from plugins dir
        plugins_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "plugins")
        os.makedirs(plugins_dir, exist_ok=True)
        load_plugins_from_dir(plugins_dir)

        # Live Preview setup
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(500)
        self.preview_timer.timeout.connect(self._render_live_preview)
        self.live_editor.textChanged.connect(self.on_editor_changed)
        self.chk_presentation_mode.toggled.connect(self._render_live_preview)
        self.live_editor.installEventFilter(self)
        self.live_editor.verticalScrollBar().valueChanged.connect(self.sync_scroll_preview)

        logger.info("Application started (v%s)", __version__)

    def _resolve_asset(self, rel_path: str) -> str:
        return os.path.join(AppConfig.base_path(), rel_path)

    def on_kroki_check_finished(self, available: bool):
        self.kroki_available = available
        logger.info("Kroki.io availability checked: %s", available)
        # Refresh preview once check completes
        self._render_live_preview()

    def _setup_shortcuts(self):
        """Register keyboard shortcuts."""
        QShortcut(QKeySequence("Ctrl+O"), self, activated=self.select_files)
        QShortcut(QKeySequence("Ctrl+Shift+O"), self, activated=self.select_folder)
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self.convert_files)
        QShortcut(QKeySequence("Ctrl+D"), self, activated=self.toggle_theme)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self.toggle_search_panel)
        QShortcut(QKeySequence("Ctrl+Shift+T"), self, activated=self.update_markdown_toc_in_editor)
        QShortcut(QKeySequence("Ctrl+Shift+G"), self, activated=self.show_table_generator_dialog)
        QShortcut(QKeySequence("Ctrl+Shift+A"), self, activated=self.show_document_audit)
        QShortcut(QKeySequence("Ctrl+Shift+Return"), self, activated=self.insert_page_break)
        QShortcut(QKeySequence("Ctrl+P"), self, activated=self.print_document)
        QShortcut(QKeySequence("Ctrl++"), self, activated=self.zoom_in)
        QShortcut(QKeySequence("Ctrl+="), self, activated=self.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, activated=self.zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self, activated=self.zoom_reset)
        QShortcut(QKeySequence("Ctrl+Space"), self, activated=self.show_snippets_dialog)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self, activated=self.toggle_zen_mode)
        QShortcut(QKeySequence("Ctrl+Shift+F"), self, activated=self.format_markdown_document)
        QShortcut(QKeySequence("Ctrl+/"), self, activated=self.show_shortcuts)

    # ─── Settings persistence ───

    def load_settings(self):
        self.doc_theme_combo.setCurrentIndex(self.settings.value("doc_theme", 0, int))
        self.code_theme_combo.setCurrentIndex(self.settings.value("code_theme", 0, int))
        self.paper_combo.setCurrentIndex(self.settings.value("paper_size", 0, int))
        
        # OS Theme sync fallback
        if not self.settings.contains("dark_mode"):
            self.is_dark = (self.get_windows_theme() == "dark")
        else:
            self.is_dark = self.settings.value("dark_mode", False, bool)

        self.last_output_dir = self.settings.value("last_output_dir", "", str)
        self.custom_css_input.setText(self.settings.value("custom_css", "", str))
        self.format_combo.setCurrentIndex(self.settings.value("export_format", 0, int))
        self.chk_page_numbers.setChecked(self.settings.value("page_numbers", False, bool))
        self.combo_page_format.setCurrentIndex(self.settings.value("page_num_format", 0, int))
        self.combo_page_format.setEnabled(self.chk_page_numbers.isChecked())
        self.chk_presentation_mode.setChecked(self.settings.value("presentation_mode", False, bool))
        if self.is_dark:
            QApplication.instance().setStyleSheet(DARK_STYLE)
            self.btn_theme.setText("☀️ Светлая тема")
        else:
            QApplication.instance().setStyleSheet(LIGHT_STYLE)
            self.btn_theme.setText("🌙 Тёмная тема")
        self.update_recent_menu()

    def save_settings(self):
        self.settings.setValue("doc_theme", self.doc_theme_combo.currentIndex())
        self.settings.setValue("code_theme", self.code_theme_combo.currentIndex())
        self.settings.setValue("paper_size", self.paper_combo.currentIndex())
        self.settings.setValue("dark_mode", self.is_dark)
        self.settings.setValue("last_output_dir", self.last_output_dir)
        self.settings.setValue("custom_css", self.custom_css_input.text().strip())
        self.settings.setValue("export_format", self.format_combo.currentIndex())
        self.settings.setValue("page_numbers", self.chk_page_numbers.isChecked())
        self.settings.setValue("page_num_format", self.combo_page_format.currentIndex())
        self.settings.setValue("presentation_mode", self.chk_presentation_mode.isChecked())

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

    # ─── Recent files ───

    def add_to_recent(self, filepath: str):
        file_manager.add_to_recent(self, filepath)

    def update_recent_menu(self):
        file_manager.update_recent_menu(self)

    def open_recent(self, filepath: str):
        file_manager.open_recent(self, filepath)

    # ─── Dark / Light toggle ───

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        app = QApplication.instance()
        t = lambda k: TRANSLATIONS[self.current_lang].get(k, k)

        # Smooth fade transition
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
        from PyQt6.QtWidgets import QGraphicsOpacityEffect

        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(250)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        def apply_theme():
            if self.is_dark:
                app.setStyleSheet(DARK_STYLE)
                self.btn_theme.setText(t('btn_theme_light'))
            else:
                app.setStyleSheet(LIGHT_STYLE)
                self.btn_theme.setText(t('btn_theme_dark'))

            if hasattr(self, 'highlighter'):
                self.highlighter.set_theme(self.is_dark)
                self.highlighter.rehighlight()

        anim.finished.connect(lambda: self.setGraphicsEffect(None))
        anim.valueChanged.connect(lambda v: None)
        anim.setStartValue(0.7)
        anim.setEndValue(1.0)
        apply_theme()
        anim.start(QPropertyAnimation.DeleteWhenStopped)
        self._theme_anim = anim

    def preview_code_theme(self):
        theme_file = self.code_theme_combo.currentData()
        theme_dir = AppConfig.template_dir()
        css_path = os.path.join(theme_dir, theme_file)
        css_content = ""
        if os.path.exists(css_path):
            with open(css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()

        sample_code = """<pre><code class="language-python">def hello_world():
    name = "MarkdownToPDF"
    print(f"Hello, {name}!")
    return {"status": True, "count": 42}

class Parser:
    def __init__(self):
        self.patterns = [r"\\*\\*(.+?)\\*\\*", r"`(.+?)`"]

    def parse(self, text):
        for pattern in self.patterns:
            text = re.sub(pattern, r"<strong>\\1</strong>", text)
        return text
</code></pre>"""

        html = f"""<!DOCTYPE html>
<html><head><style>
body {{ font-family: sans-serif; padding: 20px; background: #fff; }}
{css_content}
</style></head><body>
<h3>Предпросмотр темы: {theme_file}</h3>
{sample_code}
</body></html>"""

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Тема кода: {theme_file}")
        dlg.setMinimumSize(500, 400)
        layout = QVBoxLayout(dlg)
        browser = QTextBrowser()
        browser.setHtml(html)
        layout.addWidget(browser)
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(dlg.close)
        layout.addWidget(btn_close)
        dlg.exec()

    # ─── Drag & Drop ───

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(u.toLocalFile().endswith('.md') or u.toLocalFile().endswith(('.pdf', '.docx')) or os.path.isdir(u.toLocalFile()) for u in urls):
                event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        
        folders = [u.toLocalFile() for u in urls if os.path.isdir(u.toLocalFile())]
        if folders:
            folder = folders[0]
            
            msgBox = QMessageBox(self)
            msgBox.setWindowTitle("Перетаскивание папки" if self.current_lang == "ru" else "Folder dropped")
            msgBox.setText("Вы перетащили папку. Что вы хотите с ней сделать?" if self.current_lang == "ru" else "You dropped a folder. What do you want to do?")
            
            btn_merge = msgBox.addButton("Объединить в единую книгу" if self.current_lang == "ru" else "Merge into a book", QMessageBox.ButtonRole.ActionRole)
            btn_open = msgBox.addButton("Открыть как проект" if self.current_lang == "ru" else "Open as workspace", QMessageBox.ButtonRole.ActionRole)
            btn_cancel = msgBox.addButton("Отмена" if self.current_lang == "ru" else "Cancel", QMessageBox.ButtonRole.RejectRole)
            
            msgBox.exec()
            
            if msgBox.clickedButton() == btn_merge:
                dialog = DocumentBuilderDialog(self, lang=self.current_lang)
                dialog.load_folder(folder)
                dialog.exec()
                return
            elif msgBox.clickedButton() == btn_open:
                md_files = [
                    os.path.join(folder, f)
                    for f in os.listdir(folder) if f.endswith('.md')
                ]
                if not md_files:
                    QMessageBox.warning(self, self.tr_msg("msg_folder_empty_title"), self.tr_msg("msg_folder_empty"))
                    return
                self.selected_files = md_files
                self.active_workspace_folder = folder
                self.file_label.setText(self.tr_msg("folder_selected", os.path.basename(folder), len(md_files)))
                self.btn_convert.setEnabled(True)
                self.btn_watch.setEnabled(False)
                self.log_output.clear()
                self.progress_bar.setValue(0)
                self.append_log(self.tr_msg("log_found_folder", len(md_files)))
                self.update_workspace_explorer()
                self.explorer_group.show()
                self.update_preview(md_files[0])
                return
            else:
                return

        md_files = [u.toLocalFile() for u in urls if u.toLocalFile().endswith('.md')]
        if md_files:
            self.selected_files = md_files
            self.active_workspace_folder = None
            self.explorer_group.hide()
            for f in md_files:
                self.add_to_recent(f)
            names = ", ".join(os.path.basename(f) for f in md_files)
            self.file_label.setText(self.tr_msg("files_selected", len(md_files), names))
            self.btn_convert.setEnabled(True)
            self.btn_watch.setEnabled(len(md_files) == 1)
            self.log_output.clear()
            self.progress_bar.setValue(0)
            self.append_log(self.tr_msg("log_dragged", len(md_files)))
            self.update_preview(md_files[0])

        # Handle .pdf/.docx as templates
        template_files = [u.toLocalFile() for u in urls
                          if os.path.splitext(u.toLocalFile())[1].lower() in ('.pdf', '.docx')]
        if template_files:
            template = template_files[0]
            if template.endswith('.docx'):
                self.docx_template_input.setText(template)
            self.append_log(f"📎 Template set: {os.path.basename(template)}")

    # ─── File / Folder selection ───

    def select_custom_css(self):
        file_manager.select_custom_css(self)

    def select_docx_template(self):
        file_manager.select_docx_template(self)

    def select_files(self):
        file_manager.select_files(self)

    def select_folder(self):
        file_manager.select_folder(self)

    # ─── Watch mode ───

    def toggle_watch(self):
        t = lambda k, *args: self.tr_msg(k, *args)
        if not self.watch_active:
            # Turn ON
            if len(self.selected_files) != 1:
                QMessageBox.warning(self, t("msg_watch_title"), t("msg_watch_one_file"))
                return
            if not self.last_output_dir:
                out_dir = QFileDialog.getExistingDirectory(
                    self, "Папка для PDF (Watch)",
                    os.path.dirname(self.selected_files[0])
                )
                if not out_dir:
                    return
                self.last_output_dir = out_dir

            filepath = self.selected_files[0]
            self.watcher.addPath(filepath)
            self.watch_active = True
            self.watch_output_dir = self.last_output_dir
            self.btn_watch.setText(t("btn_watch_on"))
            self.btn_watch.setStyleSheet("""
                QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #059669,stop:1 #10b981); color: white; font-weight: bold;
                              padding: 12px; border: none; border-radius: 8px; font-size: 13px; }
                QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #047857,stop:1 #059669); }
            """)
            self.append_log(t("log_watch_on", os.path.basename(filepath)))
            self.append_log(t("log_watch_on_dir", self.watch_output_dir))
            # Run initial conversion
            self._run_single_conversion(filepath, self.watch_output_dir)
        else:
            # Turn OFF
            self.watcher.removePaths(self.watcher.files())
            self.watch_active = False
            self.btn_watch.setText(t("btn_watch_off"))
            self.btn_watch.setStyleSheet("""
                QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #475569,stop:1 #64748b); color: white; font-weight: bold;
                              padding: 12px; border: none; border-radius: 8px; font-size: 13px; }
                QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #334155,stop:1 #475569); }
            """)
            self.append_log(t("log_watch_off"))

    def on_file_changed(self, filepath: str):
        if self.watch_active and os.path.exists(filepath):
            self.append_log(self.tr_msg("log_watch_change", os.path.basename(filepath)))
            # Some editors delete & recreate files; re-add to watcher
            if filepath not in self.watcher.files():
                self.watcher.addPath(filepath)
            self._run_single_conversion(filepath, self.watch_output_dir)

    def _run_single_conversion(self, filepath: str, out_dir: str):
        options = self._get_options()
        base = os.path.splitext(os.path.basename(filepath))[0]
        ext = self._get_extension(options.export_format)
        out_path = os.path.join(out_dir, base + ext)
        pairs = [(filepath, out_path)]
        self._start_conversion(pairs, out_dir, options)

    # ─── Conversion (unified) ───

    def _start_conversion(self, pairs: list, out_dir: str, options: ConversionOptions):
        """Single entry point for starting any conversion — eliminates duplication."""
        # Safety: cancel and wait for any running thread
        if self.thread is not None and self.thread.isRunning():
            self.thread.cancel()
            self.thread.wait(3000)

        template_dir = self._get_template_dir()
        wp_exe = self._get_weasyprint_path()

        self.thread = ConversionThread(pairs, out_dir, template_dir, options, wp_exe, lang=self.current_lang, kroki_available=self.kroki_available)
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.log.connect(self.append_log)
        self.thread.finished_one.connect(self.on_finished_one)
        self.thread.finished_all.connect(self.on_all_done)
        self.btn_convert.hide()
        self.btn_cancel.show()
        self.btn_cancel.setEnabled(True)
        self.thread.start()

    def convert_files(self):
        if not self.selected_files:
            return

        default_dir = self.last_output_dir or os.path.dirname(self.selected_files[0])
        out_dir = QFileDialog.getExistingDirectory(
            self, "Папка для сохранения файлов", default_dir
        )
        if not out_dir:
            return

        self.last_output_dir = out_dir
        self.btn_convert.setEnabled(False)
        self.btn_convert.setText("⏳ Конвертация...")
        self.btn_convert.setStyleSheet("""
            QPushButton { background: rgba(99, 102, 241, 0.3); color: #94a3b8; font-weight: 700;
                          padding: 12px 24px; border-radius: 12px; font-size: 15px;
                          border: 1px solid rgba(255,255,255,0.05); }
        """)
        self.progress_bar.setValue(0)
        self.log_output.clear()

        options = self._get_options()
        ext = self._get_extension(options.export_format)

        pairs = []
        for f in self.selected_files:
            base = os.path.splitext(os.path.basename(f))[0]
            out_path = os.path.join(out_dir, base + ext)
            pairs.append((f, out_path))

        self._start_conversion(pairs, out_dir, options)

    # ─── Helpers ───

    def _get_template_dir(self) -> str:
        return AppConfig.template_dir()

    def _get_weasyprint_path(self) -> str:
        return AppConfig.weasyprint_exe()

    @staticmethod
    def _get_extension(export_format: str) -> str:
        fmt_map = {
            ExportFormat.PDF: ".pdf",
            ExportFormat.DOCX: ".docx",
            ExportFormat.HTML: ".html",
            ExportFormat.EPUB: ".epub",
            ExportFormat.PNG: ".png",
            ExportFormat.JPG: ".jpg",
            ExportFormat.PPTX: ".pptx",
            ExportFormat.REVEAL: ".html",
        }
        return fmt_map.get(export_format, ".pdf")

    def _get_options(self) -> ConversionOptions:
        return _get_options(self)


    def append_log(self, text: str):
        self.log_output.append(text)

    def cancel_conversion(self):
        if self.thread is not None and self.thread.isRunning():
            self.thread.cancel()
            self.btn_cancel.setEnabled(False)
            self.append_log(self.tr_msg("log_cancel_req"))

    def update_preview(self, filepath: str):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                md_text = f.read()
            self.is_welcome_doc_active = False
            self.live_editor.blockSignals(True)
            self.live_editor.setPlainText(md_text)
            self.live_editor.blockSignals(False)
            self._render_live_preview()
        except Exception as e:
            self.preview_output.setHtml(f"<p style='color:red;'>Ошибка предпросмотра: {e}</p>")
            logger.error("Preview failed for %s: %s", filepath, e, exc_info=True)

    def get_current_document_dir(self) -> str | None:
        if self.current_workspace_file and os.path.exists(self.current_workspace_file):
            return os.path.dirname(os.path.abspath(self.current_workspace_file))
        if self.selected_files and os.path.exists(self.selected_files[0]):
            return os.path.dirname(os.path.abspath(self.selected_files[0]))
        return None

    def _render_live_preview(self):
        preview_manager.render_live_preview(self)

    def on_all_done(self):
        self.btn_cancel.hide()
        self.btn_convert.show()
        self.btn_convert.setEnabled(True)
        self.btn_convert.setText("⚡ Конвертировать")
        self.btn_convert.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #3b82f6);
                color: white; font-weight: 700; padding: 12px 24px; border-radius: 12px; font-size: 15px;
                border: 1px solid rgba(255, 255, 255, 0.15);
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1d4ed8, stop:1 #2563eb); }
            QPushButton:disabled { background: rgba(99, 102, 241, 0.3); color: #94a3b8; }
        """)
        if self.thread is not None and not self.thread.is_cancelled():
            if self.export_history:
                last_file = self.export_history[0]
                self.append_log(f'<a href="file:///{last_file}" style="color: #27ae60; font-weight: bold;">📂 Открыть: {os.path.basename(last_file)}</a>')
            QMessageBox.information(self, self.tr_msg("msg_done_title"), self.tr_msg("msg_done_desc"))
        else:
            QMessageBox.warning(self, self.tr_msg("msg_cancel_title"), self.tr_msg("msg_cancel_desc"))

    # ─── Presets ───

    def load_presets(self):
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        
        # Load presets dict from settings
        presets_str = self.settings.value("presets", "{}", str)
        try:
            self.presets = json.loads(presets_str)
        except Exception:
            self.presets = {}
            
        default_label = "(по умолчанию)" if self.current_lang == "ru" else "(default)"
        self.preset_combo.addItem(default_label)
        
        for name in sorted(self.presets.keys()):
            self.preset_combo.addItem(name)
            
        self.preset_combo.blockSignals(False)

    def save_preset(self):
        title = self.tr_msg("preset_prompt_title")
        desc = self.tr_msg("preset_prompt_desc")
        name, ok = QInputDialog.getText(self, title, desc)
        name = name.strip()
        if not ok or not name:
            return
            
        # Capture current settings
        opt = self._get_options()
        preset_data = {
            "doc_theme": self.doc_theme_combo.currentIndex(),
            "code_theme": self.code_theme_combo.currentIndex(),
            "paper_size": self.paper_combo.currentIndex(),
            "watermark": opt.watermark,
            "footer_text": opt.footer_text,
            "custom_css": opt.custom_css,
            "export_format": self.format_combo.currentIndex(),
            "margins": opt.margins,
            "docx_template": opt.docx_template,
            "page_numbers": opt.page_numbers,
            "page_num_format": self.combo_page_format.currentIndex(),
            "presentation_mode": opt.is_presentation,
        }
        
        self.presets[name] = preset_data
        self.settings.setValue("presets", json.dumps(self.presets))
        
        self.load_presets()
        # Select newly created preset
        idx = self.preset_combo.findText(name)
        if idx >= 0:
            self.preset_combo.setCurrentIndex(idx)
            
        QMessageBox.information(self, self.tr_msg("msg_done_title"), self.tr_msg("msg_preset_saved", name))

    def delete_preset(self):
        idx = self.preset_combo.currentIndex()
        if idx <= 0: # Cannot delete default
            return
        name = self.preset_combo.currentText()
        if name in self.presets:
            del self.presets[name]
            self.settings.setValue("presets", json.dumps(self.presets))
            self.load_presets()
            QMessageBox.information(self, self.tr_msg("msg_done_title"), self.tr_msg("msg_preset_deleted", name))

    def on_preset_changed(self, idx: int):
        if idx <= 0:
            # Load factory default settings or just keep current
            return
        name = self.preset_combo.currentText()
        preset = self.presets.get(name)
        if not preset:
            return
            
        # Apply preset to UI elements
        self.doc_theme_combo.setCurrentIndex(preset.get("doc_theme", 0))
        self.code_theme_combo.setCurrentIndex(preset.get("code_theme", 0))
        self.paper_combo.setCurrentIndex(preset.get("paper_size", 0))
        self.watermark_input.setText(preset.get("watermark", ""))
        self.footer_input.setText(preset.get("footer_text", ""))
        self.custom_css_input.setText(preset.get("custom_css", ""))
        self.format_combo.setCurrentIndex(preset.get("export_format", 0))
        self.margins_input.setText(preset.get("margins", ""))
        self.docx_template_input.setText(preset.get("docx_template", ""))
        self.chk_page_numbers.setChecked(preset.get("page_numbers", False))
        self.combo_page_format.setCurrentIndex(preset.get("page_num_format", 0))
        self.combo_page_format.setEnabled(self.chk_page_numbers.isChecked())
        self.chk_presentation_mode.setChecked(preset.get("presentation_mode", False))

    # ─── Translations ───

    def tr_msg(self, key: str, *args) -> str:
        text = TRANSLATIONS.get(self.current_lang, {}).get(key, key)
        if args:
            try:
                return text.format(*args)
            except Exception:
                pass
        return text

    def change_lang(self, lang_code: str):
        self.current_lang = lang_code
        self.settings.setValue("language", lang_code)
        self.retranslate_ui()
        self.load_presets() # Reload default text in presets combo
        
        # If welcome guide is still active and unmodified, swap it to the new language
        if self.is_welcome_doc_active:
            self.load_welcome_document()
        
    def retranslate_ui(self):
        t = lambda k: TRANSLATIONS[self.current_lang].get(k, k)
        
        self.setWindowTitle(f"{t('title')} v{__version__}")
        
        # Menu Bar
        try:
            menubar = self.menuBar()
            menubar.actions()[0].setText(t('menu_file'))
            self.recent_menu.setTitle(t('menu_recent'))
            self.lang_menu.setTitle(t('menu_language'))
            if hasattr(self, 'tools_menu'):
                self.tools_menu.setTitle(t('menu_tools'))
                self.action_update_toc.setText(t('menu_update_toc'))
                self.action_audit.setText(t('menu_audit'))
                self.action_format.setText(t('menu_format'))
        except Exception:
            pass
            
        self.btn_theme.setText(t('btn_theme_light') if self.is_dark else t('btn_theme_dark'))
        
        # Labels and Groupboxes
        self.label_doc_style.setText(t('doc_style'))
        self.label_code_style.setText(t('code_style'))
        self.label_paper_size.setText(t('paper_size'))
        self.label_watermark.setText(t('watermark'))
        self.label_footer.setText(t('footer'))
        self.label_custom_css.setText(t('custom_css'))
        self.label_pdf_password.setText(t('pdf_password'))
        self.label_margins.setText(t('pdf_margins'))
        self.label_docx_template.setText(t('docx_template'))
        self.label_preset.setText(t('preset_label'))
        
        # Translate page numbering and presentation mode widgets
        self.chk_page_numbers.setText(t('chk_page_numbers'))
        self.label_page_format.setText(t('lbl_page_format'))
        self.chk_presentation_mode.setText(t('chk_presentation_mode'))
        self.chk_presentation_mode.setToolTip(t('tip_chk_presentation'))
        
        self.combo_page_format.blockSignals(True)
        current_data = self.combo_page_format.currentData()
        self.combo_page_format.clear()
        self.combo_page_format.addItem(t('page_format_simple'), "simple")
        self.combo_page_format.addItem(t('page_format_slash'), "slash")
        self.combo_page_format.addItem(t('page_format_text'), "text")
        idx = self.combo_page_format.findData(current_data)
        if idx >= 0:
            self.combo_page_format.setCurrentIndex(idx)
        self.combo_page_format.blockSignals(False)
        
        # Placeholders
        self.watermark_input.setPlaceholderText(t('placeholder_watermark'))
        self.footer_input.setPlaceholderText(t('placeholder_footer'))
        self.custom_css_input.setPlaceholderText(t('placeholder_css'))
        self.pdf_password_input.setPlaceholderText(t('placeholder_password'))
        self.margins_input.setPlaceholderText(t('placeholder_margins'))
        self.docx_template_input.setPlaceholderText(t('placeholder_docx'))
        self.live_editor.setPlaceholderText(t('placeholder_editor'))
        
        # Buttons
        self.btn_select_css.setText(t('btn_browse'))
        self.btn_select_docx.setText(t('btn_browse'))
        self.btn_save_preset.setText(t('btn_save_preset'))
        self.btn_delete_preset.setText(t('btn_delete_preset'))
        self.btn_select.setText(t('btn_select_files'))
        self.btn_select_folder.setText(t('btn_select_folder'))
        self.btn_out_folder.setText(t('btn_out_folder'))
        
        if self.watch_active:
            self.btn_watch.setText(t('btn_watch_on'))
        else:
            self.btn_watch.setText(t('btn_watch_off'))
            
        self.btn_cancel.setText(t('btn_cancel'))
        
        # Dynamic Text update for convert button
        fmt = self.format_combo.currentData()
        self.btn_convert.setText(t('btn_convert').format(fmt))
        
        # Tab headers
        self.tabs.setTabText(0, t('tab_log'))
        self.tabs.setTabText(1, t('tab_editor'))
        
        # Search & Replace and Export History retranslate
        self.history_group.setTitle(t('history_title'))
        self.label_search_find.setText(t('search_find_lbl'))
        self.label_search_replace.setText(t('search_replace_lbl'))
        self.btn_search_next.setText(t('btn_find_next'))
        self.btn_replace_all.setText(t('btn_replace_all'))
        self.search_regex_checkbox.setText(t('search_regex_lbl'))
        
        # Tooltips
        self.btn_format_bold.setToolTip(t('tip_format_bold'))
        self.btn_format_italic.setToolTip(t('tip_format_italic'))
        self.btn_format_h1.setToolTip(t('tip_format_h1'))
        self.btn_format_h2.setToolTip(t('tip_format_h2'))
        self.btn_format_code.setToolTip(t('tip_format_code'))
        self.btn_format_quote.setToolTip(t('tip_format_quote'))
        self.btn_format_list.setToolTip(t('tip_format_list'))
        self.btn_format_pagebreak.setToolTip(t('tip_format_pagebreak'))
        
        self.btn_design_style.setText(t('btn_design_style'))
        self.btn_design_style.setToolTip(t('tip_btn_design_style'))
        self.btn_print.setText(t('btn_print'))
        self.btn_copy_html.setText(t('btn_copy_html'))
        self.btn_merge_files.setText(t('btn_merge_files'))
        self.btn_snippets.setText(t('btn_snippets'))
        self.btn_snippets.setToolTip(t('tip_btn_snippets'))
        self.btn_zen.setText(t('btn_zen'))
        self.btn_zen.setToolTip(t('tip_btn_zen'))
        self.btn_format.setText(t('btn_format'))
        self.btn_format.setToolTip(t('tip_btn_format'))
        self.btn_history.setText(t('btn_history'))
        self.btn_history.setToolTip(t('tip_btn_history'))
        self.btn_audit.setText(t('btn_audit'))
        self.btn_audit.setToolTip(t('tip_btn_audit'))
        self.btn_toc.setText(t('btn_toc'))
        self.btn_toc.setToolTip(t('tip_btn_toc'))
        
        self.explorer_group.setTitle(t('explorer_title'))
        self.explorer_search.setPlaceholderText(t('explorer_search_placeholder'))
        
        self.update_text_statistics()
        self.update_export_history_ui()
        
        if not self.selected_files:
            self.file_label.setText(t('file_not_selected'))

    def load_welcome_document(self):
        self.is_welcome_doc_active = True
        text = WELCOME_RU if self.current_lang == "ru" else WELCOME_EN
        self.live_editor.blockSignals(True)
        self.live_editor.setPlainText(text)
        self.live_editor.blockSignals(False)
        self._render_live_preview()
        self.update_text_statistics()

    def on_editor_changed(self):
        self.is_welcome_doc_active = False
        self.preview_timer.start()
        self.update_text_statistics()

    # ─── Statistics & Search & History logics ───

    def update_text_statistics(self):
        text = self.live_editor.toPlainText()
        char_count = len(text)
        words = [w for w in text.split() if w.strip()]
        word_count = len(words)
        
        reading_time = max(1, round(word_count / 180))
        if word_count == 0:
            reading_time = 0
            
        t = lambda k: TRANSLATIONS[self.current_lang].get(k, k)
        stats_text = (
            f"{t('stats_words').format(word_count)} | "
            f"{t('stats_chars').format(char_count)} | "
            f"{t('stats_reading').format(reading_time)}"
        )
        
        if self.writing_goal > 0:
            pct = min(100, int((word_count / self.writing_goal) * 100))
            self.goal_progress.setValue(pct)
            self.goal_progress.show()
            stats_text += f" | 🎯 {pct}% ({word_count}/{self.writing_goal} {t('stats_words').format('').strip()})"
            
            if pct >= 100 and not self.goal_celebrated:
                self.goal_celebrated = True
                QMessageBox.information(
                    self,
                    t('goal_celebrate_title'),
                    t('goal_celebrate_desc').format(self.writing_goal)
                )
        else:
            self.goal_progress.hide()
            
        self.stats_label.setText(stats_text)

    def toggle_search_panel(self):
        if self.search_panel.isVisible():
            self.search_panel.hide()
            self.live_editor.setFocus()
        else:
            self.search_panel.show()
            self.search_find_input.setFocus()
            self.search_find_input.selectAll()

    def search_next(self):
        query = self.search_find_input.text()
        if not query:
            return
        
        regex_mode = self.search_regex_checkbox.isChecked()
        if regex_mode:
            expr = QRegularExpression(query)
            found = self.live_editor.find(expr)
            if not found:
                cursor = self.live_editor.textCursor()
                cursor.movePosition(cursor.MoveOperation.Start)
                self.live_editor.setTextCursor(cursor)
                self.live_editor.find(expr)
        else:
            found = self.live_editor.find(query)
            if not found:
                cursor = self.live_editor.textCursor()
                cursor.movePosition(cursor.MoveOperation.Start)
                self.live_editor.setTextCursor(cursor)
                self.live_editor.find(query)

    def replace_all_occurrences(self):
        query = self.search_find_input.text()
        replace_text = self.search_replace_input.text()
        if not query:
            return
            
        cursor = self.live_editor.textCursor()
        scroll_pos = self.live_editor.verticalScrollBar().value()
        text = self.live_editor.toPlainText()
        
        regex_mode = self.search_regex_checkbox.isChecked()
        if regex_mode:
            import re
            try:
                new_text = re.sub(query, replace_text, text)
            except Exception as e:
                QMessageBox.critical(self, "RegEx Error", f"Invalid regular expression:\n{e}")
                return
        else:
            new_text = text.replace(query, replace_text)
        
        self.live_editor.blockSignals(True)
        self.live_editor.setPlainText(new_text)
        self.live_editor.blockSignals(False)
        
        self.live_editor.setTextCursor(cursor)
        self.live_editor.verticalScrollBar().setValue(scroll_pos)
        self._render_live_preview()
        self.update_text_statistics()

    def on_finished_one(self, success: bool, filepath: str):
        if success:
            self.add_to_export_history(filepath)

    def add_to_export_history(self, filepath: str):
        if filepath in self.export_history:
            self.export_history.remove(filepath)
        self.export_history.insert(0, filepath)
        self.export_history = self.export_history[:5]
        self.settings.setValue("export_history", self.export_history)
        self.update_export_history_ui()

    def update_export_history_ui(self):
        t = lambda k: TRANSLATIONS[self.current_lang].get(k, k)
        
        # Clear layout
        while self.history_layout.count() > 0:
            item = self.history_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
                
        if not self.export_history:
            self.history_placeholder = QLabel(t('history_placeholder') if 'history_placeholder' in TRANSLATIONS[self.current_lang] else "Журнал экспорта пуст")
            self.history_placeholder.setStyleSheet("color: #94a3b8; font-style: italic; font-size: 11px; padding: 5px;")
            self.history_layout.addWidget(self.history_placeholder)
            return
            
        for filepath in self.export_history:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(5, 2, 5, 2)
            row_layout.setSpacing(10)
            
            lbl = QLabel(os.path.basename(filepath))
            lbl.setStyleSheet("font-size: 11px; color: #94a3b8; font-weight: bold;")
            lbl.setToolTip(filepath)
            
            btn_open = QPushButton(t('btn_history_open'))
            btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_open.setStyleSheet("""
                QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2563eb,stop:1 #60a5fa); color: white; padding: 3px 8px; border-radius: 6px; font-size: 10px; border: none; font-weight: bold; }
                QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1d4ed8,stop:1 #2563eb); }
            """)
            btn_open.clicked.connect(lambda checked, p=filepath: self.open_exported_file(p))
            
            btn_folder = QPushButton(t('btn_history_folder'))
            btn_folder.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_folder.setStyleSheet("""
                QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #475569,stop:1 #64748b); color: white; padding: 3px 8px; border-radius: 6px; font-size: 10px; border: none; font-weight: bold; }
                QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #334155,stop:1 #475569); }
            """)
            btn_folder.clicked.connect(lambda checked, p=filepath: self.open_exported_folder(p))
            
            row_layout.addWidget(lbl, stretch=1)
            row_layout.addWidget(btn_open)
            row_layout.addWidget(btn_folder)
            
            self.history_layout.addWidget(row)

    def open_exported_file(self, filepath: str):
        if not os.path.exists(filepath):
            QMessageBox.warning(self, self.tr_msg("msg_file_not_found"), self.tr_msg("msg_file_moved", filepath))
            return
        try:
            os.startfile(filepath)
        except Exception as e:
            logger.error("Failed to open file %s: %s", filepath, e)
            
    def open_exported_folder(self, filepath: str):
        if not os.path.exists(filepath):
            QMessageBox.warning(self, self.tr_msg("msg_file_not_found"), self.tr_msg("msg_file_moved", filepath))
            return
        try:
            import subprocess
            subprocess.run(["explorer", "/select,", os.path.normpath(filepath)])
        except Exception as e:
            logger.error("Failed to open folder for %s: %s", filepath, e)

    def get_windows_theme(self) -> str:
        """Detect whether Windows is in dark or light mode. Returns 'dark' or 'light'."""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return "light" if value == 1 else "dark"
        except Exception:
            return "light"

    def autosave_draft(self):
        document_tools.autosave_draft(self)

    def save_current_workspace_file(self):
        file_manager.save_current_workspace_file(self)

    def save_revision(self):
        document_tools.save_revision(self)

    def show_revision_history(self):
        document_tools.show_revision_history(self)

    def goto_editor_line(self, line_num: int):
        cursor = self.live_editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        for _ in range(line_num - 1):
            cursor.movePosition(cursor.MoveOperation.Down)
        
        # Select full line
        cursor.movePosition(cursor.MoveOperation.StartOfLine)
        cursor.movePosition(cursor.MoveOperation.EndOfLine, cursor.MoveMode.KeepAnchor)
        
        self.live_editor.setTextCursor(cursor)
        self.live_editor.setFocus()

    def show_document_audit(self):
        document_tools.show_document_audit(self)

    def auto_fix_document_issues(self):
        document_tools.auto_fix_document_issues(self)

    def show_toc_generator(self):
        document_tools.show_toc_generator(self)

    def update_markdown_toc_in_editor(self):
        document_tools.update_markdown_toc_in_editor(self)

    def show_table_generator_dialog(self):
        document_tools.show_table_generator_dialog(self)

    def show_snippets_dialog(self):
        from src.gui.dialogs import SnippetsManagerDialog
        dlg = SnippetsManagerDialog(self, self.current_lang)
        if dlg.exec() and dlg.selected_code:
            cursor = self.live_editor.textCursor()
            cursor.insertText(dlg.selected_code)
            self.live_editor.setTextCursor(cursor)

    def show_doc_templates_dialog(self):
        from src.gui.templates_data import get_template_list, get_template_content
        templates = get_template_list()
        names = [name for _, name in templates]
        chosen, ok = QInputDialog.getItem(
            self,
            self.tr_msg("doc_templates_title"),
            self.tr_msg("doc_templates_label"),
            names, 0, False
        )
        if ok and chosen:
            for key, name in templates:
                if name == chosen:
                    content = get_template_content(key)
                    if content:
                        self.live_editor.setPlainText(content)
                        self.update_preview_from_editor()
                    break

    def show_diff_dialog(self):
        from src.gui.dialogs import DiffDialog
        dlg = DiffDialog(self, self.current_lang)
        dlg.exec()

    def toggle_split_view(self):
        modes = ['both', 'editor', 'preview']
        current = getattr(self, '_split_view_mode', 'both')
        idx = (modes.index(current) + 1) % len(modes)
        self._split_view_mode = modes[idx]

        if self._split_view_mode == 'both':
            self.editor_splitter.setSizes([200, 400, 400])
            self.preview_output.show()
            self.live_editor.show()
        elif self._split_view_mode == 'editor':
            self.editor_splitter.setSizes([0, 1, 0])
            self.preview_output.hide()
            self.live_editor.show()
        elif self._split_view_mode == 'preview':
            self.editor_splitter.setSizes([0, 0, 1])
            self.live_editor.hide()
            self.preview_output.show()

        labels = {'both': '📏 Оба', 'editor': '📝 Редактор', 'preview': '👁 Превью'}
        if hasattr(self, 'btn_split_view'):
            self.btn_split_view.setText(labels[self._split_view_mode])

    def toggle_wysiwyg(self):
        """Toggle simplified WYSIWYG mode - show rendered preview inline."""
        if not hasattr(self, '_wysiwyg_active'):
            self._wysiwyg_active = False

        self._wysiwyg_active = not self._wysiwyg_active

        if self._wysiwyg_active:
            # Hide editor, show preview full width
            self.editor_splitter.setSizes([0, 0, 1])
            self.live_editor.hide()
            self.preview_output.show()
            self._render_live_preview()
            if hasattr(self, 'btn_wysiwyg'):
                self.btn_wysiwyg.setText("📝 MD")
        else:
            # Restore split view
            self.editor_splitter.setSizes([0, 400, 400])
            self.live_editor.show()
            self.preview_output.show()
            if hasattr(self, 'btn_wysiwyg'):
                self.btn_wysiwyg.setText("✨ WYSIWYG")

    def run_linter(self):
        from src.core.linter import lint_markdown
        text = self.live_editor.toPlainText()
        issues = lint_markdown(text, self.current_lang)

        if not issues:
            QMessageBox.information(self, "Lint", "✅ Ошибок не найдено" if self.current_lang == "ru" else "✅ No issues found")
            return

        severity_icons = {'error': '❌', 'warning': '⚠️', 'info': 'ℹ️'}
        lines = [f"<b>{len(issues)} проблем(а):</b><br><br>"]
        for issue in sorted(issues, key=lambda x: x.line):
            icon = severity_icons.get(issue.severity, '')
            lines.append(f"{icon} <b>Стр. {issue.line}</b>: {issue.message} <span style='color:#999'>({issue.rule})</span><br>")

        dlg = QDialog(self)
        dlg.setWindowTitle("Результаты линтинга")
        dlg.setMinimumSize(500, 400)
        layout = QVBoxLayout(dlg)
        browser = QTextBrowser()
        browser.setHtml(''.join(lines))
        layout.addWidget(browser)
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(dlg.close)
        layout.addWidget(btn_close)
        dlg.exec()

    def show_readability_dashboard(self):
        document_tools.show_readability_dashboard(self)

    def show_design_style_dialog(self):
        document_tools.show_design_style_dialog(self)

    def show_merge_dialog(self):
        document_tools.show_merge_dialog(self)

    def show_stats_menu(self):
        document_tools.show_stats_menu(self)

    def set_writing_goal(self):
        document_tools.set_writing_goal(self)

    def show_toc_generator(self):
        dialog = MarkdownTOCDialog(parent=self, lang=self.current_lang)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            max_depth = dialog.depth_combo.currentData()
            list_style = dialog.style_combo.currentData()
            use_anchors = dialog.anchors_chk.isChecked()
            
            text = self.live_editor.toPlainText()
            lines = text.splitlines()
            
            import re
            toc_lines = []
            
            h1_count = 0
            h2_count = 0
            h3_count = 0
            
            toc_lines.append("## Оглавление" if self.current_lang == "ru" else "## Table of Contents")
            toc_lines.append("")
            
            for line in lines:
                m = re.match(r'^(#{1,3})\s+(.*)$', line)
                if m:
                    level = len(m.group(1))
                    title = m.group(2).strip()
                    
                    if level > max_depth or not title:
                        continue
                        
                    # Build a standard anchor format, same as Python-Markdown TOC extension
                    anchor_name = re.sub(r'[^\w\s-]', '', title.lower()).strip().replace(' ', '-')
                    
                    if list_style == "bullet":
                        indent = "  " * (level - 1)
                        if use_anchors:
                            item_text = f"{indent}- [{title}](#{anchor_name})"
                        else:
                            item_text = f"{indent}- {title}"
                    else:
                        if level == 1:
                            h1_count += 1
                            h2_count = 0
                            h3_count = 0
                            num_str = f"{h1_count}."
                            indent = ""
                        elif level == 2:
                            h2_count += 1
                            h3_count = 0
                            num_str = f"{h1_count}.{h2_count}."
                            indent = "  "
                        else:
                            h3_count += 1
                            num_str = f"{h1_count}.{h2_count}.{h3_count}."
                            indent = "    "
                            
                        if use_anchors:
                            item_text = f"{indent}{num_str} [{title}](#{anchor_name})"
                        else:
                            item_text = f"{indent}{num_str} {title}"
                            
                    toc_lines.append(item_text)
                    
            if len(toc_lines) <= 2:
                QMessageBox.warning(
                    self, 
                    "Оглавление" if self.current_lang == "ru" else "TOC Builder",
                    "Заголовки для построения оглавления не найдены!" if self.current_lang == "ru" else "No headings found to generate Table of Contents!"
                )
                return
                
            toc_content = "\n".join(toc_lines) + "\n\n"
            
            cursor = self.live_editor.textCursor()
            cursor.insertText(toc_content)
            self.live_editor.setTextCursor(cursor)
            self.live_editor.setFocus()

    def update_markdown_toc_in_editor(self):
        text = self.live_editor.toPlainText()
        
        lines = text.splitlines()
        headings = []
        import re
        
        in_code_block = False
        
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
                
            m = re.match(r'^(#{1,3})\s+(.*)$', line)
            if m:
                level = len(m.group(1))
                title = m.group(2).strip()
                if title and not title.startswith("<!--") and not title.endswith("-->"):
                    headings.append((level, title))
                    
        toc_lines = []
        toc_lines.append("## " + ("Оглавление" if self.current_lang == "ru" else "Table of Contents"))
        toc_lines.append("")
        
        for level, title in headings:
            anchor_name = re.sub(r'[^\w\s-]', '', title.lower()).strip().replace(' ', '-')
            indent = "  " * (level - 1)
            toc_lines.append(f"{indent}- [{title}](#{anchor_name})")
            
        toc_body = "\n".join(toc_lines)
        
        start_marker = "<!-- TOC START -->"
        end_marker = "<!-- TOC END -->"
        
        if start_marker in text and end_marker in text:
            start_idx = text.find(start_marker)
            end_idx = text.find(end_marker) + len(end_marker)
            
            new_text = (
                text[:start_idx] +
                start_marker + "\n\n" +
                toc_body + "\n\n" +
                text[end_idx:]
            )
        else:
            cursor = self.live_editor.textCursor()
            insert_text = f"\n{start_marker}\n\n{toc_body}\n\n{end_marker}\n"
            
            cursor.insertText(insert_text)
            self.live_editor.setFocus()
            new_text = self.live_editor.toPlainText()
            
        if new_text != text:
            scroll_pos = self.live_editor.verticalScrollBar().value()
            cursor_pos = self.live_editor.textCursor().position()
            
            self.live_editor.blockSignals(True)
            self.live_editor.setPlainText(new_text)
            self.live_editor.blockSignals(False)
            
            self._render_live_preview()
            self.update_text_statistics()
            
            self.live_editor.verticalScrollBar().setValue(scroll_pos)
            
            cursor = self.live_editor.textCursor()
            cursor.setPosition(min(cursor_pos, len(new_text)))
            self.live_editor.setTextCursor(cursor)
            
        t = lambda k: TRANSLATIONS[self.current_lang].get(k, k)
        QMessageBox.information(
            self,
            t('msg_toc_updated_title'),
            t('msg_toc_updated_desc')
        )

    def load_workspace_file(self, item):
        file_manager.load_workspace_file(self, item)

    def update_workspace_explorer(self):
        file_manager.update_workspace_explorer(self)

    def filter_workspace_explorer(self, text):
        file_manager.filter_workspace_explorer(self, text)

    def restore_draft_if_exists(self):
        document_tools.restore_draft_if_exists(self)

    def open_output_folder(self):
        file_manager.open_output_folder(self)

    def show_table_generator_dialog(self):
        document_tools.show_table_generator_dialog(self)

    def zoom_in(self):
        preview_manager.zoom_in(self)

    def zoom_out(self):
        preview_manager.zoom_out(self)

    def zoom_reset(self):
        preview_manager.zoom_reset(self)



    # ─── Quick Formatting Methods ───

    def _wrap_selection(self, prefix: str, suffix: str):
        editor_commands._wrap_selection(self, prefix, suffix)

    def format_bold(self):
        editor_commands.format_bold(self)

    def format_italic(self):
        editor_commands.format_italic(self)

    def format_code(self):
        editor_commands.format_code(self)

    def format_header(self, level: int):
        editor_commands.format_header(self, level)

    def format_quote(self):
        editor_commands.format_quote(self)

    def format_list(self):
        editor_commands.format_list(self)

    def insert_page_break(self):
        editor_commands.insert_page_break(self)

    def print_document(self):
        preview_manager.print_document(self)

    def copy_styled_html(self):
        preview_manager.copy_styled_html(self)

    def show_design_style_dialog(self):
        document_tools.show_design_style_dialog(self)

    def print_document_direct(self):
        """Print directly without preview using system printer."""
        from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
        from PyQt6.QtGui import QTextDocument
        printer = QPrinter()
        dlg = QPrintDialog(printer, self)
        if dlg.exec():
            doc = QTextDocument()
            doc.setHtml(self.preview_output.toHtml())
            doc.print_(printer)

    def export_selection(self):
        """Export only selected text from editor."""
        cursor = self.live_editor.textCursor()
        selected = cursor.selectedText()
        if not selected:
            QMessageBox.information(self, "Экспорт", "Выделите текст для экспорта")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт выделенного", "",
            "Markdown (*.md);;Text (*.txt);;HTML (*.html)"
        )
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(selected)
            self.append_log(f"✅ Экспорт выделенного: {path}")

    def export_as_markdown(self):
        """Save current editor content as formatted Markdown file."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как Markdown", "",
            "Markdown (*.md)"
        )
        if path:
            text = self.live_editor.toPlainText()
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
            self.append_log(f"✅ Сохранено: {path}")

    def show_conversion_history(self):
        """Show conversion history with ability to reopen files."""
        history = self.export_history if hasattr(self, 'export_history') else []
        if not history:
            QMessageBox.information(self, "История", "История конвертаций пуста")
            return

        items = []
        for path in history[:20]:
            if os.path.exists(path):
                mtime = os.path.getmtime(path)
                from datetime import datetime
                dt = datetime.fromtimestamp(mtime).strftime("%d.%m.%Y %H:%M")
                items.append(f"{os.path.basename(path)}  ({dt})")

        chosen, ok = QInputDialog.getItem(
            self, "История конвертаций", "Файл:",
            items, 0, False
        )
        if ok and chosen:
            idx = items.index(chosen)
            path = history[idx]
            if os.path.exists(path):
                import subprocess
                os.startfile(path)

    def show_cloud_templates(self):
        from src.gui.dialogs import CloudTemplatesDialog
        dlg = CloudTemplatesDialog(self, self.current_lang)
        if dlg.exec() and dlg.selected_content:
            self.live_editor.setPlainText(dlg.selected_content)
            self.update_preview_from_editor()

    # ─── Focus Mode ───

    def toggle_focus_mode(self):
        """Toggle focus mode - dims everything except current paragraph."""
        if not hasattr(self, '_focus_mode_active'):
            self._focus_mode_active = False

        self._focus_mode_active = not self._focus_mode_active

        if self._focus_mode_active:
            self.live_editor.setStyleSheet("""
                QTextEdit {
                    background-color: #1a1a2e;
                    color: #e0e0e0;
                    font-size: 16pt;
                    line-height: 1.8;
                    padding: 40px;
                    selection-background-color: #6366f1;
                }
            """)
            self.live_editor.setFocus()
        else:
            self.live_editor.setStyleSheet("")
            if self.is_dark:
                self.live_editor.setStyleSheet("QTextEdit { background-color: rgba(30, 41, 59, 0.85); color: #e2e8f0; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 10px; font-family: monospace; font-size: 14px; selection-background-color: #4f46e5; }")
            else:
                self.live_editor.setStyleSheet("QTextEdit { background-color: rgba(255, 255, 255, 0.9); color: #334155; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; font-family: monospace; font-size: 14px; selection-background-color: #818cf8; }")

    def toggle_sentence_focus(self):
        """Highlight only the current sentence in the editor."""
        cursor = self.live_editor.textCursor()
        text = self.live_editor.toPlainText()
        pos = cursor.position()

        # Find current sentence boundaries
        import re
        sentences = list(re.finditer(r'[^.!?]*[.!?]+', text, re.DOTALL))

        for match in sentences:
            if match.start() <= pos <= match.end():
                # Select the current sentence
                cursor.setPosition(match.start())
                cursor.setPosition(match.end(), cursor.MoveMode.KeepAnchor)
                self.live_editor.setTextCursor(cursor)
                break

    # ─── Emoji Shortcodes ───

    EMOJI_MAP = {
        ':rocket:': '🚀', ':fire:': '🔥', ':star:': '⭐', ':check:': '✅',
        ':x:': '❌', ':warning:': '⚠️', ':bulb:': '💡', ':heart:': '❤️',
        ':thumbsup:': '👍', ':thumbsdown:': '👎', ':clap:': '👏',
        ':eyes:': '👀', ':tada:': '🎉', ':sparkles:': '✨', ':zap:': '⚡',
        ':book:': '📖', ':pencil:': '📝', ':wrench:': '🔧', ':gear:': '⚙️',
        ':bug:': '🐛', ':lock:': '🔒', ':unlock:': '🔓', ':key:': '🔑',
        ':link:': '🔗', ':email:': '📧', ':calendar:': '📅', ':clock:': '🕐',
        ':check_mark:': '✅', ':cross_mark:': '❌', ':heavy_check:': '✔️',
        ':arrow_right:': '➡️', ':arrow_left:': '⬅️', ':arrow_up:': '⬆️',
        ':arrow_down:': '⬇️', ':white_check:': '✅', ':red_circle:': '🔴',
        ':green_circle:': '🟢', ':blue_circle:': '🔵', ':large_circle:': '⭕',
    }

    def convert_emoji_shortcodes(self):
        """Replace :shortcode: with actual emoji in editor."""
        text = self.live_editor.toPlainText()
        for code, emoji in self.EMOJI_MAP.items():
            text = text.replace(code, emoji)
        self.live_editor.setPlainText(text)

    # ─── Document Versioning ───

    def save_version(self, label=""):
        """Save a named version of the current document."""
        if not hasattr(self, '_versions'):
            self._versions = []

        text = self.live_editor.toPlainText()
        from datetime import datetime
        version = {
            'label': label or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'content': text,
            'timestamp': datetime.now().isoformat(),
            'word_count': len(text.split()),
        }
        self._versions.append(version)

        # Keep only last 50 versions
        if len(self._versions) > 50:
            self._versions = self._versions[-50:]

        self.append_log(f"📌 Версия сохранена: {version['label']}")

    def restore_version(self):
        """Restore a previously saved version."""
        if not hasattr(self, '_versions') or not self._versions:
            QMessageBox.information(self, "Версии", "Нет сохранённых версий")
            return

        items = [f"{v['label']} ({v['word_count']} слов)" for v in self._versions]
        chosen, ok = QInputDialog.getItem(
            self, "Восстановить версию", "Версия:",
            items, len(items) - 1, False
        )
        if ok and chosen:
            idx = items.index(chosen)
            self.live_editor.setPlainText(self._versions[idx]['content'])
            self.update_preview_from_editor()

    def show_version_diff(self):
        """Show diff between current and a saved version."""
        if not hasattr(self, '_versions') or not self._versions:
            QMessageBox.information(self, "Версии", "Нет сохранённых версий")
            return

        items = [f"{v['label']} ({v['word_count']} слов)" for v in self._versions]
        chosen, ok = QInputDialog.getItem(
            self, "Сравнить с версией", "Версия:",
            items, len(items) - 1, False
        )
        if ok and chosen:
            idx = items.index(chosen)
            import difflib
            old = self._versions[idx]['content'].splitlines(keepends=True)
            new = self.live_editor.toPlainText().splitlines(keepends=True)
            diff = list(difflib.unified_diff(old, new, fromfile='Версия', tofile='Текущая', lineterm=''))

            html = ['<pre style="font-family: monospace; font-size: 12px;">']
            for line in diff:
                escaped = line.replace('&', '&amp;').replace('<', '&lt;').rstrip()
                if line.startswith('+'):
                    html.append(f'<span style="background: #d5f5e3; color: #27ae60;">{escaped}</span>')
                elif line.startswith('-'):
                    html.append(f'<span style="background: #fadbd8; color: #e74c3c;">{escaped}</span>')
                elif line.startswith('@@'):
                    html.append(f'<span style="color: #9b59b6;">{escaped}</span>')
                else:
                    html.append(escaped)
            html.append('</pre>')

            dlg = QDialog(self)
            dlg.setWindowTitle("Diff версий")
            dlg.setMinimumSize(600, 400)
            layout = QVBoxLayout(dlg)
            browser = QTextBrowser()
            browser.setHtml('\n'.join(html))
            layout.addWidget(browser)
            btn = QPushButton("Закрыть")
            btn.clicked.connect(dlg.close)
            layout.addWidget(btn)
            dlg.exec()

    # ─── Spell Check ───

    def run_spell_check(self):
        """Basic spell check using dictionary file or simple word check."""
        text = self.live_editor.toPlainText()
        words = set()
        import re
        for word in re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{3,}\b', text):
            words.add(word.lower())

        # Common misspellings dictionary (English)
        common_misspells = {
            'teh': 'the', 'adn': 'and', 'taht': 'that', 'wiht': 'with',
            'thier': 'their', 'recieve': 'receive', 'seperate': 'separate',
            'occured': 'occurred', 'definately': 'definitely', 'accomodate': 'accommodate',
            'occurence': 'occurrence', 'untill': 'until', 'wierd': 'weird',
            'begining': 'beginning', 'freind': 'friend', 'goverment': 'government',
        }

        issues = []
        for word in words:
            if word in common_misspells:
                issues.append((word, common_misspells[word]))

        if issues:
            msg = "Возможные ошибки:\n\n" + "\n".join(f"• {w} → {c}" for w, c in issues[:20])
            QMessageBox.information(self, "Spell Check", msg)
        else:
            QMessageBox.information(self, "Spell Check", "✅ Ошибок не найдено")

    # ─── Wikilinks ───

    def process_wikilinks(self):
        from src.core.wikilinks import WikiLinkProcessor
        text = self.live_editor.toPlainText()
        processor = WikiLinkProcessor(os.path.dirname(self.selected_files[0]) if self.selected_files else os.getcwd())
        processed = processor.resolve_links(text)
        self.live_editor.setPlainText(processed)

    def show_transclusion(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", "Markdown (*.md)")
        if path:
            cursor = self.live_editor.textCursor()
            cursor.insertText(f"{{{{include:{os.path.basename(path)}}}}}")

    # ─── Graph View ───

    def show_graph_view(self):
        from src.core.wikilinks import GraphBuilder
        base_dir = os.path.dirname(self.selected_files[0]) if self.selected_files else os.getcwd()
        builder = GraphBuilder(base_dir)
        html = builder.build_graph_html()
        dlg = QDialog(self)
        dlg.setWindowTitle("Graph View")
        dlg.setMinimumSize(800, 600)
        layout = QVBoxLayout(dlg)
        browser = QTextBrowser()
        browser.setHtml(html)
        layout.addWidget(browser)
        btn = QPushButton("Закрыть")
        btn.clicked.connect(dlg.close)
        layout.addWidget(btn)
        dlg.exec()

    # ─── Voice-to-Text ───

    def start_voice_input(self):
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                self.append_log("🎤 Слушаю...")
                QApplication.processEvents()
                audio = recognizer.listen(source, timeout=10)
                text = recognizer.recognize_google(audio, language='ru-RU')
                cursor = self.live_editor.textCursor()
                cursor.insertText(text)
        except ImportError:
            QMessageBox.information(self, "Voice", "Установите: pip install SpeechRecognition pyaudio")
        except Exception as e:
            self.append_log(f"🎤 Ошибка: {e}")

    # ─── AI Text ───

    def ai_improve_text(self):
        cursor = self.live_editor.textCursor()
        selected = cursor.selectedText()
        if not selected:
            QMessageBox.information(self, "AI", "Выделите текст")
            return
        from src.core.ai_assistant import get_ai_assistant
        assistant = get_ai_assistant()
        suggestions = assistant.analyze(selected, self.current_lang)
        if suggestions:
            lines = []
            for s in suggestions[:5]:
                lines.append(f"• [{s.category}] {s.explanation}")
            QMessageBox.information(self, "AI Suggestions", "\n".join(lines))
        else:
            improved = selected.strip()
            improved = ' '.join(improved.split())
            cursor.insertText(improved)
            self.toast("Текст обработан", "success")

    def ai_generate_outline(self):
        text = self.live_editor.toPlainText()
        from src.core.ai_assistant import get_ai_assistant
        assistant = get_ai_assistant()
        outline = assistant.generate_outline(text, self.current_lang)
        cursor = self.live_editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        cursor.insertText(outline + "\n\n")
        self.toast("Оглавление сгенерировано", "success")

    def show_ai_assistant(self):
        from src.core.ai_assistant import get_ai_assistant
        assistant = get_ai_assistant()
        text = self.live_editor.toPlainText()
        if not text.strip():
            self.toast("Нет текста для анализа", "warning")
            return
        suggestions = assistant.analyze(text, self.current_lang)
        if not suggestions:
            self.toast("Проблем не найдено! Текст хороший.", "success")
            return
        lines = [f"🔍 Найдено {len(suggestions)} предложений:\n"]
        for s in suggestions[:10]:
            emoji = {"grammar": "📝", "style": "✨", "readability": "📖", "structure": "🏗️"}.get(s.category, "💡")
            lines.append(f"{emoji} Строка {s.line}: {s.explanation}")
        QMessageBox.information(self, "AI Writing Assistant", "\n".join(lines))

    # ─── Task Board ───

    def export_task_board(self):
        text = self.live_editor.toPlainText()
        import re
        todo, done = [], []
        for line in text.split('\n'):
            stripped = line.strip()
            if re.match(r'^- \[[ x]\]\s', stripped):
                content = re.sub(r'^- \[[ x]\]\s*', '', stripped)
                (done if '[x]' in stripped else todo).append(content)
        html = f"""<html><head><style>
body{{font-family:sans-serif;padding:20px;}}
.board{{display:flex;gap:20px;}}
.column{{background:white;border-radius:8px;padding:16px;min-width:250px;box-shadow:0 2px 8px rgba(0,0,0,0.1);}}
.todo{{border-top:3px solid #3498db;}}.done{{border-top:3px solid #27ae60;}}
.task{{background:#f8f9fa;padding:8px;margin:6px 0;border-radius:4px;font-size:14px;}}
</style></head><body><h2>📋 Task Board</h2><div class="board">
<div class="column todo"><h3>To Do ({len(todo)})</h3>{''.join(f'<div class="task">{t}</div>' for t in todo)}</div>
<div class="column done"><h3>Done ({len(done)})</h3>{''.join(f'<div class="task" style="text-decoration:line-through;color:#999">{t}</div>' for t in done)}</div>
</div></body></html>"""
        dlg = QDialog(self); dlg.setWindowTitle("Task Board"); dlg.setMinimumSize(700, 400)
        layout = QVBoxLayout(dlg)
        browser = QTextBrowser(); browser.setHtml(html); layout.addWidget(browser)
        btn = QPushButton("Закрыть"); btn.clicked.connect(dlg.close); layout.addWidget(btn)
        dlg.exec()

    # ─── Tags Cloud ───

    def show_tag_cloud(self):
        from src.core.wikilinks import WikiLinkProcessor
        from collections import Counter
        import random
        text = self.live_editor.toPlainText()
        tags = WikiLinkProcessor().extract_tags(text)
        if not tags:
            QMessageBox.information(self, "Теги", "Теги не найдены (#тег)")
            return
        counts = Counter(tags)
        colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
        words = [f'<span style="font-size:{14+c*6}px;color:{random.choice(colors)};margin:4px 8px;display:inline-block;">#{t}</span>' for t, c in counts.most_common(30)]
        html = f"<html><body style='text-align:center;padding:20px;'><h2>Tags</h2><p style='line-height:2;'>{''.join(words)}</p></body></html>"
        dlg = QDialog(self); dlg.setWindowTitle("Облако тегов"); dlg.setMinimumSize(500, 300)
        layout = QVBoxLayout(dlg)
        browser = QTextBrowser(); browser.setHtml(html); layout.addWidget(browser)
        btn = QPushButton("Закрыть"); btn.clicked.connect(dlg.close); layout.addWidget(btn)
        dlg.exec()

    # ─── Typewriter Mode ───

    def toggle_typewriter_mode(self):
        if not hasattr(self, '_typewriter_active'):
            self._typewriter_active = False
        self._typewriter_active = not self._typewriter_active
        if self._typewriter_active:
            self.live_editor.setStyleSheet(self.live_editor.styleSheet() + " QTextEdit { padding-top: 200px; padding-bottom: 200px; }")
        else:
            bg = "#1e1e2e" if self.is_dark else "#ffffff"
            fg = "#cdd6f4" if self.is_dark else "#2c3e50"
            self.live_editor.setStyleSheet(f"QTextEdit {{ background-color: {bg}; color: {fg}; }}")

    # ─── Reading Analytics ───

    def show_reading_analytics(self):
        text = self.live_editor.toPlainText()
        import re
        words = text.split()
        wc = len(words)
        cc = len(text)
        sc = len(re.findall(r'[.!?]+', text))
        pc = len([p for p in text.split('\n\n') if p.strip()])
        rt = max(1, round(wc / 180))
        syllables = sum(max(1, len(re.findall(r'[аеёиоуыэюя]', w.lower()))) for w in words)
        asl = wc / max(1, sc); asw = syllables / max(1, wc)
        flesch = max(0, min(100, 206.835 - 1.3 * asl - 60.1 * asw))
        html = f"""<html><body style="font-family:sans-serif;padding:20px;text-align:center;">
<h2>📊 Analytics</h2>
<div style="display:flex;justify-content:center;flex-wrap:wrap;">
<div style="background:#f8f9fa;border-radius:8px;padding:16px 24px;margin:8px;text-align:center;"><div style="font-size:28px;font-weight:bold;">{wc}</div><div style="color:#999;font-size:12px;">Слов</div></div>
<div style="background:#f8f9fa;border-radius:8px;padding:16px 24px;margin:8px;text-align:center;"><div style="font-size:28px;font-weight:bold;">{cc}</div><div style="color:#999;font-size:12px;">Символов</div></div>
<div style="background:#f8f9fa;border-radius:8px;padding:16px 24px;margin:8px;text-align:center;"><div style="font-size:28px;font-weight:bold;">{rt} мин</div><div style="color:#999;font-size:12px;">Чтение</div></div>
<div style="background:#f8f9fa;border-radius:8px;padding:16px 24px;margin:8px;text-align:center;"><div style="font-size:28px;font-weight:bold;">{flesch:.0f}</div><div style="color:#999;font-size:12px;">Читаемость</div></div>
</div></body></html>"""
        dlg = QDialog(self); dlg.setWindowTitle("Analytics"); dlg.setMinimumSize(500, 300)
        layout = QVBoxLayout(dlg)
        browser = QTextBrowser(); browser.setHtml(html); layout.addWidget(browser)
        btn = QPushButton("Закрыть"); btn.clicked.connect(dlg.close); layout.addWidget(btn)
        dlg.exec()

    # ─── API Docs Generator ───

    def generate_api_docs(self):
        path, _ = QFileDialog.getOpenFileName(self, "Python файл", "", "Python (*.py)")
        if not path: return
        try:
            import ast
            with open(path, 'r', encoding='utf-8') as f: source = f.read()
            tree = ast.parse(source)
            docs = [f"# API: {os.path.basename(path)}\n"]
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef):
                    docs.append(f"\n## class {node.name}\n")
                    if ast.get_docstring(node): docs.append(f"{ast.get_docstring(node)}\n")
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            args = [a.arg for a in item.args.args if a.arg != 'self']
                            docs.append(f"### {item.name}({', '.join(args)})\n")
                            if ast.get_docstring(item): docs.append(f"{ast.get_docstring(item)}\n")
                elif isinstance(node, ast.FunctionDef):
                    args = [a.arg for a in node.args.args]
                    docs.append(f"\n## def {node.name}({', '.join(args)})\n")
                    if ast.get_docstring(node): docs.append(f"{ast.get_docstring(node)}\n")
            self.live_editor.setPlainText('\n'.join(docs))
            self.update_preview_from_editor()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


    # ─── Smart Auto-completion Event Filter ───

    def eventFilter(self, obj, event):
        if editor_commands.handle_event_filter(self, obj, event):
            return True
        return super().eventFilter(obj, event)

    def show_merge_dialog(self):
        document_tools.show_merge_dialog(self)

    def show_readability_dashboard(self):
        document_tools.show_readability_dashboard(self)

    def show_stats_menu(self):
        document_tools.show_stats_menu(self)

    def set_writing_goal(self):
        document_tools.set_writing_goal(self)

    def show_snippets_dialog(self):
        document_tools.show_snippets_dialog(self)

    def sync_scroll_preview(self, value):
        preview_manager.sync_scroll_preview(self, value)

    def toggle_zen_mode(self):
        self.is_zen_mode = not getattr(self, 'is_zen_mode', False)
        
        self.settings_group.setVisible(not self.is_zen_mode)
        self.history_group.setVisible(not self.is_zen_mode)
        self.log_output.setVisible(not self.is_zen_mode)
        self.tabs.setTabVisible(0, not self.is_zen_mode)
        
        if self.is_zen_mode:
            self.btn_zen.setStyleSheet("""
                QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #c2410c,stop:1 #ea580c); color: white; border: none; font-weight: bold; padding: 4px 10px; border-radius: 6px; }
            """)
        else:
            self.btn_zen.setStyleSheet("""
                QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #ea580c,stop:1 #f97316); color: white; border: none; font-weight: bold; padding: 4px 10px; border-radius: 6px; }
                QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #c2410c,stop:1 #ea580c); }
            """)

    def format_markdown_document(self):
        editor_commands.format_markdown_document(self)

    # ─── PDF → Markdown (OCR) ───

    def pdf_to_markdown_convert(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF (*.pdf)")
        if not path:
            return
        try:
            from src.core.pdf_to_markdown import pdf_to_markdown_file
            out = pdf_to_markdown_file(path)
            with open(out, "r", encoding="utf-8") as f:
                content = f.read()
            self.live_editor.setPlainText(content)
            self._render_live_preview()
            self.append_log(f"📄 PDF → Markdown: {out}")
            QMessageBox.information(self, "PDF → Markdown", f"Extracted to:\n{out}")
        except ImportError:
            QMessageBox.warning(self, "Error", "Install pypdf: pip install pypdf")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # ─── GitHub Sync ───

    def show_github_sync_dialog(self):
        from src.gui.dialogs import GitHubSyncDialog
        folder = self.active_workspace_folder or os.getcwd()
        dlg = GitHubSyncDialog(self, folder, self.current_lang)
        dlg.exec()

    # ─── Multi-cursor ───

    def add_multi_cursor(self):
        cursor = self.live_editor.textCursor()
        line = cursor.blockNumber()
        self.multi_cursor.add_cursor_at_line(line)

    def clear_multi_cursors(self):
        self.multi_cursor.clear_cursors()

    # ─── Plugin Manager ───

    def show_plugin_manager(self):
        from src.gui.dialogs import PluginManagerDialog
        dlg = PluginManagerDialog(self, self.current_lang)
        dlg.exec()

    # ─── Excalidraw ───

    def show_excalidraw(self):
        from src.gui.excalidraw_canvas import ExcalidrawDialog
        dlg = ExcalidrawDialog(self, self.current_lang)
        if dlg.exec() and dlg.selected_markdown:
            cursor = self.live_editor.textCursor()
            cursor.insertText(dlg.selected_markdown)
            self._render_live_preview()

    # ─── CSV Editor ───

    def show_csv_editor(self):
        from src.gui.csv_editor import CSVEditorDialog
        dlg = CSVEditorDialog(self, self.current_lang)
        if dlg.exec() and dlg.selected_markdown:
            cursor = self.live_editor.textCursor()
            cursor.insertText(dlg.selected_markdown)
            self._render_live_preview()

    # ─── Template Variables ───

    def apply_template_vars(self):
        text = self.live_editor.toPlainText()
        filename = self.selected_files[0] if self.selected_files else ""
        result = process_document_vars(text, filename)
        self.live_editor.setPlainText(result)
        self._render_live_preview()
        self.append_log("🔧 Template variables applied")

    # ─── Calendar Notes ───

    def show_calendar_notes(self):
        from src.gui.calendar_view import CalendarNotesDialog
        folder = self.active_workspace_folder or os.getcwd()
        dlg = CalendarNotesDialog(self, self.current_lang, folder)
        dlg.exec()

    # ─── Pomodoro Timer ───

    def show_pomodoro(self):
        from src.gui.pomodoro import PomodoroDialog
        dlg = PomodoroDialog(self, self.current_lang)
        dlg.exec()

    # ─── Writing Goals (enhanced) ───

    def set_writing_goal(self):
        from PyQt6.QtWidgets import QInputDialog
        goal, ok = QInputDialog.getInt(
            self, "🎯 Writing Goal" if self.current_lang == "en" else "🎯 Цель по словам",
            "Target word count (0 to disable):" if self.current_lang == "en" else "Целевое количество слов (0 для отключения):",
            self.writing_goal, 0, 100000
        )
        if ok:
            self.writing_goal = goal
            self.goal_celebrated = False
            self.update_text_statistics()

    # ─── Toast Notifications ───

    def toast(self, message: str, toast_type: str = "info", duration: int = 3000):
        """Show a modern toast notification."""
        return ToastNotification.show_toast(self, message, toast_type, duration)

    # ─── About Dialog ───

    def show_about(self):
        from src.__version__ import __version__
        dlg = AboutDialog(self, __version__, self.current_lang)
        dlg.exec()

    def show_shortcuts(self):
        from src.gui.dialogs import ShortcutsDialog
        dlg = ShortcutsDialog(self, self.current_lang)
        dlg.exec()

    # ─── Welcome Tour ───

    def show_welcome_tour(self):
        from src.gui.welcome_tour import WelcomeTourDialog
        dlg = WelcomeTourDialog(self, self.current_lang)
        dlg.exec()

    # ─── Custom Title Bar ───

    def _setup_custom_titlebar(self):
        """Enable custom frameless title bar."""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self._titlebar = CustomTitleBar(self, self.windowTitle())
        self._titlebar.setGeometry(0, 0, self.width(), 42)
        self._titlebar.show()

    # ─── Ambient Glow ───

    def _setup_ambient_glow(self):
        """Enable animated ambient glow orbs."""
        self._glow = AmbientGlowWidget(self)
        self._glow.setGeometry(0, 0, self.width(), self.height())
        self._glow.lower()
        self._glow.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_glow') and self._glow.isVisible():
            self._glow.setGeometry(0, 0, self.width(), self.height())
        if hasattr(self, '_titlebar') and self._titlebar.isVisible():
            self._titlebar.setGeometry(0, 0, self.width(), 42)

    # ─── Image → Text (OCR) ───

    def ocr_image_to_text(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image for OCR", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.webp)"
        )
        if not path:
            return
        try:
            from src.core.ocr_engine import image_to_markdown
            md = image_to_markdown(path)
            cursor = self.live_editor.textCursor()
            cursor.insertText(md)
            self._render_live_preview()
            self.append_log(f"🖼 OCR completed: {os.path.basename(path)}")
        except ImportError:
            QMessageBox.warning(self, "OCR", "Install: pip install pytesseract Pillow\nAlso install Tesseract OCR from https://github.com/tesseract-ocr/tesseract")
        except Exception as e:
            QMessageBox.critical(self, "OCR Error", str(e))

    # ─── LaTeX Preview ───

    def show_latex_preview(self):
        from src.core.latex_preview import find_latex_expressions, latex_to_url
        text = self.live_editor.toPlainText()
        expressions = find_latex_expressions(text)

        if not expressions:
            QMessageBox.information(self, "LaTeX", "No LaTeX expressions found (use $...$ or $$...$$)")
            return

        html_parts = ["<html><head><style>body{font-family:sans-serif;padding:20px;} .expr{margin:16px;padding:12px;background:#f8f9fa;border-radius:8px;border:1px solid #dfe4ea;} .src{font-family:monospace;color:#7f8c8d;font-size:12px;}</style></head><body>"]
        html_parts.append(f"<h2>📐 LaTeX Preview ({len(expressions)} expressions)</h2>")

        for start, end, formula in expressions:
            url = latex_to_url(formula)
            html_parts.append(f'<div class="expr"><img src="{url}" alt="{formula}" style="max-width:100%;"/><br><span class="src">{formula}</span></div>')

        html_parts.append("</body></html>")

        dlg = QDialog(self)
        dlg.setWindowTitle("LaTeX Preview")
        dlg.setMinimumSize(600, 400)
        layout = QVBoxLayout(dlg)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml('\n'.join(html_parts))
        layout.addWidget(browser)
        btn = QPushButton("Close")
        btn.clicked.connect(dlg.close)
        layout.addWidget(btn)
        dlg.exec()

    # ─── Multi-Export ───

    def show_multi_export(self):
        if not self.selected_files:
            QMessageBox.information(self, "Multi-Export", "Select a file first")
            return

        from src.gui.dialogs import MultiExportDialog
        dlg = MultiExportDialog(self, self.current_lang)
        if dlg.exec():
            from src.core.multi_export import multi_export, export_summary
            out_dir = QFileDialog.getExistingDirectory(self, "Output Directory")
            if not out_dir:
                return
            results = multi_export(
                self.selected_files[0], out_dir, dlg.selected_formats,
                self._get_template_dir(), self._get_options()
            )
            summary = export_summary(results)
            QMessageBox.information(self, "Multi-Export", summary)
            self.append_log(f"📦 Multi-export completed: {len(results)} formats")

    # ─── Text-to-Speech ───

    def text_to_speech_speak(self):
        text = self.live_editor.toPlainText()
        if not text.strip():
            QMessageBox.information(self, "TTS", "No text to speak")
            return

        from src.core.tts_engine import strip_markdown_for_tts, get_tts_engine
        clean = strip_markdown_for_tts(text)
        engine = get_tts_engine()

        def on_state(state):
            icons = {"playing": "🔊", "paused": "⏸", "stopped": "⏹"}
            self.append_log(f"{icons.get(state, '🔊')} TTS: {state}")

        engine.set_on_state_change(on_state)

        if engine.is_playing():
            engine.stop()
            self.toast("TTS остановлен", "info")
            return

        engine.speak(clean, lang=self.current_lang)
        self.toast("🔊 Воспроизведение...", "success")

    def show_tts_settings(self):
        from src.core.tts_engine import get_tts_engine
        engine = get_tts_engine()
        voices = engine.get_voices()

        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSlider, QPushButton
        dlg = QDialog(self)
        dlg.setWindowTitle("🔊 TTS Settings")
        dlg.setMinimumWidth(400)
        layout = QVBoxLayout(dlg)

        # Voice selection
        voice_layout = QHBoxLayout()
        voice_layout.addWidget(QLabel("Голос:"))
        voice_combo = QComboBox()
        for v in voices:
            gender_icon = {"male": "👨", "female": "👩", "neutral": "🤖"}.get(v.gender.value, "🔊")
            premium = " ⭐" if v.is_premium else ""
            voice_combo.addItem(f"{gender_icon} {v.name} ({v.language}){premium} - {v.description}", v.id)
        voice_layout.addWidget(voice_combo)
        layout.addLayout(voice_layout)

        # Speed
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Скорость:"))
        speed_slider = QSlider(Qt.Orientation.Horizontal)
        speed_slider.setRange(50, 200)
        speed_slider.setValue(int(engine.settings.speed * 100))
        speed_label = QLabel(f"{engine.settings.speed:.1f}x")
        speed_slider.valueChanged.connect(lambda v: speed_label.setText(f"{v/100:.1f}x"))
        speed_layout.addWidget(speed_slider)
        speed_layout.addWidget(speed_label)
        layout.addLayout(speed_layout)

        # Pitch
        pitch_layout = QHBoxLayout()
        pitch_layout.addWidget(QLabel("Тон:"))
        pitch_slider = QSlider(Qt.Orientation.Horizontal)
        pitch_slider.setRange(50, 200)
        pitch_slider.setValue(int(engine.settings.pitch * 100))
        pitch_label = QLabel(f"{engine.settings.pitch:.1f}")
        pitch_slider.valueChanged.connect(lambda v: pitch_label.setText(f"{v/100:.1f}"))
        pitch_layout.addWidget(pitch_slider)
        pitch_layout.addWidget(pitch_label)
        layout.addLayout(pitch_layout)

        # Volume
        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel("Громкость:"))
        vol_slider = QSlider(Qt.Orientation.Horizontal)
        vol_slider.setRange(0, 100)
        vol_slider.setValue(int(engine.settings.volume * 100))
        vol_label = QLabel(f"{int(engine.settings.volume * 100)}%")
        vol_slider.valueChanged.connect(lambda v: vol_label.setText(f"{v}%"))
        vol_layout.addWidget(vol_slider)
        vol_layout.addWidget(vol_label)
        layout.addLayout(vol_layout)

        # Pause
        pause_layout = QHBoxLayout()
        pause_layout.addWidget(QLabel("Пауза абзацев:"))
        pause_slider = QSlider(Qt.Orientation.Horizontal)
        pause_slider.setRange(0, 200)
        pause_slider.setValue(int(engine.settings.pause_between_paragraphs * 100))
        pause_label = QLabel(f"{engine.settings.pause_between_paragraphs:.1f}s")
        pause_slider.valueChanged.connect(lambda v: pause_label.setText(f"{v/100:.1f}s"))
        pause_layout.addWidget(pause_slider)
        pause_layout.addWidget(pause_label)
        layout.addLayout(pause_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_export = QPushButton("💾 Export to File")
        btn_export.clicked.connect(lambda: self._export_tts_audio(engine))
        btn_layout.addWidget(btn_export)

        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(dlg.accept)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

        def apply_settings():
            engine.set_voice(voice_combo.currentData())
            engine.set_speed(speed_slider.value() / 100)
            engine.set_pitch(pitch_slider.value() / 100)
            engine.set_volume(vol_slider.value() / 100)
            engine.set_pause_between_paragraphs(pause_slider.value() / 100)

        btn_export.clicked.connect(apply_settings)
        dlg.exec()

    def _export_tts_audio(self, engine):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Audio", "speech.mp3",
            "MP3 (*.mp3);;WAV (*.wav);;All (*)"
        )
        if path:
            text = self.live_editor.toPlainText()
            clean = strip_markdown_for_tts(text)
            if engine.export_to_file(clean, path, self.current_lang):
                self.toast(f"✅ Audio saved: {os.path.basename(path)}", "success")
            else:
                self.toast("❌ Export failed", "error")

    # ─── HTML → Markdown ───

    def html_to_markdown_convert(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select HTML file", "", "HTML (*.html *.htm)")
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        md = html_to_markdown(html)
        self.live_editor.setPlainText(md)
        self._render_live_preview()
        self.append_log(f"🔄 HTML → Markdown: {os.path.basename(path)}")

    # ─── Watermark Designer ───

    def show_watermark_designer(self):
        from src.gui.watermark_designer import WatermarkDesignerDialog
        dlg = WatermarkDesignerDialog(self, self.current_lang)
        if dlg.exec():
            self.footer_input.setText(f"[WATERMARK:{self.footer_input.text()}]")
            self.append_log("🎨 Watermark applied")

    # ─── Flashcards ───

    def generate_flashcards(self):
        text = self.live_editor.toPlainText()
        cards = extract_flashcards(text)
        if not cards:
            QMessageBox.information(self, "Flashcards", "No flashcards found (need headings with content)")
            return

        from src.core.flashcards import cards_to_html, cards_to_markdown

        dlg = QDialog(self)
        dlg.setWindowTitle(f"🃏 Flashcards ({len(cards)} cards)")
        dlg.setMinimumSize(700, 500)
        layout = QVBoxLayout(dlg)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(cards_to_html(cards))
        layout.addWidget(browser)

        btn_row = QHBoxLayout()
        btn_export_md = QPushButton("📝 Export as Markdown")
        btn_export_md.clicked.connect(lambda: self._export_flashcards_md(cards))
        btn_row.addWidget(btn_export_md)
        btn_export_html = QPushButton("🌐 Export as HTML")
        btn_export_html.clicked.connect(lambda: self._export_flashcards_html(cards))
        btn_row.addWidget(btn_export_html)
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dlg.close)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)
        dlg.exec()

    def _export_flashcards_md(self, cards):
        from src.core.flashcards import cards_to_markdown
        path, _ = QFileDialog.getSaveFileName(self, "Export Flashcards", "", "Markdown (*.md)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(cards_to_markdown(cards))

    def _export_flashcards_html(self, cards):
        from src.core.flashcards import cards_to_html
        path, _ = QFileDialog.getSaveFileName(self, "Export Flashcards", "", "HTML (*.html)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(cards_to_html(cards))

    # ─── Citation Manager ───

    def show_citation_manager(self):
        from src.gui.dialogs import CitationManagerDialog
        dlg = CitationManagerDialog(self, self.current_lang)
        dlg.exec()

    # ─── Glossary Builder ───

    def build_glossary(self):
        text = self.live_editor.toPlainText()
        defs = extract_definitions(text)
        if not defs:
            QMessageBox.information(self, "Glossary", "No definitions found (use **Term**: definition)")
            return

        from src.core.glossary import glossary_to_html
        html = glossary_to_html(defs)

        dlg = QDialog(self)
        dlg.setWindowTitle(f"📖 Glossary ({len(defs)} terms)")
        dlg.setMinimumSize(600, 400)
        layout = QVBoxLayout(dlg)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(html)
        layout.addWidget(browser)
        btn = QPushButton("Close")
        btn.clicked.connect(dlg.close)
        layout.addWidget(btn)
        dlg.exec()

    # ─── Quiz Generator ───

    def generate_quiz(self):
        text = self.live_editor.toPlainText()
        quiz = generate_quiz_from_text(text)
        if not quiz["questions"]:
            QMessageBox.information(self, "Quiz", "Not enough content to generate quiz")
            return

        from src.core.quiz_generator import quiz_to_html
        html = quiz_to_html(quiz)

        dlg = QDialog(self)
        dlg.setWindowTitle(f"📝 Quiz ({quiz['total']} questions)")
        dlg.setMinimumSize(700, 500)
        layout = QVBoxLayout(dlg)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(html)
        layout.addWidget(browser)
        btn = QPushButton("Close")
        btn.clicked.connect(dlg.close)
        layout.addWidget(btn)
        dlg.exec()


# ─── CSS Theme / Document Builder / Readability Utilities ───

def estimate_readability(text: str, lang: str):
    from src.gui.document_tools import estimate_readability as _est
    return _est(text, lang)


def _get_options(window) -> ConversionOptions:
    return ConversionOptions(
        doc_theme=window.doc_theme_combo.currentData(),
        code_theme=window.code_theme_combo.currentData(),
        paper_size=window.paper_combo.currentText(),
        watermark=window.watermark_input.text().strip(),
        footer_text=window.footer_input.text().strip(),
        custom_css=window.custom_css_input.text().strip(),
        export_format=window.format_combo.currentData(),
        pdf_password=window.pdf_password_input.text().strip(),
        margins=window.margins_input.text().strip(),
        docx_template=window.docx_template_input.text().strip(),
        page_numbers=window.chk_page_numbers.isChecked(),
        page_num_format=window.combo_page_format.currentData() or "simple",
        is_presentation=window.chk_presentation_mode.isChecked(),
        compress=window.chk_compress.isChecked(),
    )


from PyQt6.QtWidgets import QListWidget, QFileDialog, QGroupBox
