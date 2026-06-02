from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextBrowser, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPainter, QLinearGradient


class AboutDialog(QDialog):
    """Modern glassmorphism About dialog."""

    def __init__(self, parent=None, version="1.0.0", lang="ru"):
        super().__init__(parent)
        self.lang = lang
        self.setWindowTitle("About" if lang == "en" else "О программе")
        self.setFixedSize(480, 520)
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Main card
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(15, 15, 26, 0.95), stop:1 rgba(26, 20, 50, 0.95));
                border: 1px solid rgba(139, 92, 246, 0.2);
                border-radius: 16px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 24)
        card_layout.setSpacing(16)

        # Icon
        icon = QLabel("\U0001F4C4")
        icon.setStyleSheet("font-size: 48px; background: transparent; border: none;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(icon)

        # Title
        title = QLabel("Markdown to PDF Converter Pro")
        title.setStyleSheet("color: #e2e8f0; font-size: 20px; font-weight: bold; background: transparent; border: none;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)

        # Version
        ver = QLabel(f"Version {version}")
        ver.setStyleSheet("color: #8b5cf6; font-size: 13px; font-weight: 600; background: transparent; border: none;")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(ver)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: rgba(139, 92, 246, 0.2); max-height: 1px; border: none;")
        card_layout.addWidget(sep)

        # Description
        desc = QLabel(
            "A modern Markdown converter with 69+ features:\n"
            "PDF, DOCX, HTML, EPUB, PNG, JPG, PPTX export.\n"
            "Live preview, code highlighting, LaTeX math,\n"
            "Mermaid diagrams, wikilinks, graph view,\n"
            "and much more." if lang == "en" else
            "Современный конвертер Markdown с 69+ функциями:\n"
            "Экспорт в PDF, DOCX, HTML, EPUB, PNG, JPG, PPTX.\n"
            "Живой превью, подсветка кода, LaTeX математика,\n"
            "диаграммы Mermaid, wikilinks, graph view,\n"
            "и многое другое."
        )
        desc.setStyleSheet("color: #a0a0c0; font-size: 12px; line-height: 1.6; background: transparent; border: none;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        card_layout.addWidget(desc)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("background: rgba(139, 92, 246, 0.2); max-height: 1px; border: none;")
        card_layout.addWidget(sep2)

        # Features count
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(24)

        for count, label in [("69+", "Features"), ("8", "Export Formats"), ("59+", "Tools")]:
            col = QVBoxLayout()
            col.setSpacing(2)
            num = QLabel(count)
            num.setStyleSheet("color: #8b5cf6; font-size: 22px; font-weight: bold; background: transparent; border: none;")
            num.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(num)
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #64748b; font-size: 11px; background: transparent; border: none;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(lbl)
            stats_layout.addLayout(col)

        card_layout.addLayout(stats_layout)

        # Links
        links_layout = QHBoxLayout()
        links_layout.setSpacing(12)

        for url, text in [
            ("https://github.com", "GitHub"),
            ("https://docs.python.org", "Docs"),
        ]:
            link = QLabel(f'<a href="{url}" style="color: #8b5cf6; text-decoration: none; font-size: 12px;">{text}</a>')
            link.setOpenExternalLinks(True)
            link.setStyleSheet("background: transparent; border: none;")
            links_layout.addWidget(link)

        links_layout.addStretch()
        card_layout.addLayout(links_layout)

        # Close button
        btn_close = QPushButton("Close" if lang == "en" else "Закрыть")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setFixedWidth(120)
        btn_close.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #a78bfa);
                color: white; border: none; font-weight: 600; padding: 8px 16px;
                border-radius: 10px; font-size: 13px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6d28d9, stop:1 #7c3aed); }
        """)
        btn_close.clicked.connect(self.close)
        card_layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(card)
