"""Поведенческие тесты миксинов: форматирование, конвертация, интеграции, воркспейс.

Дополняет `test_coverage_mixins.py` (PLAN-013, этап 3). Покрывает:
- `mixins/editor_formatting.py` — спеллчек, эмодзи, мульти-курсор, делегаты;
- `mixins/convert_tools.py` — PDF→MD, HTML→MD, OCR (в т.ч. отмена и ошибки);
- `mixins/integrations.py` — диалоги интеграций, применение водяного знака;
- `mixins/workspace.py` — wikilinks, переменные шаблона, делегаты, resize.
"""
import os
import sys
import tempfile
import types

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QWidget

app = QApplication.instance() or QApplication([])

import src.gui.mixins.convert_tools as ct
import src.gui.mixins.editor_formatting as ef
import src.gui.mixins.integrations as integ
import src.gui.mixins.workspace as ws


# ─── общие заглушки ──────────────────────────────────────────────────────────

class _MsgBox:
    """Заглушка QMessageBox, записывающая вызовы."""

    def __init__(self):
        self.calls = []

    def install(self, module):
        self._orig = module.QMessageBox
        module.QMessageBox = types.SimpleNamespace(
            information=lambda *a, **k: self.calls.append(("information", a)),
            warning=lambda *a, **k: self.calls.append(("warning", a)),
            critical=lambda *a, **k: self.calls.append(("critical", a)),
            question=lambda *a, **k: self.calls.append(("question", a)),
        )
        return self

    def restore(self, module):
        module.QMessageBox = self._orig

    @property
    def kinds(self):
        return [c[0] for c in self.calls]

    def text_of(self, i=0):
        return self.calls[i][1][-1] if self.calls else ""


class _Cursor:
    def __init__(self):
        self.inserted = []

    def insertText(self, s):
        self.inserted.append(s)


class _Editor:
    def __init__(self, text=""):
        self._text = text
        self.cursor = _Cursor()
        self.focused = False

    def toPlainText(self):
        return self._text

    def setPlainText(self, t):
        self._text = t

    def textCursor(self):
        return self.cursor

    def setFocus(self):
        self.focused = True


class _Label:
    def __init__(self):
        self.text = ""

    def setText(self, t):
        self.text = t


class _Input:
    def __init__(self):
        self.text = ""

    def setText(self, t):
        self.text = t


class _TextField:
    """Поле ввода Qt-стиля: значение читается методом text()."""

    def __init__(self, value=""):
        self._value = value

    def text(self):
        return self._value

    def setText(self, t):
        self._value = t


class _MultiCursor:
    def __init__(self):
        self.added = 0

    def add_cursor_at_current(self):
        self.added += 1


class FakeHost(QWidget):
    """Фейковый хост MainWindow."""

    def __init__(self, text="", lang="ru"):
        super().__init__()
        self.live_editor = _Editor(text)
        self.current_lang = lang
        self.logs = []
        self.toasts = []
        self.previews = []
        self.stats_label = _Label()
        self.footer_input = _Input()
        self.watermark_css_input = _Input()
        self.multi_cursor = _MultiCursor()
        self.active_workspace_folder = None
        self.selected_files = []
        self.explorer_list = None

    def append_log(self, msg):
        self.logs.append(msg)

    def toast(self, msg, kind="info"):
        self.toasts.append((msg, kind))

    def _render_live_preview(self):
        self.previews.append("render")

    def update_text_statistics(self):
        pass


# ─── editor_formatting ───────────────────────────────────────────────────────

def test_spell_check_no_words():
    """Без слов спеллчек сообщает об этом."""
    rec = _MsgBox().install(ef)
    try:
        h = FakeHost("123 !!! ---")
        ef.EditorFormattingMixin.run_spell_check(h)
    finally:
        rec.restore(ef)
    assert "information" in rec.kinds, rec.calls
    assert "No words found" in rec.text_of()
    print("[PASS] test_spell_check_no_words")


def test_spell_check_counts_long_words():
    """Спеллчек считает слова и находит потенциально длинные."""
    rec = _MsgBox().install(ef)
    try:
        long_word = "a" * 25
        h = FakeHost(f"hello {long_word} world")
        ef.EditorFormattingMixin.run_spell_check(h)
    finally:
        rec.restore(ef)
    msg = rec.text_of()
    assert "Checked 3 words" in msg, msg
    assert "Found 1 potential issues" in msg, msg
    print("[PASS] test_spell_check_counts_long_words")


