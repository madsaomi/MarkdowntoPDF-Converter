"""Поведенческие тесты диалогов версий (gui/dialogs/versions).

Покрывает загрузку истории ревизий (разбор имён файлов, сортировка, формат
метки) и сравнение документов (unified diff, HTML-вывод, статистика).
"""
import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication

app = QApplication.instance() or QApplication([])

import src.gui.dialogs.versions as v


class _NoopMsgBox:
    calls = []

    @staticmethod
    def warning(*a, **k):
        _NoopMsgBox.calls.append(("warning", a))

    @staticmethod
    def critical(*a, **k):
        _NoopMsgBox.calls.append(("critical", a))

    @staticmethod
    def information(*a, **k):
        _NoopMsgBox.calls.append(("information", a))


def _patch_msgbox():
    orig = v.QMessageBox
    v.QMessageBox = _NoopMsgBox
    return orig


def _restore_msgbox(orig):
    v.QMessageBox = orig


def test_revision_history_loads_backups_newest_first():
    """load_revisions загружает .md-бэкапы, сортируя от новых к старым."""
    with tempfile.TemporaryDirectory() as d:
        for name in (
            "20260101_100000_50.md",
            "20260601_120000_120.md",
            "20260301_110000_80.md",
        ):
            with open(os.path.join(d, name), "w", encoding="utf-8") as f:
                f.write("содержимое " + name)
        # Не-.md и неизвестный формат — должны быть пропущены/обработаны отдельно
        with open(os.path.join(d, "notes.txt"), "w", encoding="utf-8") as f:
            f.write("ignore me")

        dlg = v.RevisionHistoryDialog(d, lang="ru")
        count = dlg.list_widget.count()
        assert count == 3, count
        labels = [dlg.list_widget.item(i).text() for i in range(count)]
        # Обратная сортировка по имени файла → самый новый первый
        assert "01.06.2026" in labels[0], labels
        assert "01.03.2026" in labels[1], labels
        assert "01.01.2026" in labels[2], labels
        # Слово-count подписан в русской локали
        assert "сл." in labels[0], labels
        dlg.close()
    print("[PASS] test_revision_history_loads_backups_newest_first")


def test_revision_history_english_labels():
    """В английской локали подпись счётчика слов другая."""
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "20260101_100000_50.md"), "w", encoding="utf-8") as f:
            f.write("x")
        dlg = v.RevisionHistoryDialog(d, lang="en")
        label = dlg.list_widget.item(0).text()
        assert "words" in label, label
        dlg.close()
    print("[PASS] test_revision_history_english_labels")


def test_revision_history_missing_dir_is_safe():
    """Отсутствующий каталог бэкапов не вызывает исключение."""
    with tempfile.TemporaryDirectory() as d:
        missing = os.path.join(d, "no_such_dir")
        dlg = v.RevisionHistoryDialog(missing, lang="ru")
        assert dlg.list_widget.count() == 0
        assert dlg.selected_content is None
        dlg.close()
    print("[PASS] test_revision_history_missing_dir_is_safe")


def test_revision_history_selection_loads_content():
    """Выбор ревизии показывает её содержимое и включает кнопку восстановления."""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "20260101_100000_50.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write("моё содержимое")
        dlg = v.RevisionHistoryDialog(d, lang="ru")
        dlg.on_item_changed(dlg.list_widget.item(0), None)
        assert dlg.selected_content == "моё содержимое"
        assert dlg.btn_restore.isEnabled() is True
        assert "моё содержимое" in dlg.preview_browser.toPlainText()
        dlg.close()
    print("[PASS] test_revision_history_selection_loads_content")


def test_revision_history_clears_on_empty_selection():
    """Снятие выделения очищает предпросмотр и блокирует восстановление."""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "20260101_100000_50.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write("текст")
        dlg = v.RevisionHistoryDialog(d, lang="ru")
        dlg.on_item_changed(dlg.list_widget.item(0), None)
        dlg.on_item_changed(None, None)
        assert dlg.selected_content is None
        assert dlg.btn_restore.isEnabled() is False
        dlg.close()
    print("[PASS] test_revision_history_clears_on_empty_selection")


