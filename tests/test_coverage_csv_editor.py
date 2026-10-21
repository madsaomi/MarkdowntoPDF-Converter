"""Поведенческие тесты gui/csv_editor.py (CSVEditorDialog).

Покрывает импорт CSV/TSV (включая регрессию BUG_010: выбор разделителя,
отличного от «Auto», раньше ронял импорт с TypeError), загрузку примера,
работу с таблицей и оба вида экспорта.
"""
import csv
import os
import shutil
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QDialog, QTableWidgetItem

app = QApplication.instance() or QApplication([])

from src.gui import csv_editor
from src.gui.csv_editor import CSVEditorDialog


# ─── Вспомогательные объекты ────────────────────────────────────────────────

class _FakeFileDialog:
    """Подменяет QFileDialog: отдаёт заранее заданный путь."""

    open_path = ""
    save_path = ""
    calls = []

    @classmethod
    def getOpenFileName(cls, *args, **kwargs):
        cls.calls.append("open")
        return cls.open_path, ""

    @classmethod
    def getSaveFileName(cls, *args, **kwargs):
        cls.calls.append("save")
        return cls.save_path, ""


class _FakeMessageBox:
    """Запоминает вызовы critical вместо показа модального окна."""

    criticals = []

    @classmethod
    def critical(cls, parent, title, text, *args, **kwargs):
        cls.criticals.append((title, text))


def _patch_file_dialog(open_path="", save_path=""):
    _FakeFileDialog.open_path = open_path
    _FakeFileDialog.save_path = save_path
    _FakeFileDialog.calls = []
    csv_editor.QFileDialog = _FakeFileDialog


def _restore():
    import PyQt6.QtWidgets as qtw
    csv_editor.QFileDialog = qtw.QFileDialog
    csv_editor.QMessageBox = qtw.QMessageBox
    _FakeMessageBox.criticals = []


def _patch_message_box():
    _FakeMessageBox.criticals = []
    csv_editor.QMessageBox = _FakeMessageBox


