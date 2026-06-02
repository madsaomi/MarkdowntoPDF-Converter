from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QColor, QFont


class ToastNotification(QWidget):
    """Modern toast notification that slides in from bottom-right."""

    COLORS = {
        "success": ("#059669", "#10b981", "\u2705"),
        "error": ("#dc2626", "#ef4444", "\u274C"),
        "warning": ("#d97706", "#f59e0b", "\u26A0\uFE0F"),
        "info": ("#2563eb", "#3b82f6", "\u2139\uFE0F"),
    }

    def __init__(self, message: str, toast_type: str = "info", duration: int = 3000, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(360)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        bg_color, accent_color, icon = self.COLORS.get(toast_type, self.COLORS["info"])

        # Glass card
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(30, 30, 50, 0.92);
                border: 1px solid {accent_color}33;
                border-left: 3px solid {accent_color};
                border-radius: 12px;
            }}
        """)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(14, 10, 14, 10)
        card_layout.setSpacing(10)

        # Icon
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 18px; background: transparent; border: none;")
        card_layout.addWidget(icon_lbl)

        # Message
        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet(f"""
            color: #e2e8f0;
            font-size: 13px;
            font-weight: 500;
            background: transparent;
            border: none;
        """)
        card_layout.addWidget(msg_lbl, stretch=1)

        # Close button
        close_btn = QPushButton("\u2715")
        close_btn.setFixedSize(20, 20)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent; border: none; color: #94a3b8;
                font-size: 11px; border-radius: 10px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.1); color: #e2e8f0; }
        """)
        close_btn.clicked.connect(self._close)
        card_layout.addWidget(close_btn)

        layout.addWidget(card)

        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 60))
        card.setGraphicsEffect(shadow)

        # Auto-close
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._close)
        self._timer.start(duration)

        self._anim = None

    def show_at(self, x: int, y: int):
        self.move(x, y)
        self.setWindowOpacity(0.0)
        self.show()
        self._slide_in()
        self._fade_in()

    def _fade_in(self):
        self._fade = QPropertyAnimation(self, b"windowOpacity")
        self._fade.setDuration(300)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade.start()

    def _slide_in(self):
        start_pos = QPoint(self.x() + 50, self.y())
        end_pos = QPoint(self.x(), self.y())
        self._anim = QPropertyAnimation(self, b"pos")
        self._anim.setDuration(300)
        self._anim.setStartValue(start_pos)
        self._anim.setEndValue(end_pos)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

    def _close(self):
        self._fade_out = QPropertyAnimation(self, b"windowOpacity")
        self._fade_out.setDuration(200)
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)
        self._fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self._fade_out.finished.connect(self.deleteLater)
        self._fade_out.start()

    @staticmethod
    def show_toast(parent, message: str, toast_type: str = "info", duration: int = 3000):
        """Show a toast notification relative to parent window."""
        toast = ToastNotification(message, toast_type, duration, parent)
        x = parent.x() + parent.width() - 380
        y = parent.y() + parent.height() - 80
        toast.show_at(x, y)
        return toast
