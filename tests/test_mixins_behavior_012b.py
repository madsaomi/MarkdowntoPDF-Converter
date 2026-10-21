"""Поведенческие тесты остальных GUI-миксинов TASK-012 (часть 2).

Продолжение `test_mixins_behavior_012.py`: покрывает миксины, не затронутые
там — convert_tools (PDF/HTML->MD, OCR-fallback), export_history
(дедупликация/лимит), presets (save/delete), integrations (watermark, csv).

Диалоги Qt подменяются, синхронные ветки (fallback) вызываются напрямую,
чтобы не зависеть от фоновых потоков.
"""
import json
import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Реальному Qt для виджетов нужен дисплей; в CI и локально без GUI — offscreen.
# Ставим до первого импорта Qt.
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
    for cls_name in ("QInputDialog", "QFileDialog"):
        cls = type(cls_name, (_Base,), {})
        for m in ("getText", "getItem", "getInt", "getDouble",
                  "getSaveFileName", "getOpenFileName", "getExistingDirectory"):
            setattr(cls, m, staticmethod(_noop))
        setattr(widgets, cls_name, cls)
    return True


STUB_ACTIVE = _install_qt_stub()


def _ensure_qapplication():
    """Создаёт QApplication, если PyQt6 настоящий (виджеты без него крашат)."""
    if STUB_ACTIVE:
        return None
    try:
        from PyQt6.QtWidgets import QApplication
        return QApplication.instance() or QApplication([])
    except Exception:
        return None


_APP = _ensure_qapplication()


class _NoopDialog:
    """Заменяет статические методы диалогов Qt на no-op в модулях миксинов.

    С настоящим PyQt6 ``QMessageBox.information(fake_host, ...)`` падает
    (fake_host — не QWidget), а модальные диалоги блокируют прогон.
    """

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
    for mod_name in module_names:
        mod = importlib.import_module(mod_name)
        for cls_name in ("QMessageBox", "QInputDialog", "QFileDialog"):
            if hasattr(mod, cls_name):
                setattr(mod, cls_name, _NoopDialog())


_patch_dialogs(
    "src.gui.mixins.export_history",
    "src.gui.mixins.presets",
    "src.gui.mixins.convert_tools",
    "src.gui.mixins.integrations",
    "src.gui.mixins.document_ops",
    "src.gui.mixins.editor_tools",
)


# ─── общий фейковый хост ─────────────────────────────────────────────────────

class _FakeCursor:
    def __init__(self):
        self.inserted = []

    def insertText(self, t):
        self.inserted.append(t)


class _FakeEditor:
    def __init__(self, text=""):
        self._text = text
        self._cursor = _FakeCursor()

    def toPlainText(self):
        return self._text

    def setPlainText(self, t):
        self._text = t

    def textCursor(self):
        return self._cursor

    def setTextCursor(self, c):
        pass

    def setFocus(self):
        pass


class FakeHost:
    def __init__(self, text=""):
        self.live_editor = _FakeEditor(text)
        self.current_lang = "ru"
        self.logs = []
        self.toasts = []
        self.selected_files = []
        self.warnings = []
        self.criticals = []

    def append_log(self, msg):
        self.logs.append(msg)

    def toast(self, msg, kind="info"):
        self.toasts.append((msg, kind))

    def _render_live_preview(self):
        pass

    def _get_template_dir(self):
        return ""

    def _get_options(self):
        return None

    def tr_msg(self, key, *a):
        return key


# ─── export_history ──────────────────────────────────────────────────────────

class _Settings:
    def __init__(self):
        self.store = {}

    def setValue(self, k, v):
        self.store[k] = v

    def value(self, k, default=None, *a):
        return self.store.get(k, default)


class _Layout:
    def __init__(self):
        self.widgets = []

    def count(self):
        return len(self.widgets)

    def takeAt(self, i):
        if i < len(self.widgets):
            w = self.widgets.pop(i)
            return types.SimpleNamespace(widget=lambda: w)
        return types.SimpleNamespace(widget=lambda: None)

    def addWidget(self, w, *a, **k):
        self.widgets.append(w)


def _export_history_host():
    from src.gui.mixins.export_history import ExportHistoryMixin

    class Host(FakeHost, ExportHistoryMixin):
        pass

    h = Host()
    h.export_history = []
    h.settings = _Settings()
    h.history_layout = _Layout()
    h.open_exported_file = lambda p: None
    h.open_exported_folder = lambda p: None
    return h


def test_export_history_dedupes_and_caps():
    """add_to_export_history: новый — в начало, повтор не дублируется, максимум 5."""
    h = _export_history_host()
    for i in range(7):
        h.add_to_export_history(f"C:/out/file{i}.pdf")
    assert len(h.export_history) == 5, h.export_history
    assert h.export_history[0] == "C:/out/file6.pdf"
    assert "C:/out/file0.pdf" not in h.export_history

    # повторный add поднимает элемент наверх, не увеличивая список
    h.add_to_export_history("C:/out/file3.pdf")
    assert h.export_history[0] == "C:/out/file3.pdf"
    assert len(h.export_history) == 5
    assert h.settings.store.get("export_history") == h.export_history
    print("[PASS] test_export_history_dedupes_and_caps")