def test_diff_requires_both_files():
    """Без обоих файлов показывается предупреждение, сравнение не выполняется."""
    orig = _patch_msgbox()
    try:
        _NoopMsgBox.calls.clear()
        dlg = v.DiffDialog(lang="ru")
        dlg.left_path.setText("")
        dlg.right_path.setText("")
        dlg.do_compare()
        assert _NoopMsgBox.calls, "ожидалось предупреждение"
        assert _NoopMsgBox.calls[0][0] == "warning"
        dlg.close()
    finally:
        _restore_msgbox(orig)
    print("[PASS] test_diff_requires_both_files")


def test_diff_identical_files():
    """Одинаковые файлы — сообщение об идентичности."""
    with tempfile.TemporaryDirectory() as d:
        a = os.path.join(d, "a.md")
        b = os.path.join(d, "b.md")
        for p in (a, b):
            with open(p, "w", encoding="utf-8") as f:
                f.write("одинаковый текст\n")
        dlg = v.DiffDialog(lang="ru")
        dlg.left_path.setText(a)
        dlg.right_path.setText(b)
        dlg.do_compare()
        assert "идентичны" in dlg.stats_label.text()
        assert "идентичны" in dlg.diff_browser.toPlainText()
        dlg.close()
    print("[PASS] test_diff_identical_files")


def test_diff_reports_added_and_removed():
    """Различающиеся файлы дают unified diff со счётчиками."""
    with tempfile.TemporaryDirectory() as d:
        a = os.path.join(d, "a.md")
        b = os.path.join(d, "b.md")
        with open(a, "w", encoding="utf-8") as f:
            f.write("общая строка\nтолько в A\n")
        with open(b, "w", encoding="utf-8") as f:
            f.write("общая строка\nтолько в B\n")
        dlg = v.DiffDialog(lang="ru")
        dlg.left_path.setText(a)
        dlg.right_path.setText(b)
        dlg.do_compare()
        html = dlg.diff_browser.toHtml()
        assert "Добавлено" in dlg.stats_label.text()
        assert "Удалено" in dlg.stats_label.text()
        assert "только в B" in html
        assert "только в A" in html
        # Добавленные/удалённые строки помечены цветом
        assert "#d5f5e3" in html  # зелёный фон для добавленных
        assert "#fadbd8" in html  # красный фон для удалённых
        dlg.close()
    print("[PASS] test_diff_reports_added_and_removed")


def test_diff_missing_file_shows_critical():
    """Нечитаемый файл — критическая ошибка, а не исключение."""
    orig = _patch_msgbox()
    try:
        _NoopMsgBox.calls.clear()
        with tempfile.TemporaryDirectory() as d:
            a = os.path.join(d, "a.md")
            with open(a, "w", encoding="utf-8") as f:
                f.write("x")
            dlg = v.DiffDialog(lang="ru")
            dlg.left_path.setText(a)
            dlg.right_path.setText(os.path.join(d, "missing.md"))
            dlg.do_compare()
            assert _NoopMsgBox.calls
            assert _NoopMsgBox.calls[0][0] == "critical"
            dlg.close()
    finally:
        _restore_msgbox(orig)
    print("[PASS] test_diff_missing_file_shows_critical")


def test_diff_escapes_html_in_content():
    """HTML-спецсимволы в содержимом экранируются в выводе diff."""
    with tempfile.TemporaryDirectory() as d:
        a = os.path.join(d, "a.md")
        b = os.path.join(d, "b.md")
        with open(a, "w", encoding="utf-8") as f:
            f.write("строка <script>alert(1)</script>\n")
        with open(b, "w", encoding="utf-8") as f:
            f.write("строка <script>alert(2)</script>\n")
        dlg = v.DiffDialog(lang="ru")
        dlg.left_path.setText(a)
        dlg.right_path.setText(b)
        dlg.do_compare()
        html = dlg.diff_browser.toHtml()
        assert "<script>" not in html, "HTML должен быть экранирован"
        assert "&lt;script&gt;" in html
        dlg.close()
    print("[PASS] test_diff_escapes_html_in_content")


def main():
    tests = [
        test_revision_history_loads_backups_newest_first,
        test_revision_history_english_labels,
        test_revision_history_missing_dir_is_safe,
        test_revision_history_selection_loads_content,
        test_revision_history_clears_on_empty_selection,
        test_diff_requires_both_files,
        test_diff_identical_files,
        test_diff_reports_added_and_removed,
        test_diff_missing_file_shows_critical,
        test_diff_escapes_html_in_content,
    ]
    for t in tests:
        t()
    print("\nAll versions-dialog tests passed!")


if __name__ == "__main__":
    main()
