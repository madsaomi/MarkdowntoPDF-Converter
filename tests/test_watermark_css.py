"""Тесты генератора CSS watermark-дизайнера (PLAN-004/TASK-004).

Модуль `src.gui.watermark_designer` зависит от PyQt6. Логика генерации
вынесена в чистую функцию, поэтому при отсутствии PyQt6 модуль загружается
с подменённым PyQt6-стабом — проверяется именно генерация CSS.
"""
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _install_qt_stub_if_needed():
    """Если PyQt6 нет — подменяем минимальными заглушками (только для импорта)."""
    try:
        import PyQt6  # noqa: F401
        return False
    except ImportError:
        pass

    qt = types.ModuleType("PyQt6")
    widgets = types.ModuleType("PyQt6.QtWidgets")
    core = types.ModuleType("PyQt6.QtCore")
    gui = types.ModuleType("PyQt6.QtGui")

    class _Dialog:
        def __init__(self, *a, **k):
            pass

    widgets.QDialog = _Dialog
    for name in ("QVBoxLayout", "QHBoxLayout", "QPushButton", "QLabel", "QLineEdit",
                 "QSpinBox", "QComboBox", "QColorDialog", "QCheckBox", "QSlider",
                 "QFormLayout", "QTextBrowser"):
        setattr(widgets, name, type(name, (), {}))
    core.Qt = type("Qt", (), {"Orientation": type("O", (), {"Horizontal": 1})})
    gui.QColor = type("QColor", (), {})

    sys.modules["PyQt6"] = qt
    sys.modules["PyQt6.QtWidgets"] = widgets
    sys.modules["PyQt6.QtCore"] = core
    sys.modules["PyQt6.QtGui"] = gui
    return True


def load_builder():
    _install_qt_stub_if_needed()
    from src.gui.watermark_designer import build_watermark_css
    return build_watermark_css


def main():
    build = load_builder()

    # 1. Базовый CSS-фрагмент: текст/цвет/прозрачность/размер/угол
    css = build("DRAFT", (200, 200, 200), 0.25, 80, -45)
    assert css.startswith(".watermark {"), css
    assert css.rstrip().endswith("}"), css
    assert "rgba(200, 200, 200, 0.25)" in css, css
    assert "font-size: 80pt" in css, css
    assert "rotate(-45deg)" in css, css
    assert '"DRAFT"' in css, css

    # 2. CSS не содержит пользовательского HTML
    evil = build('</style><script>alert(1)</script>', (1, 2, 3), 0.5, 12, 0)
    assert "<script" not in evil, evil
    assert "style>" not in evil, evil
    assert "<" not in evil and ">" not in evil, evil

    # 3. Кавычки и обратные слэши санитизируются (нельзя вырваться из content:"")
    quotes = build('say "hi" \\ break', (0, 0, 0), 0.1, 20, 45)
    content_line = [l for l in quotes.splitlines() if l.strip().startswith("content:")][0]
    assert content_line.count('"') == 2, content_line

    # 4. Прозрачность клампится в [0, 1]
    assert "rgba(0, 0, 0, 0)" in build("x", (0, 0, 0), -5, 10, 0)
    assert "rgba(0, 0, 0, 1)" in build("x", (0, 0, 0), 99, 10, 0)

    # 5. Tiled-режим отличается от обычного
    normal = build("X", (255, 0, 0), 0.3, 40, -30, diagonal=True, tiled=False)
    tiled = build("X", (255, 0, 0), 0.3, 40, -30, diagonal=False, tiled=True)
    assert normal != tiled
    assert "position: fixed" in normal and "width: 100%" in tiled

    print("[PASS] test_build_watermark_css: безопасный CSS watermark (5 проверок)")
    print("\nAll watermark designer tests passed!")


if __name__ == "__main__":
    main()
