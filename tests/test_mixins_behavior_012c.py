"""Поведенческие тесты GUI-миксинов TASK-012 (часть 3).

Покрывают оставшиеся миксины: editor_view_modes (чистая логика режимов),
ai_tools (generate_api_docs, ai_improve_text), tts_media (_export_tts_audio).

Работает и под Qt-стабом, и под настоящим PyQt6 (offscreen + QApplication),
как test_mixins_behavior_012b.py.
"""
import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _install_qt_stub():
    try:
        import PyQt6  # noqa: F401
        return False
    except ImportError:
        pass

    class _Anything:
        def __init__(self, *a, **k):
            pass

        def __getattr__(self, item):
            return _Anything()

        def __call__(self, *a, **k):
            return _Anything()

        def __getitem__(self, item):
            return _Anything()

    class _Base:
        def __init__(self, *a, **k):
            pass

        def __getattr__(self, item):
            return _Anything()

    for mod_name in (
        "PyQt6", "PyQt6.QtWidgets", "PyQt6.QtCore", "PyQt6.QtGui",
        "PyQt6.QtPrintSupport", "PyQt6.QtSvg", "PyQt6.QtNetwork",
    ):
        mod = types.ModuleType(mod_name)
        mod.__getattr__ = lambda name, _m=mod: type(name, (_Base,), {})
        sys.modules[mod_name] = mod

    core = sys.modules["PyQt6.QtCore"]
    core.Qt = _Anything()
    core.QThread = _Base
    core.pyqtSignal = lambda *a, **k: _Anything()

    widgets = sys.modules["PyQt6.QtWidgets"]

    def _noop(*a, **k):
        return None

    widgets.QMessageBox = type("QMessageBox", (_Base,), {
        "information": staticmethod(_noop),
        "warning": staticmethod(_noop),
        "critical": staticmethod(_noop),
        "question": staticmethod(_noop),
    })
    widgets.QFileDialog = type("QFileDialog", (_Base,), {
        "getOpenFileName": staticmethod(_noop),
        "getSaveFileName": staticmethod(_noop),
    })
    return True


STUB_ACTIVE = _install_qt_stub()


def _ensure_qapplication():
    if STUB_ACTIVE:
        return None
    try:
        from PyQt6.QtWidgets import QApplication
        return QApplication.instance() or QApplication([])
    except Exception:
        return None


_APP = _ensure_qapplication()


