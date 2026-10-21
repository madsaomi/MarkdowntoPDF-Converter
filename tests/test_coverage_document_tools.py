"""Поведенческие тесты gui/document_tools.py.

Покрывает «чистую» логику модуля: авто-исправление текста, генерацию
оглавления, читаемость, ревизии, черновики и генераторы.
"""
import os
import sys
import tempfile
import types

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QWidget

app = QApplication.instance() or QApplication([])

import src.gui.document_tools as dt


# ─── заглушки ────────────────────────────────────────────────────────────────

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
    MoveOperation = types.SimpleNamespace(
        Start="start", Down="down", StartOfLine="sol", EndOfLine="eol"
    )
    MoveMode = types.SimpleNamespace(KeepAnchor="keep")

    def __init__(self, text="", editor=None):
        self._text = text
        self._pos = 0
        self.inserted = []
        self.moved = []
        self.editor = editor

    def selectedText(self):
        return ""

    def insertText(self, s):
        self.inserted.append(s)
        self._text += s
        # Настоящий курсор меняет документ — синхронизируем и редактор
        if self.editor is not None:
            self.editor._text = self._text

    def movePosition(self, op, *a, **k):
        self.moved.append(op)
        return True

    def position(self):
        return self._pos

    def setPosition(self, p):
        self._pos = p


class _Editor:
    def __init__(self, text=""):
        self._text = text
        self.cursor = _Cursor(text, editor=self)
        self.focused = False
        self.blocked = False
        self._scroll = 0

    def toPlainText(self):
        return self._text

    def setPlainText(self, t):
        self._text = t

    def textCursor(self):
        self.cursor._text = self._text
        self.cursor.editor = self
        return self.cursor

    def setTextCursor(self, c):
        self.cursor = c
        c.editor = self

    def setFocus(self):
        self.focused = True

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


class FakeHost(QWidget):
    def __init__(self, text="", lang="ru", tmpdir=None):
        super().__init__()
        self.live_editor = _Editor(text)
        self.current_lang = lang
        self.logs = []
        self.toasts = []
        self.previews = []
        self.stats_calls = 0
        self.writing_goal = 0
        self.goal_celebrated = False
        self.is_welcome_doc_active = False
        self.current_workspace_file = None
        self.selected_files = []
        self.draft_path = os.path.join(tmpdir or tempfile.gettempdir(), "draft.md")

    def append_log(self, msg):
        self.logs.append(msg)

    def toast(self, msg, kind="info"):
        self.toasts.append((msg, kind))

    def _render_live_preview(self):
        self.previews.append("render")

    def update_text_statistics(self):
        self.stats_calls += 1

    def tr_msg(self, key, *args):
        table = {
            "msg_file_not_found": "Файл не найден",
            "history_empty": "История пуста",
            "log_draft_restored": "Черновик восстановлен",
        }
        text = table.get(key, key)
        return text % args if args else text


# ─── estimate_readability ────────────────────────────────────────────────────

def test_estimate_readability_empty_text():
    """Пустой текст — 100 баллов и «N/A»."""
    score, level = dt.estimate_readability("", "ru")
    assert score == 100
    assert level == "N/A"
    print("[PASS] test_estimate_readability_empty_text")


def test_estimate_readability_short_text_is_easy():
    """Короткие простые предложения дают высокий балл."""
    score, level = dt.estimate_readability("Cat and dog. Sun is hot. I am ok.", "en")
    assert score > 70, score
    assert level != "N/A"
    print("[PASS] test_estimate_readability_short_text_is_easy")


def test_estimate_readability_long_text_is_hard():
    """Длинные сложные предложения дают низкий балл."""
    text = (
        "Notwithstanding the aforementioned considerations regarding "
        "the implementation of comprehensive methodological frameworks, "
        "the demonstrated discrepancies necessitate further investigation. "
        "Furthermore, the interdepartmental collaboration exhibited "
        "unprecedented inconsistencies throughout the organization."
    )
    score, level = dt.estimate_readability(text, "en")
    assert score < 50, score
    print("[PASS] test_estimate_readability_long_text_is_hard")


