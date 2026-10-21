"""Поведенческие тесты: рендерер HTML, AI-инструменты, TTS, document_ops, справка.

Завершающий пакет роста покрытия (PLAN-013, этап 4). Покрывает:
- `core/renderer.py` — `render_html` со всеми опциями, кэш CSS, санитизация;
- `core/html_builder.py` — основной путь и fallback;
- `mixins/ai_tools.py` — улучшение текста, генерация плана, голосовой ввод;
- `mixins/tts_media.py` — озвучка, диалог настроек TTS;
- `mixins/document_ops.py` — переход к строке, шаблоны документа, делегаты;
- `mixins/help_dialogs.py` — диалоги справки.
"""
import os
import sys
import tempfile
import types

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QDialog, QTextBrowser, QWidget

app = QApplication.instance() or QApplication([])

import src.core.html_builder as hb
import src.core.renderer as rend
import src.gui.mixins.ai_tools as ai
import src.gui.mixins.document_ops as dops
import src.gui.mixins.help_dialogs as helpdlg
import src.gui.mixins.tts_media as tts
from src.config import AppConfig


# ─── общие заглушки ──────────────────────────────────────────────────────────

class _MsgBox:
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


class _NonBlockingDialog(QDialog):
    created = []

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        _NonBlockingDialog.created.append(self)

    def exec(self):
        return 0


def _patch_dialog(module):
    orig = module.QDialog
    module.QDialog = _NonBlockingDialog
    _NonBlockingDialog.created = []
    return orig


def _restore_dialog(module, orig):
    module.QDialog = orig


class _Cursor:
    MoveOperation = types.SimpleNamespace(
        Start="start", Down="down", StartOfLine="sol", EndOfLine="eol"
    )
    MoveMode = types.SimpleNamespace(KeepAnchor="keep")

    def __init__(self, selected=""):
        self._selected = selected
        self.inserted = []
        self.moved = []

    def selectedText(self):
        return self._selected

    def insertText(self, s):
        self.inserted.append(s)

    def movePosition(self, op, *a, **k):
        self.moved.append(op)
        return True


class _Editor:
    def __init__(self, text="", selected=""):
        self._text = text
        self.cursor = _Cursor(selected)
        self.focused = False

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


class FakeHost(QWidget):
    def __init__(self, text="", lang="ru"):
        super().__init__()
        self.live_editor = _Editor(text)
        self.current_lang = lang
        self.logs = []
        self.toasts = []
        self.previews = []

    def append_log(self, msg):
        self.logs.append(msg)

    def toast(self, msg, kind="info"):
        self.toasts.append((msg, kind))

    def update_preview_from_editor(self):
        self.previews.append("preview")

    def _render_live_preview(self):
        self.previews.append("render")

    def tr_msg(self, key, *args):
        table = {
            "doc_templates_title": "Шаблоны документов",
            "doc_templates_label": "Выберите шаблон:",
        }
        text = table.get(key, key)
        return text % args if args else text


# ─── core/renderer.py ────────────────────────────────────────────────────────

def test_render_html_includes_content_and_theme():
    """render_html подставляет содержимое и CSS темы в шаблон."""
    r = rend.PDFRenderer(AppConfig.template_dir(), "")
    html = r.render_html("<h1>Заголовок</h1>", {"title": "Док"})
    assert "<h1>Заголовок</h1>" in html, html[:300]
    assert "<html" in html.lower()
    # CSS темы подключён
    assert "body" in html.lower()
    print("[PASS] test_render_html_includes_content_and_theme")


def test_render_html_caches_css():
    """_read_css кэширует содержимое файла темы."""
    r = rend.PDFRenderer(AppConfig.template_dir(), "")
    first = r._read_css("theme_modern.css")
    assert first
    assert r._read_css("theme_modern.css") is first, "CSS должен кэшироваться"
    print("[PASS] test_render_html_caches_css")


