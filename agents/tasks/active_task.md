# 📋 Активная задача: IDLE (нет активной задачи)

**Статус:** ⚪ IDLE  
**Дата обновления:** 2026-10-21  
**Исполнитель:** Big Pickle (OpenCode)  
**Последняя завершённая задача:** PLAN-013 — покрытие кода `src/` поднято с 42 % до 81 % (порог CI 76 %)  

---

## 🎯 Цель (следующий кандидат)

**Основной бэклог (TASK-001…013) и веха M4 закрыты.** Дальше — продолжение декомпозиции и «Идеи на будущее» из [`backlog.md`](file:///agents/tasks/backlog.md):

- **разделить `ToolMethodsMixin`** (68 методов, 730 строк) по темам — тем же приёмом (вербатим-перенос + регресс-тест);
- починить [BUG_003](file:///agents/bugs_and_fixes/BUG_003_readability_missing_import.md) (`estimate_readability` без импорта);
- офлайн-замена внешних сервисов (LaTeX/CodeCogs, диаграммы/Kroki);
- фоновые потоки для OCR, PDF→MD, GitHub sync, распознавания речи;
- единый рендер-путь превью и экспорта; честная маркировка декоративных фич.

> При взятии задачи: перенести её формулировку сюда, создать/обновить план в [`agents/plans/`](file:///agents/plans/) (Plan-First).

---

## ✅ Журнал закрытых задач

- ✅ **TASK-001 (критические баги)** — коммит `79ae4e5`. Отчёт: [`session_2026-10-20_01_big_pickle.md`](file:///agents/history/session_2026-10-20_01_big_pickle.md).
- ✅ **TASK-002 (рендер PDF-движка)** — коммит `ffcbbe6`. Отчёт: [`session_2026-10-20_02_big_pickle.md`](file:///agents/history/session_2026-10-20_02_big_pickle.md).
- ✅ **TASK-003 (чистка мёртвого кода GUI)** — коммит `1db3a81`. Отчёт: [`session_2026-10-20_03_big_pickle.md`](file:///agents/history/session_2026-10-20_03_big_pickle.md).
- ✅ **TASK-004 (4 хрупкие UI-механики)** — коммит `451bfc9`. Отчёт: [`session_2026-10-20_04_big_pickle.md`](file:///agents/history/session_2026-10-20_04_big_pickle.md).
- ✅ **TASK-005 (тестовое покрытие ядра)** — коммит `bb9426e`. Отчёт: [`session_2026-10-20_05_big_pickle.md`](file:///agents/history/session_2026-10-20_05_big_pickle.md). Попутно исправлен [BUG_002](file:///agents/bugs_and_fixes/BUG_002_reveal_js_slide_split.md).
- ✅ **TASK-006 (синхронизация зависимостей)** — коммит `688f55f`. Отчёт: [`session_2026-10-20_06_big_pickle.md`](file:///agents/history/session_2026-10-20_06_big_pickle.md).
- ✅ **TASK-007 (мелкие баги ядра)** — коммит `aae3974`. Отчёт: [`session_2026-10-20_07_big_pickle.md`](file:///agents/history/session_2026-10-20_07_big_pickle.md).
- ✅ **TASK-008 (судьба фичевых заглушек)** — коммит `c26c383`. Отчёт: [`session_2026-10-20_08_big_pickle.md`](file:///agents/history/session_2026-10-20_08_big_pickle.md).
- ✅ **TASK-009 (M4 «Релиз»)** — коммит `2b3566d`. Отчёт: [`session_2026-10-20_09_big_pickle.md`](file:///agents/history/session_2026-10-20_09_big_pickle.md).
- ✅ **TASK-010 (декомпозиция God-object MainWindow)** — коммит `d95c394`. Отчёт: [`session_2026-10-20_10_big_pickle.md`](file:///agents/history/session_2026-10-20_10_big_pickle.md).
- ✅ **TASK-011 (разбиение `dialogs.py` на пакет)** — коммиты `7b00c6c` + `8e929c6`. Отчёт: [`session_2026-10-20_11_big_pickle.md`](file:///agents/history/session_2026-10-20_11_big_pickle.md).
- ✅ **TASK-012 (декомпозиция миксинов)** — отчёты: [`session_2026-10-21_40…42_big_pickle.md`](file:///agents/history/session_2026-10-21_42_big_pickle.md).
- ✅ **PLAN-013 (покрытие кода)** — 42 % → **81 %**, порог CI **76 %**, 61 тест-файл, 8 найденных багов. Отчёты: [`session_2026-10-21_43_big_pickle.md`](file:///agents/history/session_2026-10-21_43_big_pickle.md), [`session_2026-10-21_44_big_pickle.md`](file:///agents/history/session_2026-10-21_44_big_pickle.md).

---

## 🧪 Состояние верификации

- Тесты: **61/61** тестовых файлов зелёные (`python tests/run_all.py`); `pytest` — 729 passed.
- Покрытие `src/`: **81 %** (порог CI 76 %).
- Integrity-check «Второго Мозга»: 0 ошибок.
- **Бэклог TASK-001…013 и веха M4 закрыты.**
