import os
import re
from datetime import datetime


def substitute_template_vars(text: str, context: dict = None) -> str:
    """Replace {{variable}} placeholders in text with values.

    Built-in variables:
        {{date}}        - current date YYYY-MM-DD
        {{time}}        - current time HH:MM
        {{datetime}}    - current datetime
        {{filename}}    - current file name without extension
        {{title}}       - first H1 heading in the text
        {{word_count}}  - word count
        {{year}}        - current year
        {{month}}       - current month
        {{day}}         - current day
        {{author}}      - from context or 'Author'

    Custom variables are passed via context dict.
    """
    now = datetime.now()

    word_count = len(text.split())
    title_match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "Untitled"

    builtins = {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "datetime": now.strftime("%Y-%m-%d %H:%M"),
        "year": str(now.year),
        "month": f"{now.month:02d}",
        "day": f"{now.day:02d}",
        "title": title,
        "word_count": str(word_count),
        "author": "Author",
    }

    if context:
        builtins.update(context)

    def replacer(match):
        var = match.group(1).strip()
        return builtins.get(var, match.group(0))

    return re.sub(r'\{\{(\w+)\}\}', replacer, text)


def extract_front_matter(text: str) -> tuple[dict, str]:
    """Extract YAML-like front matter from text.

    Supports:
        ---
        title: My Document
        author: John
        tags: markdown, pdf
        ---
        Rest of content...

    Returns (dict_of_vars, content_without_front_matter).
    """
    if not text.startswith("---"):
        return {}, text

    end = text.find("---", 3)
    if end == -1:
        return {}, text

    fm_block = text[3:end].strip()
    content = text[end + 3:].strip()

    vars_dict = {}
    for line in fm_block.splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            vars_dict[key.strip()] = val.strip()

    return vars_dict, content


def process_document_vars(text: str, filename: str = "") -> str:
    """Full pipeline: extract front matter, then substitute all variables."""
    fm_vars, content = extract_front_matter(text)

    if filename:
        fm_vars["filename"] = os.path.splitext(os.path.basename(filename))[0]

    return substitute_template_vars(content, fm_vars)
