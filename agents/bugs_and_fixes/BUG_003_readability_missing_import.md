# 🐛 Баг: `ReadabilityDashboardDialog` использует `estimate_readability` без импорта

**Дата:** 2026-10-20  
**Статус:** ✅ FIXED (фиксирован в коммите 8786124) (обнаружен попутно при [TASK-011](file:///agents/plans/plan_011_split_dialogs.md)/[PLAN-011](file:///agents/plans/plan_011_split_dialogs.md))  
**Затронутые модули:** `src/gui/dialogs/analysis.py` (ранее — `src/gui/dialogs.py`)

---

## Симптом → Причина

- **Симптом:** при вызове диалога «Панель читаемости» (`ReadabilityDashboardDialog`) должен
  падать `NameError: name 'estimate_readability' is not defined`.
- **Причина:** в классе вызывается `score, level = estimate_readability(text, lang)`,
  но **ни в исходном `dialogs.py`, ни где-либо ещё в этом файле нет импорта**
  `estimate_readability`. Функция определена в `src/gui/document_tools.py:623`,
  однако импорта `from src.gui.document_tools import estimate_readability` нет.
- **Как обнаружено:** при вербатим-переносе классов в [PLAN-011](file:///agents/plans/plan_011_split_dialogs.md)
  делалась AST-сверка с `git HEAD`; сверка «использованных, но не импортированных имён» показала
  «висячее» имя `estimate_readability`.
- **Важно:** дефект **предсуществующий**, не внесён декомпозицией. Перенос выполнен строго
  вербатим (тела не менялись), поэтому баг сохранён «как есть» — исправление выходит за рамки
  задачи декомпозиции (принцип «поведение не меняем»).

## Предлагаемое решение
Добавить в `analysis.py` (или локально внутри метода) импорт:
```python
from src.gui.document_tools import estimate_readability
```
и проверить отсутствие циклического импорта (`document_tools` ↔ `dialogs`):
безопаснее — **локальный импорт внутри метода** (как уже делается для `github_sync`,
`plugin_system`, `citation_manager`, `cloud_templates`).

## Уроки
- Разбор монолита на модули выявляет «спящие» дефекты, которые не видны в обычном прогоне,
  потому что код-путь не вызывается тестами (GUI-диалог без теста + Qt-стаб).
- Полезная эвристика: сверка «имена, использованные в классе, но не импортированные и не
  локальные» — стоит оформить как отдельную проверку (кандидат в идеи на будущее).
