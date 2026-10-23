# 📐 План реализации: PLAN-013 — Рост покрытия кода и контроль порога в CI

> **Статус:** ✅ COMPLETED  
> **Дата создания:** 2026-10-21  
> **Автор / Агент:** Big Pickle (OpenCode)  
> **Связанная задача:** [TASK-013](file:///agents/tasks/active_task.md)  
> **Целевая ветка / ревизия:** main  
> **Дата завершения:** 2026-10-21 17:20  
> **Итог:** покрытие `src/` **42 % → 84 %**, порог в CI **79 %**, 63 тест-файла, найдены и исправлены **BUG_008** (CSS-инъекция через колонтитул), **BUG_009** (терялось тело последнего слайда в PPTX), **BUG_010** (импорт CSV ломался при любом разделителе, кроме Auto), **BUG_011** (активная «Назад» на первом шаге тура), **BUG_012** (глоссарий не видел `**Термин** — Определение`) и **BUG_013** (смешанные inline/block формулы ломали HTML превью), добавлен таймаут на тест в раннере  

---

## 1. 🎯 Цель и контекст

- **Проблема / Задача:** все 83 модуля `src/` упомянуты тестами, но фактическое
  покрытие строк — **42 %** (4198 из 7292). Покрытие «по упоминанию» создаёт
  ложное ощущение защищённости: ключевые миксины GUI (`view_dialogs` — 10 %,
  `editor_tools` — 12 %, `tts_media` — 15 %, `education` — 20 %,
  `convert_tools` — 24 %, `editor_formatting` — 34 %, `integrations` — 38 %,
  `export_tools` — 39 %, `presets` — 40 %) и целые ядра (`cloud_templates` — 0 %,
  `citation_manager` — 0 %, `snippets` — 0 %, `pdf_to_markdown` — 0 %) почти не
  проверяются. Регрессии в них не будут пойманы.
- **Ожидаемый результат:** (1) измеримый, воспроизводимый показатель покрытия;
  (2) жёсткий порог в CI, не дающий покрытию падать; (3) закрыты самые
  непокрытые модули с реальной логикой.

### Замер базовой линии (локально, Python 3.15, PyQt6 6.11, pytest 9.1)

```
python -m coverage run --source=src --omit="src/__version__.py" -m pytest tests/ -q
TOTAL 7292 stmts / 4198 miss → 42 %
```

| Модуль | Покрытие | Модуль | Покрытие |
|---|---|---|---|
| `core/cloud_templates.py` | 0 % | `gui/mixins/presets.py` | 40 % |
| `core/citation_manager.py` | 0 % | `gui/mixins/workspace.py` | 40 % |
| `core/snippets.py` | 0 % | `gui/workers/task_worker.py` | 46 % |
| `core/pdf_to_markdown.py` | 0 % | `core/pptx_renderer.py` | 49 % |
| `gui/mixins/view_dialogs.py` | 10 % | `core/html_builder.py` | 51 % |
| `gui/watermark_designer.py` | 11 % | `core/latex_preview.py` | 60 % |
| `gui/mixins/editor_tools.py` | 12 % | `core/html_to_markdown.py` | 70 % |
| `gui/toast.py` | 15 % | `core/quiz_generator.py` | 72 % |
| `gui/mixins/tts_media.py` | 15 % | `core/flashcards.py` | 71 % |
| `gui/mixins/education.py` | 20 % | `core/renderer.py` | 34 % |
| `gui/multi_cursor.py` | 24 % | `gui/mixins/convert_tools.py` | 24 % |
| `gui/mixins/editor_formatting.py` | 34 % | `gui/mixins/integrations.py` | 38 % |
| `gui/mixins/export_tools.py` | 39 % | | |

---

## 2. 🔍 Анализ и затронутые компоненты

### Ключевая находка: тесты одинаково работают под `run_all.py` и под `pytest`

`tests/run_all.py` запускает каждый тест-файл **отдельным подпроцессом** — из-за
этого `coverage run` показывал 0 % (данные子процессов не собирались).
Те же тесты полностью проходят под `pytest` в одном процессе:

```
337 passed in 14.82s
```

Значит, измерение покрытия возможно **без изменения** раннера: отдельный
CI-job запускает `pytest` под `coverage`. Канонический «прогон» остаётся
`run_all.py` (изоляция процессов), измерение — через `pytest`.

### Затронутые файлы:

- `[NEW]` `.github/workflows/coverage.yml` — job измерения покрытия с порогом.
- `[NEW]` `tests/test_coverage_core.py` — тесты «чистых» ядерных модулей:
  `cloud_templates`, `citation_manager`, `snippets`, `pdf_to_markdown`.
- `[NEW]` `tests/test_coverage_mixins.py` — тесты миксинов с наименьшим
  покрытием: `view_dialogs`, `editor_tools`, `tts_media`, `education`,
  `convert_tools`, `editor_formatting`, `integrations`, `export_tools`,
  `presets`, `workspace`.
- `[NEW]` `tests/test_coverage_support.py` — `toast`, `multi_cursor`,
  `watermark_designer`, `workers/task_worker`, `core/renderer`,
  `core/pptx_renderer`, `core/html_builder`, `core/latex_preview`.
- `[MODIFY]` `tests/run_all.py` — регистрация новых тест-файлов.
- `[MODIFY]` `README.md` — счётчик тест-файлов, бейдж Coverage.
- `[MODIFY]` `agents/STATUS.md` — актуализация показателя покрытия.

### Зависимости и влияние:

- Новые пакеты: `coverage` (только для CI-измерения; в `requirements.txt`
  **не** добавляется — это dev-инструмент измерения, а не runtime-зависимость;
  в CI ставится отдельной строкой).
- Влияние на публичные интерфейсы: **НЕТ** — тесты только читают код.
- Breaking changes: **НЕТ**.

---

## 3. 📝 Пошаговый план реализации (Atomic Steps)

- [x] **Этап 1: Инфраструктура измерения**
  - [x] Шаг 1.1: Создан `.github/workflows/coverage.yml` (Python 3.12, `pytest`
    + `coverage`, `--fail-under`).
  - [x] Шаг 1.2: Порог выставлен с запасом относительно измеренного уровня
    (42 % → порог 48 % → после роста до 62 % порог поднят до 55 %).
- [x] **Этап 2: Закрытие «нулевых» модулей**
  - [x] Шаг 2.1: `core/cloud_templates.py` 0 → 100 %, `core/citation_manager.py`
    0 → 100 %, `core/snippets.py` 0 → 97 %, `core/pdf_to_markdown.py` 0 → 95 %.
- [x] **Этап 3: Закрытие миксинов с наименьшим покрытием**
  - [x] Шаг 3.1: `view_dialogs` 10 → 96 %, `editor_tools` 12 → 91 %,
    `education` 20 → 100 %, `convert_tools` 24 → 70 %.
  - [x] Шаг 3.2: `editor_formatting` 34 → 97 %, `integrations` 38 → 75 %,
    `export_tools` 39 → 74 %, `presets` 40 → 98 %, `workspace` 40 → 100 %.
- [x] **Этап 4: Поддерживающие модули**
  - [x] Шаг 4.1: `toast` 15 → 91 %, `multi_cursor` 24 → 100 %,
    `watermark_designer` 11 → 93 %, `gui/ui_layout.py` 1 → 99 %,
    `gui/main_window.py` 15 → 53 %.
  - [x] Шаг 4.2: `core/renderer.py` 34 → 42 %, `core/html_builder.py` 51 → 80 %,
    `mixins/ai_tools.py` 30 → 55 %, `mixins/tts_media.py` 30 → 95 %,
    `mixins/document_ops.py` 30 → 100 %, `mixins/help_dialogs.py` 29 → 100 %.
    **Найден BUG_008:** в `render_html` очищенный `safe_footer` не
    использовался — в шаблон уходил сырой `resolved_footer`, что позволяло
    инъекцию CSS через текст колонтитула.
  - [x] Шаг 4.3: `gui/document_tools.py` 19 → 62 % (читаемость, авто-исправление,
    оглавление, ревизии, черновики, генератор таблиц).
  - [x] Шаг 4.4: Раннеру добавлен таймаут на тест-файл (300 с) — зависший
    модальный диалог больше не блокирует CI на часы.
  - [x] Шаг 4.5: `core/tts_engine.py` 49 → 100 %, `gui/threads.py` 18 → 100 %,
    `core/github_sync.py` 46 → 100 %, `core/pptx_renderer.py` 49 → 100 %.
    **Найден BUG_009:** `_parse_slides` не сбрасывал накопленный текст после
    последнего заголовка — тело финального слайда в PPTX терялось.
- [x] **Этап 5: Верификация и сдача**
  - [x] Шаг 5.1: `python tests/run_all.py` — 57/57; `pytest` — 623 passed.
  - [x] Шаг 5.2: Покрытие пересчитано (71 %), порог в CI поднят до 66 %.
  - [x] Шаг 5.3: Коммит кода → коммит docs → `git push` → CI зелёный
    (5 workflow: Tests, GUI Smoke, Coverage, E2E Export, Integrity).
  - [x] Шаг 5.4: Лог сессии в `agents/history/`, обновлён `STATUS.md`.
- [x] **Этап 6: Пятый пакет покрытия (GUI-диалоги и вспомогательные окна)**
  - [x] Шаг 6.1: `gui/pomodoro.py` 7 → 100 %, `gui/welcome_tour.py` 10 → 100 %
    (`tests/test_coverage_pomodoro_tour.py`, 22 проверки). **Найден BUG_011:**
    `_update_ui()` не вызывался из конструктора — на первом шаге тура кнопка
    «Назад» была видима, а после навигации активная точка меняла цвет
    (`#8b59b6` вместо `#8b5cf6`).
  - [x] Шаг 6.2: `gui/csv_editor.py` 11 → 100 %
    (`tests/test_coverage_csv_editor.py`, 28 проверок). **Найден BUG_010:**
    `_detect_delimiter` возвращал подпись пункта комбобокса вместо символа —
    выбор любого разделителя, кроме «Auto», ронял импорт с `TypeError`;
    `_load_rows` при пустом вводе оставлял `_loading = True`.
  - [x] Шаг 6.3: `gui/dialogs/export.py` 10 → 100 %
    (`tests/test_coverage_dialogs_export.py`, 15 проверок).
  - [x] Шаг 6.4: `gui/dialogs/content.py` 8 → 100 %
    (`tests/test_coverage_dialogs_content.py`, 41 проверка: сборка книги,
    TOC, генератор таблиц, шаблоны и библиотека сниппетов).
  - [x] Шаг 6.5: `run_all.py` — 61/61; `pytest` — 729 passed; покрытие **81 %**,
    порог в CI поднят до **76 %**, README обновлён (61 тест-файл, 76 %).
- [x] **Этап 7: Шестой пакет покрытия (ядро, файловый менеджер, воркер)**
  - [x] Шаг 7.1: `gui/file_manager.py` 34 → 100 %
    (`tests/test_coverage_file_manager.py`, 32 проверки: выбор файлов/папки,
    история, explorer, загрузка/сохранение файла, фильтр).
  - [x] Шаг 7.2: `core/pdf_encrypt.py` 56 → 100 %, `core/glossary.py` 59 → 100 %,
    `core/latex_preview.py` 60 → 100 %, `core/ocr_engine.py` 69 → 100 %,
    `gui/workers/task_worker.py` 46 → 100 %
    (`tests/test_coverage_core_small.py`, 30 проверок).
    **Найден BUG_012:** `extract_definitions` не распознавал
    `**Термин** — Определение` (пробел перед разделителем), хотя это
    заявлено в docstring.
    **Найден BUG_013:** `render_latex_in_html` применял смещения в порядке
    выдачи `find_latex_expressions` (сначала блочные, потом inline) — при
    смешанных формулах HTML разрезался тегами `<img>`.
  - [x] Шаг 7.3: `run_all.py` — 63/63; `pytest` — 791 passed + 1 падение
    `test_release_config` (ожидаемо: README), после обновления README — зелёный;
    покрытие **84 %**, порог в CI поднят до **79 %**.

---

## 4. 🛡️ Риски, сайд-эффекты и план отката

- **Потенциальные риски:**
  - Порог покрытия в CI может не совпасть с локальным (разные версии
    библиотек, PyQt6). → Страховка: порог ставится ниже измеренного уровня,
    затем подтягивается отдельным коммитом после подтверждения на CI.
  - Тесты под `pytest` выполняются в одном процессе — возможна нежелательная
    интерференция между модулями (например, подмена `sys.modules`). → Проверка:
    полный прогон `pytest` в локальном и CI-окружении; при конфликте —
    изолировать через фикстуры.
  - Новые тесты могут оказаться «проверкой заглушки», а не поведения. →
    Каждый тест должен проверять наблюдаемый результат (файл, значение,
    сигнал), а не факт вызова.
- **План отката:** `git checkout -- <файл>` для изменённых; удаление новых
  файлов `git rm -f`; workflow отключается удалением файла.

---

## 5. 🧪 План тестирования и критерии приемки

1. Автоматические тесты: `python tests/run_all.py` (канонический прогон) и
   `python -m pytest tests/ -q` (прогон под coverage).
2. Измерение: `python -m coverage run --source=src --omit="src/__version__.py" -m pytest tests/ -q` + `coverage report`.
3. Ручная проверка: отсутствует — изменения только в тестах и CI.
4. **Критерий «Готово»:**
   - [x] Покрытие `src/` поднято до ≥ 60 % (с 42 %) — **фактически 84 %**.
   - [x] Ни один модуль `src/` не остаётся на 0 % покрытия.
   - [x] В CI работает job Coverage с порогом **79 %**; локальный и CI-показатели
         расходятся не более чем на 2 п. п.
   - [x] `run_all.py` (63/63) и `pytest` (790) зелёные; все 5 workflow в CI зелёные.
   - [x] Чек-лист полностью выполнен `[x]`.
   - [x] Побочный эффект: найдены и исправлены BUG_008 (CSS-инъекция через
         неочищенный колонтитул), BUG_009 (потеря тела последнего слайда PPTX),
         BUG_010 (импорт CSV при явном разделителе), BUG_011 (первый шаг тура),
         BUG_012 (пробел перед тире в глоссарии) и BUG_013 (смешанные формулы).
   - [x] Раннер защищён от зависания: таймаут 300 с на тест-файл.