class _NoopDialog:
    def __init__(self, returns=None):
        self._returns = returns
        self.calls = []

    def __getattr__(self, name):
        def _method(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            return self._returns
        return _method


def _patch_dialogs(*module_names):
    import importlib
    holders = {}
    for mod_name in module_names:
        mod = importlib.import_module(mod_name)
        holders[mod_name] = {}
        for cls_name in ("QMessageBox", "QFileDialog", "QInputDialog"):
            if hasattr(mod, cls_name):
                holder = _NoopDialog()
                setattr(mod, cls_name, holder)
                holders[mod_name][cls_name] = holder
    return holders


DIALOGS = _patch_dialogs(
    "src.gui.mixins.ai_tools",
    "src.gui.mixins.tts_media",
    "src.gui.mixins.editor_view_modes",
)


# ─── фейковый хост ───────────────────────────────────────────────────────────

class _MoveOperation:
    Start = "start"
    End = "end"


class _FakeCursor:
    MoveOperation = _MoveOperation

    def __init__(self, selected=""):
        self._selected = selected
        self.inserted = []
        self._pos = None

    def selectedText(self):
        return self._selected

    def insertText(self, t):
        self.inserted.append(t)

    def movePosition(self, *a, **k):
        self._pos = a[0] if a else None


class _FakeEditor:
    def __init__(self, text="", selected=""):
        self._text = text
        self._cursor = _FakeCursor(selected=selected)
        self._style = ""
        self._visible = True

    def toPlainText(self):
        return self._text

    def setPlainText(self, t):
        self._text = t

    def textCursor(self):
        return self._cursor

    def setTextCursor(self, c):
        self._cursor = c

    def styleSheet(self):
        return self._style

    def setStyleSheet(self, s):
        self._style = s

    def show(self):
        self._visible = True

    def hide(self):
        self._visible = False


class _FakeWidget:
    def __init__(self):
        self._visible = True
        self.sizes = None

    def show(self):
        self._visible = True

    def hide(self):
        self._visible = False

    def setSizes(self, s):
        self.sizes = s

    def setVisible(self, v):
        self._visible = v

    def setStyleSheet(self, s):
        pass


class FakeHost:
    def __init__(self, text="", selected=""):
        self.live_editor = _FakeEditor(text, selected)
        self.current_lang = "ru"
        self.logs = []
        self.toasts = []
        self.preview_output = _FakeWidget()
        self.editor_splitter = _FakeWidget()

    def append_log(self, msg):
        self.logs.append(msg)

    def toast(self, msg, kind="info"):
        self.toasts.append((msg, kind))

    def update_preview_from_editor(self):
        pass

    def statusBar(self):
        return _FakeWidget()


# ─── editor_view_modes ───────────────────────────────────────────────────────

def test_split_view_cycles_modes():
    """toggle_split_view циклически проходит both -> editor -> preview -> both."""
    from src.gui.mixins.editor_view_modes import EditorViewModesMixin

    class Host(FakeHost, EditorViewModesMixin):
        pass

    h = Host()
    assert getattr(h, "_split_view_mode", "both") == "both"

    h.toggle_split_view()
    assert h._split_view_mode == "editor", h._split_view_mode
    assert h.live_editor._visible is True
    assert h.preview_output._visible is False

    h.toggle_split_view()
    assert h._split_view_mode == "preview"
    assert h.live_editor._visible is False
    assert h.preview_output._visible is True

    h.toggle_split_view()
    assert h._split_view_mode == "both"
    assert h.editor_splitter.sizes == [500, 500]
    print("[PASS] test_split_view_cycles_modes")


def test_focus_mode_adds_and_removes_style():
    """toggle_focus_mode добавляет и затем снимает CSS-стиль с редактора."""
    from src.gui.mixins.editor_view_modes import EditorViewModesMixin

    class Host(FakeHost, EditorViewModesMixin):
        pass

    h = Host()
    base = h.live_editor.styleSheet()

    h.toggle_focus_mode()
    assert h._focus_mode is True
    assert "font-size: 16px" in h.live_editor.styleSheet()

    h.toggle_focus_mode()
    assert h._focus_mode is False
    assert h.live_editor.styleSheet() == base, h.live_editor.styleSheet()
    print("[PASS] test_focus_mode_adds_and_removes_style")


def test_typewriter_mode_sets_style_and_toasts():
    """toggle_typewriter_mode меняет стиль и уведомляет ON/OFF."""
    from src.gui.mixins.editor_view_modes import EditorViewModesMixin

    class Host(FakeHost, EditorViewModesMixin):
        pass

    h = Host()
    h.toggle_typewriter_mode()
    assert h._typewriter_mode is True
    assert "line-height: 2.0" in h.live_editor.styleSheet()
    assert h.toasts and "ON" in h.toasts[-1][0], h.toasts

    h.toggle_typewriter_mode()
    assert h._typewriter_mode is False
    assert "line-height: 2.0" not in h.live_editor.styleSheet()
    assert "OFF" in h.toasts[-1][0]
    print("[PASS] test_typewriter_mode_sets_style_and_toasts")


def test_wysiwyg_toggles_visibility():
    """toggle_wysiwyg скрывает редактор и показывает превью (и обратно)."""
    from src.gui.mixins.editor_view_modes import EditorViewModesMixin

    class Host(FakeHost, EditorViewModesMixin):
        pass

    h = Host()
    h.toggle_wysiwyg()
    assert h._wysiwyg is True
    assert h.live_editor._visible is False
    assert h.preview_output._visible is True

    h.toggle_wysiwyg()
    assert h._wysiwyg is False
    assert h.live_editor._visible is True
    assert h.preview_output._visible is False
    print("[PASS] test_wysiwyg_toggles_visibility")


def test_zen_mode_calls_showfullscreen():
    """toggle_zen_mode переключает полноэкранный режим."""
    from src.gui.mixins.editor_view_modes import EditorViewModesMixin

    class Host(FakeHost, EditorViewModesMixin):
        pass

    h = Host()
    calls = []
    h.showFullScreen = lambda: calls.append("full")
    h.showNormal = lambda: calls.append("normal")

    h.toggle_zen_mode()
    assert h._zen_mode is True and calls == ["full"], calls
    h.toggle_zen_mode()
    assert h._zen_mode is False and calls == ["full", "normal"], calls
    print("[PASS] test_zen_mode_calls_showfullscreen")


# ─── ai_tools ────────────────────────────────────────────────────────────────

def test_ai_improve_text_no_selection_warns():
    """ai_improve_text без выделения не трогает текст и показывает подсказку."""
    from src.gui.mixins.ai_tools import AiToolsMixin

    class Host(FakeHost, AiToolsMixin):
        pass

    h = Host(text="весь текст", selected="")
    h.ai_improve_text()
    assert h.live_editor._cursor.inserted == [], "текст не должен меняться"
    print("[PASS] test_ai_improve_text_no_selection_warns")


def test_generate_api_docs_from_file():
    """generate_api_docs строит Markdown-документацию по AST Python-файла."""
    import tempfile

    from src.gui.mixins.ai_tools import AiToolsMixin
    import src.gui.mixins.ai_tools as at

    class Host(FakeHost, AiToolsMixin):
        pass

    sample = (
        '"""Модуль."""\n\n'
        "def top(a, b):\n"
        '    """Складывает."""\n'
        "    return a + b\n\n"
        "class Greeter:\n"
        '    """Приветствие."""\n\n'
        "    def greet(self, name):\n"
        '        """Здоровается."""\n'
        "        return name\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "sample.py")
        with open(p, "w", encoding="utf-8") as f:
            f.write(sample)

        at.QFileDialog = types.SimpleNamespace(
            getOpenFileName=lambda *a, **k: (p, "")
        )
        h = Host()
        h.generate_api_docs()
        doc = h.live_editor.toPlainText()

        assert "API: sample.py" in doc, doc
        assert "## def top(a, b)" in doc, doc
        assert "## class Greeter" in doc, doc
        assert "### greet(name)" in doc, "self должен быть исключён из аргументов"
    print("[PASS] test_generate_api_docs_from_file")


def test_generate_api_docs_cancel_noop():
    """Отмена выбора файла ничего не меняет."""
    from src.gui.mixins.ai_tools import AiToolsMixin
    import src.gui.mixins.ai_tools as at

    class Host(FakeHost, AiToolsMixin):
        pass

    at.QFileDialog = types.SimpleNamespace(
        getOpenFileName=lambda *a, **k: ("", "")
    )
    h = Host(text="исходный")
    h.generate_api_docs()
    assert h.live_editor.toPlainText() == "исходный"
    print("[PASS] test_generate_api_docs_cancel_noop")


# ─── tts_media ───────────────────────────────────────────────────────────────

def test_export_tts_audio_saves_via_engine():
    """_export_tts_audio вызывает engine.export_to_file и сообщает об успехе."""
    from src.gui.mixins.tts_media import TtsMediaMixin
    import src.gui.mixins.tts_media as tm

    class Host(FakeHost, TtsMediaMixin):
        pass

    class _Engine:
        def __init__(self):
            self.exported = None

        def export_to_file(self, text, path, lang):
            self.exported = (text, path, lang)
            return True

    engine = _Engine()
    tm.QFileDialog = types.SimpleNamespace(
        getSaveFileName=lambda *a, **k: ("C:/out/speech.mp3", "")
    )
    h = Host(text="# Заголовок\n\nтекст")
    h._export_tts_audio(engine)
    assert engine.exported is not None
    _, path, lang = engine.exported
    assert path == "C:/out/speech.mp3"
    assert lang == "ru"
    assert h.toasts and h.toasts[-1][1] == "success", h.toasts
    print("[PASS] test_export_tts_audio_saves_via_engine")


def test_export_tts_audio_cancel_noop():
    """Отмена сохранения аудио не вызывает export."""
    from src.gui.mixins.tts_media import TtsMediaMixin
    import src.gui.mixins.tts_media as tm

    class Host(FakeHost, TtsMediaMixin):
        pass

    class _Engine:
        def __init__(self):
            self.called = False

        def export_to_file(self, *a, **k):
            self.called = True
            return True

    engine = _Engine()
    tm.QFileDialog = types.SimpleNamespace(
        getSaveFileName=lambda *a, **k: ("", "")
    )
    h = Host(text="текст")
    h._export_tts_audio(engine)
    assert engine.called is False, "export не должен вызываться при отмене"
    print("[PASS] test_export_tts_audio_cancel_noop")


def test_mixins_part3_have_no_collisions():
    """editor_view_modes, ai_tools, tts_media не конфликтуют по именам методов."""
    from src.gui.mixins.editor_view_modes import EditorViewModesMixin
    from src.gui.mixins.ai_tools import AiToolsMixin
    from src.gui.mixins.tts_media import TtsMediaMixin

    owners = {}
    dupes = []
    for cls in (EditorViewModesMixin, AiToolsMixin, TtsMediaMixin):
        for name in vars(cls):
            if name.startswith("__"):
                continue
            if name in owners:
                dupes.append(f"{name} ({owners[name]} + {cls.__name__})")
            owners[name] = cls.__name__
    assert not dupes, f"дублирующиеся методы: {dupes}"
    print("[PASS] test_mixins_part3_have_no_collisions")


def main():
    tests = [
        test_mixins_part3_have_no_collisions,
        test_split_view_cycles_modes,
        test_focus_mode_adds_and_removes_style,
        test_typewriter_mode_sets_style_and_toasts,
        test_wysiwyg_toggles_visibility,
        test_zen_mode_calls_showfullscreen,
        test_ai_improve_text_no_selection_warns,
        test_generate_api_docs_from_file,
        test_generate_api_docs_cancel_noop,
        test_export_tts_audio_saves_via_engine,
        test_export_tts_audio_cancel_noop,
    ]
    for t in tests:
        t()
    print("\nAll mixin behavior tests (part 3) passed!")


if __name__ == "__main__":
    main()
