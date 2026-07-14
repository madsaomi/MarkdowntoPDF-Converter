"""AI Writing Assistant - local text analysis and improvement suggestions."""

import re
import logging
from dataclasses import dataclass

logger = logging.getLogger("MarkdownToPDF.ai_assistant")


@dataclass
class AISuggestion:
    """A single AI suggestion."""
    category: str  # grammar, style, readability, structure
    original: str
    suggestion: str
    explanation: str
    line: int = 0


class AIWritingAssistant:
    """Local AI-powered writing assistant for Markdown documents."""

    # Common Russian/English grammar patterns
    GRAMMAR_RULES = {
        "ru": [
            (r"(\w+)\s+тоже\s+(\w+)", "Используйте «также» вместо «тоже» в формальном тексте"),
            (r"очень\s+очень", "Избегайте повторений «очень»"),
        ],
        "en": [
            (r"\bi\b", "Используйте заглавную букву «I» вместо строчной"),
            (r"(\w+)\s+alot\b", "Правильно: «a lot» (два слова)"),
            (r"\byour\b\s+(?=car|house|dog|cat)", "Возможно, имелось в виду «you're» (you are)"),
            (r"\bits\b\s+(?=a|the|very|not)", "Возможно, имелось в виду «it's» (it is)"),
        ],
    }

    # Style improvements: (pattern, replacement, explanation)
    STYLE_RULES = {
        "ru": [
            (r"в\s+настоящее\s+время", "сейчас", "Сократите до «сейчас» или «ныне»"),
            (r"для\s+того\s+чтобы", "чтобы", "Сократите до «чтобы»"),
        ],
        "en": [
            (r"in\s+order\s+to", "to", "Сократите до «to»"),
            (r"due\s+to\s+the\s+fact\s+that", "because", "Сократите до «because»"),
            (r"at\s+the\s+present\s+time", "now", "Сократите до «now»"),
            (r"has\s+the\s+ability\s+to", "can", "Сократите до «can»"),
        ],
    }

    def analyze(self, text: str, lang: str = "ru") -> list[AISuggestion]:
        """Analyze text and return suggestions."""
        suggestions = []
        lines = text.split("\n")

        for line_num, line in enumerate(lines, 1):
            if line.startswith("```") or line.startswith("|"):
                continue

            suggestions.extend(self._check_grammar(line, lang, line_num))
            suggestions.extend(self._check_style(line, lang, line_num))
            suggestions.extend(self._check_readability(line, line_num))
            suggestions.extend(self._check_structure(line, line_num))

        return suggestions

    def _check_grammar(self, text: str, lang: str, line: int) -> list[AISuggestion]:
        results = []
        rules = self.GRAMMAR_RULES.get(lang, []) + self.GRAMMAR_RULES.get("en", [])
        for pattern, explanation in rules:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                results.append(AISuggestion(
                    category="grammar",
                    original=match.group(),
                    suggestion=match.group(),
                    explanation=explanation,
                    line=line
                ))
        return results

    def _check_style(self, text: str, lang: str, line: int) -> list[AISuggestion]:
        results = []
        rules = self.STYLE_RULES.get(lang, []) + self.STYLE_RULES.get("en", [])
        for pattern, _replacement, explanation in rules:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                results.append(AISuggestion(
                    category="style",
                    original=match.group(),
                    suggestion=match.group(),
                    explanation=explanation,
                    line=line
                ))
        return results

    def _check_readability(self, text: str, line: int) -> list[AISuggestion]:
        results = []
        words = text.split()
        if len(words) > 30:
            results.append(AISuggestion(
                category="readability",
                original=text[:50] + "...",
                suggestion="Разбейте на 2-3 предложения",
                explanation=f"Предложение содержит {len(words)} слов. Рекомендуется не более 25-30.",
                line=line
            ))
        return results

    def _check_structure(self, text: str, line: int) -> list[AISuggestion]:
        results = []
        if text.startswith("#") and text.endswith("#"):
            results.append(AISuggestion(
                category="structure",
                original=text,
                suggestion="Уберите лишние # в заголовке",
                explanation="Заголовок не должен заканчиваться на #",
                line=line
            ))
        return results

    def improve_text(self, text: str, lang: str = "ru") -> str:
        """Auto-improve text based on suggestions."""
        improved = text

        for pattern, replacement, _ in self.STYLE_RULES.get(lang, []):
            improved = re.sub(pattern, replacement, improved, flags=re.IGNORECASE)

        return improved

    def generate_outline(self, text: str, lang: str = "ru") -> str:
        """Generate an outline from existing text."""
        lines = text.split("\n")
        headings: list[tuple[int, str]] = []
        content_map = {}

        current_heading = None
        current_content = []

        for line in lines:
            if line.startswith("#"):
                if current_heading:
                    content_map[current_heading] = " ".join(current_content)[:100]
                level = len(line) - len(line.lstrip("#"))
                current_heading = line.strip("# ").strip()
                headings.append((level, current_heading))
                current_content = []
            else:
                if line.strip():
                    current_content.append(line.strip())

        if current_heading:
            content_map[current_heading] = " ".join(current_content)[:100]

        if not headings:
            return ""

        outline_parts = ["## Оглавление\n"]
        for i, (level, h) in enumerate(headings, 1):
            prefix = "  " * (level - 1)
            outline_parts.append(f"{prefix}{i}. {h}")

        return "\n".join(outline_parts)


def get_ai_assistant() -> AIWritingAssistant:
    """Get singleton AI assistant instance."""
    if not hasattr(get_ai_assistant, "_instance"):
        get_ai_assistant._instance = AIWritingAssistant()
    return get_ai_assistant._instance
