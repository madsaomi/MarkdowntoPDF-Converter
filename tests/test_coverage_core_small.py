"""Поведенческие тесты небольших модулей ядра и воркера.

Покрывает `core/pdf_encrypt.py`, `core/glossary.py`, `core/latex_preview.py`,
`core/ocr_engine.py` и `gui/workers/task_worker.py`. Внешние сервисы
(pypdf, CodeCogs-кэш, pytesseract) подменяются, Qt-потоки проверяются на
реальных сигналах.
"""
import json
import os
import re
import shutil
import sys
import tempfile
import types
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget

app = QApplication.instance() or QApplication([])

from src.core import glossary, latex_preview, ocr_engine, pdf_encrypt
from src.gui.workers import task_worker


def _make_pdf(path, metadata=None):
    """Создаёт настоящий одностраничный PDF через pypdf."""
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    if metadata:
        writer.add_metadata(metadata)
    with open(path, "wb") as f:
        writer.write(f)


# ─── pdf_encrypt ────────────────────────────────────────────────────────────

def test_encrypt_pdf_in_place():
    """PDF шифруется на месте, пароль действительно требуется для чтения."""
    tmpdir = tempfile.mkdtemp()
    try:
        path = os.path.join(tmpdir, "doc.pdf")
        _make_pdf(path)
        assert pdf_encrypt.encrypt_pdf(path, "secret") is True

        from pypdf import PdfReader
        reader = PdfReader(path)
        assert reader.is_encrypted is True
        assert reader.decrypt("secret")
        assert len(reader.pages) == 1
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_encrypt_pdf_in_place")


def test_encrypt_pdf_to_separate_output():
    """При явном output_path исходный файл остаётся незашифрованным."""
    tmpdir = tempfile.mkdtemp()
    try:
        src = os.path.join(tmpdir, "src.pdf")
        out = os.path.join(tmpdir, "out.pdf")
        _make_pdf(src)
        assert pdf_encrypt.encrypt_pdf(src, "pw", out) is True

        from pypdf import PdfReader
        assert os.path.exists(out)
        assert PdfReader(out).is_encrypted is True
        assert PdfReader(src).is_encrypted is False
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_encrypt_pdf_to_separate_output")


def test_encrypt_pdf_successful_path_is_logged_on_error_only():
    """Ошибка шифрования пишется в лог и возвращает False."""
    fake_logger = types.SimpleNamespace(errors=[])
    fake_logger.error = lambda fmt, *a: fake_logger.errors.append(fmt % a if a else fmt)
    original = pdf_encrypt.logger
    pdf_encrypt.logger = fake_logger
    try:
        assert pdf_encrypt.encrypt_pdf("no_such_file.pdf", "pw") is False
        assert fake_logger.errors and "no_such_file.pdf" in fake_logger.errors[0]
    finally:
        pdf_encrypt.logger = original
    print("[PASS] test_encrypt_pdf_successful_path_is_logged_on_error_only")


# ─── glossary: извлечение определений ───────────────────────────────────────

def test_extract_definitions_colon_and_dash():
    """Двоеточие, дефис и длинное тире распознаются."""
    text = (
        "**API**: Application Programming Interface\n"
        "**CLI** - command line interface\n"
        "**GUI** — graphical user interface\n"
    )
    defs = glossary.extract_definitions(text)
    assert [d["term"] for d in defs] == ["API", "CLI", "GUI"]
    assert defs[0]["definition"] == "Application Programming Interface"
    assert defs[1]["definition"] == "command line interface"
    assert defs[2]["definition"] == "graphical user interface"
    print("[PASS] test_extract_definitions_colon_and_dash")


def test_extract_definitions_ignores_plain_and_deduplicates():
    """Не-bold строки игнорируются, повторы терминов (в любом регистре) — тоже."""
    text = (
        "API: not bold, ignored\n"
        "**Term**: first definition\n"
        "**term**: second definition\n"
        "  **Indented** — not at line start\n"
    )
    defs = glossary.extract_definitions(text)
    assert defs == [{"term": "Term", "definition": "first definition"}]
    assert glossary.extract_definitions("") == []
    print("[PASS] test_extract_definitions_ignores_plain_and_deduplicates")


