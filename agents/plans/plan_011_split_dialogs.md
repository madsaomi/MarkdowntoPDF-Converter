# 📐 План реализации: PLAN-011 — Разбиение `dialogs.py` на пакет

> **Статус:** 🟢 APPROVED  
> **Дата создания:** 2026-10-20  
> **Автор / Агент:** Big Pickle (OpenCode)  
> **Связанная задача:** TASK-011  
> **Целевая ветка / Ревизия:** main  

---

## 1. 🎯 Цель и контекст
- **Проблема / Задача:** `src/gui/dialogs.py` — **1534 строки**, 17 классов разной тематики в одном файле (GitHub sync, плагины, экспорт, цитаты, конструктор документов, читаемость, аудит, TOC, сниппеты, таблицы, PDF-стили, ревизии, diff, облачные шаблоны, шорткаты). Это второй по величине файл проекта после декомпозиции `MainWindow` и один из главных источников «распухания» (4 файла держали 33% кода).
- **Ожидаемый результат:** `dialogs.py` превращается в пакет `src/gui/dialogs/` с модулями по темам. **Публичный интерфейс не меняется** — `from src.gui.dialogs import <Dialog>` продолжает работать для всех 13 существующих мест импорта.

---

## 2. 🔍 Анализ и затронутые компоненты (верифицировано)

### Состав `dialogs.py` (AST-замер): 1534 строки, 17 классов
| Класс | Строк | Методов |
|---|---|---|
| `GitHubSyncDialog` | 129 | 7 |
| `PluginManagerDialog` | 62 | 3 |
| `MultiExportDialog` | 41 | 2 |
| `CitationManagerDialog` | 123 | 5 |
| `DocumentBuilderDialog` | 261 | 8 |
| `ReadabilityDashboardDialog` | 59 | 1 |
| `DocumentAuditorDialog` | 92 | 3 |
| `MarkdownTOCDialog` | 39 | 1 |
| `SnippetsDialog` | 41 | 2 |
| `MarkdownTableDialog` | 30 | 1 |
| `ColorButton` | 15 | 3 |
| `PDFStyleEditorDialog` | 110 | 4 |
| `RevisionHistoryDialog` | 95 | 3 |
| `DiffDialog` | 111 | 3 |
| `SnippetsManagerDialog` | 96 | 7 |
| `CloudTemplatesDialog` | 77 | 6 |
| `ShortcutsDialog` | 73 | 1 |

### Потребители (13 мест, верифицировано grep):
- `build.py:101` — `--hidden-import=src.gui.dialogs` (останется валидным).
- `src/gui/document_tools.py:15` — пакетный импорт (5 классов).
- `src/gui/main_window.py:41` — пакетный импорт (9 классов).
- `src/gui/window_tools.py` — ленивые точечные импорты (`ShortcutsDialog`, `DiffDialog`, `MultiExportDialog`, `CitationManagerDialog`, `GitHubSyncDialog`, `PluginManagerDialog`).
- Тесты — прямых импортов `dialogs` **нет** (проверено).

> **Стратегия совместимости:** `src/gui/dialogs/__init__.py` реэкспортирует все 17 имён, поэтому **ни одна из 13 точек импорта не меняется**.

### Затронутые файлы:
- `[DELETE]` `src/gui/dialogs.py` — заменяется пакетом с тем же именем.
- `[NEW]` `src/gui/dialogs/__init__.py` — реэкспорт всех классов (фасад совместимости).
- `[NEW]` `src/gui/dialogs/github_plugin.py` — `GitHubSyncDialog`, `PluginManagerDialog`.
- `[NEW]` `src/gui/dialogs/export.py` — `MultiExportDialog`, `PDFStyleEditorDialog`.
- `[NEW]` `src/gui/dialogs/content.py` — `DocumentBuilderDialog`, `MarkdownTOCDialog`, `MarkdownTableDialog`, `SnippetsDialog`, `SnippetsManagerDialog`.
- `[NEW]` `src/gui/dialogs/analysis.py` — `ReadabilityDashboardDialog`, `DocumentAuditorDialog`, `CitationManagerDialog`, `CloudTemplatesDialog`.
- `[NEW]` `src/gui/dialogs/versions.py` — `RevisionHistoryDialog`, `DiffDialog`.
- `[NEW]` `src/gui/dialogs/common.py` — `ColorButton`, `ShortcutsDialog`.
- `[NEW]` `tests/test_dialogs_package_011.py` — регресс-тест.