def test_estimate_readability_russian_uses_russian_vowels():
    """Для русского текста используются русские гласные."""
    ru_score, _ = dt.estimate_readability("Кот и собака. Солнце жарко. Я в порядке.", "ru")
    en_score, _ = dt.estimate_readability("Кот и собака. Солнце жарко. Я в порядке.", "en")
    assert isinstance(ru_score, float)
    assert ru_score != en_score, "подсчёт слогов должен различаться"
    print("[PASS] test_estimate_readability_russian_uses_russian_vowels")


def test_estimate_readability_score_is_bounded():
    """Балл всегда в диапазоне 0..100."""
    for text in ("", "a", "а" * 500, "The quick brown fox. " * 50):
        score, _ = dt.estimate_readability(text, "en")
        assert 0 <= score <= 100, (text[:20], score)
    print("[PASS] test_estimate_readability_score_is_bounded")


# ─── auto_fix_document_issues ────────────────────────────────────────────────

def test_auto_fix_smart_quotes_russian():
    """Прямые кавычки превращаются в «ёлочки» (RU)."""
    rec = _MsgBox().install(dt)
    try:
        w = FakeHost('Он сказал "привет" и ушёл.')
        dt.auto_fix_document_issues(w)
    finally:
        rec.restore(dt)
    text = w.live_editor.toPlainText()
    assert '"' not in text, text
    assert "«привет»" in text, text
    print("[PASS] test_auto_fix_smart_quotes_russian")


def test_auto_fix_smart_quotes_english():
    """В английской локали ставятся типографские кавычки."""
    rec = _MsgBox().install(dt)
    try:
        w = FakeHost('He said "hello" and left.', lang="en")
        dt.auto_fix_document_issues(w)
    finally:
        rec.restore(dt)
    text = w.live_editor.toPlainText()
    assert '"' not in text, text
    assert "“" in text and "”" in text, text
    print("[PASS] test_auto_fix_smart_quotes_english")


def test_auto_fix_removes_trailing_space():
    """Висячий пробел в конце строки удаляется."""
    rec = _MsgBox().install(dt)
    try:
        w = FakeHost("первая строка \nвторая")
        dt.auto_fix_document_issues(w)
    finally:
        rec.restore(dt)
    assert " \n" not in w.live_editor.toPlainText(), repr(w.live_editor.toPlainText())
    print("[PASS] test_auto_fix_removes_trailing_space")


def test_auto_fix_adds_space_after_punctuation():
    """После запятой/двоеточия добавляется пробел."""
    rec = _MsgBox().install(dt)
    try:
        w = FakeHost("слово,слово;слово:слово")
        dt.auto_fix_document_issues(w)
    finally:
        rec.restore(dt)
    text = w.live_editor.toPlainText()
    assert ", " in text, text
    assert "; " in text, text
    assert ": " in text, text
    print("[PASS] test_auto_fix_adds_space_after_punctuation")


def test_auto_fix_no_change_shows_no_message():
    """Если текст не изменился — сообщения нет."""
    rec = _MsgBox().install(dt)
    try:
        w = FakeHost("обычный текст без кавычек")
        dt.auto_fix_document_issues(w)
    finally:
        rec.restore(dt)
    assert not rec.calls, rec.calls
    assert w.previews == []
    print("[PASS] test_auto_fix_no_change_shows_no_message")


# ─── update_markdown_toc_in_editor ───────────────────────────────────────────

def test_update_toc_inserts_markers_and_entries():
    """Оглавление вставляется между маркерами с якорями."""
    rec = _MsgBox().install(dt)
    try:
        w = FakeHost("# Первый\n\n## Второй\n\nтекст")
        dt.update_markdown_toc_in_editor(w)
    finally:
        rec.restore(dt)
    text = w.live_editor.toPlainText()
    assert "<!-- TOC START -->" in text, text
    assert "<!-- TOC END -->" in text, text
    assert "[Первый](#первый)" in text, text
    assert "  - [Второй](#второй)" in text, text
    assert "information" in rec.kinds, rec.calls
    print("[PASS] test_update_toc_inserts_markers_and_entries")


