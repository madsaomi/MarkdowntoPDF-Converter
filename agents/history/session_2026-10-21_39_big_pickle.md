# Лог сессии: 2026-10-21 — Big Pickle (E2E-воркфлоу с настоящим WeasyPrint)

## Цель
Закрыть последний пробел: реальный рендер не проверялся ни одним тестом.

## Действия
- Создан `tests/test_e2e_export.py` (3 проверки):
  - настоящий экспорт в PDF (WeasyPrint) — файл > 1 КБ, сигнатура `%PDF-`,
    читается pypdf, страниц ≥ 1;
  - настоящий экспорт в PNG (WeasyPrint + PyMuPDF) — валидная сигнатура PNG;
  - `multi_export` с реальными рендерерами: pdf/html/docx/epub/pptx — все
    файлы созданы и непусты.
- Тест корректно **пропускается**, если движка нет (обычная матрица CI), но с
  `REQUIRE_E2E=1` отсутствие движка становится ошибкой.
- Создан workflow `.github/workflows/e2e.yml`: Python 3.12, apt-установка
  pango/cairo/gdk-pixbuf + шрифты, `pip install weasyprint PyMuPDF …`,
  проверка `python -m weasyprint --version`, запуск e2e-теста с
  `REQUIRE_E2E=1`.
- Тест зарегистрирован в `run_all.py` (46 → 47), README: бейдж E2E и счётчик.
- Локально WeasyPrint поставить не удалось (Python 3.15, `brotli` без колеса) —
  проверка реального движка выполняется в CI.

## Результат
47/47 локально (e2e пропущен), `test_release_config.py` OK, `brain.py check` 100%.
