# Лог сессии: 2026-10-21 — Big Pickle (красный CI: тесты под настоящим PyQt6)

## Цель
Проверить реальный GUI-smoke в CI и починить красный job `Tests`.

## Действия
- Установлен `gh`? Нет. Проверка CI через GitHub API (Invoke-RestMethod).
- Обнаружено: workflow `Tests` красный на всех версиях (3.10–3.14), причём
  падал и до этой сессии (`0fa1ea7`, 2026-07-14) → предсуществующая проблема.
- Установлен настоящий PyQt6 локально (Python 3.15) → воспроизведено:
  27/29, падают ОБА новых теста миксинов (BUG_005).
- Причины: `QMessageBox.information(fake_host, …)` → TypeError (не QWidget);
  реальные QLabel/QWidget в `update_export_history_ui` крашат без QApplication.
- Фикс: `QT_QPA_PLATFORM=offscreen` до импорта Qt, `_ensure_qapplication()`,
  no-op-патч диалогов в модулях миксинов (независимо от стаб/реал).
- Прогнан `scripts/smoke_gui.py` ВЖИВУЮ (offscreen): окно, меню (4 шт.),
  превью, экспорт HTML и DOCX — всё зелёное. Установлены python-docx/htmldocx.

## Результат
Локально с PyQt6: 29/29, smoke exit=0. Коммит ba07695. BUG_005 заведён.

## Уроки
Тесты под заглушкой ничего не гарантируют — нужен прогон под реальной
библиотекой. Offscreen + QApplication обязательны для виджетных тестов.
