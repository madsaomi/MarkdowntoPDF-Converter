import re
import functools
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor
from PyQt6.QtCore import QRegularExpression


@functools.lru_cache(maxsize=20)
def _compile_regex(pattern: str) -> QRegularExpression:
    return QRegularExpression(pattern)


class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dark = False
        self.rules = []
        self._generate_rules()

    def set_theme(self, is_dark: bool):
        self.is_dark = is_dark
        self._generate_rules()
        self.rehighlight()

    def _generate_rules(self):
        self.rules = []

        if self.is_dark:
            color_header = "#bb8fce"
            color_bold = "#f1c40f"
            color_italic = "#82e0aa"
            color_code = "#e59866"
            color_quote = "#a6acaf"
            color_list = "#5dade2"
            color_latex = "#48c9b0"
            color_mermaid = "#f48fb1"
            color_link = "#1abc9c"
        else:
            color_header = "#8e44ad"
            color_bold = "#ba4a00"
            color_italic = "#1e8449"
            color_code = "#c0392b"
            color_quote = "#7f8c8d"
            color_list = "#2980b9"
            color_latex = "#117a65"
            color_mermaid = "#c2185b"
            color_link = "#16a085"

        def _fmt(color, bold=False, italic=False, underline=False, mono=False):
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(QFont.Weight.Bold)
            if italic:
                f.setFontItalic(True)
            if underline:
                f.setFontUnderline(True)
            if mono:
                f.setFontFamilies(["monospace", "Courier New"])
            return f

        self.rules = [
            (_compile_regex(r"^#{1,6}\s+.*$"), _fmt(color_header, bold=True)),
            (_compile_regex(r"\*\*([^*]+)\*\*"), _fmt(color_bold, bold=True)),
            (_compile_regex(r"__([^_]+)__"), _fmt(color_bold, bold=True)),
            (_compile_regex(r"\*([^*]+)\*"), _fmt(color_italic, italic=True)),
            (_compile_regex(r"_([^_]+)_"), _fmt(color_italic, italic=True)),
            (_compile_regex(r"^>\s+.*$"), _fmt(color_quote, italic=True)),
            (_compile_regex(r"^\s*[-*+]\s+"), _fmt(color_list, bold=True)),
            (_compile_regex(r"^\s*\d+\.\s+"), _fmt(color_list, bold=True)),
            (_compile_regex(r"!?\[([^\]]+)\]\(([^)]+)\)"), _fmt(color_link, underline=True)),
            (_compile_regex(r"(?<!\$)\$(?!\s)[^\$\n]+(?<!\s)\$(?!\$)"), _fmt(color_latex)),
            (_compile_regex(r"\$\$.*?\$\$"), _fmt(color_latex, bold=True)),
            (_compile_regex(r"^\s*\$\$\s*$"), _fmt(color_latex, bold=True)),
            (_compile_regex(r"```mermaid.*"), _fmt(color_mermaid, bold=True)),
            (_compile_regex(r"`([^`]+)`"), _fmt(color_code, mono=True)),
            (_compile_regex(r"```[a-zA-Z0-9]*"), _fmt(color_code, mono=True)),
        ]

    def highlightBlock(self, text):
        for expression, char_format in self.rules:
            iterator = expression.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, char_format)
