# 📋 Активная задача: нет активной задачи

**Статус:** 🟢 IDLE (Ожидание)  
**Дата создания:** 2026-10-20  
**Дата завершения последней задачи:** 2026-10-20  
**Исполнитель:** —  
**Приоритет:** —  

---

## 🎯 Текущее состояние

- ✅ **TASK-001 (критические баги)** — коммит `79ae4e5`. Отчёт: [`session_2026-10-20_01_big_pickle.md`](file:///agents/history/session_2026-10-20_01_big_pickle.md).
- ✅ **TASK-002 (PDF-движок)** — коммит `ffcbbe6`. Отчёт: [`session_2026-10-20_02_big_pickle.md`](file:///agents/history/session_2026-10-20_02_big_pickle.md).
- ✅ **TASK-003 (чистка мёртвого кода)** — коммит `1db3a81`. Отчёт: [`session_2026-10-20_03_big_pickle.md`](file:///agents/history/session_2026-10-20_03_big_pickle.md).
- ✅ **TASK-004 (хрупкие UI-механики)** — коммит `451bfc9`. Отчёт: [`session_2026-10-20_04_big_pickle.md`](file:///agents/history/session_2026-10-20_04_big_pickle.md).
- Тесты: **11/11** тестовых файлов зелёные.
- ⚠️ Локальный PDF-рендер недоступен: pip-пакет `weasyprint` не устанавливается под Python 3.15 (нет колёс `brotli`); портативного `weasyprint.exe` нет. Нужен Python ≤3.14 или exe.

---

## 📌 Следующие действия

1. Выбрать задачу из [`backlog.md`](file:///agents/tasks/backlog.md) — кандидаты:
   - **TASK-005 (MEDIUM):** расширение тестового покрытия рендереров + PyQt6 в CI.
   - **TASK-006 (LOW):** дрейф версий `requirements.txt` ↔ `pyproject.toml`.
   - **TASK-007 (LOW):** мелкие баги ядра (дублирующийся лог «saved», шэдоуинг `QThread.finished`, busy-wait в TTS, `<html lang="en">`).
   - **TASK-008 (LOW):** судьба фичевых заглушек.
2. Создать план: `python brain.py plan "Название"`.
3. Перенести выбранный backlog-элемент в этот файл с чек-листом (Plan-First).
