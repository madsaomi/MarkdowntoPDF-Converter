"""Общие виджеты и диалоги: ``ColorButton``, ``ShortcutsDialog``.

Выделено из ``src/gui/dialogs.py`` (TASK-011/PLAN-011), тела перенесены вербатим.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QLabel, QTextBrowser, QColorDialog,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class ColorButton(QPushButton):
    def __init__(self, color_hex="#ffffff", parent=None):
        super().__init__(parent)
        self.color = QColor(color_hex)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_style()
        self.clicked.connect(self.choose_color)

    def update_style(self):
        self.setStyleSheet(f"background-color: {self.color.name()}; border: 1px solid rgba(255,255,255,0.15); border-radius: 6px; height: 24px;")

    def choose_color(self):
        dlg = QColorDialog(self.color, self)
        if dlg.exec() == QColorDialog.DialogCode.Accepted:
            self.color = dlg.selectedColor()
            self.update_style()


class ShortcutsDialog(QDialog):
    """Glassmorphism keyboard shortcuts overlay."""

    SHORTCUTS = [
        ("Ctrl+N", "Новый файл / New file"),
        ("Ctrl+O", "Открыть файл / Open file"),
        ("Ctrl+S", "Сохранить / Save"),
        ("Ctrl+Shift+S", "Сохранить как / Save as"),
        ("Ctrl+Z", "Отменить / Undo"),
        ("Ctrl+Y", "Повторить / Redo"),
        ("Ctrl+F", "Поиск и замена / Search & Replace"),
        ("Ctrl+H", "Замена / Replace"),
        ("Ctrl+P", "Печать / Print"),
        ("Ctrl+B", "Жирный / Bold"),
        ("Ctrl+I", "Курсив / Italic"),
        ("Ctrl+K", "Ссылка / Link"),
        ("Ctrl+Shift+K", "Код / Code"),
        ("Ctrl+Shift+Q", "Цитата / Quote"),
        ("Ctrl+Shift+L", "Список / List"),
        ("Ctrl+Shift+X", "Зачёркнутый / Strikethrough"),
        ("Ctrl+E", "Эмодзи / Emoji"),
        ("Ctrl+=", "Zoom in"),
        ("Ctrl+-", "Zoom out"),
        ("Ctrl+0", "Сброс зума / Reset zoom"),
        ("Ctrl+M", "Мерmaid / Mermaid"),
        ("Ctrl+D", "Диаграмма / Diagram"),
        ("Ctrl+Tab", "Следующая вкладка / Next tab"),
        ("F11", "Zen режим / Zen mode"),
        ("Ctrl+Shift+F", "Фокус / Focus mode"),
    ]

    def __init__(self, parent=None, lang="ru"):
        super().__init__(parent)
        self.setWindowTitle("⌨️ Shortcuts" if lang == "en" else "⌨️ Горячие клавиши")
        self.setMinimumSize(520, 480)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("⌨️ Горячие клавиши" if lang == "ru" else "⌨️ Keyboard Shortcuts")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #e2e8f0; border: none;")
        layout.addWidget(title)

        html_parts = ['<table style="width:100%; border-collapse:collapse; font-size:13px;">']
        for i, (key, desc) in enumerate(self.SHORTCUTS):
            bg = "rgba(51, 65, 85, 0.3)" if i % 2 == 0 else "transparent"
            html_parts.append(
                f'<tr style="background:{bg};">'
                f'<td style="padding:8px 12px; border-bottom:1px solid rgba(255,255,255,0.05);">'
                f'<kbd style="background:rgba(99,102,241,0.2); color:#a5b4fc; padding:3px 8px; '
                f'border-radius:4px; font-family:monospace; font-size:12px;">{key}</kbd></td>'
                f'<td style="padding:8px 12px; color:#cbd5e1; border-bottom:1px solid rgba(255,255,255,0.05);">{desc}</td>'
                f'</tr>'
            )
        html_parts.append('</table>')

        browser = QTextBrowser()
        browser.setHtml(''.join(html_parts))
        browser.setStyleSheet("""
            QTextBrowser { background: transparent; border: none; color: #e2e8f0; }
        """)
        layout.addWidget(browser)

        btn_close = QPushButton("Закрыть" if lang == "ru" else "Close")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton { background: rgba(99, 102, 241, 0.5); color: white; padding: 8px 20px;
                          border: none; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background: rgba(99, 102, 241, 0.7); }
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)


