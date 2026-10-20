"""Тесты контрактов рендереров (PLAN-005/TASK-005).

Внешние библиотеки (python-docx, htmldocx, ebooklib, python-pptx, Pillow)
в окружении CI/локали могут отсутствовать. Тогда рендерер ОБЯЗАН поднять
понятный ImportError с инструкцией установки, а не падать с AttributeError
или молча создавать пустой файл.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.docx_renderer import DOCXRenderer, Document, HtmlToDocx
from src.core.pptx_renderer import PPTXRenderer
from src.core import epub_renderer, ocr_engine

HTML = "<h1>Заголовок</h1><p>Текст</p>"
META = {"title": "Документ", "author": "Автор", "date": "2026-10-20"}


def test_docx_import_error_or_render(tmp_path=None):
    """Без python-docx/htmldocx — понятный ImportError, с ними — файл создаётся."""
    renderer = DOCXRenderer()
    out = os.path.join(os.path.dirname(__file__), "_tmp_docx.docx")
    try:
        if Document is None or HtmlToDocx is None:
            try:
                renderer.render(HTML, META, out)
            except ImportError as e:
                assert "pip install" in str(e), f"ImportError без инструкции: {e}"
                print("[PASS] test_docx_import_error_or_render: понятный ImportError без python-docx")
                return
            raise AssertionError("Ожидался ImportError при отсутствии python-docx")
        renderer.render(HTML, META, out)
        assert os.path.exists(out) and os.path.getsize(out) > 0
        print("[PASS] test_docx_import_error_or_render: DOCX создан")
    finally:
        if os.path.exists(out):
            os.remove(out)


def test_epub_import_error_or_render():
    """Без ebooklib — понятный ImportError; с ним — файл создаётся."""
    renderer = epub_renderer.EPUBRenderer()
    out = os.path.join(os.path.dirname(__file__), "_tmp_epub.epub")
    try:
        try:
            renderer.render(HTML, META, out)
        except ImportError as e:
            assert "pip install" in str(e), f"ImportError без инструкции: {e}"
            print("[PASS] test_epub_import_error_or_render: понятный ImportError без ebooklib")
            return
        assert os.path.exists(out) and os.path.getsize(out) > 0
        print("[PASS] test_epub_import_error_or_render: EPUB создан")
    finally:
        if os.path.exists(out):
            os.remove(out)


def test_pptx_import_error_or_render():
    """Без python-pptx — понятный ImportError; с ним — файл и число слайдов."""
    renderer = PPTXRenderer()
    out = os.path.join(os.path.dirname(__file__), "_tmp_pptx.pptx")
    try:
        try:
            count = renderer.render(HTML, META, out)
        except ImportError as e:
            assert "pip install" in str(e), f"ImportError без инструкции: {e}"
            print("[PASS] test_pptx_import_error_or_render: понятный ImportError без python-pptx")
            return
        assert count >= 1, f"Ожидался >= 1 слайд, получено {count}"
        assert os.path.exists(out) and os.path.getsize(out) > 0
        print(f"[PASS] test_pptx_import_error_or_render: PPTX создан ({count} слайдов)")
    finally:
        if os.path.exists(out):
            os.remove(out)


def test_ocr_import_error():
    """Без pytesseract/Pillow image_to_text обязан поднять ImportError с инструкцией."""
    try:
        ocr_engine.image_to_text("nope.png")
    except ImportError as e:
        assert "pip install" in str(e), f"ImportError без инструкции: {e}"
        print("[PASS] test_ocr_import_error: понятный ImportError без OCR-зависимостей")
        return
    except Exception as e:
        raise AssertionError(f"Ожидался ImportError, получено {type(e).__name__}: {e}")
    print("[PASS] test_ocr_import_error: OCR-зависимости установлены (рендер пропущен)")


def test_batch_ocr_degrades_gracefully():
    """batch_ocr не падает при отсутствии зависимостей — возвращает сообщение об ошибке."""
    result = ocr_engine.batch_ocr(["missing1.png", "missing2.png"])
    assert set(result.keys()) == {"missing1.png", "missing2.png"}
    for value in result.values():
        assert value.startswith("[OCR Error:"), value
    print("[PASS] test_batch_ocr_degrades_gracefully: ошибки изолированы по файлу")


def main():
    tests = [
        test_docx_import_error_or_render,
        test_epub_import_error_or_render,
        test_pptx_import_error_or_render,
        test_ocr_import_error,
        test_batch_ocr_degrades_gracefully,
    ]
    for t in tests:
        t()
    print("\nAll renderer contract tests passed!")


if __name__ == "__main__":
    main()
