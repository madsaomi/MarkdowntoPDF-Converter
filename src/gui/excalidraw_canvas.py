import json
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QSpinBox, QColorDialog, QTextBrowser, QFileDialog,
    QMessageBox, QWidget
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QPainterPath, QMouseEvent


class ExcalidrawCanvas(QWidget):
    """Simple drawing canvas for creating diagrams."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 400)
        self.setMouseTracking(True)
        self._drawing = False
        self._strokes: list[list[QPoint]] = []
        self._current_stroke: list[QPoint] = []
        self._pen_color = QColor("#2c3e50")
        self._pen_width = 3
        self._tool = "pen"  # pen, line, rect, circle, eraser
        self._start_point = None
        self._shapes: list[dict] = []
        self.setStyleSheet("background-color: rgba(30, 41, 59, 0.85); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px;")

    def set_tool(self, tool: str):
        self._tool = tool

    def set_color(self, color: QColor):
        self._pen_color = color

    def set_width(self, width: int):
        self._pen_width = width

    def clear_all(self):
        self._strokes.clear()
        self._shapes.clear()
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drawing = True
            self._start_point = event.pos()
            if self._tool in ("pen", "eraser"):
                self._current_stroke = [event.pos()]

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drawing:
            if self._tool in ("pen", "eraser"):
                self._current_stroke.append(event.pos())
                self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._drawing:
            end = event.pos()
            if self._tool == "pen":
                self._strokes.append(list(self._current_stroke))
            elif self._tool == "eraser":
                self._strokes.append(list(self._current_stroke))
            elif self._tool == "line":
                self._shapes.append({"type": "line", "start": self._start_point, "end": end, "color": self._pen_color.name(), "width": self._pen_width})
            elif self._tool == "rect":
                self._shapes.append({"type": "rect", "start": self._start_point, "end": end, "color": self._pen_color.name(), "width": self._pen_width})
            elif self._tool == "circle":
                self._shapes.append({"type": "circle", "start": self._start_point, "end": end, "color": self._pen_color.name(), "width": self._pen_width})
            self._drawing = False
            self._current_stroke = []
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("white"))

        # Draw completed strokes
        for stroke in self._strokes:
            if len(stroke) < 2:
                continue
            is_eraser = self._tool == "eraser"
            pen = QPen(QColor("white") if is_eraser else self._pen_color, self._pen_width if not is_eraser else 10)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            path = QPainterPath()
            path.moveTo(stroke[0])
            for pt in stroke[1:]:
                path.lineTo(pt)
            painter.drawPath(path)

        # Draw current stroke
        if self._current_stroke and len(self._current_stroke) >= 2:
            pen = QPen(self._pen_color, self._pen_width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            path = QPainterPath()
            path.moveTo(self._current_stroke[0])
            for pt in self._current_stroke[1:]:
                path.lineTo(pt)
            painter.drawPath(path)

        # Draw shapes
        for shape in self._shapes:
            pen = QPen(QColor(shape["color"]), shape["width"])
            painter.setPen(pen)
            s, e = shape["start"], shape["end"]
            if shape["type"] == "line":
                painter.drawLine(s, e)
            elif shape["type"] == "rect":
                painter.drawRect(min(s.x(), e.x()), min(s.y(), e.y()), abs(e.x() - s.x()), abs(e.y() - s.y()))
            elif shape["type"] == "circle":
                painter.drawEllipse(min(s.x(), e.x()), min(s.y(), e.y()), abs(e.x() - s.x()), abs(e.y() - s.y()))

        painter.end()

    def to_svg(self) -> str:
        """Export drawing as SVG."""
        w, h = self.width(), self.height()
        svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">']
        svg.append(f'<rect width="{w}" height="{h}" fill="white"/>')

        for stroke in self._strokes:
            if len(stroke) < 2:
                continue
            points = " ".join(f"{p.x()},{p.y()}" for p in stroke)
            svg.append(f'<polyline points="{points}" fill="none" stroke="#2c3e50" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')

        for shape in self._shapes:
            s, e = shape["start"], shape["end"]
            c = shape["color"]
            w = shape["width"]
            if shape["type"] == "line":
                svg.append(f'<line x1="{s.x()}" y1="{s.y()}" x2="{e.x()}" y2="{e.y()}" stroke="{c}" stroke-width="{w}"/>')
            elif shape["type"] == "rect":
                x, y = min(s.x(), e.x()), min(s.y(), e.y())
                svg.append(f'<rect x="{x}" y="{y}" width="{abs(e.x()-s.x())}" height="{abs(e.y()-s.y())}" fill="none" stroke="{c}" stroke-width="{w}"/>')
            elif shape["type"] == "circle":
                cx, cy = (s.x()+e.x())//2, (s.y()+e.y())//2
                rx, ry = abs(e.x()-s.x())//2, abs(e.y()-s.y())//2
                svg.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="{c}" stroke-width="{w}"/>')

        svg.append("</svg>")
        return "\n".join(svg)

    def to_dict(self) -> dict:
        """Export as JSON-serializable dict."""
        return {
            "strokes": [[{"x": p.x(), "y": p.y()} for p in s] for s in self._strokes],
            "shapes": [
                {**s, "start": {"x": s["start"].x(), "y": s["start"].y()}, "end": {"x": s["end"].x(), "y": s["end"].y()}}
                for s in self._shapes
            ],
        }


class ExcalidrawDialog(QDialog):
    """Dialog wrapping the Excalidraw canvas."""

    def __init__(self, parent=None, lang="ru"):
        super().__init__(parent)
        self.lang = lang
        self.setWindowTitle("🎨 Excalidraw Diagram")
        self.setMinimumSize(700, 520)

        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()

        self.tool_combo = QComboBox()
        self.tool_combo.addItems(["Pen", "Line", "Rectangle", "Circle", "Eraser"])
        self.tool_combo.currentTextChanged.connect(lambda t: self.canvas.set_tool(t.lower()))
        toolbar.addWidget(QLabel("Tool:"))
        toolbar.addWidget(self.tool_combo)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 20)
        self.width_spin.setValue(3)
        self.width_spin.valueChanged.connect(self.canvas.set_width)
        toolbar.addWidget(QLabel("Width:"))
        toolbar.addWidget(self.width_spin)

        self.btn_color = QPushButton("🎨 Color")
        self.btn_color.clicked.connect(self._pick_color)
        toolbar.addWidget(self.btn_color)

        self.btn_clear = QPushButton("🗑 Clear")
        self.btn_clear.clicked.connect(self.canvas.clear_all)
        toolbar.addWidget(self.btn_clear)

        toolbar.addStretch()

        self.btn_export_svg = QPushButton("💾 SVG")
        self.btn_export_svg.clicked.connect(self._export_svg)
        toolbar.addWidget(self.btn_export_svg)

        self.btn_insert = QPushButton("📋 Insert as Markdown")
        self.btn_insert.clicked.connect(self._insert_markdown)
        toolbar.addWidget(self.btn_insert)

        layout.addLayout(toolbar)

        # Canvas
        self.canvas = ExcalidrawCanvas()
        layout.addWidget(self.canvas)

        # Close
        btn_row = QHBoxLayout()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        self.selected_markdown = ""

    def _pick_color(self):
        color = QColorDialog.getColor(self.canvas._pen_color, self)
        if color.isValid():
            self.canvas.set_color(color)

    def _export_svg(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export SVG", "", "SVG (*.svg)")
        if path:
            svg = self.canvas.to_svg()
            with open(path, "w", encoding="utf-8") as f:
                f.write(svg)

    def _insert_markdown(self):
        svg = self.canvas.to_svg()
        self.selected_markdown = f"\n```diagram\n{svg}\n```\n"
        self.accept()
