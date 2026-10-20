# 📐 План реализации: PLAN-008 — Судьба фичевых заглушек

> **Статус:** ✅ COMPLETED (2026-10-20, коммит `c26c383`)  
> **Дата создания:** 2026-10-20  
> **Автор / Агент:** Big Pickle (OpenCode)  
> **Связанная задача:** TASK-008  
> **Целевая ветка / Ревизия:** main  

---

## 1. 🎯 Цель и контекст
- **Проблема / Задача:** В `main_window.py` есть 6 методов с рабочими локальными реализациями (`start_voice_input`, `ai_improve_text`, `ai_generate_outline`, `show_ai_assistant`, `export_task_board`, `generate_api_docs`), но **ни один не вызывается** (не подключены к меню). Плюс мёртвый декор: импорты `CustomTitleBar`/`AmbientGlowWidget` (никогда не инстанцируются, `_setup_*` не существуют) и файл `splash_screen.py` (`ModernSplashScreen` не создаётся нигде).
- **Ожидаемый результат:** Рабочие инструменты доступны из меню Tools (честные локальные фичи, без ML/сети — но функциональные); мёртвый декоративный код удалён; нет «мёртвых» импортов.

---

## 2. 🔍 Анализ и затронутые компоненты (верифицировано)

### Факты из кода (grep/read):

**A. Рабочие, но недостижимые методы (все — локальные, самодостаточные):**
| Метод | Строки | Что делает | Зависимость |
|---|---|---|---|
| `start_voice_input` | 1142 | Распознавание речи (Google API) | `speech_recognition` (opus: сеть) |
| `ai_improve_text` | 1160 | `ai_assistant.analyze()` → подсказки/нормализация | локально |
| `ai_generate_outline` | 1180 | `ai_assistant.generate_outline()` → оглавление | локально |
| `show_ai_assistant` | 1190 | Анализ текста с эмодзи-категориями | локально |
| `export_task_board` | 1209 | Kanban-доска из `- [ ]`/`- [x]` в диалоге | локально |
| `generate_api_docs` | 1236 | AST-док из выбранного .py в редактор | локально |

Проверено: **0 call sites** во всём репозитории (grep).

**B. Мёртвый декор:**
- `main_window.py:53-54` — `from src.gui.custom_titlebar import CustomTitleBar`, `from src.gui.ambient_glow import AmbientGlowWidget`; сами классы нигде не инстанцируются; вызовы `self._setup_custom_titlebar()` / `self._setup_ambient_glow()` закомментированы (стр. 112, 127) и **определений не имеют**.
- `src/gui/splash_screen.py` — `ModernSplashScreen` не инстанцируется ни в `main.py`, ни в `main_window.py`.

### Затронутые файлы:
- `[MODIFY]` `src/gui/ui_layout.py` — секция Tools: добавить пункты «AI Assistant», «Task Board», «API Docs», «Voice Input» (+ AI Improve/Outline в подменю).
- `[MODIFY]` `src/gui/main_window.py` — удалить мёртвые импорты (53-54) и закомментированные вызовы (112, 127).
- `[DELETE]` `src/gui/splash_screen.py` — неиспользуемый `ModernSplashScreen`.
- `[DELETE]` `src/gui/custom_titlebar.py`, `[DELETE]` `src/gui/ambient_glow.py` — неиспользуемые виджеты (импорты удаляются).
- `[NEW]` `tests/test_stub_wiring_008.py` — проверка: методы вызываемы из меню, мёртвые модули удалены.

### Зависимости и влияние:
- Новые библиотеки: нет.
- Breaking changes: **НЕТ** — методы уже существуют; удаляются только недостижимые модули.
- Риск: `start_voice_input` требует `speech_recognition`+микрофон — при отсутствии показывает `QMessageBox` (не падает). Маркируем пункт как «(требует микрофон)».

---

## 3. 📝 Пошаговый план реализации (Atomic Steps)

- [x] **Этап 1: Подключить AI-инструменты** — в `ui_layout.py` секция Tools: «AI Writing Assistant» → `show_ai_assistant`, «AI Improve Selection» → `ai_improve_text`, «Generate Outline» → `ai_generate_outline`.
- [x] **Этап 2: Подключить Task Board / API Docs / Voice** — «Task Board (Kanban)» → `export_task_board`, «API Docs from .py» → `generate_api_docs`, «Voice Input (mic)» → `start_voice_input`.
- [x] **Этап 3: Удалить мёртвый декор** — убраны импорты `CustomTitleBar`/`AmbientGlowWidget` и закомментированные вызовы; `git rm` для `splash_screen.py`, `custom_titlebar.py`, `ambient_glow.py`.
- [x] **Этап 4: Тесты** — `tests/test_stub_wiring_008.py` (5 проверок); проверено, что тест ловит рассинхрон меню.
- [x] **Этап 5: Верификация** — регистрация в `run_all.py`, `py_compile`, полный прогон **21/21**.

---

## 4. 🛡️ Риски, сайд-эффекты и план отката
- **Риски:** удаление модулей, на которые кто-то ссылается. Митигация: grep подтверждает отсутствие потребителей (кроме удаляемых импортов) и пользователь ранее постановил удалить мёртвый декор.
- **План отката:** `git revert` — правки изолированы в `ui_layout.py`, `main_window.py` и 3 удалённых файлах + тест.

---

## 5. 🧪 План тестирования и критерии приемки
1. Автоматические тесты: `python tests/test_stub_wiring_008.py` + `python tests/run_all.py`.
2. Ручная проверка: пункты меню Tools вызывают соответствующие методы (под Qt-стабом — проверка wiring).
3. Definition of Done:
   - [x] 6 методов имеют call site в `ui_layout.py`.
   - [x] Нет импортов `CustomTitleBar`/`AmbientGlowWidget`; файлы `splash_screen.py`/`custom_titlebar.py`/`ambient_glow.py` удалены.
   - [x] Тест зелёный, батарея **21/21**.
