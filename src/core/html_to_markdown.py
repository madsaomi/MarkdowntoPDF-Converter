import re
import logging

logger = logging.getLogger("MarkdownToPDF.html2md")


def html_to_markdown(html: str) -> str:
    """Convert HTML to Markdown. Simple but functional converter."""
    text = html

    # Remove script and style
    text = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', text, flags=re.IGNORECASE)

    # Headings
    for i in range(6, 0, -1):
        text = re.sub(rf'<h{i}[^>]*>(.*?)</h{i}>', lambda m: f"\n{'#' * i} {m.group(1).strip()}\n", text, flags=re.DOTALL | re.IGNORECASE)

    # Bold
    text = re.sub(r'<(?:strong|b)>(.*?)</(?:strong|b)>', r'**\1**', text, flags=re.DOTALL | re.IGNORECASE)

    # Italic
    text = re.sub(r'<(?:em|i)>(.*?)</(?:em|i)>', r'*\1*', text, flags=re.DOTALL | re.IGNORECASE)

    # Strikethrough
    text = re.sub(r'<(?:del|s|strike)>(.*?)</(?:del|s|strike)>', r'~~\1~~', text, flags=re.DOTALL | re.IGNORECASE)

    # Code (inline)
    text = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', text, flags=re.DOTALL | re.IGNORECASE)

    # Code blocks
    text = re.sub(r'<pre[^>]*><code[^>]*>(.*?)</code></pre>', r'\n```\n\1\n```\n', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<pre[^>]*>(.*?)</pre>', r'\n```\n\1\n```\n', text, flags=re.DOTALL | re.IGNORECASE)

    # Links
    text = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', text, flags=re.DOTALL | re.IGNORECASE)

    # Images
    text = re.sub(r'<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*/?>', r'![\2](\1)', text, flags=re.IGNORECASE)
    text = re.sub(r'<img[^>]*src="([^"]*)"[^>]*/?>', r'![](\1)', text, flags=re.IGNORECASE)

    # Unordered lists
    def convert_ul(match):
        items = re.findall(r'<li[^>]*>(.*?)</li>', match.group(0), re.DOTALL | re.IGNORECASE)
        return '\n' + '\n'.join(f'- {re.sub(r"<[^>]+>", "", item).strip()}' for item in items) + '\n'
    text = re.sub(r'<ul[^>]*>[\s\S]*?</ul>', convert_ul, text, flags=re.IGNORECASE)

    # Ordered lists
    def convert_ol(match):
        items = re.findall(r'<li[^>]*>(.*?)</li>', match.group(0), re.DOTALL | re.IGNORECASE)
        return '\n' + '\n'.join(f'{i+1}. {re.sub(r"<[^>]+>", "", item).strip()}' for i, item in enumerate(items)) + '\n'
    text = re.sub(r'<ol[^>]*>[\s\S]*?</ol>', convert_ol, text, flags=re.IGNORECASE)

    # Tables
    def convert_table(match):
        table_html = match.group(0)
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
        if not rows:
            return ''
        md_rows = []
        for i, row in enumerate(rows):
            cells = re.findall(r'<(?:th|td)[^>]*>(.*?)</(?:th|td)>', row, re.DOTALL | re.IGNORECASE)
            cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
            md_rows.append('| ' + ' | '.join(cells) + ' |')
            if i == 0:
                md_rows.append('| ' + ' | '.join(['---'] * len(cells)) + ' |')
        return '\n' + '\n'.join(md_rows) + '\n'
    text = re.sub(r'<table[^>]*>[\s\S]*?</table>', convert_table, text, flags=re.IGNORECASE)

    # Blockquotes
    text = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', lambda m: '\n> ' + m.group(1).strip() + '\n', text, flags=re.DOTALL | re.IGNORECASE)

    # Horizontal rules
    text = re.sub(r'<hr[^>]*/?>', '\n---\n', text, flags=re.IGNORECASE)

    # Line breaks / paragraphs
    text = re.sub(r'<br[^>]*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\1\n', text, flags=re.DOTALL | re.IGNORECASE)

    # Remove remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Decode HTML entities
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    text = text.replace('&nbsp;', ' ')

    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    return text
