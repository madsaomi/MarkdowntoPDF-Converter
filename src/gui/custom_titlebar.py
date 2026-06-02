from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPainter, QLinearGradient


class CustomTitleBar(QWidget):
    """Modern glassmorphism custom title bar."""

    def __init__(self, parent=None, title="Markdown to PDF Converter Pro"):
        super().__init__(parent)
        self.parent_window = parent
        self._drag_pos = None
        self.setFixedHeight(42)
        self.setObjectName("customTitleBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(8)

        # App icon
        self.icon_label = QLabel("\U0001F4C4")
        self.icon_label.setStyleSheet("font-size: 16px; padding: 0;")
        layout.addWidget(self.icon_label)

        # Title
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("""
            color: #e2e8f0;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 0.3px;
        """)
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Window control buttons
        btn_style = """
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
                color: #94a3b8;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.08);
                color: #e2e8f0;
            }
        """
        active_style = """
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
                color: #94a3b8;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.08);
                color: #e2e8f0;
            }
        """
        close_style = """
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
                color: #94a3b8;
            }
            QPushButton:hover {
                background: #dc2626;
                color: white;
            }
        """

        self.btn_minimize = QPushButton("\u2013")
        self.btn_minimize.setFixedSize(32, 28)
        self.btn_minimize.setStyleSheet(btn_style)
        self.btn_minimize.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_minimize.clicked.connect(self._minimize)

        self.btn_maximize = QPushButton("\u25A1")
        self.btn_maximize.setFixedSize(32, 28)
        self.btn_maximize.setStyleSheet(btn_style)
        self.btn_maximize.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_maximize.clicked.connect(self._maximize)

        self.btn_close = QPushButton("\u2715")
        self.btn_close.setFixedSize(32, 28)
        self.btn_close.setStyleSheet(close_style)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self._close)

        layout.addWidget(self.btn_minimize)
        layout.addWidget(self.btn_maximize)
        layout.addWidget(self.btn_close)

    def _minimize(self):
        if self.parent_window:
            self.parent_window.showMinimized()

    def _maximize(self):
        if self.parent_window:
            if self.parent_window.isMaximized():
                self.parent_window.showNormal()
                self.btn_maximize.setText("\u25A1")
            else:
                self.parent_window.showMaximized()
                self.btn_maximize.setText("\u29C9")

    def _close(self):
        if self.parent_window:
            self.parent_window.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.parent_window.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event):
        self._maximize()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor(15, 15, 26, 200))
        gradient.setColorAt(0.5, QColor(20, 20, 40, 200))
        gradient.setColorAt(1, QColor(15, 15, 26, 200))
        painter.fillRect(self.rect(), gradient)
        painter.setPen(QColor(255, 255, 255, 10))
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        painter.end()
