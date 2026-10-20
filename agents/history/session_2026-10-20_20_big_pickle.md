# Лог сессии: 2026-10-20 — Big Pickle (smoke: реальный экспорт)

## Цель
Покрыть smoke-проверкой реальный путь экспорта (HTML/DOCX) без PDF-движка.

## Действия
- scripts/smoke_gui.py: добавлен headless multi_export (HTML + DOCX)
- Обработка особенностей multi_export (возвращает строку-ошибку вместо исключения)
- gui-smoke.yml: установка markdown/jinja2/python-docx/htmldocx
- Батарея 26/26

## Находка
multi_export не бросает исключение при сбое рендерера, а кладёт в результат
строку ERROR — smoke учёл это (проверка isfile+size).

## Результат
CI проверяет и GUI, и реальный экспорт.

