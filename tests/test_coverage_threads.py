"""Поведенческие тесты gui/threads.py.

Потоки конвертации — самая «серверная» часть GUI, поэтому проверяем их
синхронно: вызываем `run()` в главном потоке, подменяя парсер, рендереры и
шифрование. Так видно и выбранный формат экспорта, и порядок логов,
и обработку отмены/ошибок.
"""
import os
import sys
import tempfile
import urllib.request

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication

app = QApplication.instance() or QApplication([])

import src.core.epub_renderer as epub_mod
import src.core.image_renderer as image_mod
import src.core.pptx_renderer as pptx_mod
import src.core.reveal_exporter as reveal_mod
import src.gui.threads as th
from src.gui.models import ConversionOptions, ExportFormat


# ─── общие заглушки ──────────────────────────────────────────────────────────

def _opts(**kw):
    base = dict(
        doc_theme="theme_modern.css",
        code_theme="pygments.css",
        paper_size="A4",
        watermark="",
        footer_text="",
        custom_css="",
        export_format=ExportFormat.PDF,
    )
    base.update(kw)
    return ConversionOptions(**base)


class _Signals:
    """Собирает сигналы потока в списки."""

    def __init__(self, thread):
        self.logs = []
        self.progress = []
        self.one = []
        self.all = 0
        thread.log.connect(self.logs.append)
        thread.progress.connect(self.progress.append)
        thread.finished_one.connect(lambda ok, payload: self.one.append((ok, payload)))
        thread.finished_all.connect(self._on_all)

    def _on_all(self):
        self.all += 1

    @property
    def joined_logs(self):
        return "\n".join(self.logs)


class _FakeParser:
    calls = []
    result = ("<p>html</p>", {"title": "Doc"})
    error = None

    def parse(self, text, **kw):
        type(self).calls.append((text, kw))
        if type(self).error is not None:
            raise type(self).error
        return type(self).result


class _FakePDFRenderer:
    instances = []

    def __init__(self, *a, **k):
        self.init_args = (a, k)
        self.rendered = []
        self.render_html_calls = []
        type(self).instances.append(self)

    def render(self, *a, **k):
        self.rendered.append((a, k))
        return "pdf-bytes"

    def render_html(self, *a, **k):
        self.render_html_calls.append((a, k))
        return "<html>rendered-by-test</html>"


class _FakeDOCXRenderer:
    instances = []

    def __init__(self, *a, **k):
        self.calls = []
        type(self).instances.append(self)

    def render(self, *a, **k):
        self.calls.append((a, k))


class _FakeCountingRenderer:
    """Рендерер, возвращающий число страниц/слайдов."""

    instances = []

    def __init__(self, *a, **k):
        self.init_args = (a, k)
        self.calls = []
        type(self).instances.append(self)

    def render(self, *a, **k):
        self.calls.append((a, k))
        return 3


class _Patch:
    """Контекстный менеджер для временной подмены атрибутов.

    Ключи вида ``"Модуль.Атрибут"`` разрешаются через таблицу ``_MODULES``;
    ключ без точки — атрибут самого ``src.gui.threads``.
    """

    _MODULES = {
        "": th,
        "epub_mod": epub_mod,
        "pptx_mod": pptx_mod,
        "reveal_mod": reveal_mod,
        "image_mod": image_mod,
    }

    def __init__(self, **targets):
        self.targets = targets
        self.saved = []

    def __enter__(self):
        for key, value in self.targets.items():
            if "." in key:
                owner, attr = key.rsplit(".", 1)
                obj = self._MODULES[owner]
            else:
                obj, attr = th, key
            self.saved.append((obj, attr, getattr(obj, attr)))
            setattr(obj, attr, value)
        return self

    def __exit__(self, *exc):
        for obj, attr, value in reversed(self.saved):
            setattr(obj, attr, value)
        return False


