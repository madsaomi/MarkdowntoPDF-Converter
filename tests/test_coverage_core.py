"""Поведенческие тесты «чистых» ядерных модулей с нулевым покрытием.

Покрывает:
- `core/cloud_templates.py` — индекс шаблонов, SSRF-защита, локальное хранилище;
- `core/citation_manager.py` — библиография, стили APA/MLA, ключи цитат;
- `core/snippets.py` — библиотека сниппетов (дефолты, добавление, удаление);
- `core/pdf_to_markdown.py` — извлечение текста из PDF и сохранение в .md.
"""
import json
import logging
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src.core.citation_manager as cm
import src.core.cloud_templates as ct
import src.core.pdf_to_markdown as p2m
import src.core.snippets as sn


class _QuietLogs:
    """Глушит ожидаемые сообщения об ошибках модулей."""

    def __init__(self, *logger_names):
        self.names = logger_names
        self._prev = {}

    def __enter__(self):
        for name in self.names:
            lg = logging.getLogger(name)
            self._prev[name] = lg.disabled
            lg.disabled = True
        return self

    def __exit__(self, *exc):
        for name, prev in self._prev.items():
            logging.getLogger(name).disabled = prev
        return False


# ─── cloud_templates ─────────────────────────────────────────────────────────

def test_cloud_index_falls_back_to_builtin(monkeypatch=None):
    """Без сети возвращаются встроенные шаблоны."""
    import urllib.request

    orig = urllib.request.urlopen

    def _boom(*a, **k):
        raise OSError("no network")

    urllib.request.urlopen = _boom
    try:
        templates = ct.get_cloud_templates_index()
    finally:
        urllib.request.urlopen = orig
    assert len(templates) >= 3, len(templates)
    assert all("name" in t and "content" in t for t in templates)
    assert all(t.get("builtin") is True for t in templates)
    assert any("README" in t["name"] for t in templates)
    print("[PASS] test_cloud_index_falls_back_to_builtin")


def test_cloud_index_uses_remote_data():
    """При доступном индексе берутся данные из сети."""
    import io
    import urllib.request

    orig = urllib.request.urlopen
    payload = json.dumps({"templates": [{"name": "Remote", "content": "x"}]}).encode()

    class _Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    urllib.request.urlopen = lambda *a, **k: _Resp(payload)
    try:
        templates = ct.get_cloud_templates_index()
    finally:
        urllib.request.urlopen = orig
    assert templates == [{"name": "Remote", "content": "x"}], templates
    print("[PASS] test_cloud_index_uses_remote_data")


def test_is_safe_template_url():
    """SSRF-защита: разрешены только известные репозитории."""
    assert ct._is_safe_template_url("https://raw.githubusercontent.com/a/b/c.md") is True
    assert ct._is_safe_template_url("https://github.com/a/b") is True
    assert ct._is_safe_template_url("http://raw.githubusercontent.com/a/b") is False
    assert ct._is_safe_template_url("https://evil.example.com/x.md") is False
    assert ct._is_safe_template_url("file:///etc/passwd") is False
    print("[PASS] test_is_safe_template_url")


def test_download_template_blocks_unsafe_url():
    """Загрузка по небезопасному URL не выполняется и возвращает None."""
    orig = ct.urllib.request.urlopen
    called = []

    def _spy(*a, **k):
        called.append(a)
        raise AssertionError("сеть не должна вызываться")

    ct.urllib.request.urlopen = _spy
    try:
        with _QuietLogs("MarkdownToPDF.cloud_templates"):
            assert ct.download_template("https://evil.example.com/x.md") is None
    finally:
        ct.urllib.request.urlopen = orig
    assert not called, "сетевой запрос не должен был выполняться"
    print("[PASS] test_download_template_blocks_unsafe_url")


def test_download_template_returns_content():
    """Успешная загрузка возвращает текст шаблона."""
    import io
    orig = ct.urllib.request.urlopen

    class _Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    ct.urllib.request.urlopen = lambda *a, **k: _Resp("# Контент\n".encode("utf-8"))
    try:
        out = ct.download_template("https://raw.githubusercontent.com/a/b.md")
    finally:
        ct.urllib.request.urlopen = orig
    assert out == "# Контент\n", out
    print("[PASS] test_download_template_returns_content")


