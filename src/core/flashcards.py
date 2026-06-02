import re
import logging

logger = logging.getLogger("MarkdownToPDF.flashcards")


def extract_flashcards(text: str) -> list[dict]:
    """Extract flashcards from Markdown headings + content.

    Each heading becomes a 'front', the paragraph(s) after it become 'back'.
    """
    lines = text.split('\n')
    cards = []
    current_heading = None
    current_content = []

    for line in lines:
        heading_match = re.match(r'^(#{1,3})\s+(.*)', line)
        if heading_match:
            if current_heading:
                cards.append({
                    "front": current_heading,
                    "back": '\n'.join(current_content).strip()
                })
            current_heading = heading_match.group(2).strip()
            current_content = []
        elif current_heading is not None:
            current_content.append(line)

    if current_heading:
        cards.append({
            "front": current_heading,
            "back": '\n'.join(current_content).strip()
        })

    return cards


def cards_to_anki(cards: list[dict], separator: str = "\t") -> str:
    """Export flashcards as Anki-compatible TSV."""
    lines = []
    for card in cards:
        front = card["front"].replace("\t", " ").replace("\n", " ")
        back = card["back"].replace("\t", " ").replace("\n", "<br>")
        lines.append(f"{front}{separator}{back}")
    return '\n'.join(lines)


def cards_to_markdown(cards: list[dict]) -> str:
    """Export flashcards as Markdown."""
    lines = ["# Flashcards\n"]
    for i, card in enumerate(cards, 1):
        lines.append(f"## Card {i}: {card['front']}\n")
        lines.append(f"{card['back']}\n")
    return '\n'.join(lines)


def cards_to_html(cards: list[dict]) -> str:
    """Export flashcards as interactive HTML with flip animation."""
    cards_html = []
    for i, card in enumerate(cards):
        back = card['back'].replace('\n', '<br>')
        cards_html.append(f"""
        <div class="card" onclick="this.classList.toggle('flipped')">
            <div class="front">{card['front']}</div>
            <div class="back">{back}</div>
        </div>""")

    return f"""<!DOCTYPE html>
<html><head><style>
.card {{
    width: 300px; min-height: 200px; margin: 20px; padding: 20px;
    background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    cursor: pointer; perspective: 1000px; display: inline-block;
    transition: transform 0.3s; text-align: center; vertical-align: top;
}}
.card:hover {{ box-shadow: 0 6px 20px rgba(0,0,0,0.2); }}
.card .front {{ font-size: 18px; font-weight: bold; color: #2c3e50; }}
.card .back {{ display: none; font-size: 14px; color: #7f8c8d; margin-top: 16px; }}
.card.flipped .front {{ display: none; }}
.card.flipped .back {{ display: block; }}
body {{ font-family: sans-serif; padding: 20px; background: #f8f9fa; text-align: center; }}
h2 {{ color: #2c3e50; }}
</style></head><body>
<h2>🃏 Flashcards ({len(cards)} cards)</h2>
<p>Click a card to flip it</p>
{''.join(cards_html)}
</body></html>"""
