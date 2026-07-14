import re
import logging

logger = logging.getLogger("MarkdownToPDF.glossary")


def extract_definitions(text: str) -> list[dict]:
    """Extract definitions from Markdown.

    Recognizes patterns:
        - **Term**: Definition
        - **Term** — Definition
        - **Term**: Definition text here
        - Term: Definition (at start of line with bold)
    """
    definitions = []

    patterns = [
        re.compile(r'^\*\*(.+?)\*\*[:\-—]\s*(.+)$', re.MULTILINE),
        re.compile(r'^\*\*(.+?)\*\*\s*:\s*(.+)$', re.MULTILINE),
    ]

    seen = set()
    for pattern in patterns:
        for match in pattern.finditer(text):
            term = match.group(1).strip()
            definition = match.group(2).strip()
            if term.lower() not in seen:
                seen.add(term.lower())
                definitions.append({"term": term, "definition": definition})

    return sorted(definitions, key=lambda d: d["term"].lower())


def glossary_to_markdown(definitions: list[dict]) -> str:
    """Convert definitions to a formatted glossary."""
    if not definitions:
        return ""

    lines = ["## Glossary\n"]
    for d in definitions:
        lines.append(f"**{d['term']}**: {d['definition']}\n")
    return "\n".join(lines)


def glossary_to_html(definitions: list[dict]) -> str:
    """Convert definitions to HTML glossary with anchor links."""
    import html
    if not definitions:
        return ""

    items = []
    nav = []
    for d in definitions:
        safe_term = html.escape(d['term'])
        safe_def = html.escape(d['definition'])
        anchor = re.sub(r'[^\w]', '', d['term'].lower())
        nav.append(f'<a href="#{anchor}" style="display:inline-block;margin:4px 8px;padding:4px 12px;background:#f1f2f6;border-radius:4px;text-decoration:none;color:#2c3e50;">{safe_term}</a>')
        items.append(f'<dt id="{anchor}" style="font-weight:bold;color:#2c3e50;margin-top:12px;">{safe_term}</dt>')
        items.append(f'<dd style="margin:0 0 0 20px;color:#7f8c8d;">{safe_def}</dd>')

    return f"""<!DOCTYPE html>
<html><head><style>
body {{ font-family: sans-serif; padding: 20px; max-width: 700px; margin: 0 auto; }}
dt {{ font-size: 16px; }}
dd {{ font-size: 14px; }}
</style></head><body>
<h2>📖 Glossary ({len(definitions)} terms)</h2>
<div style="text-align:center;padding:10px;">{''.join(nav)}</div>
<dl>{''.join(items)}</dl>
</body></html>"""


def glossary_to_json(definitions: list[dict]) -> str:
    """Export glossary as JSON."""
    import json
    return json.dumps(definitions, ensure_ascii=False, indent=2)


def find_term_in_text(text: str, term: str) -> list[int]:
    """Find all occurrences of a glossary term in text (case-insensitive)."""
    return [m.start() for m in re.finditer(re.escape(term), text, re.IGNORECASE)]
