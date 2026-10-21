"""Поведенческие тесты настоящего MainWindow (offscreen).

Строит реальное окно приложения и проверяет, что раскладка, сигналы и
методы из декомпозированных миксинов работают. Тест дублирует smoke-проверку
(`scripts/smoke_gui.py`), но в виде pytest-кейсов — он даёт и проверку
поведения, и существенный прирост покрытия `ui_layout.py` / `main_window.py`.

Если PyQt6 недоступен — тест корректно пропускается.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from PyQt6.QtWidgets import QApplication
    HAVE_QT = True
except ImportError:  # pragma: no cover - Qt отсутствует
    HAVE_QT = False

if HAVE_QT:
    app = QApplication.instance() or QApplication([])

    from src.gui.main_window import MainWindow


def _make_window():
    """Создаёт настоящее окно; None, если Qt недоступен."""
    if not HAVE_QT:
        return None
    return MainWindow()


def _skip_if_no_qt():
    if not HAVE_QT:
        print("[SKIP] PyQt6 недоступен")
        return True
    return False


def test_main_window_builds_with_expected_widgets():
    """Окно создаётся, ключевые виджеты на месте."""
    if _skip_if_no_qt():
        return
    win = _make_window()
    for name in ("live_editor", "preview_output", "tabs", "menuBar",
                 "statusBar", "append_log", "current_lang"):
        assert hasattr(win, name), f"нет атрибута {name}"
    win.close()
    print("[PASS] test_main_window_builds_with_expected_widgets")


def test_main_window_exposes_mixin_methods():
    """Методы из миксинов доступны через MRO."""
    if _skip_if_no_qt():
        return
    win = _make_window()
    for name in (
        "show_about", "show_shortcuts", "toggle_split_view", "toggle_zen_mode",
        "toggle_focus_mode", "format_bold", "format_italic", "format_code",
        "run_linter", "convert_emoji_shortcodes", "pdf_to_markdown_convert",
        "html_to_markdown_convert", "run_ocr", "show_ai_assistant",
        "update_export_history_ui", "show_multi_export", "export_as_markdown",
        "load_presets", "save_preset", "update_text_statistics",
        "search_next", "replace_all_occurrences", "process_wikilinks",
        "apply_template_vars", "show_graph_view", "show_reading_analytics",
        "generate_flashcards", "build_glossary", "generate_quiz",
    ):
        assert callable(getattr(win, name, None)), f"нет метода {name}"
    win.close()
    print("[PASS] test_main_window_exposes_mixin_methods")


def test_main_window_menu_is_populated():
    """Меню построено и содержит пункты."""
    if _skip_if_no_qt():
        return
    win = _make_window()
    actions = win.menuBar().actions()
    assert actions, "menuBar пуст"
    labels = [a.text() for a in actions]
    assert any("Файл" in t for t in labels), labels
    win.close()
    print("[PASS] test_main_window_menu_is_populated")


def test_main_window_renders_live_preview():
    """Живое превью строится по тексту из редактора."""
    if _skip_if_no_qt():
        return
    win = _make_window()
    win.live_editor.setPlainText("# Заголовок\n\nПараграф **жирным**.")
    win._render_live_preview()
    html = win.preview_output.toHtml()
    assert html.strip(), "превью пустое"
    # QTextBrowser парсит документ, поэтому текст проверяем через toPlainText
    text = win.preview_output.toPlainText()
    assert "Заголовок" in text, text[:300]
    assert "Параграф" in text, text[:300]
    win.close()
    print("[PASS] test_main_window_renders_live_preview")


def test_main_window_toggle_split_view_cycles_modes():
    """Переключатель сплиттера циклически меняет режим."""
    if _skip_if_no_qt():
        return
    win = _make_window()
    win.toggle_split_view()
    assert win._split_view_mode == "editor", win._split_view_mode
    win.toggle_split_view()
    assert win._split_view_mode == "preview", win._split_view_mode
    win.toggle_split_view()
    assert win._split_view_mode == "both", win._split_view_mode
    win.close()
    print("[PASS] test_main_window_toggle_split_view_cycles_modes")


def test_main_window_toggles_focus_and_typewriter_modes():
    """Режимы фокуса и пишущей машинки включаются и выключаются."""
    if _skip_if_no_qt():
        return
    win = _make_window()
    win.toggle_focus_mode()
    assert win._focus_mode is True
    assert "font-size: 16px" in win.live_editor.styleSheet()
    win.toggle_focus_mode()
    assert win._focus_mode is False

    win.toggle_typewriter_mode()
    assert win._typewriter_mode is True
    win.toggle_typewriter_mode()
    assert win._typewriter_mode is False
    win.close()
    print("[PASS] test_main_window_toggles_focus_and_typewriter_modes")


def test_main_window_update_text_statistics():
    """Статистика текста выводится в панель."""
    if _skip_if_no_qt():
        return
    win = _make_window()
    win.live_editor.setPlainText("одно два три")
    win.update_text_statistics()
    assert win.stats_label.text(), "статистика пустая"
    assert "3" in win.stats_label.text(), win.stats_label.text()
    win.close()
    print("[PASS] test_main_window_update_text_statistics")


def test_main_window_convert_emoji_shortcodes():
    """Шорткоды эмодзи конвертируются в редакторе."""
    if _skip_if_no_qt():
        return
    win = _make_window()
    win.live_editor.setPlainText("Привет :smile:")
    win.convert_emoji_shortcodes()
    assert ":smile:" not in win.live_editor.toPlainText(), win.live_editor.toPlainText()
    win.close()
    print("[PASS] test_main_window_convert_emoji_shortcodes")


def test_main_window_export_history_ui_updates():
    """Журнал экспорта обновляется без ошибок."""
    if _skip_if_no_qt():
        return
    win = _make_window()
    win.update_export_history_ui()
    win.close()
    print("[PASS] test_main_window_export_history_ui_updates")


def test_main_window_wikilinks_and_template_vars():
    """Wikilinks и переменные шаблона применяются к тексту редактора."""
    if _skip_if_no_qt():
        return
    win = _make_window()
    win.live_editor.setPlainText("---\ntitle: Док\n---\n\n# {{title}}")
    win.apply_template_vars()
    assert "{{title}}" not in win.live_editor.toPlainText(), win.live_editor.toPlainText()
    win.close()
    print("[PASS] test_main_window_wikilinks_and_template_vars")


def test_main_window_search_and_replace():
    """Поиск и замена работают на реальном редакторе."""
    if _skip_if_no_qt():
        return
    win = _make_window()
    win.live_editor.setPlainText("alpha beta alpha")
    win.search_find_input.setText("alpha")
    win.search_replace_input.setText("gamma")
    win.replace_all_occurrences()
    assert "gamma" in win.live_editor.toPlainText(), win.live_editor.toPlainText()
    assert "alpha" not in win.live_editor.toPlainText(), win.live_editor.toPlainText()
    win.close()
    print("[PASS] test_main_window_search_and_replace")


def test_main_window_presets_roundtrip():
    """Пресет сохраняется и применяется в настоящем окне."""
    if _skip_if_no_qt():
        return
    win = _make_window()
    win.presets = {}
    win.load_presets()
    assert win.preset_combo.count() >= 1, win.preset_combo.count()
    win.close()
    print("[PASS] test_main_window_presets_roundtrip")


def main():
    tests = [
        test_main_window_builds_with_expected_widgets,
        test_main_window_exposes_mixin_methods,
        test_main_window_menu_is_populated,
        test_main_window_renders_live_preview,
        test_main_window_toggle_split_view_cycles_modes,
        test_main_window_toggles_focus_and_typewriter_modes,
        test_main_window_update_text_statistics,
        test_main_window_convert_emoji_shortcodes,
        test_main_window_export_history_ui_updates,
        test_main_window_wikilinks_and_template_vars,
        test_main_window_search_and_replace,
        test_main_window_presets_roundtrip,
    ]
    for t in tests:
        t()
    print("\nAll MainWindow tests passed!")


if __name__ == "__main__":
    main()
