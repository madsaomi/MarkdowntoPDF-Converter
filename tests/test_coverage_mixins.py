"""Поведенческие тесты миксинов с наименьшим покрытием (PLAN-013).

Покрывает:
- `mixins/view_dialogs.py` — история, LaTeX-превью, tag cloud, аналитика, граф, diff;
- `mixins/editor_tools.py` — статистика текста, цель, поиск, замена;
- `mixins/education.py` — карточки, Anki TSV, глоссарий, квиз.

Модальные диалоги подменяются неблокирующей версией QDialog, а QMessageBox —
заглушкой, записывающей вызовы.
"""
import os
import sys
import tempfile
import types

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QDialog, QTextBrowser, QWidget

app = QApplication.instance() or QApplication([])

import src.gui.mixins.editor_tools as et
import src.gui.mixins.education as edu
import src.gui.mixins.view_dialogs as vd


# ─── общие заглушки ──────────────────────────────────────────────────────────

class _MsgBoxRecorder:
    """Заглушка QMessageBox, записывающая вызовы."""

    def __init__(self):
        self.calls = []

    def _record(self, kind):
        def _fn(*args, **kwargs):
            self.calls.append((kind, args))
        return _fn

    def install(self, module):
        self._orig = module.QMessageBox
        holder = types.SimpleNamespace(
            information=self._record("information"),
            warning=self._record("warning"),
            critical=self._record("critical"),
            question=self._record("question"),
        )
        module.QMessageBox = holder
        return self

    def restore(self, module):
        module.QMessageBox = self._orig

    @property
    def kinds(self):
        return [c[0] for c in self.calls]

    def text_of(self, index=0):
        return self.calls[index][1][-1] if self.calls else ""


class _NonBlockingDialog(QDialog):
    """QDialog, у которого exec() не блокирует."""

    created = []

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        _NonBlockingDialog.created.append(self)

    def exec(self):
        return 0

    def browser_html(self):
        browsers = self.findChildren(QTextBrowser)
        return browsers[0].toHtml() if browsers else ""


def _patch_dialog(module):
    orig = module.QDialog
    module.QDialog = _NonBlockingDialog
    _NonBlockingDialog.created = []
    return orig


def _restore_dialog(module, orig):
    module.QDialog = orig


class _FakeTimer:
    def __init__(self):
        self.started = 0

    def start(self):
        self.started += 1


class _FakeLabel:
    def __init__(self):
        self.text = ""

    def setText(self, t):
        self.text = t


class _FakeCursor:
    MoveOperation = types.SimpleNamespace(Start="start")

    def __init__(self, text=""):
        self._text = text
        self.inserted = []
        self.moved = []

    def selectedText(self):
        return ""

    def insertText(self, s):
        self.inserted.append(s)
        self._text += s

    def movePosition(self, op, *a, **k):
        self.moved.append(op)
        return True


class _FakeEditor:
    def __init__(self, text=""):
        self._text = text
        self.cursor = _FakeCursor(text)
        self.find_calls = []
        self.find_result = True
        self.focused = False
        self.blocked = False
        self._scroll = 0

    def toPlainText(self):
        return self._text

    def setPlainText(self, t):
        self._text = t

    def textCursor(self):
        return self.cursor

    def setTextCursor(self, c):
        self.cursor = c

    def setFocus(self):
        self.focused = True

    def find(self, what):
        self.find_calls.append(what)
        return self.find_result

    def blockSignals(self, v):
        self.blocked = v

    def verticalScrollBar(self):
        class _SB:
            def __init__(self, e):
                self.e = e

            def value(self):
                return self.e._scroll

            def setValue(self, v):
                self.e._scroll = v

        return _SB(self)


class _FakeCheckbox:
    def __init__(self, checked=False):
        self._checked = checked

    def isChecked(self):
        return self._checked


class _FakeInput:
    def __init__(self, text=""):
        self._text = text
        self.focused = False
        self.selected_all = False

    def text(self):
        return self._text

    def setFocus(self):
        self.focused = True

    def selectAll(self):
        self.selected_all = True


class _FakePanel:
    def __init__(self):
        self.visible = False

    def isVisible(self):
        return self.visible

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False


