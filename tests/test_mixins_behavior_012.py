"""Поведенческие тесты GUI-миксинов TASK-012 (под Qt-стабом).

В отличие от `test_decomposition_012.py` (только структура: имена методов),
здесь методы реально вызываются с **фейковым хостом**, а диалоги Qt
подменяются, чтобы не блокировать выполнение. Проверяем настоящую логику:
запись файлов, вызовы `append_log`, обработку пустых состояний, fallback-ветки.

PyQt6 в этом окружении не устанавливается (Python 3.15), поэтому используется
Qt-стаб; в CI дополнительно прогоняется реальный smoke (scripts/smoke_gui.py).
"""
import os
import sys
import tempfile
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Реальному Qt для виджетов нужен дисплей; без GUI — offscreen (до импорта Qt).
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

    # У ключевых виджетов-диалогов должны быть вызываемые статические методы
    # (QMessageBox.information и т.п.) — иначе реальные вызовы падают с
    # AttributeError, потому что базовый класс не отдаёт атрибуты через __getattr__.
    widgets = sys.modules["PyQt6.QtWidgets"]

    def _noop(*a, **k):
        return None

    msgbox = type("QMessageBox", (_Base,), {
        "information": staticmethod(_noop),
        "warning": staticmethod(_noop),
        "critical": staticmethod(_noop),
        "question": staticmethod(_noop),
        "about": staticmethod(_noop),
    })
    widgets.QMessageBox = msgbox

    for cls_name in ("QInputDialog", "QFileDialog", "QColorDialog", "QFontDialog"):
        cls = type(cls_name, (_Base,), {})
        for m in ("getText", "getItem", "getInt", "getDouble", "getSaveFileName",
                  "getOpenFileName", "getExistingDirectory", "getSaveFileName",
                  "getColor", "getFont", "exec"):
            setattr(cls, m, staticmethod(_noop))
        setattr(widgets, cls_name, cls)

    return True


STUB_ACTIVE = _install_qt_stub()


class _NoopDialog:
    """Заменяет QMessageBox/QFileDialog в модулях миксинов.

    С настоящим PyQt6 вызовы вида ``QMessageBox.information(fake_host, ...)``
    падают (fake_host — не QWidget), а модальные диалоги блокируют прогон.
    Поэтому методы диалогов принудительно заменяются no-op в каждом модуле,
    который импортирует соответствующий класс.
    """

    def __init__(self, returns=None):
        self._returns = returns
        self.calls = []

    def _record(self, name, *args, **kwargs):
        self.calls.append((name, args, kwargs))
        if self._returns is not None:
            return self._returns
        return None

    def __getattr__(self, name):
        def _method(*args, **kwargs):
            return self._record(name, *args, **kwargs)
        return _method


def _patch_msgbox(*module_names):
    """Делает QMessageBox.* no-op в указанных модулях."""
    import importlib
    patched = []
    for mod_name in module_names:
        mod = importlib.import_module(mod_name)
        if hasattr(mod, "QMessageBox"):
            holder = _NoopDialog()
            try:
                mod.QMessageBox = holder
                patched.append((mod, holder))
            except Exception:
                pass
    return patched


# Модули миксинов, где вызываются QMessageBox-методы с фейковым хостом.
MSG_DIALOG_MODULES = (
    "src.gui.mixins.export_tools",
    "src.gui.mixins.editor_formatting",
    "src.gui.mixins.workspace",
    "src.gui.mixins.education",
    "src.gui.mixins.view_dialogs",
)
_patch_msgbox(*MSG_DIALOG_MODULES)


# ─── фейковый хост и вспомогательное ─────────────────────────────────────────

class _FakeCursor:
    def __init__(self, selected="", text=""):
        self._selected = selected
        self.inserted = []

    def selectedText(self):
        return self._selected

    def insertText(self, t):
        self.inserted.append(t)


class _FakeEditor:
    def __init__(self, text="", selected=""):
        self._text = text
        self._cursor = _FakeCursor(selected=selected)

    def toPlainText(self):
        return self._text

    def setPlainText(self, t):
        self._text = t

    def textCursor(self):
        return self._cursor


