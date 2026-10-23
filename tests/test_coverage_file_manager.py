"""Поведенческие тесты gui/file_manager.py.

Модуль целиком построен на «окне» (главное окно приложения), поэтому тесты
подставляют фейковый хост с настоящими Qt-виджетами там, где это важно
(`QListWidget`, `QPlainTextEdit`, `QMenu`), и счётчиками вместо остального.
"""
import os
import shutil
import sys
import tempfile
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QListWidget, QListWidgetItem, QMenu, QPlainTextEdit,
)

app = QApplication.instance() or QApplication([])

from src.gui import file_manager


# ─── Фейковый хост ──────────────────────────────────────────────────────────

class _FakeSettings:
    def __init__(self, data=None):
        self.data = dict(data or {})

    def value(self, key, default=None, type=None):
        if key not in self.data:
            return default
        value = self.data[key]
        if type is list:
            return list(value)
        return value

    def setValue(self, key, value):
        self.data[key] = value


class _FakeGroup:
    def __init__(self):
        self.hidden = 0
        self.shown = 0

    def hide(self):
        self.hidden += 1

    def show(self):
        self.shown += 1


class _FakeLabel:
    def __init__(self):
        self.texts = []

    def setText(self, text):
        self.texts.append(text)

    @property
    def text(self):
        return self.texts[-1] if self.texts else ""


class _FakeButton:
    def __init__(self, enabled=False):
        self.enabled = enabled

    def setEnabled(self, value):
        self.enabled = value


class _FakeValue:
    def __init__(self):
        self.values = []

    def setValue(self, value):
        self.values.append(value)


class _FakeLog:
    def __init__(self):
        self.clears = 0

    def clear(self):
        self.clears += 1


class _FakeWindow:
    MAX_RECENT = 5

    def __init__(self, with_watch=True):
        self.settings = _FakeSettings()
        self.recent_menu = QMenu()
        self.explorer_list = QListWidget()
        self.explorer_group = _FakeGroup()
        self.live_editor = QPlainTextEdit()
        self.file_label = _FakeLabel()
        self.btn_convert = _FakeButton(False)
        if with_watch:
            self.btn_watch = _FakeButton(True)
        self.custom_css_input = _FakeLabel()
        self.docx_template_input = _FakeLabel()
        self.log_output = _FakeLog()
        self.progress_bar = _FakeValue()
        self.logs = []
        self.previews = []
        self.msg_keys = []
        self.last_output_dir = ""
        self.selected_files = []
        self.active_workspace_folder = None
        self.current_workspace_file = None
        self.is_welcome_doc_active = True
        self.render_calls = 0
        self.stats_calls = 0

    def tr_msg(self, key, *args):
        self.msg_keys.append(key)
        return key if not args else key + ":" + "|".join(str(a) for a in args)

    def append_log(self, msg):
        self.logs.append(msg)

    def update_preview(self, path):
        self.previews.append(path)

    def _render_live_preview(self):
        self.render_calls += 1

    def update_text_statistics(self):
        self.stats_calls += 1


class _FakeFileDialog:
    open_file = ""
    open_files = ([], "")
    directory = ""
    calls = []

    @classmethod
    def getOpenFileName(cls, *args, **kwargs):
        cls.calls.append("open_file")
        return cls.open_file, ""

    @classmethod
    def getOpenFileNames(cls, *args, **kwargs):
        cls.calls.append("open_files")
        return cls.open_files

    @classmethod
    def getExistingDirectory(cls, *args, **kwargs):
        cls.calls.append("directory")
        return cls.directory


class _FakeMessageBox:
    warnings = []

    @classmethod
    def warning(cls, parent, title, text, *args, **kwargs):
        cls.warnings.append((title, text))


class _FakeLogger:
    def __init__(self):
        self.errors = []

    def error(self, fmt, *args):
        self.errors.append(fmt % args if args else fmt)


def _patch_all(open_file="", open_files=([], ""), directory=""):
    _FakeFileDialog.open_file = open_file
    _FakeFileDialog.open_files = open_files
    _FakeFileDialog.directory = directory
    _FakeFileDialog.calls = []
    _FakeMessageBox.warnings = []
    file_manager.QFileDialog = _FakeFileDialog
    file_manager.QMessageBox = _FakeMessageBox


