"""Тесты судьбы фичевых заглушек (PLAN-008/TASK-008).

Проверяет:
1. Шесть ранее недостижимых методов получили call site в меню (`ui_layout.py`).
2. Мёртвый декор удалён: нет импортов/ссылок `CustomTitleBar`/`AmbientGlowWidget`,
   нет файлов `splash_screen.py`/`custom_titlebar.py`/`ambient_glow.py`.
3. `ui_layout.py` и `main_window.py` компилируются после правок.
"""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

UI_LAYOUT = os.path.join(ROOT, "src", "gui", "ui_layout.py")
MAIN_WINDOW = os.path.join(ROOT, "src", "gui", "main_window.py")
GUI_DIR = os.path.join(ROOT, "src", "gui")

# Методы, которые были недостижимы и теперь подключены к меню
WIRED_METHODS = [
    "show_ai_assistant",
    "ai_improve_text",
    "ai_generate_outline",
    "export_task_board",
    "generate_api_docs",
    "start_voice_input",
]

# Полностью удалённый мёртвый декор
REMOVED_FILES = ["splash_screen.py", "custom_titlebar.py", "ambient_glow.py"]


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def test_methods_wired_to_menu():
    """Каждый из 6 методов присутствует в ui_layout.py (подключён к меню Tools)."""
    src = _read(UI_LAYOUT)
    missing = [m for m in WIRED_METHODS if f"window.{m}" not in src]
    assert not missing, f"Не подключены к меню: {missing}"
    print(f"[PASS] test_methods_wired_to_menu: {len(WIRED_METHODS)} методов подключено")


def test_methods_still_defined():
    """Методы по-прежнему определены в MainWindow (не удалены ошибочно)."""
    tree = ast.parse(_read(MAIN_WINDOW), MAIN_WINDOW)
    defined = set()
    for cls in ast.walk(tree):
        if isinstance(cls, ast.ClassDef) and cls.name == "MainWindow":
            for node in cls.body:
                if isinstance(node, ast.FunctionDef):
                    defined.add(node.name)
    missing = [m for m in WIRED_METHODS if m not in defined]
    assert not missing, f"Методы отсутствуют в MainWindow: {missing}"
    print("[PASS] test_methods_still_defined")


def test_dead_decor_removed():
    """Файлы мёртвого декора удалены, ссылок не осталось."""
    for fname in REMOVED_FILES:
        assert not os.path.exists(os.path.join(GUI_DIR, fname)), f"Файл не удалён: {fname}"

    src = _read(MAIN_WINDOW)
    for symbol in ("CustomTitleBar", "AmbientGlowWidget", "custom_titlebar", "ambient_glow"):
        assert symbol not in src, f"Остался мёртвый декор: {symbol}"
    print("[PASS] test_dead_decor_removed")


def test_no_stale_splash_references():
    """Нигде в проекте не осталось ссылок на ModernSplashScreen/splash_screen."""
    hits = []
    self_name = os.path.basename(__file__)
    for dirpath, _dirs, files in os.walk(ROOT):
        if any(part in dirpath for part in ("__pycache__", ".git", "agents", "node_modules")):
            continue
        for fn in files:
            if not fn.endswith(".py") or fn == self_name:
                continue
            path = os.path.join(dirpath, fn)
            try:
                content = _read(path)
            except Exception:
                continue
            if "ModernSplashScreen" in content or "splash_screen" in content:
                hits.append(os.path.relpath(path, ROOT))
    assert not hits, f"Остались ссылки на splash: {hits}"
    print("[PASS] test_no_stale_splash_references")


def test_files_compile():
    """Изменённые файлы компилируются."""
    for path in (UI_LAYOUT, MAIN_WINDOW):
        with open(path, "rb") as f:
            compile(f.read(), path, "exec")
    print("[PASS] test_files_compile")


def main():
    tests = [
        test_files_compile,
        test_methods_wired_to_menu,
        test_methods_still_defined,
        test_dead_decor_removed,
        test_no_stale_splash_references,
    ]
    for t in tests:
        t()
    print("\nAll TASK-008 stub-wiring tests passed!")


if __name__ == "__main__":
    main()
