import sys
import os
import re
import logging
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QTextEdit, QProgressBar,
    QMessageBox, QComboBox, QLineEdit, QGroupBox, QGridLayout, QMenu,
    QTabWidget, QTextBrowser, QInputDialog, QListWidgetItem, QListWidget,
    QSpinBox, QFormLayout, QDialog, QDialogButtonBox, QColorDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings, QFileSystemWatcher, QTimer, QEvent, QRegularExpression
from PyQt6.QtGui import QIcon, QAction, QShortcut, QKeySequence, QCursor, QColor

from src.config import AppConfig
from src.gui.ui_layout import setup_ui
from src.__version__ import __version__
from src.gui.translations import TRANSLATIONS
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
from src.gui import editor_commands, file_manager, preview_manager, document_tools
from src.gui.multi_cursor import MultiCursorManager
from src.core.template_vars import process_document_vars
from src.core.plugin_system import load_plugins_from_dir
from src.gui.toast import ToastNotification
from src.gui.about_dialog import AboutDialog
from src.gui.custom_titlebar import CustomTitleBar
from src.gui.ambient_glow import AmbientGlowWidget
from src.gui.window_tools import ToolMethodsMixin

# ──────────────────────── Dark / Light stylesheets ────────────────────────

from src.gui.styles import LIGHT_STYLE, DARK_STYLE

APP_NAME = "MarkdownToPDF_Pro"




# ──────────────────────── Main Window ────────────────────────

