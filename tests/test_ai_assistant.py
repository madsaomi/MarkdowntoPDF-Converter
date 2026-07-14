import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.ai_assistant import AIWritingAssistant, AISuggestion

ai = AIWritingAssistant()


def test_analyze_returns_list():
    result = ai.analyze("Some text here", "en")
    assert isinstance(result, list)
    print("[PASS] test_analyze_returns_list")


def test_grammar_russian():
    result = ai.analyze("очень очень много", "ru")
    assert any(s.explanation and "очень" in s.explanation for s in result)
    print("[PASS] test_grammar_russian")


def test_grammar_english_i():
    result = ai.analyze("i think this is wrong", "en")
    assert any(s.category == "grammar" for s in result)
    print("[PASS] test_grammar_english_i")


def test_style_russian():
    result = ai.analyze("в настоящее время", "ru")
    assert any(s.category == "style" for s in result)
    print("[PASS] test_style_russian")


def test_style_english():
    result = ai.analyze("in order to improve", "en")
    assert any(s.category == "style" for s in result)
    print("[PASS] test_style_english")


def test_style_replacement_works():
    improved = ai.improve_text("in order to test this", "en")
    assert "in order to" not in improved
    assert "to" in improved
    print(f"[PASS] test_style_replacement_works: '{improved}'")


def test_style_replacement_russian():
    improved = ai.improve_text("для того чтобы проверить", "ru")
    assert "для того чтобы" not in improved
    assert "чтобы" in improved
    print(f"[PASS] test_style_replacement_russian: '{improved}'")


def test_style_replacement_no_change():
    improved = ai.improve_text("hello world", "en")
    assert improved == "hello world"
    print(f"[PASS] test_style_replacement_no_change")


def test_readability_long_sentence():
    long_text = "word " * 35
    result = ai.analyze(long_text, "en")
    assert any(s.category == "readability" for s in result)
    print("[PASS] test_readability_long_sentence")


def test_structure_bad_header():
    result = ai.analyze("# heading #", "ru")
    assert any(s.category == "structure" for s in result)
    print("[PASS] test_structure_bad_header")


def test_generate_outline():
    text = "# Intro\nSome text\n# Body\nMore text"
    outline = ai.generate_outline(text)
    assert "Intro" in outline
    assert "Body" in outline
    assert outline.startswith("## ")
    print(f"[PASS] test_generate_outline")


def test_generate_outline_empty():
    text = "No headings here"
    outline = ai.generate_outline(text)
    assert outline == ""
    print("[PASS] test_generate_outline_empty")


def test_generate_outline_nested():
    text = "# Top\n# Sub\n## Detail"
    outline = ai.generate_outline(text)
    assert "Top" in outline
    assert "Sub" in outline
    print(f"[PASS] test_generate_outline_nested")


def test_suggestion_dataclass():
    s = AISuggestion(category="grammar", original="bad", suggestion="good", explanation="fix", line=5)
    assert s.category == "grammar"
    assert s.line == 5
    assert s.suggestion == "good"
    print("[PASS] test_suggestion_dataclass")


if __name__ == '__main__':
    test_analyze_returns_list()
    test_grammar_russian()
    test_grammar_english_i()
    test_style_russian()
    test_style_english()
    test_style_replacement_works()
    test_style_replacement_russian()
    test_style_replacement_no_change()
    test_readability_long_sentence()
    test_structure_bad_header()
    test_generate_outline()
    test_generate_outline_empty()
    test_generate_outline_nested()
    test_suggestion_dataclass()
    print("\nAll AI assistant tests passed!")
