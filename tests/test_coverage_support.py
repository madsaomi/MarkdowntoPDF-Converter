"""Поведенческие тесты: экспорт, пресеты, TTS, toast, мульти-курсор, watermark.

Завершает серию роста покрытия (PLAN-013, этапы 3–4). Покрывает:
- `mixins/export_tools.py` — мульти-экспорт, экспорт выделения/документа,
  версии, облачные шаблоны;
- `mixins/presets.py` — загрузка/сохранение/удаление/применение пресетов;
- `mixins/tts_media.py` — озвучка и экспорт аудио;
- `gui/toast.py` — всплывающее уведомление;
- `gui/multi_cursor.py` — менеджер мульти-курсора;
- `gui/watermark_designer.py` — генерация CSS водяного знака.
"""
import os
import sys
import tempfile
import types

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QTextEdit, QWidget

app = QApplication.instance() or QApplication([])

import src.gui.mixins.export_tools as ex
import src.gui.mixins.presets as pre
import src.gui.mixins.tts_media as tts
import src.gui.multi_cursor as mc
import src.gui.toast as toast_mod
import src.gui.watermark_designer as wd


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


class _Cursor:
    def __init__(self, selected=""):
        self._selected = selected

    def selectedText(self):
        return self._selected


class _Editor:
    def __init__(self, text="", selected=""):
        self._text = text
        self.cursor = _Cursor(selected)

    def toPlainText(self):
        return self._text

    def setPlainText(self, t):
        self._text = t

    def textCursor(self):
        return self.cursor


class _Combo:
    def __init__(self, index=0, items=None):
        self._index = index
        self._items = list(items or [])
        self.blocked = False
        self.enabled = True

    def blockSignals(self, v):
        self.blocked = v

    def clear(self):
        self._items = []

    def addItem(self, text):
        self._items.append(text)

    def currentIndex(self):
        return self._index

    def setCurrentIndex(self, i):
        self._index = i

    def setEnabled(self, v):
        self.enabled = v

    def currentText(self):
        return self._items[self._index] if 0 <= self._index < len(self._items) else ""

    def findText(self, text):
        return self._items.index(text) if text in self._items else -1

    def items(self):
        return list(self._items)


class _Input:
    def __init__(self, text=""):
        self._text = text

    def text(self):
        return self._text

    def setText(self, t):
        self._text = t


class _Check:
    def __init__(self, checked=False):
        self._checked = checked
        self.enabled = True

    def isChecked(self):
        return self._checked

    def setChecked(self, v):
        self._checked = v

    def setEnabled(self, v):
        self.enabled = v


class _Settings:
    def __init__(self):
        self._d = {}

    def value(self, key, default=None, type=None):
        return self._d.get(key, default)

    def setValue(self, key, val):
        self._d[key] = val


class _Options:
    def __init__(self):
        self.watermark = ""
        self.footer_text = ""
        self.custom_css = ""
        self.margins = ""
        self.docx_template = ""
        self.page_numbers = False
        self.is_presentation = False


class FakeHost(QWidget):
    def __init__(self, text="", lang="ru"):
        super().__init__()
        self.live_editor = _Editor(text)
        self.current_lang = lang
        self.logs = []
        self.toasts = []
        self.previews = []
        self.selected_files = []
        self.settings = _Settings()
        self.presets = {}
        self.preset_combo = _Combo()
        self.doc_theme_combo = _Combo()
        self.code_theme_combo = _Combo()
        self.paper_combo = _Combo()
        self.format_combo = _Combo()
        self.combo_page_format = _Combo()
        self.watermark_input = _Input()
        self.footer_input = _Input()
        self.custom_css_input = _Input()
        self.margins_input = _Input()
        self.docx_template_input = _Input()
        self.chk_page_numbers = _Check()
        self.chk_presentation_mode = _Check()

    def append_log(self, msg):
        self.logs.append(msg)

    def toast(self, msg, kind="info"):
        self.toasts.append((msg, kind))

    def _render_live_preview(self):
        self.previews.append("render")

    def update_preview_from_editor(self):
        self.previews.append("preview")

    def tr_msg(self, key, *args):
        table = {
            "preset_prompt_title": "Имя пресета",
            "preset_prompt_desc": "Введите имя",
            "msg_done_title": "Готово",
            "msg_preset_saved": "Пресет сохранён: %s",
            "msg_preset_deleted": "Пресет удалён: %s",
        }
        text = table.get(key, key)
        return text % args if args else text

    def _get_options(self):
        return _Options()

    def _get_template_dir(self):
        return ""