class FakeHost(QWidget):
    """Фейковый хост MainWindow с необходимыми атрибутами.

    Наследуется от QWidget, чтобы его можно было передавать как родителя
    настоящим диалогам Qt.
    """

    def __init__(self, text="", lang="ru"):
        super().__init__()
        self.live_editor = _FakeEditor(text)
        self.current_lang = lang
        self.stats_label = _FakeLabel()
        self.preview_timer = _FakeTimer()
        self.writing_goal = 0
        self.goal_celebrated = False
        self.is_welcome_doc_active = True
        self.search_panel = _FakePanel()
        self.search_find_input = _FakeInput()
        self.search_replace_input = _FakeInput()
        self.search_regex_checkbox = _FakeCheckbox()
        self.logs = []
        self.toasts = []
        self.previews = []
        self.stats_calls = 0
        self.tabs = None
        self.history_container = None
        self.active_workspace_folder = None
        self.selected_files = []

    def append_log(self, msg):
        self.logs.append(msg)

    def toast(self, msg, kind="info"):
        self.toasts.append((msg, kind))

    def _render_live_preview(self):
        self.previews.append("render")

    def update_text_statistics(self):
        self.stats_calls += 1

    def update_export_history_ui(self):
        self.logs.append("history-ui")


# ─── view_dialogs ────────────────────────────────────────────────────────────

def test_show_conversion_history_switches_tab():
    """show_conversion_history обновляет историю и переключает вкладку."""
    calls = []

    class _Tabs:
        def setCurrentWidget(self, w):
            calls.append(w)

    h = FakeHost()
    h.tabs = _Tabs()
    h.history_container = "HISTORY"
    vd.ViewDialogsMixin.show_conversion_history(h)
    assert calls == ["HISTORY"], calls
    assert "history-ui" in h.logs
    print("[PASS] test_show_conversion_history_switches_tab")


def test_show_reading_analytics_computes_stats():
    """Аналитика считает слова, символы, предложения и индекс Флеша."""
    rec = _MsgBoxRecorder().install(vd)
    try:
        h = FakeHost("One two three. Four five six seven. Eight.")
        vd.ViewDialogsMixin.show_reading_analytics(h)
    finally:
        rec.restore(vd)
    assert "information" in rec.kinds, rec.calls
    msg = rec.text_of()
    assert "Words: 8" in msg, msg
    assert "Characters: 42" in msg, msg
    assert "Sentences: 3" in msg, msg
    assert "Flesch Score" in msg, msg
    print("[PASS] test_show_reading_analytics_computes_stats")


def test_show_reading_analytics_russian_vowels():
    """Для русского текста используются русские гласные."""
    rec = _MsgBoxRecorder().install(vd)
    try:
        h = FakeHost("Привет мир как дела сегодня хорошо", lang="ru")
        vd.ViewDialogsMixin.show_reading_analytics(h)
    finally:
        rec.restore(vd)
    msg = rec.text_of()
    assert "Words: 6" in msg, msg
    assert "Syllables:" in msg, msg
    print("[PASS] test_show_reading_analytics_russian_vowels")


def test_show_latex_preview_without_expressions():
    """Без LaTeX-выражений показывается информационное сообщение."""
    rec = _MsgBoxRecorder().install(vd)
    orig = _patch_dialog(vd)
    try:
        h = FakeHost("Просто текст без формул")
        vd.ViewDialogsMixin.show_latex_preview(h)
    finally:
        _restore_dialog(vd, orig)
        rec.restore(vd)
    assert "information" in rec.kinds, rec.calls
    assert "No LaTeX expressions" in rec.text_of()
    assert not _NonBlockingDialog.created, "диалог не должен создаваться"
    print("[PASS] test_show_latex_preview_without_expressions")


def test_show_latex_preview_with_expressions():
    """С LaTeX-выражениями создаётся диалог с картинками формул."""
    rec = _MsgBoxRecorder().install(vd)
    orig = _patch_dialog(vd)
    try:
        h = FakeHost("Формула $E=mc^2$ и ещё $\\alpha$")
        vd.ViewDialogsMixin.show_latex_preview(h)
    finally:
        _restore_dialog(vd, orig)
        rec.restore(vd)
    assert len(_NonBlockingDialog.created) == 1
    dlg = _NonBlockingDialog.created[0]
    html = dlg.browser_html()
    assert "LaTeX Preview (2 expressions)" in html, html
    assert "<img" in html
    assert "latex" in html.lower()
    dlg.close()
    print("[PASS] test_show_latex_preview_with_expressions")


def test_show_tag_cloud_counts_words():
    """Tag cloud считает слова длиной больше 3 и показывает частоты."""
    orig = _patch_dialog(vd)
    try:
        text = "alpha alpha alpha beta gamma delta epsilon zeta theta kappa lambda mu"
        h = FakeHost(text)
        vd.ViewDialogsMixin.show_tag_cloud(h)
    finally:
        _restore_dialog(vd, orig)
    dlg = _NonBlockingDialog.created[0]
    html = dlg.browser_html()
    assert "Tag Cloud" in html, html
    assert "alpha (3)" in html, html
    # Короткие слова не считаются
    assert ">mu<" not in html and "mu (" not in html, html
    dlg.close()
    print("[PASS] test_show_tag_cloud_counts_words")


