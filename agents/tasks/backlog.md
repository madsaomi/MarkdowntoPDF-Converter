# 📋 Бэклог Проекта (BACKLOG.md)

Список будущих задач, улучшений, фич и технических долгов для проекта **Markdown to PDF Converter Pro**.

> [!TIP]
> Когда задача берется в работу, перенеси её описание в `agents/tasks/active_task.md`.

---

## 🚀 Предстоящие задачи (Upcoming Tasks)

### 📌 Высокий приоритет (High)
- [x] **TASK-001 (✅ 2026-10-20, коммит `79ae4e5`):** Устранение критических багов по итогам аудита от 2026-10-20:
  - `main_window.py:1021` — `self.history_layout` нигде не создаётся → **FIXED** (вкладка History в `ui_layout.py`).
  - `window_tools.py:31` — импорт несуществующей функции `show_conversion_history` → **FIXED** (переключение вкладки).
  - `window_tools.py:542` — `NameError: QInputDialog` → **FIXED** (импорт добавлен).
  - `pptx_renderer.py:77` — `IndexError` при контенте до первого заголовка → **FIXED** (+ регрессионный тест `tests/test_pptx_parser.py`).
  - `image_renderer.py:45,108-116` — утечка temp-логфайла WeasyPrint → **FIXED** (+ защита `temp_pdf_path` в finally).
  - Детали: [`BUG_001`](file:///agents/bugs_and_fixes/BUG_001_critical_gui_pptx_bugs.md), [`PLAN-001`](file:///agents/plans/plan_001_fix_critical_bugs.md).
- [x] **TASK-002 (✅ 2026-10-20, коммит `ffcbbe6`):** Решение по PDF-движку: резолвер `AppConfig.resolve_weasyprint_cmd()` (exe → pip `weasyprint` → понятная ошибка), `build.py` не падает без движка (+`--skip-pdf-engine`), добавлен `setup_pdf_engine.ps1`. См. [`PLAN-002`](file:///agents/plans/plan_002_weasyprint_engine_resolver.md).

### 📌 Средний приоритет (Medium)
- [x] **TASK-003 (✅ 2026-10-20, коммит `1db3a81`):** Чистка мёртвого и дублирующегося кода GUI: удалены 19 неиспользуемых импортов, неиспользуемый `self.translator`, `EMOJI_MAP`, `preview_code_theme`, недостижимый дубль `set_writing_goal`, 6 затенённых дублей методов миксина в `window_tools.py`, дубль connect-панели поиска (−119 строк). Попутно опровергнут пункт аудита: `save_version` достижим из меню — сохранён. См. [PLAN-003](file:///agents/plans/plan_003_cleanup_dead_code.md).
- [x] **TASK-004 (✅ 2026-10-20, коммит `451bfc9`):** Починка 4 хрупких UI-механик: `toggle_split_view` (2 виджета — теперь через `setVisible`), watermark-дизайнер (`build_watermark_css()` → новый `watermark_css` реально доходит до PDF), меню Language/Tools/Help переводится, `closeEvent` останавливает потоки и таймеры. См. [PLAN-004](file:///agents/plans/plan_004_fix_brittle_ui.md).
- [x] **TASK-005 (✅ 2026-10-20, коммит `bb9426e`):** Расширение тестового покрытия: 8 новых файлов (`test_renderers`, `test_reveal_exporter`, `test_multi_export`, `test_plugin_system`, `test_github_sync`, `test_pdf_encrypt`, `test_gui_stubs`; OCR — внутри `test_renderers`), CI ставит PyQt6 и зависимости рендереров, матрица Python 3.10–3.14. Итог: **18/18** зелёных. Попутно исправлен [BUG_002](file:///agents/bugs_and_fixes/BUG_002_reveal_js_slide_split.md) (нарезка слайдов Reveal.js). См. [PLAN-005](file:///agents/plans/plan_005_test_coverage.md).

### 📌 Низкий приоритет (Low)
- [x] **TASK-006 (✅ 2026-10-20, коммит `688f55f`):** Зависимости синхронизированы: жёсткие пины `requirements.txt` → диапазоны `>=`, выровнены с `pyproject.toml`; объявлен `SpeechRecognition>=3.10` (использовался в `main_window.py`, но не был задекларирован); добавлен `markupsafe>=2.1` и extra `speech`. Новый тест `tests/test_dependency_sync.py` (5 проверок: согласованность множеств, объявление SpeechRecognition, «используется в коде → объявлено» через AST, отсутствие `==`-пинов, парсинг pyproject с fallback для Python 3.10). Итог: **19/19** зелёных. См. [PLAN-006](file:///agents/plans/plan_006_dependency_sync.md).
- [x] **TASK-007 (✅ 2026-10-20, коммит `aae3974`):** Устранены 4 мелких бага ядра: (1) дублирующийся лог «Сохранено» — ветки PPTX/REVEAL/PNG-JPG убраны, суффикс «(N slides/pages)» перенесён в единый emit; (2) шэдоуинг `QThread.finished` — сигнал `KrokiCheckThread` переименован в `checked` (+ потребитель в `main_window.py`); (3) busy-wait паузы в `tts_engine.py` заменён на `threading.Event.wait(timeout=0.1)`; (4) `<html lang="en">` в `base.html` → `{{ lang | default('en') }}` (проброшен из `renderer.py`). Новый тест `tests/test_core_fixes_007.py` (6 проверок). Итог: **20/20** зелёных. См. [PLAN-007](file:///agents/plans/plan_007_core_fixes.md).
- [x] **TASK-008 (✅ 2026-10-20, коммит `c26c383`):** Судьба фичевых заглушек решена: 6 методов с рабочими локальными реализациями (`show_ai_assistant`, `ai_improve_text`, `ai_generate_outline`, `export_task_board`, `generate_api_docs`, `start_voice_input`) подключены к меню Tools (секция «AI & Productivity»); удалён мёртвый декор — `splash_screen.py` (`ModernSplashScreen`), `custom_titlebar.py`, `ambient_glow.py` и их неиспользуемые импорты (−307 строк). Новый тест `tests/test_stub_wiring_008.py` (5 проверок). Итог: **21/21** зелёных. См. [PLAN-008](file:///agents/plans/plan_008_feature_stubs.md).
- [x] **TASK-009 (✅ 2026-10-20, коммит `2b3566d`, веха M4 «Релиз»):** Закрыта релизная веха. (1) `.github/workflows/release.yml` — по тегу `v*`: job `test` (ubuntu) → job `build-windows` (`build.py --skip-pdf-engine` → Inno Setup через choco → `upload-artifact` + `softprops/action-gh-release`). (2) `scripts/build_release.ps1` — локальная сборка `.exe` + опционально инсталлятор Inno Setup (проверка окружения, `-Clean`/`-Console`/`-SkipPdfEngine`/`-SkipInstaller`); файл сохранён в UTF-8 **with BOM** (иначе PowerShell 5.1 ломается на кириллице). и (3) README актуализирован: бейджи на реальный репозиторий + badge релиза, структура (`src/config.py` + 28 core + 26 gui), «22 test files», раздел Build/Release. Новый тест `tests/test_release_config.py` (6 проверок, без PyYAML). Итог: **22/22** зелёных. См. [PLAN-009](file:///agents/plans/plan_009_release_milestone.md).

### 💡 Идеи на будущее (Ideas & Nice-to-Have)
- [ ] Офлайн-замена внешних зависимостей: LaTeX (CodeCogs) и диаграммы (Kroki) → локальный рендер или кэш формул.
- [ ] Вынести блокирующие GUI-операции (OCR, PDF→MD, GitHub sync, распознавание речи) в фоновые потоки.
- [ ] Перевести превью на тот же рендер-путь, что и экспорт (Jinja2-шаблоны), для визуального соответствия.
- [ ] Честная маркировка декоративных фич (AI-ассистент, переводчик, Plugin Marketplace, облачные шаблоны).
