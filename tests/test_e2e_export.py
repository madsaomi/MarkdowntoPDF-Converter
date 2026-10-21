"""Сквозной тест экспорта с НАСТОЯЩИМ движком (WeasyPrint + PyMuPDF).

Обычная матрица CI не ставит WeasyPrint (нужны системные библиотеки pango),
поэтому здесь тест корректно пропускается. Отдельный workflow `e2e.yml`
устанавливает движок и запускает тест с `REQUIRE_E2E=1` — тогда пропуск
превращается в ошибку, и экспорт проверяется по-настоящему.

Что проверяется:
- Markdown → HTML → PDF (настоящий WeasyPrint), PDF читается pypdf;
- Markdown → PDF → PNG (настоящий WeasyPrint + PyMuPDF), валидный PNG;
- multi_export с реальными рендерерами: pdf/html/docx/epub/pptx.
"""
import importlib.util
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# REQUIRE_E2E=1 — движок обязателен, отсутствие = ошибка, а не пропуск.
REQUIRE_E2E = os.environ.get("REQUIRE_E2E", "").strip().lower() in ("1", "true", "yes")

MARKDOWN = """# Тестовый документ

Параграф с **жирным** и *курсивным* текстом.

## Список

- Пункт один
- Пункт два

## Таблица

| Колонка | Значение |
|:--------|:--------:|
| a       | 1        |

## Код

```python
print("hello")
```
"""


def _weasyprint_works():
    """Проверяет, что движок реально запускается: `python -m weasyprint`."""
    if importlib.util.find_spec("weasyprint") is None:
        return False
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "weasyprint", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )
    except Exception:
        return False
    return proc.returncode == 0


def _pymupdf_available():
    return importlib.util.find_spec("fitz") is not None


def _skip(reason):
    if REQUIRE_E2E:
        raise AssertionError(f"E2E-режим: зависимость недоступна — {reason}")
    print(f"[SKIP] {reason}")
    return True


def _check_dependencies():
    """Возвращает True, если тест следует пропустить."""
    if not _weasyprint_works():
        return _skip("WeasyPrint недоступен (нужны системные библиотеки pango)")
    if not _pymupdf_available():
        return _skip("PyMuPDF (fitz) не установлен")
    return False


def _write_markdown(folder, name="doc.md"):
    path = os.path.join(folder, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(MARKDOWN)
    return path


def test_real_pdf_export():
    """Настоящий экспорт в PDF: файл валиден и читается pypdf."""
    if _check_dependencies():
        return

    from pypdf import PdfReader

    from src.core.parser import MarkdownParser
    from src.core.renderer import PDFRenderer
    from src.config import AppConfig

    with tempfile.TemporaryDirectory() as d:
        md_path = _write_markdown(d)
        html, meta = MarkdownParser().parse(
            MARKDOWN, base_dir=d, kroki_available=False
        )
        assert "<h1" in html.lower(), html[:200]

        out_pdf = os.path.join(d, "out.pdf")
        renderer = PDFRenderer(AppConfig.template_dir(), "")
        renderer.render(html, meta, out_pdf, input_filepath=md_path, lang="ru")

        assert os.path.isfile(out_pdf), out_pdf
        assert os.path.getsize(out_pdf) > 1000, os.path.getsize(out_pdf)
        with open(out_pdf, "rb") as f:
            assert f.read(5) == b"%PDF-", "файл не является PDF"

        reader = PdfReader(out_pdf)
        assert len(reader.pages) >= 1, len(reader.pages)
    print("[PASS] test_real_pdf_export")


def test_real_png_export():
    """Настоящий экспорт в PNG: WeasyPrint → PDF → PyMuPDF → картинка."""
    if _check_dependencies():
        return

    from src.core.parser import MarkdownParser
    from src.core.image_renderer import ImageRenderer
    from src.config import AppConfig

    with tempfile.TemporaryDirectory() as d:
        html, meta = MarkdownParser().parse(
            MARKDOWN, base_dir=d, kroki_available=False
        )
        out_png = os.path.join(d, "out.png")
        renderer = ImageRenderer()
        count = renderer.render(html, meta, out_png, lang="ru", dpi=96)

        assert count >= 1, count
        assert os.path.isfile(out_png), out_png
        assert os.path.getsize(out_png) > 0
        with open(out_png, "rb") as f:
            magic = f.read(8)
        assert magic == b"\x89PNG\r\n\x1a\n", magic
    print("[PASS] test_real_png_export")


def test_real_multi_export_all_formats():
    """multi_export с настоящими рендерерами создаёт все запрошенные файлы."""
    if _check_dependencies():
        return

    from src.core.multi_export import multi_export
    from src.config import AppConfig

    with tempfile.TemporaryDirectory() as d:
        md_path = _write_markdown(d)
        out_dir = os.path.join(d, "out")
        os.makedirs(out_dir, exist_ok=True)

        formats = ["pdf", "html", "docx", "epub", "pptx"]
        results = multi_export(
            md_path, out_dir, formats, template_dir=AppConfig.template_dir()
        )

        for fmt in formats:
            path = results.get(fmt)
            assert path is not None, f"{fmt}: нет результата"
            assert not str(path).startswith("ERROR:"), f"{fmt}: {path}"
            assert os.path.isfile(path), f"{fmt}: файл не создан — {path}"
            assert os.path.getsize(path) > 0, f"{fmt}: пустой файл"
    print("[PASS] test_real_multi_export_all_formats")


def main():
    tests = [
        test_real_pdf_export,
        test_real_png_export,
        test_real_multi_export_all_formats,
    ]
    for t in tests:
        t()
    print("\nAll end-to-end export tests passed!")


if __name__ == "__main__":
    main()
