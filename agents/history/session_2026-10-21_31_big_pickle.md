# Лог сессии: 2026-10-21 — Big Pickle (тесты core/wikilinks)

## Цель
Покрыть Wikilinks/GraphBuilder.

## Действия
- Создан `tests/test_wikilinks_behavior.py` (8 проверок): извлечение ссылок с display,
  теги с дедупликацией, резолв на существующий файл и fallback на target.md,
  трансclusions с удалением front matter и обработкой отсутствующего файла,
  построение графа (узлы/рёбра, размер узлов) и пустой случай + HTML.
- Зарегистрирован в `run_all.py` (33 → 34), README обновлён.

## Результат
34/34, `test_release_config.py` OK, `brain.py check` 100%.
