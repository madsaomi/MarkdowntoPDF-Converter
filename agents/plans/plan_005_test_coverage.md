# 📐 План реализации: PLAN-005 — Расширение тестового покрытия ядра

> **Статус:** ✅ COMPLETED (2026-10-20, коммит `bb9426e`)  
> **Дата создания:** 2026-10-20  
> **Автор / Агент:** Big Pickle (OpenCode)  
> **Связанная задача:** [TASK-005](file:///agents/tasks/active_task.md)  
> **Целевая ветка / Ревизия:** main  

---

## 1. 🎯 Цель и контекст
- **Проблема / Задача:** аудит показал, что из `src/core/` (28 модулей) покрыто тестами лишь ~10. Полностью не покрыты рендереры (PDF-шаблон, DOCX, EPUB, PPTX, Reveal, Multi-export, Image), `plugin_system`, `github_sync`, `pdf_encrypt`, `ocr_engine`. CI (`.github/workflows/test.yml`) не ставит PyQt6 и не ставит зависимости рендереров.
- **Ожидаемый бизнес/технический результат:** регрессионная сеть для путей экспорта; тесты, которые ловят поломки без внешних бинарей (WeasyPrint/PyQt6 локально недоступны); CI, где тесты реально могут импортировать `src.gui.*`.

---

## 2. 🔍 Анализ и затронутые компоненты

### Затронутые файлы:
- `[NEW]` `tests/test_renderers.py` — ошибки-контракты рендереров без внешних библиотек (DOCX/EPUB/PPTX/Image поднимают понятный `ImportError`), плюс `EPUBRenderer`/`DOCXRenderer` инстанциируются как no-op.
- `[NEW]` `tests/test_reveal_exporter.py` — `export_reveal_js`: разбиение по H1/H2 на слайды, лангуаге-атрибут, титульный слайд, файл записан.
- `[NEW]` `tests/test_multi_export.py` — `multi_export` изолированно (fake-renderer → dict результатов), `export_summary` (✅/❌), graceful degrade для неподдерживаемого формата.
- `[NEW]` `tests/test_plugin_system.py` — `register_plugin`/`hook`/`emit_hook`/`init_plugin`, устойчивость к падающим хукам, `PluginMarketplace` (install/uninstall/search/categories), singleton.
- `[NEW]` `tests/test_github_sync.py` — `is_git_repo`/`git_status`/`git_log`/`git_branch_list`/`git_file_history` на реальном репозитории проекта (read-only); graceful-ошибки на несуществующем пути.
- `[NEW]` `tests/test_pdf_encrypt.py` — `encrypt_pdf` с None-входом/несуществующим файлом → `False` без исключения; корректный путь при отсутствии `pypdf`.
- `[NEW]` `tests/test_ocr_engine.py` — `batch_ocr` деградирует в `[OCR Error: ...]` без падения; `image_to_markdown` пустого текста → `''` (через monkeypatch).
- `[NEW]` `tests/test_gui_stubs.py` — smoke-импорт GUI-модулей (`models`, `translations`, а при наличии PyQt6 — `main_window`) под Qt-стабом; проверяет, что GUI-пакеты не ломаются на этапе импорта.
- `[MODIFY]` `tests/run_all.py` — зарегистрировать 8 новых файлов.
- `[MODIFY]` `.github/workflows/test.yml` — поставить PyQt6 + реальные зависимости (python-docx, htmldocx, ebooklib, python-pptx, pypdf, Pillow, pytesseract, pyttsx3) c `|| true` для необязательных; добавить Python 3.14 в матрицу.

### Зависимости и влияние:
- Новые библиотеки: **нет** (тесты не требуют установки рендереров — проверяются контракты и graceful-пути).
- Влияние на существующие API: **нет** — тесты read-only, меняется только список в раннере и CI.
- Breaking changes: **НЕТ**.

---

## 3. 📝 Пошаговый план реализации (Atomic Steps)

- [x] **Этап 1: Тесты рендереров** — `test_renderers.py` (контракты ImportError DOCX/EPUB/PPTX/OCR + graceful `batch_ocr`), `test_reveal_exporter.py` (нарезка слайдов, lang, титул), `test_multi_export.py` (подмена `PDFRenderer`, изоляция ошибок, `export_summary`).
- [x] **Этап 2: Тесты сервисов ядра** — `test_plugin_system.py` (реестр, хуки с изоляцией падений, marketplace, singleton), `test_github_sync.py` (read-only статус/лог/ветки/история), `test_pdf_encrypt.py` (деградация → `False`), `test_ocr_engine` — в составе `test_renderers.py`.
- [x] **Этап 3: GUI-smoke** — `test_gui_stubs.py` (Qt-стаб; 28 модулей компилируются, 13 импортируются).
- [x] **Этап 4: CI** — `.github/workflows/test.yml`: `PyQt6` + `python-docx htmldocx ebooklib python-pptx Pillow`, матрица Python 3.10–3.14, `fail-fast: false`.
- [x] **Этап 5: Верификация** — 8 файлов зарегистрированы в `run_all.py`; `py_compile` OK; **18/18 файлов зелёные**.

> **Попутно (найдено тестом):** исправлена нарезка слайдов в `reveal_exporter.py` — шаг цикла 2→3 по массиву `re.split` (иначе повреждённые слайды и лишний слайд). Зафиксировано в [`BUG_002`](file:///agents/bugs_and_fixes/BUG_002_reveal_js_slide_split.md).

---

## 4. 🛡️ Риски, сайд-эффекты и план отката
- **Потенциальные риски:** тесты `github_sync` зависят от наличия `git` в CI — есть (ubuntu-latest). Тесты не должны ничего коммитить/пушить (только чтение).
- **План отката:** `git revert` — изменения изолированы в `tests/` и одном CI-файле.

---

## 5. 🧪 План тестирования и критерии приемки
1. Автоматические тесты: `python -m py_compile tests/*.py` + `python tests/run_all.py`.
2. Ручная проверка: `python tests/run_all.py` → **все файлы PASS**, старые 11 не сломаны.
3. Definition of Done:
   - [x] 8 новых тестовых файлов написаны и зелёные.
   - [x] `run_all.py` регистрирует все файлы; суммарно **18** файлов.
   - [x] CI ставит PyQt6 и зависимости рендереров.
   - [x] Ни один тест не требует сеть/внешние бинари (WeasyPrint, tesseract, MS Word).
