from PyQt6.QtWidgets import QSplashScreen, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QRect
from PyQt6.QtGui import QPixmap, QPainter, QColor, QLinearGradient, QFont, QIcon


class ModernSplashScreen(QSplashScreen):
    """Animated glassmorphism splash screen."""

    def __init__(self, version="1.0.0"):
        # Create splash pixmap
        pixmap = QPixmap(480, 320)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background with gradient
        gradient = QLinearGradient(0, 0, 480, 320)
        gradient.setColorAt(0, QColor(15, 15, 26))
        gradient.setColorAt(0.3, QColor(26, 15, 46))
        gradient.setColorAt(0.6, QColor(15, 26, 46))
        gradient.setColorAt(1, QColor(15, 46, 26))
        painter.fillRect(pixmap.rect(), gradient)

        # Ambient glow orbs
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
        glow1 = QColor(139, 92, 246, 30)
        glow2 = QColor(59, 130, 246, 20)
        glow3 = QColor(6, 182, 212, 25)
        painter.setBrush(glow1)
        painter.drawEllipse(50, 30, 200, 200)
        painter.setBrush(glow2)
        painter.drawEllipse(280, 120, 180, 180)
        painter.setBrush(glow3)
        painter.drawEllipse(100, 180, 160, 160)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        # Glass card
        painter.setBrush(QColor(255, 255, 255, 8))
        painter.setPen(QColor(255, 255, 255, 15))
        painter.drawRoundedRect(40, 40, 400, 240, 16, 16)

        # App icon area (emoji)
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Segoe UI Emoji", 42)
        painter.setFont(font)
        painter.drawText(QRect(180, 60, 120, 70), Qt.AlignmentFlag.AlignCenter, "\U0001F4C4")

        # Title
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Segoe UI", 22, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(QRect(40, 140, 400, 40), Qt.AlignmentFlag.AlignCenter, "Markdown to PDF")

        # Subtitle
        painter.setPen(QColor(160, 160, 200))
        font = QFont("Segoe UI", 12)
        painter.setFont(font)
        painter.drawText(QRect(40, 180, 400, 30), Qt.AlignmentFlag.AlignCenter, "Converter Pro")

        # Version
        painter.setPen(QColor(120, 120, 160))
        font = QFont("Segoe UI", 10)
        painter.setFont(font)
        painter.drawText(QRect(40, 215, 400, 20), Qt.AlignmentFlag.AlignCenter, f"v{version}")

        # Loading dots
        painter.setPen(QColor(139, 92, 246))
        font = QFont("Segoe UI", 10)
        painter.setFont(font)
        painter.drawText(QRect(40, 245, 400, 20), Qt.AlignmentFlag.AlignCenter, "Loading...")

        painter.end()

        super().__init__(pixmap)
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self._dots = 0
        self._dot_timer = QTimer()
        self._dot_timer.timeout.connect(self._animate_dots)
        self._dot_timer.start(400)

    def _animate_dots(self):
        self._dots = (self._dots + 1) % 4
        dots = "." * self._dots
        self.showMessage(f"Loading{dots}", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, QColor(160, 160, 200))

    def finish_with(self, window, delay_ms=1500):
        QTimer.singleShot(delay_ms, lambda: (self._dot_timer.stop(), self.finish(window), window.show()))
