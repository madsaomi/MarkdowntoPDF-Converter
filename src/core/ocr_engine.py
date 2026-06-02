import logging
import os

logger = logging.getLogger("MarkdownToPDF.ocr")


def image_to_text(image_path: str, lang: str = "eng") -> str:
    """Extract text from image using pytesseract OCR."""
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        raise ImportError("Install OCR deps: pip install pytesseract Pillow")

    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang=lang)
    return text.strip()


def image_to_markdown(image_path: str, lang: str = "eng") -> str:
    """Extract text from image and return as Markdown."""
    text = image_to_text(image_path, lang)
    if not text:
        return ""
    return f"![Extracted from {os.path.basename(image_path)}]({image_path})\n\n{text}"


def batch_ocr(image_paths: list[str], lang: str = "eng") -> dict[str, str]:
    """OCR multiple images, return dict of path → text."""
    results = {}
    for path in image_paths:
        try:
            results[path] = image_to_text(path, lang)
        except Exception as e:
            logger.error("OCR failed for %s: %s", path, e)
            results[path] = f"[OCR Error: {e}]"
    return results