def _restore():
    import PyQt6.QtWidgets as qtw
    file_manager.QFileDialog = qtw.QFileDialog
    file_manager.QMessageBox = qtw.QMessageBox
    _FakeMessageBox.warnings = []


def _md_files(folder, names, content="# x\n"):
    paths = []
    for name in names:
        path = os.path.join(folder, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        paths.append(path)
    return paths


# ─── Выбор одного файла (CSS / DOCX) ────────────────────────────────────────

def test_select_custom_css():
    """Выбранный CSS подставляется в поле, отмена — нет."""
    try:
        _patch_all(open_file="c:/styles/dark.css")
        w = _FakeWindow()
        file_manager.select_custom_css(w)
        assert w.custom_css_input.text == "c:/styles/dark.css"

        _FakeFileDialog.open_file = ""
        w2 = _FakeWindow()
        file_manager.select_custom_css(w2)
        assert w2.custom_css_input.text == ""
        assert _FakeFileDialog.calls == ["open_file", "open_file"]
    finally:
        _restore()
    print("[PASS] test_select_custom_css")


def test_select_docx_template():
    """Выбранный шаблон DOCX подставляется в поле."""
    try:
        _patch_all(open_file="c:/templates/letter.docx")
        w = _FakeWindow()
        file_manager.select_docx_template(w)
        assert w.docx_template_input.text == "c:/templates/letter.docx"
    finally:
        _restore()
    print("[PASS] test_select_docx_template")


# ─── Выбор нескольких файлов ────────────────────────────────────────────────

def test_select_files_populates_window():
    """Выбор файлов: список, история, подпись, лог и превью первого файла."""
    tmpdir = tempfile.mkdtemp()
    try:
        files = _md_files(tmpdir, ["a.md", "b.md"])
        _patch_all(open_files=(files, ""))
        w = _FakeWindow()
        w.active_workspace_folder = tmpdir
        file_manager.select_files(w)

        assert w.selected_files == files
        assert w.active_workspace_folder is None
        assert w.explorer_group.hidden == 1
        assert w.settings.data["recent_files"] == [files[1], files[0]]
        assert w.file_label.text == "files_selected:2|a.md, b.md"
        assert w.btn_convert.enabled is True
        assert w.btn_watch.enabled is False  # два файла — слежение недоступно
        assert w.log_output.clears == 1
        assert w.progress_bar.values == [0]
        assert w.logs == ["log_selected:2"]
        assert w.previews == [files[0]]
    finally:
        _restore()
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_select_files_populates_window")


def test_select_files_single_enables_watch():
    """Один файл включает кнопку слежения за изменениями."""
    tmpdir = tempfile.mkdtemp()
    try:
        files = _md_files(tmpdir, ["one.md"])
        _patch_all(open_files=(files, ""))
        w = _FakeWindow()
        file_manager.select_files(w)
        assert w.btn_watch.enabled is True
    finally:
        _restore()
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_select_files_single_enables_watch")


def test_select_files_without_watch_button():
    """Окно без кнопки слежения не ломает выбор файлов."""
    tmpdir = tempfile.mkdtemp()
    try:
        files = _md_files(tmpdir, ["one.md"])
        _patch_all(open_files=(files, ""))
        w = _FakeWindow(with_watch=False)
        file_manager.select_files(w)
        assert w.selected_files == files
        assert not hasattr(w, "btn_watch")
    finally:
        _restore()
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_select_files_without_watch_button")


def test_select_files_cancelled():
    """Отмена выбора файлов ничего не меняет."""
    try:
        _patch_all(open_files=([], ""))
        w = _FakeWindow()
        w.selected_files = ["keep.md"]
        file_manager.select_files(w)
        assert w.selected_files == ["keep.md"]
        assert w.logs == []
        assert w.previews == []
    finally:
        _restore()
    print("[PASS] test_select_files_cancelled")


# ─── Выбор папки ────────────────────────────────────────────────────────────

def test_select_folder_loads_markdown():
    """Папка: только .md, рабочая папка выставлена, explorer показан."""
    tmpdir = tempfile.mkdtemp()
    try:
        _md_files(tmpdir, ["b.md", "a.md"])
        with open(os.path.join(tmpdir, "notes.txt"), "w", encoding="utf-8") as f:
            f.write("no")
        _patch_all(directory=tmpdir)
        w = _FakeWindow()
        file_manager.select_folder(w)

        assert len(w.selected_files) == 2
        assert all(p.endswith(".md") for p in w.selected_files)
        assert w.active_workspace_folder == tmpdir
        assert w.file_label.text.startswith("folder_selected:")
        assert w.btn_convert.enabled is True
        assert w.btn_watch.enabled is False
        assert w.explorer_group.shown == 1
        assert w.explorer_list.count() == 2
        # update_workspace_explorer сортирует по имени без учёта регистра
        assert [w.explorer_list.item(i).text() for i in range(2)] == ["a.md", "b.md"]
        assert w.previews == [w.selected_files[0]]
        assert w.is_welcome_doc_active is False
    finally:
        _restore()
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_select_folder_loads_markdown")


def test_select_folder_empty_warns():
    """Пустая папка: предупреждение, состояние не меняется."""
    tmpdir = tempfile.mkdtemp()
    try:
        with open(os.path.join(tmpdir, "readme.txt"), "w", encoding="utf-8") as f:
            f.write("no")
        _patch_all(directory=tmpdir)
        w = _FakeWindow()
        file_manager.select_folder(w)
        assert w.selected_files == []
        assert w.active_workspace_folder is None
        assert w.explorer_group.shown == 0
        assert len(_FakeMessageBox.warnings) == 1
        title, text = _FakeMessageBox.warnings[0]
        assert title == "msg_folder_empty_title"
        assert text == "msg_folder_empty"
    finally:
        _restore()
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_select_folder_empty_warns")


def test_select_folder_cancelled():
    """Отмена выбора папки ничего не делает."""
    try:
        _patch_all(directory="")
        w = _FakeWindow()
        file_manager.select_folder(w)
        assert w.selected_files == []
        assert w.explorer_group.shown == 0
    finally:
        _restore()
    print("[PASS] test_select_folder_cancelled")


# ─── Недавние файлы ─────────────────────────────────────────────────────────

def test_add_to_recent_prepends_and_moves_duplicates():
    """Новый файл встаёт в начало, повторный — перемещается наверх."""
    w = _FakeWindow()
    file_manager.add_to_recent(w, "c:/a.md")
    file_manager.add_to_recent(w, "c:/b.md")
    assert w.settings.data["recent_files"] == ["c:/b.md", "c:/a.md"]

    file_manager.add_to_recent(w, "c:/a.md")
    assert w.settings.data["recent_files"] == ["c:/a.md", "c:/b.md"]
    assert w.recent_menu.actions()[0].text() == "a.md"
    print("[PASS] test_add_to_recent_prepends_and_moves_duplicates")


def test_add_to_recent_respects_limit():
    """История обрезается до MAX_RECENT."""
    w = _FakeWindow()
    for i in range(7):
        file_manager.add_to_recent(w, f"c:/f{i}.md")
    recent = w.settings.data["recent_files"]
    assert len(recent) == w.MAX_RECENT
    assert recent[0] == "c:/f6.md"
    assert recent[-1] == "c:/f2.md"
    assert len(w.recent_menu.actions()) == 5
    print("[PASS] test_add_to_recent_respects_limit")


def test_update_recent_menu_empty():
    """Пустая история: один отключённый пункт с подсказкой."""
    w = _FakeWindow()
    w.settings.data["recent_files"] = []
    file_manager.update_recent_menu(w)
    actions = w.recent_menu.actions()
    assert len(actions) == 1
    assert actions[0].text() == "menu_empty"
    assert actions[0].isEnabled() is False
    print("[PASS] test_update_recent_menu_empty")


def test_update_recent_menu_opens_selected():
    """Пункты меню хранят путь и открывают файл по клику."""
    w = _FakeWindow()
    w.settings.data["recent_files"] = ["c:/docs/a.md", "c:/docs/b.md"]
    opened = []
    original = file_manager.open_recent
    file_manager.open_recent = lambda win, path: opened.append((win, path))
    try:
        file_manager.update_recent_menu(w)
        actions = w.recent_menu.actions()
        assert [a.text() for a in actions] == ["a.md", "b.md"]
        assert [a.data() for a in actions] == ["c:/docs/a.md", "c:/docs/b.md"]
        actions[1].trigger()
        assert opened == [(w, "c:/docs/b.md")]
    finally:
        file_manager.open_recent = original
    print("[PASS] test_update_recent_menu_opens_selected")


def test_open_recent_missing_file_warns():
    """Удалённый файл: предупреждение, состояние не меняется."""
    try:
        _patch_all()
        w = _FakeWindow()
        file_manager.open_recent(w, "c:/gone.md")
        assert w.selected_files == []
        assert len(_FakeMessageBox.warnings) == 1
        assert _FakeMessageBox.warnings[0][0] == "msg_file_not_found"
        assert "c:/gone.md" in _FakeMessageBox.warnings[0][1]
        assert w.previews == []
    finally:
        _restore()
    print("[PASS] test_open_recent_missing_file_warns")


def test_open_recent_existing_file():
    """Существующий файл открывается как единственный выбранный."""
    tmpdir = tempfile.mkdtemp()
    try:
        path = _md_files(tmpdir, ["recent.md"])[0]
        w = _FakeWindow()
        w.active_workspace_folder = tmpdir
        file_manager.open_recent(w, path)
        assert w.selected_files == [path]
        assert w.active_workspace_folder is None
        assert w.explorer_group.hidden == 1
        assert w.file_label.text == "recent.md"
        assert w.btn_convert.enabled is True
        assert w.btn_watch.enabled is True
        assert w.log_output.clears == 1
        assert w.progress_bar.values == [0]
        assert w.logs == [f"log_opened_recent:{path}"]
        assert w.previews == [path]
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_open_recent_existing_file")


# ─── Папка с результатами ───────────────────────────────────────────────────

def test_open_output_folder_prefers_last_dir():
    """Открывается last_output_dir, если он существует."""
    tmpdir = tempfile.mkdtemp()
    try:
        called = []
        with patch.object(file_manager.os, "startfile", create=True, side_effect=called.append):
            w = _FakeWindow()
            w.last_output_dir = tmpdir
            file_manager.open_output_folder(w)
        assert called == [tmpdir]
        assert _FakeMessageBox.warnings == []
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_open_output_folder_prefers_last_dir")


def test_open_output_folder_falls_back_to_selected_file():
    """Без last_output_dir берётся папка выбранного файла."""
    tmpdir = tempfile.mkdtemp()
    try:
        path = _md_files(tmpdir, ["a.md"])[0]
        called = []
        with patch.object(file_manager.os, "startfile", create=True, side_effect=called.append):
            w = _FakeWindow()
            w.selected_files = [path]
            file_manager.open_output_folder(w)
        assert called == [os.path.dirname(path)]
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_open_output_folder_falls_back_to_selected_file")


def test_open_output_folder_falls_back_to_cwd():
    """Без выбранных файлов открывается текущий каталог."""
    called = []
    with patch.object(file_manager.os, "startfile", create=True, side_effect=called.append):
        w = _FakeWindow()
        file_manager.open_output_folder(w)
    assert called == [os.getcwd()]
    print("[PASS] test_open_output_folder_falls_back_to_cwd")


def test_open_output_folder_missing_warns():
    """Несуществующая папка: предупреждение вместо открытия."""
    fake = _FakeLogger()
    original = file_manager.logger
    file_manager.logger = fake
    try:
        _patch_all()
        called = []
        with patch.object(file_manager.os, "startfile", create=True, side_effect=called.append):
            w = _FakeWindow()
            w.last_output_dir = "c:/definitely/not/here"
            file_manager.open_output_folder(w)
        assert called == []
        assert len(_FakeMessageBox.warnings) == 1
        assert "Folder not found" in _FakeMessageBox.warnings[0][1]
    finally:
        file_manager.logger = original
        _restore()
    print("[PASS] test_open_output_folder_missing_warns")


def test_open_output_folder_startfile_failure_is_logged():
    """Сбой os.startfile не всплывает, а пишется в лог."""
    tmpdir = tempfile.mkdtemp()
    try:
        fake = _FakeLogger()
        original = file_manager.logger
        file_manager.logger = fake
        try:
            with patch.object(file_manager.os, "startfile", create=True, side_effect=OSError("denied")):
                w = _FakeWindow()
                w.last_output_dir = tmpdir
                file_manager.open_output_folder(w)
            assert fake.errors and "denied" in fake.errors[0]
        finally:
            file_manager.logger = original
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_open_output_folder_startfile_failure_is_logged")


# ─── Explorer рабочей папки ─────────────────────────────────────────────────

def test_update_workspace_explorer_hides_without_folder():
    """Без активной папки explorer скрывается."""
    w = _FakeWindow()
    file_manager.update_workspace_explorer(w)
    assert w.explorer_group.hidden == 1
    assert w.explorer_list.count() == 0

    w.active_workspace_folder = "c:/gone"
    file_manager.update_workspace_explorer(w)
    assert w.explorer_group.hidden == 2
    print("[PASS] test_update_workspace_explorer_hides_without_folder")


def test_update_workspace_explorer_lists_and_opens_first_file():
    """Список сортируется, первый файл открывается в редакторе."""
    tmpdir = tempfile.mkdtemp()
    try:
        _md_files(tmpdir, ["b.md"], content="# B\n")
        _md_files(tmpdir, ["a.md"], content="# A\n")
        with open(os.path.join(tmpdir, "skip.txt"), "w", encoding="utf-8") as f:
            f.write("x")
        w = _FakeWindow()
        w.active_workspace_folder = tmpdir
        file_manager.update_workspace_explorer(w)

        assert w.explorer_list.count() == 2
        assert [w.explorer_list.item(i).text() for i in range(2)] == ["a.md", "b.md"]
        assert [os.path.basename(p) for p in w.selected_files] == ["a.md", "b.md"]
        assert w.current_workspace_file == w.selected_files[0]
        assert w.live_editor.toPlainText() == "# A\n"
        assert w.is_welcome_doc_active is False
        assert w.render_calls == 1
        assert w.stats_calls == 1
        assert w.explorer_list.currentItem().text() == "a.md"
        assert w.explorer_list.currentItem().isSelected() is True
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_update_workspace_explorer_lists_and_opens_first_file")


def test_update_workspace_explorer_keeps_current_file():
    """Если текущий файл уже в папке, редактор не перезагружается."""
    tmpdir = tempfile.mkdtemp()
    try:
        files = _md_files(tmpdir, ["a.md", "b.md"])
        w = _FakeWindow()
        w.active_workspace_folder = tmpdir
        w.current_workspace_file = files[1]
        w.live_editor.setPlainText("draft text")
        file_manager.update_workspace_explorer(w)

        assert w.live_editor.toPlainText() == "draft text"
        assert w.render_calls == 0
        assert w.explorer_list.currentItem().text() == "b.md"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_update_workspace_explorer_keeps_current_file")


def test_update_workspace_explorer_listing_error_is_logged():
    """Ошибка чтения каталога логируется, explorer остаётся пустым."""
    tmpdir = tempfile.mkdtemp()
    fake = _FakeLogger()
    original = file_manager.logger
    file_manager.logger = fake
    try:
        w = _FakeWindow()
        w.active_workspace_folder = tmpdir
        with patch.object(file_manager.os, "listdir", side_effect=OSError("boom")):
            file_manager.update_workspace_explorer(w)
        assert w.explorer_list.count() == 0
        assert w.selected_files == []
        assert fake.errors and "boom" in fake.errors[0]
    finally:
        file_manager.logger = original
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_update_workspace_explorer_listing_error_is_logged")


def test_update_workspace_explorer_unreadable_file_is_logged():
    """Файл, который не читается (каталог с именем .md), не ломает обновление."""
    tmpdir = tempfile.mkdtemp()
    fake = _FakeLogger()
    original = file_manager.logger
    file_manager.logger = fake
    try:
        os.makedirs(os.path.join(tmpdir, "broken.md"))
        w = _FakeWindow()
        w.active_workspace_folder = tmpdir
        file_manager.update_workspace_explorer(w)
        assert w.explorer_list.count() == 1
        assert w.live_editor.toPlainText() == ""
        assert fake.errors
        assert w.render_calls == 0
    finally:
        file_manager.logger = original
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_update_workspace_explorer_unreadable_file_is_logged")


def test_load_workspace_file_ignores_invalid_items():
    """Пустой/несуществующий путь игнорируется без сохранения текущего файла."""
    saved = []
    original = file_manager.save_current_workspace_file
    file_manager.save_current_workspace_file = lambda w: saved.append(w)
    try:
        w = _FakeWindow()
        file_manager.load_workspace_file(w, QListWidgetItem("no data"))
        assert saved == []
        assert w.current_workspace_file is None

        item = QListWidgetItem("gone")
        item.setData(Qt.ItemDataRole.UserRole, "c:/gone.md")
        file_manager.load_workspace_file(w, item)
        assert saved == []
        assert w.current_workspace_file is None
    finally:
        file_manager.save_current_workspace_file = original
    print("[PASS] test_load_workspace_file_ignores_invalid_items")


def test_load_workspace_file_opens_content():
    """Загрузка файла: сохранение предыдущего, текст, выбор строки, превью."""
    tmpdir = tempfile.mkdtemp()
    try:
        files = _md_files(tmpdir, ["a.md", "b.md"])
        _md_files(tmpdir, ["b.md"], content="# Second\n")
        saved = []
        original = file_manager.save_current_workspace_file
        file_manager.save_current_workspace_file = lambda w: saved.append(w)
        try:
            w = _FakeWindow()
            w.active_workspace_folder = tmpdir
            file_manager.update_workspace_explorer(w)  # заполняет список, открывает a.md

            item = w.explorer_list.item(1)
            assert item.text() == "b.md"
            file_manager.load_workspace_file(w, item)

            assert saved == [w]
            assert w.current_workspace_file == files[1]
            assert w.live_editor.toPlainText() == "# Second\n"
            assert w.explorer_list.currentItem() is item
            assert w.is_welcome_doc_active is False
        finally:
            file_manager.save_current_workspace_file = original
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_load_workspace_file_opens_content")


def test_load_workspace_file_read_error_is_logged():
    """Ошибка чтения логируется, текущий файл всё равно переключается."""
    tmpdir = tempfile.mkdtemp()
    fake = _FakeLogger()
    original_logger = file_manager.logger
    original_save = file_manager.save_current_workspace_file
    file_manager.logger = fake
    file_manager.save_current_workspace_file = lambda w: None
    try:
        broken = os.path.join(tmpdir, "broken.md")
        os.makedirs(broken)
        w = _FakeWindow()
        w.live_editor.setPlainText("keep me")
        item = QListWidgetItem("broken.md")
        item.setData(Qt.ItemDataRole.UserRole, broken)
        file_manager.load_workspace_file(w, item)
        assert w.current_workspace_file == broken
        assert w.live_editor.toPlainText() == "keep me"
        assert fake.errors
    finally:
        file_manager.logger = original_logger
        file_manager.save_current_workspace_file = original_save
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_load_workspace_file_read_error_is_logged")


def test_save_current_workspace_file_writes_and_saves_revision():
    """Содержимое редактора пишется в файл, ревизия сохраняется."""
    tmpdir = tempfile.mkdtemp()
    try:
        path = _md_files(tmpdir, ["a.md"], content="old")[0]
        revisions = []
        import src.gui.document_tools as document_tools
        original = document_tools.save_revision
        document_tools.save_revision = lambda w: revisions.append(w)
        try:
            w = _FakeWindow()
            w.current_workspace_file = path
            w.live_editor.setPlainText("# new\n")
            file_manager.save_current_workspace_file(w)
            with open(path, "r", encoding="utf-8") as f:
                assert f.read() == "# new\n"
            assert revisions == [w]
        finally:
            document_tools.save_revision = original
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_save_current_workspace_file_writes_and_saves_revision")


def test_save_current_workspace_file_skips_without_file():
    """Без текущего файла запись не выполняется."""
    import src.gui.document_tools as document_tools
    revisions = []
    original = document_tools.save_revision
    document_tools.save_revision = lambda w: revisions.append(w)
    try:
        w = _FakeWindow()
        with patch.object(file_manager.os.path, "exists", return_value=False):
            file_manager.save_current_workspace_file(w)
        assert revisions == []
    finally:
        document_tools.save_revision = original
    print("[PASS] test_save_current_workspace_file_skips_without_file")


def test_save_current_workspace_file_write_error_is_logged():
    """Ошибка записи логируется и не пробрасывается."""
    tmpdir = tempfile.mkdtemp()
    fake = _FakeLogger()
    original_logger = file_manager.logger
    file_manager.logger = fake
    try:
        path = _md_files(tmpdir, ["a.md"])[0]
        w = _FakeWindow()
        w.current_workspace_file = path
        w.live_editor.setPlainText("text")
        with patch("builtins.open", side_effect=OSError("disk full")):
            file_manager.save_current_workspace_file(w)
        assert fake.errors and "disk full" in fake.errors[0]
    finally:
        file_manager.logger = original_logger
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_save_current_workspace_file_write_error_is_logged")


def test_filter_workspace_explorer():
    """Фильтр скрывает несовпадающие файлы и игнорирует регистр/пробелы."""
    w = _FakeWindow()
    for name in ("a.md", "b.md", "note.md"):
        w.explorer_list.addItem(QListWidgetItem(name))

    file_manager.filter_workspace_explorer(w, "  NO  ")
    assert [w.explorer_list.item(i).isHidden() for i in range(3)] == [True, True, False]

    file_manager.filter_workspace_explorer(w, "")
    assert all(not w.explorer_list.item(i).isHidden() for i in range(3))

    file_manager.filter_workspace_explorer(w, "A.")
    assert [w.explorer_list.item(i).isHidden() for i in range(3)] == [False, True, True]
    print("[PASS] test_filter_workspace_explorer")


def main():
    tests = [
        test_select_custom_css,
        test_select_docx_template,
        test_select_files_populates_window,
        test_select_files_single_enables_watch,
        test_select_files_without_watch_button,
        test_select_files_cancelled,
        test_select_folder_loads_markdown,
        test_select_folder_empty_warns,
        test_select_folder_cancelled,
        test_add_to_recent_prepends_and_moves_duplicates,
        test_add_to_recent_respects_limit,
        test_update_recent_menu_empty,
        test_update_recent_menu_opens_selected,
        test_open_recent_missing_file_warns,
        test_open_recent_existing_file,
        test_open_output_folder_prefers_last_dir,
        test_open_output_folder_falls_back_to_selected_file,
        test_open_output_folder_falls_back_to_cwd,
        test_open_output_folder_missing_warns,
        test_open_output_folder_startfile_failure_is_logged,
        test_update_workspace_explorer_hides_without_folder,
        test_update_workspace_explorer_lists_and_opens_first_file,
        test_update_workspace_explorer_keeps_current_file,
        test_update_workspace_explorer_listing_error_is_logged,
        test_update_workspace_explorer_unreadable_file_is_logged,
        test_load_workspace_file_ignores_invalid_items,
        test_load_workspace_file_opens_content,
        test_load_workspace_file_read_error_is_logged,
        test_save_current_workspace_file_writes_and_saves_revision,
        test_save_current_workspace_file_skips_without_file,
        test_save_current_workspace_file_write_error_is_logged,
        test_filter_workspace_explorer,
    ]
    for t in tests:
        t()
    print("\nAll file manager tests passed!")


if __name__ == "__main__":
    main()
