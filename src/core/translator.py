"""Document Translation Engine - Translate Markdown documents."""

import re
import logging
from dataclasses import dataclass
from typing import Optional
from enum import Enum

logger = logging.getLogger("MarkdownToPDF.translator")


class TranslationLanguage(Enum):
    RUSSIAN = "ru"
    ENGLISH = "en"
    GERMAN = "de"
    FRENCH = "fr"
    SPANISH = "es"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    ARABIC = "ar"
    HINDI = "hi"
    TURKISH = "tr"
    DUTCH = "nl"
    POLISH = "pl"
    UKRAINIAN = "uk"


@dataclass
class TranslationResult:
    """Translation result."""
    original: str
    translated: str
    source_lang: str
    target_lang: str
    confidence: float = 1.0


class DocumentTranslator:
    """Document translator for Markdown content."""

    def __init__(self):
        self.supported_languages = [lang.value for lang in TranslationLanguage]

        # Common translations dictionary (offline fallback)
        self._common_words = {
            ("ru", "en"): {
                "привет": "hello",
                "мир": "world",
                "документ": "document",
                "файл": "file",
                "текст": "text",
                "заголовок": "heading",
                "список": "list",
                "таблица": "table",
                "код": "code",
                "ссылка": "link",
                "изображение": "image",
                "заметки": "notes",
                "проект": "project",
                "задача": "task",
                "встреча": "meeting",
                "отчёт": "report",
                "дата": "date",
                "время": "time",
                "автор": "author",
                "название": "title",
                "описание": "description",
                "содержание": "content",
                "введение": "introduction",
                "заключение": "conclusion",
            },
            ("en", "ru"): {
                "hello": "привет",
                "world": "мир",
                "document": "документ",
                "file": "файл",
                "text": "текст",
                "heading": "заголовок",
                "list": "список",
                "table": "таблица",
                "code": "код",
                "link": "ссылка",
                "image": "изображение",
                "notes": "заметки",
                "project": "проект",
                "task": "задача",
                "meeting": "встреча",
                "report": "отчёт",
                "date": "дата",
                "time": "время",
                "author": "автор",
                "title": "название",
                "description": "описание",
                "content": "содержание",
                "introduction": "введение",
                "conclusion": "заключение",
            },
        }

        # Pre-compute reverse lookups to avoid rebuilding dict on each call
        self._reverse_cache: dict[tuple[str, str], dict[str, str]] = {}
        for (src, tgt), mapping in self._common_words.items():
            self._reverse_cache[(tgt, src)] = {v: k for k, v in mapping.items()}

    def translate_text(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        """Translate text between languages."""
        if source_lang == target_lang:
            return TranslationResult(text, text, source_lang, target_lang)

        # Try using translation dictionary
        translated = self._translate_with_dict(text, source_lang, target_lang)

        return TranslationResult(
            original=text,
            translated=translated,
            source_lang=source_lang,
            target_lang=target_lang,
            confidence=0.8
        )

    def _translate_with_dict(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using built-in dictionary."""
        dict_key = (source_lang, target_lang)

        word_dict = self._common_words.get(dict_key)
        if word_dict is None:
            word_dict = self._reverse_cache.get(dict_key, {})

        if not word_dict:
            return text

        # Simple word-by-word translation
        words = text.split()
        translated_words = []
        for word in words:
            lower_word = word.lower().strip('.,!?;:')
            if lower_word in word_dict:
                translated = word_dict[lower_word]
                # Preserve capitalization
                if word[0].isupper():
                    translated = translated.capitalize()
                # Preserve punctuation
                if word[-1] in '.,!?;:':
                    translated += word[-1]
                translated_words.append(translated)
            else:
                translated_words.append(word)

        return ' '.join(translated_words)

    def translate_markdown(self, markdown: str, source_lang: str, target_lang: str) -> str:
        """Translate Markdown document preserving formatting."""
        lines = markdown.split('\n')
        translated_lines = []

        for line in lines:
            # Preserve Markdown formatting
            if line.startswith('#'):
                # Translate heading text
                heading_match = re.match(r'^(#{1,6})\s+(.*)', line)
                if heading_match:
                    level = heading_match.group(1)
                    text = heading_match.group(2)
                    result = self.translate_text(text, source_lang, target_lang)
                    translated_lines.append(f"{level} {result.translated}")
                else:
                    translated_lines.append(line)
            elif line.startswith('- ') or line.startswith('* '):
                # Translate list items
                prefix = line[:2]
                text = line[2:]
                result = self.translate_text(text, source_lang, target_lang)
                translated_lines.append(f"{prefix}{result.translated}")
            elif line.startswith('> '):
                # Translate blockquotes
                text = line[2:]
                result = self.translate_text(text, source_lang, target_lang)
                translated_lines.append(f"> {result.translated}")
            elif '|' in line:
                # Translate table cells
                cells = line.split('|')
                translated_cells = []
                for cell in cells:
                    if cell.strip() and not re.match(r'^[-:]+$', cell.strip()):
                        result = self.translate_text(cell.strip(), source_lang, target_lang)
                        translated_cells.append(f" {result.translated} ")
                    else:
                        translated_cells.append(cell)
                translated_lines.append('|'.join(translated_cells))
            elif line.strip():
                # Translate regular text
                result = self.translate_text(line, source_lang, target_lang)
                translated_lines.append(result.translated)
            else:
                translated_lines.append(line)

        return '\n'.join(translated_lines)

    def detect_language(self, text: str) -> str:
        """Simple language detection based on common words."""
        text_lower = text.lower()

        # Check for Russian characters
        cyrillic_count = sum(1 for c in text if '\u0400' <= c <= '\u04ff')
        if cyrillic_count > len(text) * 0.3:
            return "ru"

        # Check for common English words
        english_words = ["the", "is", "are", "was", "were", "have", "has", "had", "will", "would"]
        english_count = sum(1 for word in english_words if word in text_lower.split())
        if english_count > 2:
            return "en"

        # Default to English
        return "en"

    def get_supported_languages(self) -> list[dict]:
        """Get list of supported languages."""
        return [
            {"code": lang.value, "name": lang.name}
            for lang in TranslationLanguage
        ]

    def get_translation_pairs(self) -> list[dict]:
        """Get available translation pairs."""
        pairs = []
        for source in TranslationLanguage:
            for target in TranslationLanguage:
                if source != target:
                    pairs.append({
                        "source": source.value,
                        "target": target.value,
                    })
        return pairs


def get_translator() -> DocumentTranslator:
    """Get singleton translator instance."""
    if not hasattr(get_translator, "_instance"):
        get_translator._instance = DocumentTranslator()
    return get_translator._instance
