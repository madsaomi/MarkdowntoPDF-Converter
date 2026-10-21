from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QStackedWidget, QWidget, QFrame
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor


class WelcomeTourDialog(QDialog):
    """Interactive welcome tour with step-by-step feature highlights."""

    STEPS = [
        {
            "icon": "\U0001F4C4",
            "title": "Welcome to Markdown to PDF Converter Pro",
            "desc": "A powerful tool to convert Markdown to professional documents.\nLet's explore what you can do!",
            "color": "#8b5cf6",
        },
        {
            "icon": "\u2728",
            "title": "Live Editor with Preview",
            "desc": "Write Markdown on the left, see the rendered preview on the right.\nReal-time updates as you type.",
            "color": "#3b82f6",
        },
        {
            "icon": "\u26A1",
            "title": "Multi-Format Export",
            "desc": "Export to PDF, DOCX, HTML, EPUB, PNG, JPG, PPTX, or Reveal.js slides.\nOne click to convert.",
            "color": "#10b981",
        },
        {
            "icon": "\U0001F3A8",
            "title": "59+ Built-in Tools",
            "desc": "LaTeX math, Mermaid diagrams, OCR, flashcards,\nquiz generator, citation manager, and much more.",
            "color": "#f59e0b",
        },
        {
            "icon": "\U0001F319",
            "title": "Dark & Light Themes",
            "desc": "Beautiful glassmorphism design with dark and light modes.\nToggle with the Theme button or Ctrl+D.",
            "color": "#ec4899",
        },
        {
            "icon": "\U0001F680",
            "title": "Keyboard Shortcuts",
            "desc": "Ctrl+B bold, Ctrl+I italic, Ctrl+F find, Ctrl+D theme,\nCtrl+Space snippets, F11 focus mode. And many more!",
            "color": "#06b6d4",
        },
    ]

    def __init__(self, parent=None, lang="ru"):
        super().__init__(parent)
        self.lang = lang
        self.setWindowTitle("Welcome Tour" if lang == "en" else "Тур")
        self.setFixedSize(520, 400)
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Card
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(15, 15, 26, 0.97), stop:1 rgba(26, 20, 50, 0.97));
                border: 1px solid rgba(139, 92, 246, 0.2);
                border-radius: 16px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 30, 36, 24)
        card_layout.setSpacing(16)

        # Stacked widget for steps
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent; border: none;")

        for step in self.STEPS:
            page = QWidget()
            page.setStyleSheet("background: transparent; border: none;")
            page_layout = QVBoxLayout(page)
            page_layout.setContentsMargins(0, 0, 0, 0)
            page_layout.setSpacing(12)

            icon = QLabel(step["icon"])
            icon.setStyleSheet(f"font-size: 42px; color: {step['color']}; background: transparent; border: none;")
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            page_layout.addWidget(icon)

            title = QLabel(step["title"])
            title.setStyleSheet("color: #e2e8f0; font-size: 18px; font-weight: bold; background: transparent; border: none;")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title.setWordWrap(True)
            page_layout.addWidget(title)

            desc = QLabel(step["desc"])
            desc.setStyleSheet("color: #a0a0c0; font-size: 13px; line-height: 1.5; background: transparent; border: none;")
            desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
            desc.setWordWrap(True)
            page_layout.addWidget(desc)

            page_layout.addStretch()
            self.stack.addWidget(page)

        card_layout.addWidget(self.stack)

        # Step indicator dots
        dots_layout = QHBoxLayout()
        dots_layout.setSpacing(8)
        self.dots = []
        for i in range(len(self.STEPS)):
            dot = QLabel("\u25CF")
            dot.setStyleSheet(f"color: {'#8b5cf6' if i == 0 else '#4a4a6a'}; font-size: 10px; background: transparent; border: none;")
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.dots.append(dot)
            dots_layout.addWidget(dot)
        dots_layout.addStretch()
        card_layout.addLayout(dots_layout)

        # Navigation
        nav_layout = QHBoxLayout()

        self.btn_prev = QPushButton("\u2190 Back" if lang == "en" else "\u2190 Назад")
        self.btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prev.setFixedWidth(100)
        self.btn_prev.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.06); color: #94a3b8; border: 1px solid rgba(255,255,255,0.08);
                font-weight: 500; padding: 8px 14px; border-radius: 8px; font-size: 12px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.1); color: #e2e8f0; }
        """)
        self.btn_prev.clicked.connect(self._prev)
        nav_layout.addWidget(self.btn_prev)

        nav_layout.addStretch()

        self.btn_next = QPushButton("Next \u2192" if lang == "en" else "Далее \u2192")
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.setFixedWidth(100)
        self.btn_next.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #a78bfa);
                color: white; border: none; font-weight: 600; padding: 8px 14px;
                border-radius: 8px; font-size: 12px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6d28d9, stop:1 #7c3aed); }
        """)
        self.btn_next.clicked.connect(self._next)
        nav_layout.addWidget(self.btn_next)

        self.btn_skip = QPushButton("Skip" if lang == "en" else "Пропустить")
        self.btn_skip.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_skip.setStyleSheet("""
            QPushButton { background: transparent; color: #64748b; border: none; font-size: 11px; }
            QPushButton:hover { color: #94a3b8; }
        """)
        self.btn_skip.clicked.connect(self.close)
        nav_layout.addWidget(self.btn_skip)

        card_layout.addLayout(nav_layout)
        layout.addWidget(card)

        self._current = 0
        self._update_ui()

    def _update_ui(self):
        self.stack.setCurrentIndex(self._current)
        for i, dot in enumerate(self.dots):
            color = "#8b5cf6" if i == self._current else "#4a4a6a"
            dot.setStyleSheet(f"color: {color}; font-size: 10px; background: transparent; border: none;")
        self.btn_prev.setVisible(self._current > 0)
        is_last = self._current == len(self.STEPS) - 1
        self.btn_next.setText("Start!" if self.lang == "en" and is_last else ("Начать!" if is_last else ("Next \u2192" if self.lang == "en" else "Далее \u2192")))
        self.btn_skip.setVisible(not is_last)

    def _next(self):
        if self._current < len(self.STEPS) - 1:
            self._current += 1
            self._update_ui()
        else:
            self.accept()

    def _prev(self):
        if self._current > 0:
            self._current -= 1
            self._update_ui()