def _reset_fakes():
    _FakeParser.calls = []
    _FakeParser.result = ("<p>html</p>", {"title": "Doc"})
    _FakeParser.error = None
    _FakePDFRenderer.instances = []
    _FakeDOCXRenderer.instances = []
    _FakeCountingRenderer.instances = []


def _make_thread(files, opts=None, lang="ru"):
    return th.ConversionThread(
        files, tempfile.gettempdir(), "templates", opts or _opts(),
        wp_executable="wp", lang=lang,
    )


def _write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


# ─── KrokiCheckThread ────────────────────────────────────────────────────────

def test_kroki_check_reports_available():
    """Успешный HEAD-запрос к kroki.io даёт True."""
    thread = th.KrokiCheckThread()
    got = []
    thread.checked.connect(got.append)
    sentinel = object()
    original_request, original_urlopen = urllib.request.Request, urllib.request.urlopen
    seen = {}

    def fake_request(url, method=None):
        seen["url"] = url
        seen["method"] = method
        return sentinel

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(req, timeout=None):
        seen["req"] = req
        seen["timeout"] = timeout
        return _Response()

    urllib.request.Request = fake_request
    urllib.request.urlopen = fake_urlopen
    try:
        thread.run()
    finally:
        urllib.request.Request = original_request
        urllib.request.urlopen = original_urlopen

    assert got == [True], got
    assert seen["url"] == "https://kroki.io"
    assert seen["method"] == "HEAD"
    assert seen["req"] is sentinel
    assert seen["timeout"] == 1.5
    print("[PASS] test_kroki_check_reports_available")


def test_kroki_check_reports_unavailable():
    """Сетевой сбой даёт False, исключение наружу не выходит."""
    thread = th.KrokiCheckThread()
    got = []
    thread.checked.connect(got.append)
    original_urlopen = urllib.request.urlopen

    def fake_urlopen(*a, **k):
        raise OSError("network down")

    urllib.request.urlopen = fake_urlopen
    try:
        thread.run()
    finally:
        urllib.request.urlopen = original_urlopen
    assert got == [False], got
    print("[PASS] test_kroki_check_reports_unavailable")


def test_kroki_signal_name_does_not_shadow_finished():
    """Сигнал называется checked и не перекрывает встроенный finished."""
    thread = th.KrokiCheckThread()
    assert hasattr(thread, "checked")
    assert hasattr(thread, "finished"), "встроенный сигнал QThread.finished должен остаться"
    print("[PASS] test_kroki_signal_name_does_not_shadow_finished")


# ─── ConversionThread: отмена ────────────────────────────────────────────────

def test_conversion_thread_cancel_flag_is_thread_safe():
    """cancel() выставляет флаг, is_cancelled() его читает."""
    thread = _make_thread([])
    assert thread.is_cancelled() is False
    thread.cancel()
    assert thread.is_cancelled() is True
    print("[PASS] test_conversion_thread_cancel_flag_is_thread_safe")


def test_conversion_stops_before_processing_when_cancelled():
    """Отменённый поток не трогает файлы, но корректно завершается."""
    _reset_fakes()
    with tempfile.TemporaryDirectory() as d:
        src_file = os.path.join(d, "a.md")
        out_file = os.path.join(d, "a.pdf")
        _write(src_file, "# hi")
        thread = _make_thread([(src_file, out_file)])
        sig = _Signals(thread)
        with _Patch(**{"MarkdownParser": _FakeParser, "PDFRenderer": _FakePDFRenderer}):
            thread.cancel()
            thread.run()
        assert _FakeParser.calls == [], "парсер не должен вызываться"
        assert sig.one == [], sig.one
        assert "отменена" in sig.joined_logs, sig.joined_logs
        assert sig.progress == [100], sig.progress
        assert sig.all == 1
    print("[PASS] test_conversion_stops_before_processing_when_cancelled")


# ─── ConversionThread: PDF и пароль ──────────────────────────────────────────