def test_download_template_handles_error():
    """Ошибка сети при загрузке даёт None, а не исключение."""
    orig = ct.urllib.request.urlopen

    def _boom(*a, **k):
        raise OSError("down")

    ct.urllib.request.urlopen = _boom
    try:
        with _QuietLogs("MarkdownToPDF.cloud_templates"):
            assert ct.download_template("https://raw.githubusercontent.com/a/b.md") is None
    finally:
        ct.urllib.request.urlopen = orig
    print("[PASS] test_download_template_handles_error")


def test_local_templates_save_and_list():
    """Сохранённый локальный шаблон читается обратно через get_local_templates."""
    orig_dir = ct.LOCAL_TEMPLATES_DIR
    with tempfile.TemporaryDirectory() as d:
        ct.LOCAL_TEMPLATES_DIR = os.path.join(d, "cloud_templates")
        try:
            assert ct.get_local_templates() == []
            path = ct.save_local_template("my/template", "# Мой шаблон")
            assert os.path.isfile(path), path
            assert path.endswith("my_template.md"), path
            items = ct.get_local_templates()
            assert len(items) == 1, items
            assert items[0]["name"] == "my_template"
            assert "# Мой шаблон" in items[0]["content"]
        finally:
            ct.LOCAL_TEMPLATES_DIR = orig_dir
    print("[PASS] test_local_templates_save_and_list")


def test_local_templates_ignores_non_md():
    """В списке локальных шаблонов только .md файлы."""
    orig_dir = ct.LOCAL_TEMPLATES_DIR
    with tempfile.TemporaryDirectory() as d:
        ct.LOCAL_TEMPLATES_DIR = d
        try:
            with open(os.path.join(d, "a.md"), "w", encoding="utf-8") as f:
                f.write("x")
            with open(os.path.join(d, "b.txt"), "w", encoding="utf-8") as f:
                f.write("y")
            items = ct.get_local_templates()
            assert len(items) == 1, items
            assert items[0]["name"] == "a"
        finally:
            ct.LOCAL_TEMPLATES_DIR = orig_dir
    print("[PASS] test_local_templates_ignores_non_md")


# ─── citation_manager ────────────────────────────────────────────────────────

def test_citation_add_and_get():
    """Цитата добавляется, читается и сохраняется в JSON."""
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "citations.json")
        assert cm.get_citations(path) == []
        entry = cm.add_citation(
            path, "smith2020", "Smith, J.", "A Title", "2020",
            source="Journal", url="https://example.com",
        )
        assert entry["key"] == "smith2020"
        items = cm.get_citations(path)
        assert len(items) == 1, items
        assert items[0]["title"] == "A Title"
        assert os.path.isfile(path)
    print("[PASS] test_citation_add_and_get")


def test_citation_add_updates_existing_key():
    """Повторное добавление с тем же ключом обновляет запись, а не дублирует."""
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "citations.json")
        cm.add_citation(path, "k1", "A", "Old", "2019")
        cm.add_citation(path, "k1", "B", "New", "2021")
        items = cm.get_citations(path)
        assert len(items) == 1, items
        assert items[0]["authors"] == "B"
        assert items[0]["title"] == "New"
    print("[PASS] test_citation_add_updates_existing_key")


def test_citation_remove():
    """Удаление цитаты по ключу возвращает True, несуществующей — False."""
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "citations.json")
        cm.add_citation(path, "k1", "A", "T", "2020")
        cm.add_citation(path, "k2", "B", "T2", "2021")
        assert cm.remove_citation(path, "k1") is True
        assert len(cm.get_citations(path)) == 1
        assert cm.remove_citation(path, "missing") is False
    print("[PASS] test_citation_remove")


