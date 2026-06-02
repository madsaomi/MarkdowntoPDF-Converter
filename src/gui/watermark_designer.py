from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QSpinBox, QComboBox, QColorDialog, QCheckBox,
    QSlider, QFormLayout, QTextBrowser
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class WatermarkDesignerDialog(QDialog):
    """Visual watermark designer with preview."""

    def __init__(self, parent=None, lang="ru"):
        super().__init__(parent)
        self.lang = lang
        self.setWindowTitle("🎨 Watermark Designer")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.text_input = QLineEdit("DRAFT")
        form.addRow("Text:", self.text_input)

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(5, 50)
        self.opacity_slider.setValue(15)
        self.opacity_label = QLabel("15%")
        self.opacity_slider.valueChanged.connect(lambda v: self.opacity_label.setText(f"{v}%"))
        opacity_row = QHBoxLayout()
        opacity_row.addWidget(self.opacity_slider)
        opacity_row.addWidget(self.opacity_label)
        form.addRow("Opacity:", opacity_row)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(12, 120)
        self.font_size_spin.setValue(48)
        form.addRow("Font Size:", self.font_size_spin)

        self.angle_spin = QSpinBox()
        self.angle_spin.setRange(-180, 180)
        self.angle_spin.setValue(-45)
        form.addRow("Angle:", self.angle_spin)

        self.color_btn = QPushButton("🎨 Choose Color")
        self._color = QColor(200, 200, 200)
        self.color_btn.clicked.connect(self._pick_color)
        form.addRow("Color:", self.color_btn)

        self.chk_diagonal = QCheckBox("Diagonal pattern")
        self.chk_diagonal.setChecked(True)
        form.addRow("", self.chk_diagonal)

        self.chk_tiled = QCheckBox("Tiled (repeat)")
        self.chk_tiled.setChecked(True)
        form.addRow("", self.chk_tiled)

        layout.addLayout(form)

        # Preview
        self.preview = QTextBrowser()
        self.preview.setMaximumHeight(180)
        layout.addWidget(QLabel("Preview:"))
        layout.addWidget(self.preview)

        self.btn_generate = QPushButton("🔄 Update Preview")
        self.btn_generate.clicked.connect(self._update_preview)
        layout.addWidget(self.btn_generate)

        # Result
        self.result_css = ""

        btn_layout = QHBoxLayout()
        self.btn_apply = QPushButton("✅ Apply to Footer")
        self.btn_apply.setStyleSheet("QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #059669,stop:1 #10b981); color: white; font-weight: bold; padding: 8px 16px; border: none; border-radius: 6px; } QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #047857,stop:1 #059669); }")
        self.btn_apply.clicked.connect(self._apply)
        btn_layout.addWidget(self.btn_apply)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.close)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        self._update_preview()

    def _pick_color(self):
        color = QColorDialog.getColor(self._color, self)
        if color.isValid():
            self._color = color
            self.color_btn.setText(f"🎨 {color.name()}")

    def _update_preview(self):
        text = self.text_input.text()
        opacity = self.opacity_slider.value() / 100
        size = self.font_size_spin.value()
        angle = self.angle_spin.value()
        r, g, b = self._color.red(), self._color.green(), self._color.blue()

        self.result_css = f"""
        <div class="watermark" style="
            position: fixed; top: 50%; left: 50%;
            transform: translate(-50%, -50%) rotate({angle}deg);
            font-size: {size}px; color: rgba({r},{g},{b},{opacity});
            font-weight: bold; white-space: nowrap; pointer-events: none;
            z-index: 9999; user-select: none;
        ">{text}</div>
        """

        html = f"""<html><body style="position:relative; min-height:150px; background:#f8f9fa; padding:20px; border-radius:8px;">
        {self.result_css}
        <p style="color:#2c3e50; font-size:14px;">Sample document content goes here. The watermark will appear diagonally across the page.</p>
        <p style="color:#7f8c8d; font-size:12px;">More text to demonstrate the watermark effect...</p>
        </body></html>"""
        self.preview.setHtml(html)

    def _apply(self):
        self._update_preview()
        self.accept()