def test_spell_check_without_issues():
    """Без проблем сообщается, что всё в порядке."""
    rec = _MsgBox().install(ef)
    try:
        h = FakeHost("hello world")
        ef.EditorFormattingMixin.run_spell_check(h)
    finally:
        rec.restore(ef)
    assert "No issues found" in rec.text_of(), rec.text_of()
    print("[PASS] test_spell_check_without_issues")


def test_convert_emoji_shortcodes():
    """Шорткоды эмодзи заменяются символами, неизвестные остаются."""
    h = FakeHost("Привет :smile: и :unknown_code: и :fire:")
    ef.EditorFormattingMixin.convert_emoji_shortcodes(h)
    text = h.live_editor.toPlainText()
    assert ":smile:" not in text, text
    assert "\U0001F604" in text, text
    assert "\U0001F525" in text, text
    assert ":unknown_code:" in text, text
    assert h.previews == ["render"]
    assert h.toasts and h.toasts[-1][1] == "success", h.toasts
    print("[PASS] test_convert_emoji_shortcodes")


def test_add_multi_cursor():
    """Мульти-курсор добавляется в текущей позиции."""
    h = FakeHost()
    ef.EditorFormattingMixin.add_multi_cursor(h)
    assert h.multi_cursor.added == 1
    assert h.toasts and "Multi-cursor" in h.toasts[-1][0], h.toasts
    print("[PASS] test_add_multi_cursor")


def test_editor_formatting_delegates_to_editor_commands():
    """Форматирование делегируется в src.gui.editor_commands."""
    import src.gui.editor_commands as ec

    calls = []
    orig = {}
    for name in ("format_bold", "format_italic", "format_code", "format_quote",
                 "format_list", "insert_page_break", "format_markdown_document",
                 "format_header"):
        orig[name] = getattr(ec, name)

        def _make(nm):
            def _f(window, *a, **k):
                calls.append((nm, window))
            return _f

        setattr(ec, name, _make(name))

    try:
        h = FakeHost()
        ef.EditorFormattingMixin.format_bold(h)
        ef.EditorFormattingMixin.format_italic(h)
        ef.EditorFormattingMixin.format_code(h)
        ef.EditorFormattingMixin.format_quote(h)
        ef.EditorFormattingMixin.format_list(h)
        ef.EditorFormattingMixin.insert_page_break(h)
        ef.EditorFormattingMixin.format_markdown_document(h)
        ef.EditorFormattingMixin.format_header(h, 2)
    finally:
        for name, fn in orig.items():
            setattr(ec, name, fn)

    names = [c[0] for c in calls]
    for expected in ("format_bold", "format_italic", "format_code", "format_quote",
                     "format_list", "insert_page_break", "format_markdown_document",
                     "format_header"):
        assert expected in names, (expected, names)
    assert all(c[1] is h for c in calls)
    print("[PASS] test_editor_formatting_delegates_to_editor_commands")


def test_run_linter_opens_audit():
    """run_linter открывает окно аудита документа."""
    import src.gui.document_tools as dt

    called = []
    orig = dt.show_document_audit
    dt.show_document_audit = lambda w: called.append(w)
    try:
        h = FakeHost("# Заголовок\n\nтекст")
        h.current_lang = "ru"
        ef.EditorFormattingMixin.run_linter(h)
    finally:
        dt.show_document_audit = orig
    assert called == [h], called
    print("[PASS] test_run_linter_opens_audit")


# ─── convert_tools ───────────────────────────────────────────────────────────

