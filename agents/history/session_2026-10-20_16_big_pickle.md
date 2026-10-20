# Лог сессии: 2026-10-20 — Big Pickle (офлайн-кэш LaTeX/Kroki)

## Цель
Офлайн-замена внешних зависимостей LaTeX (CodeCogs) и диаграмм (Kroki) — локальный кэш.

## Действия
- Создан src/core/render_cache.py
- Кэш для latex_to_url и Kroki URL
- Добавлена поддержка mermaid в parser.preprocess_diagrams
- Тесты: 25/25

## Результат
Повторные формулы/диаграммы берутся из локального кэша.