def test_render_html_footer_variables():
    """Переменные {date}, {time}, {filename}, {title}, {word_count} подставляются."""
    with tempfile.TemporaryDirectory() as d:
        md = os.path.join(d, "report.md")
        with open(md, "w", encoding="utf-8") as f:
            f.write("# Отчёт")
        r = rend.PDFRenderer(AppConfig.template_dir(), "")
        html = r.render_html(
            "<p>тест</p>", {"title": "Мой отчёт"},
            footer_text="{date} {time} {filename} {title} {word_count}",
            input_filepath=md, word_count=42,
        )
        assert "{date}" not in html, "переменная не подставлена"
        assert "{filename}" not in html
        assert "{title}" not in html
        assert "{word_count}" not in html
        assert "report.md" in html
        assert "42" in html
    print("[PASS] test_render_html_footer_variables")


def test_render_html_custom_css_is_embedded():
    """Пользовательский CSS подключается в итоговый документ."""
    with tempfile.TemporaryDirectory() as d:
        css = os.path.join(d, "custom.css")
        with open(css, "w", encoding="utf-8") as f:
            f.write(".my-marker { color: #ff0000; }")
        r = rend.PDFRenderer(AppConfig.template_dir(), "")
        html = r.render_html("<p>x</p>", {"title": "T"}, custom_css_path=css)
        assert "my-marker" in html, html[:500]
    print("[PASS] test_render_html_custom_css_is_embedded")


def test_render_html_missing_custom_css_is_ignored():
    """Отсутствующий файл пользовательского CSS не ломает рендер."""
    r = rend.PDFRenderer(AppConfig.template_dir(), "")
    html = r.render_html(
        "<p>x</p>", {"title": "T"},
        custom_css_path="/definitely/not/exists.css",
    )
    assert "<html" in html.lower()
    print("[PASS] test_render_html_missing_custom_css_is_ignored")


def test_render_html_sanitizes_watermark_and_footer():
    """Водяной знак и колонтитул очищаются от управляющих символов.

    Раньше в шаблон передавался неочищенный `resolved_footer` — текст
    колонтитула попадал в CSS-строку `content: "..."` как есть, что позволяло
    вырваться из неё инъекцией произвольных CSS-правил (BUG_008).
    """
    r = rend.PDFRenderer(AppConfig.template_dir(), "")
    html = r.render_html(
        "<p>x</p>", {"title": "T"},
        watermark="WM\x00\x07",
        footer_text="Footer\x00\x07",
    )
    assert "\x00" not in html, "нулевые символы должны быть вырезаны"
    assert "\x07" not in html, "управляющие символы должны быть вырезаны"
    assert "WM" in html
    assert "Footer" in html
    print("[PASS] test_render_html_sanitizes_watermark_and_footer")


def test_render_html_footer_cannot_break_out_of_css():
    """Колонтитул не может вырваться из CSS-строки content: "..."."""
    r = rend.PDFRenderer(AppConfig.template_dir(), "")
    payload = 'X"; } body { background-image: url("http://evil/x.png"); } .z { content: "'
    html = r.render_html("<p>x</p>", {"title": "T"}, footer_text=payload)

    # Опасные символы, ломающие CSS-правило, вырезаны.
    # Внутри кавычек безобидны «;» и «:», но закрывающая кавычка и
    # фигурные скобки вырвали бы новые правила — их быть не должно.
    body = html.split("@bottom-center")[1] if "@bottom-center" in html else html
    content_line = next(
        (ln for ln in body.split("\n") if "content:" in ln), ""
    )
    inner = content_line.split('content: "', 1)[-1].rsplit('"', 1)[0]
    for bad in ('"', "{", "}"):
        assert bad not in inner, (bad, inner)
    # Инъекция осталась внутри строки и не создала отдельного CSS-правила:
    # строка с payload — та же самая строка content:, и она закрыта кавычкой.
    payload_lines = [ln for ln in html.split("\n") if "evil" in ln]
    assert len(payload_lines) == 1, payload_lines
    assert payload_lines[0].strip().startswith("content: "), payload_lines[0]
    assert payload_lines[0].strip().endswith('";'), payload_lines[0]
    print("[PASS] test_render_html_footer_cannot_break_out_of_css")


