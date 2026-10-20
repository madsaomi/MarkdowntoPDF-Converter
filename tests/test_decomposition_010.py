"""Тесты декомпозиции God-object MainWindow (PLAN-010 / TASK-010).

Проверяет, что перенос методов в миксины НЕ потерял и НЕ продублировал
ничего, и что main_window.py действительно уменьшился.
"""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

GUI = os.path.join(ROOT, "src", "gui")
MAIN_WINDOW = os.path.join(GUI, "main_window.py")
MIXINS_DIR = os.path.join(GUI, "mixins")

# Эталонный список методов MainWindow ДО декомпозиции (74 шт., снят AST-замером).
BASELINE_METHODS = [
    "__init__", "_resolve_asset", "on_kroki_check_finished", "_setup_shortcuts",
    "load_settings", "save_settings", "closeEvent", "add_to_recent",
    "update_recent_menu", "open_recent", "toggle_theme", "dragEnterEvent",
    "dropEvent", "select_custom_css", "select_docx_template", "select_files",
    "select_folder", "toggle_watch", "on_file_changed", "_run_single_conversion",
    "_start_conversion", "convert_files", "_get_template_dir", "_get_weasyprint_path",
    "_get_extension", "_get_options", "append_log", "cancel_conversion",
    "update_preview_from_editor", "update_preview", "get_current_document_dir",
    "_render_live_preview", "on_all_done", "load_presets", "save_preset",
    "delete_preset", "on_preset_changed", "tr_msg", "change_lang", "retranslate_ui",
    "load_welcome_document", "on_editor_changed", "update_text_statistics",
    "toggle_search_panel", "search_next", "replace_all_occurrences", "on_finished_one",
    "add_to_export_history", "update_export_history_ui", "open_exported_file",
    "open_exported_folder", "get_windows_theme", "autosave_draft",
    "save_current_workspace_file", "save_revision", "show_revision_history",
    "goto_editor_line", "show_document_audit", "auto_fix_document_issues",
    "show_doc_templates_dialog", "_wrap_selection", "start_voice_input",
    "ai_improve_text", "ai_generate_outline", "show_ai_assistant",
    "export_task_board", "generate_api_docs", "eventFilter", "show_merge_dialog",
    "show_readability_dashboard", "show_stats_menu", "show_snippets_dialog",
    "sync_scroll_preview", "toast",
]


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _class_methods(path, cls_name):
    """{method_name: ast_node} для указанного класса в файле."""
    tree = ast.parse(_read(path), path)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == cls_name:
            return {
                n.name: n
                for n in node.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
    return {}


def _all_gui_methods():
    """Методы MainWindow + всех миксинов пакета src/gui/mixins/."""
    out = _class_methods(MAIN_WINDOW, "MainWindow")
    if os.path.isdir(MIXINS_DIR):
        for fn in sorted(os.listdir(MIXINS_DIR)):
            if not fn.endswith(".py") or fn == "__init__.py":
                continue
            path = os.path.join(MIXINS_DIR, fn)
            tree = ast.parse(_read(path), path)
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            out.setdefault(item.name, item)
    return out


def test_no_method_lost():
    """Каждый из 74 базовых методов по-прежнему доступен."""
    available = _all_gui_methods()
    missing = [m for m in BASELINE_METHODS if m not in available]
    assert not missing, f"Потеряны методы при декомпозиции: {missing}"
    print(f"[PASS] test_no_method_lost ({len(BASELINE_METHODS)} методов на месте)")


def test_no_duplicate_definitions():
    """Ни одно имя метода не определено одновременно в MainWindow и миксине."""
    in_main = set(_class_methods(MAIN_WINDOW, "MainWindow"))
    dupes = []
    if os.path.isdir(MIXINS_DIR):
        for fn in sorted(os.listdir(MIXINS_DIR)):
            if not fn.endswith(".py") or fn == "__init__.py":
                continue
            path = os.path.join(MIXINS_DIR, fn)
            tree = ast.parse(_read(path), path)
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if item.name in in_main:
                                dupes.append(f"{item.name} ({fn})")
    assert not dupes, f"Дубли определений: {dupes}"
    print("[PASS] test_no_duplicate_definitions")


def test_mixins_are_plain_classes():
    """Миксины не имеют __init__ и базовых классов (требование PLAN-010)."""
    assert os.path.isdir(MIXINS_DIR), "Нет пакета src/gui/mixins/"
    problems = []
    for fn in sorted(os.listdir(MIXINS_DIR)):
        if not fn.endswith(".py") or fn == "__init__.py":
            continue
        tree = ast.parse(_read(os.path.join(MIXINS_DIR, fn)), fn)
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                if node.bases:
                    problems.append(f"{fn}:{node.name} имеет базовые классы")
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                        problems.append(f"{fn}:{node.name} определяет __init__")
    assert not problems, f"Миксины должны быть простыми классами: {problems}"
    print("[PASS] test_mixins_are_plain_classes")


def test_main_window_shrunk():
    """Защита от обратного распухания: main_window.py и MainWindow уменьшились."""
    loc = len(_read(MAIN_WINDOW).splitlines())
    n_methods = len(_class_methods(MAIN_WINDOW, "MainWindow"))
    assert loc < 1200, f"main_window.py снова распух: {loc} строк"
    assert n_methods < 60, f"MainWindow снова God-object: {n_methods} методов"
    print(f"[PASS] test_main_window_shrunk ({loc} строк, {n_methods} методов)")


def test_modules_compile():
    """Все модули пакета миксинов и main_window.py компилируются."""
    paths = [MAIN_WINDOW]
    if os.path.isdir(MIXINS_DIR):
        paths += [
            os.path.join(MIXINS_DIR, fn)
            for fn in sorted(os.listdir(MIXINS_DIR))
            if fn.endswith(".py")
        ]
    for p in paths:
        with open(p, "rb") as f:
            compile(f.read(), p, "exec")
    print(f"[PASS] test_modules_compile ({len(paths)} модулей)")


def main():
    tests = [
        test_modules_compile,
        test_no_method_lost,
        test_no_duplicate_definitions,
        test_mixins_are_plain_classes,
        test_main_window_shrunk,
    ]
    for t in tests:
        t()
    print("\nAll TASK-010 decomposition tests passed!")


if __name__ == "__main__":
    main()
