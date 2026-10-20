# 📐 План реализации: PLAN-007 — Фиксация мелких багов ядра

> **Статус:** ✅ COMPLETED (2026-10-20, коммит `TBD`)  
> **Дата создания:** 2026-10-20  
> **Автор / Агент:** Big Pickle (OpenCode)  
> **Связанная задача:** TASK-007  
> **Целевая ветка / Ревизия:** main  

---

## 1. 🎯 Цель и контекст
- **Проблема / Задача:** Четыре мелких, но реальных дефекта, выявленных при полном аудите: дублирующийся лог «Сохранено», шэдоуинг встроенного сигнала `QThread.finished`, пустой busy-wait цикл в TTS и захардкоженный `<html lang="en">` в шаблоне.
- **Ожидаемый результат:** Лог без дублей, отсутствие конфликта с `QThread.finished`, TTS не жжёт CPU в ожидании, атрибут `lang` в HTML отражает выбранный язык (RU/EN).

---

## 2. 🔍 Анализ и затронутые компоненты (верифицировано)

### Факты из кода (grep/read):

**1. Дублирующийся лог «saved» — `src/gui/threads.py`**
- Ветки PPTX (стр. 100), REVEAL (стр. 104), PNG/JPG (стр. 116) **сами** эмитят `log_saved`, а затем строка **151** эмитит `log_saved` повторно для **всех** форматов.
- Итог: для PPTX/REVEAL/PNG/JPG пользователь видит **две** строки «Сохранено» на один файл (вторая — без суффикса «(N slides/pages)»).
- DOCX/EPUB/HTML/PDF — один раз (только стр. 151), корректно.

**2. Шэдоуинг `QThread.finished` — `src/gui/threads.py:18`**
- `class KrokiCheckThread(QThread): finished = pyqtSignal(bool)` переопределяет встроенный сигнал `QThread.finished` (без аргументов).
- Работает за счёт PyQt, но это ломает семантику (кто-то ожидает `finished` без аргументов) и хрупко.
- Потребитель: `main_window.py:95` `self.kroki_thread.finished.connect(self.on_kroki_check_finished)`.

**3. Busy-wait в TTS — `src/core/tts_engine.py:181-183`**
```python
while self._is_paused:
    if not self._is_playing:
        break
```
- Тело цикла пустое → активное вращение CPU на 100% всё время паузы.

**4. `<html lang="en">` — `templates/base.html:2`**
- Захардкожен `lang="en"`, хотя `renderer.py:74-75` уже резолвит `lang` (RU/EN) для `tr_page`/`tr_of`. В шаблон `lang` не передаётся.

### Затронутые файлы:
- `[MODIFY]` `src/gui/threads.py` — убрать дублирующие `log_saved` в ветках; переименовать сигнал `finished` → `checked` в `KrokiCheckThread`.
- `[MODIFY]` `src/gui/main_window.py` — обновить подключение сигнала (`checked`).
- `[MODIFY]` `src/core/tts_engine.py` — заменить busy-wait на блокирующее ожидание (`threading.Event`).
- `[MODIFY]` `src/core/renderer.py` — передать `lang` в контекст шаблона.
- `[MODIFY]` `templates/base.html` — `<html lang="{{ lang | default('en') }}">`.
- `[NEW]` `tests/test_core_fixes_007.py` — тесты: отсутствие дублей `log_saved`, наличие/передача `lang`, не-busy пауза TTS.

### Зависимости и влияние:
- Новые библиотеки: нет.
- Breaking changes: **НЕТ** публичного API. Сигнал `KrokiCheckThread.finished` переименовывается вместе с единственным потребителем.
- Риск: PyQt6 локально недоступен → тест `threads.py` возможен только через Qt-стаб (как в `test_gui_stubs.py`); TTS тестируется без `pyttsx3` (сам класс импортируется без него).

---

## 3. 📝 Пошаговый план реализации (Atomic Steps)

- [x] **Этап 1: Дубль лога** — в `threads.py` убран `log_saved` из веток PPTX/REVEAL/PNG-JPG; счётчик перенесён в `saved_suffix`, единый emit в конце тела цикла.
- [x] **Этап 2: Сигнал Kroki** — `finished` → `checked` в `KrokiCheckThread`; подключение в `main_window.py:95` обновлено.
- [x] **Этап 3: TTS пауза** — busy-wait заменён на `threading.Event.wait(timeout=0.1)`; `pause()`/`resume()`/`stop()` управляют событием.
- [x] **Этап 4: lang в шаблоне** — `renderer.py` передаёт `lang`; `base.html` использует `{{ lang | default('en') }}`.
- [x] **Этап 5: Тесты** — `tests/test_core_fixes_007.py` (6 проверок), проверено, что тест ловит старый баг (4 emit-а вместо 1).
- [x] **Этап 6: Верификация** — регистрация в `run_all.py`, `py_compile`, полный прогон **20/20**.

---

## 4. 🛡️ Риски, сайд-эффекты и план отката
- **Риски:** Переименование сигнала — забыть потребителя. Митигация: grep подтверждает **единственного** потребителя (`main_window.py:95`).
- **Риски:** Замена busy-wait может «залипнуть» при паузе. Митигация: `Event.wait(timeout=0.1)` в цикле для повторной проверки `_is_playing`.
- **План отката:** `git revert` — правки изолированы в 5 файлах + тест.

---

## 5. 🧪 План тестирования и критерии приемки
1. Автоматические тесты: `python tests/test_core_fixes_007.py` + `python tests/run_all.py`.
2. Ручная проверка: рендер `base.html` с `lang='ru'` → `lang="ru"`; лог конверсии не содержит двух «Сохранено».
3. Definition of Done:
   - [x] Один файл → одна строка «Сохранено» для всех форматов (суффикс сохранён для slides/pages).
   - [x] Нет сигнала с именем `finished` в `KrokiCheckThread`; потребитель обновлён.
   - [x] В TTS нет пустого busy-wait цикла.
   - [x] `<html lang>` соответствует языку; тест зелёный, батарея **20/20**.
