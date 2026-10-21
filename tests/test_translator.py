"""Поведенческие тесты модуля перевода документов (core/translator).

Проверяет словарь перевода, сохранение форматирования Markdown, определение
языка, списки языков/пар, синглтон get_translator().
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.translator import (
    DocumentTranslator,
    TranslationLanguage,
    TranslationResult,
    get_translator,
)


def test_translation_result_dataclass():
    """TranslationResult хранит поля и значение confidence по умолчанию."""
    r = TranslationResult("a", "b", "ru", "en")
    assert r.original == "a"
    assert r.translated == "b"
    assert r.source_lang == "ru"
    assert r.target_lang == "en"
    assert r.confidence == 1.0
    print("[PASS] test_translation_result_dataclass")


def test_same_language_returns_original_with_full_confidence():
    """При одинаковых языках перевод возвращает исходный текст, confidence 1.0."""
    t = DocumentTranslator()
    r = t.translate_text("Привет мир", "ru", "ru")
    assert r.translated == "Привет мир"
    assert r.confidence == 1.0
    print("[PASS] test_same_language_returns_original_with_full_confidence")


def test_dict_translation_preserves_capitalization_and_punctuation():
    """Словарный перевод сохраняет заглавную букву и знаки препинания."""
    t = DocumentTranslator()
    assert t.translate_text("Привет мир", "ru", "en").translated == "Hello world"
    assert t.translate_text("Файл текст", "ru", "en").translated == "File text"
    assert t.translate_text("текст, файл.", "ru", "en").translated == "text, file."
    print("[PASS] test_dict_translation_preserves_capitalization_and_punctuation")


def test_unknown_words_kept_as_is():
    """Неизвестные слова остаются без изменений, известные переводятся."""
    t = DocumentTranslator()
    assert t.translate_text("текст xyzzy", "ru", "en").translated == "text xyzzy"
    assert t.translate_text("hello unknown", "en", "ru").translated == "привет unknown"
    print("[PASS] test_unknown_words_kept_as_is")


def test_unsupported_pair_returns_original_text():
    """Для неподдерживаемой пары словарём возвращается исходный текст."""
    t = DocumentTranslator()
    assert t.translate_text("hello", "en", "de").translated == "hello"
    assert t.translate_text("привет", "ru", "ja").translated == "привет"
    print("[PASS] test_unsupported_pair_returns_original_text")


def test_translate_markdown_preserves_formatting():
    """translate_markdown сохраняет заголовки, списки, цитаты, таблицы."""
    t = DocumentTranslator()
    md = (
        "# Заголовок\n\n"
        "- текст\n"
        "- файл\n\n"
        "> документ\n\n"
        "| код | текст |\n"
        "| --- | --- |\n\n"
        "обычный текст\n"
    )
    out = t.translate_markdown(md, "ru", "en")
    assert out.startswith("# Heading"), out
    assert "- text\n" in out
    assert "- file\n" in out
    assert "> document\n" in out
    assert "| code | text |" in out
    assert "| --- | --- |" in out  # разделитель таблицы не переводится
    assert "\nобычный text\n" in out or out.endswith("\nобычный text")
    print("[PASS] test_translate_markdown_preserves_formatting")


def test_detect_language():
    """detect_language определяет русский по кириллице, английский по словам."""
    t = DocumentTranslator()
    assert t.detect_language("Это русский текст документ") == "ru"
    assert t.detect_language("the file is here and it was") == "en"
    assert t.detect_language("xyz") == "en"
    print("[PASS] test_detect_language")


def test_get_supported_languages_and_pairs():
    """Списки языков и пар перевода корректны."""
    t = DocumentTranslator()
    langs = t.get_supported_languages()
    assert len(langs) == len(TranslationLanguage)
    assert {"code": "ru", "name": "RUSSIAN"} in langs
    pairs = t.get_translation_pairs()
    assert len(pairs) == len(TranslationLanguage) * (len(TranslationLanguage) - 1)
    assert {"source": "ru", "target": "en"} in pairs
    assert all(p["source"] != p["target"] for p in pairs)
    print("[PASS] test_get_supported_languages_and_pairs")


def test_get_translator_is_singleton():
    """get_translator возвращает один и тот же экземпляр."""
    a = get_translator()
    b = get_translator()
    assert a is b
    assert isinstance(a, DocumentTranslator)
    print("[PASS] test_get_translator_is_singleton")


def main():
    tests = [
        test_translation_result_dataclass,
        test_same_language_returns_original_with_full_confidence,
        test_dict_translation_preserves_capitalization_and_punctuation,
        test_unknown_words_kept_as_is,
        test_unsupported_pair_returns_original_text,
        test_translate_markdown_preserves_formatting,
        test_detect_language,
        test_get_supported_languages_and_pairs,
        test_get_translator_is_singleton,
    ]
    for t in tests:
        t()
    print("\nAll translator tests passed!")


if __name__ == "__main__":
    main()
