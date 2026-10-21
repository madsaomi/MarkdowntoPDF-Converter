# Лог сессии: 2026-10-21 — Big Pickle (PLAN-013: рост покрытия 42 % → 62 %)

## Цель
Покрытие «по упоминанию» создавало ложное ощущение защищённости: 83 модуля
упомянуты тестами, но покрытие строк — 42 %, а 17 модулей — 0 %.

## Действия

### Замер и инфраструктура
- Замер: `coverage run --source=src -m pytest tests/ -q` → **42 %**.
- Обнаружено: `tests/run_all.py` запускает каждый тест отдельным подпроцессом,
  поэтому `coverage run` видел 0 %. Те же тесты полностью проходят под
  `pytest` в одном процессе (337 → 453 passed) — измерение возможно без
  изменения канонического раннера.
- Создан `.github/workflows/coverage.yml` (Python 3.12, pytest + coverage,
  `--fail-under`), бейдж в README, раздел «Tests» с командой измерения.

### Тесты (5 новых файлов, +106 проверок)
| Файл | Проверок | Что покрывает |
|---|---|---|
| `test_coverage_core.py` | 23 | `cloud_templates` (fallback индекса, SSRF-блокировка, локальное хранилище), `citation_manager` (APA/MLA, библиография, ключи), `snippets` (дефолты, битый JSON), `pdf_to_markdown` |
| `test_coverage_mixins.py` | 27 | `view_dialogs` (аналитика, LaTeX, tag cloud, граф), `editor_tools` (статистика, цель, поиск/замена), `education` (карточки, Anki, глоссарий, квиз) |
| `test_coverage_mixins2.py` | 28 | `editor_formatting`, `convert_tools` (PDF/HTML/OCR), `integrations`, `workspace` |
| `test_coverage_support.py` | 28 | `export_tools`, `presets`, `tts_media`, `toast`, `multi_cursor`, `watermark_designer` |
| `test_main_window.py` | 12 | Настоящий `MainWindow` offscreen: раскладка, меню, превью, режимы, статистика, поиск/замена |

### Итог по покрытию
| Модуль | Было | Стало |
|---|---|---|
| `core/cloud_templates.py` | 0 % | 100 % |
| `core/citation_manager.py` | 0 % | 100 % |
| `core/snippets.py` | 0 % | 97 % |
| `core/pdf_to_markdown.py` | 0 % | 95 % |
| `gui/mixins/view_dialogs.py` | 10 % | 96 % |
| `gui/mixins/editor_tools.py` | 12 % | 91 % |
| `gui/mixins/education.py` | 20 % | 100 % |
| `gui/mixins/convert_tools.py` | 24 % | 70 % |
| `gui/mixins/editor_formatting.py` | 34 % | 97 % |
| `gui/mixins/export_tools.py` | 39 % | 74 % |
| `gui/mixins/presets.py` | 40 % | 98 % |
| `gui/mixins/workspace.py` | 40 % | 100 % |
| `gui/toast.py` | 15 % | 91 % |
| `gui/multi_cursor.py` | 24 % | 100 % |
| `gui/watermark_designer.py` | 11 % | 93 % |
| `gui/ui_layout.py` | 1 % | 99 % |
| `gui/main_window.py` | 15 % | 53 % |
| **ИТОГО по `src/`** | **42 %** | **62 %** |

## Замечания по ходу
- Хосты-фейки для диалогов должны наследоваться от `QWidget` — иначе Qt
  отвергает их как родителя.
- `QTextBrowser.toHtml()` пере-сериализует документ: текст проверяем через
  `toPlainText()`.
- offscreen-платформа слегка корректирует позицию окон — для toast
  используется допуск ±60 px.
- `_Combo` в фейках пресетов нужен с `setEnabled` — вызывается при применении.
- `save_preset`/`delete_preset` вызывают `self.load_presets()`, поэтому хост
  должен наследовать сам миксин.

## Результат
- Покрытие **42 % → 62 %**, ни одного модуля на 0 %.
- Порог в CI: 48 % → **55 %** (фактический уровень ~62 %).
- Батарея: `run_all.py` **52/52**, `pytest` **453 passed**.
- Все 5 workflow в CI зелёные: Tests, GUI Smoke, **Coverage**, E2E Export,
  Second Brain Integrity Check.
- План [`plan_013_coverage_improvement.md`](file:///agents/plans/plan_013_coverage_improvement.md)
  закрыт.
