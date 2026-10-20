# 📋 Активная задача: TASK-001 — Устранение критических багов

**Статус:** 🔵 IN_PROGRESS  
**Дата создания:** 2026-10-20  
**Исполнитель:** Big Pickle (OpenCode)  
**Приоритет:** HIGH  
**Связанный план:** [PLAN-001](file:///agents/plans/plan_001_fix_critical_bugs.md)  

---

## 🎯 Цель задачи
Устранить 5 критических дефектов, найденных полным аудитом 2026-10-20, приводящих к падению при типовых сценариях использования.

---

## 📌 Пошаговый чек-лист выполнения:

- [ ] **Шаг 1:** `main_window.py` → `update_export_history_ui` падает с `AttributeError: history_layout` — создать контейнер `window.history_layout` (вкладка History в `ui_layout.py`).
- [ ] **Шаг 2:** `window_tools.py:31` — импорт несуществующей функции `show_conversion_history` из `document_tools` → заменить на переключение вкладки.
- [ ] **Шаг 3:** `window_tools.py:542` — `NameError: QInputDialog` → добавить импорт.
- [ ] **Шаг 4:** `pptx_renderer.py:77` — `IndexError` при контенте до первого заголовка → защита пустого `self.slides`.
- [ ] **Шаг 5:** `image_renderer.py` — утечка `temp_err_path` → удаление в `finally`.
- [ ] **Шаг 6:** Верификация: py_compile, `tests/run_all.py`, новый тест PPTX.

---

## 🧪 Критерии готовности (Definition of Done):
1. Экспорт в PDF/DOCX/EPUB/PPTX/HTML не вызывает исключений на документах с преамбулой.
2. Пункт меню «Export History» работает и отображает журнал последних 5 экспортов.
3. Temp-логи WeasyPrint не накапливаются в `%TEMP%`.
4. `python tests/run_all.py` — все тесты зелёные.
