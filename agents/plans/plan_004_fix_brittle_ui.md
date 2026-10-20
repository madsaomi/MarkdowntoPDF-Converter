# 📐 План реализации: PLAN-004 — Починка хрупких UI-механик

> **Статус:** 🟢 APPROVED  
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

- [ ] **Этап 1: Сплиттер (window_tools.py)**
  - [ ] 1.1: `setSizes` → 2 значения; режимы `both` / `editor` / `preview` через `setVisible`, плюс корректные размеры.
- [ ] **Этап 2: Watermark-дизайнер (watermark_designer.py + ui_layout.py + renderer.py + base.html)**
  - [ ] 2.1: `watermark_designer` генерирует **CSS-фрагмент** `result_css` (без пользовательского HTML), новые сигналы-свойства `preview_html()` для превью.
  - [ ] 2.2: `chk_diagonal`/`chk_tiled` реально влияют на генерацию (угол/повтор).
  - [ ] 2.3: в UI-настройках добавляется `watermark_css` (QLineEdit, скрытое поле-носитель).
  - [ ] 2.4: `window_tools.show_watermark_designer` пишет `result_css` в `watermark_css_input` (а не теряет его).
  - [ ] 2.5: `ConversionOptions.watermark_css` + прокидывание в `_get_options` → `ConversionThread` → `PDFRenderer.render/render_html` → `base.html` (`{{ watermark_css }}` в `<style>` последним).
- [ ] **Этап 3: Меню Language (ui_layout.py + main_window.py)**
  - [ ] 3.1: `window.lang_menu = lang_menu` (+ `window.help_menu`), ярлык перевода `menu_language` убрать из ui_layout.
  - [ ] 3.2: `retranslate_ui` переводит и локализует пункты меню: File, Tools, Language, Help (с `menu_file`…, фолбэк — английские названия).
- [ ] **Этап 4: `closeEvent` (main_window.py)**
  - [ ] 4.1: остановить таймеры (`autosave_timer`, `preview_timer`), очистить watcher, отменить+дождаться `self.thread` и `kroki_thread`, сохранить настройки и черновик.
- [ ] **Этап 5: Тесты и верификация**
  - [ ] 5.1: `tests/test_watermark_css.py` — генерация CSS в дизайнере (без Qt: чистые функции/формат).
  - [ ] 5.2: `tests/test_renderer_watermark_css.py` — `PDFRenderer.render_html` вставляет `watermark_css` в `<style>` последним.
  - [ ] 5.3: `py_compile` + `python tests/run_all.py` (все файлы).

## 4. 🛡️ Риски и откат
- **Риски:** PyQt6 не установлен → GUI правится под `py_compile` + grep; логика вынесена в тестируемые чистые функции. `watermark_css` — новый параметр с дефолтом `''`, обратная совместимость сохраняется.
- **Откат:** `git revert` — правки изолированы.

## 5. 🧪 Критерии приемки
- [ ] `toggle_split_view` переключает 3 режима при 2 виджетах.
- [ ] Дизайнер: выбор цвета/размера/угла реально попадает в PDF (через `watermark_css`).
- [ ] Меню Language переводится при смене языка; пункты Tools/Help локализуются.
- [ ] `closeEvent` корректно останавливает потоки/таймеры (нет предупреждений Qt).
- [ ] Все тесты зелёные.
