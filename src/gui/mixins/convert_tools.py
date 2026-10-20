"""Конвертация: PDF→MD, HTML→MD, OCR.

Выделено из ``src/gui/window_tools.py`` (TASK-012/PLAN-012), тела вербатим.
"""

import os

from PyQt6.QtWidgets import QFileDialog, QMessageBox


class ConvertToolsMixin:
    def pdf_to_markdown_convert(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF (*.pdf)")
        if not path:
            return
        try:
            from src.core.pdf_to_markdown import pdf_to_markdown
            md = pdf_to_markdown(path)
            self.live_editor.setPlainText(md)
            self._render_live_preview()
            self.append_log(f"PDF -> Markdown: {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "PDF Error", str(e))

    def html_to_markdown_convert(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select HTML file", "", "HTML (*.html *.htm)")
        if not path:
            return
        from src.core.html_to_markdown import html_to_markdown
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        md = html_to_markdown(html)
        self.live_editor.setPlainText(md)
        self._render_live_preview()
        self.append_log(f"HTML -> Markdown: {os.path.basename(path)}")

    def run_ocr(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image for OCR", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.webp)"
        )
        if not path:
            return
        try:
            from src.core.ocr_engine import image_to_markdown
            md = image_to_markdown(path)
            cursor = self.live_editor.textCursor()
            cursor.insertText(md)
            self._render_live_preview()
            self.append_log(f"OCR completed: {os.path.basename(path)}")
        except ImportError:
            QMessageBox.warning(self, "OCR", "Install: pip install pytesseract Pillow")
        except Exception as e:
            QMessageBox.critical(self, "OCR Error", str(e))

    def ocr_image_to_text(self):
        self.run_ocr()

