"""Поведенческие тесты gui/dialogs/content.py.

``DocumentBuilderDialog`` (сборка книги), ``MarkdownTOCDialog``,
``MarkdownTableDialog``, ``SnippetsDialog`` и ``SnippetsManagerDialog``.
Внешние зависимости (поток сборки, файловые диалоги, QMessageBox, QInputDialog,
файл библиотеки сниппетов) подменяются фейками.
"""
import json
import os
import shutil
import sys
import tempfile
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QWidget

app = QApplication.instance() or QApplication([])

from src.core import snippets as snippets_mod
from src.gui.dialogs import content as content_mod
from src.gui.dialogs.content import (
    DocumentBuilderDialog,
    MarkdownTOCDialog,
    MarkdownTableDialog,
    SnippetsDialog,
    SnippetsManagerDialog,
)


# ─── Фейки ──────────────────────────────────────────────────────────────────

class _FakeSignal:
    def __init__(self):
        self.slots = []

    def connect(self, fn):
        self.slots.append(fn)

    def emit(self, *args):
        for fn in self.slots:
            fn(*args)


class _FakeThread:
    """Заглушка BookBuilderThread: запоминает kwargs и умеет «завершиться»."""

    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.log = _FakeSignal()
        self.finished_task = _FakeSignal()
        self.started = False
        _FakeThread.instances.append(self)

    def start(self):
        self.started = True


class _FakeFileDialog:
    existing_dir = ""
    open_files = ([], "")
    save_path = ""
    calls = []

    @classmethod
    def getExistingDirectory(cls, *args, **kwargs):
        cls.calls.append("existing_dir")
        return cls.existing_dir

    @classmethod
    def getOpenFileNames(cls, *args, **kwargs):
        cls.calls.append("open_files")
        return cls.open_files

    @classmethod
    def getSaveFileName(cls, *args, **kwargs):
        cls.calls.append("save_file")
        return cls.save_path, ""


class _FakeMessageBox:
    warnings = []
    infos = []
    criticals = []

    @classmethod
    def warning(cls, parent, title, text, *args, **kwargs):
        cls.warnings.append((title, text))

    @classmethod
    def information(cls, parent, title, text, *args, **kwargs):
        cls.infos.append((title, text))

    @classmethod
    def critical(cls, parent, title, text, *args, **kwargs):
        cls.criticals.append((title, text))


class _FakeInputDialog:
    replies = []

    @classmethod
    def getText(cls, *args, **kwargs):
        if _FakeInputDialog.replies:
            return _FakeInputDialog.replies.pop(0)
        return "", False


class _FakeCombo:
    def __init__(self, data=None, text=""):
        self._data = data
        self._text = text

    def currentData(self):
        return self._data

    def currentText(self):
        return self._text


class _FakeInput:
    def __init__(self, text=""):
        self._text = text

    def text(self):
        return self._text


class _FakeLogOutput:
    def __init__(self):
        self.cleared = 0

    def clear(self):
        self.cleared += 1


class _FakeParent:
    """Минимальный хост: только то, что читает DocumentBuilderDialog."""

    def __init__(self):
        self.logs = []
        self.log_output = _FakeLogOutput()
        self.history = []
        self.history_ui_updates = 0
        self.doc_theme_combo = _FakeCombo("theme_modern.css")
        self.code_theme_combo = _FakeCombo("pygments.css")
        self.paper_combo = _FakeCombo(None, "A4")
        self.watermark_input = _FakeInput("CONFIDENTIAL")
        self.footer_input = _FakeInput("footer text")
        self.custom_css_input = _FakeInput("body { margin: 0; }")
        self.margins_input = _FakeInput("20mm")
        self.pdf_password_input = _FakeInput("secret")
        self.kroki_available = False

    def append_log(self, msg):
        self.logs.append(msg)

    def _get_template_dir(self):
        return "/templates"

    def _get_weasyprint_path(self):
        return "/usr/bin/weasyprint"

    def add_to_export_history(self, path):
        self.history.append(path)

    def update_export_history_ui(self):
        self.history_ui_updates += 1


def _patch_all(save_path="", existing_dir="", open_files=([], "")):
    _FakeThread.instances = []
    _FakeFileDialog.calls = []
    _FakeFileDialog.save_path = save_path
    _FakeFileDialog.existing_dir = existing_dir
    _FakeFileDialog.open_files = open_files
    _FakeMessageBox.warnings = []
    _FakeMessageBox.infos = []
    _FakeMessageBox.criticals = []
    content_mod.QFileDialog = _FakeFileDialog
    content_mod.QMessageBox = _FakeMessageBox
    import src.gui.threads as threads_mod
    threads_mod.BookBuilderThread = _FakeThread


