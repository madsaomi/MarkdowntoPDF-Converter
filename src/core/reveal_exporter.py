"""Reveal.js export - converts Markdown to a self-contained HTML presentation."""

import os
import re
import logging

logger = logging.getLogger("MarkdownToPDF.reveal_exporter")


def export_reveal_js(html_content: str, metadata: dict, output_path: str, lang: str = 'ru'):
    """
    Wraps Markdown HTML content in a Reveal.js presentation template.
    Each H1/H2 heading becomes a new slide.
    """
    title = metadata.get('title', 'Presentation')
    author = metadata.get('author', '')

    # Split content by headings into slides
    slides = []
    parts = re.split(r'<h([12])[^>]*>(.*?)</h\1>', html_content, flags=re.DOTALL)

    if len(parts) > 1:
        # First part before first heading (skip if empty)
        for i in range(1, len(parts), 2):
            level = parts[i]
            heading = re.sub(r'<[^>]+>', '', parts[i + 1]).strip() if i + 1 < len(parts) else ''
            body = parts[i + 2] if i + 2 < len(parts) else ''
            slides.append(f'<section>\n<h{level}>{heading}</h{level}>\n{body}\n</section>')
    else:
        slides.append(f'<section>\n<h1>{title}</h1>\n{html_content}\n</section>')

    # Build Reveal.js HTML
    reveal_html = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/theme/white.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/highlight/monokai.css">
    <style>
        .reveal h1 {{ font-size: 2em; color: #2c3e50; }}
        .reveal h2 {{ font-size: 1.5em; color: #34495e; }}
        .reveal pre {{ background: #f8f8f8; padding: 20px; border-radius: 8px; }}
        .reveal code {{ font-size: 0.85em; }}
        .reveal table {{ margin: 0 auto; border-collapse: collapse; }}
        .reveal th, .reveal td {{ padding: 8px 16px; border: 1px solid #ddd; }}
        .reveal th {{ background: #f5f5f5; font-weight: bold; }}
        .reveal blockquote {{ border-left: 4px solid #3498db; padding-left: 20px; color: #555; font-style: italic; }}
        .reveal img {{ max-width: 80%; max-height: 60vh; }}
        .reveal .slides > section {{ padding: 40px; }}
    </style>
</head>
<body>
    <div class="reveal">
        <div class="slides">
            <section>
                <h1>{title}</h1>
                {'<p>' + author + '</p>' if author else ''}
                <p style="color: #999; font-size: 0.8em;">Создано с MarkdownToPDF Pro</p>
            </section>
            {''.join(slides)}
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/highlight/highlight.js"></script>
    <script>
        Reveal.initialize({{
            hash: true,
            slideNumber: true,
            transition: 'slide',
            plugins: [RevealHighlight]
        }});
    </script>
</body>
</html>"""

    # Ensure output directory
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(reveal_html)

    logger.info("Reveal.js saved: %s (%d slides)", output_path, len(slides))
    return len(slides)
