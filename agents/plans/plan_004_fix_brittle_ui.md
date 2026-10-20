# 📐 План реализации: PLAN-004 — Починка хрупких UI-механик

> **Статус:** ✅ COMPLETED (2026-10-20, коммит `451bfc9`)  
> **Дата создания:** 2026-10-20  
> **Автор / Агент:** Big Pickle (OpenCode)  
> **Связанная задача:** [TASK-004](file:///agents/tasks/active_task.md)  
> **Целевая ветка / Ревизия:** main  

---

## 1. 🎯 Цель и контекст
Аудит (сессия 01) выявил 4 хрупкие UI-механики: сплиттер с неверным числом размеров, watermark-дизайнер, теряющий результат, непереводимое меню Language и `closeEvent`, не останавливающий фоновые потоки. Все четыре верифицированы по актуальному коду.

## 2. 🔍 Факты из кода (верифицировано)

| # | Проблема | Факт |
|---|----------|------|
| 1 | `toggle_split_view` | `ui_layout.py:269-334` — `editor_splitter` содержит **2 виджета** (`editor_container`, `preview_output`), а `window_tools.py:249,253,257` передаёт **3 размера**. Qt молча игнорирует `setSizes`, режимы не работают. |
| 2 | Watermark-дизайнер | `window_tools.py:92-98` получает `dlg.result_css` (полный HTML-`<div class="watermark" style="...">`) и **выбрасывает его**, записывая только текст в `footer_input`. Стили (цвет/размер/угол/прозрачность), а также чекбоксы `chk_diagonal`/`chk_tiled` нигде не используются. |
| 3 | Меню Language | `ui_layout.py:70` создаёт локальную `lang_menu`, `main_window.py:742-743` ищет `self.lang_menu` → меню навсегда остаётся `"Language"`. Плюс `retranslate_ui` переводит только `actions()[0]` (File). |
| 4 | `closeEvent` | `main_window.py:260-262` — только `save_settings()`. Не останавливаются/не дожидаются `ConversionThread` (`self.thread`, строка 78/476), `KrokiCheckThread` (94), таймеры `autosave_timer` (157), `preview_timer` (179); watcher не очищается. Qt уничтожит QThread при работающем цикле → предупреждение/крэш. |

## 3. 📝 Пошаговый план реализации (Atomic Steps)

- [x] **Этап 1: Сплиттер (window_tools.py)**
  - [x] 1.1: `setSizes` → 2 значения; режимы `both` / `editor` / `preview` через `setVisible`.
- [x] **Этап 2: Watermark-дизайнер**
  - [x] 2.1: `build_watermark_css()` генерирует **CSS** (без пользовательского HTML), `result_css` = CSS.
  - [x] 2.2: `chk_diagonal`/`chk_tiled` реально влияют на генерацию.
  - [x] 2.3: добавлен скрытый носитель `watermark_css_input`.
  - [x] 2.4: `show_watermark_designer` пишет CSS в носитель (результат больше не теряется).
  - [x] 2.5: `ConversionOptions.watermark_css` → `ConversionThread` → `PDFRenderer.render/render_html` → `base.html`.
- [x] **Этап 3: Меню Language**
  - [x] 3.1: `window.lang_menu`/`tools_menu`/`help_menu`/`file_menu` экспонированы.
  - [x] 3.2: `retranslate_ui` переводит все четыре меню (+ новый ключ `menu_help`).
- [x] **Этап 4: `closeEvent`**
  - [x] 4.1: остановка таймеров, черновик, watcher, отмена+ожидание `self.thread` и `kroki_thread`.
- [x] **Этап 5: Тесты и верификация**
  - [x] 5.1: `tests/test_watermark_css.py` (5 проверок, включая санитизацию HTML из текста).
  - [x] 5.2: `tests/test_renderer_watermark_css.py` (проброс + приоритет CSS).
  - [x] 5.3: `py_compile` OK; `tests/run_all.py` — **11/11 зелёные**; HTML-смоук CLI: `.watermark` и кастомный CSS в документе.

> **Попутно:** инициализация `AppConfig.base_path()` уже исправлена в TASK-002; здесь дополнительно исправлена генерация HTML-preview дизайнера (раньше CSS-текст вставлялся в `<body>` как видимый текст).

## 4. 🛡️ Риски и откат
- **Риски:** PyQt6 не установлен → GUI правится под `py_compile` + grep; логика вынесена в тестируемые чистые функции. `watermark_css` — новый параметр с дефолтом `''`, обратная совместимость сохраняется.
- **Откат:** `git revert` — правки изолированы.

## 5. 🧪 Критерии приемки
- [ ] `toggle_split_view` переключает 3 режима при 2 виджетах.
- [ ] Дизайнер: выбор цвета/размера/угла реально попадает в PDF (через `watermark_css`).
- [ ] Меню Language переводится при смене языка; пункты Tools/Help локализуются.
- [ ] `closeEvent` корректно останавливает потоки/таймеры (нет предупреждений Qt).
- [ ] Все тесты зелёные.
