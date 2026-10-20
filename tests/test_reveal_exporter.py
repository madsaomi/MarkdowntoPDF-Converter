"""Тесты экспорта Reveal.js (PLAN-005/TASK-005).

`export_reveal_js` не требует внешних библиотек — только stdlib.
Проверяем разбиение на слайды, атрибут языка, титульный слайд и запись файла.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.reveal_exporter import export_reveal_js


def test_slides_split_by_headings():
    """Каждый H1/H2 становится отдельным слайдом."""
    html = "<h1>Слайд 1</h1><p>тело 1</p><h2>Слайд 2</h2><p>тело 2</p>"
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "deck.html")
        count = export_reveal_js(html, {"title": "Моя презентация"}, out)
        assert count == 2, f"Ожидалось 2 слайда, получено {count}"
        content = open(out, encoding="utf-8").read()
        assert "<h1>Слайд 1</h1>" in content
        assert "<h2>Слайд 2</h2>" in content
        assert content.count("<section>") == 3, "титул + 2 слайда"
    print("[PASS] test_slides_split_by_headings")


def test_no_headings_single_slide():
    """Документ без заголовков — один слайд из всего контента."""
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "deck.html")
        count = export_reveal_js("<p>просто текст</p>", {"title": "T"}, out)
        assert count == 1, count
    print("[PASS] test_no_headings_single_slide")


def test_lang_attribute_and_title():
    """Атрибут lang пробрасывается, title попадает в <title>."""
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "deck.html")
        export_reveal_js("<h1>A</h1>", {"title": "Заголовок"}, out, lang="en")
        content = open(out, encoding="utf-8").read()
        assert '<html lang="en">' in content
        assert "<title>Заголовок</title>" in content
    print("[PASS] test_lang_attribute_and_title")


def test_creates_output_directory():
    """Отсутствующий каталог вывода создаётся."""
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "nested", "deep", "deck.html")
        export_reveal_js("<h1>A</h1>", {"title": "T"}, out)
        assert os.path.exists(out)
    print("[PASS] test_creates_output_directory")


def test_author_rendered():
    """Автор из метаданных попадает на титульный слайд."""
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "deck.html")
        export_reveal_js("<h1>A</h1>", {"title": "T", "author": "Иван"}, out)
        content = open(out, encoding="utf-8").read()
        assert "<p>Иван</p>" in content
    print("[PASS] test_author_rendered")


def main():
    tests = [
        test_slides_split_by_headings,
        test_no_headings_single_slide,
        test_lang_attribute_and_title,
        test_creates_output_directory,
        test_author_rendered,
    ]
    for t in tests:
        t()
    print("\nAll reveal exporter tests passed!")


if __name__ == "__main__":
    main()
