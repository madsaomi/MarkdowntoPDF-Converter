from src.gui.translations import TRANSLATIONS


class Translator:
    """Centralized UI translation helper with format support."""

    def __init__(self, lang: str = "ru"):
        self.lang = lang

    def set_lang(self, lang: str):
        self.lang = lang

    def t(self, key: str, *args) -> str:
        text = TRANSLATIONS.get(self.lang, {}).get(key, key)
        if args:
            try:
                return text.format(*args)
            except (KeyError, IndexError, AttributeError):
                return text
        return text
