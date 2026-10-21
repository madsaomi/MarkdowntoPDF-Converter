# 🐛 Баг: миксины TASK-010/012 используют глобальные имена без импорта

**Дата:** 2026-10-21  
**Статус:** ✅ FIXED (коммит — см. сессию 2026-10-21)  
**Затронутые модули:**
- `src/gui/mixins/presets.py`
- `src/gui/mixins/document_ops.py`
- `src/gui/mixins/editor_tools.py`

---

## Симптом → Причина

- **Симптом:** вызовы `PresetsMixin.save_preset/delete_preset`,
  `DocumentOpsMixin.show_doc_templates_dialog/save_revision/...` и ветка
  достижения цели в `EditorToolsMixin.update_text_statistics` (а также
  `search_next` при regex) должны падать с `NameError`/`AttributeError`.
- **Причина:** при вербатим-переносе методов из `main_window.py` в миксины
  (TASK-010/012) тела методов не менялись, но **модульные глобали не были
  перенесены**. Методы ссылаются на:
  - `json`, `QInputDialog`, `QMessageBox` (`presets.py`);
  - `QInputDialog`, `document_tools`, `file_manager` (`document_ops.py`);
  - `QMessageBox`, `QRegularExpression` (`editor_tools.py`).

  В старом `main_window.py` эти имена были доступны как глобали модуля
  (`import json`, импорты Qt, `from src.gui import ... document_tools, file_manager`).
  После переноса в отдельные файлы они исчезли, а `main_window.py` импортирует
  миксины, а не наоборот.
- **Как обнаружено:** при написании поведенческих тестов миксинов
  (`tests/test_mixins_behavior_012b.py`) — вызов `delete_preset()` дал
  `NameError: name 'json' is not defined`. Дополнительно написан сканер
  (AST: «имена, использованные как базис атрибута, но не импортированные и не
  локальные»), который нашёл **все три** модуля.

## Исправление

Добавлены импорты на уровне модуля (в соответствии со стилем соседних миксинов):

```python
# presets.py
import json
from PyQt6.QtWidgets import QInputDialog, QMessageBox

# document_ops.py
from PyQt6.QtWidgets import QInputDialog
from src.gui import document_tools, file_manager

# editor_tools.py
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtWidgets import QMessageBox
```

Проверено: сканер «висячих» глобалов по `src/gui/mixins/` — чисто; новые
поведенческие тесты зелёные; батарея 28/28.

## Уроки
- Декомпозиция «вербатим» переносит тела, но **не** неявные зависимости от
  модульных глобалов исходного файла — это скрытый источник поломок, невидимый
  `py_compile` (синтаксис корректен) и Qt-стабу (путь не вызывается).
- Скан «использованные, но не импортированные глобали» (AST) — дешёвая и
  полезная регрессионная проверка; стоит включить в батарею как отдельный тест.