def test_conversion_pdf_success_logs_and_signals():
    """PDF: один файл → один лог «saved», прогресс 0/100, сигналы завершения."""
    _reset_fakes()
    with tempfile.TemporaryDirectory() as d:
        src_file = os.path.join(d, "a.md")
        out_file = os.path.join(d, "a.pdf")
        _write(src_file, "# Заголовок\n\nтекст")
        opts = _opts(export_format=ExportFormat.PDF, page_numbers=True,
                     page_num_format="dash", compress=True, watermark="ЧЕРНОВИК",
                     footer_text="Подвал", watermark_css=".x{}")
        thread = _make_thread([(src_file, out_file)], opts)
        sig = _Signals(thread)
        with _Patch(**{"MarkdownParser": _FakeParser, "PDFRenderer": _FakePDFRenderer}):
            thread.run()

        assert sig.one == [(True, out_file)], sig.one
        assert sig.all == 1
        assert sig.progress == [0, 100], sig.progress
        saved = [line for line in sig.logs if "Сохранено" in line]
        assert len(saved) == 1, sig.logs
        assert saved[0].count(out_file) == 1, saved

        renderer = _FakePDFRenderer.instances[0]
        assert len(renderer.rendered) == 1
        args, kwargs = renderer.rendered[0]
        assert args[2] == out_file
        assert args[3] == "theme_modern.css"
        assert kwargs["word_count"] == 3, kwargs
        assert kwargs["compress"] is True
        assert kwargs["page_numbers"] is True
        assert kwargs["page_num_format"] == "dash"
        assert kwargs["watermark_css"] == ".x{}"
        assert args[6] == "ЧЕРНОВИК", args
        assert args[7] == "Подвал", args
        assert args[8] == src_file, args

        assert _FakeParser.calls[0][1]["base_dir"] == d
        assert _FakeParser.calls[0][1]["kroki_available"] is True
    print("[PASS] test_conversion_pdf_success_logs_and_signals")


def test_conversion_pdf_password_success():
    """Успешное шифрование даёт лог о защите паролем."""
    _reset_fakes()
    encrypted = []

    def fake_encrypt(path, password):
        encrypted.append((path, password))
        return True

    with tempfile.TemporaryDirectory() as d:
        src_file = os.path.join(d, "a.md")
        out_file = os.path.join(d, "a.pdf")
        _write(src_file, "text")
        thread = _make_thread([(src_file, out_file)], _opts(pdf_password="s3cret"))
        sig = _Signals(thread)
        with _Patch(**{"MarkdownParser": _FakeParser, "PDFRenderer": _FakePDFRenderer,
                       "encrypt_pdf": fake_encrypt}):
            thread.run()

        assert encrypted == [(out_file, "s3cret")], encrypted
        assert "защищен паролем" in sig.joined_logs, sig.joined_logs
        assert sig.one == [(True, out_file)]
    print("[PASS] test_conversion_pdf_password_success")


def test_conversion_pdf_password_failure_is_logged():
    """Сбой шифрования логируется, но файл считается сохранённым."""
    _reset_fakes()

    def fake_encrypt(path, password):
        return False

    with tempfile.TemporaryDirectory() as d:
        src_file = os.path.join(d, "a.md")
        out_file = os.path.join(d, "a.pdf")
        _write(src_file, "text")
        thread = _make_thread([(src_file, out_file)], _opts(pdf_password="pw"))
        sig = _Signals(thread)
        with _Patch(**{"MarkdownParser": _FakeParser, "PDFRenderer": _FakePDFRenderer,
                       "encrypt_pdf": fake_encrypt}):
            thread.run()

        assert "Ошибка шифрования" in sig.joined_logs, sig.joined_logs
        assert sig.one == [(True, out_file)], sig.one
    print("[PASS] test_conversion_pdf_password_failure_is_logged")


