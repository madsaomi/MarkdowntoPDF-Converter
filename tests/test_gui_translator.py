"""Поведенческие тесты обёртки перевода GUI (gui/translator).

Проверяет хранение языка, метод t() с подстановкой аргументов, fallback
на ключ при отсутствии перевода и обработку ошибок формата.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.gui import translator as tr
from src.gui.translator import Translator


def test_translator_default_lang_ru():
    """Translator по умолчанию использует русский язык."""
    t = Translator()
    assert t.lang == "ru"
    print("[PASS] test_translator_default_lang_ru")


def test_translator_set_lang_changes_language():
    """set_lang переключает язык."""
    t = Translator("ru")
    t.set_lang("en")
    assert t.lang == "en"
    print("[PASS] test_translator_set_lang_changes_language")


def test_t_returns_translation_from_translations():
    """t() возвращает перевод из TRANSLATIONS для текущего языка."""
    t = Translator("ru")
    assert t.t("btn_cancel") == "🛑 Отмена"
    assert t.t("btn_convert") == "⚡ Конвертировать в {}"
    print("[PASS] test_t_returns_translation_from_translations")


def test_t_formats_with_args():
    """t() подставляет аргументы в строку перевода."""
    t = Translator("ru")
    s = t.t("btn_convert", "PDF")
    assert s == "⚡ Конвертировать в PDF", s
    s = t.t("files_selected", 2, "5 МБ")
    assert s == "Выбрано файлов: 2 (5 МБ)", s
    print("[PASS] test_t_formats_with_args")


def test_t_falls_back_to_key_when_missing():
    """Если перевод отсутствует — возвращается сам ключ."""
    t = Translator("ru")
    assert t.t("nonexistent_key_xyz") == "nonexistent_key_xyz"
    t2 = Translator("en")
    assert t2.t("another_missing_key") == "another_missing_key"
    print("[PASS] test_t_falls_back_to_key_when_missing")


def test_t_survives_format_errors():
    """При ошибке форматирования (неверное число аргументов) возвращается сырой текст."""
    t = Translator("ru")
    # btn_convert ожидает 1 аргумент, передаём 0
    s = t.t("btn_convert")
    assert s == "⚡ Конвертировать в {}", s
    s = t.t("btn_convert", 1, 2)
    # IndexError при отсутствии плейсхолдера/лишних аргументах — fallback
    assert isinstance(s, str)
    print("[PASS] test_t_survives_format_errors")


def main():
    tests = [
        test_translator_default_lang_ru,
        test_translator_set_lang_changes_language,
        test_t_returns_translation_from_translations,
        test_t_formats_with_args,
        test_t_falls_back_to_key_when_missing,
        test_t_survives_format_errors,
    ]
    for test in tests:
        test()
    print("\nAll GUI translator tests passed!")


if __name__ == "__main__":
    main()
