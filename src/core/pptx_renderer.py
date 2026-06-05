"""PPTX export renderer - converts Markdown to PowerPoint."""

import os
import re
import logging
from html.parser import HTMLParser

logger = logging.getLogger("MarkdownToPDF.pptx_renderer")


class _SlideParser(HTMLParser):
    """HTML parser that splits content into slides by h1/h2 headings."""
    def __init__(self):
        super().__init__()
        self.slides = []
        self._current_title = None
        self._current_content = []
        self._in_heading = False
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        if tag_lower in ('h1', 'h2') and self._skip_depth == 0:
            self._in_heading = True
            self._current_title = ''
            if self._current_content:
                self._flush_content()
        elif self._in_heading:
            pass
        elif tag_lower in ('script', 'style'):
            self._skip_depth += 1
        else:
            pass

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in ('script', 'style'):
            if self._skip_depth > 0:
                self._skip_depth -= 1
        elif tag_lower in ('h1', 'h2'):
            if self._in_heading:
                self._in_heading = False
                title = self._current_title.strip() if self._current_title else ''
                if title:
                    self.slides.append({'title': title, 'content': []})
                self._current_title = None
        elif tag_lower in ('p', 'li', 'tr', 'div', 'pre', 'blockquote'):
            if not self._in_heading and self._skip_depth == 0:
                self._current_content.append('')

    def handle_data(self, data):
        if self._skip_depth > 0:
            return
        if self._in_heading:
            if self._current_title is not None:
                self._current_title += data
        else:
            text = data.strip()
            if text:
                if self._current_content and self._current_content[-1] != '':
                    self._current_content[-1] += ' ' + text
                else:
                    self._current_content.append(text)

    def handle_entityref(self, name):
        if self._in_heading and self._current_title is not None:
            self._current_title += f'&{name};'

    def handle_charref(self, name):
        if self._in_heading and self._current_title is not None:
            self._current_title += f'&#{name};'

    def _flush_content(self):
        if self._current_content:
            joined = ' '.join(self._current_content).strip()
            if joined:
                self.slides[-1]['content'] = [joined]
            self._current_content = []


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
        except ImportError:
            raise ImportError("python-pptx is required for PPTX export. Install with: pip install python-pptx")

        prs = Presentation()

        if slide_width and slide_height:
            prs.slide_width = Emu(slide_width)
            prs.slide_height = Emu(slide_height)
        else:
            prs.slide_width = Inches(13.333)
            prs.slide_height = Inches(7.5)

        slides = self._parse_slides(html_content, metadata)

        for slide_data in slides:
            slide_layout = prs.slide_layouts[1]
            slide = prs.slides.add_slide(slide_layout)

            title_shape = slide.shapes.title
            if title_shape:
                title_shape.text = slide_data.get('title', '')
                for paragraph in title_shape.text_frame.paragraphs:
                    paragraph.font.size = Pt(32)
                    paragraph.font.bold = True

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

                    if re.match(r'^[-*+]\s', line):
                        p.text = re.sub(r'^[-*+]\s', '• ', line)
                    elif re.match(r'^\d+\.\s', line):
                        pass
                    elif line.startswith('#'):
                        p.font.bold = True
                        p.font.size = Pt(24)

        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        prs.save(output_path)
        logger.info("PPTX saved: %s (%d slides)", output_path, len(prs.slides))
        return len(prs.slides)

    def _parse_slides(self, html_content: str, metadata: dict) -> list:
        """Parse HTML content into slide data using HTMLParser."""
        slides = []

        title = metadata.get('title', '')
        author = metadata.get('author', '')
        if title:
            slides.append({
                'title': title,
                'content': [f"by {author}"] if author else []
            })

        parser = _SlideParser()
        parser.feed(html_content)

        for s in parser.slides:
            slides.append(s)

        if not parser.slides:
            body_clean = re.sub(r'<[^>]+>', ' ', html_content)
            body_clean = re.sub(r'\s+', ' ', body_clean).strip()
            lines = [l.strip() for l in body_clean.split('\n') if l.strip()]
            slides.append({
                'title': title or 'Presentation',
                'content': lines[:20]
            })

        return slides
