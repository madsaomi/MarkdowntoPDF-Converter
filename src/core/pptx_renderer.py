"""PPTX export renderer - converts Markdown to PowerPoint."""

import os
import re
import logging

logger = logging.getLogger("MarkdownToPDF.pptx_renderer")


class PPTXRenderer:
    def __init__(self):
        pass

    def render(self, html_content: str, metadata: dict, output_path: str,
               slide_width: int = None, slide_height: int = None, lang: str = 'ru'):
        """
        Converts Markdown HTML content to PPTX.
        Each H1/H2 heading starts a new slide. Content under it becomes slide body.
        """
        try:
            from pptx import Presentation
            from pptx.util import Inches, Pt, Emu
            from pptx.enum.text import PP_ALIGN
        except ImportError:
            raise ImportError("python-pptx is required for PPTX export. Install with: pip install python-pptx")

        prs = Presentation()

        # Set slide size (16:9 default)
        if slide_width and slide_height:
            prs.slide_width = Emu(slide_width)
            prs.slide_height = Emu(slide_height)
        else:
            prs.slide_width = Inches(13.333)
            prs.slide_height = Inches(7.5)

        # Parse HTML to extract slides
        slides = self._parse_slides(html_content, metadata)

        for slide_data in slides:
            slide_layout = prs.slide_layouts[1]  # Title and Content layout
            slide = prs.slides.add_slide(slide_layout)

            # Set title
            title_shape = slide.shapes.title
            if title_shape:
                title_shape.text = slide_data.get('title', '')
                for paragraph in title_shape.text_frame.paragraphs:
                    paragraph.font.size = Pt(32)
                    paragraph.font.bold = True

            # Set body content
            body_shape = slide.placeholders[1]
            if body_shape and slide_data.get('content'):
                text_frame = body_shape.text_frame
                text_frame.clear()
                for line in slide_data['content']:
                    line = line.strip()
                    if not line:
                        continue
                    p = text_frame.add_paragraph()
                    p.text = line
                    p.font.size = Pt(18)
                    p.space_after = Pt(6)

                    # Detect list items
                    if re.match(r'^[-*+]\s', line):
                        p.text = re.sub(r'^[-*+]\s', '• ', line)
                    elif re.match(r'^\d+\.\s', line):
                        pass  # Keep numbered
                    elif line.startswith('#'):
                        p.font.bold = True
                        p.font.size = Pt(24)

        # Ensure output directory exists
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        prs.save(output_path)
        logger.info("PPTX saved: %s (%d slides)", output_path, len(prs.slides))
        return len(prs.slides)

    def _parse_slides(self, html_content: str, metadata: dict) -> list:
        """Parse HTML content into slide data (title + content)."""
        slides = []

        # Add title slide
        title = metadata.get('title', '')
        author = metadata.get('author', '')
        if title:
            slides.append({
                'title': title,
                'content': [f"by {author}"] if author else []
            })

        # Split by h1 and h2 headings
        parts = re.split(r'<h[12][^>]*>(.*?)</h[12]>', html_content, flags=re.DOTALL)

        if len(parts) > 1:
            # First part is content before first heading (skip if empty)
            for i in range(1, len(parts), 2):
                heading = re.sub(r'<[^>]+>', '', parts[i]).strip()
                body = parts[i + 1] if i + 1 < len(parts) else ''

                # Clean HTML tags from body
                body_clean = re.sub(r'<[^>]+>', ' ', body)
                body_clean = re.sub(r'\s+', ' ', body_clean).strip()

                # Split into lines for bullet points
                lines = [l.strip() for l in body_clean.split('\n') if l.strip()]

                slides.append({
                    'title': heading,
                    'content': lines[:20]  # Limit content per slide
                })
        else:
            # No headings found, create single slide
            body_clean = re.sub(r'<[^>]+>', ' ', html_content)
            body_clean = re.sub(r'\s+', ' ', body_clean).strip()
            lines = [l.strip() for l in body_clean.split('\n') if l.strip()]
            slides.append({
                'title': title or 'Presentation',
                'content': lines[:20]
            })

        return slides
