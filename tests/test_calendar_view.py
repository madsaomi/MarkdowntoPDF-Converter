"""Поведенческие тесты календаря заметок (gui/calendar_view).

Покрывает сканирование папки, группировку файлов по дате, выбор даты,
список заметок и предпросмотр содержимого.
"""
import os
import sys
import tempfile
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import QApplication, QListWidgetItem

app = QApplication.instance() or QApplication([])

from src.gui.calendar_view import CalendarNotesDialog


def _make_files(folder, names):
    """Создаёт .md файлы и проставляет им разные mtime."""
    paths = []
    for i, name in enumerate(names):
        p = os.path.join(folder, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(f"# {name}\n\nСодержимое {name}\n")
        # Разводим по времени, чтобы порядок был детерминированным
        t = time.time() - (len(names) - i) * 60
        os.utime(p, (t, t))
        paths.append(p)
    return paths


def test_scan_folder_collects_md_files_only():
    """Сканирование собирает только .md файлы."""
    with tempfile.TemporaryDirectory() as d:
        _make_files(d, ["a.md", "b.md"])
        with open(os.path.join(d, "skip.txt"), "w", encoding="utf-8") as f:
            f.write("not markdown")
        dlg = CalendarNotesDialog(folder=d, lang="ru")
        total = sum(len(v) for v in dlg._file_dates.values())
        assert total == 2, dlg._file_dates
        dlg.close()
    print("[PASS] test_scan_folder_collects_md_files_only")


def test_scan_folder_groups_by_date():
    """Файлы группируются по дате изменения."""
    with tempfile.TemporaryDirectory() as d:
        _make_files(d, ["a.md", "b.md"])
        dlg = CalendarNotesDialog(folder=d, lang="ru")
        assert len(dlg._file_dates) == 1, dlg._file_dates
        (date, files), = dlg._file_dates.items()
        assert isinstance(date, QDate)
        assert len(files) == 2
        dlg.close()
    print("[PASS] test_scan_folder_groups_by_date")


def test_select_date_lists_notes():
    """Выбор даты заполняет список заметок с временем изменения."""
    with tempfile.TemporaryDirectory() as d:
        _make_files(d, ["a.md", "b.md"])
        dlg = CalendarNotesDialog(folder=d, lang="ru")
        (date, files), = dlg._file_dates.items()
        dlg.calendar.setSelectedDate(date)
        dlg._on_date_selected()
        assert dlg.notes_list.count() == 2, dlg.notes_list.count()
        texts = [dlg.notes_list.item(i).text() for i in range(dlg.notes_list.count())]
        assert any("a.md" in t for t in texts), texts
        assert any("📝" in t for t in texts), texts
        # Метка даты заполнена
        assert dlg.date_label.text(), dlg.date_label.text()
        dlg.close()
    print("[PASS] test_select_date_lists_notes")


def test_select_date_without_notes_shows_placeholder():
    """Дата без заметок показывает заглушку и пустое превью."""
    with tempfile.TemporaryDirectory() as d:
        _make_files(d, ["a.md"])
        dlg = CalendarNotesDialog(folder=d, lang="ru")
        empty_day = QDate.currentDate().addDays(-365)
        dlg.calendar.setSelectedDate(empty_day)
        dlg._on_date_selected()
        assert dlg.notes_list.count() == 1
        assert "No notes" in dlg.notes_list.item(0).text()
        assert dlg.preview.toPlainText() == ""
        dlg.close()
    print("[PASS] test_select_date_without_notes_shows_placeholder")


def test_open_note_shows_preview():
    """Двойной клик по заметке показывает её содержимое в превью."""
    with tempfile.TemporaryDirectory() as d:
        _make_files(d, ["a.md"])
        dlg = CalendarNotesDialog(folder=d, lang="ru")
        (date, files), = dlg._file_dates.items()
        dlg.calendar.setSelectedDate(date)
        dlg._on_date_selected()
        item = dlg.notes_list.item(0)
        dlg._open_note(item)
        html = dlg.preview.toHtml()
        assert "Содержимое" in html, html
        dlg.close()
    print("[PASS] test_open_note_shows_preview")


def test_open_note_truncates_long_text():
    """Длинный текст обрезается до 3000 символов с пометкой."""
    with tempfile.TemporaryDirectory() as d:
        long_text = "A" * 5000
        p = os.path.join(d, "long.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write(long_text)
        dlg = CalendarNotesDialog(folder=d, lang="ru")
        (date, files), = dlg._file_dates.items()
        item = QListWidgetItem("long.md")
        item.setData(256, files[0])  # Qt.ItemDataRole.UserRole
        dlg._open_note(item)
        html = dlg.preview.toHtml()
        assert "truncated" in html, html[-200:]
        dlg.close()
    print("[PASS] test_open_note_truncates_long_text")


def test_open_note_missing_file_is_safe():
    """Отсутствующий файл не вызывает исключение."""
    with tempfile.TemporaryDirectory() as d:
        dlg = CalendarNotesDialog(folder=d, lang="ru")
        item = QListWidgetItem("ghost.md")
        item.setData(256, os.path.join(d, "ghost.md"))
        dlg._open_note(item)
        dlg.close()
    print("[PASS] test_open_note_missing_file_is_safe")


def test_empty_folder_has_no_dates():
    """В пустой папке нет ни одной даты с заметками."""
    with tempfile.TemporaryDirectory() as d:
        dlg = CalendarNotesDialog(folder=d, lang="ru")
        assert dlg._file_dates == {}
        dlg.close()
    print("[PASS] test_empty_folder_has_no_dates")


def main():
    tests = [
        test_scan_folder_collects_md_files_only,
        test_scan_folder_groups_by_date,
        test_select_date_lists_notes,
        test_select_date_without_notes_shows_placeholder,
        test_open_note_shows_preview,
        test_open_note_truncates_long_text,
        test_open_note_missing_file_is_safe,
        test_empty_folder_has_no_dates,
    ]
    for t in tests:
        t()
    print("\nAll calendar view tests passed!")


if __name__ == "__main__":
    main()
