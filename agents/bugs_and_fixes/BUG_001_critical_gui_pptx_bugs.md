# 🐛 Баг: Критические дефекты GUI и рендереров (комплексный аудит 2026-10-20)

**Дата:** 2026-10-20  
**Статус:** ✅ FIXED (коммит `79ae4e5`, план [PLAN-001](file:///agents/plans/plan_001_fix_critical_bugs.md))  
**Затронутые модули:** `src/gui/ui_layout.py`, `src/gui/window_tools.py`, `src/core/pptx_renderer.py`, `src/core/image_renderer.py`

---

## Симптомы → Причины → Решения

### 1. Падение GUI при первом экспорте
- **Симптом:** `AttributeError: 'MainWindow' object has no attribute 'history_layout'` после первого же успешного экспорта (цепочка `on_finished_one` → `add_to_export_history` → `update_export_history_ui`).
- **Причина:** `update_export_history_ui` работал с контейнером `history_layout`, который нигде не создавался.
- **Решение:** добавлена вкладка «History» в `window.tabs` (`ui_layout.py`) с контейнером `window.history_layout`.

### 2. Нерабочий пункт меню «Export History»
- **Симптом:** `ImportError` при клике — несуществующая функция.
- **Причина:** `window_tools.show_conversion_history` импортировал `show_conversion_history` из `document_tools`, где такой функции никогда не было.
- **Решение:** метод переписан — обновляет журнал и переключает на вкладку History.

### 3. NameError в облачных шаблонах
- **Симптом:** `NameError: name 'QInputDialog' is not defined` в `show_cloud_templates`.
- **Причина:** `QInputDialog` не был импортирован в `window_tools.py`.
- **Решение:** импорт добавлен.

### 4. IndexError в PPTX-экспорте
- **Симптом:** падение экспорта в .pptx на документах с текстом до первого заголовка (`<p>преамбула</p><h1>...`).
- **Причина:** `_SlideParser._flush_content` писал в `self.slides[-1]`, но список слайдов пуст, пока не встретился H1/H2.
- **Решение:** при пустом `self.slides` создаётся вводный слайд с пустым заголовком. Добавлен регрессионный тест `tests/test_pptx_parser.py`.

### 5. Утечка temp-файлов при PNG/JPG-экспорте
- **Симптом:** лог-файл WeasyPrint (`*.log`) накапливался в `%TEMP%` после каждого экспорта изображений; при раннем исключении `finally` мог упасть с `NameError` на `temp_pdf_path`.
- **Причина:** `finally` в `image_renderer.py` удалял только html и pdf, а `temp_err_path`/`temp_pdf_path` могли быть не определены.
- **Решение:** переменные инициализируются `None` до `try`, все три temp-файла удаляются в `finally` (по образцу корректной реализации в `renderer.py`).

---

## Уроки
- Контейнеры виджетов, на которые ссылается UI-код, должны создаваться в `ui_layout.py` — проверять `hasattr`-цепочки при добавлении методов обновления UI.
- Оба рендерера (`renderer.py` и `image_renderer.py`) дублируют паттерн subprocess+tempfiles с расхождениями — при правках синхронизировать оба или вынести общий хелпер.
