# Лог сессии: 2026-10-20 — Big Pickle (CI GUI smoke)

## Цель
Настоящая проверка GUI на реальном PyQt6 (offscreen) в CI.

## Действия
- scripts/smoke_gui.py: MainWindow() под offscreen, проверка виджетов/методов/меню/превью; skip если PyQt6 нет
- .github/workflows/gui-smoke.yml: ubuntu + PyQt6 + offscreen libs, на push/PR
- Локально: SKIP (PyQt6 не установлен), exit 0
- Батарея 26/26

## Результат
GUI проверяется по-настоящему в CI, а не только Qt-стабом.