def _restore():
    import PyQt6.QtWidgets as qtw
    import src.gui.threads as threads_mod
    content_mod.QFileDialog = qtw.QFileDialog
    content_mod.QMessageBox = qtw.QMessageBox
    threads_mod.BookBuilderThread = _original_thread
    _FakeMessageBox.warnings = []
    _FakeMessageBox.infos = []
    _FakeMessageBox.criticals = []


import src.gui.threads as _threads_module
_original_thread = _threads_module.BookBuilderThread


def _make_book(tmpdir, spec):
    """Создаёт файлы книги и возвращает их пути в порядке spec."""
    paths = []
    for name, text in spec:
        path = os.path.join(tmpdir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        paths.append(os.path.abspath(path))
    return paths


def _builder(paths=(), lang="ru", parent=None):
    d = DocumentBuilderDialog(parent=None, lang=lang)
    d.parent_window = parent if parent is not None else _FakeParent()
    for p in paths:
        d.list_widget.addItem(p)
    return d


# ─── DocumentBuilderDialog: начальное состояние ─────────────────────────────

def test_builder_defaults_russian():
    """Заголовок, подписи и включённые по умолчанию опции."""
    d = DocumentBuilderDialog(lang="ru")
    assert d.windowTitle() == "📖 Объединение .md файлов"
    assert d.isModal() is True
    assert d.chk_toc.isChecked() is True
    assert d.chk_pagebreak.isChecked() is True
    assert d.chk_pagenum.isChecked() is True
    assert d.chk_toc.text() == "Сгенерировать оглавление"
    assert d.chk_pagebreak.text() == "Разрыв страницы между главами"
    assert d.chk_pagenum.text() == "Нумерация страниц"
    assert d.btn_add_folder.text() == "📂 Добавить папку"
    assert d.btn_build.text() == "📖 Собрать книгу в PDF 🚀"
    assert d.book_title_input.placeholderText() == "Моя Книга"
    assert d.list_widget.count() == 0
    print("[PASS] test_builder_defaults_russian")


def test_builder_defaults_english():
    """Английские подписи конструктора книги."""
    d = DocumentBuilderDialog(lang="en")
    assert d.windowTitle() == "Book Builder & File Merger"
    assert d.chk_toc.text() == "Generate Table of Contents"
    assert d.btn_add.text() == "📄 Add Files..."
    assert d.btn_remove.text() == "Remove ✕"
    assert d.btn_up.text() == "Move Up ▲"
    assert d.btn_down.text() == "Move Down ▼"
    assert d.btn_build.text() == "📖 Build Book as PDF 🚀"
    assert d.book_title_input.placeholderText() == "My Book"
    print("[PASS] test_builder_defaults_english")


# ─── DocumentBuilderDialog: наполнение списка ───────────────────────────────

def test_load_folder_recursive_and_sorted():
    """Папка обходится рекурсивно, файлы сортируются, .txt игнорируется."""
    tmpdir = tempfile.mkdtemp()
    try:
        paths = _make_book(tmpdir, [
            ("b.md", "# B\n"),
            ("a.md", "# A\n"),
            ("notes.txt", "text"),
            ("sub/c.MD", "# C\n"),
            ("sub/deep/d.md", "# D\n"),
        ])
        expected = [paths[1], paths[0], paths[3], paths[4]]
        d = _builder()
        d.load_folder(tmpdir)
        got = [d.list_widget.item(i).text() for i in range(d.list_widget.count())]
        assert got == expected, got
        assert d.parent_window.logs == ["Найдено 4 файлов .md в папке"]
        assert _FakeMessageBox.warnings == []
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_load_folder_recursive_and_sorted")


def test_load_folder_empty_warns():
    """Пустая папка: предупреждение, список не меняется."""
    tmpdir = tempfile.mkdtemp()
    try:
        with open(os.path.join(tmpdir, "readme.txt"), "w", encoding="utf-8") as f:
            f.write("no markdown")
        _patch_all()
        d = _builder()
        d.load_folder(tmpdir)
        assert d.list_widget.count() == 0
        assert len(_FakeMessageBox.warnings) == 1
        title, text = _FakeMessageBox.warnings[0]
        assert title == "!"
        assert text == "В выбранной папке нет .md файлов."
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_load_folder_empty_warns")


def test_add_folder_uses_dialog():
    """Выбор папки делегируется в load_folder, отмена ничего не делает."""
    tmpdir = tempfile.mkdtemp()
    try:
        paths = _make_book(tmpdir, [("x.md", "# X\n"), ("y.md", "# Y\n")])
        try:
            _patch_all(existing_dir=tmpdir)
            d = _builder()
            d.add_folder()
            assert d.list_widget.count() == 2
            assert [d.list_widget.item(i).text() for i in range(2)] == paths
            assert _FakeFileDialog.calls == ["existing_dir"]

            _FakeFileDialog.calls = []
            _FakeFileDialog.existing_dir = ""
            d2 = _builder()
            d2.add_folder()
            assert d2.list_widget.count() == 0
            assert _FakeFileDialog.calls == ["existing_dir"]
        finally:
            _restore()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_add_folder_uses_dialog")


def test_add_files_uses_dialog():
    """Выбранные файлы добавляются абсолютными путями; отмена — ничего."""
    tmpdir = tempfile.mkdtemp()
    try:
        paths = _make_book(tmpdir, [("one.md", "# 1\n"), ("two.md", "# 2\n")])
        relative = [os.path.relpath(p, os.getcwd()) for p in paths]
        try:
            _patch_all(open_files=(relative, ""))
            d = _builder()
            d.add_files()
            got = [d.list_widget.item(i).text() for i in range(d.list_widget.count())]
            assert got == paths, got

            _FakeFileDialog.open_files = ([], "")
            d2 = _builder()
            d2.add_files()
            assert d2.list_widget.count() == 0
        finally:
            _restore()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_add_files_uses_dialog")


def test_remove_file_respects_selection():
    """Удаляется выделенный элемент, без выделения список не меняется."""
    d = _builder(["c:/a.md", "c:/b.md", "c:/c.md"])
    d.list_widget.setCurrentRow(1)
    d.remove_file()
    assert [d.list_widget.item(i).text() for i in range(d.list_widget.count())] == ["c:/a.md", "c:/c.md"]

    d.list_widget.setCurrentRow(-1)
    d.remove_file()
    assert d.list_widget.count() == 2
    print("[PASS] test_remove_file_respects_selection")


def test_move_up_and_down():
    """Перестановка строк работает и не выходит за границы списка."""
    d = _builder(["a", "b", "c"])
    d.list_widget.setCurrentRow(1)
    d.move_up()
    assert [d.list_widget.item(i).text() for i in range(3)] == ["b", "a", "c"]
    assert d.list_widget.currentRow() == 0

    d.move_up()  # уже наверху — без изменений
    assert [d.list_widget.item(i).text() for i in range(3)] == ["b", "a", "c"]

    d.list_widget.setCurrentRow(1)
    d.move_down()
    assert [d.list_widget.item(i).text() for i in range(3)] == ["b", "c", "a"]
    assert d.list_widget.currentRow() == 2

    d.move_down()  # уже внизу — без изменений
    assert [d.list_widget.item(i).text() for i in range(3)] == ["b", "c", "a"]
    print("[PASS] test_move_up_and_down")


def test_move_on_empty_list_is_safe():
    """Пустой список: обе операции ничего не делают."""
    d = _builder()
    d.move_up()
    d.move_down()
    assert d.list_widget.count() == 0
    print("[PASS] test_move_on_empty_list_is_safe")


# ─── DocumentBuilderDialog: сборка книги ────────────────────────────────────

def test_build_requires_files():
    """Без файлов сборка даже не спрашивает путь сохранения."""
    try:
        _patch_all(save_path="c:/out.pdf")
        d = _builder()
        d.build_merged_document()
        assert _FakeFileDialog.calls == []
        assert _FakeThread.instances == []
    finally:
        _restore()
    print("[PASS] test_build_requires_files")


def test_build_cancelled_by_save_dialog():
    """Отмена выбора PDF ничего не запускает."""
    tmpdir = tempfile.mkdtemp()
    try:
        paths = _make_book(tmpdir, [("a.md", "# A\n")])
        _patch_all(save_path="")
        d = _builder(paths)
        d.build_merged_document()
        assert _FakeFileDialog.calls == ["save_file"]
        assert _FakeThread.instances == []
        assert d.btn_build.isEnabled() is True
    finally:
        _restore()
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_build_cancelled_by_save_dialog")


def test_build_generates_merged_markdown():
    """Заголовок книги, оглавление с якорями, разрывы страниц и главы."""
    tmpdir = tempfile.mkdtemp()
    try:
        paths = _make_book(tmpdir, [
            ("ch1.md", "# Chapter One\n\nFirst body.\n"),
            ("ch2.md", "No heading here.\n"),
        ])
        out = os.path.join(tmpdir, "book.pdf")
        _patch_all(save_path=out)
        parent = _FakeParent()
        d = _builder(paths, parent=parent)
        d.book_title_input.setText("My Book")
        d.build_merged_document()

        assert len(_FakeThread.instances) == 1
        thread = _FakeThread.instances[0]
        merged = thread.kwargs["merged_md"]

        assert merged.startswith("# My Book\n\n")
        assert "## Оглавление" in merged
        assert "1. [Chapter One](#chapter-one)" in merged
        assert "2. [ch2](#ch2)" in merged
        assert "# Chapter One" in merged
        assert "No heading here." in merged
        assert merged.count('<div style="page-break-before: always;"></div>') == 2
        assert merged.index("## Оглавление") < merged.index("# Chapter One")
        print("[PASS] test_build_generates_merged_markdown")
    finally:
        _restore()
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_build_passes_all_settings_to_thread():
    """В поток уходят тема, шрифты, бумага, поля, пароль и флаги."""
    tmpdir = tempfile.mkdtemp()
    try:
        paths = _make_book(tmpdir, [("a.md", "# A\n"), ("sub/b.md", "# B\n")])
        out = os.path.join(tmpdir, "book.pdf")
        _patch_all(save_path=out)
        parent = _FakeParent()
        d = _builder(paths, parent=parent)
        d.book_title_input.setText("T")
        d.chk_pagenum.setChecked(False)
        d.build_merged_document()

        kw = _FakeThread.instances[0].kwargs
        assert kw["base_dir"] == tmpdir
        assert os.path.normcase(kw["base_dir"]) == os.path.normcase(os.path.dirname(paths[0]))
        assert kw["save_path"] == out
        assert kw["book_title"] == "T"
        assert kw["template_dir"] == "/templates"
        assert kw["wp_executable"] == "/usr/bin/weasyprint"
        assert kw["doc_theme"] == "theme_modern.css"
        assert kw["code_theme"] == "pygments.css"
        assert kw["paper_size"] == "A4"
        assert kw["watermark"] == "CONFIDENTIAL"
        assert kw["footer"] == "footer text"
        assert kw["custom_css"] == "body { margin: 0; }"
        assert kw["margins"] == "20mm"
        assert kw["password"] == "secret"
        assert kw["page_numbers"] is False
        assert kw["lang"] == "ru"
        assert kw["kroki_available"] is False
        print("[PASS] test_build_passes_all_settings_to_thread")
    finally:
        _restore()
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_build_disables_button_while_running():
    """На время сборки кнопка блокируется и меняет подпись."""
    tmpdir = tempfile.mkdtemp()
    try:
        paths = _make_book(tmpdir, [("a.md", "# A\n")])
        _patch_all(save_path=os.path.join(tmpdir, "out.pdf"))
        parent = _FakeParent()
        d = _builder(paths, parent=parent)
        d.build_merged_document()
        assert d.btn_build.isEnabled() is False
        assert d.btn_build.text() == "Сборка..."
        assert _FakeThread.instances[0].started is True
        assert parent.log_output.cleared == 1
        assert parent.logs[0].startswith("\n📚 Building book (1 chapters) → ")
        assert parent.logs[1] == "  📖 Chapter 1: A"
    finally:
        _restore()
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_build_disables_button_while_running")


def test_build_log_and_finish_callbacks():
    """log пробрасывается в лог окна, успешное завершение закрывает диалог."""
    tmpdir = tempfile.mkdtemp()
    try:
        paths = _make_book(tmpdir, [("a.md", "# A\n"), ("b.md", "# B\n")])
        out = os.path.join(tmpdir, "book.pdf")
        _patch_all(save_path=out)
        parent = _FakeParent()
        d = _builder(paths, parent=parent)
        d.build_merged_document()
        thread = _FakeThread.instances[0]

        thread.log.emit("render step")
        assert parent.logs[-1] == "render step"

        thread.finished_task.emit(True, out)
        assert d.btn_build.isEnabled() is True
        assert d.btn_build.text() == "📖 Собрать книгу в PDF 🚀"
        assert d.result() == QDialog.DialogCode.Accepted
        assert parent.history == [out]
        assert parent.history_ui_updates == 1
        assert len(_FakeMessageBox.infos) == 1
        title, text = _FakeMessageBox.infos[0]
        assert title == "Готово!"
        assert "Глав: 2" in text
        assert out in text
        assert any("Книга собрана успешно!" in m for m in parent.logs)
    finally:
        _restore()
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_build_log_and_finish_callbacks")


def test_build_failure_reports_critical():
    """Неудачная сборка: критическое сообщение, диалог остаётся открытым."""
    tmpdir = tempfile.mkdtemp()
    try:
        paths = _make_book(tmpdir, [("a.md", "# A\n")])
        _patch_all(save_path=os.path.join(tmpdir, "book.pdf"))
        d = _builder(paths, parent=_FakeParent())
        d.build_merged_document()
        thread = _FakeThread.instances[0]
        thread.finished_task.emit(False, "weasyprint not found")

        assert d.btn_build.isEnabled() is True
        assert d.result() != QDialog.DialogCode.Accepted
        assert len(_FakeMessageBox.criticals) == 1
        title, text = _FakeMessageBox.criticals[0]
        assert title == "Error"
        assert "weasyprint not found" in text
    finally:
        _restore()
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_build_failure_reports_critical")


def test_build_missing_file_logs_setup_error():
    """Ошибка подготовки (нет файла) логируется и показывается пользователю."""
    try:
        _patch_all(save_path="c:/out.pdf")
        parent = _FakeParent()
        d = _builder(["c:/does/not/exist.md"], parent=parent)
        with patch("traceback.print_exc"):
            d.build_merged_document()
        assert _FakeThread.instances == []
        assert len(_FakeMessageBox.criticals) == 1
        assert "Failed to setup book builder" in _FakeMessageBox.criticals[0][1]
        assert any("❌ Error:" in m for m in parent.logs)
        assert d.btn_build.isEnabled() is True  # кнопка не успела заблокироваться
    finally:
        _restore()
    print("[PASS] test_build_missing_file_logs_setup_error")


def test_build_without_toc_and_pagebreaks():
    """Отключённые опции убирают оглавление и разрывы страниц."""
    tmpdir = tempfile.mkdtemp()
    try:
        paths = _make_book(tmpdir, [("a.md", "# A\n"), ("b.md", "# B\n")])
        _patch_all(save_path=os.path.join(tmpdir, "book.pdf"))
        d = _builder(paths, parent=_FakeParent())
        d.chk_toc.setChecked(False)
        d.chk_pagebreak.setChecked(False)
        d.build_merged_document()
        merged = _FakeThread.instances[0].kwargs["merged_md"]
        assert "Оглавление" not in merged
        assert "page-break-before" not in merged
        print("[PASS] test_build_without_toc_and_pagebreaks")
    finally:
        _restore()
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_build_pagebreak_without_toc():
    """Без оглавления остаётся только разрыв между главами."""
    tmpdir = tempfile.mkdtemp()
    try:
        paths = _make_book(tmpdir, [("a.md", "# A\n"), ("b.md", "# B\n"), ("c.md", "# C\n")])
        _patch_all(save_path=os.path.join(tmpdir, "book.pdf"))
        d = _builder(paths, parent=_FakeParent())
        d.chk_toc.setChecked(False)
        d.build_merged_document()
        merged = _FakeThread.instances[0].kwargs["merged_md"]
        assert merged.count('<div style="page-break-before: always;"></div>') == 2
        print("[PASS] test_build_pagebreak_without_toc")
    finally:
        _restore()
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_build_without_book_title_starts_with_toc():
    """Без названия книги документ начинается с оглавления."""
    tmpdir = tempfile.mkdtemp()
    try:
        paths = _make_book(tmpdir, [("a.md", "# A\n")])
        _patch_all(save_path=os.path.join(tmpdir, "book.pdf"))
        d = _builder(paths, parent=_FakeParent())
        d.build_merged_document()
        merged = _FakeThread.instances[0].kwargs["merged_md"]
        assert merged.startswith("## Оглавление")
        print("[PASS] test_build_without_book_title_starts_with_toc")
    finally:
        _restore()
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_build_english_labels():
    """Английская локаль: заголовок TOC, текст кнопки, финальное сообщение."""
    tmpdir = tempfile.mkdtemp()
    try:
        paths = _make_book(tmpdir, [("a.md", "# A\n")])
        out = os.path.join(tmpdir, "book.pdf")
        _patch_all(save_path=out)
        d = _builder(paths, lang="en", parent=_FakeParent())
        d.build_merged_document()
        thread = _FakeThread.instances[0]
        assert "## Table of Contents" in thread.kwargs["merged_md"]
        assert d.btn_build.text() == "Building..."
        thread.finished_task.emit(True, out)
        assert d.btn_build.text() == "📖 Build Book as PDF 🚀"
        title, text = _FakeMessageBox.infos[0]
        assert title == "Done!"
        assert "Chapters: 1" in text
    finally:
        _restore()
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_build_english_labels")


def test_build_chapter_title_fallback_and_slug():
    """Заголовок без H1 берётся из имени файла, якорь чистится от пунктуации."""
    tmpdir = tempfile.mkdtemp()
    try:
        paths = _make_book(tmpdir, [
            ("my notes.md", "Plain text\n"),
            ("punct.md", "# Hello, World! (Draft)\n"),
        ])
        _patch_all(save_path=os.path.join(tmpdir, "book.pdf"))
        parent = _FakeParent()
        d = _builder(paths, parent=parent)
        d.build_merged_document()
        merged = _FakeThread.instances[0].kwargs["merged_md"]
        assert "1. [my notes](#my-notes)" in merged
        assert "2. [Hello, World! (Draft)](#hello-world-draft)" in merged
        assert "  📖 Chapter 2: Hello, World! (Draft)" in parent.logs
    finally:
        _restore()
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_build_chapter_title_fallback_and_slug")


# ─── MarkdownTOCDialog / MarkdownTableDialog ────────────────────────────────

def test_toc_dialog_defaults():
    """Глубина H1–H2, маркированный список, якоря включены."""
    d = MarkdownTOCDialog(lang="ru")
    assert d.windowTitle() == "📋 Генератор оглавления"
    assert d.depth_combo.count() == 3
    assert [d.depth_combo.itemData(i) for i in range(3)] == [1, 2, 3]
    assert d.depth_combo.currentIndex() == 1
    assert d.depth_combo.currentData() == 2
    assert d.style_combo.count() == 2
    assert d.style_combo.itemData(0) == "bullet"
    assert d.style_combo.itemData(1) == "numbered"
    assert d.style_combo.currentData() == "bullet"
    assert d.anchors_chk.isChecked() is True
    ok = d.button_box.button(QDialogButtonBox.StandardButton.Ok)
    cancel = d.button_box.button(QDialogButtonBox.StandardButton.Cancel)
    assert ok.text() == "Сгенерировать"
    assert cancel.text() == "Отмена"
    print("[PASS] test_toc_dialog_defaults")


def test_toc_dialog_english_and_signals():
    """Английские подписи; кнопки дают Accepted/Rejected."""
    d = MarkdownTOCDialog(lang="en")
    assert d.windowTitle() == "📋 Table of Contents Generator"
    ok = d.button_box.button(QDialogButtonBox.StandardButton.Ok)
    assert ok.text() == "Generate"
    ok.click()
    assert d.result() == QDialog.DialogCode.Accepted

    d2 = MarkdownTOCDialog()
    d2.button_box.button(QDialogButtonBox.StandardButton.Cancel).click()
    assert d2.result() == QDialog.DialogCode.Rejected
    print("[PASS] test_toc_dialog_english_and_signals")


def test_table_dialog_defaults():
    """Таблица 3×3, диапазоны 1…50 и 1…20."""
    d = MarkdownTableDialog(lang="ru")
    assert d.windowTitle() == "Генератор таблиц Markdown"
    assert d.rows_spin.value() == 3
    assert d.cols_spin.value() == 3
    assert d.rows_spin.minimum() == 1 and d.rows_spin.maximum() == 50
    assert d.cols_spin.minimum() == 1 and d.cols_spin.maximum() == 20
    ok = d.button_box.button(QDialogButtonBox.StandardButton.Ok)
    assert ok.text() == "Вставить"
    ok.click()
    assert d.result() == QDialog.DialogCode.Accepted
    print("[PASS] test_table_dialog_defaults")


def test_table_dialog_english_and_cancel():
    """Английская подпись кнопки и отмена."""
    d = MarkdownTableDialog(lang="en")
    assert d.windowTitle() == "Markdown Table Generator"
    assert d.button_box.button(QDialogButtonBox.StandardButton.Ok).text() == "Insert"
    d.button_box.button(QDialogButtonBox.StandardButton.Cancel).click()
    assert d.result() == QDialog.DialogCode.Rejected
    print("[PASS] test_table_dialog_english_and_cancel")


# ─── SnippetsDialog ─────────────────────────────────────────────────────────

def test_snippets_dialog_lists_all_templates():
    """Шесть шаблонов, выбор по умолчанию отсутствует."""
    d = SnippetsDialog(lang="ru")
    assert d.windowTitle() == "🧩 Выберите шаблон для вставки"
    assert d.list_widget.count() == 6
    assert d.get_selected_snippet() == ""
    print("[PASS] test_snippets_dialog_lists_all_templates")


def test_snippets_dialog_returns_selected_text():
    """Выбранный шаблон отдаётся в виде markdown-текста."""
    d = SnippetsDialog(lang="ru")
    d.list_widget.setCurrentRow(0)
    got = d.get_selected_snippet()
    assert got.startswith("- [ ] Шаг 1")
    d.list_widget.setCurrentRow(3)
    assert "```python" in d.get_selected_snippet()
    d.list_widget.setCurrentRow(5)
    assert d.get_selected_snippet().startswith("![")
    print("[PASS] test_snippets_dialog_returns_selected_text")


def test_snippets_dialog_english_titles():
    """Английские названия шаблонов, содержимое шаблонов не переводится."""
    d = SnippetsDialog(lang="en")
    items = [d.list_widget.item(i).text() for i in range(d.list_widget.count())]
    assert "📋 Task List (Checklist)" in items
    assert "🐍 Python Code Block" in items
    d.list_widget.setCurrentRow(0)
    assert d.get_selected_snippet().startswith("- [ ] Шаг 1")
    print("[PASS] test_snippets_dialog_english_titles")


def test_snippets_dialog_buttons():
    """OK/Cancel закрывают диалог соответствующим результатом."""
    d = SnippetsDialog(lang="ru")
    assert d.button_box.button(QDialogButtonBox.StandardButton.Ok).text() == "Сохранить тему"
    d.button_box.button(QDialogButtonBox.StandardButton.Ok).click()
    assert d.result() == QDialog.DialogCode.Accepted

    d2 = SnippetsDialog()
    d2.button_box.button(QDialogButtonBox.StandardButton.Cancel).click()
    assert d2.result() == QDialog.DialogCode.Rejected
    print("[PASS] test_snippets_dialog_buttons")


# ─── SnippetsManagerDialog ──────────────────────────────────────────────────

class _FakeCursor:
    def __init__(self, text):
        self._text = text

    def selectedText(self):
        return self._text


class _FakeEditor:
    def __init__(self, selected="", full=""):
        self.selected = selected
        self.full = full

    def textCursor(self):
        return _FakeCursor(self.selected)

    def toPlainText(self):
        return self.full


class _FakeHost(QWidget):
    def __init__(self, selected="", full=""):
        super().__init__()
        self.live_editor = _FakeEditor(selected, full)


class _snippets_file:
    """Подменяет путь библиотеки на временный, чтобы не трогать APPDATA."""

    def __enter__(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = os.path.join(self.tmpdir, "snippets.json")
        self._orig = snippets_mod.SNIPPETS_FILE
        snippets_mod.SNIPPETS_FILE = self.path
        return self.path

    def __exit__(self, *exc):
        snippets_mod.SNIPPETS_FILE = self._orig
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        return False


def test_manager_lists_default_library():
    """Библиотека по умолчанию: 8 сниппетов с языком в подписи."""
    with _snippets_file() as path:
        d = SnippetsManagerDialog(lang="ru")
        assert d.windowTitle() == "Библиотека сниппетов"
        assert d.snippet_list.count() == 8
        assert d.snippet_list.item(0).text() == "[python] Python function"
        assert os.path.exists(path), "библиотека должна сохраниться в файл"
        with open(path, "r", encoding="utf-8") as f:
            assert len(json.load(f)) == 8
        assert d.selected_code is None
        assert d.btn_insert.text() == "Вставить"
    print("[PASS] test_manager_lists_default_library")


def test_manager_english_title():
    """Английский заголовок и подсказка поиска."""
    with _snippets_file():
        d = SnippetsManagerDialog(lang="en")
        assert d.windowTitle() == "Snippet Library"
        assert d.search_input.placeholderText() == "Search..."
    print("[PASS] test_manager_english_title")


def test_manager_filter_snippets():
    """Поиск скрывает несовпадающие элементы, пустой запрос возвращает все."""
    with _snippets_file():
        d = SnippetsManagerDialog()
        d.search_input.setText("python")
        hidden = [d.snippet_list.item(i).isHidden() for i in range(d.snippet_list.count())]
        assert hidden[:2] == [False, False]
        assert hidden[2] is True  # JavaScript
        assert hidden[4] is True  # SQL
        d.search_input.setText("")
        assert all(not d.snippet_list.item(i).isHidden() for i in range(d.snippet_list.count()))
        d.search_input.setText("НЕТ ТАКОГО")
        assert all(d.snippet_list.item(i).isHidden() for i in range(d.snippet_list.count()))
    print("[PASS] test_manager_filter_snippets")


def test_manager_preview_escapes_html():
    """Превью показывает имя, язык и экранированный код."""
    with _snippets_file():
        d = SnippetsManagerDialog()
        d.snippet_list.setCurrentRow(3)  # HTML template
        html = d.preview.toHtml()
        assert "HTML template" in html
        assert "html" in html
        assert "&lt;!DOCTYPE html&gt;" in html
        assert "&lt;/html&gt;" in html
        assert d.preview.toPlainText().count("<!DOCTYPE html>") == 1
    print("[PASS] test_manager_preview_escapes_html")


def test_manager_on_select_ignores_none():
    """Снятие выделения не сбрасывает превью и не падает."""
    with _snippets_file():
        d = SnippetsManagerDialog()
        d.snippet_list.setCurrentRow(0)
        html = d.preview.toHtml()
        d.on_select(None, d.snippet_list.item(0))
        assert d.preview.toHtml() == html
    print("[PASS] test_manager_on_select_ignores_none")


def test_manager_insert_snippet():
    """Вставка отдаёт код выбранного сниппета и закрывает диалог."""
    with _snippets_file():
        d = SnippetsManagerDialog()
        d.insert_snippet()
        assert d.selected_code is None
        assert d.result() != QDialog.DialogCode.Accepted

        d.snippet_list.setCurrentRow(1)
        d.insert_snippet()
        assert d.selected_code.startswith("class ClassName:")
        assert d.result() == QDialog.DialogCode.Accepted
    print("[PASS] test_manager_insert_snippet")


def test_manager_delete_snippet():
    """Удаление убирает сниппет из списка, библиотеки и файла."""
    with _snippets_file() as path:
        d = SnippetsManagerDialog()
        d.delete_snippet()  # без выделения — ничего
        assert d.snippet_list.count() == 8

        d.snippet_list.setCurrentRow(0)
        d.delete_snippet()
        assert d.snippet_list.count() == 7
        assert len(d.library.get_all()) == 7
        assert d.snippet_list.item(0).text() == "[python] Python class"
        with open(path, "r", encoding="utf-8") as f:
            names = [s["name"] for s in json.load(f)]
        assert "Python function" not in names
        assert len(names) == 7
    print("[PASS] test_manager_delete_snippet")


def test_manager_add_current_code_uses_selection():
    """Добавление кода: выбранный в редакторе текст, два запроса ввода."""
    with _snippets_file():
        host = _FakeHost(selected="print(42)", full="full document")
        try:
            _FakeInputDialog.replies = [("My snippet", True), ("python", True)]
            _patch_input()
            d = SnippetsManagerDialog(parent=host)
            d.add_current_code()
            assert d.snippet_list.count() == 9
            added = d.library.get_all()[-1]
            assert added.name == "My snippet"
            assert added.language == "python"
            assert added.code == "print(42)"
            assert d.snippet_list.item(8).text() == "[python] My snippet"
        finally:
            _restore_input_dialog()
    print("[PASS] test_manager_add_current_code_uses_selection")


def test_manager_add_current_code_falls_back_to_document():
    """Без выделения берётся начало документа (не более 500 символов)."""
    with _snippets_file():
        host = _FakeHost(selected="", full="x" * 700)
        try:
            _FakeInputDialog.replies = [("Long", True), ("text", True)]
            _patch_input()
            d = SnippetsManagerDialog(parent=host)
            d.add_current_code()
            added = d.library.get_all()[-1]
            assert added.code == "x" * 500
        finally:
            _restore_input_dialog()
    print("[PASS] test_manager_add_current_code_falls_back_to_document")


def test_manager_add_current_code_without_editor():
    """Без родительского редактора сохраняется пустой код."""
    with _snippets_file():
        try:
            _FakeInputDialog.replies = [("Empty", True), ("python", True)]
            _patch_input()
            d = SnippetsManagerDialog()
            d.add_current_code()
            added = d.library.get_all()[-1]
            assert added.name == "Empty"
            assert added.code == ""
        finally:
            _restore_input_dialog()
    print("[PASS] test_manager_add_current_code_without_editor")


def test_manager_add_current_code_cancelled():
    """Отмена любого из запросов не добавляет сниппет."""
    with _snippets_file():
        host = _FakeHost(selected="s", full="f")
        try:
            _patch_input()
            _FakeInputDialog.replies = [("Name", False)]
            d = SnippetsManagerDialog(parent=host)
            d.add_current_code()
            assert d.snippet_list.count() == 8

            _FakeInputDialog.replies = [("Name", True), ("python", False)]
            d.add_current_code()
            assert d.snippet_list.count() == 8

            _FakeInputDialog.replies = [("", True), ("python", True)]
            d.add_current_code()
            assert d.snippet_list.count() == 8
        finally:
            _restore_input_dialog()
    print("[PASS] test_manager_add_current_code_cancelled")


def _restore_input_dialog():
    import PyQt6.QtWidgets as qtw
    qtw.QInputDialog = qtw._orig_QInputDialog


def _patch_input():
    import PyQt6.QtWidgets as qtw
    if not hasattr(qtw, "_orig_QInputDialog"):
        qtw._orig_QInputDialog = qtw.QInputDialog
    qtw.QInputDialog = _FakeInputDialog


def main():
    tests = [
        test_builder_defaults_russian,
        test_builder_defaults_english,
        test_load_folder_recursive_and_sorted,
        test_load_folder_empty_warns,
        test_add_folder_uses_dialog,
        test_add_files_uses_dialog,
        test_remove_file_respects_selection,
        test_move_up_and_down,
        test_move_on_empty_list_is_safe,
        test_build_requires_files,
        test_build_cancelled_by_save_dialog,
        test_build_generates_merged_markdown,
        test_build_passes_all_settings_to_thread,
        test_build_disables_button_while_running,
        test_build_log_and_finish_callbacks,
        test_build_failure_reports_critical,
        test_build_missing_file_logs_setup_error,
        test_build_without_toc_and_pagebreaks,
        test_build_pagebreak_without_toc,
        test_build_without_book_title_starts_with_toc,
        test_build_english_labels,
        test_build_chapter_title_fallback_and_slug,
        test_toc_dialog_defaults,
        test_toc_dialog_english_and_signals,
        test_table_dialog_defaults,
        test_table_dialog_english_and_cancel,
        test_snippets_dialog_lists_all_templates,
        test_snippets_dialog_returns_selected_text,
        test_snippets_dialog_english_titles,
        test_snippets_dialog_buttons,
        test_manager_lists_default_library,
        test_manager_english_title,
        test_manager_filter_snippets,
        test_manager_preview_escapes_html,
        test_manager_on_select_ignores_none,
        test_manager_insert_snippet,
        test_manager_delete_snippet,
        test_manager_add_current_code_uses_selection,
        test_manager_add_current_code_falls_back_to_document,
        test_manager_add_current_code_without_editor,
        test_manager_add_current_code_cancelled,
    ]
    for t in tests:
        t()
    print("\nAll content dialog tests passed!")


if __name__ == "__main__":
    main()
