# 📋 Активная задача: TASK-006 — Синхронизация зависимостей

**Статус:** 🔵 IN_PROGRESS  
**Дата создания:** 2026-10-20  
**Исполнитель:** Big Pickle (OpenCode)  
**Приоритет:** LOW  
**Связанный план:** [PLAN-006](file:///agents/plans/plan_006_dependency_sync.md)  

---

## 🎯 Цель задачи
Устранить дрейф между `requirements.txt` и `pyproject.toml`: выровнять версии, объявить используемый, но незадекларированный `SpeechRecognition`, добавить extra `speech`.

---

## 📌 Пошаговый чек-лист выполнения:

- [ ] **Шаг 1:** `requirements.txt` — выровнять операторы версий, добавить `SpeechRecognition`.
- [ ] **Шаг 2:** `pyproject.toml` — добавить `MarkupSafe`, extra `speech`, расширить `all`.
- [ ] **Шаг 3:** `tests/test_dependency_sync.py` — сверка обоих файлов и покрытие используемых в коде библиотек.
- [ ] **Шаг 4:** Верификация — регистрация в `run_all.py`, полный прогон.

---

## 🧪 Критерии готовности (Definition of Done):
1. Множества зависимостей `requirements.txt` и `pyproject.toml` согласованы.
2. `SpeechRecognition` объявлен в обоих файлах.
3. `tests/run_all.py` — все файлы PASS (19/19).