def test_conversion_password_ignored_for_non_pdf():
    """Пароль применяется только к PDF-экспорту."""
    _reset_fakes()
    calls = []

    with tempfile.TemporaryDirectory() as d:
        src_file = os.path.join(d, "a.md")
        out_file = os.path.join(d, "a.docx")
        _write(src_file, "text")
        thread = _make_thread([(src_file, out_file)],
                              _opts(export_format=ExportFormat.DOCX, pdf_password="pw"))
        _Signals(thread)
        with _Patch(**{"MarkdownParser": _FakeParser,
                       "DOCXRenderer": _FakeDOCXRenderer,
                       "encrypt_pdf": lambda p, pw: calls.append((p, pw)) or True}):
            thread.run()
        assert calls == [], calls
        assert len(_FakeDOCXRenderer.instances) == 1
    print("[PASS] test_conversion_password_ignored_for_non_pdf")


# ─── ConversionThread: остальные форматы ─────────────────────────────────────

def test_conversion_docx_uses_template():
    """DOCX-экспорт передаёт шаблон и язык в рендерер."""
    _reset_fakes()
    with tempfile.TemporaryDirectory() as d:
        src_file = os.path.join(d, "a.md")
        out_file = os.path.join(d, "a.docx")
        _write(src_file, "text")
        thread = _make_thread([(src_file, out_file)],
                              _opts(export_format=ExportFormat.DOCX,
                                    docx_template="ref.docx"))
        sig = _Signals(thread)
        with _Patch(**{"MarkdownParser": _FakeParser,
                       "DOCXRenderer": _FakeDOCXRenderer}):
            thread.run()
        calls = _FakeDOCXRenderer.instances[0].calls
        assert len(calls) == 1, calls
        args, kwargs = calls[0]
        assert args[2] == out_file
        assert kwargs["reference_docx"] == "ref.docx"
        assert kwargs["lang"] == "ru"
        assert sig.one == [(True, out_file)]
    print("[PASS] test_conversion_docx_uses_template")


def test_conversion_epub_uses_epub_renderer():
    """EPUB-экспорт идёт через EPUBRenderer."""
    _reset_fakes()
    with tempfile.TemporaryDirectory() as d:
        src_file = os.path.join(d, "a.md")
        out_file = os.path.join(d, "a.epub")
        _write(src_file, "text")
        thread = _make_thread([(src_file, out_file)], _opts(export_format=ExportFormat.EPUB))
        sig = _Signals(thread)
        with _Patch(**{"MarkdownParser": _FakeParser,
                       "epub_mod.EPUBRenderer": _FakeCountingRenderer}):
            thread.run()
        assert len(_FakeCountingRenderer.instances) == 1
        assert _FakeCountingRenderer.instances[0].calls[0][0][2] == out_file
        assert sig.one == [(True, out_file)]
    print("[PASS] test_conversion_epub_uses_epub_renderer")


def test_conversion_pptx_appends_slide_count():
    """PPTX-экспорт добавляет число слайдов в лог сохранения."""
    _reset_fakes()
    with tempfile.TemporaryDirectory() as d:
        src_file = os.path.join(d, "a.md")
        out_file = os.path.join(d, "a.pptx")
        _write(src_file, "text")
        thread = _make_thread([(src_file, out_file)], _opts(export_format=ExportFormat.PPTX))
        sig = _Signals(thread)
        with _Patch(**{"MarkdownParser": _FakeParser,
                       "pptx_mod.PPTXRenderer": _FakeCountingRenderer}):
            thread.run()
        saved = [line for line in sig.logs if "Сохранено" in line]
        assert len(saved) == 1, sig.logs
        assert "(3 slides)" in saved[0], saved[0]
        assert sig.one == [(True, out_file)]
    print("[PASS] test_conversion_pptx_appends_slide_count")


