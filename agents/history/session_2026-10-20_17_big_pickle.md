# Лог сессии: 2026-10-20 — Big Pickle (унификация превью и экспорта)

## Цель
Перевести превью на тот же рендер-путь (Jinja2), что и экспорт.

## Действия
- Создан src/core/html_builder.py с build_html_for_preview_and_export()
- Функция переиспользует PDFRenderer.render_html (base.html)
- preview_manager теперь сначала пробует общий путь, при сбое — прежний inline-CSS
- Тесты: 25/25

## Результат
Превью строится тем же шаблоном, что PDF/HTML-экспорт.