class FakeHost:
    """Минимальный хост-объект, которого требуют миксины."""

    def __init__(self, text="", selected=""):
        self.live_editor = _FakeEditor(text, selected)
        self.current_lang = "ru"
        self.logs = []
        self.toasts = []
        self.selected_files = []
        self.preview_renders = 0
        self._preview_rendered = False
        self.kroki_available = False

    def append_log(self, msg):
        self.logs.append(msg)

    def toast(self, msg, kind="info"):
        self.toasts.append((msg, kind))

    def _render_live_preview(self):
        self.preview_renders += 1

    def update_preview_from_editor(self):
        self.preview_renders += 1

    def update_export_history_ui(self):
        self.logs.append("history-ui")

    def _get_template_dir(self):
        return ""

    def _get_options(self):
        return None

    def get_current_document_dir(self):
        return ""


def _mixins():
    from src.gui.mixins.export_tools import ExportToolsMixin
    from src.gui.mixins.view_dialogs import ViewDialogsMixin
    from src.gui.mixins.editor_formatting import EditorFormattingMixin
    from src.gui.mixins.workspace import WorkspaceMixin
    from src.gui.mixins.education import EducationMixin
    return ExportToolsMixin, ViewDialogsMixin, EditorFormattingMixin, WorkspaceMixin, EducationMixin


def _patch_qfiledialog(monkeypatch_target, returns):
    """Подменяет QFileDialog в модуле миксина (разные модули — разные объекты)."""
    import src.gui.mixins.export_tools as et
    et.QFileDialog = returns


# ─── export_tools ────────────────────────────────────────────────────────────

def test_export_as_markdown_writes_file():
    """export_as_markdown сохраняет текст редактора в файл и логирует."""
    from src.gui.mixins.export_tools import ExportToolsMixin

    class Host(FakeHost, ExportToolsMixin):
        pass

    h = Host(text="# Привет\n\nтело")
    import src.gui.mixins.export_tools as et

    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "doc.md")
        et.QFileDialog = types.SimpleNamespace(
            getSaveFileName=lambda *a, **k: (out, "Markdown (*.md)")
        )
        host = Host.__new__(Host)
        FakeHost.__init__(host, text="# Привет\n\nтело")
        host.export_as_markdown()
        assert os.path.isfile(out), "файл не создан"
        with open(out, encoding="utf-8") as f:
            assert f.read() == "# Привет\n\nтело"
        assert any("Markdown" in m for m in host.logs), f"нет лога: {host.logs}"
    print("[PASS] test_export_as_markdown_writes_file")


def test_export_as_markdown_cancel_no_write():
    """Отмена диалога (пустой путь) не создаёт файл и не логирует."""
    from src.gui.mixins.export_tools import ExportToolsMixin

    class Host(FakeHost, ExportToolsMixin):
        pass

    import src.gui.mixins.export_tools as et
    et.QFileDialog = types.SimpleNamespace(
        getSaveFileName=lambda *a, **k: ("", "")
    )
    host = Host(text="x")
    host.logs.clear()
    host.export_as_markdown()
    assert host.logs == [], f"не должно быть логов: {host.logs}"
    print("[PASS] test_export_as_markdown_cancel_no_write")


def test_export_selection_writes_selected_text():
    """export_selection пишет выделенный фрагмент, а не весь текст."""
    from src.gui.mixins.export_tools import ExportToolsMixin

    class Host(FakeHost, ExportToolsMixin):
        pass

    import src.gui.mixins.export_tools as et
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "sel.md")
        et.QFileDialog = types.SimpleNamespace(
            getSaveFileName=lambda *a, **k: (out, "")
        )
        host = Host(text="весь текст", selected="только выделенное")
        host.export_selection()
        with open(out, encoding="utf-8") as f:
            assert f.read() == "только выделенное"
    print("[PASS] test_export_selection_writes_selected_text")


