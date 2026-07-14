import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.template_vars import substitute_template_vars, extract_front_matter, process_document_vars


def test_substitute_simple():
    result = substitute_template_vars("Hello {{name}}!", {"name": "World"})
    assert result == "Hello World!"
    print("[PASS] test_substitute_simple")


def test_substitute_builtin_date():
    result = substitute_template_vars("Date: {{date}}")
    assert "Date: 20" in result  # starts with 20xx
    print(f"[PASS] test_substitute_builtin_date: {result}")


def test_substitute_builtin_year():
    result = substitute_template_vars("Year: {{year}}")
    assert "Year: 20" in result
    print(f"[PASS] test_substitute_builtin_year: {result}")


def test_substitute_word_count():
    result = substitute_template_vars("Words: {{word_count}}")
    assert "Words: " in result
    count = int(result.split(": ")[1])
    assert count > 0
    print(f"[PASS] test_substitute_word_count: {result}")


def test_substitute_unknown_var():
    result = substitute_template_vars("{{unknown_var}}")
    assert result == "{{unknown_var}}"  # unchanged
    print("[PASS] test_substitute_unknown_var")


def test_extract_front_matter_basic():
    vars_dict, content = extract_front_matter("---\ntitle: Test\nauthor: Me\n---\n\nBody text")
    assert vars_dict.get('title') == 'Test'
    assert vars_dict.get('author') == 'Me'
    assert content == 'Body text'
    print("[PASS] test_extract_front_matter_basic")


def test_extract_front_matter_no_fm():
    vars_dict, content = extract_front_matter("No front matter here")
    assert vars_dict == {}
    assert content == "No front matter here"
    print("[PASS] test_extract_front_matter_no_fm")


def test_extract_front_matter_missing_end():
    vars_dict, content = extract_front_matter("---\ntitle: Test\nNo closing marker")
    assert vars_dict == {}
    assert "title" not in vars_dict
    print("[PASS] test_extract_front_matter_missing_end")


def test_process_document_vars():
    result = process_document_vars("---\ntitle: MyDoc\n---\n\n{{title}} is here")
    assert "MyDoc is here" in result
    print(f"[PASS] test_process_document_vars: {result}")


def test_substitute_empty_context():
    result = substitute_template_vars("Hello {{name}}!", {})
    assert "{{name}}" in result  # not replaced
    print("[PASS] test_substitute_empty_context")


if __name__ == '__main__':
    test_substitute_simple()
    test_substitute_builtin_date()
    test_substitute_builtin_year()
    test_substitute_word_count()
    test_substitute_unknown_var()
    test_extract_front_matter_basic()
    test_extract_front_matter_no_fm()
    test_extract_front_matter_missing_end()
    test_process_document_vars()
    test_substitute_empty_context()
    print("\nAll template vars tests passed!")