class _FakeTaskThread:
    """Синхронный TaskThread: выполняет задачу и вызывает on_finish."""

    calls = []

    def __init__(self, fn, *args, **kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        _FakeTaskThread.calls.append(self)

    def start(self, on_finish=None, on_error=None, parent=None):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            if on_error:
                on_error(str(e))
            return self
        if on_finish:
            on_finish(result)
        return self


def _patch_task_thread():
    import src.gui.workers.task_worker as tw

    orig = tw.TaskThread
    tw.TaskThread = _FakeTaskThread
    _FakeTaskThread.calls = []
    return orig


def _restore_task_thread(orig):
    import src.gui.workers.task_worker as tw

    tw.TaskThread = orig


def test_pdf_to_markdown_cancel_noop():
    """Отмена выбора PDF ничего не делает."""
    orig = ct.QFileDialog
    ct.QFileDialog = types.SimpleNamespace(getOpenFileName=lambda *a, **k: ("", ""))
    try:
        h = FakeHost()
        ct.ConvertToolsMixin.pdf_to_markdown_convert(h)
    finally:
        ct.QFileDialog = orig
    assert h.logs == []
    assert h.previews == []
    print("[PASS] test_pdf_to_markdown_cancel_noop")


def test_pdf_to_markdown_converts():
    """Выбранный PDF конвертируется и результат попадает в редактор."""
    orig_dialog = ct.QFileDialog
    orig_thread = _patch_task_thread()
    try:
        with tempfile.TemporaryDirectory() as d:
            pdf_path = os.path.join(d, "doc.pdf")
            with open(pdf_path, "wb") as f:
                f.write(b"%PDF-1.4 fake")
            ct.QFileDialog = types.SimpleNamespace(
                getOpenFileName=lambda *a, **k: (pdf_path, "")
            )

            import src.core.pdf_to_markdown as p2m
            orig_conv = p2m.pdf_to_markdown
            p2m.pdf_to_markdown = lambda p: "# Из PDF\n"
            try:
                h = FakeHost()
                ct.ConvertToolsMixin.pdf_to_markdown_convert(h)
            finally:
                p2m.pdf_to_markdown = orig_conv
    finally:
        ct.QFileDialog = orig_dialog
        _restore_task_thread(orig_thread)
    assert h.live_editor.toPlainText() == "# Из PDF\n", h.live_editor.toPlainText()
    assert h.previews == ["render"]
    assert any("PDF -> Markdown" in log for log in h.logs), h.logs
    print("[PASS] test_pdf_to_markdown_converts")


def test_pdf_to_markdown_reports_error():
    """Ошибка конвертации показывается в QMessageBox."""
    orig_dialog = ct.QFileDialog
    orig_thread = _patch_task_thread()
    rec = _MsgBox().install(ct)
    try:
        with tempfile.TemporaryDirectory() as d:
            pdf_path = os.path.join(d, "doc.pdf")
            with open(pdf_path, "wb") as f:
                f.write(b"x")
            ct.QFileDialog = types.SimpleNamespace(
                getOpenFileName=lambda *a, **k: (pdf_path, "")
            )

            import src.core.pdf_to_markdown as p2m
            orig_conv = p2m.pdf_to_markdown

            def _boom(p):
                raise RuntimeError("сломалось")

            p2m.pdf_to_markdown = _boom
            try:
                h = FakeHost()
                ct.ConvertToolsMixin.pdf_to_markdown_convert(h)
            finally:
                p2m.pdf_to_markdown = orig_conv
    finally:
        ct.QFileDialog = orig_dialog
        _restore_task_thread(orig_thread)
        rec.restore(ct)
    assert "critical" in rec.kinds, rec.calls
    assert "сломалось" in rec.text_of()
    print("[PASS] test_pdf_to_markdown_reports_error")


def test_html_to_markdown_cancel_noop():
    """Отмена выбора HTML ничего не делает."""
    orig = ct.QFileDialog
    ct.QFileDialog = types.SimpleNamespace(getOpenFileName=lambda *a, **k: ("", ""))
    try:
        h = FakeHost()
        ct.ConvertToolsMixin.html_to_markdown_convert(h)
    finally:
        ct.QFileDialog = orig
    assert h.logs == []
    print("[PASS] test_html_to_markdown_cancel_noop")


def test_html_to_markdown_converts():
    """Выбранный HTML конвертируется в Markdown."""
    orig_dialog = ct.QFileDialog
    orig_thread = _patch_task_thread()
    try:
        with tempfile.TemporaryDirectory() as d:
            html_path = os.path.join(d, "doc.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write("<h1>Заголовок</h1>")
            ct.QFileDialog = types.SimpleNamespace(
                getOpenFileName=lambda *a, **k: (html_path, "")
            )
            h = FakeHost()
            ct.ConvertToolsMixin.html_to_markdown_convert(h)
    finally:
        ct.QFileDialog = orig_dialog
        _restore_task_thread(orig_thread)
    assert "Заголовок" in h.live_editor.toPlainText(), h.live_editor.toPlainText()
    assert any("HTML -> Markdown" in log for log in h.logs), h.logs
    print("[PASS] test_html_to_markdown_converts")


def test_run_ocr_cancel_noop():
    """Отмена выбора изображения для OCR ничего не делает."""
    orig = ct.QFileDialog
    ct.QFileDialog = types.SimpleNamespace(getOpenFileName=lambda *a, **k: ("", ""))
    try:
        h = FakeHost()
        ct.ConvertToolsMixin.run_ocr(h)
    finally:
        ct.QFileDialog = orig
    assert h.logs == []
    print("[PASS] test_run_ocr_cancel_noop")


def test_run_ocr_inserts_text():
    """Результат OCR вставляется в редактор."""
    orig_dialog = ct.QFileDialog
    orig_thread = _patch_task_thread()
    try:
        with tempfile.TemporaryDirectory() as d:
            img = os.path.join(d, "scan.png")
            with open(img, "wb") as f:
                f.write(b"png")
            ct.QFileDialog = types.SimpleNamespace(
                getOpenFileName=lambda *a, **k: (img, "")
            )
            import src.core.ocr_engine as ocr
            orig_ocr = ocr.image_to_markdown
            ocr.image_to_markdown = lambda p: "Распознанный текст"
            try:
                h = FakeHost()
                ct.ConvertToolsMixin.run_ocr(h)
            finally:
                ocr.image_to_markdown = orig_ocr
    finally:
        ct.QFileDialog = orig_dialog
        _restore_task_thread(orig_thread)
    assert "Распознанный текст" in h.live_editor.cursor.inserted, h.live_editor.cursor.inserted
    assert any("OCR completed" in log for log in h.logs), h.logs
    print("[PASS] test_run_ocr_inserts_text")


def test_ocr_image_to_text_delegates_to_run_ocr():
    """ocr_image_to_text вызывает run_ocr."""
    calls = []
    orig = ct.ConvertToolsMixin.run_ocr
    ct.ConvertToolsMixin.run_ocr = lambda self: calls.append(self)
    try:
        class _Host(FakeHost, ct.ConvertToolsMixin):
            pass

        h = _Host()
        ct.ConvertToolsMixin.ocr_image_to_text(h)
    finally:
        ct.ConvertToolsMixin.run_ocr = orig
    assert calls == [h], calls
    print("[PASS] test_ocr_image_to_text_delegates_to_run_ocr")


# ─── integrations ────────────────────────────────────────────────────────────

def test_show_watermark_designer_applies_result():
    """Принятый дизайн водяного знака применяется к полям."""
    import src.gui.watermark_designer as wd

    class _FakeDesigner:
        def __init__(self, *a, **k):
            self.text_input = _TextField("КОПИЯ")
            self.result_css = "  .wm { color: red; }  "

        def exec(self):
            return 1

    orig = wd.WatermarkDesignerDialog
    wd.WatermarkDesignerDialog = _FakeDesigner
    try:
        h = FakeHost()
        integ.IntegrationsMixin.show_watermark_designer(h)
    finally:
        wd.WatermarkDesignerDialog = orig
    assert h.footer_input.text == "КОПИЯ"
    assert h.watermark_css_input.text == ".wm { color: red; }"
    assert any("Watermark applied" in log for log in h.logs), h.logs
    print("[PASS] test_show_watermark_designer_applies_result")


def test_show_watermark_designer_cancel_keeps_fields():
    """Отмена диалога не меняет поля."""
    import src.gui.watermark_designer as wd

    class _FakeDesigner:
        def __init__(self, *a, **k):
            self.text_input = _TextField("КОПИЯ")
            self.result_css = "css"

        def exec(self):
            return 0

    orig = wd.WatermarkDesignerDialog
    wd.WatermarkDesignerDialog = _FakeDesigner
    try:
        h = FakeHost()
        integ.IntegrationsMixin.show_watermark_designer(h)
    finally:
        wd.WatermarkDesignerDialog = orig
    assert h.footer_input.text == ""
    assert h.watermark_css_input.text == ""
    print("[PASS] test_show_watermark_designer_cancel_keeps_fields")


def test_show_csv_editor_inserts_markdown():
    """Выбранный CSV вставляется в редактор как Markdown."""
    import src.gui.csv_editor as ce

    class _FakeDialog:
        def __init__(self, *a, **k):
            self.selected_markdown = "| a | b |\n|---|---|\n| 1 | 2 |"

        def exec(self):
            return 1

    orig = ce.CSVEditorDialog
    ce.CSVEditorDialog = _FakeDialog
    try:
        h = FakeHost()
        integ.IntegrationsMixin.show_csv_editor(h)
    finally:
        ce.CSVEditorDialog = orig
    assert h.live_editor.cursor.inserted, "Markdown должен быть вставлен"
    assert "| a | b |" in h.live_editor.cursor.inserted[0]
    assert h.previews == ["render"]
    print("[PASS] test_show_csv_editor_inserts_markdown")


def test_show_excalidraw_inserts_markdown():
    """Рисунок Excalidraw вставляется в редактор как Markdown."""
    import src.gui.excalidraw_canvas as ec

    class _FakeDialog:
        def __init__(self, *a, **k):
            self.selected_markdown = "![diagram](data:image/svg+xml;base64,AAA)"

        def exec(self):
            return 1

    orig = ec.ExcalidrawDialog
    ec.ExcalidrawDialog = _FakeDialog
    try:
        h = FakeHost()
        integ.IntegrationsMixin.show_excalidraw(h)
    finally:
        ec.ExcalidrawDialog = orig
    assert h.live_editor.cursor.inserted
    assert "diagram" in h.live_editor.cursor.inserted[0]
    print("[PASS] test_show_excalidraw_inserts_markdown")


def test_show_github_sync_requires_files():
    """Без открытых файлов диалог GitHub не показывается."""
    rec = _MsgBox().install(integ)
    try:
        h = FakeHost()
        integ.IntegrationsMixin.show_github_sync_dialog(h)
    finally:
        rec.restore(integ)
    assert "information" in rec.kinds, rec.calls
    assert "Open a folder first" in rec.text_of()
    print("[PASS] test_show_github_sync_requires_files")


def test_integrations_open_dialogs():
    """Диалоги интеграций открываются без ошибок."""
    import src.gui.calendar_view as cv
    import src.gui.pomodoro as pom
    import src.gui.dialogs as dlg_pkg

    created = []

    def _make_dialog(cls):
        class _D:
            def __init__(self, *a, **k):
                created.append(cls.__name__)

            def exec(self):
                return 0

            def close(self):
                pass

        return _D

    origs = {
        "calendar": (cv.CalendarNotesDialog, cv.CalendarNotesDialog),
        "pomodoro": (pom.PomodoroDialog, pom.PomodoroDialog),
    }
    try:
        cv.CalendarNotesDialog = _make_dialog(cv.CalendarNotesDialog)
        pom.PomodoroDialog = _make_dialog(pom.PomodoroDialog)

        h = FakeHost()
        with tempfile.TemporaryDirectory() as d:
            h.active_workspace_folder = d
            integ.IntegrationsMixin.show_calendar_notes(h)
            integ.IntegrationsMixin.show_pomodoro(h)
    finally:
        cv.CalendarNotesDialog = origs["calendar"][1]
        pom.PomodoroDialog = origs["pomodoro"][1]
    assert "CalendarNotesDialog" in created, created
    assert "PomodoroDialog" in created, created
    print("[PASS] test_integrations_open_dialogs")


# ─── workspace ───────────────────────────────────────────────────────────────

def test_process_wikilinks_resolves():
    """Wikilinks заменяются на обычные Markdown-ссылки."""
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "Note.md"), "w", encoding="utf-8") as f:
            f.write("# Note")
        h = FakeHost("См. [[Note]] и [[Missing]]")
        h.active_workspace_folder = d
        ws.WorkspaceMixin.process_wikilinks(h)
        text = h.live_editor.toPlainText()
        assert "[[Note]]" not in text, text
        assert "Note.md" in text, text
        assert h.previews == ["render"]
        assert any("Wiki links resolved" in log for log in h.logs), h.logs
    print("[PASS] test_process_wikilinks_resolves")