def test_extract_definitions_separator_may_be_spaced():
    """BUG_012: `**Term** — Definition` (с пробелом) тоже распознаётся."""
    text = (
        "**API** : Interface\n"
        "**CLI**  - command line\n"
        "**GUI**\t— graphical\n"
    )
    defs = glossary.extract_definitions(text)
    assert [d["term"] for d in defs] == ["API", "CLI", "GUI"], defs
    assert defs[1]["definition"] == "command line"
    print("[PASS] test_extract_definitions_separator_may_be_spaced")


def test_extract_definitions_does_not_cross_newlines():
    """Строка `**Term**` со списком на следующей строке — не определение."""
    text = "**Term**\n- bullet item\n"
    assert glossary.extract_definitions(text) == []
    print("[PASS] test_extract_definitions_does_not_cross_newlines")


def test_extract_definitions_sorted_case_insensitively():
    """Результат сортируется по термину без учёта регистра."""
    text = "**banana**: b\n**Apple**: a\n**cherry**: c\n"
    assert [d["term"] for d in glossary.extract_definitions(text)] == ["Apple", "banana", "cherry"]
    print("[PASS] test_extract_definitions_sorted_case_insensitively")


# ─── glossary: экспорт ──────────────────────────────────────────────────────

def test_glossary_to_markdown():
    """Markdown-глоссарий: заголовок и по строке на термин."""
    assert glossary.glossary_to_markdown([]) == ""
    defs = [{"term": "API", "definition": "Interface"}, {"term": "CLI", "definition": "Command line"}]
    md = glossary.glossary_to_markdown(defs)
    assert md.startswith("## Glossary\n")
    assert "**API**: Interface" in md
    assert "**CLI**: Command line" in md
    print("[PASS] test_glossary_to_markdown")


def test_glossary_to_html_escapes_and_links():
    """HTML-глоссарий экранирует ввод и строит якорные ссылки."""
    assert glossary.glossary_to_html([]) == ""
    defs = [
        {"term": "<script>", "definition": "bad & ugly"},
        {"term": "API", "definition": "Interface"},
    ]
    html = glossary.glossary_to_html(defs)
    assert "&lt;script&gt;" in html
    assert "&amp;" in html
    assert "<script>" not in html
    assert 'href="#script"' in html
    assert 'id="script"' in html
    assert 'href="#api"' in html
    assert "2 terms" in html
    assert html.startswith("<!DOCTYPE html>")
    print("[PASS] test_glossary_to_html_escapes_and_links")


def test_glossary_to_json_roundtrip():
    """JSON-экспорт сохраняет юникод и читается обратно."""
    defs = [{"term": "Термин", "definition": "Определение"}]
    raw = glossary.glossary_to_json(defs)
    assert "Термин" in raw
    assert json.loads(raw) == defs
    assert glossary.glossary_to_json([]) == "[]"
    print("[PASS] test_glossary_to_json_roundtrip")


def test_find_term_in_text():
    """Поиск термина без учёта регистра, со спецсимволами и без совпадений."""
    text = "API — это api. API!" 
    assert glossary.find_term_in_text(text, "api") == [0, 10, 15]
    assert glossary.find_term_in_text("use C++ here", "C++") == [4]
    assert glossary.find_term_in_text("nothing", "zzz") == []
    print("[PASS] test_find_term_in_text")


# ─── latex_preview ──────────────────────────────────────────────────────────

def test_latex_to_url_inline_and_block():
    """Inline-формула оборачивается в colorbox, блочная — нет."""
    cached = {}

    def get_cached(kind, key):
        return cached.get(key)

    def set_cached(kind, key, value):
        cached[key] = value

    with patch.object(latex_preview, "get_cached", get_cached), \
         patch.object(latex_preview, "set_cached", set_cached):
        inline = latex_preview.latex_to_url("x^2", inline=True)
        block = latex_preview.latex_to_url("x^2", inline=False)

    assert inline.startswith(latex_preview.LATEX_SERVICE)
    assert "%5Ccolorbox%7Bwhite%7D" in inline
    assert "%24%20x%5E2%20%24" in inline
    assert "%5Ccolorbox" not in block
    assert inline != block
    assert set(cached) == {"True|x^2", "False|x^2"}
    print("[PASS] test_latex_to_url_inline_and_block")


