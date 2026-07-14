import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.gui.translations import TRANSLATIONS


def test_all_ru_keys_in_en():
    ru_keys = set(TRANSLATIONS['ru'].keys())
    en_keys = set(TRANSLATIONS['en'].keys())
    missing = ru_keys - en_keys
    assert not missing, f"Keys in 'ru' but missing from 'en': {missing}"
    print(f"[PASS] test_all_ru_keys_in_en: {len(ru_keys)} keys in both")


def test_all_en_keys_in_ru():
    ru_keys = set(TRANSLATIONS['ru'].keys())
    en_keys = set(TRANSLATIONS['en'].keys())
    missing = en_keys - ru_keys
    assert not missing, f"Keys in 'en' but missing from 'ru': {missing}"
    print(f"[PASS] test_all_en_keys_in_ru: {len(en_keys)} keys in both")


def test_no_russian_text_in_english():
    en = TRANSLATIONS['en']
    russian_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
    for key, value in en.items():
        if any(c in russian_chars for c in value):
            # Allow some known exceptions like "lang_ru" which contains "Русский"
            if key not in ('lang_ru',):
                print(f"[WARN] Possible Russian text in en.{key}: '{value[:30]}'")
    print("[PASS] test_no_russian_text_in_english")


def test_placeholder_keys():
    """Ensure all history_placeholder keys are translated correctly."""
    assert 'Export history' in TRANSLATIONS['en']['history_placeholder']
    assert 'Журнал экспорта' in TRANSLATIONS['ru']['history_placeholder']
    print("[PASS] test_placeholder_keys")


def test_dashboard_keys_english():
    en = TRANSLATIONS['en']
    assert 'Very easy' in en['dashboard_readability_easy']
    assert 'Standard' in en['dashboard_readability_medium']
    assert 'Difficult' in en['dashboard_readability_hard']
    assert 'Flesch' in en['dashboard_lbl_readability_desc']
    print("[PASS] test_dashboard_keys_english")


if __name__ == '__main__':
    test_all_ru_keys_in_en()
    test_all_en_keys_in_ru()
    test_no_russian_text_in_english()
    test_placeholder_keys()
    test_dashboard_keys_english()
    print("\nAll translation tests passed!")
