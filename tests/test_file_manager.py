"""Поведенческие тесты file_manager (gui/file_manager).

Проверяет добавление в недавние файлы, открытие из недавних, фильтр
проводника, сохранение текущего файла в рабочем пространстве.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Тест работает и без установленного PyQt6: подставляем минимальный стаб.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _install_qt_stub():
    try:
        import PyQt6  # noqa: F401
        return False
    except ImportError:
        pass

    import types

    class _Anything:
        def __init__(self, *a, **k):
            pass

        def __getattr__(self, item):
            return _Anything()

        def __call__(self, *a, **k):
            return _Anything()

    class _Base:
        def __init__(self, *a, **k):
            pass

        def __getattr__(self, item):
            return _Anything()

    for mod_name in ("PyQt6", "PyQt6.QtWidgets", "PyQt6.QtCore", "PyQt6.QtGui"):
        mod = types.ModuleType(mod_name)
        mod.__getattr__ = lambda name, _m=mod: type(name, (_Base,), {})
        sys.modules[mod_name] = mod

    core = sys.modules["PyQt6.QtCore"]
    core.Qt = _Anything()

    widgets = sys.modules["PyQt6.QtWidgets"]

    def _noop(*a, **k):
        return None

    widgets.QMessageBox = type("QMessageBox", (_Base,), {
        "information": staticmethod(_noop),
        "warning": staticmethod(_noop),
        "critical": staticmethod(_noop),
    })
    return True


STUB_ACTIVE = _install_qt_stub()

import src.gui.file_manager as fm  # noqa: E402


class _FakeAction:
    def __init__(self, text=""):
        self.text = text
        self.enabled = True
        self._data = None
        self._cb = None

    def setEnabled(self, v):
        self.enabled = v

    def setData(self, d):
        self._data = d

    def trigger(self, checked=False):
        if self._cb:
            self._cb(checked)

    @property
    def triggered(self):
        action = self

        class _Sig:
            def connect(self, cb):
                action._cb = cb

        return _Sig()


class _FakeMenu:
    def __init__(self):
        self.actions = []

    def clear(self):
        self.actions = []

    def addAction(self, text):
        a = _FakeAction(text)
        self.actions.append(a)
        return a


class _FakeSettings:
    def __init__(self, recent=None):
        self._d = {}
        self._recent = list(recent or [])

    def value(self, key, default=None, type=None):
        if key == "recent_files":
            return list(self._recent)
        return self._d.get(key, default)

    def setValue(self, key, val):
        if key == "recent_files":
            self._recent = list(val)
        else:
            self._d[key] = val


class _FakeListItem:
    def __init__(self, text, data=None):
        self._text = text
        self.data = data
        self.hidden = False
        self.selected = False

    def text(self):
        return self._text

    def setData(self, role, d):
        self.data = d

    def data(self, role):
        return self.data

    def setHidden(self, v):
        self.hidden = v

    def setSelected(self, v):
        self.selected = v


class _FakeList:
    def __init__(self):
        self.items = []
        self.signals_blocked = False

    def blockSignals(self, v):
        self.signals_blocked = v

    def clear(self):
        self.items = []

    def addItem(self, item):
        self.items.append(item)

    def count(self):
        return len(self.items)

    def item(self, row):
        return self.items[row]

    def setCurrentItem(self, item):
        pass


class _FakeEditor:
    def __init__(self):
        self.text = ""
        self.blocked = False

    def blockSignals(self, v):
        self.blocked = v

    def toPlainText(self):
        return self.text

    def setPlainText(self, t):
        self.text = t


class _FakeGroup:
    def __init__(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def show(self):
        self.visible = True


class _FakeLabel:
    def __init__(self):
        self.text = ""

    def setText(self, t):
        self.text = t


class _FakeButton:
    def __init__(self):
        self.enabled = True

    def setEnabled(self, v):
        self.enabled = v


class _FakeLog:
    def clear(self):
        pass


class _FakeProgress:
    def __init__(self):
        self.value = 0

    def setValue(self, v):
        self.value = v


class FakeHost:
    def __init__(self, tmpdir):
        self.tmpdir = tmpdir
        self.settings = _FakeSettings()
        self.recent_menu = _FakeMenu()
        self.MAX_RECENT = 5
        self.explorer_list = _FakeList()
        self.explorer_group = _FakeGroup()
        self.live_editor = _FakeEditor()
        self.file_label = _FakeLabel()
        self.btn_convert = _FakeButton()
        self.log_output = _FakeLog()
        self.progress_bar = _FakeProgress()
        self.logs = []
        self.previews = []
        self.messages = []
        self.active_workspace_folder = None
        self.current_workspace_file = None
        self.selected_files = []
        self.is_welcome_doc_active = True
        self.last_output_dir = None

    def update_preview(self, path):
        self.previews.append(path)

    def tr_msg(self, key, *args):
        if key == "menu_empty":
            return "(пусто)"
        if key == "msg_file_not_found":
            return "Файл не найден"
        if key == "msg_file_moved":
            return "Файл мог быть перемещён: %s"
        if key == "log_opened_recent":
            return "Открыт из недавних: %s"
        if args:
            return key + str(args)
        return key

    def append_log(self, msg):
        self.logs.append(msg)

    def _render_live_preview(self):
        self.previews.append("render")

    def update_text_statistics(self):
        self.previews.append("stats")


def test_add_to_recent_dedupes_and_caps():
    """add_to_recent перемещает дубли вперёд и ограничивает длину MAX_RECENT."""
    h = FakeHost("")
    p1 = os.path.join(h.tmpdir, "a.md")
    p2 = os.path.join(h.tmpdir, "b.md")
    p3 = os.path.join(h.tmpdir, "c.md")
    fm.add_to_recent(h, p1)
    fm.add_to_recent(h, p2)
    fm.add_to_recent(h, p3)
    fm.add_to_recent(h, p1)  # дубликат — должен оказаться первым
    recent = h.settings.value("recent_files")
    assert recent[0] == p1
    assert recent.count(p1) == 1
    # cap
    for i in range(10):
        fm.add_to_recent(h, os.path.join(h.tmpdir, f"x{i}.md"))
    assert len(h.settings.value("recent_files")) == 5
    print("[PASS] test_add_to_recent_dedupes_and_caps")


def test_update_recent_menu_empty():
    """Пустой список недавних добавляет неактивный пункт."""
    h = FakeHost("")
    fm.update_recent_menu(h)
    assert len(h.recent_menu.actions) == 1
    assert h.recent_menu.actions[0].enabled is False
    print("[PASS] test_update_recent_menu_empty")


def test_update_recent_menu_builds_actions():
    """Меню недавних заполняется действиями с basename файла."""
    with tempfile.TemporaryDirectory() as d:
        h = FakeHost(d)
        p = os.path.join(d, "note.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write("hello")
        fm.add_to_recent(h, p)
        fm.update_recent_menu(h)
        assert len(h.recent_menu.actions) == 1
        assert h.recent_menu.actions[0].text == "note.md"
    print("[PASS] test_update_recent_menu_builds_actions")


def test_open_recent_loads_file():
    """open_recent выбирает файл, обновляет метку и вызывает update_preview."""
    with tempfile.TemporaryDirectory() as d:
        h = FakeHost(d)
        p = os.path.join(d, "note.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write("hello")
        fm.open_recent(h, p)
        assert h.selected_files == [p]
        assert h.active_workspace_folder is None
        assert h.file_label.text == "note.md"
        assert h.btn_convert.enabled is True
        assert h.explorer_group.visible is False
        assert h.previews == [p]
        assert h.logs, "должен быть записан лог"
    print("[PASS] test_open_recent_loads_file")


def test_open_recent_missing_file_warns():
    """Открытие отсутствующего файла показывает предупреждение."""
    h = FakeHost("")
    warnings = []
    orig = fm.QMessageBox
    fm.QMessageBox = type("QMessageBox", (), {"warning": staticmethod(lambda *a, **k: warnings.append(a))})
    try:
        fm.open_recent(h, "C:/no/such/file.md")
    finally:
        fm.QMessageBox = orig
    assert len(warnings) == 1
    print("[PASS] test_open_recent_missing_file_warns")


def test_filter_workspace_explorer():
    """Фильтр скрывает/показывает элементы по подстроке."""
    h = FakeHost("")
    h.explorer_list.items = [
        _FakeListItem("README.md"),
        _FakeListItem("notes.md"),
        _FakeListItem("todo.txt"),
    ]
    fm.filter_workspace_explorer(h, "note")
    # "README.md" не содержит "note" → скрыт
    assert h.explorer_list.items[0].hidden is True
    # "notes.md" содержит "note" → виден
    assert h.explorer_list.items[1].hidden is False
    # "todo.txt" не содержит "note" → скрыт
    assert h.explorer_list.items[2].hidden is True
    fm.filter_workspace_explorer(h, "")
    assert all(not i.hidden for i in h.explorer_list.items)
    print("[PASS] test_filter_workspace_explorer")


def test_save_current_workspace_file_writes_and_calls_revision():
    """save_current_workspace_file записывает содержимое и вызывает save_revision."""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "doc.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write("old")
        h = FakeHost(d)
        h.current_workspace_file = p
        h.live_editor.text = "новое содержимое"
        revisions = []
        import src.gui.document_tools as dt

        orig = dt.save_revision
        try:
            dt.save_revision = lambda w: revisions.append(w)
            fm.save_current_workspace_file(h)
        finally:
            dt.save_revision = orig
        assert open(p, encoding="utf-8").read() == "новое содержимое"
        assert len(revisions) == 1
    print("[PASS] test_save_current_workspace_file_writes_and_calls_revision")


def test_save_current_workspace_file_noop_without_file():
    """Без текущего файла сохранение ничего не делает."""
    h = FakeHost("")
    h.live_editor.text = "x"
    h.current_workspace_file = None
    fm.save_current_workspace_file(h)
    print("[PASS] test_save_current_workspace_file_noop_without_file")


def main():
    tests = [
        test_add_to_recent_dedupes_and_caps,
        test_update_recent_menu_empty,
        test_update_recent_menu_builds_actions,
        test_open_recent_loads_file,
        test_open_recent_missing_file_warns,
        test_filter_workspace_explorer,
        test_save_current_workspace_file_writes_and_calls_revision,
        test_save_current_workspace_file_noop_without_file,
    ]
    for t in tests:
        t()
    print("\nAll file_manager tests passed!")


if __name__ == "__main__":
    main()