def test_conversion_reveal_appends_slide_count():
    """Reveal.js-экспорт добавляет число слайдов в лог."""
    _reset_fakes()
    called = []

    def fake_export(html, metadata, path, lang=None):
        called.append((html, metadata, path, lang))
        return 5

    with tempfile.TemporaryDirectory() as d:
        src_file = os.path.join(d, "a.md")
        out_file = os.path.join(d, "slides.html")
        _write(src_file, "text")
        thread = _make_thread([(src_file, out_file)], _opts(export_format=ExportFormat.REVEAL))
        sig = _Signals(thread)
        with _Patch(**{"MarkdownParser": _FakeParser,
                       "reveal_mod.export_reveal_js": fake_export}):
            thread.run()
        assert called and called[0][2] == out_file, called
        saved = [line for line in sig.logs if "Сохранено" in line]
        assert "(5 slides)" in saved[0], saved[0]
        assert sig.one == [(True, out_file)]
    print("[PASS] test_conversion_reveal_appends_slide_count")


def test_conversion_png_and_jpg_pass_format():
    """PNG/JPG передают формат и флаг отмены в ImageRenderer."""
    for fmt, expected in ((ExportFormat.PNG, "png"), (ExportFormat.JPG, "jpg")):
        _reset_fakes()
        with tempfile.TemporaryDirectory() as d:
            src_file = os.path.join(d, "a.md")
            out_file = os.path.join(d, f"a.{expected}")
            _write(src_file, "text")
            thread = _make_thread([(src_file, out_file)], _opts(export_format=fmt))
            sig = _Signals(thread)
            with _Patch(**{"MarkdownParser": _FakeParser,
                           "image_mod.ImageRenderer": _FakeCountingRenderer}):
                thread.run()
            renderer = _FakeCountingRenderer.instances[0]
            args, kwargs = renderer.calls[0]
            assert renderer.init_args[0] == ("wp",), renderer.init_args
            assert kwargs["image_format"] == expected, kwargs
            assert callable(kwargs["cancel_flag"])
            assert kwargs["doc_theme"] == "theme_modern.css"
            saved = [line for line in sig.logs if "Сохранено" in line]
            assert "(3 pages)" in saved[0], saved[0]
            assert sig.one == [(True, out_file)]
    print("[PASS] test_conversion_png_and_jpg_pass_format")


def test_conversion_html_writes_rendered_markup():
    """HTML-экспорт пишет в файл результат render_html."""
    _reset_fakes()
    with tempfile.TemporaryDirectory() as d:
        src_file = os.path.join(d, "a.md")
        out_file = os.path.join(d, "a.html")
        _write(src_file, "text")
        thread = _make_thread([(src_file, out_file)],
                              _opts(export_format=ExportFormat.HTML))
        sig = _Signals(thread)
        with _Patch(**{"MarkdownParser": _FakeParser, "PDFRenderer": _FakePDFRenderer}):
            thread.run()
        with open(out_file, encoding="utf-8") as f:
            assert f.read() == "<html>rendered-by-test</html>"
        renderer = _FakePDFRenderer.instances[0]
        assert renderer.rendered == [], "PDF-рендер вызываться не должен"
        assert renderer.render_html_calls
        assert sig.one == [(True, out_file)]
    print("[PASS] test_conversion_html_writes_rendered_markup")


def test_conversion_presentation_uses_presentation_theme():
    """Презентация подменяет тему документа на theme_presentation.css."""
    _reset_fakes()
    with tempfile.TemporaryDirectory() as d:
        src_file = os.path.join(d, "a.md")
        out_file = os.path.join(d, "a.pdf")
        _write(src_file, "text")
        thread = _make_thread([(src_file, out_file)],
                              _opts(is_presentation=True))
        _Signals(thread)
        with _Patch(**{"MarkdownParser": _FakeParser, "PDFRenderer": _FakePDFRenderer}):
            thread.run()
        args, _ = _FakePDFRenderer.instances[0].rendered[0]
        assert args[3] == "theme_presentation.css", args
        assert _FakeParser.calls[0][1]["is_presentation"] is True
    print("[PASS] test_conversion_presentation_uses_presentation_theme")