class _PresetHost(FakeHost, pre.PresetsMixin):
    """Хост с самим миксином пресетов (save_preset вызывает self.load_presets)."""


# ─── export_tools ────────────────────────────────────────────────────────────

def test_show_multi_export_requires_file():
    """Без выбранного файла мульти-экспорт не запускается."""
    rec = _MsgBox().install(ex)
    try:
        h = FakeHost()
        ex.ExportToolsMixin.show_multi_export(h)
    finally:
        rec.restore(ex)
    assert "information" in rec.kinds, rec.calls
    assert "Select a file first" in rec.text_of()
    print("[PASS] test_show_multi_export_requires_file")


def test_export_selection_empty_warns():
    """Без выделения экспорт не выполняется."""
    rec = _MsgBox().install(ex)
    try:
        h = FakeHost()
        ex.ExportToolsMixin.export_selection(h)
    finally:
        rec.restore(ex)
    assert "Select text first" in rec.text_of()
    print("[PASS] test_export_selection_empty_warns")


def test_export_selection_writes_file():
    """Выделенный текст сохраняется в файл."""
    orig = ex.QFileDialog
    try:
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "sel.md")
            ex.QFileDialog = types.SimpleNamespace(
                getSaveFileName=lambda *a, **k: (path, "")
            )
            h = FakeHost()
            h.live_editor.cursor = _Cursor("выделенный текст")
            ex.ExportToolsMixin.export_selection(h)
            assert os.path.isfile(path)
            assert open(path, encoding="utf-8").read() == "выделенный текст"
            assert any("Selection saved" in log for log in h.logs), h.logs
    finally:
        ex.QFileDialog = orig
    print("[PASS] test_export_selection_writes_file")


def test_export_as_markdown_writes_file():
    """Документ сохраняется в Markdown."""
    orig = ex.QFileDialog
    try:
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "doc.md")
            ex.QFileDialog = types.SimpleNamespace(
                getSaveFileName=lambda *a, **k: (path, "")
            )
            h = FakeHost("# Заголовок")
            ex.ExportToolsMixin.export_as_markdown(h)
            assert os.path.isfile(path)
            assert "# Заголовок" in open(path, encoding="utf-8").read()
            assert any("Saved as Markdown" in log for log in h.logs), h.logs
    finally:
        ex.QFileDialog = orig
    print("[PASS] test_export_as_markdown_writes_file")


def test_save_version_saves_revision():
    """save_version сохраняет ревизию и показывает toast."""
    import src.gui.document_tools as dt

    called = []
    orig = dt.save_revision
    dt.save_revision = lambda w: called.append(w)
    try:
        h = FakeHost()
        ex.ExportToolsMixin.save_version(h)
    finally:
        dt.save_revision = orig
    assert called == [h], called
    assert h.toasts and h.toasts[-1][1] == "success", h.toasts
    print("[PASS] test_save_version_saves_revision")


def test_restore_version_opens_history():
    """restore_version открывает историю и обновляет превью."""
    import src.gui.document_tools as dt

    called = []
    orig = dt.show_revision_history
    dt.show_revision_history = lambda w: called.append(w)
    try:
        h = FakeHost()
        ex.ExportToolsMixin.restore_version(h)
    finally:
        dt.show_revision_history = orig
    assert called == [h], called
    assert "preview" in h.previews, h.previews
    print("[PASS] test_restore_version_opens_history")


