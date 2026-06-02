"""EPUB export renderer using ebooklib."""

import os
import logging

logger = logging.getLogger("MarkdownToPDF.epub_renderer")


class EPUBRenderer:
    def __init__(self):
        pass

    def render(self, html_content: str, metadata: dict, output_path: str, lang: str = "ru"):
        """
        Takes raw HTML content (from Markdown parser), converts it to EPUB format,
        and saves it to the output_path.
        """
        try:
            from ebooklib import epub
        except ImportError:
            raise ImportError("ebooklib is required for EPUB export. Install with: pip install ebooklib")

        book = epub.EpubBook()

        title = metadata.get('title', 'Document')
        author = metadata.get('author', 'Unknown')
        date = metadata.get('date', '')

        book.set_identifier(f'mdpdf-{id(book)}')
        book.set_title(title)
        book.set_language(lang)
        book.add_author(author)

        # Create chapter
        chapter = epub.EpubHtml(title=title, file_name='chapter.xhtml', lang=lang)
        chapter.content = html_content.encode('utf-8')

        # Add basic styling
        style = epub.EpubItem(
            uid="style",
            file_name="style/default.css",
            media_type="text/css",
            content=b"""
            body { font-family: serif; line-height: 1.6; margin: 1em; }
            h1 { font-size: 2em; margin-bottom: 0.5em; }
            h2 { font-size: 1.5em; margin-top: 1em; margin-bottom: 0.5em; }
            pre { background: #f4f4f4; padding: 10px; border-radius: 4px; overflow-x: auto; }
            code { font-family: monospace; background: #f4f4f4; padding: 2px 4px; }
            blockquote { border-left: 3px solid #ccc; margin: 1em 0; padding: 0.5em 1em; color: #555; }
            table { border-collapse: collapse; width: 100%; margin: 1em 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background: #f9f9f9; }
            img { max-width: 100%; height: auto; }
            """
        )
        book.add_item(style)
        chapter.add_item(style)

        book.add_item(chapter)
        book.spine = ['nav', chapter]

        # Add navigation files
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # Ensure output directory exists
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        epub.write_epub(output_path, book)
        logger.info("EPUB saved: %s", output_path)