def test_export_selection_empty_shows_no_file():
    """Без выделения файл не создаётся, показывается предупреждение."""
    from src.gui.mixins.export_tools import ExportToolsMixin

    class Host(FakeHost, ExportToolsMixin):
        pass

    import src.gui.mixins.export_tools as et
    called = {"save": False}

    def _save(*a, **k):
        called["save"] = True
        return ("x.md", "")

    et.QFileDialog = types.SimpleNamespace(getSaveFileName=_save)
    host = Host(text="текст", selected="")
    host.export_selection()
    assert called["save"] is False, "диалог не должен вызываться без выделения"
    print("[PASS] test_export_selection_empty_shows_no_file")


# ─── workspace ───────────────────────────────────────────────────────────────

def test_apply_template_vars_replaces_placeholders():
    """apply_template_vars заменяет {{date}} и берёт title из первого H1."""
    from src.gui.mixins.workspace import WorkspaceMixin

    class Host(FakeHost, WorkspaceMixin):
        pass

    host = Host(text="# Отчёт\n\nДокумент: {{title}}\nДата: {{date}}\n")
    host.apply_template_vars()
    new_text = host.live_editor.toPlainText()
    assert "{{title}}" not in new_text and "{{date}}" not in new_text
    # title подставляется из первого H1, который остаётся в тексте
    assert "Отчёт" in new_text, f"title не подставлен: {new_text!r}"
    assert host.toasts, "ожидали toast об успехе"
    print("[PASS] test_apply_template_vars_replaces_placeholders")


# ─── education ───────────────────────────────────────────────────────────────

def test_save_anki_tsv_writes_file():
    """_save_anki_tsv пишет карточки (список dict) в TSV-файл."""
    from src.gui.mixins.education import EducationMixin

    class Host(FakeHost, EducationMixin):
        pass

    import src.gui.mixins.education as ed
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "cards.tsv")
        ed.QFileDialog = types.SimpleNamespace(
            getSaveFileName=lambda *a, **k: (out, "")
        )
        host = Host()
        cards = [{"front": "Что такое Python?", "back": "Язык программирования"}]
        host._save_anki_tsv(cards)
        assert os.path.isfile(out), "TSV не создан"
        with open(out, encoding="utf-8") as f:
            content = f.read()
        assert "Python" in content and "\t" in content
        assert host.toasts, "ожидали toast о сохранении"
    print("[PASS] test_save_anki_tsv_writes_file")


# ─── editor_formatting (чистая логика) ───────────────────────────────────────

def test_run_linter_on_live_editor_text():
    """run_linter обрабатывает текст редактора и не падает."""
    from src.gui.mixins.editor_formatting import EditorFormattingMixin

    class Host(FakeHost, EditorFormattingMixin):
        pass

    # show_document_audit требует полного состояния окна — подменяем на no-op,
    # чтобы проверить именно линтер-ветку run_linter.
    import src.gui.document_tools as dt
    original = getattr(dt, "show_document_audit", None)
    dt.show_document_audit = lambda host: None
    try:
        host = Host(text="# Заголовок\n\n\n\nтекст   с пробелами")
        host.run_linter()
    except Exception as e:
        raise AssertionError(f"run_linter упал: {e}")
    finally:
        if original is not None:
            dt.show_document_audit = original
    print("[PASS] test_run_linter_on_live_editor_text")


def test_mixins_have_no_state_collision():
    """Миксины не переопределяют друг друга (нет дублирующих имён в MRO)."""
    E, V, F, W, Ed = _mixins()
    owners = {}
    dupes = []
    for cls in (E, V, F, W, Ed):
        for name in vars(cls):
            if name.startswith("__"):
                continue
            if name in owners:
                dupes.append(f"{name} ({owners[name]} + {cls.__name__})")
            owners[name] = cls.__name__
    assert not dupes, f"дублирующиеся методы между миксинами: {dupes}"
    print("[PASS] test_mixins_have_no_state_collision")


def main():
    tests = [
        test_mixins_have_no_state_collision,
        test_export_as_markdown_writes_file,
        test_export_as_markdown_cancel_no_write,
        test_export_selection_writes_selected_text,
        test_export_selection_empty_shows_no_file,
        test_apply_template_vars_replaces_placeholders,
        test_save_anki_tsv_writes_file,
        test_run_linter_on_live_editor_text,
    ]
    for t in tests:
        t()
    print("\nAll GUI mixin behavior tests passed!")


if __name__ == "__main__":
    main()
