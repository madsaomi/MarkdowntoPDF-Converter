# 📋 Активная задача: TASK-005 — Расширение тестового покрытия ядра

**Статус:** 🔵 IN_PROGRESS  
**Дата создания:** 2026-10-20  
**Исполнитель:** Big Pickle (OpenCode)  
**Приоритет:** MEDIUM  
**Связанный план:** [PLAN-005](file:///agents/plans/plan_005_test_coverage.md)  

---

## 🎯 Цель задачи
Покрыть тестами непокрытые модули `src/core/` (рендереры DOCX/EPUB/PPTX/Reveal/Multi-export, plugin_system,
github_sync, pdf_encrypt, ocr_engine) и добавить GUI-smoke-тесты; CI должен ставить PyQt6 и зависимости рендереров.

---

## 📌 Пошаговый чек-лист выполнения:

- [ ] **Шаг 1:** Тесты рендереров (`test_renderers.py`, `test_reveal_exporter.py`, `test_multi_export.py`).
- [ ] **Шаг 2:** Тесты сервисов (`test_plugin_system.py`, `test_github_sync.py`, `test_pdf_encrypt.py`, `test_ocr_engine.py`).
- [ ] **Шаг 3:** GUI-smoke под Qt-стабом (`test_gui_stubs.py`).
- [ ] **Шаг 4:** CI: PyQt6 + зависимости рендереров + матрица Python.
- [ ] **Шаг 5:** Регистрация в `run_all.py`, `py_compile`, полный прогон.

---

## 🧪 Критерии готовности (Definition of Done):
1. 8 новых тестовых файлов написаны и зелёные.
2. `tests/run_all.py` — все файлы PASS, старые 11 не сломаны.
3. `.github/workflows/test.yml` ставит PyQt6 и зависимости рендереров.
4. Ни один тест не требует сеть, WeasyPrint, tesseract или MS Word.