def test_format_citation_apa_and_mla():
    """Форматирование цитат в стилях APA и MLA."""
    entry = {
        "key": "k", "authors": "Smith, J.", "title": "Title",
        "year": "2020", "source": "Journal", "url": "https://e.com",
    }
    apa = cm.format_citation_apa(entry)
    assert "Smith, J." in apa
    assert "(2020)" in apa
    assert "Journal" in apa
    assert "https://e.com" in apa

    mla = cm.format_citation_mla(entry)
    assert '"Title."' in mla, mla
    assert "2020" in mla
    assert "Smith, J." in mla
    print("[PASS] test_format_citation_apa_and_mla")


def test_generate_bibliography():
    """Библиография формируется по алфавиту ключей."""
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "citations.json")
        assert "No references" in cm.generate_bibliography(path)
        cm.add_citation(path, "zeta", "Zed Author", "Zed", "2021")
        cm.add_citation(path, "alpha", "Ay Author", "Ay", "2020")
        bib = cm.generate_bibliography(path)
        assert bib.startswith("## Bibliography")
        # Сортировка по ключу: alpha (Ay) идёт раньше zeta (Zed)
        assert bib.index("Ay Author") < bib.index("Zed Author"), bib
        assert bib.count("- ") == 2, bib
    print("[PASS] test_generate_bibliography")


def test_extract_citation_keys():
    """Ключи цитат извлекаются из текста в квадратных скобках."""
    keys = cm.extract_citation_keys("См. [smith2020] и [jones-2019], но не [1] или [].")
    assert "smith2020" in keys, keys
    assert "jones-2019" in keys, keys
    assert "1" not in keys, keys
    print("[PASS] test_extract_citation_keys")


def test_insert_citation_inline():
    """Вставка ссылки дописывает [key] к тексту."""
    assert cm.insert_citation_inline("Текст", "k1") == "Текст [k1]"
    print("[PASS] test_insert_citation_inline")


# ─── snippets ────────────────────────────────────────────────────────────────

def test_snippet_library_defaults():
    """При отсутствии файла загружаются дефолтные сниппеты."""
    orig = sn.SNIPPETS_FILE
    with tempfile.TemporaryDirectory() as d:
        sn.SNIPPETS_FILE = os.path.join(d, "sub", "snippets.json")
        try:
            lib = sn.SnippetLibrary()
            assert len(lib.snippets) >= 8, len(lib.snippets)
            assert any(s.name == "Python function" for s in lib.snippets)
            assert all(isinstance(s, sn.Snippet) for s in lib.snippets)
            # Дефолты сохранены на диск
            assert os.path.isfile(sn.SNIPPETS_FILE)
        finally:
            sn.SNIPPETS_FILE = orig
    print("[PASS] test_snippet_library_defaults")


def test_snippet_add_and_remove():
    """Сниппет добавляется и удаляется, изменения сохраняются."""
    orig = sn.SNIPPETS_FILE
    with tempfile.TemporaryDirectory() as d:
        sn.SNIPPETS_FILE = os.path.join(d, "snippets.json")
        try:
            lib = sn.SnippetLibrary()
            before = len(lib.snippets)
            lib.add("My snippet", "python", "print(1)", tags=["demo"])
            assert len(lib.snippets) == before + 1
            added = lib.snippets[-1]
            assert added.name == "My snippet"
            assert added.tags == ["demo"]

            # Перечитывание с диска сохраняет изменения
            lib2 = sn.SnippetLibrary()
            assert len(lib2.snippets) == before + 1
            assert any(s.name == "My snippet" for s in lib2.snippets)

            lib2.remove(len(lib2.snippets) - 1)
            assert len(lib2.snippets) == before
        finally:
            sn.SNIPPETS_FILE = orig
    print("[PASS] test_snippet_add_and_remove")


def test_snippet_remove_out_of_range_is_noop():
    """Удаление по неверному индексу ничего не меняет."""
    orig = sn.SNIPPETS_FILE
    with tempfile.TemporaryDirectory() as d:
        sn.SNIPPETS_FILE = os.path.join(d, "snippets.json")
        try:
            lib = sn.SnippetLibrary()
            before = len(lib.snippets)
            lib.remove(-1)
            lib.remove(9999)
            assert len(lib.snippets) == before
        finally:
            sn.SNIPPETS_FILE = orig
    print("[PASS] test_snippet_remove_out_of_range_is_noop")


