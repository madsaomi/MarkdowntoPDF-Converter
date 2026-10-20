"""Smoke-запуск настоящего GUI (PyQt6, offscreen).

Цель — поймать ошибки, которые не видны под Qt-стабом: несовпадение сигнатур
сигналов, отсутствующие атрибуты у реальных виджетов, ошибки при построении
UI-раскладки. Запускается в CI с ``QT_QPA_PLATFORM=offscreen``.

Если PyQt6 не установлен — скрипт сообщает об этом и завершается с кодом 0
(локальная разработка без GUI не должна «ломать» батарею).
"""
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> int:
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError as e:
        print(f"[SKIP] PyQt6 недоступен: {e}")
        return 0

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    app = QApplication.instance() or QApplication(sys.argv)
    failures = []

    # 1. Импорт окна
    try:
        from src.gui.main_window import MainWindow
        print("[PASS] импорт MainWindow")
    except Exception as e:
        print(f"[FAIL] импорт MainWindow: {e}")
        traceback.print_exc()
        return 1

    # 2. Создание окна (главная проверка: реальная раскладка + сигналы)
    try:
        win = MainWindow()
        print("[PASS] MainWindow() создано")
    except Exception as e:
        print(f"[FAIL] создание MainWindow: {e}")
        traceback.print_exc()
        return 1

    # 3. Ключевые виджеты/атрибуты
    expected = [
        "live_editor", "preview_output", "append_log",
        "current_lang", "tabs",
    ]
    for name in expected:
        if hasattr(win, name):
            print(f"[PASS] атрибут {name}")
        else:
            failures.append(f"нет атрибута {name}")
            print(f"[FAIL] нет атрибута {name}")

    # 4. Методы из декомпозированных миксинов (TASK-010/012)
    methods = [
        "show_about", "toggle_split_view", "format_bold",
        "pdf_to_markdown_convert", "show_ai_assistant",
        "update_export_history_ui",
    ]
    for name in methods:
        if callable(getattr(win, name, None)):
            print(f"[PASS] метод {name}")
        else:
            failures.append(f"нет метода {name}")
            print(f"[FAIL] нет метода {name}")

    # 5. Меню построено и содержит пункты
    try:
        menubar = win.menuBar()
        menus = menubar.actions()
        assert menus, "menuBar пуст"
        labels = [a.text() for a in menus]
        print(f"[PASS] меню: {len(labels)} шт. -> {labels[:5]}")
    except Exception as e:
        failures.append(f"menuBar: {e}")
        print(f"[FAIL] menuBar: {e}")

    # 6. Рендер превью не падает на простом тексте
    try:
        win.live_editor.setPlainText("# Заголовок\n\nТекст **жирный**.")
        win._render_live_preview()
        app.processEvents()
        print("[PASS] _render_live_preview")
    except Exception as e:
        failures.append(f"_render_live_preview: {e}")
        print(f"[FAIL] _render_live_preview: {e}")
        traceback.print_exc()

    try:
        win.close()
    except Exception:
        pass

    if failures:
        print(f"\n[FAIL] GUI smoke: {len(failures)} проблем")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("\n[PASS] GUI smoke: окно создаётся, меню и методы на месте")
    return 0


if __name__ == "__main__":
    sys.exit(main())
