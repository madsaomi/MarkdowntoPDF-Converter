from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QRect
from PyQt6.QtGui import QPainter, QColor, QRadialGradient


class AmbientGlowWidget(QWidget):
    """Animated ambient glow orbs behind glass elements."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._offset1 = 0
        self._offset2 = 0
        self._offset3 = 0

        # Animation timer
        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._animate)
        self._timer.start()

    def _animate(self):
        self._offset1 = (self._offset1 + 1) % 360
        self._offset2 = (self._offset2 + 1) % 360
        self._offset3 = (self._offset3 + 1) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        import math

        w, h = self.width(), self.height()

        # Orb 1: purple, slow orbit
        x1 = w * 0.2 + math.sin(math.radians(self._offset1 * 0.5)) * 50
        y1 = h * 0.3 + math.cos(math.radians(self._offset1 * 0.3)) * 30
        grad1 = QRadialGradient(x1, y1, 120)
        grad1.setColorAt(0, QColor(139, 92, 246, 18))
        grad1.setColorAt(1, QColor(139, 92, 246, 0))
        painter.setBrush(grad1)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(x1 - 120), int(y1 - 120), 240, 240)

        # Orb 2: blue, medium orbit
        x2 = w * 0.7 + math.cos(math.radians(self._offset2 * 0.4)) * 40
        y2 = h * 0.5 + math.sin(math.radians(self._offset2 * 0.25)) * 35
        grad2 = QRadialGradient(x2, y2, 100)
        grad2.setColorAt(0, QColor(59, 130, 246, 14))
        grad2.setColorAt(1, QColor(59, 130, 246, 0))
        painter.setBrush(grad2)
        painter.drawEllipse(int(x2 - 100), int(y2 - 100), 200, 200)

        # Orb 3: cyan, fast orbit
        x3 = w * 0.5 + math.sin(math.radians(self._offset3 * 0.6)) * 45
        y3 = h * 0.7 + math.cos(math.radians(self._offset3 * 0.35)) * 25
        grad3 = QRadialGradient(x3, y3, 90)
        grad3.setColorAt(0, QColor(6, 182, 212, 16))
        grad3.setColorAt(1, QColor(6, 182, 212, 0))
        painter.setBrush(grad3)
        painter.drawEllipse(int(x3 - 90), int(y3 - 90), 180, 180)

        painter.end()