def test_show_cloud_templates_loads_chosen():
    """Выбранный облачный шаблон загружается в редактор."""
    import src.core.cloud_templates as ctm

    orig_index = ctm.get_cloud_templates_index
    orig_input = ex.QInputDialog
    ctm.get_cloud_templates_index = lambda lang="ru": [
        {"name": "Built-in", "content": "# Облачный шаблон"},
    ]
    ex.QInputDialog = types.SimpleNamespace(
        getItem=lambda *a, **k: ("Built-in", True)
    )
    try:
        h = FakeHost()
        ex.ExportToolsMixin.show_cloud_templates(h)
    finally:
        ctm.get_cloud_templates_index = orig_index
        ex.QInputDialog = orig_input
    assert h.live_editor.toPlainText() == "# Облачный шаблон"
    assert h.previews == ["render"]
    assert any("Template loaded" in log for log in h.logs), h.logs
    print("[PASS] test_show_cloud_templates_loads_chosen")


def test_show_cloud_templates_cancel_keeps_text():
    """Отмена выбора шаблона не меняет текст."""
    import src.core.cloud_templates as ctm

    orig_index = ctm.get_cloud_templates_index
    orig_input = ex.QInputDialog
    ctm.get_cloud_templates_index = lambda lang="ru": [
        {"name": "Built-in", "content": "# Облачный шаблон"},
    ]
    ex.QInputDialog = types.SimpleNamespace(
        getItem=lambda *a, **k: ("Built-in", False)
    )
    try:
        h = FakeHost("исходный")
        ex.ExportToolsMixin.show_cloud_templates(h)
    finally:
        ctm.get_cloud_templates_index = orig_index
        ex.QInputDialog = orig_input
    assert h.live_editor.toPlainText() == "исходный"
    print("[PASS] test_show_cloud_templates_cancel_keeps_text")


# ─── presets ─────────────────────────────────────────────────────────────────

def test_load_presets_reads_settings():
    """Пресеты читаются из настроек и сортируются по имени."""
    h = _PresetHost()
    h.settings.setValue("presets", '{"zulu": {"doc_theme": 1}, "alpha": {"doc_theme": 2}}')
    pre.PresetsMixin.load_presets(h)
    items = h.preset_combo.items()
    assert items[0] == "(по умолчанию)", items
    assert items[1:] == ["alpha", "zulu"], items
    assert h.preset_combo.blocked is False
    print("[PASS] test_load_presets_reads_settings")


def test_load_presets_handles_broken_json():
    """Битый JSON не ломает загрузку — пресеты пусты."""
    h = _PresetHost()
    h.settings.setValue("presets", "{не json")
    pre.PresetsMixin.load_presets(h)
    assert h.presets == {}
    assert h.preset_combo.items() == ["(по умолчанию)"]
    print("[PASS] test_load_presets_handles_broken_json")


def test_save_preset_captures_settings():
    """Сохранение пресета захватывает текущие настройки."""
    rec = _MsgBox().install(pre)
    orig = pre.QInputDialog
    pre.QInputDialog = types.SimpleNamespace(getText=lambda *a, **k: ("Мой пресет", True))
    try:
        h = _PresetHost()
        pre.PresetsMixin.save_preset(h)
    finally:
        pre.QInputDialog = orig
        rec.restore(pre)
    assert "Мой пресет" in h.presets, h.presets
    assert "doc_theme" in h.presets["Мой пресет"]
    assert h.settings.value("presets"), "пресеты должны сохраняться в настройки"
    assert "information" in rec.kinds, rec.calls
    print("[PASS] test_save_preset_captures_settings")


def test_save_preset_cancel_does_nothing():
    """Отмена сохранения не создаёт пресет."""
    orig = pre.QInputDialog
    pre.QInputDialog = types.SimpleNamespace(getText=lambda *a, **k: ("", False))
    try:
        h = _PresetHost()
        pre.PresetsMixin.save_preset(h)
    finally:
        pre.QInputDialog = orig
    assert h.presets == {}
    print("[PASS] test_save_preset_cancel_does_nothing")


def test_delete_preset_removes_and_persists():
    """Удаление пресета убирает его из настроек."""
    rec = _MsgBox().install(pre)
    try:
        h = _PresetHost()
        h.presets = {"Мой": {"doc_theme": 1}}
        h.preset_combo = _Combo(index=1, items=["(по умолчанию)", "Мой"])
        pre.PresetsMixin.delete_preset(h)
    finally:
        rec.restore(pre)
    assert h.presets == {}
    assert "information" in rec.kinds, rec.calls
    print("[PASS] test_delete_preset_removes_and_persists")


