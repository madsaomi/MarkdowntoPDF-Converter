import os
import sys
import logging
import time
import tempfile
import subprocess
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger("MarkdownToPDF.renderer")


class PDFRenderer:
    def __init__(self, template_dir: str, wp_executable: str = ""):
        self.template_dir = template_dir
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.template = self.env.get_template('base.html')
        self.wp_executable = wp_executable
        # CSS cache to avoid re-reading the same files
        self._css_cache: dict[str, str] = {}

    def _read_css(self, filename: str) -> str:
        """Read CSS file with caching."""
        filepath = os.path.join(self.template_dir, filename)
        if filepath not in self._css_cache:
            with open(filepath, 'r', encoding='utf-8') as f:
                self._css_cache[filepath] = f.read()
        return self._css_cache[filepath]

    def render_html(self, html_content: str, metadata: dict,
                    doc_theme: str = 'theme_modern.css', code_theme: str = 'pygments.css',
                    paper_size: str = 'A4', watermark: str = '', footer_text: str = '',
                    input_filepath: str = None, custom_css_path: str = '', margins: str = '',
                    page_numbers: bool = False, page_num_format: str = 'simple', lang: str = 'ru',
                    word_count: int = 0) -> str:
        """
        Renders the final HTML string from Markdown HTML content + Jinja2 template.
        This is reused by both PDF rendering and HTML export.
        """
        doc_theme_css = self._read_css(doc_theme)
        code_theme_css = self._read_css(code_theme)

        custom_css = ""
        if custom_css_path and os.path.exists(custom_css_path):
            try:
                with open(custom_css_path, 'r', encoding='utf-8') as f:
                    custom_css = f.read()
            except Exception as e:
                logger.warning("Failed to read custom CSS '%s': %s", custom_css_path, e)

        # Sanitize user-provided strings for CSS injection safety
        safe_watermark = watermark.replace('"', '\\"').replace('\\', '\\\\') if watermark else ''
        safe_footer = footer_text.replace('"', '\\"').replace('\\', '\\\\') if footer_text else ''

        # Resolve dynamic footer variables
        import datetime
        current_date = datetime.datetime.now().strftime("%d.%m.%Y")
        current_time = datetime.datetime.now().strftime("%H:%M")
        input_filename = os.path.basename(input_filepath) if input_filepath else ""
        doc_title = metadata.get('title', '')

        resolved_footer = safe_footer
        if resolved_footer:
            resolved_footer = resolved_footer.replace("{date}", current_date)
            resolved_footer = resolved_footer.replace("{time}", current_time)
            resolved_footer = resolved_footer.replace("{filename}", input_filename)
            resolved_footer = resolved_footer.replace("{title}", doc_title)
            resolved_footer = resolved_footer.replace("{word_count}", str(word_count))

        tr_page = 'Страница' if lang == 'ru' else 'Page'
        tr_of = 'из' if lang == 'ru' else 'of'

        rendered_html = self.template.render(
            content=html_content,
            meta=metadata,
            doc_theme_css=doc_theme_css,
            code_theme_css=code_theme_css,
            custom_css=custom_css,
            paper_size=paper_size,
            watermark=safe_watermark,
            footer_text=resolved_footer,
            margins=margins,
            page_numbers=page_numbers,
            page_num_format=page_num_format,
            tr_page=tr_page,
            tr_of=tr_of,
        )
        return rendered_html

    def render(self, html_content: str, metadata: dict, output_path: str,
               doc_theme: str = 'theme_modern.css', code_theme: str = 'pygments.css',
               paper_size: str = 'A4', watermark: str = '', footer_text: str = '',
               input_filepath: str = None, custom_css_path: str = '', margins: str = '',
               page_numbers: bool = False, page_num_format: str = 'simple', lang: str = 'ru',
               cancel_flag: callable = None, compress: bool = False, word_count: int = 0):
        """
        Takes raw HTML content (from Markdown), injects it into the base template,
        and renders it to a PDF using WeasyPrint.
        """
        rendered_html = self.render_html(
            html_content, metadata, doc_theme, code_theme,
            paper_size, watermark, footer_text, input_filepath, custom_css_path, margins,
            page_numbers, page_num_format, lang, word_count
        )

        # Determine base URL for relative resources
        from urllib.parse import quote
        if input_filepath:
            md_dir = os.path.dirname(os.path.abspath(input_filepath))
            base_url = "file:///" + quote(md_dir.replace(os.sep, '/'), safe='/:') + "/"
        else:
            base_url = "file:///" + quote(os.path.abspath(self.template_dir).replace(os.sep, '/'), safe='/:') + "/"

        # Resolve WeasyPrint executable path
        wp_exe = self.wp_executable
        if not wp_exe or not os.path.exists(wp_exe):
            raise FileNotFoundError(f"Не найден движок WeasyPrint по пути: {wp_exe}")

        # Write rendered HTML to a temporary file
        fd, temp_html_path = tempfile.mkstemp(suffix='.html', text=True)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(rendered_html)

        temp_err_path = None
        try:
            fd_err, temp_err_path = tempfile.mkstemp(suffix='.log', text=True)
            with os.fdopen(fd_err, 'w+', encoding='utf-8') as stderr_file:
                process = subprocess.Popen([
                    wp_exe,
                    temp_html_path,
                    output_path,
                    '--base-url', base_url,
                    '--encoding', 'utf-8'
                ], stdout=subprocess.DEVNULL, stderr=stderr_file, text=True)
    
                start_time = time.time()
                while process.poll() is None:
                    if cancel_flag and cancel_flag():
                        process.kill()
                        raise RuntimeError("Конвертация отменена пользователем" if lang == 'ru' else "Conversion cancelled by user")
                    
                    if time.time() - start_time > 1800:
                        process.kill()
                        raise RuntimeError("Ошибка WeasyPrint: превышено время ожидания (таймаут 1800 сек)." if lang == 'ru' else "WeasyPrint Error: Timeout exceeded (1800s).")
                    
                    time.sleep(0.5)
    
                if process.returncode != 0:
                    stderr_file.seek(0)
                    stderr = stderr_file.read()
                    raise RuntimeError(f"Ошибка WeasyPrint:\n{stderr}" if lang == 'ru' else f"WeasyPrint Error:\n{stderr}")
        finally:
            try:
                os.remove(temp_html_path)
            except Exception:
                logger.warning("Failed to remove temp HTML: %s", temp_html_path)
            if temp_err_path:
                try:
                    os.remove(temp_err_path)
                except Exception:
                    logger.warning("Failed to remove temp log: %s", temp_err_path)

        # Post-process: compress PDF if requested
        if compress:
            try:
                from pypdf import PdfReader, PdfWriter
                reader = PdfReader(output_path)
                writer = PdfWriter()
                for page in reader.pages:
                    page.compress_content_streams()
                    writer.add_page(page)
                if reader.metadata:
                    writer.add_metadata({k: v for k, v in reader.metadata.items() if v})
                with open(output_path, 'wb') as f:
                    writer.write(f)
                logger.info("PDF compressed: %s", output_path)
            except Exception as e:
                logger.warning("PDF compression failed: %s", e)