# ─── ConversionThread: ошибки и несколько файлов ─────────────────────────────

def test_conversion_reports_parser_error_and_continues():
    """Ошибка разбора по одному файлу не прерывает обработку остальных."""
    _reset_fakes()
    with tempfile.TemporaryDirectory() as d:
        good = os.path.join(d, "good.md")
        bad = os.path.join(d, "bad.md")
        _write(good, "ok")
        _write(bad, "bad")
        thread = _make_thread([(bad, "bad.pdf"), (good, "good.pdf")])
        sig = _Signals(thread)

        original_parse = _FakeParser.parse

        def parse(self, text, **kw):
            if text == "bad":
                raise ValueError("broken markdown")
            return original_parse(self, text, **kw)

        _FakeParser.parse = parse
        try:
            with _Patch(**{"MarkdownParser": _FakeParser, "PDFRenderer": _FakePDFRenderer}):
                thread.run()
        finally:
            _FakeParser.parse = original_parse

        assert sig.one[0] == (False, "broken markdown"), sig.one
        assert sig.one[1] == (True, "good.pdf"), sig.one
        assert "broken markdown" in sig.joined_logs
        assert sig.progress == [0, 50, 100], sig.progress
        assert sig.all == 1
    print("[PASS] test_conversion_reports_parser_error_and_continues")


def test_conversion_missing_input_file_reports_error():
    """Отсутствующий входной файл даёт ошибку, а не падение потока."""
    _reset_fakes()
    thread = _make_thread([("no-such-file.md", "out.pdf")])
    sig = _Signals(thread)
    with _Patch(**{"MarkdownParser": _FakeParser, "PDFRenderer": _FakePDFRenderer}):
        thread.run()
    assert sig.one and sig.one[0][0] is False, sig.one
    assert sig.all == 1
    print("[PASS] test_conversion_missing_input_file_reports_error")


def test_conversion_multiple_files_progress():
    """Прогресс растёт по числу файлов и доходит до 100."""
    _reset_fakes()
    with tempfile.TemporaryDirectory() as d:
        files = []
        for i in range(3):
            src_file = os.path.join(d, f"{i}.md")
            _write(src_file, f"text {i}")
            files.append((src_file, os.path.join(d, f"{i}.pdf")))
        thread = _make_thread(files)
        sig = _Signals(thread)
        with _Patch(**{"MarkdownParser": _FakeParser, "PDFRenderer": _FakePDFRenderer}):
            thread.run()
        # int((idx-1)/3*100) для idx=1..3 → 0, 33, 66, затем финальные 100
        assert sig.progress == [0, 33, 66, 100], sig.progress
        assert len(sig.one) == 3
        assert all(ok for ok, _ in sig.one)
        assert sig.all == 1
    print("[PASS] test_conversion_multiple_files_progress")


def test_conversion_uses_english_translations():
    """Английская локаль даёт английские логи."""
    _reset_fakes()
    with tempfile.TemporaryDirectory() as d:
        src_file = os.path.join(d, "a.md")
        out_file = os.path.join(d, "a.pdf")
        _write(src_file, "text")
        thread = _make_thread([(src_file, out_file)], _opts(), lang="en")
        sig = _Signals(thread)
        with _Patch(**{"MarkdownParser": _FakeParser, "PDFRenderer": _FakePDFRenderer}):
            thread.run()
        assert "Converting" in sig.joined_logs, sig.joined_logs
        assert "Saved" in sig.joined_logs, sig.joined_logs
        assert "All files processed" in sig.joined_logs, sig.joined_logs
    print("[PASS] test_conversion_uses_english_translations")


# ─── BookBuilderThread ───────────────────────────────────────────────────────

