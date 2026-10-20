"""Диалоги экспорта: ``MultiExportDialog``, ``PDFStyleEditorDialog``.

Выделено из ``src/gui/dialogs.py`` (TASK-011/PLAN-011), тела перенесены вербатим.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox,
    QSpinBox, QFormLayout, QDialogButtonBox, QComboBox, QTabWidget,
    QCheckBox, QWidget,
)

from src.gui.translations import TRANSLATIONS
from src.gui.dialogs.common import ColorButton


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
        lay.addRow(t('paper_size'), self.paper_combo)
        
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