def test_render_html_watermark_css_and_margins():
    """CSS водяного знака и поля страницы попадают в документ."""
    r = rend.PDFRenderer(AppConfig.template_dir(), "")
    html = r.render_html(
        "<p>x</p>", {"title": "T"},
        watermark_css=".watermark { color: red; }",
        margins="20mm",
        page_numbers=True,
        page_num_format="dash",
    )
    assert "watermark" in html.lower()
    assert "20mm" in html
    print("[PASS] test_render_html_watermark_css_and_margins")


def test_render_html_english_pagination():
    """В английской локали подписи страниц меняются."""
    r = rend.PDFRenderer(AppConfig.template_dir(), "")
    html_ru = r.render_html("<p>x</p>", {"title": "T"}, lang="ru",
                             page_numbers=True, page_num_format="text")
    html_en = r.render_html("<p>x</p>", {"title": "T"}, lang="en",
                             page_numbers=True, page_num_format="text")
    assert "Страница" in html_ru, html_ru[-500:]
    assert "Page" in html_en
    print("[PASS] test_render_html_english_pagination")


# ─── core/html_builder.py ────────────────────────────────────────────────────

def test_html_builder_builds_full_document():
    """HtmlBuilder возвращает полноценный HTML-документ."""
    b = hb.HtmlBuilder()
    html = b.build_html("<h1>Док</h1>", {"title": "Док"})
    assert "<h1>Док</h1>" in html
    assert "<html" in html.lower()
    print("[PASS] test_html_builder_builds_full_document")


def test_html_builder_fallback_when_renderer_fails():
    """Если PDFRenderer падает, используется запасной минимальный рендер."""
    orig = rend.PDFRenderer

    def _boom(*a, **k):
        raise RuntimeError("сломалось")

    rend.PDFRenderer = _boom
    try:
        b = hb.HtmlBuilder()
        html = b.build_html("<h1>Док</h1>", {"title": "Док"})
    finally:
        rend.PDFRenderer = orig
    assert "<h1>Док</h1>" in html, html[:300]
    assert "<html" in html.lower()
    print("[PASS] test_html_builder_fallback_when_renderer_fails")


def test_html_builder_module_level_helper():
    """Функция build_html_for_preview_and_export работает."""
    from src.core.html_builder import build_html_for_preview_and_export

    html = build_html_for_preview_and_export("<p>текст</p>", metadata={"title": "T"})
    assert "<p>текст</p>" in html
    assert "<html" in html.lower()
    print("[PASS] test_html_builder_module_level_helper")


# ─── mixins/ai_tools.py ──────────────────────────────────────────────────────

def test_ai_improve_text_without_suggestions_normalizes():
    """Без подсказок текст нормализуется и вставляется в редактор."""
    rec = _MsgBox().install(ai)
    import src.core.ai_assistant as aia

    orig_get = aia.get_ai_assistant
    aia.get_ai_assistant = lambda: types.SimpleNamespace(analyze=lambda t, l: [])
    try:
        h = FakeHost()
        h.live_editor.cursor = _Cursor("  много   пробелов  ")
        ai.AiToolsMixin.ai_improve_text(h)
    finally:
        aia.get_ai_assistant = orig_get
        rec.restore(ai)
    assert h.live_editor.cursor.inserted == ["много пробелов"], h.live_editor.cursor.inserted
    assert h.toasts and h.toasts[-1][1] == "success", h.toasts
    print("[PASS] test_ai_improve_text_without_suggestions_normalizes")


