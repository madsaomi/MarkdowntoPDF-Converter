# 📋 Бэклог Проекта (BACKLOG.md)

Список будущих задач, улучшений, фич и технических долгов для проекта **Markdown to PDF Converter Pro**.

> [!TIP]
> Когда задача берется в работу, перенеси её описание в `agents/tasks/active_task.md`.

---

## 🚀 Предстоящие задачи (Upcoming Tasks)

### 📌 Высокий приоритет (High)
- [ ] **TASK-001:** Устранение критических багов по итогам аудита от 2026-10-20:
  - `main_window.py:1021` — `self.history_layout` нигде не создаётся → `AttributeError` при первом экспорте.
  - `window_tools.py:31` — импорт несуществующей функции `show_conversion_history` из `document_tools` → пункт меню «Export History» падает.
  - `window_tools.py:542` — `NameError: QInputDialog` в `show_cloud_templates`.
  - `pptx_renderer.py:77` — `IndexError` при контенте до первого заголовка (пустой `self.slides`).
  - `image_renderer.py:45,108-116` — утечка temp-логфайла WeasyPrint при каждом экспорте PNG/JPG.
- [ ] **TASK-002:** Решить проблему движка PDF: `weasyprint-windows/dist/weasyprint.exe` отсутствует в репозитории, pip-пакет `WeasyPrint==61.2` нигде не импортируется. Без внешнего бинарника рендер PDF невозможен, сборка на чистом клоне падает (`build.py:43`, `renderer.py:118`).

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