def test_delete_preset_default_forbidden():
    """Пресет по умолчанию удалить нельзя."""
    h = _PresetHost()
    h.presets = {"Мой": {"doc_theme": 1}}
    h.preset_combo = _Combo(index=0, items=["(по умолчанию)", "Мой"])
    pre.PresetsMixin.delete_preset(h)
    assert "Мой" in h.presets
    print("[PASS] test_delete_preset_default_forbidden")


def test_on_preset_changed_applies_to_ui():
    """Применение пресета расставляет значения по элементам интерфейса."""
    h = FakeHost()
    h.presets = {
        "Мой": {
            "doc_theme": 3, "code_theme": 2, "paper_size": 1,
            "watermark": "WM", "footer_text": "F", "custom_css": "CSS",
            "export_format": 4, "margins": "10mm", "docx_template": "t.docx",
            "page_numbers": True, "page_num_format": 2, "presentation_mode": True,
        }
    }
    h.preset_combo = _Combo(index=1, items=["(по умолчанию)", "Мой"])
    pre.PresetsMixin.on_preset_changed(h, 1)
    assert h.doc_theme_combo.currentIndex() == 3
    assert h.code_theme_combo.currentIndex() == 2
    assert h.paper_combo.currentIndex() == 1
    assert h.watermark_input.text() == "WM"
    assert h.footer_input.text() == "F"
    assert h.custom_css_input.text() == "CSS"
    assert h.format_combo.currentIndex() == 4
    assert h.margins_input.text() == "10mm"
    assert h.docx_template_input.text() == "t.docx"
    assert h.chk_page_numbers.isChecked() is True
    assert h.combo_page_format.currentIndex() == 2
    assert h.combo_page_format.enabled is True
    assert h.chk_presentation_mode.isChecked() is True
    print("[PASS] test_on_preset_changed_applies_to_ui")


def test_on_preset_changed_default_ignored():
    """Индекс 0 (по умолчанию) ничего не применяет."""
    h = FakeHost()
    h.presets = {"Мой": {"doc_theme": 3}}
    h.preset_combo = _Combo(index=0, items=["(по умолчанию)", "Мой"])
    pre.PresetsMixin.on_preset_changed(h, 0)
    assert h.doc_theme_combo.currentIndex() == 0
    print("[PASS] test_on_preset_changed_default_ignored")


# ─── tts_media ───────────────────────────────────────────────────────────────

def test_text_to_speech_empty_text_warns():
    """Пустой текст не озвучивается."""
    rec = _MsgBox().install(tts)
    try:
        h = FakeHost("   ")
        tts.TtsMediaMixin.text_to_speech_speak(h)
    finally:
        rec.restore(tts)
    assert "No text to speak" in rec.text_of()
    print("[PASS] test_text_to_speech_empty_text_warns")


def test_text_to_speech_uses_engine():
    """Озвучка запускает движок и пишет состояние в лог."""
    import src.core.tts_engine as te

    class _Engine:
        def __init__(self):
            self.state_cb = None
            self.stopped = False

        def set_on_state_change(self, cb):
            self.state_cb = cb

        def is_playing(self):
            return False

        def stop(self):
            self.stopped = True

        def speak(self, *a, **k):
            self.spoke = True

    engine = _Engine()
    orig_get = te.get_tts_engine
    orig_strip = te.strip_markdown_for_tts
    te.get_tts_engine = lambda: engine
    te.strip_markdown_for_tts = lambda t: "очищенный текст"
    try:
        h = FakeHost("# Заголовок\n\nтекст")
        tts.TtsMediaMixin.text_to_speech_speak(h)
    finally:
        te.get_tts_engine = orig_get
        te.strip_markdown_for_tts = orig_strip
    assert engine.state_cb is not None, "обработчик состояния должен быть установлен"
    engine.state_cb("playing")
    assert any("TTS: playing" in log for log in h.logs), h.logs
    print("[PASS] test_text_to_speech_uses_engine")


