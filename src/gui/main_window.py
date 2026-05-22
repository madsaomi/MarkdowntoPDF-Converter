import sys
import os
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

from src.core.parser import MarkdownParser
from src.core.renderer import PDFRenderer
from src.core.docx_renderer import DOCXRenderer
from src.gui.ui_layout import setup_ui
from src.__version__ import __version__
from src.gui.translations import TRANSLATIONS
from src.gui.welcome_docs import WELCOME_RU, WELCOME_EN

# ──────────────────────── Logging setup ────────────────────────

LOG_DIR = os.path.join(os.getenv("APPDATA", "."), "MarkdownToPDF_Pro", "logs")
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

# ──────────────────────── Dark / Light stylesheets ────────────────────────

LIGHT_STYLE = """
QMainWindow { background-color: #f8f9fa; }
QWidget { background-color: #f8f9fa; color: #2c3e50; }
QLabel { color: #2c3e50; }
QComboBox { padding: 4px; border: 1px solid #ced4da; border-radius: 3px; background-color: #ffffff; color: #2c3e50; }
QComboBox QAbstractItemView { background-color: #ffffff; color: #2c3e50; selection-background-color: #e9ecef; }
QLineEdit { padding: 4px; border: 1px solid #ced4da; border-radius: 3px; background-color: #ffffff; color: #2c3e50; }
QGroupBox { font-weight: bold; border: 1px solid #ced4da; border-radius: 5px; margin-top: 10px; padding-top: 15px; color: #2c3e50; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
QTextEdit { background-color: #ffffff; border: 1px solid #ced4da; color: #2c3e50; }
QProgressBar { border: 1px solid #ced4da; border-radius: 5px; background-color: #e9ecef; }
QProgressBar::chunk { background-color: #4caf50; border-radius: 5px; }
QMenuBar { background-color: #f8f9fa; color: #2c3e50; }
QMenuBar::item:selected { background-color: #e9ecef; }
QMenu { background-color: #ffffff; color: #2c3e50; border: 1px solid #ced4da; }
QMenu::item:selected { background-color: #e9ecef; }
"""

