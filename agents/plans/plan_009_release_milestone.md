# 📐 План реализации: PLAN-009 (M4) — Релизная веха: CI-сборка, релизный workflow, README

> **Статус:** ✅ COMPLETED (2026-10-20, коммит `TBD`)  
> **Дата создания:** 2026-10-20  
> **Автор / Агент:** Big Pickle (OpenCode)  
> **Связанная задача:** Веха M4 «Релиз» (TASK-009)  
> **Целевая ветка / Ревизия:** main  

---

## 1. 🎯 Цель и контекст
- **Проблема / Задача:** Веха M4 не закрыта: (1) CI только запускает тесты — `.exe` и инсталлятор не собираются; (2) нет релизного workflow, публикующего артефакты по тегу; (3) README содержит устаревшие данные (число тестов, структура, удалённые модули).
- **Ожидаемый результат:** воспроизводимая сборка Windows-артефактов в CI и локально (`scripts/build_release.ps1`), релизный workflow по тегу `v*`, актуальный README.

---

## 2. 🔍 Анализ и затронутые компоненты (верифицировано)

### Факты из репозитория:
- `.github/workflows/test.yml` — 5 версий Python, тесты. Сборки нет.
- `.github/workflows/integrity.yml` — проверка «Второго Мозга». Сборки нет.
- Релизного workflow **нет**; git-тегов нет; remote: `https://github.com/madsaomi/MarkdowntoPDF-Converter.git`.
- `build.py` — PyInstaller `--onefile`; требует `weasyprint-windows/dist/weasyprint.exe` либо `--skip-pdf-engine`; синхронизирует версию `installer.iss` из `src/__version__.py`.
- `installer.iss` — Inno Setup, `AppVersion=1.0.0`, `OutputBaseFilename=MarkdownToPDF_Setup`.
- `src/__version__.py` — `__version__ = "1.0.0"`.
- README устарел: `tests/ # 77 tests`, `pytest (69 tests)`, структура перечисляет уже удалённые модули (`templates_data.py`/`ModernSplashScreen`-эра), строки `main_window.py (~1330 lines)` и др.

### Затронутые файлы:
- `[NEW]` `scripts/build_release.ps1` — локальная сборка: PyInstaller → `dist/MarkdownToPDF.exe`, опционально Inno Setup → `dist/MarkdownToPDF_Setup.exe`; понятные сообщения, если чего-то нет.
- `[NEW]` `.github/workflows/release.yml` — по тегу `v*`: тесты → `build.py --skip-pdf-engine` (или с движком, если он есть в репо) → Inno Setup (choco) → `gh release create` с артефактами.
- `[MODIFY]` `README.md` — актуализировать: число тестов (**21 файл**), структуру (`src/core`/`src/gui` реальная), раздел Build/Release, бейдж CI, убрать удалённые модули.
- `[NEW]` `tests/test_release_config.py` — проверки консистентности: версия `__version__` == `installer.iss`; наличие/валидность релизного workflow и скрипта сборки (YAML/структура), наличие бейджа CI в README.

### Зависимости и влияние:
- Новые библиотеки: нет (PyInstaller/Inno Setup — внешние инструменты, не пакеты Python).
- Breaking changes: **НЕТ** — только добавление CI/скриптов и правки README.
- Риск: релизный workflow не сможет собрать PDF-движок (он большой бинарь). Митигация: собирать с `--skip-pdf-engine` и явно указывать в release notes; либо работать с движком, если он в репо (проверяется на месте).

---

## 3. 📝 Пошаговый план реализации (Atomic Steps)

- [x] **Этап 1: Скрипт сборки** — `scripts/build_release.ps1`: проверка Python/PyInstaller, вызов `build.py`, поиск `iscc.exe` (Inno Setup) и сборка инсталлятора, итоговый отчёт. **Важно: файл сохранён в UTF-8 **with BOM** — без BOM PowerShell 5.1 декодирует кириллицу как ANSI и даёт ложные ошибки парсинга (проверено, добавлен тест).**
- [x] **Этап 2: Релизный workflow** — `.github/workflows/release.yml`: триггер `push: tags: ['v*']`, `workflow_dispatch`; job `test` (ubuntu) → job `build-windows`: deps → `build.py --skip-pdf-engine` → Inno Setup (choco) → `upload-artifact` + `softprops/action-gh-release`.
- [x] **Этап 3: README** — актуализированы бейджи (реальный репозиторий + badge релиза), структура (`src/config.py` + 28 core + 26 gui), «22 test files», раздел Build/Release со скриптом и тегом.
- [x] **Этап 4: Тесты** — `tests/test_release_config.py`: 6 проверок (версия↔installer, workflow, существование referenced-файлов, скрипт, UTF-8 BOM, README) без PyYAML.
- [x] **Этап 5: Верификация** — регистрация в `run_all.py`, `py_compile`, PS1-парсер (0 ошибок), полный прогон **22/22**.

---

## 4. 🛡️ Риски, сайд-эффекты и план отката
- **Риски:** сборка `.exe` в CI не воспроизводится локально (Python 3.15, нет PyInstaller) — тест проверяет только конфиг, а не саму сборку. Митигация: конфиг-тесты + ручной запуск `build.py --skip-pdf-engine` при возможности.
- **Риски:** YAML-парсинг без PyYAML. Митигация: в тесте — минимальный построчный/regex-анализ, как в `test_dependency_sync.py`.
- **План отката:** `git revert` — правки изолированы в 2 новых файлах CI/скрипта, README и одном тесте.

---

## 5. 🧪 План тестирования и критерии приемки
1. Автоматические тесты: `python tests/test_release_config.py` + `python tests/run_all.py`.
2. Ручная проверка: `python build.py --skip-pdf-engine` (если доступен PyInstaller) или сухой прогон скрипта; проверка `actionlint`-совместимости YAML вручную.
3. Definition of Done:
   - [x] `.github/workflows/release.yml` валиден и ссылается на существующие шаги/файлы.
   - [x] `scripts/build_release.ps1` собирает `.exe` и (при наличии) инсталлятор; парсится PowerShell без ошибок (UTF-8 BOM).
   - [x] README соответствует реальности (22 тест-файла, актуальная структура).
   - [x] Тест зелёный, батарея **22/22**.