### Зависимости и влияние:
- Новые библиотеки: **нет**.
- Breaking changes: **НЕТ** (фасад `__init__.py` сохраняет все имена).
- Риски: PyInstaller `--hidden-import=src.gui.dialogs` должен работать с пакетом — да, имена модулей разрешаются так же. Риск: `QColor` импортируется в файле **дважды** (строки 13 и 18) — при разбиении следим, чтобы импорты в каждом модуле были самодостаточны.

---

## 3. 📝 Пошаговый план реализации (Atomic Steps)

- [ ] **Этап 1: Каркас пакета.** Создать `src/gui/dialogs/__init__.py` (пока пустой реэкспорт) и `git rm src/gui/dialogs.py` **только после** переноса всех классов.
- [ ] **Этап 2: Тематические модули (вербатим).** Перенести классы по AST-диапазонам строк (тем же приёмом, что PLAN-010) в 6 модулей; в каждый модуль — самодостаточные импорты по факту использования.
- [ ] **Этап 3: Фасад.** В `__init__.py` реэкспортировать все 17 имён с `__all__`; проверить, что все 13 точек импорта работают без правок.
- [ ] **Этап 4: Тесты.** `tests/test_dialogs_package_011.py`: все 17 имён импортируемы из `src.gui.dialogs`; каждый класс определён ровно один раз; модули компилируются; размеры файлов в пределах; нет модуля-«монстра» > 400 строк.
- [ ] **Этап 5: Верификация.** `py_compile`, AST-сверка переносов с `git HEAD`, регресс на отсутствие дублей, `run_all.py`, `brain.py check`.

---

## 4. 🛡️ Риски, сайд-эффекты и план отката
- **Риск: «тихая» потеря/дубль класса.** Митигация: AST-сверка каждого перенесённого класса с `git HEAD` (как в PLAN-010) + тест на 17 имён + тест на отсутствие дублей.
- **Риск: неполные импорты в новом модуле** (класс ссылается на символ, оставшийся в шапке старого файла). Митигация: после переноса — `py_compile` каждого модуля; при `NameError` в рантайме под Qt-стабом ловится структурным тестом на использованные имена.
- **Риск: сломать PyInstaller-сборку.** Митигация: `build.py` уже использует `--hidden-import=src.gui.dialogs`; пакет с именем `dialogs` разрешается аналогично; при необходимости добавить `--hidden-import=src.gui.dialogs.<module>`.
- **План отката:** `git revert` — перенос изолирован одним коммитом; `dialogs.py` восстанавливается из истории.

---

## 5. 🧪 План тестирования и критерии приемки
1. **Автоматические тесты** `tests/test_dialogs_package_011.py`:
   1. `test_all_dialogs_importable` — все 17 имён импортируются из `src.gui.dialogs` (через Qt-стаб).
   2. `test_no_dialog_defined_twice` — каждое имя определено ровно в одном модуле пакета.
   3. `test_modules_compile` — все модули пакета компилируются.
   4. `test_no_monster_module` — ни один модуль пакета не превышает 400 строк.
   5. `test_consumers_still_resolve` — исходники `main_window.py`/`document_tools.py`/`window_tools.py` по-прежнему импортируют те же имена из `src.gui.dialogs`.
   - Полный прогон: `python tests/run_all.py`.
2. **Ручная проверка:** под Qt-стабом — импорт пакета и разрешение имён; `py_compile`.
3. **Definition of Done:**
   - [ ] `src/gui/dialogs.py` заменён пакетом; ни одна из 13 точек импорта не изменена.
   - [ ] Все 17 классов перенесены вербатим (AST-сверка с `git HEAD`).
   - [ ] Ни один модуль пакета > 400 строк; самый большой класс (`DocumentBuilderDialog`, 261) — в `content.py`.
   - [ ] Тест зелёный, батарея **24/24**.
