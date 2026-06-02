import os
import logging

logger = logging.getLogger("MarkdownToPDF.pdf_encrypt")


def encrypt_pdf(input_path: str, password: str, output_path: str = None) -> bool:
    """
    Encrypt a PDF file with a password using pypdf.
    Overwrites in-place if output_path is None.
    Returns True on success, False on failure.
    """
    try:
        from pypdf import PdfReader, PdfWriter

        reader = PdfReader(input_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(password)

        save_to = output_path or input_path
        with open(save_to, "wb") as f:
            writer.write(f)
        return True
    except Exception as e:
        logger.error("Failed to encrypt PDF %s: %s", input_path, e)
        return False
