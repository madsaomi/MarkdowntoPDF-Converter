import os
import logging
import urllib.request
from PyQt6.QtCore import QThread, pyqtSignal, QMutex
from src.gui.models import ConversionOptions, ExportFormat
from src.core.parser import MarkdownParser
from src.core.renderer import PDFRenderer
from src.core.docx_renderer import DOCXRenderer
from src.gui.translations import TRANSLATIONS

logger = logging.getLogger("MarkdownToPDF.threads")


# ──────────────────────── Kroki.io Network Checker ────────────────────────

class KrokiCheckThread(QThread):
    finished = pyqtSignal(bool)

    def run(self):
        import urllib.request
        try:
            req = urllib.request.Request("https://kroki.io", method="HEAD")
            with urllib.request.urlopen(req, timeout=1.5):
                self.finished.emit(True)
        except Exception:
            self.finished.emit(False)


# ──────────────────────── Conversion thread ────────────────────────

class ConversionThread(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished_one = pyqtSignal(bool, str)
    finished_all = pyqtSignal()

    def __init__(self, files: list, output_dir: str, template_dir: str,
                 options: ConversionOptions, wp_executable: str = "", lang: str = "ru", kroki_available: bool = True):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.template_dir = template_dir
        self.options = options
        self.wp_executable = wp_executable
        self.lang = lang
        self.kroki_available = kroki_available
        self._cancel_mutex = QMutex()
        self._is_cancelled = False

    def cancel(self):
        """Thread-safe cancellation."""
        self._cancel_mutex.lock()
        self._is_cancelled = True
        self._cancel_mutex.unlock()

    def is_cancelled(self) -> bool:
        """Thread-safe cancellation check."""
        self._cancel_mutex.lock()
        val = self._is_cancelled
        self._cancel_mutex.unlock()
        return val

    def run(self):
        total = len(self.files)
        t = lambda k, *args: TRANSLATIONS[self.lang].get(k, k).format(*args) if args else TRANSLATIONS[self.lang].get(k, k)
        for idx, (input_file, output_file) in enumerate(self.files, start=1):
            if self.is_cancelled():
                self.log.emit(t("log_cancelled"))
                break
            try:
                self.log.emit(t("log_processing", idx, total, os.path.basename(input_file)))
                self.progress.emit(int((idx - 1) / total * 100))

                with open(input_file, 'r', encoding='utf-8') as f:
                    md_text = f.read()

                opt = self.options
                parser = MarkdownParser()
                html_content, metadata = parser.parse(
                    md_text, 
                    base_dir=os.path.dirname(os.path.abspath(input_file)),
                    is_presentation=opt.is_presentation,
                    kroki_available=self.kroki_available
                )

                doc_theme_file = 'theme_presentation.css' if opt.is_presentation else opt.doc_theme

                if opt.export_format == ExportFormat.DOCX:
                    renderer = DOCXRenderer()
                    renderer.render(html_content, metadata, output_file, reference_docx=opt.docx_template, lang=self.lang)
                elif opt.export_format == ExportFormat.HTML:
                    # HTML export: render through Jinja2 template but save as .html
                    renderer = PDFRenderer(self.template_dir, self.wp_executable)
                    rendered_html = renderer.render_html(
                        html_content, metadata,
                        doc_theme_file, opt.code_theme,
                        opt.paper_size, opt.watermark, opt.footer_text,
                        input_file, opt.custom_css, opt.margins,
                        page_numbers=opt.page_numbers, page_num_format=opt.page_num_format, lang=self.lang
                    )
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(rendered_html)
                else:
                    renderer = PDFRenderer(self.template_dir, self.wp_executable)
                    renderer.render(
                        html_content, metadata, output_file,
                        doc_theme_file, opt.code_theme,
                        opt.paper_size, opt.watermark, opt.footer_text,
                        input_file, opt.custom_css, opt.margins,
                        page_numbers=opt.page_numbers, page_num_format=opt.page_num_format, lang=self.lang,
                        cancel_flag=lambda: self._is_cancelled
                    )
                    
                    if opt.pdf_password and opt.export_format == ExportFormat.PDF:
                        try:
                            from pypdf import PdfReader, PdfWriter
                            reader = PdfReader(output_file)
                            writer = PdfWriter()
                            for page in reader.pages:
                                writer.add_page(page)
                            writer.encrypt(opt.pdf_password)
                            with open(output_file, "wb") as f:
                                writer.write(f)
                            self.log.emit(t("log_pdf_encrypted"))
                        except Exception as e:
                            self.log.emit(t("log_pdf_encrypt_error", str(e)))
                            logger.error("Failed to encrypt PDF %s: %s", output_file, e)

                self.log.emit(t("log_saved", output_file))
                self.finished_one.emit(True, output_file)
                logger.info("Converted: %s -> %s", input_file, output_file)
            except Exception as e:
                self.log.emit(t("log_error", str(e)))
                self.finished_one.emit(False, str(e))
                logger.error("Conversion failed for %s: %s", input_file, e, exc_info=True)

        self.progress.emit(100)
        self.log.emit(t("log_done_all"))
        self.finished_all.emit()


# ──────────────────────── Book Builder Thread ────────────────────────

class BookBuilderThread(QThread):
    log = pyqtSignal(str)
    finished_task = pyqtSignal(bool, str)

    def __init__(self, merged_md, base_dir, save_path, book_title, template_dir, wp_executable,
                 doc_theme, code_theme, paper_size, watermark, footer, custom_css, margins,
                 password, page_numbers, lang, kroki_available):
        super().__init__()
        self.merged_md = merged_md
        self.base_dir = base_dir
        self.save_path = save_path
        self.book_title = book_title
        self.template_dir = template_dir
        self.wp_executable = wp_executable
        self.doc_theme = doc_theme
        self.code_theme = code_theme
        self.paper_size = paper_size
        self.watermark = watermark
        self.footer = footer
        self.custom_css = custom_css
        self.margins = margins
        self.password = password
        self.page_numbers = page_numbers
        self.lang = lang
        self.kroki_available = kroki_available
        self._cancel_mutex = QMutex()
        self._is_cancelled = False

    def cancel(self):
        self._cancel_mutex.lock()
        self._is_cancelled = True
        self._cancel_mutex.unlock()

    def is_cancelled(self) -> bool:
        self._cancel_mutex.lock()
        val = self._is_cancelled
        self._cancel_mutex.unlock()
        return val

    def run(self):
        t = lambda k, *args: TRANSLATIONS[self.lang].get(k, k).format(*args) if args else TRANSLATIONS[self.lang].get(k, k)
        try:
            self.log.emit(f"\n⚙️ Parsing merged Markdown ({len(self.merged_md)} chars)...")
            
            parser = MarkdownParser()
            html_content, metadata = parser.parse(self.merged_md, base_dir=self.base_dir, kroki_available=self.kroki_available)
            
            if self.book_title:
                metadata['title'] = self.book_title

            if self.is_cancelled():
                self.log.emit(t("log_cancelled"))
                self.finished_task.emit(False, "Cancelled")
                return

            self.log.emit("⚙️ Rendering PDF with WeasyPrint...")
            renderer = PDFRenderer(self.template_dir, self.wp_executable)
            
            renderer.render(
                html_content, metadata, self.save_path,
                self.doc_theme, self.code_theme,
                self.paper_size, self.watermark, self.footer,
                input_filepath=None, custom_css_path=self.custom_css, margins=self.margins,
                page_numbers=self.page_numbers, page_num_format='simple',
                lang=self.lang,
                cancel_flag=lambda: self.is_cancelled()
            )

            if self.password:
                try:
                    from pypdf import PdfReader, PdfWriter
                    reader = PdfReader(self.save_path)
                    writer = PdfWriter()
                    for page in reader.pages:
                        writer.add_page(page)
                    writer.encrypt(self.password)
                    with open(self.save_path, "wb") as f:
                        writer.write(f)
                    self.log.emit(t("log_pdf_encrypted"))
                except Exception as e:
                    self.log.emit(t("log_pdf_encrypt_error", str(e)))

            self.log.emit(t("log_saved", self.save_path))
            self.finished_task.emit(True, self.save_path)

        except Exception as e:
            self.log.emit(t("log_error", str(e)))
            self.finished_task.emit(False, str(e))
