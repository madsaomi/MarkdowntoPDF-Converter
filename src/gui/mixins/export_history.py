"""История экспорта: список последних выгруженных файлов и его UI."""

import os
import logging

from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout, QPushButton, QMessageBox
from PyQt6.QtCore import Qt

from src.gui.translations import TRANSLATIONS

logger = logging.getLogger("MarkdownToPDF.export_history")


class ExportHistoryMixin:
    """Методы ``MainWindow`` для журнала экспорта.

    Перенесено из ``src/gui/main_window.py`` (группа A плана PLAN-010).
    Требует от хоста: ``export_history`` (list), ``settings``,
    ``history_layout``, ``current_lang``, ``tr_msg``.
    """

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