def test_ai_improve_text_with_suggestions_shows_dialog():
    """При наличии подсказок показывается список рекомендаций."""
    rec = _MsgBox().install(ai)
    import src.core.ai_assistant as aia

    class _Sug:
        def __init__(self, category, explanation):
            self.category = category
            self.explanation = explanation

    orig_get = aia.get_ai_assistant
    aia.get_ai_assistant = lambda: types.SimpleNamespace(
        analyze=lambda t, l: [_Sug("Стиль", "Используйте простые предложения")]
    )
    try:
        h = FakeHost()
        h.live_editor.cursor = _Cursor("текст")
        ai.AiToolsMixin.ai_improve_text(h)
    finally:
        aia.get_ai_assistant = orig_get
        rec.restore(ai)
    assert rec.kinds == ["information"], rec.calls
    msg = rec.text_of()
    assert "Стиль" in msg, msg
    assert "простые предложения" in msg, msg
    assert h.live_editor.cursor.inserted == [], "текст не меняется при подсказках"
    print("[PASS] test_ai_improve_text_with_suggestions_shows_dialog")


def test_ai_generate_outline_inserts_structure():
    """Генерация плана вставляет структуру в редактор."""
    import src.core.ai_assistant as aia

    orig_get = aia.get_ai_assistant
    aia.get_ai_assistant = lambda: types.SimpleNamespace(
        generate_outline=lambda text, lang: "1. Введение\n2. Заключение"
    )
    try:
        h = FakeHost("текст")
        ai.AiToolsMixin.ai_generate_outline(h)
    finally:
        aia.get_ai_assistant = orig_get
    assert h.live_editor.cursor.inserted, "план должен быть вставлен"
    assert "Введение" in h.live_editor.cursor.inserted[0]
    print("[PASS] test_ai_generate_outline_inserts_structure")


def test_start_voice_input_reports_missing_dependency():
    """Без SpeechRecognition показывается подсказка об установке."""
    rec = _MsgBox().install(ai)
    import src.gui.workers.task_worker as tw

    orig = tw.TaskThread

    class _FailThread:
        def __init__(self, fn, *a, **k):
            raise ImportError("No module named 'speech_recognition'")

    tw.TaskThread = _FailThread
    try:
        h = FakeHost()
        ai.AiToolsMixin.start_voice_input(h)
    finally:
        tw.TaskThread = orig
        rec.restore(ai)
    assert "information" in rec.kinds, rec.calls
    assert "SpeechRecognition" in rec.text_of()
    print("[PASS] test_start_voice_input_reports_missing_dependency")


# ─── mixins/tts_media.py ─────────────────────────────────────────────────────

def test_text_to_speech_stops_playing_engine():
    """Если движок уже играет — он останавливается."""
    import src.core.tts_engine as te

    class _Engine:
        def __init__(self):
            self.stopped = False
            self.spoke = False

        def set_on_state_change(self, cb):
            pass

        def is_playing(self):
            return True

        def stop(self):
            self.stopped = True

        def speak(self, *a, **k):
            self.spoke = True

    engine = _Engine()
    orig_get = te.get_tts_engine
    orig_strip = te.strip_markdown_for_tts
    te.get_tts_engine = lambda: engine
    te.strip_markdown_for_tts = lambda t: "чисто"
    try:
        h = FakeHost("текст")
        tts.TtsMediaMixin.text_to_speech_speak(h)
    finally:
        te.get_tts_engine = orig_get
        te.strip_markdown_for_tts = orig_strip
    assert engine.stopped is True
    assert engine.spoke is False
    assert h.toasts and h.toasts[-1][0] == "TTS stopped", h.toasts
    print("[PASS] test_text_to_speech_stops_playing_engine")


def test_text_to_speech_speaks_when_idle():
    """Если движок не играет — произносится текст."""
    import src.core.tts_engine as te

    class _Engine:
        def __init__(self):
            self.spoke = None

        def set_on_state_change(self, cb):
            pass

        def is_playing(self):
            return False

        def stop(self):
            pass

        def speak(self, text, lang=None):
            self.spoke = (text, lang)

    engine = _Engine()
    orig_get = te.get_tts_engine
    orig_strip = te.strip_markdown_for_tts
    te.get_tts_engine = lambda: engine
    te.strip_markdown_for_tts = lambda t: "чистый текст"
    try:
        h = FakeHost("текст")
        tts.TtsMediaMixin.text_to_speech_speak(h)
    finally:
        te.get_tts_engine = orig_get
        te.strip_markdown_for_tts = orig_strip
    assert engine.spoke == ("чистый текст", "ru"), engine.spoke
    assert h.toasts and h.toasts[-1][1] == "success", h.toasts
    print("[PASS] test_text_to_speech_speaks_when_idle")