def test_update_toc_replaces_existing_block():
    """Повторное обновление заменяет блок, а не дублирует его."""
    rec = _MsgBox().install(dt)
    try:
        w = FakeHost("# Первый\n\n## Второй")
        dt.update_markdown_toc_in_editor(w)
        first = w.live_editor.toPlainText()
        dt.update_markdown_toc_in_editor(w)
        second = w.live_editor.toPlainText()
    finally:
        rec.restore(dt)
    assert first.count("<!-- TOC START -->") == 1, first
    assert second.count("<!-- TOC START -->") == 1, second
    assert second.count("[Первый](#первый)") == 1, second
    print("[PASS] test_update_toc_replaces_existing_block")


def test_update_toc_skips_code_blocks_and_comments():
    """Заголовки внутри блоков кода и HTML-комментариев игнорируются."""
    rec = _MsgBox().install(dt)
    try:
        w = FakeHost("# Настоящий\n\n```\n# В коде\n```\n\n## <!-- Комментарий -->")
        dt.update_markdown_toc_in_editor(w)
    finally:
        rec.restore(dt)
    text = w.live_editor.toPlainText()
    assert "[Настоящий](#настоящий)" in text, text
    # Проверяем именно блок оглавления, а не исходный текст
    toc = text.split("<!-- TOC START -->")[1].split("<!-- TOC END -->")[0]
    assert "В коде" not in toc, toc
    assert "Комментарий" not in toc, toc
    print("[PASS] test_update_toc_skips_code_blocks_and_comments")


# ─── show_toc_generator ──────────────────────────────────────────────────────

class _FakeTocDialog:
    """Заглушка MarkdownTOCDialog."""

    def __init__(self, max_depth=3, style="numbered", anchors=True, accepted=True):
        self._max_depth = max_depth
        self._style = style
        self._anchors = anchors
        self._accepted = accepted

        class _Combo:
            def __init__(self, value):
                self._value = value

            def currentData(self):
                return self._value

        class _Chk:
            def __init__(self, value):
                self._value = value

            def isChecked(self):
                return self._value

        self.depth_combo = _Combo(max_depth)
        self.style_combo = _Combo(style)
        self.anchors_chk = _Chk(anchors)

    def exec(self):
        from PyQt6.QtWidgets import QDialog
        return QDialog.DialogCode.Accepted if self._accepted else QDialog.DialogCode.Rejected


def test_show_toc_generator_numbered():
    """Нумерованное оглавление строит иерархию 1. / 1.1. / 1.1.1."""
    from PyQt6.QtWidgets import QDialog

    orig = dt.MarkdownTOCDialog
    dt.MarkdownTOCDialog = lambda *a, **k: _FakeTocDialog(style="numbered")
    try:
        w = FakeHost("# Раздел\n\n## Подраздел\n\n### Пункт")
        dt.show_toc_generator(w)
    finally:
        dt.MarkdownTOCDialog = orig
    text = w.live_editor.toPlainText()
    assert "1. [Раздел](#раздел)" in text, text
    assert "  1.1. [Подраздел](#подраздел)" in text, text
    assert "    1.1.1. [Пункт](#пункт)" in text, text
    print("[PASS] test_show_toc_generator_numbered")


def test_show_toc_generator_bullet_without_anchors():
    """Маркированное оглавление без якорей."""
    orig = dt.MarkdownTOCDialog
    dt.MarkdownTOCDialog = lambda *a, **k: _FakeTocDialog(style="bullet", anchors=False)
    try:
        w = FakeHost("# Раздел\n\n## Подраздел")
        dt.show_toc_generator(w)
    finally:
        dt.MarkdownTOCDialog = orig
    text = w.live_editor.toPlainText()
    assert "- Раздел" in text, text
    assert "  - Подраздел" in text, text
    assert "#раздел" not in text, "якорей быть не должно"
    print("[PASS] test_show_toc_generator_bullet_without_anchors")


def test_show_toc_generator_respects_max_depth():
    """Заголовки глубже выбранной глубины пропускаются."""
    orig = dt.MarkdownTOCDialog
    dt.MarkdownTOCDialog = lambda *a, **k: _FakeTocDialog(max_depth=1)
    try:
        w = FakeHost("# Раздел\n\n## Подраздел")
        dt.show_toc_generator(w)
    finally:
        dt.MarkdownTOCDialog = orig
    text = w.live_editor.toPlainText()
    # Проверяем блок оглавления, а не исходный текст
    toc = text.split("## Оглавление")[1] if "## Оглавление" in text else text
    assert "Раздел" in toc, toc
    assert "Подраздел" not in toc, toc
    print("[PASS] test_show_toc_generator_respects_max_depth")


