"""Tests for pptx_renderer._SlideParser (regression: IndexError on content before first heading)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.pptx_renderer import _SlideParser


def test_preamble_before_first_heading():
    """Контент до первого заголовка не должен ронять парсер (ранее — IndexError)."""
    parser = _SlideParser()
    parser.feed("<p>Преамбула документа</p><h1>Первый раздел</h1><p>Текст раздела</p>")
    parser.close()
    parser._flush_content()

    assert len(parser.slides) == 2, f"Ожидалось 2 слайда, получено {len(parser.slides)}"
    assert parser.slides[0]['title'] == ''
    assert parser.slides[0]['content'] == ['Преамбула документа']
    assert parser.slides[1]['title'] == 'Первый раздел'
    assert parser.slides[1]['content'] == ['Текст раздела']


def test_only_preamble_no_headings():
    """Документ без единого заголовка — один вводный слайд, без исключений."""
    parser = _SlideParser()
    parser.feed("<p>Просто текст</p>")
    parser.close()
    parser._flush_content()

    assert len(parser.slides) == 1
    assert parser.slides[0]['title'] == ''
    assert parser.slides[0]['content'] == ['Просто текст']


def test_normal_slides_split():
    """Обычный документ: H1/H2 начинают новые слайды."""
    parser = _SlideParser()
    parser.feed("<h1>А</h1><p>один</p><h2>Б</h2><p>два</p>")
    parser.close()
    parser._flush_content()

    assert len(parser.slides) == 2
    assert parser.slides[0] == {'title': 'А', 'content': ['один']}
    assert parser.slides[1] == {'title': 'Б', 'content': ['два']}


def test_empty_document():
    """Пустой документ — ни одного слайда, без исключений."""
    parser = _SlideParser()
    parser.feed("")
    parser.close()
    parser._flush_content()

    assert parser.slides == []


def main():
    tests = [
        test_preamble_before_first_heading,
        test_only_preamble_no_headings,
        test_normal_slides_split,
        test_empty_document,
    ]
    for t in tests:
        t()
        print(f"[PASS] {t.__name__}: {t.__doc__.strip()}")
    print("\nAll pptx parser tests passed!")


if __name__ == "__main__":
    main()
