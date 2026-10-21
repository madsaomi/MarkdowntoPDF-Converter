# Лог сессии: 2026-10-21 — Big Pickle (тесты миксинов ч.2 + BUG_004)

## Цель
Покрыть поведенческими тестами остальные миксины TASK-012 и проверить,
что декомпозиция не оставила скрытых поломок.

## Действия
- Создан tests/test_mixins_behavior_012b.py (11 проверок):
  export_history (дедуп/лимит 5/placeholder), presets (load/save/delete),
  convert_tools (HTML->MD fallback, отмена PDF, алиас OCR),
  integrations (watermark designer, github sync без файлов).
- Написан AST-сканер «использованные, но не импортированные глобали»
  → найдены 3 модуля с висячими именами.

## Находка (BUG_004)
Вербатим-перенос методов из main_window.py в миксины не перенёс модульные
глобали. Падало бы на реальных путях:
- presets.py: json, QInputDialog, QMessageBox
- document_ops.py: QInputDialog, document_tools, file_manager
- editor_tools.py: QMessageBox, QRegularExpression

## Исправление
Добавлены импорты на уровне модуля. Сканер чист, тесты зелёные.
Заведён agents/bugs_and_fixes/BUG_004_mixins_missing_globals.md.

## Результат
Батарея 28/28. Коммит кода bd59ac5 (fix + tests).

## Уроки
`py_compile` и Qt-стаб не ловят висячие глобали — нужен явный AST-тест
(кандидат: оформить сканер как постоянную проверку батареи).
