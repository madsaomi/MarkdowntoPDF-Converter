"""Поведенческие тесты диалога «О программе» (gui/about_dialog).

Проверяет заголовок, локализацию описания, версию и наличие ссылок.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QLabel, QPushButton

app = QApplication.instance() or QApplication([])

from src.gui.about_dialog import AboutDialog


def _labels(dialog):
    return [lbl.text() for lbl in dialog.findChildren(QLabel)]


def test_about_dialog_title_by_lang():
    """Заголовок окна зависит от языка."""
    d_ru = AboutDialog(version="2.5.0", lang="ru")
    d_en = AboutDialog(version="2.5.0", lang="en")
    assert "О программе" in d_ru.windowTitle()
    assert d_en.windowTitle() == "About", d_en.windowTitle()
    d_ru.close()
    d_en.close()
    print("[PASS] test_about_dialog_title_by_lang")


def test_about_dialog_shows_version():
    """Версия отображается в интерфейсе."""
    d = AboutDialog(version="3.1.4", lang="ru")
    labels = " | ".join(_labels(d))
    assert "3.1.4" in labels, labels
    d.close()
    print("[PASS] test_about_dialog_shows_version")


def test_about_dialog_description_is_localized():
    """Описание диалога переведено."""
    d_ru = AboutDialog(version="1.0", lang="ru")
    d_en = AboutDialog(version="1.0", lang="en")
    ru_text = " | ".join(_labels(d_ru))
    en_text = " | ".join(_labels(d_en))
    assert "Современный конвертер" in ru_text, ru_text
    assert "A modern Markdown converter" in en_text, en_text
    d_ru.close()
    d_en.close()
    print("[PASS] test_about_dialog_description_is_localized")


def test_about_dialog_shows_stats():
    """Показаны счётчики функций, форматов и инструментов."""
    d = AboutDialog(version="1.0", lang="ru")
    labels = " | ".join(_labels(d))
    assert "69+" in labels, labels
    assert "Features" in labels, labels
    d.close()
    print("[PASS] test_about_dialog_shows_stats")


def test_about_dialog_has_close_button():
    """Есть кнопка закрытия, подписанная по языку."""
    d_ru = AboutDialog(version="1.0", lang="ru")
    d_en = AboutDialog(version="1.0", lang="en")
    ru_buttons = [b.text() for b in d_ru.findChildren(QPushButton)]
    en_buttons = [b.text() for b in d_en.findChildren(QPushButton)]
    assert "Закрыть" in ru_buttons, ru_buttons
    assert "Close" in en_buttons, en_buttons
    d_ru.close()
    d_en.close()
    print("[PASS] test_about_dialog_has_close_button")


def test_about_dialog_has_external_links():
    """Есть кликабельные ссылки на GitHub и документацию."""
    d = AboutDialog(version="1.0", lang="ru")
    links = [lbl.text() for lbl in d.findChildren(QLabel) if "href" in lbl.text()]
    assert any("github.com" in t for t in links), links
    assert any("docs.python.org" in t for t in links), links
    d.close()
    print("[PASS] test_about_dialog_has_external_links")


def main():
    tests = [
        test_about_dialog_title_by_lang,
        test_about_dialog_shows_version,
        test_about_dialog_description_is_localized,
        test_about_dialog_shows_stats,
        test_about_dialog_has_close_button,
        test_about_dialog_has_external_links,
    ]
    for t in tests:
        t()
    print("\nAll about-dialog tests passed!")


if __name__ == "__main__":
    main()