# ─── show_table_generator_dialog ─────────────────────────────────────────────

def test_show_table_generator_inserts_markdown():
    """Генератор таблиц вставляет Markdown-таблицу."""
    from PyQt6.QtWidgets import QDialog
    import src.gui.dialogs as dlg_pkg

    class _FakeTableDialog:
        def __init__(self, *a, **k):
            class _Spin:
                def value(self):
                    return 2
            self.rows_spin = _Spin()
            self.cols_spin = _Spin()

        def exec(self):
            return QDialog.DialogCode.Accepted

    # show_table_generator_dialog импортирует диалог внутри функции,
    # поэтому подменять нужно атрибут пакета.
    orig = dlg_pkg.MarkdownTableDialog
    dlg_pkg.MarkdownTableDialog = _FakeTableDialog
    try:
        w = FakeHost()
        dt.show_table_generator_dialog(w)
    finally:
        dlg_pkg.MarkdownTableDialog = orig
    text = "".join(w.live_editor.cursor.inserted)
    assert "| Header 1 | Header 2 |" in text, text
    assert "Row 1 Col 1" in text, text
    print("[PASS] test_show_table_generator_inserts_markdown")


# ─── set_writing_goal ────────────────────────────────────────────────────────

def test_set_writing_goal_updates_value():
    """Цель по числу слов сохраняется и сбрасывает флаг праздника."""
    orig = dt.QInputDialog
    dt.QInputDialog = types.SimpleNamespace(
        getInt=lambda *a, **k: (500, True)
    )
    try:
        w = FakeHost()
        w.goal_celebrated = True
        dt.set_writing_goal(w)
    finally:
        dt.QInputDialog = orig
    assert w.writing_goal == 500
    assert w.goal_celebrated is False
    assert w.stats_calls == 1
    print("[PASS] test_set_writing_goal_updates_value")


def test_set_writing_goal_cancel_keeps_value():
    """Отмена не меняет цель."""
    orig = dt.QInputDialog
    dt.QInputDialog = types.SimpleNamespace(getInt=lambda *a, **k: (0, False))
    try:
        w = FakeHost()
        w.writing_goal = 100
        dt.set_writing_goal(w)
    finally:
        dt.QInputDialog = orig
    assert w.writing_goal == 100
    print("[PASS] test_set_writing_goal_cancel_keeps_value")


# ─── ревизии и черновики ─────────────────────────────────────────────────────

def test_save_revision_creates_backup():
    """save_revision создаёт резервную копию в каталоге бэкапов."""
    with tempfile.TemporaryDirectory() as d:
        w = FakeHost("# Текст документа", tmpdir=d)
        f = os.path.join(d, "doc.md")
        with open(f, "w", encoding="utf-8") as fh:
            fh.write("# Текст документа")
        w.current_workspace_file = f
        dt.save_revision(w)

        from src.config import AppConfig
        import hashlib
        h = hashlib.md5(os.path.abspath(f).encode("utf-8")).hexdigest()
        backup_dir = os.path.join(AppConfig.backups_dir(), h)
        assert os.path.isdir(backup_dir), backup_dir
        backups = os.listdir(backup_dir)
        assert len(backups) == 1, backups
        assert backups[0].endswith(".md")
        # Имя: YYYYMMDD_HHMMSS_слов
        parts = backups[0][:-3].split("_")
        assert len(parts) == 3, backups[0]
        assert parts[2] == "3", backups[0]  # 3 слова
    print("[PASS] test_save_revision_creates_backup")


def test_save_revision_skips_unchanged_content():
    """Повторное сохранение того же текста не создаёт копию."""
    with tempfile.TemporaryDirectory() as d:
        w = FakeHost("одинаковый текст", tmpdir=d)
        f = os.path.join(d, "doc.md")
        with open(f, "w", encoding="utf-8") as fh:
            fh.write("одинаковый текст")
        w.current_workspace_file = f
        dt.save_revision(w)
        dt.save_revision(w)

        from src.config import AppConfig
        import hashlib
        h = hashlib.md5(os.path.abspath(f).encode("utf-8")).hexdigest()
        backup_dir = os.path.join(AppConfig.backups_dir(), h)
        assert len(os.listdir(backup_dir)) == 1, os.listdir(backup_dir)
    print("[PASS] test_save_revision_skips_unchanged_content")