def test_show_tts_settings_builds_dialog():
    """Диалог настроек TTS строится со списком голосов."""
    import src.core.tts_engine as te

    class _Voice:
        def __init__(self):
            self.name = "Voice"
            self.language = "ru"
            self.id = "v1"
            self.description = "desc"
            self.gender = types.SimpleNamespace(value="female")
            self.is_premium = False

    class _Settings:
        def __init__(self):
            self.speed = 1.0
            self.pitch = 1.0
            self.volume = 1.0
            self.voice_id = None
            self.pause_between_paragraphs = 0.5

    class _Engine:
        def __init__(self):
            self.settings = _Settings()

        def get_voices(self):
            return [_Voice()]

    orig_get = te.get_tts_engine
    te.get_tts_engine = lambda: _Engine()
    orig = _patch_dialog(tts)
    try:
        h = FakeHost()
        tts.TtsMediaMixin.show_tts_settings(h)
    finally:
        _restore_dialog(tts, orig)
        te.get_tts_engine = orig_get
    assert len(_NonBlockingDialog.created) == 1
    dlg = _NonBlockingDialog.created[0]
    assert dlg.windowTitle() == "TTS Settings", dlg.windowTitle()
    dlg.close()
    print("[PASS] test_show_tts_settings_builds_dialog")


# ─── mixins/document_ops.py ──────────────────────────────────────────────────

def test_goto_editor_line_moves_cursor():
    """Переход к строке двигает курсор и выделяет строку."""
    h = FakeHost()
    dops.DocumentOpsMixin.goto_editor_line(h, 3)
    moved = h.live_editor.cursor.moved
    assert dops.DocumentOpsMixin is not None
    assert "down" in moved, moved
    assert "sol" in moved, moved
    assert "eol" in moved, moved
    assert h.live_editor.focused is True
    print("[PASS] test_goto_editor_line_moves_cursor")


def test_show_doc_templates_dialog_loads_chosen():
    """Выбранный шаблон документа загружается в редактор."""
    orig = dops.QInputDialog
    dops.QInputDialog = types.SimpleNamespace(
        getItem=lambda *a, **k: ("📝 Заметки / Notes", True)
    )
    try:
        h = FakeHost()
        dops.DocumentOpsMixin.show_doc_templates_dialog(h)
    finally:
        dops.QInputDialog = orig
    assert h.live_editor.toPlainText(), "шаблон должен быть вставлен"
    assert "Мои заметки" in h.live_editor.toPlainText(), h.live_editor.toPlainText()[:200]
    assert h.previews == ["preview"]
    print("[PASS] test_show_doc_templates_dialog_loads_chosen")


def test_show_doc_templates_dialog_cancel_keeps_text():
    """Отмена выбора шаблона не меняет редактор."""
    orig = dops.QInputDialog
    dops.QInputDialog = types.SimpleNamespace(
        getItem=lambda *a, **k: ("", False)
    )
    try:
        h = FakeHost("исходный")
        dops.DocumentOpsMixin.show_doc_templates_dialog(h)
    finally:
        dops.QInputDialog = orig
    assert h.live_editor.toPlainText() == "исходный"
    print("[PASS] test_show_doc_templates_dialog_cancel_keeps_text")