def test_latex_to_url_uses_cache():
    """Кэш возвращает готовый URL и не трогает set_cached."""
    calls = []
    with patch.object(latex_preview, "get_cached", lambda kind, key: {"url": "cached-url"}), \
         patch.object(latex_preview, "set_cached", lambda *a: calls.append(a)):
        assert latex_preview.latex_to_url("any") == "cached-url"
    assert calls == []
    print("[PASS] test_latex_to_url_uses_cache")


def test_latex_to_url_survives_cache_errors():
    """Сбой записи в кэш не мешает вернуть URL."""
    def boom(*args, **kwargs):
        raise OSError("cache is read-only")

    with patch.object(latex_preview, "get_cached", lambda kind, key: None), \
         patch.object(latex_preview, "set_cached", boom):
        url = latex_preview.latex_to_url("y")
    assert url.startswith(latex_preview.LATEX_SERVICE)
    print("[PASS] test_latex_to_url_survives_cache_errors")


def test_find_latex_expressions():
    """Находит блочные и inline-формулы, не путая их между собой."""
    text = "Block: $$a+b$$ and inline $c^2$ here."
    found = latex_preview.find_latex_expressions(text)
    assert len(found) == 2
    blocks = [f for f in found if f[2] == "a+b"]
    inline = [f for f in found if f[2] == "c^2"]
    assert len(blocks) == 1 and len(inline) == 1
    start, end, formula = blocks[0]
    assert text[start:end] == "$$a+b$$"
    assert latex_preview.find_latex_expressions("no math") == []
    print("[PASS] test_find_latex_expressions")


def test_inline_math_inside_block_is_skipped():
    """`$` внутри `$$…$$` не считается отдельной формулой."""
    text = "$$a $ b$$"
    found = latex_preview.find_latex_expressions(text)
    assert len(found) == 1
    assert found[0][2] == "a $ b"
    print("[PASS] test_inline_math_inside_block_is_skipped")


def test_render_latex_in_html_replaces_all_formulas():
    """Формулы заменяются на img, смещения не съезжают при нескольких заменах."""
    text = "A $x$ B $$y^2$$ C"
    with patch.object(latex_preview, "latex_to_url", lambda f, inline=True: f"http://img/{f}"):
        html = latex_preview.render_latex_in_html(text)
    img_x = '<img src="http://img/x" alt="x" style="vertical-align: middle;" />'
    img_y = '<img src="http://img/y^2" alt="y^2" style="vertical-align: middle;" />'
    # BUG_013: инлайновая формула идёт раньше блочной, замены применяются слева направо
    assert html == f"A {img_x} B {img_y} C", html
    assert "<img" in html and html.count("<img") == 2
    assert "$$" not in html and "$x$" not in html
    assert latex_preview.render_latex_in_html("no math") == "no math"
    print("[PASS] test_render_latex_in_html_replaces_all_formulas")


def test_render_latex_in_html_two_inline_formulas():
    """Две inline-формулы подряд заменяются независимо."""
    text = "sum $a$ and $b$ end"
    with patch.object(latex_preview, "latex_to_url", lambda f, inline=True: f"U({f})"):
        html = latex_preview.render_latex_in_html(text)
    assert html.count("<img") == 2
    assert 'alt="a"' in html and 'alt="b"' in html
    assert html.startswith("sum <img") and html.endswith("/> end")
    print("[PASS] test_render_latex_in_html_two_inline_formulas")


def test_validate_latex_braces_and_brackets():
    """Проверка парности фигурных и квадратных скобок."""
    assert latex_preview.validate_latex(r"\frac{a}{b}") == (True, "Valid")
    assert latex_preview.validate_latex("x^2") == (True, "Valid")
    ok, msg = latex_preview.validate_latex("a}b")
    assert ok is False and "closing brace" in msg
    ok, msg = latex_preview.validate_latex("a{b")
    assert ok is False and "1 unclosed" in msg
    ok, msg = latex_preview.validate_latex("a]b")
    assert ok is False and "closing bracket" in msg
    ok, msg = latex_preview.validate_latex("a[b")
    assert ok is False and "bracket" in msg
    print("[PASS] test_validate_latex_braces_and_brackets")


