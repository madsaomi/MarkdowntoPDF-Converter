# 📐 План реализации: PLAN-006 — Синхронизация зависимостей

> **Статус:** 🟢 APPROVED  
> **Дата создания:** 2026-10-20  
> **Автор / Агент:** Big Pickle (OpenCode)  
> **Связанная задача:** [TASK-006](file:///agents/tasks/active_task.md)  
> **Целевая ветка / Ревизия:** main  

---

## 1. 🎯 Цель и контекст
- **Проблема / Задача:** `requirements.txt` и `pyproject.toml` расходятся: в requirements жёсткие пины (`==`), в pyproject — диапазоны (`>=`); используемый в коде `speech_recognition` не объявлен нигде; `MarkupSafe` есть только в requirements; нет extras под speech.
- **Ожидаемый результат:** единая, непротиворечивая декларация зависимостей: один источник правды по версиям, все реально используемые библиотеки объявлены, оба файла согласованы.

---

## 2. 🔍 Анализ и затронутые компоненты (верифицировано)

### Факты из кода (grep):
| Библиотека | Импорт в коде | requirements.txt | pyproject.toml |
|---|---|---|---|
| markdown | `parser.py:1` | `Markdown==3.5.2` | `markdown>=3.5` |
| pymdown-extensions | (через markdown ext) | `pymdown-extensions==10.7` | `pymdown-extensions>=10.7` |
| jinja2 | `renderer.py:7` | `Jinja2==3.1.3` | `jinja2>=3.1` |
| MarkupSafe | (транзитивно) | `MarkupSafe>=2.1.0` | ✗ **отсутствует** |
| Pygments | (косвенно) | `Pygments==2.17.2` | `pygments>=2.17` |
| PyQt6 | GUI | `PyQt6>=6.5.0` | `extra gui` |
| weasyprint | (CLI/резолвер) | `WeasyPrint==61.2` | `extra pdf` |
| python-docx | `docx` | `>=1.1.0` | `extra docx` |
| htmldocx | `htmldocx` | `>=0.0.6` | `extra docx` |
| pypdf | `pdf_encrypt`, `pdf_to_markdown` | `>=4.0.0` | `>=4.0` |
| ebooklib | `epub_renderer` | `>=0.18` | `extra epub` |
| python-pptx | `pptx` | `>=1.0.0` | `extra pptx` |
| pyttsx3 | `tts_engine:163` | `>=2.90` | `extra tts` |
| pytesseract | `ocr_engine:10` | `>=0.3.10` | `extra ocr` |
| PyMuPDF | `fitz` (`image_renderer:72`) | `>=1.23.0` | `extra images` |
| Pillow | `PIL` (`ocr_engine:11`) | `>=10.0.0` | `extra images` |
| pyinstaller | build | `>=6.0.0` | `extra build` |
| **SpeechRecognition** | `main_window.py:1144` | ✗ **отсутствует** | ✗ **отсутствует** |

### Затронутые файлы:
- `[MODIFY]` `requirements.txt` — выравнивание пинов с `pyproject.toml`, добавление `SpeechRecognition`.
- `[MODIFY]` `pyproject.toml` — добавить `MarkupSafe` и extra `speech`; добавить `speech` в `all`.
- `[NEW]` `tests/test_dependency_sync.py` — тест: каждая `install_requires`-зависимость из pyproject присутствует в requirements и наоборот; прямо используемые в коде внешние библиотеки объявлены.

### Зависимости и влияние:
- Новые библиотеки: нет (только декларация уже используемой `SpeechRecognition`).
- Breaking changes: **НЕТ** — меняются только метаданные пакета.
- Риск: тест синхронизации не должен быть хрупким к порядку/регистру/оператору версии.

---

## 3. 📝 Пошаговый план реализации (Atomic Steps)

- [ ] **Этап 1: requirements.txt** — привести операторы версий к диапазонам `pyproject` (кроме обоснованных пинов), добавить `SpeechRecognition`, сохранить `MarkupSafe`.
- [ ] **Этап 2: pyproject.toml** — добавить `MarkupSafe`, extra `speech` (`SpeechRecognition` + `pyaudio`), расширить `all`.
- [ ] **Этап 3: Тест синхронизации** — `tests/test_dependency_sync.py` (парсер обоих файлов, сверка множеств; проверка «используется в коде → объявлено»).
- [ ] **Этап 4: Верификация** — регистрация в `run_all.py`, `py_compile`, полный прогон.

---

## 4. 🛡️ Риски, сайд-эффекты и план отката
- **Риски:** замена жёстких пинов на диапазоны может «потащить» мажорные обновления. Митигация: диапазоны ограничены снизу; для чувствительных к API (`markdown`) оставить осторожный `>=`.
- **План отката:** `git revert` — правки изолированы в двух метаданных-файлах и одном тесте.

---

## 5. 🧪 План тестирования и критерии приемки
1. Автоматические тесты: `python tests/test_dependency_sync.py` + `python tests/run_all.py`.
2. Ручная проверка: `python -m py_compile` обоих файлов невозможен (не .py) — вместо этого парсинг TOML/pip в тесте.
3. Definition of Done:
   - [ ] Все зависимости из `[project.dependencies]` присутствуют в `requirements.txt` и наоборот.
   - [ ] `SpeechRecognition` объявлен в обоих файлах.
   - [ ] Тест синхронизации зелёный, старая батарея не сломана.