def test_apply_template_vars_substitutes():
    """Переменные шаблона подставляются в текст."""
    h = FakeHost("---\ntitle: Мой док\n---\n\n# {{title}}")
    ws.WorkspaceMixin.apply_template_vars(h)
    text = h.live_editor.toPlainText()
    assert "Мой док" in text, text
    assert "{{title}}" not in text, text
    assert h.previews == ["render"]
    assert h.toasts and h.toasts[-1][1] == "success", h.toasts
    print("[PASS] test_apply_template_vars_substitutes")


def test_workspace_delegates_to_file_manager():
    """Методы воркспейса делегируются в src.gui.file_manager."""
    import src.gui.file_manager as fm

    calls = []
    orig = {}
    for name in ("update_workspace_explorer", "open_output_folder",
                 "filter_workspace_explorer", "load_workspace_file"):
        orig[name] = getattr(fm, name)

        def _make(nm):
            def _f(window, *a, **k):
                calls.append((nm, window, a))
            return _f

        setattr(fm, name, _make(name))

    try:
        h = FakeHost()
        ws.WorkspaceMixin.update_workspace_explorer(h)
        ws.WorkspaceMixin.open_output_folder(h)
        ws.WorkspaceMixin.filter_workspace_explorer(h, "abc")
        ws.WorkspaceMixin.load_workspace_file(h, "ITEM")
    finally:
        for name, fn in orig.items():
            setattr(fm, name, fn)

    names = [c[0] for c in calls]
    assert names == [
        "update_workspace_explorer", "open_output_folder",
        "filter_workspace_explorer", "load_workspace_file",
    ], names
    assert all(c[1] is h for c in calls)
    print("[PASS] test_workspace_delegates_to_file_manager")