# ─── ocr_engine ─────────────────────────────────────────────────────────────

def _fake_ocr_modules(text="  Hello OCR  "):
    calls = []

    def image_to_string(img, lang):
        calls.append((img, lang))
        return text

    tess = types.SimpleNamespace(image_to_string=image_to_string)
    image_mod = types.SimpleNamespace(open=lambda path: f"IMG:{path}")
    pil = types.SimpleNamespace(Image=image_mod)
    return {"pytesseract": tess, "PIL": pil, "PIL.Image": image_mod}, calls


def test_image_to_text_strips_result():
    """OCR возвращает текст без ведущих/хвостовых пробелов."""
    modules, calls = _fake_ocr_modules()
    with patch.dict(sys.modules, modules):
        assert ocr_engine.image_to_text("scan.png", lang="rus") == "Hello OCR"
    assert calls == [("IMG:scan.png", "rus")]
    print("[PASS] test_image_to_text_strips_result")


def test_image_to_text_requires_dependencies():
    """Без pytesseract поднимается понятная ошибка установки."""
    with patch.dict(sys.modules, {"pytesseract": None}):
        try:
            ocr_engine.image_to_text("scan.png")
        except ImportError as e:
            assert "pip install pytesseract Pillow" in str(e)
        else:
            raise AssertionError("ожидался ImportError")
    print("[PASS] test_image_to_text_requires_dependencies")


def test_image_to_markdown():
    """Markdown-обёртка: картинка + распознанный текст."""
    with patch.object(ocr_engine, "image_to_text", lambda path, lang="eng": "Line 1"):
        md = ocr_engine.image_to_markdown("/docs/page.png")
    assert md.startswith("![Extracted from page.png](/docs/page.png)")
    assert md.endswith("Line 1")

    with patch.object(ocr_engine, "image_to_text", lambda path, lang="eng": ""):
        assert ocr_engine.image_to_markdown("/docs/page.png") == ""
    print("[PASS] test_image_to_markdown")


def test_batch_ocr_collects_results_and_errors():
    """Пакетный OCR: успешные файлы в словаре, ошибки — строкой."""
    def fake_text(path, lang="eng"):
        if path == "bad.png":
            raise RuntimeError("boom")
        return f"text:{os.path.basename(path)}"

    fake_logger = types.SimpleNamespace(errors=[])
    fake_logger.error = lambda fmt, *a: fake_logger.errors.append(fmt % a if a else fmt)
    original = ocr_engine.logger
    ocr_engine.logger = fake_logger
    try:
        with patch.object(ocr_engine, "image_to_text", fake_text):
            result = ocr_engine.batch_ocr(["a.png", "bad.png", "b.png"], lang="eng")
    finally:
        ocr_engine.logger = original

    assert list(result) == ["a.png", "bad.png", "b.png"]
    assert result["a.png"] == "text:a.png"
    assert result["b.png"] == "text:b.png"
    assert result["bad.png"] == "[OCR Error: boom]"
    assert fake_logger.errors and "bad.png" in fake_logger.errors[0]
    assert ocr_engine.batch_ocr([]) == {}
    print("[PASS] test_batch_ocr_collects_results_and_errors")


# ─── task_worker ────────────────────────────────────────────────────────────

def test_task_worker_run_emits_result():
    """run() вызывает функцию и отдаёт результат через сигнал finished."""
    got = []
    errors = []
    w = task_worker.TaskWorker(lambda a, b=0: a + b, 2, b=3)
    w.finished.connect(got.append, Qt.ConnectionType.DirectConnection)
    w.error.connect(errors.append, Qt.ConnectionType.DirectConnection)
    w.run()
    assert got == [5]
    assert errors == []
    print("[PASS] test_task_worker_run_emits_result")


def test_task_worker_run_emits_error():
    """Исключение внутри функции превращается в сигнал error."""
    def boom():
        raise ValueError("bad input")

    got = []
    errors = []
    w = task_worker.TaskWorker(boom)
    w.finished.connect(got.append, Qt.ConnectionType.DirectConnection)
    w.error.connect(errors.append, Qt.ConnectionType.DirectConnection)
    w.run()
    assert got == []
    assert errors == ["bad input"]
    print("[PASS] test_task_worker_run_emits_error")


