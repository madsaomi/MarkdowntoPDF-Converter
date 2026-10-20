"""Тесты декомпозиции `ToolMethodsMixin` (TASK-012 / PLAN-012).

Проверяет, что 68 методов, ранее живших в одном классе `window_tools.py`,
перенесены в тематические миксины без потерь и дублей, а публичный
`ToolMethodsMixin` по-прежнему доступен из прежней точки импорта.
"""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

GUI = os.path.join(ROOT, "src", "gui")
WINDOW_TOOLS = os.path.join(GUI, "window_tools.py")
MIXINS_DIR = os.path.join(GUI, "mixins")

# Эталонный список 68 методов ToolMethodsMixin ДО декомпозиции (снят AST-замером).
BASELINE_METHODS = [
    "show_about", "show_shortcuts", "show_welcome_tour", "show_conversion_history",
    "show_diff_dialog", "show_latex_preview", "show_multi_export", "show_watermark_designer",
    "show_citation_manager", "show_csv_editor", "show_excalidraw", "show_calendar_notes",
    "show_pomodoro", "show_github_sync_dialog", "show_plugin_manager", "show_tag_cloud",
    "show_reading_analytics", "export_selection", "export_as_markdown", "save_version",
    "restore_version", "toggle_split_view", "toggle_zen_mode", "toggle_focus_mode",
    "toggle_typewriter_mode", "toggle_wysiwyg", "run_spell_check", "show_graph_view",
    "process_wikilinks", "pdf_to_markdown_convert", "html_to_markdown_convert",
    "text_to_speech_speak", "show_tts_settings", "generate_flashcards", "_save_anki_tsv",
    "build_glossary", "generate_quiz", "show_cloud_templates", "apply_template_vars",
    "convert_emoji_shortcodes", "add_multi_cursor", "run_linter", "format_markdown_document",
    "format_bold", "format_italic", "format_header", "format_code", "format_quote",
    "format_list", "insert_page_break", "run_ocr", "_export_tts_audio",
    "update_markdown_toc_in_editor", "show_toc_generator", "show_table_generator_dialog",
    "show_design_style_dialog", "ocr_image_to_text", "update_workspace_explorer",
    "restore_draft_if_exists", "open_output_folder", "print_document", "copy_styled_html",
    "filter_workspace_explorer", "load_workspace_file", "zoom_in", "zoom_out", "zoom_reset",
    "resizeEvent",
]

# Модули, появившиеся в рамках TASK-012 (миксины ToolMethodsMixin).
NEW_MIXIN_MODULES = [
    "help_dialogs.py", "view_dialogs.py", "export_tools.py", "editor_view_modes.py",
    "editor_formatting.py", "tts_media.py", "education.py", "convert_tools.py",
    "integrations.py", "workspace.py",
]


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _methods_in(path, cls_name=None):
    out = {}
    for node in ast.walk(ast.parse(_read(path), path)):
        if isinstance(node, ast.ClassDef) and (cls_name is None or node.name == cls_name):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out.setdefault(item.name, node.name)
    return out


def _all_available_methods():
    """Методы из window_tools.py (агрегатор) + всех модулей пакета mixins/."""
    out = _methods_in(WINDOW_TOOLS)
    for fn in sorted(os.listdir(MIXINS_DIR)):
        if not fn.endswith(".py") or fn == "__init__.py":
            continue
        out.update(_methods_in(os.path.join(MIXINS_DIR, fn)))
    return out


def test_no_method_lost():
    """Каждый из 68 базовых методов по-прежнему доступен."""
    available = _all_available_methods()
    missing = [m for m in BASELINE_METHODS if m not in available]
    assert not missing, f"Потеряны методы при декомпозиции: {missing}"
    print(f"[PASS] test_no_method_lost ({len(BASELINE_METHODS)} методов на месте)")


def test_no_duplicate_definitions():
    """Ни одно имя метода не определено в двух новых модулях."""
    seen = {}
    dupes = []
    for fn in NEW_MIXIN_MODULES:
        path = os.path.join(MIXINS_DIR, fn)
        for name in _methods_in(path):
            if name in seen:
                dupes.append(f"{name} ({seen[name]} + {fn})")
            seen[name] = fn
    assert not dupes, f"Дубли определений: {dupes}"
    print("[PASS] test_no_duplicate_definitions")


def test_aggregator_preserves_public_api():
    """`ToolMethodsMixin` импортируется из src.gui.window_tools и агрегирует всё."""
    tree = ast.parse(_read(WINDOW_TOOLS), WINDOW_TOOLS)
    cls = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "ToolMethodsMixin":
            cls = node
    assert cls is not None, "Класс ToolMethodsMixin исчез из window_tools.py"
    # агрегатор должен иметь базовые классы — это новые миксины
    base_names = {b.id for b in cls.bases if isinstance(b, ast.Name)}
    assert len(base_names) >= len(NEW_MIXIN_MODULES), \
        f"Агрегатор перечисляет не все миксины: {sorted(base_names)}"
    print(f"[PASS] test_aggregator_preserves_public_api ({len(base_names)} базовых миксинов)")


def test_new_mixins_are_plain_classes():
    """Новые миксины — простые классы без __init__ и без баз (требование плана)."""
    problems = []
    for fn in NEW_MIXIN_MODULES:
        path = os.path.join(MIXINS_DIR, fn)
        for node in ast.parse(_read(path), path).body:
            if isinstance(node, ast.ClassDef):
                if node.bases:
                    problems.append(f"{fn}:{node.name} имеет базовые классы")
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                        problems.append(f"{fn}:{node.name} определяет __init__")
    assert not problems, f"Новые миксины должны быть простыми классами: {problems}"
    print("[PASS] test_new_mixins_are_plain_classes")


def test_modules_compile():
    """Агрегатор и все новые модули компилируются."""
    paths = [WINDOW_TOOLS] + [os.path.join(MIXINS_DIR, fn) for fn in NEW_MIXIN_MODULES]
    for p in paths:
        with open(p, "rb") as f:
            compile(f.read(), p, "exec")
    print(f"[PASS] test_modules_compile ({len(paths)} модулей)")


def test_window_tools_shrunk():
    """Защита от обратного распухания: window_tools.py — тонкий агрегатор."""
    loc = len(_read(WINDOW_TOOLS).splitlines())
    n_methods = len(_methods_in(WINDOW_TOOLS, "ToolMethodsMixin"))
    assert loc < 120, f"window_tools.py снова распух: {loc} строк"
    assert n_methods <= 1, f"В агрегаторе снова методы: {n_methods}"
    print(f"[PASS] test_window_tools_shrunk ({loc} строк, {n_methods} методов)")


def main():
    tests = [
        test_modules_compile,
        test_no_method_lost,
        test_no_duplicate_definitions,
        test_aggregator_preserves_public_api,
        test_new_mixins_are_plain_classes,
        test_window_tools_shrunk,
    ]
    for t in tests:
        t()
    print("\nAll TASK-012 decomposition tests passed!")


if __name__ == "__main__":
    main()
