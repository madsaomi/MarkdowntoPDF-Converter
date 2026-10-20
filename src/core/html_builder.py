"""Единый билдер HTML для превью и экспорта.

Использует тот же Jinja2-шаблон, что и PDFRenderer, чтобы превью
максимально совпадало с экспортом. Функция возвращает готовый HTML.
"""

import os
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from src.config import AppConfig


class HtmlBuilder:
    def __init__(self, template_dir: Optional[str] = None):
        self.template_dir = template_dir or AppConfig.template_dir()
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        self.template = self.env.get_template("base.html")

    def build_html(
        self,
        html_content: str,
        metadata: Optional[dict] = None,
        doc_theme: str = "theme_modern.css",
        code_theme: str = "pygments.css",
        paper_size: str = "A4",
        watermark: str = "",
        footer_text: str = "",
        input_filepath: Optional[str] = None,
        custom_css_path: str = "",
        margins: str = "",
        page_numbers: bool = False,
        page_num_format: str = "simple",
        lang: str = "ru",
        word_count: int = 0,
        watermark_css: str = "",
    ) -> str:
        metadata = metadata or {}
        renderer = None
        try:
            from src.core.renderer import PDFRenderer
            renderer = PDFRenderer(self.template_dir)
            return renderer.render_html(
                html_content,
                metadata,
                doc_theme=doc_theme,
                code_theme=code_theme,
                paper_size=paper_size,
                watermark=watermark,
                footer_text=footer_text,
                input_filepath=input_filepath,
                custom_css_path=custom_css_path,
                margins=margins,
                page_numbers=page_numbers,
                page_num_format=page_num_format,
                lang=lang,
                word_count=word_count,
                watermark_css=watermark_css,
            )
        except Exception:
            # Fallback: минимальный рендер без полного окружения
            try:
                doc_theme_css = ""
                code_theme_css = ""
                for name in [doc_theme, code_theme]:
                    if not name:
                        continue
                    p = os.path.join(self.template_dir, "css", name)
                    if os.path.exists(p):
                        with open(p, "r", encoding="utf-8") as f:
                            if name == doc_theme:
                                doc_theme_css = f.read()
                            else:
                                code_theme_css = f.read()
                custom_css = ""
                if custom_css_path and os.path.exists(custom_css_path):
                    with open(custom_css_path, "r", encoding="utf-8") as f:
                        custom_css = f.read()
                tr_page = "Страница" if lang == "ru" else "Page"
                tr_of = "из" if lang == "ru" else "of"
                return self.template.render(
                    content=html_content,
                    meta=metadata,
                    doc_theme_css=doc_theme_css,
                    code_theme_css=code_theme_css,
                    custom_css=custom_css,
                    paper_size=paper_size,
                    watermark=watermark,
                    footer_text=footer_text,
                    page_numbers=page_numbers,
                    page_num_format=page_num_format,
                    tr_page=tr_page,
                    tr_of=tr_of,
                    lang=lang,
                    word_count=word_count,
                    watermark_css=watermark_css,
                )
            except Exception:
                return html_content


_builder = None


def get_html_builder() -> HtmlBuilder:
    global _builder
    if _builder is None:
        _builder = HtmlBuilder()
    return _builder


def build_html_for_preview_and_export(html_content: str, **kwargs) -> str:
    """Единая точка: использовать один и тот же шаблон для превью и экспорта."""
    return get_html_builder().build_html(html_content, **kwargs)