DARK_STYLE = """
QMainWindow { background-color: #1e1e2e; }
QWidget { background-color: #1e1e2e; color: #cdd6f4; }
QLabel { color: #cdd6f4; }
QComboBox { padding: 4px; border: 1px solid #45475a; border-radius: 3px; background-color: #313244; color: #cdd6f4; }
QComboBox QAbstractItemView { background-color: #313244; color: #cdd6f4; selection-background-color: #585b70; }
QLineEdit { padding: 4px; border: 1px solid #45475a; border-radius: 3px; background-color: #313244; color: #cdd6f4; }
QGroupBox { font-weight: bold; border: 1px solid #45475a; border-radius: 5px; margin-top: 10px; padding-top: 15px; color: #cdd6f4; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
QTextEdit { background-color: #313244; border: 1px solid #45475a; color: #a6e3a1; }
QProgressBar { border: 1px solid #45475a; border-radius: 5px; background-color: #313244; }
QProgressBar::chunk { background-color: #a6e3a1; border-radius: 5px; }
QMenuBar { background-color: #1e1e2e; color: #cdd6f4; }
QMenuBar::item:selected { background-color: #313244; }
QMenu { background-color: #313244; color: #cdd6f4; }
QMenu::item:selected { background-color: #585b70; }
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

        # Start Kroki.io connectivity check
        self.kroki_thread = KrokiCheckThread()
        self.kroki_thread.finished.connect(self.on_kroki_check_finished)
        self.kroki_thread.start()

        # Settings persistence
        self.settings = QSettings(APP_NAME, APP_NAME)
        self.current_lang = self.settings.value("language", "ru", str)
        self.export_history = self.settings.value("export_history", [], list)

        # File watcher for auto-regenerate mode
        self.watcher = QFileSystemWatcher(self)
        self.watcher.fileChanged.connect(self.on_file_changed)
        self.watch_active = False
        self.watch_output_dir = ""

        # App icon
        icon_path = self._resolve_asset("assets/icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        setup_ui(self)
        
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
        if getattr(sys, 'frozen', False):
            base = sys._MEIPASS
        else:
            base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        return os.path.join(base, rel_path)

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
        recent = self.settings.value("recent_files", [], list)
        if filepath in recent:
            recent.remove(filepath)
        recent.insert(0, filepath)
        recent = recent[:self.MAX_RECENT]
        self.settings.setValue("recent_files", recent)
        self.update_recent_menu()

    def update_recent_menu(self):
        self.recent_menu.clear()
        recent = self.settings.value("recent_files", [], list)
        if not recent:
            act = self.recent_menu.addAction(self.tr_msg("menu_empty"))
            act.setEnabled(False)
            return
        for filepath in recent:
            act = self.recent_menu.addAction(os.path.basename(filepath))
            act.setData(filepath)
            act.triggered.connect(lambda checked, p=filepath: self.open_recent(p))

    def open_recent(self, filepath: str):
        if not os.path.exists(filepath):
            QMessageBox.warning(self, self.tr_msg("msg_file_not_found"), self.tr_msg("msg_file_moved", filepath))
            return
        self.selected_files = [filepath]
        self.active_workspace_folder = None
        self.explorer_group.hide()
        self.file_label.setText(os.path.basename(filepath))
        self.btn_convert.setEnabled(True)
        self.btn_watch.setEnabled(True)
        self.log_output.clear()
        self.progress_bar.setValue(0)
        self.append_log(self.tr_msg("log_opened_recent", filepath))
        self.update_preview(filepath)

    # ─── Dark / Light toggle ───

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        app = QApplication.instance()
        t = lambda k: TRANSLATIONS[self.current_lang].get(k, k)
        if self.is_dark:
            app.setStyleSheet(DARK_STYLE)
            self.btn_theme.setText(t('btn_theme_light'))
        else:
            app.setStyleSheet(LIGHT_STYLE)
            self.btn_theme.setText(t('btn_theme_dark'))
        
        if hasattr(self, 'highlighter'):
            self.highlighter.set_theme(self.is_dark)
            self.highlighter.rehighlight()

    # ─── Drag & Drop ───

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(u.toLocalFile().endswith('.md') or os.path.isdir(u.toLocalFile()) for u in urls):
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

    # ─── File / Folder selection ───

    def select_custom_css(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Выберите CSS файл", "", "CSS Files (*.css);;All Files (*)"
        )
        if filepath:
            self.custom_css_input.setText(filepath)

    def select_docx_template(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Выберите шаблон DOCX", "", "Word Documents (*.docx);;All Files (*)"
        )
        if filepath:
            self.docx_template_input.setText(filepath)

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Выберите Markdown файлы", "",
            "Markdown Files (*.md);;All Files (*)"
        )
        if files:
            self.selected_files = files
            self.active_workspace_folder = None
            self.explorer_group.hide()
            for f in files:
                self.add_to_recent(f)
            names = ", ".join(os.path.basename(f) for f in files)
            self.file_label.setText(self.tr_msg("files_selected", len(files), names))
            self.btn_convert.setEnabled(True)
            self.btn_watch.setEnabled(len(files) == 1)
            self.log_output.clear()
            self.progress_bar.setValue(0)
            self.append_log(self.tr_msg("log_selected", len(files)))
            self.update_preview(files[0])

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку с .md файлами")
        if folder:
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
                QPushButton { background-color: #27ae60; color: white; font-weight: bold;
                              padding: 12px; border-radius: 5px; font-size: 13px; }
                QPushButton:hover { background-color: #219a52; }
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
                QPushButton { background-color: #95a5a6; color: white; font-weight: bold;
                              padding: 12px; border-radius: 5px; font-size: 13px; }
                QPushButton:hover { background-color: #7f8c8d; }
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
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        return os.path.join(base_path, 'templates')

    def _get_weasyprint_path(self) -> str:
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        return os.path.join(base_path, 'weasyprint-windows', 'dist', 'weasyprint.exe')

    @staticmethod
    def _get_extension(export_format: str) -> str:
        fmt_map = {
            ExportFormat.PDF: ".pdf",
            ExportFormat.DOCX: ".docx",
            ExportFormat.HTML: ".html",
        }
        return fmt_map.get(export_format, ".pdf")

    def _get_options(self) -> ConversionOptions:
        return ConversionOptions(
            doc_theme=self.doc_theme_combo.currentData(),
            code_theme=self.code_theme_combo.currentData(),
            paper_size=self.paper_combo.currentText(),
            watermark=self.watermark_input.text().strip(),
            footer_text=self.footer_input.text().strip(),
            custom_css=self.custom_css_input.text().strip(),
            export_format=self.format_combo.currentData(),
            pdf_password=self.pdf_password_input.text().strip(),
            margins=self.margins_input.text().strip(),
            docx_template=self.docx_template_input.text().strip(),
            page_numbers=self.chk_page_numbers.isChecked(),
            page_num_format=self.combo_page_format.currentData() or "simple",
            is_presentation=self.chk_presentation_mode.isChecked(),
        )

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
        md_text = self.live_editor.toPlainText()
        if not md_text:
            return
        try:
            is_pres = self.chk_presentation_mode.isChecked()
            parser = MarkdownParser()
            html, _ = parser.parse(md_text, base_dir=self.get_current_document_dir(), is_presentation=is_pres, kroki_available=self.kroki_available)
            
            if is_pres:
                preview_html = f"""
                <html><head><style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: #111827;
                    margin: 0;
                    padding: 20px;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                }}
                .slide {{
                    width: 90%;
                    max-width: 800px;
                    aspect-ratio: 16 / 9;
                    background: linear-gradient(135deg, #1e1b4b 0%, #311042 100%);
                    color: #f1f5f9;
                    margin-bottom: 20px;
                    padding: 40px;
                    box-sizing: border-box;
                    border-radius: 12px;
                    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: flex-start;
                    position: relative;
                    overflow: hidden;
                }}
                .slide::after {{
                    content: "";
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    width: 100%;
                    height: 4px;
                    background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
                }}
                .slide h1 {{ font-size: 28pt; color: #fbbf24; margin: 0 0 10px 0; font-weight: 800; border: none; }}
                .slide h2 {{ font-size: 20pt; color: #38bdf8; margin: 0 0 10px 0; font-weight: 700; border: none; }}
                .slide p, .slide li {{ font-size: 13pt; line-height: 1.6; color: #cbd5e1; }}
                .slide blockquote {{
                    margin: 10px 0;
                    padding: 10px 15px;
                    border-left: 4px solid #a855f7;
                    background: rgba(168, 85, 247, 0.08);
                    border-radius: 0 8px 8px 0;
                }}
                .slide blockquote p {{ font-style: italic; color: #e9d5ff; }}
                .slide pre, .slide .codehilite {{
                    background: rgba(15, 23, 42, 0.6);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                    padding: 10px 15px;
                    width: 100%;
                    box-sizing: border-box;
                }}
                .slide code {{
                    background: rgba(15, 23, 42, 0.6);
                    padding: 2px 4px;
                    border-radius: 4px;
                    color: #38bdf8;
                }}
                .slide pre code {{ background: transparent; color: inherit; }}
                .slide img {{ max-width: 100%; max-height: 250px; height: auto; }}
                </style></head><body>{html}</body></html>
                """
            else:
                # Wrap in basic HTML structure with styles for preview
                preview_html = f"""
                <html><head><style>
                body {{ font-family: sans-serif; color: #333; }}
                pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; white-space: pre-wrap; word-wrap: break-word; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; }}
                img {{ max-width: 100%; height: auto; }}
                </style></head><body>{html}</body></html>
                """
            self.preview_output.setHtml(preview_html)
        except Exception as e:
            pass

    def on_all_done(self):
        self.btn_cancel.hide()
        self.btn_convert.show()
        self.btn_convert.setEnabled(True)
        if self.thread is not None and not self.thread.is_cancelled():
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
            self.history_placeholder.setStyleSheet("color: #7f8c8d; font-style: italic; font-size: 11px; padding: 5px;")
            self.history_layout.addWidget(self.history_placeholder)
            return
            
        for filepath in self.export_history:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(5, 2, 5, 2)
            row_layout.setSpacing(10)
            
            lbl = QLabel(os.path.basename(filepath))
            lbl.setStyleSheet("font-size: 11px; color: #2c3e50; font-weight: bold;")
            lbl.setToolTip(filepath)
            
            btn_open = QPushButton(t('btn_history_open'))
            btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_open.setStyleSheet("""
                QPushButton { background: #3498db; color: white; padding: 3px 8px; border-radius: 3px; font-size: 10px; border: none; font-weight: bold; }
                QPushButton:hover { background: #2980b9; }
            """)
            btn_open.clicked.connect(lambda checked, p=filepath: self.open_exported_file(p))
            
            btn_folder = QPushButton(t('btn_history_folder'))
            btn_folder.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_folder.setStyleSheet("""
                QPushButton { background: #7f8c8d; color: white; padding: 3px 8px; border-radius: 3px; font-size: 10px; border: none; font-weight: bold; }
                QPushButton:hover { background: #5d6d7e; }
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
        if self.is_welcome_doc_active:
            return
        text = self.live_editor.toPlainText().strip()
        if not text:
            if os.path.exists(self.draft_path):
                try:
                    os.remove(self.draft_path)
                except Exception:
                    pass
            return
        try:
            with open(self.draft_path, "w", encoding="utf-8") as f:
                f.write(self.live_editor.toPlainText())
        except Exception as e:
            logger.error("Failed to autosave draft: %s", e)
            
        # Double autosave to current workspace file!
        if self.current_workspace_file and os.path.exists(self.current_workspace_file):
            try:
                with open(self.current_workspace_file, "w", encoding="utf-8") as f:
                    f.write(self.live_editor.toPlainText())
            except Exception as e:
                logger.error("Failed to autosave workspace file: %s", e)
                
        # Rolling backup point
        self.save_revision()

    def save_current_workspace_file(self):
        if self.current_workspace_file and os.path.exists(self.current_workspace_file):
            try:
                content = self.live_editor.toPlainText()
                with open(self.current_workspace_file, "w", encoding="utf-8") as f:
                    f.write(content)
                self.save_revision()
            except Exception as e:
                logger.error("Failed to save workspace file: %s", e)

    def save_revision(self):
        filepath = self.current_workspace_file
        if not filepath and self.selected_files:
            filepath = self.selected_files[0]
            
        if not filepath or not os.path.exists(filepath):
            return
            
        text = self.live_editor.toPlainText()
        if not text.strip() or self.is_welcome_doc_active:
            return
            
        try:
            import hashlib
            from datetime import datetime
            
            backups_dir = os.path.join(self.app_data_dir, "backups")
            file_hash = hashlib.md5(os.path.abspath(filepath).encode('utf-8')).hexdigest()
            file_backup_dir = os.path.join(backups_dir, file_hash)
            os.makedirs(file_backup_dir, exist_ok=True)
            
            backups = sorted(os.listdir(file_backup_dir))
            if backups:
                latest_backup_path = os.path.join(file_backup_dir, backups[-1])
                try:
                    with open(latest_backup_path, "r", encoding="utf-8") as f:
                        latest_content = f.read()
                    if latest_content == text:
                        return
                except Exception:
                    pass
                    
            if len(backups) >= 20:
                for b in backups[:-19]:
                    try:
                        os.remove(os.path.join(file_backup_dir, b))
                    except Exception:
                        pass
                        
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            words = len([w for w in text.split() if w.strip()])
            backup_filename = f"{timestamp}_{words}.md"
            backup_filepath = os.path.join(file_backup_dir, backup_filename)
            with open(backup_filepath, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception as e:
            logger.error("Failed to save revision backup: %s", e)

    def show_revision_history(self):
        filepath = self.current_workspace_file
        if not filepath and self.selected_files:
            filepath = self.selected_files[0]
            
        if not filepath:
            QMessageBox.warning(self, self.tr_msg("msg_file_not_found"), self.tr_msg("history_empty"))
            return
            
        import hashlib
        backups_dir = os.path.join(self.app_data_dir, "backups")
        file_hash = hashlib.md5(os.path.abspath(filepath).encode('utf-8')).hexdigest()
        file_backup_dir = os.path.join(backups_dir, file_hash)
        
        dialog = RevisionHistoryDialog(file_backup_dir, parent=self, lang=self.current_lang)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.selected_content is not None:
                self.live_editor.blockSignals(True)
                self.live_editor.setPlainText(dialog.selected_content)
                self.live_editor.blockSignals(False)
                self._render_live_preview()
                self.update_text_statistics()
                self.append_log(self.tr_msg("log_draft_restored"))

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
        text = self.live_editor.toPlainText()
        lines = text.splitlines()
        issues = []
        
        t = lambda k: TRANSLATIONS[self.current_lang].get(k, k)
        
        last_level = 0
        
        base_dir = None
        if self.current_workspace_file:
            base_dir = os.path.dirname(self.current_workspace_file)
        elif self.selected_files:
            base_dir = os.path.dirname(self.selected_files[0])
        else:
            base_dir = os.getcwd()
            
        import re
        
        for idx, line in enumerate(lines):
            line_num = idx + 1
            
            # --- 1. STRUCTURE CHECKS ---
            header_match = re.match(r'^(#{1,6})\s+(.*)$', line)
            if header_match:
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                
                if not title:
                    issues.append({
                        "line": line_num,
                        "type": t('audit_type_struct'),
                        "desc": "Пустой заголовок" if self.current_lang == "ru" else "Empty header level"
                    })
                else:
                    if level > last_level + 1:
                        issues.append({
                            "line": line_num,
                            "type": t('audit_type_struct'),
                            "desc": f"Пропуск уровня заголовка: переход с H{last_level} на H{level}" if self.current_lang == "ru" else f"Skipped header level: H{last_level} to H{level}"
                        })
                    last_level = level
                    
            # --- 2. TYPOGRAPHY CHECKS ---
            if '"' in line:
                issues.append({
                    "line": line_num,
                    "type": t('audit_type_typo'),
                    "desc": 'Использование прямых кавычек " вместо «»' if self.current_lang == "ru" else 'Straight quotes (") used instead of curly/angled quotes'
                })
                
            if re.search(r'[^ ] {2,}[^ ]', line):
                issues.append({
                    "line": line_num,
                    "type": t('audit_type_typo'),
                    "desc": 'Обнаружено несколько последовательных пробелов' if self.current_lang == "ru" else 'Multiple consecutive spaces detected'
                })
                
            punc_matches = re.finditer(r'([,;:])([^\s\d])', line)
            for m in punc_matches:
                char = m.group(1)
                issues.append({
                    "line": line_num,
                    "type": t('audit_type_typo'),
                    "desc": f'Пропущен пробел после знака препинания "{char}"' if self.current_lang == "ru" else f'Missing space after punctuation "{char}"'
                })
                
            if line.endswith(' ') and not line.endswith('  '):
                issues.append({
                    "line": line_num,
                    "type": t('audit_type_typo'),
                    "desc": 'Лишний висячий пробел в конце строки' if self.current_lang == "ru" else 'Trailing space at end of line'
                })
                
            # --- 3. MEDIA & LINKS ---
            img_matches = re.finditer(r'!\[.*?\]\((.*?)\)', line)
            for m in img_matches:
                img_path = m.group(1).strip()
                if not img_path:
                    issues.append({
                        "line": line_num,
                        "type": t('audit_type_media'),
                        "desc": 'Пустая ссылка на изображение' if self.current_lang == "ru" else 'Empty image reference link'
                    })
                elif not img_path.startswith(('http://', 'https://', 'data:')):
                    full_img_path = img_path
                    if base_dir and not os.path.isabs(img_path):
                        full_img_path = os.path.join(base_dir, img_path)
                    
                    if not os.path.exists(full_img_path):
                        issues.append({
                            "line": line_num,
                            "type": t('audit_type_media'),
                            "desc": f'Локальный файл изображения не найден на диске: {img_path}' if self.current_lang == "ru" else f'Local image file not found on disk: {img_path}'
                        })
                        
            link_matches = re.finditer(r'\[.*?\]\(\s*\)', line)
            for m in link_matches:
                issues.append({
                    "line": line_num,
                    "type": t('audit_type_media'),
                    "desc": 'Обнаружена пустая гиперссылка []()' if self.current_lang == "ru" else 'Empty hyperlink []() detected'
                })

        dialog = DocumentAuditorDialog(issues, parent=self, lang=self.current_lang)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.selected_line is not None:
                self.goto_editor_line(dialog.selected_line)

    def auto_fix_document_issues(self):
        text = self.live_editor.toPlainText()
        lines = text.splitlines()
        fixed_lines = []
        
        import re
        
        for line in lines:
            # 1. Trailing spaces (except double spaces at end of line for manual line breaks in Markdown)
            if line.endswith(' ') and not line.endswith('  '):
                line = line.rstrip()
                
            # 2. Straight quotes -> Russian «елочки» or English “curly”
            if self.current_lang == "ru":
                line = re.sub(r'(?<=[\s(^])"', '«', line)
                line = re.sub(r'"(?=[\s,.:;!?)$]|$)', '»', line)
                while '"' in line:
                    line = line.replace('"', '«', 1).replace('"', '»', 1)
            else:
                line = re.sub(r'(?<=[\s(^])"', '“', line)
                line = re.sub(r'"(?=[\s,.:;!?)$]|$)', '”', line)
                while '"' in line:
                    line = line.replace('"', '“', 1).replace('"', '”', 1)
                    
            # 3. Missing space after punctuation [,;:] if followed by non-space non-digit
            line = re.sub(r'([,;:])([^\s\d])', r'\1 \2', line)
            
            fixed_lines.append(line)
            
        new_text = "\n".join(fixed_lines)
        if new_text != text:
            scroll_pos = self.live_editor.verticalScrollBar().value()
            self.live_editor.blockSignals(True)
            self.live_editor.setPlainText(new_text)
            self.live_editor.blockSignals(False)
            self._render_live_preview()
            self.update_text_statistics()
            self.live_editor.verticalScrollBar().setValue(scroll_pos)
            
            t = lambda k: TRANSLATIONS[self.current_lang].get(k, k)
            QMessageBox.information(
                self,
                t('msg_autofix_done_title'),
                t('msg_autofix_done_desc')
            )

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
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if not file_path or not os.path.exists(file_path):
            return
            
        self.save_current_workspace_file()
        self.current_workspace_file = file_path
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.is_welcome_doc_active = False
            self.live_editor.blockSignals(True)
            self.live_editor.setPlainText(content)
            self.live_editor.blockSignals(False)
            self._render_live_preview()
            self.update_text_statistics()
            
            for row in range(self.explorer_list.count()):
                li = self.explorer_list.item(row)
                if li.data(Qt.ItemDataRole.UserRole) == file_path:
                    self.explorer_list.blockSignals(True)
                    self.explorer_list.setCurrentItem(li)
                    li.setSelected(True)
                    self.explorer_list.blockSignals(False)
                    break
        except Exception as e:
            logger.error("Failed to load workspace file %s: %s", file_path, e)

    def update_workspace_explorer(self):
        if not self.active_workspace_folder or not os.path.exists(self.active_workspace_folder):
            self.explorer_group.hide()
            return
            
        self.explorer_list.blockSignals(True)
        self.explorer_list.clear()
        
        md_files = []
        try:
            for f in os.listdir(self.active_workspace_folder):
                if f.endswith('.md'):
                    md_files.append(os.path.join(self.active_workspace_folder, f))
        except Exception as e:
            logger.error("Failed to list files in folder %s: %s", self.active_workspace_folder, e)
            
        md_files.sort(key=lambda x: os.path.basename(x).lower())
        self.selected_files = md_files
        
        for file_path in md_files:
            item = QListWidgetItem(os.path.basename(file_path))
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            self.explorer_list.addItem(item)
            
        if md_files:
            if not self.current_workspace_file or self.current_workspace_file not in md_files:
                self.current_workspace_file = md_files[0]
                # Populate editor with the active file
                try:
                    with open(self.current_workspace_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    self.is_welcome_doc_active = False
                    self.live_editor.blockSignals(True)
                    self.live_editor.setPlainText(content)
                    self.live_editor.blockSignals(False)
                    self._render_live_preview()
                    self.update_text_statistics()
                except Exception as e:
                    logger.error("Failed to load initial file in explorer: %s", e)
                
            for row in range(self.explorer_list.count()):
                li = self.explorer_list.item(row)
                if li.data(Qt.ItemDataRole.UserRole) == self.current_workspace_file:
                    li.setSelected(True)
                    self.explorer_list.setCurrentItem(li)
                    break
                    
        self.explorer_list.blockSignals(False)

    def filter_workspace_explorer(self, text):
        query = text.lower().strip()
        for row in range(self.explorer_list.count()):
            item = self.explorer_list.item(row)
            if not query or query in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    def restore_draft_if_exists(self):
        if os.path.exists(self.draft_path):
            try:
                with open(self.draft_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if content:
                    self.is_welcome_doc_active = False
                    self.live_editor.blockSignals(True)
                    self.live_editor.setPlainText(content)
                    self.live_editor.blockSignals(False)
                    self._render_live_preview()
                    self.append_log(self.tr_msg("log_draft_restored"))
            except Exception as e:
                logger.error("Failed to restore draft: %s", e)

    def open_output_folder(self):
        out_dir = self.last_output_dir
        if not out_dir:
            if self.selected_files:
                out_dir = os.path.dirname(self.selected_files[0])
            else:
                out_dir = os.getcwd()
                
        if os.path.exists(out_dir):
            try:
                os.startfile(out_dir)
            except Exception as e:
                logger.error("Failed to open output folder: %s", e)
        else:
            QMessageBox.warning(self, self.tr_msg("msg_file_not_found"), f"Folder not found:\n{out_dir}")

    def show_table_generator_dialog(self):
        dialog = MarkdownTableDialog(self, lang=self.current_lang)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            rows = dialog.rows_spin.value()
            cols = dialog.cols_spin.value()
            
            table_md = "\n"
            table_md += "| " + " | ".join(f"Header {i+1}" for i in range(cols)) + " |\n"
            table_md += "| " + " | ".join("---" for _ in range(cols)) + " |\n"
            for r in range(rows):
                table_md += "| " + " | ".join(f"Row {r+1} Col {c+1}" for c in range(cols)) + " |\n"
            table_md += "\n"
            
            cursor = self.live_editor.textCursor()
            cursor.insertText(table_md)
            self.live_editor.setTextCursor(cursor)
            self.live_editor.setFocus()

    def zoom_in(self):
        self.live_editor.zoomIn(1)
        self.html_preview.zoomIn(1)
        self.zoom_level += 1

    def zoom_out(self):
        self.live_editor.zoomOut(1)
        self.html_preview.zoomOut(1)
        self.zoom_level -= 1

    def zoom_reset(self):
        if self.zoom_level > 0:
            self.live_editor.zoomOut(self.zoom_level)
            self.html_preview.zoomOut(self.zoom_level)
        elif self.zoom_level < 0:
            self.live_editor.zoomIn(-self.zoom_level)
            self.html_preview.zoomIn(-self.zoom_level)
        self.zoom_level = 0



    # ─── Quick Formatting Methods ───

    def _wrap_selection(self, prefix: str, suffix: str):
        cursor = self.live_editor.textCursor()
        text = cursor.selectedText()
        cursor.insertText(f"{prefix}{text}{suffix}")
        self.live_editor.setFocus()

    def format_bold(self):
        self._wrap_selection("**", "**")

    def format_italic(self):
        self._wrap_selection("*", "*")

    def format_code(self):
        cursor = self.live_editor.textCursor()
        text = cursor.selectedText()
        if "\n" in text or "\r" in text:
            self._wrap_selection("\n```\n", "\n```\n")
        else:
            self._wrap_selection("`", "`")

    def format_header(self, level: int):
        cursor = self.live_editor.textCursor()
        cursor.select(cursor.SelectionType.LineUnderCursor)
        text = cursor.selectedText().lstrip("#").lstrip()
        cursor.insertText(f"{'#' * level} {text}")
        self.live_editor.setFocus()

    def format_quote(self):
        cursor = self.live_editor.textCursor()
        cursor.select(cursor.SelectionType.LineUnderCursor)
        text = cursor.selectedText().lstrip(">").lstrip()
        cursor.insertText(f"> {text}")
        self.live_editor.setFocus()

    def format_list(self):
        cursor = self.live_editor.textCursor()
        cursor.select(cursor.SelectionType.LineUnderCursor)
        text = cursor.selectedText().lstrip("-").lstrip()
        cursor.insertText(f"- {text}")
        self.live_editor.setFocus()

    def insert_page_break(self):
        cursor = self.live_editor.textCursor()
        cursor.insertText('\n<div style="page-break-before: always;"></div>\n')
        self.live_editor.setFocus()

    def print_document(self):
        from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
        self._render_live_preview()
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            self.html_preview.print(printer)

    def copy_styled_html(self):
        html_content = self.html_preview.toHtml()
        clipboard = QApplication.clipboard()
        clipboard.setText(html_content)
        QMessageBox.information(
            self,
            self.tr_msg("msg_html_copied_title"),
            self.tr_msg("msg_html_copied_desc")
        )

    def show_design_style_dialog(self):
        dialog = PDFStyleEditorDialog(self, lang=self.current_lang)
        
        current_paper = self.paper_combo.currentText()
        if current_paper in ["A4", "Letter", "A5"]:
            dialog.paper_combo.setCurrentText(current_paper)
            
        if dialog.exec() == QDialog.DialogCode.Accepted:
            m_top = dialog.margin_top.value()
            m_right = dialog.margin_right.value()
            m_bottom = dialog.margin_bottom.value()
            m_left = dialog.margin_left.value()
            paper_size = dialog.paper_combo.currentText()
            
            self.margins_input.setText(f"{m_top}mm {m_right}mm {m_bottom}mm {m_left}mm")
            self.paper_combo.setCurrentText(paper_size)
            
            font_family = dialog.font_combo.currentText()
            font_size = dialog.font_size_spin.value()
            line_height = dialog.line_height_combo.currentText()
            align = dialog.align_combo.currentData()
            
            h_color = dialog.h_color_btn.color.name()
            quote_color = dialog.quote_color_btn.color.name()
            code_bg = dialog.code_bg_btn.color.name()
            
            css_content = f"""/* Custom PDF Theme Generated visually by PDF Layout & Style Designer */
@page {{
    size: {paper_size};
    margin: {m_top}mm {m_right}mm {m_bottom}mm {m_left}mm;
}}

body {{
    font-family: "{font_family}", "Helvetica Neue", Arial, sans-serif;
    font-size: {font_size}px;
    line-height: {line_height};
    text-align: {align};
    color: #2c3e50;
    background-color: #ffffff;
}}

h1, h2, h3, h4, h5, h6 {{
    color: {h_color};
    font-family: "{font_family}", sans-serif;
    font-weight: bold;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}}

h1 {{
    border-bottom: 2px solid {h_color};
    padding-bottom: 5px;
    font-size: 2em;
}}

h2 {{
    font-size: 1.5em;
}}

blockquote {{
    border-left: 5px solid {quote_color};
    background-color: #fcfcfc;
    padding: 10px 15px;
    margin: 1.5em 0;
    color: #555555;
    font-style: italic;
}}

pre, code {{
    font-family: "Courier New", Courier, monospace;
    font-size: 0.9em;
}}

pre {{
    background-color: {code_bg};
    border: 1px solid #dfe4ea;
    border-radius: 4px;
    padding: 12px;
    overflow-x: auto;
    margin: 1.5em 0;
}}

code {{
    background-color: {code_bg};
    padding: 2px 4px;
    border-radius: 3px;
}}
"""
            os.makedirs("templates", exist_ok=True)
            theme_path = os.path.abspath("templates/custom_theme.css")
            try:
                with open(theme_path, "w", encoding="utf-8") as f:
                    f.write(css_content)
                self.custom_css_input.setText(theme_path)
                self._render_live_preview()
                QMessageBox.information(
                    self, 
                    self.tr_msg("msg_theme_created_title"), 
                    self.tr_msg("msg_theme_created_desc").format(theme_path)
                )
            except Exception as e:
                logger.error("Failed to save custom theme: %s", e)
                QMessageBox.critical(self, "Error", f"Failed to save custom theme:\n{e}")


    # ─── Smart Auto-completion Event Filter ───

    def eventFilter(self, obj, event):
        if obj == self.live_editor and event.type() == QEvent.Type.KeyPress:
            from PyQt6.QtCore import Qt
            key = event.key()
            text = event.text()
            
            pairs = {
                "(": ")",
                "[": "]",
                "{": "}",
                "\"": "\"",
                "'": "'",
                "`": "`",
                "<": ">"
            }
            wrap_pairs = {**pairs, "*": "*", "_": "_"}
            
            cursor = self.live_editor.textCursor()
            has_sel = cursor.hasSelection()
            
            # 1. Backspace deletion of empty pairs
            if key == Qt.Key.Key_Backspace and not has_sel:
                pos = cursor.position()
                full_text = self.live_editor.toPlainText()
                if pos > 0 and pos < len(full_text):
                    left_char = full_text[pos - 1]
                    right_char = full_text[pos]
                    if left_char in pairs and pairs[left_char] == right_char:
                        cursor.deleteChar()
                        cursor.deletePreviousChar()
                        return True

            # 2. Wrapping selection
            if has_sel and text in wrap_pairs:
                selected = cursor.selectedText()
                cursor.insertText(text + selected + wrap_pairs[text])
                return True

            # 3. Autoclosing when typing opening character
            if not has_sel and text in pairs:
                cursor.insertText(text + pairs[text])
                cursor.movePosition(cursor.MoveOperation.PreviousCharacter)
                self.live_editor.setTextCursor(cursor)
                return True
                
            # 4. Overtyping closing character
            if not has_sel and text in [")", "]", "}", "\"", "'", "`", ">"]:
                cursor.movePosition(cursor.MoveOperation.NextCharacter, cursor.MoveMode.KeepAnchor)
                next_char = cursor.selectedText()
                if next_char == text:
                    cursor = self.live_editor.textCursor()
                    cursor.movePosition(cursor.MoveOperation.NextCharacter)
                    self.live_editor.setTextCursor(cursor)
                    return True
                    
        return super().eventFilter(obj, event)

    def show_merge_dialog(self):
        dialog = DocumentBuilderDialog(self, lang=self.current_lang)
        dialog.exec()

    def show_readability_dashboard(self):
        text = self.live_editor.toPlainText()
        dialog = ReadabilityDashboardDialog(text, self, lang=self.current_lang)
        dialog.exec()

    def show_stats_menu(self):
        menu = QMenu(self)
        t = lambda k: TRANSLATIONS[self.current_lang].get(k, k)
        
        act_dashboard = menu.addAction(t('dashboard_title'))
        act_goal = menu.addAction("🎯 " + t('goal_title') + "...")
        
        action = menu.exec(QCursor.pos())
        if action == act_dashboard:
            self.show_readability_dashboard()
        elif action == act_goal:
            self.set_writing_goal()

    def set_writing_goal(self):
        t = lambda k: TRANSLATIONS[self.current_lang].get(k, k)
        val, ok = QInputDialog.getInt(
            self, t('goal_title'), t('goal_prompt'), self.writing_goal, min=0
        )
        if ok:
            self.writing_goal = val
            self.goal_celebrated = False
            self.update_text_statistics()

    def show_snippets_dialog(self):
        dialog = SnippetsDialog(self, lang=self.current_lang)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_markdown = dialog.get_selected_snippet()
            if selected_markdown:
                cursor = self.live_editor.textCursor()
                cursor.insertText(selected_markdown)
                self.live_editor.setFocus()

    def sync_scroll_preview(self, value):
        editor_scroll = self.live_editor.verticalScrollBar()
        max_editor = editor_scroll.maximum()
        if max_editor <= 0:
            return
        percentage = value / max_editor
        
        preview_scroll = self.preview_output.verticalScrollBar()
        max_preview = preview_scroll.maximum()
        preview_scroll.setValue(int(percentage * max_preview))

    def toggle_zen_mode(self):
        self.is_zen_mode = not getattr(self, 'is_zen_mode', False)
        
        self.settings_group.setVisible(not self.is_zen_mode)
        self.history_group.setVisible(not self.is_zen_mode)
        self.log_output.setVisible(not self.is_zen_mode)
        self.tabs.setTabVisible(0, not self.is_zen_mode)
        
        if self.is_zen_mode:
            self.btn_zen.setStyleSheet("""
                QPushButton { background: #e67e22; color: white; border: none; font-weight: bold; padding: 4px 10px; }
            """)
        else:
            self.btn_zen.setStyleSheet("""
                QPushButton { background: #d35400; color: white; border: none; font-weight: bold; padding: 4px 10px; }
                QPushButton:hover { background: #e67e22; }
            """)

    def format_markdown_document(self):
        import re
        scroll_pos = self.live_editor.verticalScrollBar().value()
        
        old_text = self.live_editor.toPlainText()
        lines = old_text.splitlines()
        
        def format_markdown_table(table_lines: list[str]) -> list[str]:
            rows = []
            for line in table_lines:
                stripped = line.strip()
                if stripped.startswith('|'):
                    stripped = stripped[1:]
                if stripped.endswith('|'):
                    stripped = stripped[:-1]
                cols = [c.strip() for c in stripped.split('|')]
                rows.append(cols)
                
            if not rows:
                return table_lines
                
            has_separator = False
            if len(rows) > 1:
                sec_row = rows[1]
                if all(re.match(r'^:?-+:?$', c) for c in sec_row if c):
                    has_separator = True
                    
            col_count = max(len(r) for r in rows)
            col_widths = [0] * col_count
            for r in rows:
                for idx, val in enumerate(r):
                    if idx < len(col_widths):
                        col_widths[idx] = max(col_widths[idx], len(val))
                        
            formatted = []
            for r_idx, r in enumerate(rows):
                fmt_cols = []
                for idx in range(col_count):
                    val = r[idx] if idx < len(r) else ""
                    width = col_widths[idx]
                    
                    if r_idx == 1 and has_separator:
                        col_align = "left"
                        clean_sep = val.strip()
                        if clean_sep.startswith(':') and clean_sep.endswith(':'):
                            col_align = "center"
                        elif clean_sep.endswith(':'):
                            col_align = "right"
                            
                        if col_align == "center":
                            dashed = ":" + "-" * (width) + ":"
                        elif col_align == "right":
                            dashed = "-" * (width + 1) + ":"
                        elif col_align == "left" and clean_sep.startswith(':'):
                            dashed = ":" + "-" * (width + 1)
                        else:
                            dashed = "-" * (width + 2)
                        fmt_cols.append(dashed)
                    else:
                        padded = f" {val.ljust(width)} "
                        fmt_cols.append(padded)
                        
                formatted.append("|" + "|".join(fmt_cols) + "|")
            return formatted

        formatted_lines = []
        in_table = False
        table_buffer = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('|') and '|' in stripped:
                if not in_table:
                    in_table = True
                    table_buffer = [line]
                else:
                    table_buffer.append(line)
            else:
                if in_table:
                    try:
                        formatted_table = format_markdown_table(table_buffer)
                        formatted_lines.extend(formatted_table)
                    except Exception:
                        formatted_lines.extend(table_buffer)
                    in_table = False
                    table_buffer = []
                formatted_lines.append(line.rstrip())
                
        if in_table:
            try:
                formatted_table = format_markdown_table(table_buffer)
                formatted_lines.extend(formatted_table)
            except Exception:
                formatted_lines.extend(table_buffer)

        # Standardize spacing before headings
        idx = 0
        while idx < len(formatted_lines):
            line = formatted_lines[idx]
            if line.strip().startswith('#') and idx > 0:
                if formatted_lines[idx-1].strip() != "":
                    formatted_lines.insert(idx, "")
                    idx += 1
            idx += 1
            
        new_text = "\n".join(formatted_lines)
        
        if new_text != old_text:
            self.live_editor.blockSignals(True)
            self.live_editor.setPlainText(new_text)
            self.live_editor.blockSignals(False)
            self._render_live_preview()
            self.update_text_statistics()
            self.live_editor.verticalScrollBar().setValue(scroll_pos)


# ─── CSS Theme / Document Builder / Readability Utilities ───

def estimate_readability(text: str, lang: str):
    words = [w.strip(",.!?()\"';:") for w in text.split() if w.strip()]
    if not words:
        return 100, "N/A"
        
    import re
    sentences = [s for s in re.split(r'[.!?]+', text) if s.strip()]
    total_words = len(words)
    total_sentences = max(len(sentences), 1)
    
    vowels_ru = set("аоэиуыеёюяаоэиуыеёюя")
    vowels_en = set("aeiouy")
    
    syllables = 0
    for word in words:
        word_lower = word.lower()
        if lang == "ru":
            count = sum(1 for c in word_lower if c in vowels_ru)
        else:
            count = sum(1 for c in word_lower if c in vowels_en)
        syllables += max(count, 1)
        
    if lang == "ru":
        score = 206.835 - 1.3 * (total_words / total_sentences) - 60.1 * (syllables / total_words)
    else:
        score = 206.835 - 1.015 * (total_words / total_sentences) - 84.6 * (syllables / total_words)
        
    score = max(0, min(100, score))
    
    if score >= 70:
        lvl = TRANSLATIONS[lang].get('dashboard_readability_easy', 'Easy')
    elif score >= 40:
        lvl = TRANSLATIONS[lang].get('dashboard_readability_medium', 'Standard')
    else:
        lvl = TRANSLATIONS[lang].get('dashboard_readability_hard', 'Difficult')
        
    return round(score, 1), lvl


from PyQt6.QtWidgets import QListWidget, QFileDialog, QGroupBox