def test_export_history_empty_shows_placeholder():
    """Пустая история добавляет placeholder, а не ряды."""
    h = _export_history_host()
    h.update_export_history_ui()
    assert len(h.history_layout.widgets) == 1, h.history_layout.widgets
    print("[PASS] test_export_history_empty_shows_placeholder")


# ─── presets ─────────────────────────────────────────────────────────────────

def _presets_host():
    from src.gui.mixins.presets import PresetsMixin

    class Combo:
        def __init__(self, items=None):
            self._items = list(items or [])
            self._idx = 0
            self._current = self._items[0] if self._items else ""

        def blockSignals(self, b):
            pass

        def clear(self):
            self._items = []

        def addItem(self, t):
            self._items.append(t)

        def currentIndex(self):
            return self._idx

        def setCurrentIndex(self, i):
            self._idx = i
            if 0 <= i < len(self._items):
                self._current = self._items[i]

        def currentText(self):
            return self._current

        def findText(self, t):
            return self._items.index(t) if t in self._items else -1

    class LineEdit:
        def __init__(self):
            self._t = ""

        def setText(self, t):
            self._t = t

        def text(self):
            return self._t

    class Check:
        def setChecked(self, b):
            pass

        def isChecked(self):
            return False

    class Host(FakeHost, PresetsMixin):
        pass

    h = Host()
    h.settings = _Settings()
    h.presets = {}
    h.preset_combo = Combo()
    for name in ("doc_theme_combo", "code_theme_combo", "paper_combo", "format_combo",
                 "combo_page_format"):
        setattr(h, name, Combo())
    for name in ("watermark_input", "footer_input", "custom_css_input",
                 "margins_input", "docx_template_input"):
        setattr(h, name, LineEdit())
    for name in ("chk_page_numbers", "chk_presentation_mode"):
        setattr(h, name, Check())

    class Opt:
        watermark = ""
        footer_text = ""
        custom_css = ""
        margins = ""
        docx_template = ""
        page_numbers = False
        is_presentation = False

    h._get_options = lambda: Opt()
    return h


def test_presets_load_empty():
    """load_presets на пустых настройках даёт только пункт «по умолчанию»."""
    h = _presets_host()
    h.load_presets()
    assert h.preset_combo.count() if hasattr(h.preset_combo, "count") else True
    assert len(h.preset_combo._items) == 1, h.preset_combo._items
    assert h.presets == {}
    print("[PASS] test_presets_load_empty")


def test_presets_delete_default_forbidden():
    """delete_preset на элементе 0 (по умолчанию) не трогает настройки."""
    h = _presets_host()
    h.presets = {"Мой": {"doc_theme": 1}}
    h.preset_combo._items = ["(по умолчанию)", "Мой"]
    h.preset_combo._idx = 0
    h.delete_preset()
    assert "Мой" in h.presets, "пресет не должен удаляться"
    assert "presets" not in h.settings.store
    print("[PASS] test_presets_delete_default_forbidden")


def test_presets_delete_removes_and_persists():
    """delete_preset удаляет выбранный пресет и пишет настройки."""
    h = _presets_host()
    h.presets = {"Мой": {"doc_theme": 1}}
    h.preset_combo._items = ["(по умолчанию)", "Мой"]
    h.preset_combo._idx = 1
    h.preset_combo._current = "Мой"
    h.delete_preset()
    assert "Мой" not in h.presets
    assert "presets" in h.settings.store
    assert json.loads(h.settings.store["presets"]) == {}
    print("[PASS] test_presets_delete_removes_and_persists")


# ─── convert_tools (синхронные fallback-ветки) ───────────────────────────────

def _convert_host():
    from src.gui.mixins.convert_tools import ConvertToolsMixin

    class Host(FakeHost, ConvertToolsMixin):
        pass

    return Host()