def test_show_graph_view_builds_dialog():
    """Граф связей строится по рабочей папке и показывается в диалоге."""
    orig = _patch_dialog(vd)
    try:
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "A.md"), "w", encoding="utf-8") as f:
                f.write("[[B]]")
            with open(os.path.join(d, "B.md"), "w", encoding="utf-8") as f:
                f.write("b")
            h = FakeHost()
            h.active_workspace_folder = d
            vd.ViewDialogsMixin.show_graph_view(h)
    finally:
        _restore_dialog(vd, orig)
    dlg = _NonBlockingDialog.created[0]
    assert dlg.windowTitle() == "Graph View", dlg.windowTitle()
    # QTextBrowser пере-сериализует документ, поэтому проверяем наличие
    # содержимого, а не конкретный тег.
    html = dlg.browser_html()
    assert "graph" in html.lower(), html[:300]
    dlg.close()
    print("[PASS] test_show_graph_view_builds_dialog")


# ─── editor_tools ────────────────────────────────────────────────────────────

def test_on_editor_changed_resets_state():
    """on_editor_changed сбрасывает флаг приветствия и запускает таймер."""
    h = FakeHost()
    et.EditorToolsMixin.on_editor_changed(h)
    assert h.is_welcome_doc_active is False
    assert h.preview_timer.started == 1
    assert h.stats_calls == 1
    print("[PASS] test_on_editor_changed_resets_state")


def test_update_text_statistics_sets_label():
    """Статистика: слова, символы, время чтения."""
    h = FakeHost("одно два три четыре пять")
    et.EditorToolsMixin.update_text_statistics(h)
    text = h.stats_label.text
    assert "5 слов" in text, text
    assert "24 символов" in text, text
    assert "мин чтения" in text, text
    print("[PASS] test_update_text_statistics_sets_label")


def test_update_text_statistics_empty_text():
    """Для пустого текста время чтения равно нулю."""
    h = FakeHost("")
    et.EditorToolsMixin.update_text_statistics(h)
    text = h.stats_label.text
    assert "0 слов" in text, text
    assert "~0 мин чтения" in text, text
    print("[PASS] test_update_text_statistics_empty_text")


def test_update_text_statistics_with_goal():
    """Цель показывается процентом и вызывает поздравление при достижении."""
    rec = _MsgBoxRecorder().install(et)
    try:
        h = FakeHost("одно два три четыре пять")
        h.writing_goal = 5
        et.EditorToolsMixin.update_text_statistics(h)
    finally:
        rec.restore(et)
    assert "🎯 100%" in h.stats_label.text, h.stats_label.text
    assert "information" in rec.kinds, rec.calls
    assert h.goal_celebrated is True
    print("[PASS] test_update_text_statistics_with_goal")


def test_update_text_statistics_goal_not_reached():
    """Цель не достигнута — поздравления нет, процент меньше 100."""
    rec = _MsgBoxRecorder().install(et)
    try:
        h = FakeHost("одно два")
        h.writing_goal = 10
        et.EditorToolsMixin.update_text_statistics(h)
    finally:
        rec.restore(et)
    assert "🎯 20%" in h.stats_label.text, h.stats_label.text
    assert not rec.calls, rec.calls
    print("[PASS] test_update_text_statistics_goal_not_reached")


def test_toggle_search_panel_shows_and_hides():
    """Панель поиска показывается и скрывается, фокус переходит на ввод."""
    h = FakeHost()
    et.EditorToolsMixin.toggle_search_panel(h)
    assert h.search_panel.visible is True
    assert h.search_find_input.focused is True
    assert h.search_find_input.selected_all is True

    h.search_panel.visible = True
    et.EditorToolsMixin.toggle_search_panel(h)
    assert h.search_panel.visible is False
    assert h.live_editor.focused is True
    print("[PASS] test_toggle_search_panel_shows_and_hides")


def test_search_next_finds_and_wraps():
    """Поиск находит текст; при неудаче курсор возвращается в начало."""
    h = FakeHost("find me")
    h.search_find_input = _FakeInput("find")
    et.EditorToolsMixin.search_next(h)
    assert h.live_editor.find_calls == ["find"], h.live_editor.find_calls

    h2 = FakeHost("text")
    h2.search_find_input = _FakeInput("absent")
    h2.live_editor.find_result = False
    et.EditorToolsMixin.search_next(h2)
    assert h2.live_editor.find_calls == ["absent", "absent"], h2.live_editor.find_calls
    print("[PASS] test_search_next_finds_and_wraps")


