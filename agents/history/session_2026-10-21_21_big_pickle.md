# Лог сессии: 2026-10-21 — Big Pickle (поведенческие тесты миксинов TASK-012)

## Цель
Покрыть GUI-миксины TASK-012 не только структурно (AST), но и поведенчески.

## Действия
- Создан tests/test_mixins_behavior_012.py (8 проверок) с фейковым хостом.
- Доработан Qt-стаб: `QMessageBox.information/warning/critical/question/about`
  и статические методы `QFileDialog`/`QInputDialog`/… сделаны no-op —
  иначе реальные вызовы падали с AttributeError (базовый класс не отдаёт
  атрибуты через `__getattr__`).
- Исправлены ожидания в тестах по факту чтения кода:
  - `{{title}}` берётся из первого H1 (`template_vars.substitute_template_vars`),
    а не из атрибута хоста;
  - `_save_anki_tsv` принимает список dict-карточек, а не строку;
  - `run_linter` делегирует в `show_document_audit` → подменяется на no-op.
- Регистрация в run_all.py (27 файлов), README 26→27.

## Результат
Поведение 5 миксинов (export_tools, view_dialogs, editor_formatting,
workspace, education) проверяется реальными вызовами. Батарея 27/27.
Коммит кода 07bca8d.

## Замечание
Локально нет PyQt6 (Python 3.15) — используется Qt-стаб; реальный GUI
проверяется в CI через scripts/smoke_gui.py (offscreen).