def test_export_tts_audio_uses_engine():
    """Экспорт аудио вызывает движок с очищенным текстом."""
    import src.core.tts_engine as te

    class _Engine:
        def __init__(self):
            self.exported = None

        def export_to_file(self, text, path, lang):
            self.exported = (text, path, lang)
            return True

    engine = _Engine()
    orig_get = te.get_tts_engine
    orig_strip = te.strip_markdown_for_tts
    te.get_tts_engine = lambda: engine
    te.strip_markdown_for_tts = lambda t: "очищенный"
    orig_dialog = tts.QFileDialog
    try:
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "speech.mp3")
            tts.QFileDialog = types.SimpleNamespace(
                getSaveFileName=lambda *a, **k: (path, "")
            )
            h = FakeHost("текст")
            tts.TtsMediaMixin._export_tts_audio(h, engine)
    finally:
        tts.QFileDialog = orig_dialog
        te.get_tts_engine = orig_get
        te.strip_markdown_for_tts = orig_strip
    assert engine.exported is not None
    assert engine.exported[1].endswith("speech.mp3")
    assert h.toasts and h.toasts[-1][1] == "success", h.toasts
    print("[PASS] test_export_tts_audio_uses_engine")


# ─── toast ───────────────────────────────────────────────────────────────────

def test_toast_show_toast_positions_bottom_right():
    """show_toast размещает уведомление в правом нижнем углу родителя."""
    parent = QWidget()
    parent.resize(1000, 800)
    parent.move(0, 0)
    expected_x = parent.x() + parent.width() - 380
    expected_y = parent.y() + parent.height() - 80

    t = toast_mod.ToastNotification.show_toast(parent, "Привет", "success")
    assert t.width() == 360
    # offscreen-платформа слегка корректирует позицию окна, поэтому
    # сравниваем с допуском, а не попиксельно.
    assert abs(t.x() - expected_x) <= 60, (t.x(), expected_x)
    assert abs(t.y() - expected_y) <= 60, (t.y(), expected_y)
    # Уведомление находится правее и ниже левого верхнего угла родителя
    assert t.x() > parent.x()
    assert t.y() > parent.y()
    t.close()
    print("[PASS] test_toast_show_toast_positions_bottom_right")


def test_toast_types_have_colors_and_icons():
    """Для каждого типа уведомления определены цвета и иконка."""
    for kind in ("success", "error", "warning", "info"):
        bg, accent, icon = toast_mod.ToastNotification.COLORS[kind]
        assert bg.startswith("#") and accent.startswith("#")
        assert icon
    # Неизвестный тип falls back на info
    t = toast_mod.ToastNotification("msg", "unknown-type")
    assert t is not None
    t.close()
    print("[PASS] test_toast_types_have_colors_and_icons")


# ─── multi_cursor ────────────────────────────────────────────────────────────

def test_multi_cursor_add_and_remove():
    """Курсоры добавляются и удаляются, активность отражается в флаге."""
    editor = QTextEdit()
    editor.setPlainText("line1\nline2\nline3")
    mgr = mc.MultiCursorManager(editor)
    assert mgr.is_active is False

    mgr.add_cursor_at_current()
    assert len(mgr.cursors) == 1
    assert mgr.is_active is True

    mgr.add_cursor_at_line(2)
    assert len(mgr.cursors) == 2

    mgr.remove_last_cursor()
    assert len(mgr.cursors) == 1
    mgr.remove_last_cursor()
    assert len(mgr.cursors) == 0
    assert mgr.is_active is False
    print("[PASS] test_multi_cursor_add_and_remove")


def test_multi_cursor_select_all_occurrences():
    """Все вхождения текста выделяются отдельными курсорами."""
    editor = QTextEdit()
    editor.setPlainText("foo bar foo baz foo")
    mgr = mc.MultiCursorManager(editor)
    mgr.select_all_occurrences("foo")
    assert len(mgr.cursors) == 3, len(mgr.cursors)
    assert mgr.is_active is True
    print("[PASS] test_multi_cursor_select_all_occurrences")


