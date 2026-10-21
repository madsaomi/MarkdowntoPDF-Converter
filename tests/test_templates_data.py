"""Поведенческие тесты данных шаблонов и приветственного документа.

Покрывает:
- `src/gui/templates_data.py` — списки и содержимое шаблонов;
- `src/gui/welcome_docs.py` — приветственный Markdown;
- интеграцию шаблонов с `src/core/template_vars.py` (подстановка `{{...}}`).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.gui.templates_data import (
    PRO_TEMPLATES,
    TEMPLATES,
    get_pro_template_content,
    get_pro_template_list,
    get_template_content,
    get_template_list,
)
from src.gui.welcome_docs import WELCOME_EN, WELCOME_RU
from src.core.template_vars import (
    extract_front_matter,
    process_document_vars,
    substitute_template_vars,
)

PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")

# Встроенные переменные template_vars — они подставляются автоматически.
BUILTIN_VARS = {
    "date", "time", "datetime", "year", "month", "day",
    "title", "word_count", "author", "filename",
}


def test_get_template_list():
    """get_template_list возвращает пары (key, name) для всех шаблонов."""
    items = get_template_list()
    assert len(items) == len(TEMPLATES)
    keys = [k for k, _ in items]
    assert keys == list(TEMPLATES.keys())
    for key, name in items:
        assert isinstance(key, str) and key
        assert isinstance(name, str) and name
    print("[PASS] test_get_template_list")


def test_get_template_content():
    """get_template_content возвращает содержимое или None для неизвестного ключа."""
    for key in TEMPLATES:
        content = get_template_content(key)
        assert content is not None, key
        assert content.strip(), key
    assert get_template_content("no_such_template") is None
    print("[PASS] test_get_template_content")


def test_get_pro_template_list():
    """get_pro_template_list возвращает тройки (key, name, category)."""
    items = get_pro_template_list()
    assert len(items) == len(PRO_TEMPLATES)
    for key, name, category in items:
        assert key in PRO_TEMPLATES
        assert name == PRO_TEMPLATES[key]["name"]
        assert category == PRO_TEMPLATES[key]["category"]
    print("[PASS] test_get_pro_template_list")


def test_get_pro_template_content():
    """get_pro_template_content возвращает содержимое или None."""
    for key in PRO_TEMPLATES:
        assert get_pro_template_content(key) is not None, key
    assert get_pro_template_content("no_such_template") is None
    print("[PASS] test_get_pro_template_content")


def test_all_templates_have_front_matter_and_body():
    """Каждый шаблон начинается с front matter и содержит заголовок H1."""
    for key, tmpl in list(TEMPLATES.items()) + list(PRO_TEMPLATES.items()):
        content = tmpl["content"]
        assert content.startswith("---\n"), f"{key}: нет front matter"
        fm, body = extract_front_matter(content)
        assert fm, f"{key}: front matter пуст"
        assert "title" in fm, f"{key}: в front matter нет title"
        assert re.search(r"^#\s+\S", body, re.MULTILINE), f"{key}: нет H1"
    print("[PASS] test_all_templates_have_front_matter_and_body")


def test_template_placeholders_are_substitutable():
    """Все плейсхолдеры шаблонов имеют вид {{word}} и корректно подставляются."""
    for key, tmpl in list(TEMPLATES.items()) + list(PRO_TEMPLATES.items()):
        content = tmpl["content"]
        for ph in PLACEHOLDER_RE.findall(content):
            assert ph.isidentifier(), f"{key}: некорректный плейсхолдер {{{{{ph}}}}}"
        # Подстановка не должна ломать текст: неподставленные плейсхолдеры
        # остаются ровно в исходном виде.
        out = substitute_template_vars(content, {"name": "Иван", "email": "a@b.c"})
        for ph in set(PLACEHOLDER_RE.findall(content)):
            if ph not in ("name", "email") and ph not in BUILTIN_VARS:
                assert "{{" + ph + "}}" in out, f"{key}: потерян плейсхолдер {ph}"
    print("[PASS] test_template_placeholders_are_substitutable")


def test_process_document_vars_uses_front_matter():
    """process_document_vars подставляет значения из front matter и имя файла."""
    text = "---\ntitle: Мой док\nauthor: Иван\n---\n\n# {{title}}\n\nФайл: {{filename}}\nАвтор: {{author}}"
    out = process_document_vars(text, "myfile.md")
    assert "Мой док" in out
    assert "myfile" in out
    assert "Иван" in out
    assert "{{" not in out
    print("[PASS] test_process_document_vars_uses_front_matter")


def test_resume_template_renders_with_context():
    """Шаблон резюме подставляется контекстом без остаточных ключей."""
    content = get_template_content("resume")
    ctx = {
        "name": "Иван Иванов",
        "email": "ivan@example.com",
        "phone": "+7 999",
        "city": "Москва",
    }
    out = substitute_template_vars(content, ctx)
    for v in ctx.values():
        assert v in out
    # В шаблоне резюме используются только эти четыре переменные —
    # после подстановки не должно остаться плейсхолдеров.
    assert "{{" not in out, out[out.find("{{") - 40:out.find("{{") + 40] if "{{" in out else ""
    print("[PASS] test_resume_template_renders_with_context")


def test_welcome_docs_are_valid_markdown():
    """Оба приветственных документа — непустой Markdown с H1 и разделами."""
    for name, doc in (("RU", WELCOME_RU), ("EN", WELCOME_EN)):
        assert doc.strip(), name
        assert doc.startswith("# "), name
        assert doc.count("\n## ") >= 3, f"{name}: мало разделов"
        assert "```" in doc, f"{name}: нет блока кода"
        assert "| " in doc, f"{name}: нет таблицы"
    print("[PASS] test_welcome_docs_are_valid_markdown")


def test_welcome_docs_are_language_specific():
    """RU- и EN-версии отличаются и содержат свои маркеры."""
    assert WELCOME_RU != WELCOME_EN
    assert "Добро пожаловать" in WELCOME_RU
    assert "Welcome" in WELCOME_EN
    assert "Русский" not in WELCOME_EN
    print("[PASS] test_welcome_docs_are_language_specific")


def test_welcome_docs_have_no_unresolved_placeholders():
    """В приветственном документе нет незаполненных {{...}} плейсхолдеров."""
    for name, doc in (("RU", WELCOME_RU), ("EN", WELCOME_EN)):
        found = PLACEHOLDER_RE.findall(doc)
        assert not found, f"{name}: найдены плейсхолдеры {found}"
    print("[PASS] test_welcome_docs_have_no_unresolved_placeholders")


def main():
    tests = [
        test_get_template_list,
        test_get_template_content,
        test_get_pro_template_list,
        test_get_pro_template_content,
        test_all_templates_have_front_matter_and_body,
        test_template_placeholders_are_substitutable,
        test_process_document_vars_uses_front_matter,
        test_resume_template_renders_with_context,
        test_welcome_docs_are_valid_markdown,
        test_welcome_docs_are_language_specific,
        test_welcome_docs_have_no_unresolved_placeholders,
    ]
    for t in tests:
        t()
    print("\nAll templates/welcome docs tests passed!")


if __name__ == "__main__":
    main()
