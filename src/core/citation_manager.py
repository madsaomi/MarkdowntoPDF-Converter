import json
import os
import re
import logging

logger = logging.getLogger("MarkdownToPDF.citations")

CITATIONS_FILE = "citations.json"


def _load_citations(path: str) -> list[dict]:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_citations(path: str, citations: list[dict]):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(citations, f, ensure_ascii=False, indent=2)


def add_citation(path: str, key: str, authors: str, title: str,
                 year: str, source: str = "", url: str = "") -> dict:
    """Add a citation to the bibliography file."""
    citations = _load_citations(path)
    entry = {
        "key": key,
        "authors": authors,
        "title": title,
        "year": year,
        "source": source,
        "url": url,
    }
    # Update existing or add new
    existing = next((c for c in citations if c["key"] == key), None)
    if existing:
        existing.update(entry)
    else:
        citations.append(entry)
    _save_citations(path, citations)
    return entry


def remove_citation(path: str, key: str) -> bool:
    citations = _load_citations(path)
    new = [c for c in citations if c["key"] != key]
    if len(new) < len(citations):
        _save_citations(path, new)
        return True
    return False


def get_citations(path: str) -> list[dict]:
    return _load_citations(path)


def format_citation_apa(entry: dict) -> str:
    """Format citation in APA style."""
    parts = [f"{entry['authors']} ({entry['year']}). {entry['title']}."]
    if entry.get('source'):
        parts.append(f" {entry['source']}.")
    if entry.get('url'):
        parts.append(f" {entry['url']}")
    return " ".join(parts)


def format_citation_mla(entry: dict) -> str:
    """Format citation in MLA style."""
    parts = [f"{entry['authors']}. \"{entry['title']}.\""]
    if entry.get('source'):
        parts.append(f" {entry['source']},")
    parts.append(f" {entry['year']}.")
    return " ".join(parts)


def insert_citation_inline(text: str, key: str) -> str:
    """Insert inline citation reference [key] at cursor position."""
    return f"{text} [{key}]"


def generate_bibliography(path: str, style: str = "apa") -> str:
    """Generate formatted bibliography from citations."""
    citations = _load_citations(path)
    if not citations:
        return "## Bibliography\n\n_No references._\n"

    formatter = format_citation_apa if style == "apa" else format_citation_mla
    lines = ["## Bibliography\n"]
    for entry in sorted(citations, key=lambda c: c.get("key", "")):
        lines.append(f"- {formatter(entry)}")
    return "\n".join(lines) + "\n"


def extract_citation_keys(text: str) -> list[str]:
    """Find all [citation_key] references in text."""
    return re.findall(r'\[([A-Za-z][\w-]*)\]', text)