class MainWindow(QMainWindow, ToolMethodsMixin):
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

        # Settings persistence
        self.settings = QSettings(AppConfig.APP_NAME, AppConfig.APP_NAME)
        self.current_lang = self.settings.value("language", "ru", str)
        self.export_history = self.settings.value("export_history", [], list)

        # Start Kroki.io connectivity check
        self.kroki_thread = KrokiCheckThread()
        self.kroki_thread.finished.connect(self.on_kroki_check_finished)
        self.kroki_thread.start()

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
        
        # Language menu handled directly in ui_layout.py
        
        self._setup_shortcuts()
        self.load_settings()
        self.load_presets()
        self.preset_combo.currentIndexChanged.connect(self.on_preset_changed)
        
        self.retranslate_ui()

        # Connect search panel actions: см. ui_layout.py (panel_connections)

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
        plugins_dir = os.path.join(AppConfig.base_path(), "plugins")
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
        """Корректное завершение: сохранить состояние и остановить фоновые потоки/таймеры."""
        try:
            self.save_settings()
        except Exception as e:
            logger.warning("Failed to save settings on close: %s", e)

        # 1. Таймеры
        for timer_attr in ('autosave_timer', 'preview_timer'):
            timer = getattr(self, timer_attr, None)
            if timer is not None:
                try:
                    timer.stop()
                except Exception:
                    pass

        # 2. Автосохранение черновика (один раз на выходе)
        try:
            self.autosave_draft()
        except Exception as e:
            logger.warning("Draft autosave on close failed: %s", e)

        # 3. Watcher
        watcher = getattr(self, 'watcher', None)
        if watcher is not None:
            try:
                watcher.removePaths(watcher.files())
            except Exception:
                pass

        # 4. Фоновые потоки: попросить отмену и дождаться завершения
        thread = getattr(self, 'thread', None)
        if thread is not None and thread.isRunning():
            try:
                thread.cancel()
            except Exception:
                pass
            thread.wait(3000)

        kroki_thread = getattr(self, 'kroki_thread', None)
        if kroki_thread is not None and kroki_thread.isRunning():
            kroki_thread.wait(2000)

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
        anim.start()
        self._theme_anim = anim

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
            compress=self.chk_compress.isChecked(),
            watermark_css=self.watermark_css_input.text().strip() if hasattr(self, 'watermark_css_input') else "",
        )


    def append_log(self, text: str):
        self.log_output.append(text)

    def cancel_conversion(self):
        if self.thread is not None and self.thread.isRunning():
            self.thread.cancel()
            self.btn_cancel.setEnabled(False)
            self.append_log(self.tr_msg("log_cancel_req"))

    def update_preview_from_editor(self):
        self._render_live_preview()
        self.update_text_statistics()

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
            
        # Capture current settings (password excluded for security)
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
            except (KeyError, IndexError, AttributeError) as e:
                logger.warning("Translation format error for key '%s': %s", key, e)
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
        
        # Menu Bar (перевод + локализация названий пунктов меню)
        try:
            menubar = self.menuBar()
            menus = [
                ('file_menu', 'menu_file', 'File'),
                ('tools_menu', 'menu_tools', 'Tools'),
                ('lang_menu', 'menu_language', 'Language'),
                ('help_menu', 'menu_help', 'Help'),
            ]
            for attr, key, fallback in menus:
                if hasattr(self, attr):
                    getattr(self, attr).setTitle(t(key) if key in TRANSLATIONS.get(self.current_lang, {}) else fallback)
            # Файловое меню — первый пункт меню-бара (обратная совместимость)
            if menubar.actions():
                menubar.actions()[0].setText(t('menu_file'))
            if hasattr(self, 'recent_menu') and self.recent_menu:
                self.recent_menu.setTitle(t('menu_recent'))
        except Exception as e:
            logger.warning("Menu retranslation failed: %s", e)
        
        # Theme button
        if hasattr(self, 'btn_theme'):
            self.btn_theme.setText(t('btn_theme_light') if self.is_dark else t('btn_theme_dark'))
        
        # Settings dialog labels
        if hasattr(self, 'chk_page_numbers'):
            self.chk_page_numbers.setText(t('chk_page_numbers'))
        if hasattr(self, 'chk_presentation_mode'):
            self.chk_presentation_mode.setText(t('chk_presentation_mode'))
        if hasattr(self, 'chk_compress'):
            self.chk_compress.setText(t('chk_compress'))
        
        if hasattr(self, 'combo_page_format'):
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
        for attr in ['watermark_input', 'footer_input', 'custom_css_input',
                     'pdf_password_input', 'margins_input', 'docx_template_input']:
            if hasattr(self, attr):
                ph_key = f'placeholder_{attr.replace("_input", "")}'
                if ph_key in TRANSLATIONS[self.current_lang]:
                    getattr(self, attr).setPlaceholderText(t(ph_key))
        
        self.live_editor.setPlaceholderText(t('placeholder_editor'))
        
        # Buttons
        for attr in ['btn_select_css', 'btn_select_docx']:
            if hasattr(self, attr):
                getattr(self, attr).setText(t('btn_browse'))
        for attr, key in [('btn_save_preset', 'btn_save_preset'), ('btn_delete_preset', 'btn_delete_preset'),
                          ('btn_select', 'btn_select_files'), ('btn_select_folder', 'btn_select_folder'),
                          ('btn_cancel', 'btn_cancel')]:
            if hasattr(self, attr):
                getattr(self, attr).setText(t(key))
        
        if hasattr(self, 'btn_convert'):
            fmt = self.format_combo.currentText()
            self.btn_convert.setText(f"Convert to {fmt}")
        
        # Search
        if hasattr(self, 'label_search_find'):
            self.label_search_find.setText(t('search_find_lbl'))
        if hasattr(self, 'label_search_replace'):
            self.label_search_replace.setText(t('search_replace_lbl'))
        if hasattr(self, 'btn_search_next'):
            self.btn_search_next.setText(t('btn_find_next'))
        if hasattr(self, 'btn_replace_all'):
            self.btn_replace_all.setText(t('btn_replace_all'))
        if hasattr(self, 'search_regex_checkbox'):
            self.search_regex_checkbox.setText(t('search_regex_lbl'))
        
        # Tooltips for toolbar buttons
        tip_map = {
            'btn_format_bold': 'tip_format_bold', 'btn_format_italic': 'tip_format_italic',
            'btn_format_h1': 'tip_format_h1', 'btn_format_h2': 'tip_format_h2',
            'btn_format_code': 'tip_format_code', 'btn_format_quote': 'tip_format_quote',
            'btn_format_list': 'tip_format_list', 'btn_format_pagebreak': 'tip_format_pagebreak',
        }
        for btn, key in tip_map.items():
            if hasattr(self, btn) and key in TRANSLATIONS.get(self.current_lang, {}):
                getattr(self, btn).setToolTip(t(key))
        
        if hasattr(self, 'btn_print'):
            self.btn_print.setText(t('btn_print'))
        if hasattr(self, 'btn_copy_html'):
            self.btn_copy_html.setText(t('btn_copy_html'))
        
        self.update_text_statistics()
        
        if hasattr(self, 'explorer_group'):
            self.explorer_group.setTitle(t('explorer_title'))
        if hasattr(self, 'explorer_search'):
            self.explorer_search.setPlaceholderText(t('explorer_search_placeholder'))
        
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
            stats_text += f" | 🎯 {pct}% ({word_count}/{self.writing_goal} {t('stats_words').format('').strip()})"
            
            if pct >= 100 and not self.goal_celebrated:
                self.goal_celebrated = True
                QMessageBox.information(
                    self,
                    t('goal_celebrate_title'),
                    t('goal_celebrate_desc').format(self.writing_goal)
                )
            
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
            subprocess.run(["explorer", "/select,", os.path.normpath(filepath)], timeout=10)
        except subprocess.TimeoutExpired:
            logger.warning("Explorer open timed out for %s", filepath)
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
    # ─── Quick Formatting Methods ───

    def _wrap_selection(self, prefix: str, suffix: str):
        editor_commands._wrap_selection(self, prefix, suffix)
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

    def show_snippets_dialog(self):
        document_tools.show_snippets_dialog(self)

    def sync_scroll_preview(self, value):
        preview_manager.sync_scroll_preview(self, value)

    # ─── Toast Notifications ───

    def toast(self, message: str, toast_type: str = "info", duration: int = 3000):
        """Show a modern toast notification."""
        return ToastNotification.show_toast(self, message, toast_type, duration)