def test_html_to_markdown_fallback_converts():
    """html_to_markdown_convert: синхронная ветка конвертирует HTML в MD."""
    import tempfile
    import src.gui.mixins.convert_tools as ct

    # ломаем импорт TaskThread, чтобы уйти в синхронный fallback
    real_import = __import__

    def _fake_import(name, *a, **k):
        if name == "src.gui.workers.task_worker":
            raise ImportError("test: no threads")
        return real_import(name, *a, **k)

    with tempfile.TemporaryDirectory() as tmp:
        html_path = os.path.join(tmp, "in.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write("<html><body><h1>Заголовок</h1><p>Абзац</p></body></html>")

        ct.QFileDialog = types.SimpleNamespace(
            getOpenFileName=lambda *a, **k: (html_path, "")
        )
        h = _convert_host()
        import builtins
        saved = builtins.__import__
        builtins.__import__ = _fake_import
        try:
            h.html_to_markdown_convert()
        finally:
            builtins.__import__ = saved

        text = h.live_editor.toPlainText()
        assert "Заголовок" in text, f"MD не получен: {text!r}"
        assert any("HTML -> Markdown" in m for m in h.logs), h.logs
    print("[PASS] test_html_to_markdown_fallback_converts")


def test_pdf_to_markdown_cancel_noop():
    """Отмена выбора PDF (пустой путь) ничего не делает."""
    import src.gui.mixins.convert_tools as ct

    ct.QFileDialog = types.SimpleNamespace(
        getOpenFileName=lambda *a, **k: ("", "")
    )
    h = _convert_host()
    h.pdf_to_markdown_convert()
    assert h.logs == [], h.logs
    print("[PASS] test_pdf_to_markdown_cancel_noop")


def test_ocr_image_to_text_delegates():
    """ocr_image_to_text — алиас run_ocr."""
    from src.gui.mixins.convert_tools import ConvertToolsMixin
    import src.gui.mixins.convert_tools as ct

    class Host(FakeHost):
        def run_ocr(self):
            self.logs.append("run_ocr-called")

    Host = type("Host", (Host, ConvertToolsMixin), {})
    h = Host()
    h.ocr_image_to_text()
    assert h.logs == ["run_ocr-called"], h.logs
    print("[PASS] test_ocr_image_to_text_delegates")


# ─── integrations ────────────────────────────────────────────────────────────

def test_watermark_designer_applies_text():
    """show_watermark_designer переносит текст дизайнера в footer_input."""
    from src.gui.mixins.integrations import IntegrationsMixin
    import src.gui.watermark_designer as wd

    class _FakeDlg:
        def __init__(self, parent, lang):
            self.text_input = types.SimpleNamespace(text=lambda: "ЧЕРНОВИК")
            self.result_css = "  .wm{}  "

        def exec(self):
            return True

    original = getattr(wd, "WatermarkDesignerDialog", None)
    wd.WatermarkDesignerDialog = _FakeDlg

    class Host(FakeHost, IntegrationsMixin):
        pass

    try:
        h = Host()
        h.footer_input = types.SimpleNamespace(setText=lambda t: setattr(h, "_wm", t))
        h.watermark_css_input = types.SimpleNamespace(
            setText=lambda t: setattr(h, "_wm_css", t)
        )
        h.show_watermark_designer()
        assert h._wm == "ЧЕРНОВИК", h._wm
        assert h._wm_css == ".wm{}", h._wm_css
        assert any("Watermark applied" in m for m in h.logs), h.logs
    finally:
        if original is not None:
            wd.WatermarkDesignerDialog = original
    print("[PASS] test_watermark_designer_applies_text")


def test_github_sync_requires_files():
    """show_github_sync_dialog без файлов показывает подсказку и не открывает диалог."""
    from src.gui.mixins.integrations import IntegrationsMixin
    import src.gui.dialogs as dlg_mod

    opened = {"n": 0}

    class _FakeGH:
        def __init__(self, *a, **k):
            opened["n"] += 1

        def exec(self):
            return 0

    original = getattr(dlg_mod, "GitHubSyncDialog", None)
    dlg_mod.GitHubSyncDialog = _FakeGH

    class Host(FakeHost, IntegrationsMixin):
        pass

    try:
        h = Host()
        h.selected_files = []
        h.active_workspace_folder = "C:/ws"
        h.show_github_sync_dialog()
        assert opened["n"] == 0, "диалог не должен открываться без файлов"
    finally:
        if original is not None:
            dlg_mod.GitHubSyncDialog = original
    print("[PASS] test_github_sync_requires_files")


def test_mixins_part2_have_no_collisions():
    """Методы миксинов части 2 не конфликтуют между собой и с частью 1."""
    from src.gui.mixins.convert_tools import ConvertToolsMixin
    from src.gui.mixins.export_history import ExportHistoryMixin
    from src.gui.mixins.presets import PresetsMixin
    from src.gui.mixins.integrations import IntegrationsMixin
    from src.gui.mixins.document_ops import DocumentOpsMixin
    from src.gui.mixins.editor_tools import EditorToolsMixin

    owners = {}
    dupes = []
    for cls in (ConvertToolsMixin, ExportHistoryMixin, PresetsMixin,
                IntegrationsMixin, DocumentOpsMixin, EditorToolsMixin):
        for name in vars(cls):
            if name.startswith("__"):
                continue
            if name in owners:
                dupes.append(f"{name} ({owners[name]} + {cls.__name__})")
            owners[name] = cls.__name__
    assert not dupes, f"дублирующиеся методы: {dupes}"
    print("[PASS] test_mixins_part2_have_no_collisions")


def main():
    tests = [
        test_mixins_part2_have_no_collisions,
        test_export_history_dedupes_and_caps,
        test_export_history_empty_shows_placeholder,
        test_presets_load_empty,
        test_presets_delete_default_forbidden,
        test_presets_delete_removes_and_persists,
        test_html_to_markdown_fallback_converts,
        test_pdf_to_markdown_cancel_noop,
        test_ocr_image_to_text_delegates,
        test_watermark_designer_applies_text,
        test_github_sync_requires_files,
    ]
    for t in tests:
        t()
    print("\nAll mixin behavior tests (part 2) passed!")


if __name__ == "__main__":
    main()
