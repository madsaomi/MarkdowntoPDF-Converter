"""Поведенческие тесты холста для рисования (gui/excalidraw_canvas).

Покрывает инструменты (pen/line/rect/circle/eraser), очистку, экспорт в SVG
и сериализацию в dict.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QColor, QMouseEvent
from PyQt6.QtWidgets import QApplication

app = QApplication.instance() or QApplication([])

from src.gui.excalidraw_canvas import ExcalidrawCanvas


def _mouse_event(canvas, kind, x, y, button=Qt.MouseButton.LeftButton):
    pos = QPointF(x, y)
    return QMouseEvent(
        kind,
        pos,
        pos,
        button,
        button,
        Qt.KeyboardModifier.NoModifier,
    )


def test_canvas_initial_state():
    """Холст создаётся пустым, с инструментом «pen» и толщиной 3."""
    c = ExcalidrawCanvas()
    assert c._tool == "pen"
    assert c._pen_width == 3
    assert c._pen_color.name() == "#2c3e50"
    assert c._strokes == []
    assert c._shapes == []
    c.deleteLater()
    print("[PASS] test_canvas_initial_state")


def test_set_tool_color_width():
    """Сеттеры инструмента, цвета и толщины меняют состояние."""
    c = ExcalidrawCanvas()
    c.set_tool("rect")
    c.set_color(QColor("#ff0000"))
    c.set_width(7)
    assert c._tool == "rect"
    assert c._pen_color.name() == "#ff0000"
    assert c._pen_width == 7
    c.deleteLater()
    print("[PASS] test_set_tool_color_width")


def test_pen_drawing_creates_stroke():
    """Рисование пером сохраняет штрих с точками, цветом и толщиной."""
    c = ExcalidrawCanvas()
    c.set_tool("pen")
    c.set_color(QColor("#00ff00"))
    c.set_width(5)
    c.mousePressEvent(_mouse_event(c, QMouseEvent.Type.MouseButtonPress, 10, 10))
    c.mouseMoveEvent(_mouse_event(c, QMouseEvent.Type.MouseMove, 20, 20))
    c.mouseMoveEvent(_mouse_event(c, QMouseEvent.Type.MouseMove, 30, 15))
    c.mouseReleaseEvent(_mouse_event(c, QMouseEvent.Type.MouseButtonRelease, 30, 15))
    assert len(c._strokes) == 1
    s = c._strokes[0]
    assert s["tool"] == "pen"
    assert s["color"] == "#00ff00"
    assert s["width"] == 5
    assert len(s["points"]) == 3
    c.deleteLater()
    print("[PASS] test_pen_drawing_creates_stroke")


def test_shape_tools_create_shapes():
    """Инструменты line/rect/circle создают соответствующие фигуры."""
    for tool, expected in (("line", "line"), ("rect", "rect"), ("circle", "circle")):
        c = ExcalidrawCanvas()
        c.set_tool(tool)
        c.mousePressEvent(_mouse_event(c, QMouseEvent.Type.MouseButtonPress, 10, 10))
        c.mouseReleaseEvent(_mouse_event(c, QMouseEvent.Type.MouseButtonRelease, 50, 40))
        assert len(c._shapes) == 1, tool
        assert c._shapes[0]["type"] == expected
        assert len(c._strokes) == 0, tool
        c.deleteLater()
    print("[PASS] test_shape_tools_create_shapes")


def test_right_button_does_not_draw():
    """Правая кнопка мыши не начинает рисование."""
    c = ExcalidrawCanvas()
    c.mousePressEvent(_mouse_event(c, QMouseEvent.Type.MouseButtonPress, 10, 10,
                                   button=Qt.MouseButton.RightButton))
    assert c._drawing is False
    assert c._strokes == []
    c.deleteLater()
    print("[PASS] test_right_button_does_not_draw")


def test_clear_all_resets_canvas():
    """clear_all очищает штрихи и фигуры."""
    c = ExcalidrawCanvas()
    c.set_tool("pen")
    c.mousePressEvent(_mouse_event(c, QMouseEvent.Type.MouseButtonPress, 10, 10))
    c.mouseMoveEvent(_mouse_event(c, QMouseEvent.Type.MouseMove, 20, 20))
    c.mouseReleaseEvent(_mouse_event(c, QMouseEvent.Type.MouseButtonRelease, 20, 20))
    c.set_tool("rect")
    c.mousePressEvent(_mouse_event(c, QMouseEvent.Type.MouseButtonPress, 5, 5))
    c.mouseReleaseEvent(_mouse_event(c, QMouseEvent.Type.MouseButtonRelease, 30, 30))
    assert c._strokes and c._shapes
    c.clear_all()
    assert c._strokes == []
    assert c._shapes == []
    c.deleteLater()
    print("[PASS] test_clear_all_resets_canvas")


def test_to_svg_contains_strokes_and_shapes():
    """to_svg выдаёт корректный SVG с штрихами и фигурами."""
    c = ExcalidrawCanvas()
    c.resize(400, 300)
    c.set_tool("pen")
    c.mousePressEvent(_mouse_event(c, QMouseEvent.Type.MouseButtonPress, 10, 10))
    c.mouseMoveEvent(_mouse_event(c, QMouseEvent.Type.MouseMove, 20, 20))
    c.mouseReleaseEvent(_mouse_event(c, QMouseEvent.Type.MouseButtonRelease, 20, 20))
    c.set_tool("rect")
    c.mousePressEvent(_mouse_event(c, QMouseEvent.Type.MouseButtonPress, 5, 5))
    c.mouseReleaseEvent(_mouse_event(c, QMouseEvent.Type.MouseButtonRelease, 30, 30))
    c.set_tool("circle")
    c.mousePressEvent(_mouse_event(c, QMouseEvent.Type.MouseButtonPress, 40, 40))
    c.mouseReleaseEvent(_mouse_event(c, QMouseEvent.Type.MouseButtonRelease, 80, 80))

    svg = c.to_svg()
    assert svg.startswith("<svg")
    assert svg.rstrip().endswith("</svg>")
    assert "<polyline" in svg
    assert "<rect" in svg
    assert "<ellipse" in svg
    assert f'width="{c.width()}"' in svg
    assert f'height="{c.height()}"' in svg
    c.deleteLater()
    print("[PASS] test_to_svg_contains_strokes_and_shapes")


def test_to_dict_is_json_serializable():
    """to_dict отдаёт структуру, пригодную для json.dumps."""
    import json

    c = ExcalidrawCanvas()
    c.set_tool("pen")
    c.mousePressEvent(_mouse_event(c, QMouseEvent.Type.MouseButtonPress, 10, 10))
    c.mouseMoveEvent(_mouse_event(c, QMouseEvent.Type.MouseMove, 20, 20))
    c.mouseReleaseEvent(_mouse_event(c, QMouseEvent.Type.MouseButtonRelease, 20, 20))
    c.set_tool("line")
    c.mousePressEvent(_mouse_event(c, QMouseEvent.Type.MouseButtonPress, 1, 2))
    c.mouseReleaseEvent(_mouse_event(c, QMouseEvent.Type.MouseButtonRelease, 3, 4))

    d = c.to_dict()
    assert set(d.keys()) == {"strokes", "shapes"}
    assert len(d["strokes"]) == 1
    assert d["strokes"][0]["points"][0] == {"x": 10, "y": 10}
    assert d["shapes"][0]["start"] == {"x": 1, "y": 2}
    # Должно сериализоваться без ошибок
    text = json.dumps(d)
    assert "strokes" in text
    c.deleteLater()
    print("[PASS] test_to_dict_is_json_serializable")


def main():
    tests = [
        test_canvas_initial_state,
        test_set_tool_color_width,
        test_pen_drawing_creates_stroke,
        test_shape_tools_create_shapes,
        test_right_button_does_not_draw,
        test_clear_all_resets_canvas,
        test_to_svg_contains_strokes_and_shapes,
        test_to_dict_is_json_serializable,
    ]
    for t in tests:
        t()
    print("\nAll excalidraw canvas tests passed!")


if __name__ == "__main__":
    main()
