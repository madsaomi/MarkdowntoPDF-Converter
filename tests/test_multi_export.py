"""Тесты multi_export (PLAN-005/TASK-005).

`multi_export` импортирует рендереры на этапе выполнения и изолирует ошибки
каждого формата в значение "ERROR: ...". Здесь PDFRenderer подменяется
заглушкой, чтобы тест не зависел от WeasyPrint и python-docx.
"""
import os
import sys
import tempfile
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import multi_export


class _FakePDFRenderer:
    """Заглушка PDFRenderer: пишет простой файл, запоминает kwargs."""

    last_kwargs = None

    def __init__(self, template_dir, wp_executable):
        self.template_dir = template_dir
        self.wp_executable = wp_executable

    def render_html(self, html_content, metadata, **kwargs):
        _FakePDFRenderer.last_kwargs = kwargs
        return f"<html><!-- {metadata.get('title')} -->{html_content}</html>"

    def render(self, html_content, metadata, output_path, **kwargs):
        _FakePDFRenderer.last_kwargs = kwargs
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("PDF")


def _patch_pdf_renderer():
    """Подменяет PDFRenderer внутри multi_export (импортируется локально)."""
    import src.core.renderer as renderer_mod
    original = renderer_mod.PDFRenderer
    renderer_mod.PDFRenderer = _FakePDFRenderer
    return original


def test_html_and_pdf_export():
    """HTML и PDF проходят через renderer и дают пути к файлам."""
    original = _patch_pdf_renderer()
    try:
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "doc.md")
            with open(src, "w", encoding="utf-8") as f:
                f.write("# Заголовок\n\nТекст")
            out_dir = os.path.join(d, "out")
            os.makedirs(out_dir, exist_ok=True)
            results = multi_export.multi_export(src, out_dir, ["html", "pdf"], template_dir=d)
            assert not results["html"].startswith("ERROR"), results["html"]
            assert not results["pdf"].startswith("ERROR"), results["pdf"]
            assert os.path.exists(results["html"])
            assert os.path.exists(results["pdf"])
            assert results["html"].endswith("doc.html")
            assert results["pdf"].endswith("doc.pdf")
    finally:
        renderer_mod = sys.modules["src.core.renderer"]
        renderer_mod.PDFRenderer = original
    print("[PASS] test_html_and_pdf_export")


def test_unsupported_format_not_in_results():
    """Неподдерживаемый формат пропускается (warning), в results не попадает."""
    original = _patch_pdf_renderer()
    try:
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "doc.md")
            with open(src, "w", encoding="utf-8") as f:
                f.write("# T")
            out_dir = os.path.join(d, "out")
            os.makedirs(out_dir, exist_ok=True)
            results = multi_export.multi_export(src, out_dir, ["bogus"], template_dir=d)
            assert results == {}, f"Ожидался пустой результат, получено {results}"
    finally:
        sys.modules["src.core.renderer"].PDFRenderer = original
    print("[PASS] test_unsupported_format_not_in_results")


def test_failing_renderer_isolated():
    """Падение одного формата не ломает остальные — фиксируется как ERROR."""
    class _BoomPDF(_FakePDFRenderer):
        def render_html(self, *a, **k):
            raise RuntimeError("boom")

    import src.core.renderer as renderer_mod
    original = renderer_mod.PDFRenderer
    renderer_mod.PDFRenderer = _BoomPDF
    try:
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "doc.md")
            with open(src, "w", encoding="utf-8") as f:
                f.write("# T")
            out_dir = os.path.join(d, "out")
            os.makedirs(out_dir, exist_ok=True)
            results = multi_export.multi_export(src, out_dir, ["html", "pdf"], template_dir=d)
            assert results["html"].startswith("ERROR:"), results["html"]
            assert "boom" in results["html"]
            assert results["pdf"] == os.path.join(out_dir, "doc.pdf")
    finally:
        renderer_mod.PDFRenderer = original
    print("[PASS] test_failing_renderer_isolated")


def test_export_summary_marks_status():
    """export_summary помечает успех ✅ и ошибку ❌."""
    summary = multi_export.export_summary({"pdf": "/tmp/a.pdf", "html": "ERROR: nope"})
    lines = summary.splitlines()
    assert lines[0] == "Multi-export results:"
    assert "✅ pdf: /tmp/a.pdf" in summary
    assert "❌ html: ERROR: nope" in summary
    print("[PASS] test_export_summary_marks_status")


def test_options_defaults_without_options():
    """Без options используются дефолты (не падает)."""
    original = _patch_pdf_renderer()
    try:
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "doc.md")
            with open(src, "w", encoding="utf-8") as f:
                f.write("# T")
            out_dir = os.path.join(d, "out")
            os.makedirs(out_dir, exist_ok=True)
            results = multi_export.multi_export(src, out_dir, ["html"], template_dir=d)
            assert not results["html"].startswith("ERROR")
            assert _FakePDFRenderer.last_kwargs["doc_theme"] == "theme_modern.css"
    finally:
        sys.modules["src.core.renderer"].PDFRenderer = original
    print("[PASS] test_options_defaults_without_options")


def main():
    tests = [
        test_html_and_pdf_export,
        test_unsupported_format_not_in_results,
        test_failing_renderer_isolated,
        test_export_summary_marks_status,
        test_options_defaults_without_options,
    ]
    for t in tests:
        t()
    print("\nAll multi-export tests passed!")


if __name__ == "__main__":
    main()
