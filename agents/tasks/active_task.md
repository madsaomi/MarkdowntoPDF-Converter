# 📋 Активная задача: IDLE (нет активной задачи)

**Статус:** ⚪ IDLE  
**Дата обновления:** 2026-10-20  
**Исполнитель:** Big Pickle (OpenCode)  
**Последняя завершённая задача:** TASK-008 — Судьба фичевых заглушек  

---

## 🎯 Цель (следующий кандидат)

**Бэклог задач (TASK-001…008) полностью закрыт.** Осталось:

- **Веха M4 (Релиз):** CI-сборка `.exe` + инсталлятора (Inno Setup), обновление README.
- **Идеи на будущее** из [`backlog.md`](file:///agents/tasks/backlog.md):
  - офлайн-замена внешних сервисов (LaTeX/CodeCogs, диаграммы/Kroki) → локальный рендер или кэш;
  - вынести блокирующие GUI-операции (OCR, PDF→MD, GitHub sync, распознавание речи) в фоновые потоки;
  - единый рендер-путь для превью и экспорта (Jinja2-шаблоны);
  - честная маркировка декоративных фич (AI-ассистент, переводчик, Plugin Marketplace, облачные шаблоны).

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

---

## 🧪 Состояние верификации

- Тесты: **21/21** тестовых файлов зелёные (`python tests/run_all.py`).
- Integrity-check «Второго Мозга»: 0 ошибок.
- **Бэклог задач TASK-001…008 закрыт полностью.**
