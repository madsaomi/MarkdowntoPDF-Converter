"""Image export renderer - converts Markdown to PNG/JPG using WeasyPrint."""

import os
import logging
import tempfile

logger = logging.getLogger("MarkdownToPDF.image_renderer")


class ImageRenderer:
    def __init__(self, wp_executable: str = ""):
        self.wp_executable = wp_executable

    def render(self, html_content: str, metadata: dict, output_path: str,
               doc_theme_css: str = '', code_theme_css: str = '',
               paper_size: str = 'A4', lang: str = 'ru',
               image_format: str = 'png', dpi: int = 150,
               cancel_flag=None):
        """
        Renders HTML content to PNG or JPG image(s).
        For multi-page documents, creates numbered files: output_1.png, output_2.png, etc.
        """
        from jinja2 import Environment, FileSystemLoader

        template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('base.html')

        rendered_html = template.render(
            content=html_content,
            meta=metadata,
            doc_theme_css=doc_theme_css,
            code_theme_css=code_theme_css,
            custom_css='',
            paper_size=paper_size,
            watermark='',
            footer_text='',
            margins='',
            page_numbers=False,
            page_num_format='simple',
            tr_page='Страница' if lang == 'ru' else 'Page',
            tr_of='из' if lang == 'ru' else 'of',
        )

        # Use WeasyPrint Python API for image rendering
        try:
            from weasyprint import HTML as WeasyHTML
        except ImportError:
            raise ImportError("WeasyPrint is required for image export. Install with: pip install WeasyPrint")

        base_url = template_dir + "/"
        doc = WeasyHTML(string=rendered_html, base_url=base_url).render()

        # Ensure output directory exists
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        base_name, ext = os.path.splitext(output_path)
        ext = ext or ('.png' if image_format == 'png' else '.jpg')

        pages = doc.pages
        for i, page in enumerate(pages):
            if cancel_flag and cancel_flag():
                raise RuntimeError("Cancelled")

            if len(pages) == 1:
                page_path = output_path
            else:
                page_path = f"{base_name}_{i + 1}{ext}"

            surface = page.paint_page((dpi / 72.0, dpi / 72.0))

            if image_format == 'png':
                surface.write_png(page_path)
            else:
                # For JPG, write PNG first then convert
                temp_png = page_path + '.tmp.png'
                surface.write_png(temp_png)
                try:
                    from PIL import Image
                    img = Image.open(temp_png)
                    rgb_img = img.convert('RGB')
                    rgb_img.save(page_path, 'JPEG', quality=95)
                finally:
                    if os.path.exists(temp_png):
                        os.remove(temp_png)

            logger.info("Image saved: %s", page_path)

        return len(pages)