def _temp_file(content, suffix=".csv", encoding="utf-8"):
    """Создаёт временный файл и возвращает его путь (уборка в finally теста)."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    with open(path, "w", encoding=encoding, newline="") as f:
        f.write(content)
    return path


# ─── Начальное состояние ────────────────────────────────────────────────────

def test_defaults():
    """Пустая таблица, все разделители в списке, подписи кнопок на месте."""
    d = CSVEditorDialog()
    assert d.windowTitle() == "📊 CSV Table Editor"
    assert d.table.rowCount() == 0
    assert d.table.columnCount() == 0
    assert d.selected_markdown == ""
    assert d._loading is False
    assert [d.delimiter_combo.itemText(i) for i in range(d.delimiter_combo.count())] == [
        "Auto", "Comma (,)", "Tab", "Semicolon (;)", "Pipe (|)",
    ]
    assert d.delimiter_combo.currentText() == "Auto"
    assert d.btn_import.text() == "📂 Import CSV/TSV"
    assert d.btn_load_sample.text() == "📋 Load Sample"
    assert d.btn_to_md.text() == "📝 Export as Markdown Table"
    assert d.btn_to_csv.text() == "💾 Export as CSV"
    print("[PASS] test_defaults")


# ─── Определение разделителя ────────────────────────────────────────────────

def test_detect_delimiter_auto_tab_wins():
    """Наличие табуляции перевешивает остальные символы."""
    d = CSVEditorDialog()
    assert d._detect_delimiter("a\tb,c;d|e") == "\t"
    print("[PASS] test_detect_delimiter_auto_tab_wins")


def test_detect_delimiter_auto_semicolon_and_pipe():
    """Точка с запятой и pipe выбираются только при перевесе над запятой."""
    d = CSVEditorDialog()
    assert d._detect_delimiter("a;b;c,d") == ";"
    assert d._detect_delimiter("a|b|c,d") == "|"
    assert d._detect_delimiter("a;b,c") == ","       # поровну — запятая
    assert d._detect_delimiter("a|b,c") == ","       # поровну — запятая
    assert d._detect_delimiter("plain") == ","
    print("[PASS] test_detect_delimiter_auto_semicolon_and_pipe")


def test_detect_delimiter_explicit_returns_single_character():
    """BUG_010: явный выбор разделителя даёт символ, а не текст пункта."""
    d = CSVEditorDialog()
    expected = {
        "Comma (,)": ",",
        "Tab": "\t",
        "Semicolon (;)": ";",
        "Pipe (|)": "|",
    }
    for label, char in expected.items():
        d.delimiter_combo.setCurrentText(label)
        got = d._detect_delimiter("a,b")
        assert got == char, (label, repr(got))
        assert isinstance(got, str) and len(got) == 1, (label, repr(got))
        # Главное следствие бага: csv.reader принимает результат
        assert list(csv.reader(["a" + char + "b"], delimiter=got)) == [["a", "b"]]
    print("[PASS] test_detect_delimiter_explicit_returns_single_character")


# ─── Загрузка строк в таблицу ───────────────────────────────────────────────

def test_load_rows_sets_headers_and_cells():
    """Первая строка становится заголовком, остальные — данными."""
    d = CSVEditorDialog()
    d._load_rows([["Name", "City"], ["Alice", "Moscow"], ["Bob", "Berlin"]])
    assert d.table.columnCount() == 2
    assert d.table.rowCount() == 2
    assert d.table.horizontalHeaderItem(0).text() == "Name"
    assert d.table.horizontalHeaderItem(1).text() == "City"
    assert d.table.item(0, 0).text() == "Alice"
    assert d.table.item(1, 1).text() == "Berlin"
    assert d._loading is False, "флаг загрузки должен сбрасываться"
    print("[PASS] test_load_rows_sets_headers_and_cells")


def test_load_rows_empty_clears_and_resets_flag():
    """Пустой список не оставляет _loading=True (было второе следствие BUG_010)."""
    d = CSVEditorDialog()
    d._load_rows([["A"], ["1"]])
    assert d.table.rowCount() == 1
    d._load_rows([])
    assert d._loading is False, "пустой импорт не должен залипать в состоянии загрузки"
    assert d.table.rowCount() == 1, "clearContents очищает ячейки, но не счётчики"
    assert d.table.item(0, 0) is None
    print("[PASS] test_load_rows_empty_clears_and_resets_flag")


def test_load_rows_ignores_cells_beyond_header():
    """Ячейки сверх числа заголовков отбрасываются, а не ломают таблицу."""
    d = CSVEditorDialog()
    d._load_rows([["A", "B"], ["1", "2", "3"]])
    assert d.table.columnCount() == 2
    assert d.table.item(0, 1).text() == "2"
    print("[PASS] test_load_rows_ignores_cells_beyond_header")


def test_load_rows_handles_short_rows():
    """Короткая строка оставляет «дырки» в таблице — экспорт подставит пусто."""
    d = CSVEditorDialog()
    d._load_rows([["A", "B", "C"], ["1"]])
    assert d.table.rowCount() == 1
    assert d.table.item(0, 0).text() == "1"
    assert d.table.item(0, 1) is None
    print("[PASS] test_load_rows_handles_short_rows")


def test_load_sample_fills_four_by_four():
    """Кнопка «Load Sample» даёт 4 колонки и 4 строки с известными данными."""
    d = CSVEditorDialog()
    d._load_sample()
    assert d.table.columnCount() == 4
    assert d.table.rowCount() == 4
    assert [d.table.horizontalHeaderItem(c).text() for c in range(4)] == ["Name", "Age", "City", "Role"]
    assert d.table.item(0, 0).text() == "Alice"
    assert d.table.item(3, 0).text() == "Diana"
    assert d._loading is False
    print("[PASS] test_load_sample_fills_four_by_four")


# ─── Импорт файла ───────────────────────────────────────────────────────────

def test_import_csv_comma_auto():
    """Автоопределение запятой по первой строке."""
    path = _temp_file("Name,Age\nAlice,30\nBob,25\n")
    try:
        _patch_file_dialog(open_path=path)
        d = CSVEditorDialog()
        d.import_csv()
        assert d.table.columnCount() == 2
        assert d.table.rowCount() == 2
        assert d.table.horizontalHeaderItem(0).text() == "Name"
        assert d.table.item(1, 0).text() == "Bob"
        assert _FakeMessageBox.criticals == []
    finally:
        _restore()
        os.remove(path)
    print("[PASS] test_import_csv_comma_auto")


def test_import_csv_tab_auto():
    """TSV с табуляцией определяется автоматически."""
    path = _temp_file("A\tB\tC\n1\t2\t3\n", suffix=".tsv")
    try:
        _patch_file_dialog(open_path=path)
        d = CSVEditorDialog()
        d.import_csv()
        assert d.table.columnCount() == 3
        assert d.table.horizontalHeaderItem(2).text() == "C"
        assert d.table.item(0, 2).text() == "3"
    finally:
        _restore()
        os.remove(path)
    print("[PASS] test_import_csv_tab_auto")


def test_import_csv_with_bom_strips_it_from_header():
    """Файл с BOM (utf-8-sig) не оставляет BOM в имени первого столбца."""
    path = _temp_file("Name,City\nAlice,Moscow\n", encoding="utf-8-sig")
    try:
        _patch_file_dialog(open_path=path)
        d = CSVEditorDialog()
        d.import_csv()
        assert d.table.horizontalHeaderItem(0).text() == "Name"
    finally:
        _restore()
        os.remove(path)
    print("[PASS] test_import_csv_with_bom_strips_it_from_header")


def test_import_csv_explicit_delimiters_do_not_break():
    """BUG_010: явный выбор каждого разделителя успешно импортирует файл."""
    cases = [
        ("Comma (,)", "2024,January\n10,ok\n", 2, "January"),
        ("Tab", "2024\tJanuary\n10\tok\n", 2, "January"),
        ("Semicolon (;)", "2024;January\n10;ok\n", 2, "January"),
        ("Pipe (|)", "2024|January\n10|ok\n", 2, "January"),
    ]
    try:
        for label, content, cols, header in cases:
            path = _temp_file(content)
            try:
                _patch_file_dialog(open_path=path)
                d = CSVEditorDialog()
                d.delimiter_combo.setCurrentText(label)
                d.import_csv()
                assert _FakeMessageBox.criticals == [], (label, _FakeMessageBox.criticals)
                assert d.table.columnCount() == cols, label
                assert d.table.horizontalHeaderItem(1).text() == header, label
                assert d.table.item(0, 1).text() == "ok", label
            finally:
                os.remove(path)
    finally:
        _restore()
    print("[PASS] test_import_csv_explicit_delimiters_do_not_break")


def test_import_csv_cancelled_keeps_table():
    """Отмена диалога выбора файла ничего не меняет."""
    d = CSVEditorDialog()
    d._load_sample()
    try:
        _patch_file_dialog(open_path="")
        d.import_csv()
        assert d.table.rowCount() == 4
        assert _FakeMessageBox.criticals == []
        assert _FakeFileDialog.calls == ["open"]
    finally:
        _restore()
    print("[PASS] test_import_csv_cancelled_keeps_table")


def test_import_csv_empty_file_returns_quietly():
    """Пустой файл не приводит ни к падению, ни к сообщению об ошибке."""
    path = _temp_file("")
    try:
        _patch_file_dialog(open_path=path)
        d = CSVEditorDialog()
        d.import_csv()
        assert _FakeMessageBox.criticals == []
        assert d.table.rowCount() == 0
        assert d._loading is False
    finally:
        _restore()
        os.remove(path)
    print("[PASS] test_import_csv_empty_file_returns_quietly")


def test_import_csv_error_reports_critical():
    """Ошибка чтения (путь указывает на каталог) показывается через critical."""
    tmpdir = tempfile.mkdtemp()
    try:
        _patch_file_dialog(open_path=tmpdir)
        _patch_message_box()
        d = CSVEditorDialog()
        d.import_csv()
        assert len(_FakeMessageBox.criticals) == 1, _FakeMessageBox.criticals
        title, text = _FakeMessageBox.criticals[0]
        assert title == "Error"
        assert text
        assert d._loading is False
    finally:
        _restore()
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_import_csv_error_reports_critical")


# ─── Правка таблицы ─────────────────────────────────────────────────────────

def test_add_row_appends_empty_row():
    """«Add Row» добавляет строку в конец, не трогая существующие."""
    d = CSVEditorDialog()
    d._load_sample()
    d._add_row()
    assert d.table.rowCount() == 5
    assert d.table.item(4, 0) is None
    assert d.table.item(0, 0).text() == "Alice"
    print("[PASS] test_add_row_appends_empty_row")


def test_add_row_on_empty_table():
    """Добавление строки в пустую таблицу работает без исключений."""
    d = CSVEditorDialog()
    d._add_row()
    assert d.table.rowCount() == 1
    print("[PASS] test_add_row_on_empty_table")


def test_add_col_extends_headers():
    """Новая колонка получает подпись Col N, старые подписи сохраняются."""
    d = CSVEditorDialog()
    d._load_rows([["Name", "Age"], ["Alice", "30"]])
    d._add_col()
    assert d.table.columnCount() == 3
    assert d.table.horizontalHeaderItem(0).text() == "Name"
    assert d.table.horizontalHeaderItem(1).text() == "Age"
    assert d.table.horizontalHeaderItem(2).text() == "Col 3"
    assert d.table.item(0, 0).text() == "Alice"
    print("[PASS] test_add_col_extends_headers")


def test_add_col_on_empty_table_creates_placeholder():
    """Колонка без заголовка получает имя Col 1."""
    d = CSVEditorDialog()
    d._add_col()
    assert d.table.columnCount() == 1
    assert d.table.horizontalHeaderItem(0).text() == "Col 1"
    print("[PASS] test_add_col_on_empty_table_creates_placeholder")


def test_on_cell_changed_is_safe():
    """Обработчик правки ячейки не падает и ничего не ломает."""
    d = CSVEditorDialog()
    d._load_sample()
    d._on_cell_changed(0, 0)
    d._loading = True
    d._on_cell_changed(0, 0)
    d._loading = False
    assert d.table.item(0, 0).text() == "Alice"
    print("[PASS] test_on_cell_changed_is_safe")


# ─── Экспорт ────────────────────────────────────────────────────────────────

def test_export_markdown_builds_table():
    """Markdown-таблица содержит заголовок, разделитель и все строки."""
    d = CSVEditorDialog()
    d._load_rows([["Name", "Age"], ["Alice", "30"], ["Bob", "25"]])
    d.export_markdown()
    md = d.selected_markdown
    lines = md.split("\n")
    assert lines[0] == "| Name | Age |"
    assert lines[1] == "| --- | --- |"
    assert lines[2] == "| Alice | 30 |"
    assert lines[3] == "| Bob | 25 |"
    assert d.result() == QDialog.DialogCode.Accepted
    print("[PASS] test_export_markdown_builds_table")


def test_export_markdown_with_missing_cells():
    """Пустые ячейки и отсутствующие заголовки заменяются пустой строкой."""
    d = CSVEditorDialog()
    d._load_rows([["A", "B"], ["1"]])
    d.export_markdown()
    lines = d.selected_markdown.split("\n")
    assert lines[0] == "| A | B |"
    assert lines[2] == "| 1 |  |"
    print("[PASS] test_export_markdown_with_missing_cells")


def test_export_markdown_empty_table():
    """Экспорт пустой таблицы даёт две строки без данных."""
    d = CSVEditorDialog()
    d.export_markdown()
    assert d.selected_markdown == "|  |\n|  |"
    print("[PASS] test_export_markdown_empty_table")


def test_export_csv_writes_headers_and_rows():
    """CSV-файл содержит заголовки и данные, читается обратно без потерь."""
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    try:
        _patch_file_dialog(save_path=path)
        d = CSVEditorDialog()
        d._load_rows([["Name", "City"], ["Alice", "Moscow"]])
        d.export_csv()
        with open(path, "r", encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f))
        assert rows == [["Name", "City"], ["Alice", "Moscow"]]
        assert _FakeFileDialog.calls == ["save"]
    finally:
        _restore()
        os.remove(path)
    print("[PASS] test_export_csv_writes_headers_and_rows")


def test_export_csv_missing_header_uses_placeholder():
    """Колонка без заголовка выгружается как Col<N>."""
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    try:
        _patch_file_dialog(save_path=path)
        d = CSVEditorDialog()
        d.table.setColumnCount(2)
        d.table.setRowCount(1)
        d.table.setItem(0, 0, QTableWidgetItem("x"))
        d.export_csv()
        with open(path, "r", encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f))
        assert rows[0] == ["Col0", "Col1"]
        assert rows[1] == ["x", ""]
    finally:
        _restore()
        os.remove(path)
    print("[PASS] test_export_csv_missing_header_uses_placeholder")


def test_export_csv_autonamed_column_from_add_col():
    """Подпись, созданная «Add Column», уходит в файл как есть."""
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    try:
        _patch_file_dialog(save_path=path)
        d = CSVEditorDialog()
        d._add_col()
        d.export_csv()
        with open(path, "r", encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f))
        assert rows[0] == ["Col 1"]
    finally:
        _restore()
        os.remove(path)
    print("[PASS] test_export_csv_autonamed_column_from_add_col")


def test_export_csv_cancelled_writes_nothing():
    """Отмена выбора файла не создаёт файл и не бросает исключений."""
    tmpdir = tempfile.mkdtemp()
    try:
        _patch_file_dialog(save_path="")
        d = CSVEditorDialog()
        d._load_sample()
        d.export_csv()
        assert os.listdir(tmpdir) == []
        assert _FakeFileDialog.calls == ["save"]
    finally:
        _restore()
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("[PASS] test_export_csv_cancelled_writes_nothing")


def main():
    tests = [
        test_defaults,
        test_detect_delimiter_auto_tab_wins,
        test_detect_delimiter_auto_semicolon_and_pipe,
        test_detect_delimiter_explicit_returns_single_character,
        test_load_rows_sets_headers_and_cells,
        test_load_rows_empty_clears_and_resets_flag,
        test_load_rows_ignores_cells_beyond_header,
        test_load_rows_handles_short_rows,
        test_load_sample_fills_four_by_four,
        test_import_csv_comma_auto,
        test_import_csv_tab_auto,
        test_import_csv_with_bom_strips_it_from_header,
        test_import_csv_explicit_delimiters_do_not_break,
        test_import_csv_cancelled_keeps_table,
        test_import_csv_empty_file_returns_quietly,
        test_import_csv_error_reports_critical,
        test_add_row_appends_empty_row,
        test_add_row_on_empty_table,
        test_add_col_extends_headers,
        test_add_col_on_empty_table_creates_placeholder,
        test_on_cell_changed_is_safe,
        test_export_markdown_builds_table,
        test_export_markdown_with_missing_cells,
        test_export_markdown_empty_table,
        test_export_csv_writes_headers_and_rows,
        test_export_csv_missing_header_uses_placeholder,
        test_export_csv_autonamed_column_from_add_col,
        test_export_csv_cancelled_writes_nothing,
    ]
    for t in tests:
        t()
    print("\nAll CSV editor tests passed!")


if __name__ == "__main__":
    main()
