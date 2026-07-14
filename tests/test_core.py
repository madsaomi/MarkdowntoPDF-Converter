import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.flashcards import extract_flashcards, cards_to_anki, cards_to_markdown
from src.core.glossary import extract_definitions, glossary_to_markdown
from src.core.quiz_generator import generate_quiz_from_text, quiz_to_markdown
from src.core.latex_preview import find_latex_expressions, validate_latex
from src.core.html_to_markdown import html_to_markdown
from src.core.template_vars import substitute_template_vars, extract_front_matter
from src.core.pdf_encrypt import encrypt_pdf


def test_flashcards_extract():
    text = "# Question 1\nAnswer text\n## Question 2\nAnswer 2"
    cards = extract_flashcards(text)
    assert len(cards) >= 2
    assert cards[0]['front'] == 'Question 1'
    print("[PASS] test_flashcards_extract")


def test_flashcards_anki():
    cards = [{'front': 'Q', 'back': 'A'}]
    tsv = cards_to_anki(cards)
    assert 'Q\tA' in tsv
    print("[PASS] test_flashcards_anki")


def test_glossary_extract():
    text = "**Term**: Definition here"
    defs = extract_definitions(text)
    assert len(defs) >= 1
    assert defs[0]['term'] == 'Term'
    print("[PASS] test_glossary_extract")


def test_quiz_generation():
    text = "# Topic 1\n- item 1\n- item 2\n- item 3\n\n# Topic 2\n- option a"
    quiz = generate_quiz_from_text(text)
    assert 'total' in quiz
    assert quiz['total'] > 0
    for q in quiz['questions']:
        for opt in q['options']:
            assert 'Option B' not in opt, f"Hardcoded distractor found: {opt}"
    print(f"[PASS] test_quiz_generation: {quiz['total']} questions, no hardcoded distractors")


def test_latex_find():
    text = "Inline $a^2 + b^2$ and block $$\\int$$ math"
    results = find_latex_expressions(text)
    assert len(results) >= 2
    print(f"[PASS] test_latex_find: {len(results)} expressions")


def test_latex_validate():
    valid, msg = validate_latex("{valid}")
    assert valid
    print("[PASS] test_latex_validate_valid")

    invalid, msg = validate_latex("{unclosed")
    assert not invalid
    print("[PASS] test_latex_validate_invalid")


def test_html_to_markdown():
    html = "<h1>Title</h1><p>Text with <strong>bold</strong></p>"
    md = html_to_markdown(html)
    assert "# Title" in md
    assert "**bold**" in md
    print("[PASS] test_html_to_markdown")


def test_template_vars():
    result = substitute_template_vars("Hello {{name}}!", {"name": "World"})
    assert result == "Hello World!"
    print("[PASS] test_template_vars")


def test_front_matter():
    vars_dict, content = extract_front_matter("---\ntitle: Test\n---\nBody")
    assert vars_dict.get('title') == 'Test'
    assert content == 'Body'
    print("[PASS] test_front_matter")


def test_encrypt_pdf_nonexistent():
    # Should return False for non-existent file, not crash
    result = encrypt_pdf("nonexistent.pdf", "password")
    assert result is False
    print("[PASS] test_encrypt_pdf_nonexistent")


if __name__ == '__main__':
    test_flashcards_extract()
    test_flashcards_anki()
    test_glossary_extract()
    test_quiz_generation()
    test_latex_find()
    test_latex_validate()
    test_html_to_markdown()
    test_template_vars()
    test_front_matter()
    test_encrypt_pdf_nonexistent()
    print("\nAll core tests passed!")
