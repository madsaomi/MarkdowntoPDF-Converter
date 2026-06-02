import logging
import os

logger = logging.getLogger("MarkdownToPDF.pdf_to_md")


def pdf_to_markdown(pdf_path: str) -> str:
    """Extract text from PDF and return as Markdown-formatted string."""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError("pypdf is required: pip install pypdf")

    reader = PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(f"<!-- Page {i + 1} -->\n\n{text.strip()}")

    return "\n\n---\n\n".join(pages)


def pdf_to_markdown_file(pdf_path: str, out_path: str = None) -> str:
    """Extract PDF text and save as .md file. Returns output path."""
    md = pdf_to_markdown(pdf_path)
    if out_path is None:
        out_path = os.path.splitext(pdf_path)[0] + ".md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)
    return out_path
