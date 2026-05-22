from enum import Enum
from dataclasses import dataclass

class ExportFormat(str, Enum):
    PDF = "PDF"
    DOCX = "DOCX"
    HTML = "HTML"

class DocTheme(str, Enum):
    MODERN = "theme_modern.css"
    CLASSIC = "theme_classic.css"

class CodeTheme(str, Enum):
    LIGHT = "pygments.css"
    DARK = "pygments_dark.css"

@dataclass
class ConversionOptions:
    doc_theme: str
    code_theme: str
    paper_size: str
    watermark: str
    footer_text: str
    custom_css: str
    export_format: str
    pdf_password: str = ""
    margins: str = ""
    docx_template: str = ""
    page_numbers: bool = False
    page_num_format: str = "simple"
    is_presentation: bool = False