def test_multi_cursor_type_at_all_cursors():
    """Текст вставляется во всех позициях курсоров."""
    editor = QTextEdit()
    editor.setPlainText("a b a")
    mgr = mc.MultiCursorManager(editor)
    mgr.select_all_occurrences("a")
    mgr.type_at_all_cursors("X")
    assert editor.toPlainText().count("X") == 2, editor.toPlainText()
    print("[PASS] test_multi_cursor_type_at_all_cursors")


def test_multi_cursor_clear_cursors():
    """clear_cursors удаляет все курсоры."""
    editor = QTextEdit()
    editor.setPlainText("text")
    mgr = mc.MultiCursorManager(editor)
    mgr.add_cursor_at_current()
    mgr.clear_cursors()
    assert mgr.cursors == []
    assert mgr.is_active is False
    print("[PASS] test_multi_cursor_clear_cursors")


# ─── watermark_designer ──────────────────────────────────────────────────────

def test_watermark_designer_generates_css():
    """Дизайнер водяного знака генерирует CSS по заданным параметрам."""
    dlg = wd.WatermarkDesignerDialog(lang="ru")
    dlg.text_input.setText("КОПИЯ")
    dlg._update_preview()
    css = dlg.result_css
    assert "КОПИЯ" in css, css
    assert ".watermark" in css
    dlg.close()
    print("[PASS] test_watermark_designer_generates_css")


def test_build_watermark_css_parameters():
    """build_watermark_css учитывает цвет, прозрачность, размер, угол и мозаику."""
    css = wd.build_watermark_css("TEXT", (10, 20, 30), 0.5, 40, -30,
                                  diagonal=True, tiled=False)
    assert css.startswith(".watermark {")
    assert "font-size: 40pt" in css, css
    assert "rgba(10, 20, 30, 0.5)" in css, css
    assert "rotate(-30deg)" in css, css
    assert 'content: "TEXT"' in css, css
    assert "transform-origin: center" in css, css

    tiled = wd.build_watermark_css("T", (0, 0, 0), 1.0, 12, 0, tiled=True)
    assert tiled.count("T") == 5, tiled
    assert "white-space: pre-wrap" in tiled, tiled
    print("[PASS] test_build_watermark_css_parameters")


def test_build_watermark_css_sanitizes_text():
    """Пользовательский текст очищается от разметки."""
    css = wd.build_watermark_css('<script>"x"</script>', (0, 0, 0), 0.3, 12, 0)
    assert "<" not in css, css
    assert ">" not in css, css
    # Кавычки внутри текста заменяются на одинарные
    inner = css.split('content: "')[1].rsplit('"', 1)[0]
    assert '"' not in inner, inner
    assert "<" not in inner and ">" not in inner, inner
    print("[PASS] test_build_watermark_css_sanitizes_text")


def main():
    tests = [
        test_show_multi_export_requires_file,
        test_export_selection_empty_warns,
        test_export_selection_writes_file,
        test_export_as_markdown_writes_file,
        test_save_version_saves_revision,
        test_restore_version_opens_history,
        test_show_cloud_templates_loads_chosen,
        test_show_cloud_templates_cancel_keeps_text,
        test_load_presets_reads_settings,
        test_load_presets_handles_broken_json,
        test_save_preset_captures_settings,
        test_save_preset_cancel_does_nothing,
        test_delete_preset_removes_and_persists,
        test_delete_preset_default_forbidden,
        test_on_preset_changed_applies_to_ui,
        test_on_preset_changed_default_ignored,
        test_text_to_speech_empty_text_warns,
        test_text_to_speech_uses_engine,
        test_export_tts_audio_uses_engine,
        test_toast_show_toast_positions_bottom_right,
        test_toast_types_have_colors_and_icons,
        test_multi_cursor_add_and_remove,
        test_multi_cursor_select_all_occurrences,
        test_multi_cursor_type_at_all_cursors,
        test_multi_cursor_clear_cursors,
        test_watermark_designer_generates_css,
        test_build_watermark_css_parameters,
        test_build_watermark_css_sanitizes_text,
    ]
    for t in tests:
        t()
    print("\nAll support-module coverage tests passed!")


if __name__ == "__main__":
    main()