def test_save_revision_without_file_is_noop():
    """Без файла ревизия не сохраняется."""
    w = FakeHost("текст")
    w.current_workspace_file = None
    w.selected_files = []
    dt.save_revision(w)
    print("[PASS] test_save_revision_without_file_is_noop")


def test_show_revision_history_without_file_warns():
    """Без файла история ревизий не открывается."""
    rec = _MsgBox().install(dt)
    try:
        w = FakeHost()
        w.current_workspace_file = None
        w.selected_files = []
        dt.show_revision_history(w)
    finally:
        rec.restore(dt)
    assert "warning" in rec.kinds, rec.calls
    print("[PASS] test_show_revision_history_without_file_warns")


def test_autosave_draft_writes_and_restores():
    """Черновик сохраняется автосохранением и восстанавливается."""
    with tempfile.TemporaryDirectory() as d:
        w = FakeHost("черновик текста", tmpdir=d)
        w.draft_path = os.path.join(d, "draft.md")
        dt.autosave_draft(w)
        assert os.path.isfile(w.draft_path)

        w2 = FakeHost("", tmpdir=d)
        w2.draft_path = w.draft_path
        dt.restore_draft_if_exists(w2)
        assert w2.live_editor.toPlainText() == "черновик текста"
        assert w2.is_welcome_doc_active is False
        assert w2.previews == ["render"]
    print("[PASS] test_autosave_draft_writes_and_restores")


def test_autosave_draft_removes_empty_draft():
    """Пустой текст удаляет файл черновика."""
    with tempfile.TemporaryDirectory() as d:
        w = FakeHost("   ", tmpdir=d)
        w.draft_path = os.path.join(d, "draft.md")
        with open(w.draft_path, "w", encoding="utf-8") as fh:
            fh.write("старый черновик")
        dt.autosave_draft(w)
        assert not os.path.exists(w.draft_path)
    print("[PASS] test_autosave_draft_removes_empty_draft")


def test_autosave_draft_skipped_for_welcome_doc():
    """Для приветственного документа автосохранение не выполняется."""
    with tempfile.TemporaryDirectory() as d:
        w = FakeHost("текст", tmpdir=d)
        w.draft_path = os.path.join(d, "draft.md")
        w.is_welcome_doc_active = True
        dt.autosave_draft(w)
        assert not os.path.exists(w.draft_path)
    print("[PASS] test_autosave_draft_skipped_for_welcome_doc")


def main():
    tests = [
        test_estimate_readability_empty_text,
        test_estimate_readability_short_text_is_easy,
        test_estimate_readability_long_text_is_hard,
        test_estimate_readability_russian_uses_russian_vowels,
        test_estimate_readability_score_is_bounded,
        test_auto_fix_smart_quotes_russian,
        test_auto_fix_smart_quotes_english,
        test_auto_fix_removes_trailing_space,
        test_auto_fix_adds_space_after_punctuation,
        test_auto_fix_no_change_shows_no_message,
        test_update_toc_inserts_markers_and_entries,
        test_update_toc_replaces_existing_block,
        test_update_toc_skips_code_blocks_and_comments,
        test_show_toc_generator_numbered,
        test_show_toc_generator_bullet_without_anchors,
        test_show_toc_generator_respects_max_depth,
        test_show_table_generator_inserts_markdown,
        test_set_writing_goal_updates_value,
        test_set_writing_goal_cancel_keeps_value,
        test_save_revision_creates_backup,
        test_save_revision_skips_unchanged_content,
        test_save_revision_without_file_is_noop,
        test_show_revision_history_without_file_warns,
        test_autosave_draft_writes_and_restores,
        test_autosave_draft_removes_empty_draft,
        test_autosave_draft_skipped_for_welcome_doc,
    ]
    for t in tests:
        t()
    print("\nAll document_tools tests passed!")


if __name__ == "__main__":
    main()