def test_search_next_empty_query_noop():
    """Пустой запрос ничего не ищет."""
    h = FakeHost("text")
    h.search_find_input = _FakeInput("")
    et.EditorToolsMixin.search_next(h)
    assert h.live_editor.find_calls == []
    print("[PASS] test_search_next_empty_query_noop")


def test_replace_all_occurrences_plain():
    """Обычная замена заменяет все вхождения."""
    h = FakeHost("a a a")
    h.search_find_input = _FakeInput("a")
    h.search_replace_input = _FakeInput("b")
    et.EditorToolsMixin.replace_all_occurrences(h)
    assert h.live_editor.toPlainText() == "b b b", h.live_editor.toPlainText()
    assert h.previews == ["render"]
    assert h.stats_calls == 1
    print("[PASS] test_replace_all_occurrences_plain")


def test_replace_all_occurrences_regex():
    """Режим регулярных выражений заменяет по шаблону."""
    h = FakeHost("a1 b2 c3")
    h.search_find_input = _FakeInput(r"\d")
    h.search_replace_input = _FakeInput("#")
    h.search_regex_checkbox = _FakeCheckbox(True)
    et.EditorToolsMixin.replace_all_occurrences(h)
    assert h.live_editor.toPlainText() == "a# b# c#", h.live_editor.toPlainText()
    print("[PASS] test_replace_all_occurrences_regex")


def test_replace_all_occurrences_invalid_regex():
    """Некорректное выражение — сообщение об ошибке, текст не меняется."""
    rec = _MsgBoxRecorder().install(et)
    try:
        h = FakeHost("unchanged")
        h.search_find_input = _FakeInput("[unclosed")
        h.search_replace_input = _FakeInput("x")
        h.search_regex_checkbox = _FakeCheckbox(True)
        et.EditorToolsMixin.replace_all_occurrences(h)
    finally:
        rec.restore(et)
    assert "critical" in rec.kinds, rec.calls
    assert h.live_editor.toPlainText() == "unchanged"
    print("[PASS] test_replace_all_occurrences_invalid_regex")


def test_replace_all_occurrences_empty_query_noop():
    """Пустой запрос — замена не выполняется."""
    h = FakeHost("unchanged")
    h.search_find_input = _FakeInput("")
    h.search_replace_input = _FakeInput("x")
    et.EditorToolsMixin.replace_all_occurrences(h)
    assert h.live_editor.toPlainText() == "unchanged"
    assert h.previews == []
    print("[PASS] test_replace_all_occurrences_empty_query_noop")


# ─── education ───────────────────────────────────────────────────────────────

def test_generate_flashcards_without_headings():
    """Без заголовков карточки не создаются — информационное сообщение."""
    rec = _MsgBoxRecorder().install(edu)
    orig = _patch_dialog(edu)
    try:
        h = FakeHost("просто текст без заголовков")
        edu.EducationMixin.generate_flashcards(h)
    finally:
        _restore_dialog(edu, orig)
        rec.restore(edu)
    assert "information" in rec.kinds, rec.calls
    assert "No headings found" in rec.text_of()
    assert not _NonBlockingDialog.created
    print("[PASS] test_generate_flashcards_without_headings")


def test_generate_flashcards_with_headings():
    """С заголовками создаётся диалог со списком карточек."""
    orig = _patch_dialog(edu)
    try:
        h = FakeHost("# Вопрос 1\nОтвет 1\n\n# Вопрос 2\nОтвет 2")
        edu.EducationMixin.generate_flashcards(h)
    finally:
        _restore_dialog(edu, orig)
    dlg = _NonBlockingDialog.created[0]
    assert "2 cards" in dlg.windowTitle(), dlg.windowTitle()
    html = dlg.browser_html()
    assert "Вопрос 1" in html, html
    dlg.close()
    print("[PASS] test_generate_flashcards_with_headings")


def test_save_anki_tsv_writes_file():
    """Сохранение Anki TSV пишет файл и показывает toast."""
    orig = edu.QFileDialog
    edu.QFileDialog = types.SimpleNamespace(
        getSaveFileName=lambda *a, **k: ("C:/out/cards.tsv", "")
    )
    try:
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "cards.tsv")
            edu.QFileDialog = types.SimpleNamespace(
                getSaveFileName=lambda *a, **k: (path, "")
            )
            h = FakeHost()
            edu.EducationMixin._save_anki_tsv(
                h, [{"front": "Вопрос", "back": "Ответ"}]
            )
            assert os.path.isfile(path)
            content = open(path, encoding="utf-8").read()
            assert "Вопрос" in content and "Ответ" in content, content
            assert h.toasts and h.toasts[-1][1] == "success", h.toasts
    finally:
        edu.QFileDialog = orig
    print("[PASS] test_save_anki_tsv_writes_file")