def test_task_worker_start_runs_in_background_thread():
    """start() поднимает реальный QThread и завершает его после работы."""
    got = []
    w = task_worker.TaskWorker(lambda: 42)
    w.finished.connect(got.append, Qt.ConnectionType.DirectConnection)
    w.start()
    thread = w._thread
    try:
        assert thread is not None
        # quit() приходит в очередь главного потока — прокручиваем события,
        # иначе поток останется жить после выполнения функции.
        for _ in range(100):
            app.processEvents()
            if thread.wait(50):
                break
        assert thread.isFinished() is True, "поток не завершился за 5 секунд"
        assert got == [42]
    finally:
        if thread.isRunning():
            thread.quit()
            thread.wait(5000)
    print("[PASS] test_task_worker_start_runs_in_background_thread")


def test_task_thread_connects_callbacks_and_starts():
    """TaskThread связывает on_finish/on_error и запускает воркер."""
    tt = task_worker.TaskThread(lambda: 7)
    started = []
    tt.worker.start = lambda: started.append(True)
    finished, errors = [], []
    tt.start(on_finish=finished.append, on_error=errors.append)
    assert started == [True]

    tt.worker.finished.emit(7)
    tt.worker.error.emit("oops")
    assert finished == [7]
    assert errors == ["oops"]
    assert tt._on_finish is finished.append or tt._on_finish is not None
    print("[PASS] test_task_thread_connects_callbacks_and_starts")


def test_task_thread_without_callbacks_and_with_parent():
    """Без колбэков старт работает; родитель назначается воркеру."""
    tt = task_worker.TaskThread(lambda: 1)
    started = []
    tt.worker.start = lambda: started.append(True)
    tt.start()
    assert started == [True]
    assert tt.worker.parent() is None

    host = QWidget()
    tt2 = task_worker.TaskThread(lambda: 1)
    tt2.worker.start = lambda: None
    tt2.start(parent=host)
    assert tt2.worker.parent() is host
    print("[PASS] test_task_thread_without_callbacks_and_with_parent")


def test_task_thread_ignores_invalid_parent():
    """Невалидный parent не мешает запуску: setParent изолирован try/except."""
    tt = task_worker.TaskThread(lambda: 1)
    started = []
    tt.worker.start = lambda: started.append(True)
    tt.start(parent=object())          # setParent(QObject) бросит TypeError
    assert started == [True]
    assert tt.worker.parent() is None
    print("[PASS] test_task_thread_ignores_invalid_parent")


def main():
    tests = [
        test_encrypt_pdf_in_place,
        test_encrypt_pdf_to_separate_output,
        test_encrypt_pdf_successful_path_is_logged_on_error_only,
        test_extract_definitions_colon_and_dash,
        test_extract_definitions_ignores_plain_and_deduplicates,
        test_extract_definitions_separator_may_be_spaced,
        test_extract_definitions_does_not_cross_newlines,
        test_extract_definitions_sorted_case_insensitively,
        test_glossary_to_markdown,
        test_glossary_to_html_escapes_and_links,
        test_glossary_to_json_roundtrip,
        test_find_term_in_text,
        test_latex_to_url_inline_and_block,
        test_latex_to_url_uses_cache,
        test_latex_to_url_survives_cache_errors,
        test_find_latex_expressions,
        test_inline_math_inside_block_is_skipped,
        test_render_latex_in_html_replaces_all_formulas,
        test_render_latex_in_html_two_inline_formulas,
        test_validate_latex_braces_and_brackets,
        test_image_to_text_strips_result,
        test_image_to_text_requires_dependencies,
        test_image_to_markdown,
        test_batch_ocr_collects_results_and_errors,
        test_task_worker_run_emits_result,
        test_task_worker_run_emits_error,
        test_task_worker_start_runs_in_background_thread,
        test_task_thread_connects_callbacks_and_starts,
        test_task_thread_without_callbacks_and_with_parent,
        test_task_thread_ignores_invalid_parent,
    ]
    for t in tests:
        t()
    print("\nAll small core/worker tests passed!")


if __name__ == "__main__":
    main()
