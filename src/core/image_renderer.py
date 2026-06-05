"""Image export renderer - converts Markdown to PNG/JPG via WeasyPrint CLI + PyMuPDF."""

import os
import logging
import tempfile
import subprocess
import time

logger = logging.getLogger("MarkdownToPDF.image_renderer")


class ImageRenderer:
    def __init__(self, wp_executable: str = ""):
        self.wp_executable = wp_executable

    def render(self, html_content: str, metadata: dict, output_path: str,
               doc_theme_css: str = '', code_theme_css: str = '',
               paper_size: str = 'A4', lang: str = 'ru',
               image_format: str = 'png', dpi: int = 150,
               cancel_flag=None):
        from jinja2 import Environment, FileSystemLoader
        from src.config import AppConfig

        template_dir = AppConfig.template_dir()
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

        wp_exe = self.wp_executable
        if not wp_exe or not os.path.exists(wp_exe):
            raise FileNotFoundError(f"Не найден движок WeasyPrint по пути: {wp_exe}")

        # Render HTML to PDF via WeasyPrint CLI
        fd_html, temp_html_path = tempfile.mkstemp(suffix='.html', text=True)
        try:
            with os.fdopen(fd_html, 'w', encoding='utf-8') as f:
                f.write(rendered_html)

            fd_pdf, temp_pdf_path = tempfile.mkstemp(suffix='.pdf')
            os.close(fd_pdf)

            fd_err, temp_err_path = tempfile.mkstemp(suffix='.log', text=True)
            with os.fdopen(fd_err, 'w+', encoding='utf-8') as stderr_file:
                process = subprocess.Popen(
                    [wp_exe, temp_html_path, temp_pdf_path, '--encoding', 'utf-8'],
                    stdout=subprocess.DEVNULL, stderr=stderr_file, text=True
                )

                start_time = time.time()
                while process.poll() is None:
                    if cancel_flag and cancel_flag():
                        process.kill()
                        raise RuntimeError("Конвертация отменена пользователем" if lang == 'ru' else "Conversion cancelled by user")
                    if time.time() - start_time > 300:
                        process.kill()
                        raise RuntimeError("Timeout")
                    time.sleep(0.3)

                if process.returncode != 0:
                    stderr_file.seek(0)
                    stderr = stderr_file.read()
                    raise RuntimeError(stderr or f"WeasyPrint exit code {process.returncode}")

            # Convert PDF pages to images via PyMuPDF
            import fitz
            out_dir = os.path.dirname(output_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)

            base_name, ext = os.path.splitext(output_path)
            ext = ext or ('.png' if image_format == 'png' else '.jpg')
            zoom = dpi / 72.0

            pdf_doc = fitz.open(temp_pdf_path)
            num_pages = len(pdf_doc)
            for i in range(num_pages):
                if cancel_flag and cancel_flag():
                    pdf_doc.close()
                    raise RuntimeError("Cancelled")

                page = pdf_doc[i]
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)

                if num_pages == 1:
                    page_path = output_path
                else:
                    page_path = f"{base_name}_{i + 1}{ext}"

                if image_format == 'png':
                    pix.save(page_path)
                else:
                    from PIL import Image
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    img.save(page_path, 'JPEG', quality=95)

                logger.info("Image saved: %s", page_path)

            pdf_doc.close()
            return num_pages

        finally:
            try:
                os.unlink(temp_html_path)
            except OSError:
                pass
            try:
                os.unlink(temp_pdf_path)
            except OSError:
                pass