def test_save_anki_tsv_cancel_no_write():
    """Отмена сохранения не создаёт файл."""
    orig = edu.QFileDialog
    try:
        edu.QFileDialog = types.SimpleNamespace(
            getSaveFileName=lambda *a, **k: ("", "")
        )
        h = FakeHost()
        edu.EducationMixin._save_anki_tsv(
            h, [{"front": "Вопрос", "back": "Ответ"}]
        )
        assert not h.toasts, h.toasts
    finally:
        edu.QFileDialog = orig
    print("[PASS] test_save_anki_tsv_cancel_no_write")


def test_build_glossary_without_definitions():
    """Без определений глоссарий не строится."""
    rec = _MsgBoxRecorder().install(edu)
    try:
        h = FakeHost("просто текст")
        edu.EducationMixin.build_glossary(h)
    finally:
        rec.restore(edu)
    assert "information" in rec.kinds, rec.calls
    assert "No definitions found" in rec.text_of()
    assert h.previews == []
    print("[PASS] test_build_glossary_without_definitions")


def test_build_glossary_inserts_markdown():
    """Глоссарий вставляется в редактор как Markdown."""
    h = FakeHost("**Термин**: определение")
    edu.EducationMixin.build_glossary(h)
    assert h.live_editor.cursor.inserted, "текст должен быть вставлен"
    inserted = h.live_editor.cursor.inserted[0]
    assert "Термин" in inserted, inserted
    assert h.previews == ["render"]
    assert h.logs and "Glossary built" in h.logs[0], h.logs
    print("[PASS] test_build_glossary_inserts_markdown")


def test_generate_quiz_not_enough_content():
    """Слишком мало содержимого — квиз не создаётся."""
    rec = _MsgBoxRecorder().install(edu)
    orig = _patch_dialog(edu)
    try:
        h = FakeHost("слово")
        edu.EducationMixin.generate_quiz(h)
    finally:
        _restore_dialog(edu, orig)
        rec.restore(edu)
    assert "information" in rec.kinds, rec.calls
    assert "Not enough content" in rec.text_of()
    assert not _NonBlockingDialog.created
    print("[PASS] test_generate_quiz_not_enough_content")


def test_generate_quiz_with_content():
    """При достаточном содержимом создаётся диалог квиза."""
    orig = _patch_dialog(edu)
    try:
        text = "\n\n".join(f"Предложение номер {i} с разными словами для теста." for i in range(12))
        h = FakeHost(text)
        edu.EducationMixin.generate_quiz(h)
    finally:
        _restore_dialog(edu, orig)
    assert _NonBlockingDialog.created, "диалог квиза должен быть создан"
    dlg = _NonBlockingDialog.created[0]
    assert "Quiz" in dlg.windowTitle(), dlg.windowTitle()
    dlg.close()
    print("[PASS] test_generate_quiz_with_content")


def main():
    tests = [
        test_show_conversion_history_switches_tab,
        test_show_reading_analytics_computes_stats,
        test_show_reading_analytics_russian_vowels,
        test_show_latex_preview_without_expressions,
        test_show_latex_preview_with_expressions,
        test_show_tag_cloud_counts_words,
        test_show_graph_view_builds_dialog,
        test_on_editor_changed_resets_state,
        test_update_text_statistics_sets_label,
        test_update_text_statistics_empty_text,
        test_update_text_statistics_with_goal,
        test_update_text_statistics_goal_not_reached,
        test_toggle_search_panel_shows_and_hides,
        test_search_next_finds_and_wraps,
        test_search_next_empty_query_noop,
        test_replace_all_occurrences_plain,
        test_replace_all_occurrences_regex,
        test_replace_all_occurrences_invalid_regex,
        test_replace_all_occurrences_empty_query_noop,
        test_generate_flashcards_without_headings,
        test_generate_flashcards_with_headings,
        test_save_anki_tsv_writes_file,
        test_save_anki_tsv_cancel_no_write,
        test_build_glossary_without_definitions,
        test_build_glossary_inserts_markdown,
        test_generate_quiz_not_enough_content,
        test_generate_quiz_with_content,
    ]
    for t in tests:
        t()
    print("\nAll mixin coverage tests passed!")


if __name__ == "__main__":
    main()
