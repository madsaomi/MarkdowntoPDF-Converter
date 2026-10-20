# 📐 План реализации: PLAN-001 — Устранение критических багов (Critical Bug Fix)

> **Статус:** ✅ COMPLETED (2026-10-20, коммит `79ae4e5`)  
> **Дата создания:** 2026-10-20  
> **Автор / Агент:** Big Pickle (OpenCode)  
> **Связанная задача:** [TASK-001](file:///agents/tasks/active_task.md)  
> **Целевая ветка / Ревизия:** main  

---

## 1. 🎯 Цель и контекст
- **Проблема / Задача:** Полный аудит кодовой базы (2026-10-20) выявил 5 критических дефектов, которые приводят к падению при типовых сценариях: первый же успешный экспорте роняет GUI (`AttributeError`), пункт меню «Export History» нерабочен (`ImportError`), PPTX-экспорт падает на документах с преамбулой (`IndexError`), PNG/JPG-экспорт утекает temp-файлами.
- **Ожидаемый результат:** Экспорт во всех форматах работает без исключений; журнал экспорта отображается; temp-файлы не накапливаются.

---

## 2. 🔍 Анализ и затронутые компоненты

### Затронутые файлы:
- `[MODIFY]` `src/gui/ui_layout.py` — добавить вкладку «History» в `window.tabs` с контейнером `window.history_layout` (по образцу вкладки Log, строки 347–360).
- `[MODIFY]` `src/gui/window_tools.py:30-32` — `show_conversion_history`: убрать импорт несуществующей `document_tools.show_conversion_history`, заменить на переключение на вкладку History.
- `[MODIFY]` `src/gui/window_tools.py:1-10` — добавить отсутствующий импорт `QInputDialog` (используется в `show_cloud_templates:542`).
- `[MODIFY]` `src/core/pptx_renderer.py:73-78` — `_flush_content`: защита от пустого `self.slides` (контент до первого H1/H2 → IndexError).
- `[MODIFY]` `src/core/image_renderer.py:108-116` — `finally`: удалять `temp_err_path` (утечка лог-файла WeasyPrint при каждом рендере).

### Зависимости и влияние:
- Новые библиотеки: НЕТ.
- Влияние на API: НЕТ (изменения внутренние, публичные сигнатуры не меняются).
- Риск ломающих изменений: НЕТ.

---

## 3. 📝 Пошаговый план реализации (Atomic Steps)

- [x] **Этап 1: GUI — журнал экспорта**
  - [x] Шаг 1.1: Добавить вкладку History + `window.history_layout` в `ui_layout.py`.
  - [x] Шаг 1.2: Переписать `show_conversion_history` на переключение вкладки (без битого импорта).
- [x] **Этап 2: GUI — импорт QInputDialog**
  - [x] Шаг 2.1: Добавить `QInputDialog` в импорты `window_tools.py`.
- [x] **Этап 3: Ядро — рендереры**
  - [x] Шаг 3.1: Исправить `_flush_content` в `pptx_renderer.py` (garbage-slide вместо IndexError).
  - [x] Шаг 3.2: Добавить удаление `temp_err_path` в `finally` `image_renderer.py` (+ `temp_pdf_path` — дополнительный фикс NameError в finally).
- [x] **Этап 4: Верификация**
  - [x] Шаг 4.1: `python -m py_compile` всех изменённых файлов.
  - [x] Шаг 4.2: Запуск `python tests/run_all.py` — 8/8 файлов зелёные.
  - [x] Шаг 4.3: Юнит-тест на фикс PPTX (преамбула до первого заголовка) — `tests/test_pptx_parser.py`.

---

## 4. 🛡️ Риски, сайд-эффекты и план отката (Rollback Strategy)
- **Потенциальные риски:** Новая вкладка слегка меняет нижнюю панель UI; стиль вкладки наследуется от существующей QSS.
- **План отката:** `git checkout -- src/gui/ui_layout.py src/gui/window_tools.py src/core/pptx_renderer.py src/core/image_renderer.py` (фикс — один атомарный коммит).

---

## 5. 🧪 План тестирования и критерии приемки
1. Автоматические тесты: `python tests/run_all.py` + новый тест PPTX-парсера.
2. Ручная проверка: экспорт PDF/PNG (при наличии weasyprint.exe), пункт меню «Export History» открывает вкладку с журналом.
3. Критерий "Готово" (Definition of Done):
   - [ ] Все изменённые файлы компилируются без ошибок.
   - [ ] Тесты проходят.
   - [ ] Чек-лист задачи TASK-001 полностью отмечен `[x]`.