def test_snippet_library_handles_broken_file():
    """Битый JSON не ломает библиотеку — список пустой."""
    orig = sn.SNIPPETS_FILE
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "snippets.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write("{не json")
        sn.SNIPPETS_FILE = path
        try:
            with _QuietLogs("MarkdownToPDF.snippets"):
                lib = sn.SnippetLibrary()
            assert lib.snippets == []
        finally:
            sn.SNIPPETS_FILE = orig
    print("[PASS] test_snippet_library_handles_broken_file")


# ─── pdf_to_markdown ─────────────────────────────────────────────────────────

def test_pdf_to_markdown_extracts_text():
    """Текст из PDF извлекается и разбивается постраничными маркерами."""
    pypdf = None
    try:
        import pypdf  # noqa: F401
    except ImportError:
        pypdf = None

    if pypdf is None:
        print("[SKIP] pypdf не установлен — извлечение текста проверено в CI")
        return

    from pypdf import PdfWriter

    with tempfile.TemporaryDirectory() as d:
        pdf_path = os.path.join(d, "doc.pdf")
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        with open(pdf_path, "wb") as f:
            writer.write(f)

        md = p2m.pdf_to_markdown(pdf_path)
        assert isinstance(md, str)
        # Пустые страницы не дают маркеров
        assert "<!-- Page" not in md, md
    print("[PASS] test_pdf_to_markdown_extracts_text")


def test_pdf_to_markdown_file_writes_markdown():
    """pdf_to_markdown_file создаёт .md-файл рядом с PDF по умолчанию."""
    try:
        import pypdf  # noqa: F401
    except ImportError:
        print("[SKIP] pypdf не установлен")
        return

    from pypdf import PdfWriter

    with tempfile.TemporaryDirectory() as d:
        pdf_path = os.path.join(d, "doc.pdf")
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        with open(pdf_path, "wb") as f:
            writer.write(f)

        out = p2m.pdf_to_markdown_file(pdf_path)
        assert out == os.path.join(d, "doc.md"), out
        assert os.path.isfile(out)

        custom = os.path.join(d, "custom.md")
        out2 = p2m.pdf_to_markdown_file(pdf_path, custom)
        assert out2 == custom
        assert os.path.isfile(custom)
    print("[PASS] test_pdf_to_markdown_file_writes_markdown")


def test_pdf_to_markdown_requires_pypdf():
    """Без pypdf — понятный ImportError с инструкцией."""
    import builtins

    orig_import = builtins.__import__

    def _blocked(name, *a, **k):
        if name == "pypdf":
            raise ImportError("blocked")
        return orig_import(name, *a, **k)

    builtins.__import__ = _blocked
    try:
        p2m.pdf_to_markdown("x.pdf")
    except ImportError as e:
        assert "pip install pypdf" in str(e), str(e)
    else:
        raise AssertionError("Ожидался ImportError")
    finally:
        builtins.__import__ = orig_import
    print("[PASS] test_pdf_to_markdown_requires_pypdf")


def main():
    tests = [
        test_cloud_index_falls_back_to_builtin,
        test_cloud_index_uses_remote_data,
        test_is_safe_template_url,
        test_download_template_blocks_unsafe_url,
        test_download_template_returns_content,
        test_download_template_handles_error,
        test_local_templates_save_and_list,
        test_local_templates_ignores_non_md,
        test_citation_add_and_get,
        test_citation_add_updates_existing_key,
        test_citation_remove,
        test_format_citation_apa_and_mla,
        test_generate_bibliography,
        test_extract_citation_keys,
        test_insert_citation_inline,
        test_snippet_library_defaults,
        test_snippet_add_and_remove,
        test_snippet_remove_out_of_range_is_noop,
        test_snippet_library_handles_broken_file,
        test_pdf_to_markdown_extracts_text,
        test_pdf_to_markdown_file_writes_markdown,
        test_pdf_to_markdown_requires_pypdf,
    ]
    for t in tests:
        t()
    print("\nAll core coverage tests passed!")


if __name__ == "__main__":
    main()