def test_restore_draft_delegates():
    """restore_draft_if_exists делегируется в document_tools."""
    import src.gui.document_tools as dt

    called = []
    orig = dt.restore_draft_if_exists
    dt.restore_draft_if_exists = lambda w: called.append(w)
    try:
        h = FakeHost()
        ws.WorkspaceMixin.restore_draft_if_exists(h)
    finally:
        dt.restore_draft_if_exists = orig
    assert called == [h], called
    print("[PASS] test_restore_draft_delegates")


def test_resize_event_adjusts_decorations():
    """resizeEvent двигает декорации (свечение и заголовок) при их наличии."""
    from PyQt6.QtGui import QResizeEvent
    from PyQt6.QtCore import QSize

    class _Rect:
        def __init__(self):
            self.geom = None

        def setGeometry(self, *a):
            self.geom = a

        def isVisible(self):
            return True

    h = FakeHost()
    h._glow = _Rect()
    h._titlebar = _Rect()
    h.resize(800, 600)

    event = QResizeEvent(QSize(800, 600), QSize(700, 500))
    ws.WorkspaceMixin.resizeEvent(h, event)
    assert h._glow.geom == (0, 0, 800, 600), h._glow.geom
    assert h._titlebar.geom == (0, 0, 800, 42), h._titlebar.geom
    print("[PASS] test_resize_event_adjusts_decorations")