def _book(**kw):
    base = dict(
        merged_md="# Книга\n\nтекст",
        base_dir=".",
        save_path="book.pdf",
        book_title="",
        template_dir="templates",
        wp_executable="wp",
        doc_theme="theme_modern.css",
        code_theme="pygments.css",
        paper_size="A4",
        watermark="",
        footer="",
        custom_css="",
        margins="",
        password="",
        page_numbers=False,
        lang="ru",
        kroki_available=True,
    )
    base.update(kw)
    return th.BookBuilderThread(**base)


class _BookSignals:
    def __init__(self, thread):
        self.logs = []
        self.task = []
        thread.log.connect(self.logs.append)
        thread.finished_task.connect(lambda ok, payload: self.task.append((ok, payload)))

    @property
    def joined_logs(self):
        return "\n".join(self.logs)


def test_book_builder_success():
    """Книга собирается: парсинг, рендер, лог сохранения, сигнал успеха."""
    _reset_fakes()
    thread = _book()
    sig = _BookSignals(thread)
    with _Patch(**{"MarkdownParser": _FakeParser, "PDFRenderer": _FakePDFRenderer}):
        thread.run()

    assert sig.task == [(True, "book.pdf")], sig.task
    assert any("Parsing merged Markdown" in line for line in sig.logs), sig.logs
    assert any("Rendering PDF" in line for line in sig.logs), sig.logs
    assert any("Сохранено" in line for line in sig.logs), sig.logs

    renderer = _FakePDFRenderer.instances[0]
    assert renderer.init_args[0] == ("templates", "wp")
    args, kwargs = renderer.rendered[0]
    assert args[2] == "book.pdf"
    assert kwargs["input_filepath"] is None
    assert kwargs["page_num_format"] == "simple"
    assert kwargs["word_count"] == 3, kwargs
    assert callable(kwargs["cancel_flag"])
    print("[PASS] test_book_builder_success")


def test_book_builder_overrides_title():
    """Заданное название книги перекрывает заголовок из метаданных."""
    _reset_fakes()
    thread = _book(book_title="Моя книга")
    _BookSignals(thread)
    with _Patch(**{"MarkdownParser": _FakeParser, "PDFRenderer": _FakePDFRenderer}):
        thread.run()
    metadata = _FakeParser.calls[0]
    assert metadata is not None
    # Проверяем, что заголовок действительно подменён в метаданных,
    # которые получил рендерер.
    args, _ = _FakePDFRenderer.instances[0].rendered[0]
    assert args[1]["title"] == "Моя книга", args[1]
    print("[PASS] test_book_builder_overrides_title")


def test_book_builder_cancel_after_parse():
    """Отмена после парсинга даёт сигнал Cancelled и не запускает рендер."""
    _reset_fakes()
    thread = _book()
    thread.cancel()
    sig = _BookSignals(thread)
    with _Patch(**{"MarkdownParser": _FakeParser, "PDFRenderer": _FakePDFRenderer}):
        thread.run()
    assert sig.task == [(False, "Cancelled")], sig.task
    assert _FakePDFRenderer.instances == [], "рендер не должен начаться"
    print("[PASS] test_book_builder_cancel_after_parse")


def test_book_builder_reports_error():
    """Ошибка в книжном потоке превращается в сигнал (False, сообщение)."""
    _reset_fakes()
    _FakeParser.error = RuntimeError("parse failed")
    thread = _book()
    sig = _BookSignals(thread)
    with _Patch(**{"MarkdownParser": _FakeParser, "PDFRenderer": _FakePDFRenderer}):
        thread.run()
    assert sig.task == [(False, "parse failed")], sig.task
    assert "parse failed" in sig.joined_logs
    print("[PASS] test_book_builder_reports_error")