def test_document_ops_delegates_to_document_tools():
    """Методы document_ops делегируются в document_tools и file_manager."""
    calls = []
    orig = {}
    for mod, name in (
        (dops.document_tools, "autosave_draft"),
        (dops.document_tools, "save_revision"),
        (dops.document_tools, "show_revision_history"),
        (dops.document_tools, "show_document_audit"),
        (dops.document_tools, "auto_fix_document_issues"),
        (dops.file_manager, "save_current_workspace_file"),
    ):
        orig[(mod, name)] = getattr(mod, name)

        def _make(nm):
            def _f(window, *a, **k):
                calls.append(nm)
            return _f

        setattr(mod, name, _make(name))

    try:
        h = FakeHost()
        dops.DocumentOpsMixin.autosave_draft(h)
        dops.DocumentOpsMixin.save_revision(h)
        dops.DocumentOpsMixin.show_revision_history(h)
        dops.DocumentOpsMixin.show_document_audit(h)
        dops.DocumentOpsMixin.auto_fix_document_issues(h)
        dops.DocumentOpsMixin.save_current_workspace_file(h)
    finally:
        for (mod, name), fn in orig.items():
            setattr(mod, name, fn)

    assert calls == [
        "autosave_draft", "save_revision", "show_revision_history",
        "show_document_audit", "auto_fix_document_issues",
        "save_current_workspace_file",
    ], calls
    print("[PASS] test_document_ops_delegates_to_document_tools")


# ─── mixins/help_dialogs.py ──────────────────────────────────────────────────

def test_help_dialogs_open():
    """Диалоги справки (about, шорткаты, приветственный тур) открываются."""
    import src.gui.about_dialog as ad
    import src.gui.welcome_tour as wt
    import src.gui.dialogs as dlg_pkg

    created = []

    def _make(cls):
        class _D:
            def __init__(self, *a, **k):
                created.append(cls.__name__)

            def exec(self):
                return 0

        return _D

    orig_about = ad.AboutDialog
    orig_tour = wt.WelcomeTourDialog
    orig_shortcuts = dlg_pkg.ShortcutsDialog
    try:
        ad.AboutDialog = _make(ad.AboutDialog)
        wt.WelcomeTourDialog = _make(wt.WelcomeTourDialog)
        dlg_pkg.ShortcutsDialog = _make(dlg_pkg.ShortcutsDialog)

        h = FakeHost()
        helpdlg.HelpDialogsMixin.show_about(h)
        helpdlg.HelpDialogsMixin.show_shortcuts(h)
        helpdlg.HelpDialogsMixin.show_welcome_tour(h)
    finally:
        ad.AboutDialog = orig_about
        wt.WelcomeTourDialog = orig_tour
        dlg_pkg.ShortcutsDialog = orig_shortcuts
    assert "AboutDialog" in created, created
    assert "ShortcutsDialog" in created, created
    assert "WelcomeTourDialog" in created, created
    print("[PASS] test_help_dialogs_open")


def main():
    tests = [
        test_render_html_includes_content_and_theme,
        test_render_html_caches_css,
        test_render_html_footer_variables,
        test_render_html_custom_css_is_embedded,
        test_render_html_missing_custom_css_is_ignored,
        test_render_html_sanitizes_watermark_and_footer,
        test_render_html_footer_cannot_break_out_of_css,
        test_render_html_watermark_css_and_margins,
        test_render_html_english_pagination,
        test_html_builder_builds_full_document,
        test_html_builder_fallback_when_renderer_fails,
        test_html_builder_module_level_helper,
        test_ai_improve_text_without_suggestions_normalizes,
        test_ai_improve_text_with_suggestions_shows_dialog,
        test_ai_generate_outline_inserts_structure,
        test_start_voice_input_reports_missing_dependency,
        test_text_to_speech_stops_playing_engine,
        test_text_to_speech_speaks_when_idle,
        test_show_tts_settings_builds_dialog,
        test_goto_editor_line_moves_cursor,
        test_show_doc_templates_dialog_loads_chosen,
        test_show_doc_templates_dialog_cancel_keeps_text,
        test_document_ops_delegates_to_document_tools,
        test_help_dialogs_open,
    ]
    for t in tests:
        t()
    print("\nAll final coverage tests passed!")


if __name__ == "__main__":
    main()
