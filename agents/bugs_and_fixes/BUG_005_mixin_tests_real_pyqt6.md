# 🐛 Баг: тесты миксинов падали под настоящим PyQt6 (красный CI)

**Дата:** 2026-10-21  
**Статус:** ✅ FIXED  
**Затронутые модули:** `tests/test_mixins_behavior_012.py`, `tests/test_mixins_behavior_012b.py`

---

## Симптом → Причина

- **Симптом:** CI-job `Tests` (workflow `test.yml`, Python 3.10–3.14) красный
  на шаге «Run tests». Локально (Python 3.15, **без** PyQt6 — Qt-стаб) всё
  было зелёным. Проваливались `test_mixins_behavior_012*.py`.
- **Причина:** тесты были написаны и проверены только под Qt-стабом. В CI
  `pip install PyQt6` реально ставит Qt, и `_install_qt_stub()` возвращает
  `False` — код идёт по «настоящей» ветке, где:
  1. `QMessageBox.information(self, ...)` требует настоящий `QWidget`-родитель,
     а фейковый хост им не является → `TypeError: argument 1 has unexpected
     type 'Host'`;
  2. `update_export_history_ui` создаёт реальные `QLabel`/`QWidget`, которым
     нужен `QApplication` и платформа; без них — жёсткий крэш (exit code
     `0xC0000005`/`3221226505`), без вывода;
  3. без `QT_QPA_PLATFORM=offscreen` Qt пытается открыть дисплей.

## Исправление

1. `os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")` в обоих тестах —
   до первого импорта Qt.
2. `_ensure_qapplication()` — создаёт `QApplication`, если PyQt6 настоящий
   (нужен для виджетов в `update_export_history_ui`).
3. `_patch_dialogs()` / `_patch_msgbox()` — принудительно заменяют
   `QMessageBox`/`QInputDialog`/`QFileDialog` на no-op-объекты **в модулях
   миксинов**, независимо от стаб/реал. Это устраняет и `TypeError` от
   фейкового родителя, и блокировку на модальных диалогах.

## Проверка
- Локально PyQt6 установлен → полный прогон **29/29** (раньше 27/29).
- `scripts/smoke_gui.py` впервые прогнан вживую (offscreen): окно, меню,
  превью и экспорт HTML/DOCX — всё зелёное.

## Уроки
- Тест, проходящий только под заглушкой, ничего не гарантирует: нужен прогон
  и под настоящей библиотекой (CI). Дублирующий `test.yml` не ставил `pyyaml`,
  но главная причина была именно в реальном PyQt6.
- Хардкрэш Qt без вывода трудноуловим — `QT_QPA_PLATFORM=offscreen` +
  `QApplication` обязательны для любых тестов, трогающих виджеты.
