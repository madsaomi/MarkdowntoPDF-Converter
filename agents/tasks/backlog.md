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
- [ ] **TASK-003:** Чистка мёртвого и дублирующегося кода GUI: неиспользуемые импорты `main_window.py`, дубли методов MainWindow ↔ ToolMethodsMixin (6 пар), неиспользуемый `Translator`, неинстанцируемый `ModernSplashScreen`, закомментированные `CustomTitleBar`/`AmbientGlowWidget`.
- [ ] **TASK-004:** Починка хрупких UI-механик: `toggle_split_view` (3 размера для сплиттера с 2 виджетами, `window_tools.py:247-255`), watermark-дизайнер отбрасывает результат (`window_tools.py:94-96`), меню Language не переводится (`main_window.py:803-807`), `closeEvent` не останавливает потоки и таймеры.
- [ ] **TASK-005:** Расширение тестового покрытия: не покрыто ничего из рендереров (PDF/DOCX/EPUB/PPTX/Image), TTS/OCR, github_sync, plugin_system. CI не ставит PyQt6.

### 📌 Низкий приоритет (Low)
- [ ] **TASK-006:** Привести в соответствие `requirements.txt` и `pyproject.toml` (дрейф версий); добавить объявление `speech_recognition` (используется, но не объявлен); убрать мёртвый `WeasyPrint==61.2` или начать его использовать.
- [ ] **TASK-007:** Фиксация мелких багов ядра: дублирующийся лог «saved» в `threads.py:100-149`, шэдоуинг встроенного сигнала `QThread.finished` (`threads.py:18`), busy-wait в `tts_engine.py:181-183`, `<html lang="en">` захардкожен в `templates/base.html:2`.

### 💡 Идеи на будущее (Ideas & Nice-to-Have)
- [ ] Офлайн-замена внешних зависимостей: LaTeX (CodeCogs) и диаграммы (Kroki) → локальный рендер или кэш формул.
- [ ] Вынести блокирующие GUI-операции (OCR, PDF→MD, GitHub sync, распознавание речи) в фоновые потоки.
- [ ] Перевести превью на тот же рендер-путь, что и экспорт (Jinja2-шаблоны), для визуального соответствия.
- [ ] Честная маркировка декоративных фич (AI-ассистент, переводчик, Plugin Marketplace, облачные шаблоны).