def test_resize_event_without_decorations():
    """Без декораций resizeEvent не падает."""
    from PyQt6.QtGui import QResizeEvent
    from PyQt6.QtCore import QSize

    h = FakeHost()
    h.resize(640, 480)
    event = QResizeEvent(QSize(640, 480), QSize(600, 400))
    ws.WorkspaceMixin.resizeEvent(h, event)
    print("[PASS] test_resize_event_without_decorations")


def main():
    tests = [
        test_spell_check_no_words,
        test_spell_check_counts_long_words,
        test_spell_check_without_issues,
        test_convert_emoji_shortcodes,
        test_add_multi_cursor,
        test_editor_formatting_delegates_to_editor_commands,
        test_run_linter_opens_audit,
        test_pdf_to_markdown_cancel_noop,
        test_pdf_to_markdown_converts,
        test_pdf_to_markdown_reports_error,
        test_html_to_markdown_cancel_noop,
        test_html_to_markdown_converts,
        test_run_ocr_cancel_noop,
        test_run_ocr_inserts_text,
        test_ocr_image_to_text_delegates_to_run_ocr,
        test_show_watermark_designer_applies_result,
        test_show_watermark_designer_cancel_keeps_fields,
        test_show_csv_editor_inserts_markdown,
        test_show_excalidraw_inserts_markdown,
        test_show_github_sync_requires_files,
        test_integrations_open_dialogs,
        test_process_wikilinks_resolves,
        test_apply_template_vars_substitutes,
        test_workspace_delegates_to_file_manager,
        test_restore_draft_delegates,
        test_resize_event_adjusts_decorations,
        test_resize_event_without_decorations,
    ]
    for t in tests:
        t()
    print("\nAll mixin coverage tests (batch 2) passed!")


if __name__ == "__main__":
    main()
