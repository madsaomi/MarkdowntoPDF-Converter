import csv
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QFileDialog, QLineEdit,
    QMessageBox, QHeaderView, QComboBox
)
from PyQt6.QtCore import Qt


class CSVEditorDialog(QDialog):
    """CSV/TSV table editor with import and Markdown export."""

    def __init__(self, parent=None, lang="ru"):
        super().__init__(parent)
        self.lang = lang
        self.setWindowTitle("📊 CSV Table Editor")
        self.setMinimumSize(700, 480)

        layout = QVBoxLayout(self)

        # Import row
        import_row = QHBoxLayout()
        self.btn_import = QPushButton("📂 Import CSV/TSV")
        self.btn_import.clicked.connect(self.import_csv)
        import_row.addWidget(self.btn_import)

        self.delimiter_combo = QComboBox()
        self.delimiter_combo.addItems(["Auto", "Comma (,)", "Tab", "Semicolon (;)", "Pipe (|)"])
        import_row.addWidget(QLabel("Delimiter:"))
        import_row.addWidget(self.delimiter_combo)

        self.btn_load_sample = QPushButton("📋 Load Sample")
        self.btn_load_sample.clicked.connect(self._load_sample)
        import_row.addWidget(self.btn_load_sample)

        import_row.addStretch()
        layout.addLayout(import_row)

        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { background: rgba(30, 41, 59, 0.85); gridline-color: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: #e2e8f0; }
            QTableWidget::item { padding: 4px; }
            QTableWidget::item:selected { background-color: rgba(99, 102, 241, 0.4); color: white; }
            QHeaderView::section { background: rgba(51, 65, 85, 0.7); border: 1px solid rgba(255,255,255,0.1); padding: 4px; font-weight: bold; color: #94a3b8; }
        """)
        self.table.cellChanged.connect(self._on_cell_changed)
        layout.addWidget(self.table)

        # Export row
        export_row = QHBoxLayout()
        self.btn_to_md = QPushButton("📝 Export as Markdown Table")
        self.btn_to_md.clicked.connect(self.export_markdown)
        export_row.addWidget(self.btn_to_md)

        self.btn_to_csv = QPushButton("💾 Export as CSV")
        self.btn_to_csv.clicked.connect(self.export_csv)
        export_row.addWidget(self.btn_to_csv)

        self.btn_add_row = QPushButton("➕ Add Row")
        self.btn_add_row.clicked.connect(self._add_row)
        export_row.addWidget(self.btn_add_row)

        self.btn_add_col = QPushButton("➕ Add Column")
        self.btn_add_col.clicked.connect(self._add_col)
        export_row.addWidget(self.btn_add_col)

        export_row.addStretch()
        layout.addLayout(export_row)

        # Close
        btn_row = QHBoxLayout()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        self.selected_markdown = ""
        self._loading = False

    def _detect_delimiter(self, line: str) -> str:
        delim = self.delimiter_combo.currentText()
        if delim == "Auto":
            if "\t" in line:
                return "\t"
            if ";" in line and line.count(";") > line.count(","):
                return ";"
            if "|" in line and line.count("|") > line.count(","):
                return "|"
            return ","
        mapping = {"Comma (,)": ",", "\t": "Tab", ";": "Semicolon (;)", "|": "Pipe (|)"}
        return delim

    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV (*.csv *.tsv *.txt)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                lines = f.readlines()
            if not lines:
                return
            delim = self._detect_delimiter(lines[0])
            reader = csv.reader(lines, delimiter=delim)
            rows = list(reader)
            self._load_rows(rows)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _load_sample(self):
        rows = [
            ["Name", "Age", "City", "Role"],
            ["Alice", "30", "Moscow", "Developer"],
            ["Bob", "25", "Berlin", "Designer"],
            ["Charlie", "35", "London", "Manager"],
            ["Diana", "28", "Paris", "Analyst"],
        ]
        self._load_rows(rows)

    def _load_rows(self, rows: list[list[str]]):
        self._loading = True
        self.table.clearContents()
        if not rows:
            return
        headers = rows[0]
        data = rows[1:]
        self.table.setColumnCount(len(headers))
        self.table.setRowCount(len(data))
        self.table.setHorizontalHeaderLabels(headers)
        for r, row in enumerate(data):
            for c, val in enumerate(row):
                if c < len(headers):
                    self.table.setItem(r, c, QTableWidgetItem(val))
        self._loading = False

    def _on_cell_changed(self, row, col):
        if not self._loading:
            pass  # Live editing, no special action needed

    def _add_row(self):
        cols = self.table.columnCount()
        self.table.insertRow(self.table.rowCount())

    def _add_col(self):
        self.table.setColumnCount(self.table.columnCount() + 1)
        self.table.setHorizontalHeaderLabels(
            [self.table.horizontalHeaderItem(i).text() if self.table.horizontalHeaderItem(i) else f"Col {i+1}"
             for i in range(self.table.columnCount())]
        )

    def export_markdown(self):
        headers = [self.table.horizontalHeaderItem(c).text() if self.table.horizontalHeaderItem(c) else "" for c in range(self.table.columnCount())]
        sep = "| " + " | ".join(headers) + " |"
        line = "| " + " | ".join("---" for _ in headers) + " |"
        data_rows = []
        for r in range(self.table.rowCount()):
            cells = []
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                cells.append(item.text() if item else "")
            data_rows.append("| " + " | ".join(cells) + " |")
        md = "\n".join([sep, line] + data_rows)
        self.selected_markdown = md
        self.accept()

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV (*.csv)")
        if not path:
            return
        headers = [self.table.horizontalHeaderItem(c).text() if self.table.horizontalHeaderItem(c) else f"Col{c}" for c in range(self.table.columnCount())]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for r in range(self.table.rowCount()):
                row = []
                for c in range(self.table.columnCount()):
                    item = self.table.item(r, c)
                    row.append(item.text() if item else "")
                writer.writerow(row)