def test_book_builder_password_encrypts():
    """Пароль книги передаётся в encrypt_pdf."""
    _reset_fakes()
    encrypted = []
    thread = _book(password="pw123")
    sig = _BookSignals(thread)
    with _Patch(**{"MarkdownParser": _FakeParser, "PDFRenderer": _FakePDFRenderer,
                   "encrypt_pdf": lambda p, pw: encrypted.append((p, pw)) or True}):
        thread.run()
    assert encrypted == [("book.pdf", "pw123")], encrypted
    assert "защищен паролем" in sig.joined_logs, sig.joined_logs
    print("[PASS] test_book_builder_password_encrypts")


def test_book_builder_password_failure_logged():
    """Сбой шифрования книги логируется как ошибка."""
    _reset_fakes()
    thread = _book(password="pw")
    sig = _BookSignals(thread)
    with _Patch(**{"MarkdownParser": _FakeParser, "PDFRenderer": _FakePDFRenderer,
                   "encrypt_pdf": lambda p, pw: False}):
        thread.run()
    assert "Ошибка шифрования" in sig.joined_logs, sig.joined_logs
    assert sig.task == [(True, "book.pdf")]
    print("[PASS] test_book_builder_password_failure_logged")


def test_book_builder_cancel_flag_thread_safe():
    """Отмена книги доступна из другого потока."""
    thread = _book()
    assert thread.is_cancelled() is False
    thread.cancel()
    assert thread.is_cancelled() is True
    print("[PASS] test_book_builder_cancel_flag_thread_safe")


def test_book_builder_passes_themes_and_margins():
    """Все параметры оформления доходят до рендерера."""
    _reset_fakes()
    thread = _book(doc_theme="theme_classic.css", code_theme="pygments_dark.css",
                   paper_size="A5", watermark="W", footer="F", custom_css="c.css",
                   margins="10mm", page_numbers=True, kroki_available=False)
    _BookSignals(thread)
    with _Patch(**{"MarkdownParser": _FakeParser, "PDFRenderer": _FakePDFRenderer}):
        thread.run()
    args, kwargs = _FakePDFRenderer.instances[0].rendered[0]
    assert args[3] == "theme_classic.css"
    assert args[4] == "pygments_dark.css"
    assert args[5] == "A5"
    assert args[6] == "W"
    assert args[7] == "F"
    assert kwargs["custom_css_path"] == "c.css"
    assert kwargs["margins"] == "10mm"
    assert kwargs["page_numbers"] is True
    assert _FakeParser.calls[0][1]["kroki_available"] is False
    print("[PASS] test_book_builder_passes_themes_and_margins")


def main():
    tests = [
        test_kroki_check_reports_available,
        test_kroki_check_reports_unavailable,
        test_kroki_signal_name_does_not_shadow_finished,
        test_conversion_thread_cancel_flag_is_thread_safe,
        test_conversion_stops_before_processing_when_cancelled,
        test_conversion_pdf_success_logs_and_signals,
        test_conversion_pdf_password_success,
        test_conversion_pdf_password_failure_is_logged,
        test_conversion_password_ignored_for_non_pdf,
        test_conversion_docx_uses_template,
        test_conversion_epub_uses_epub_renderer,
        test_conversion_pptx_appends_slide_count,
        test_conversion_reveal_appends_slide_count,
        test_conversion_png_and_jpg_pass_format,
        test_conversion_html_writes_rendered_markup,
        test_conversion_presentation_uses_presentation_theme,
        test_conversion_reports_parser_error_and_continues,
        test_conversion_missing_input_file_reports_error,
        test_conversion_multiple_files_progress,
        test_conversion_uses_english_translations,
        test_book_builder_success,
        test_book_builder_overrides_title,
        test_book_builder_cancel_after_parse,
        test_book_builder_reports_error,
        test_book_builder_password_encrypts,
        test_book_builder_password_failure_logged,
        test_book_builder_cancel_flag_thread_safe,
        test_book_builder_passes_themes_and_margins,
    ]
    for t in tests:
        t()
    print("\nAll threads tests passed!")


if __name__ == "__main__":
    main()
