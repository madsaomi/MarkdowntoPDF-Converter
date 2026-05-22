import re
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor
from PyQt6.QtCore import QRegularExpression

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

        # Define Colors based on theme
        if self.is_dark:
            color_header = "#bb8fce"      # Violet
            color_bold = "#f1c40f"        # Gold
            color_italic = "#82e0aa"      # Pastel Green
            color_code = "#e59866"        # Soft Orange
            color_quote = "#a6acaf"       # Soft Gray
            color_list = "#5dade2"        # Bright Blue
            color_latex = "#48c9b0"       # Turquoise
            color_mermaid = "#f48fb1"     # Soft Pink
            color_link = "#1abc9c"        # Teal
        else:
            color_header = "#8e44ad"      # Deep Violet
            color_bold = "#ba4a00"        # Dark Orange
            color_italic = "#1e8449"      # Emerald Green
            color_code = "#c0392b"        # Brick Red
            color_quote = "#7f8c8d"       # Cool Gray
            color_list = "#2980b9"        # Royal Blue
            color_latex = "#117a65"       # Deep Teal
            color_mermaid = "#c2185b"     # Raspberry
            color_link = "#16a085"        # Teal

        # 1. Headers: # ... -> Bold
        header_format = QTextCharFormat()
        header_format.setFontWeight(QFont.Weight.Bold)
        header_format.setForeground(QColor(color_header))
        self.rules.append((QRegularExpression(r"^#{1,6}\s+.*$"), header_format))

        # 2. Bold: **text** or __text__ -> Bold
        bold_format = QTextCharFormat()
        bold_format.setFontWeight(QFont.Weight.Bold)
        bold_format.setForeground(QColor(color_bold))
        self.rules.append((QRegularExpression(r"\*\*([^*]+)\*\*"), bold_format))
        self.rules.append((QRegularExpression(r"__([^_]+)__"), bold_format))

        # 3. Italic: *text* or _text_ -> Italic
        italic_format = QTextCharFormat()
        italic_format.setFontItalic(True)
        italic_format.setForeground(QColor(color_italic))
        self.rules.append((QRegularExpression(r"\*([^*]+)\*"), italic_format))
        self.rules.append((QRegularExpression(r"_([^_]+)_"), italic_format))

        # 4. Blockquotes: > quote -> Italic
        quote_format = QTextCharFormat()
        quote_format.setForeground(QColor(color_quote))
        quote_format.setFontItalic(True)
        self.rules.append((QRegularExpression(r"^>\s+.*$"), quote_format))

        # 5. Unordered / Ordered lists -> Bold
        list_format = QTextCharFormat()
        list_format.setForeground(QColor(color_list))
        list_format.setFontWeight(QFont.Weight.Bold)
        self.rules.append((QRegularExpression(r"^\s*[-*+]\s+"), list_format))
        self.rules.append((QRegularExpression(r"^\s*\d+\.\s+"), list_format))

        # 6. Links and images: [text](link) or ![text](link) -> Underline
        link_format = QTextCharFormat()
        link_format.setForeground(QColor(color_link))
        link_format.setFontUnderline(True)
        self.rules.append((QRegularExpression(r"!?\[([^\]]+)\]\(([^)]+)\)"), link_format))

        # 7. Inline LaTeX: $E=mc^2$ -> Turquoise
        latex_format = QTextCharFormat()
        latex_format.setForeground(QColor(color_latex))
        self.rules.append((QRegularExpression(r"(?<!\$)\$(?!\s)[^\$\n]+(?<!\s)\$(?!\$)"), latex_format))

        # 8. LaTeX Block: $$ ... $$ -> Turquoise
        latex_block_format = QTextCharFormat()
        latex_block_format.setForeground(QColor(color_latex))
        latex_block_format.setFontWeight(QFont.Weight.Bold)
        self.rules.append((QRegularExpression(r"\$\$.*?\$\$"), latex_block_format))
        self.rules.append((QRegularExpression(r"^\s*\$\$\s*$"), latex_block_format))

        # 9. Mermaid Blocks: ```mermaid ... ``` -> Pink
        mermaid_format = QTextCharFormat()
        mermaid_format.setForeground(QColor(color_mermaid))
        mermaid_format.setFontWeight(QFont.Weight.Bold)
        self.rules.append((QRegularExpression(r"```mermaid.*"), mermaid_format))
        
        # 10. Code blocks and Inline code: `code`
        code_format = QTextCharFormat()
        code_format.setFontFamilies(["monospace", "Courier New"])
        code_format.setForeground(QColor(color_code))
        self.rules.append((QRegularExpression(r"`([^`]+)`"), code_format))
        self.rules.append((QRegularExpression(r"```[a-zA-Z0-9]*"), code_format))

    def highlightBlock(self, text):
        for expression, char_format in self.rules:
            iterator = expression.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, char_format)
