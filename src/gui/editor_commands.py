"""Editor formatting commands and event filter for the live Markdown editor."""

import re
from PyQt6.QtCore import Qt, QEvent, QRegularExpression
from PyQt6.QtWidgets import QApplication


def _wrap_selection(window, prefix: str, suffix: str):
    cursor = window.live_editor.textCursor()
    text = cursor.selectedText()
    cursor.insertText(f"{prefix}{text}{suffix}")
    window.live_editor.setFocus()


def format_bold(window):
    _wrap_selection(window, "**", "**")


def format_italic(window):
    _wrap_selection(window, "*", "*")


def format_code(window):
    cursor = window.live_editor.textCursor()
    text = cursor.selectedText()
    if "\n" in text or "\r" in text:
        _wrap_selection(window, "\n```\n", "\n```\n")
    else:
        _wrap_selection(window, "`", "`")


def format_header(window, level: int):
    cursor = window.live_editor.textCursor()
    cursor.select(cursor.SelectionType.LineUnderCursor)
    text = cursor.selectedText().lstrip("#").lstrip()
    cursor.insertText(f"{'#' * level} {text}")
    window.live_editor.setFocus()


def format_quote(window):
    cursor = window.live_editor.textCursor()
    cursor.select(cursor.SelectionType.LineUnderCursor)
    text = cursor.selectedText().lstrip(">").lstrip()
    cursor.insertText(f"> {text}")
    window.live_editor.setFocus()


def format_list(window):
    cursor = window.live_editor.textCursor()
    cursor.select(cursor.SelectionType.LineUnderCursor)
    text = cursor.selectedText().lstrip("-").lstrip()
    cursor.insertText(f"- {text}")
    window.live_editor.setFocus()


def insert_page_break(window):
    cursor = window.live_editor.textCursor()
    cursor.insertText('\n<div style="page-break-before: always;"></div>\n')
    window.live_editor.setFocus()


def format_markdown_table(table_lines):
    rows = []
    for line in table_lines:
        stripped = line.strip()
        if stripped.startswith('|'):
            stripped = stripped[1:]
        if stripped.endswith('|'):
            stripped = stripped[:-1]
        cols = [c.strip() for c in stripped.split('|')]
        rows.append(cols)

    if not rows:
        return table_lines

    has_separator = False
    if len(rows) > 1:
        sec_row = rows[1]
        if all(re.match(r'^:?-+:?$', c) for c in sec_row if c):
            has_separator = True

    col_count = max(len(r) for r in rows)
    col_widths = [0] * col_count
    for r in rows:
        for idx, val in enumerate(r):
            if idx < len(col_widths):
                col_widths[idx] = max(col_widths[idx], len(val))

    formatted = []
    for r_idx, r in enumerate(rows):
        fmt_cols = []
        for idx in range(col_count):
            val = r[idx] if idx < len(r) else ""
            width = col_widths[idx]

            if r_idx == 1 and has_separator:
                clean_sep = val.strip()
                if clean_sep.startswith(':') and clean_sep.endswith(':'):
                    col_align = "center"
                elif clean_sep.endswith(':'):
                    col_align = "right"
                else:
                    col_align = "left"

                if col_align == "center":
                    dashed = ":" + "-" * (width) + ":"
                elif col_align == "right":
                    dashed = "-" * (width + 1) + ":"
                elif col_align == "left" and clean_sep.startswith(':'):
                    dashed = ":" + "-" * (width + 1)
                else:
                    dashed = "-" * (width + 2)
                fmt_cols.append(dashed)
            else:
                padded = f" {val.ljust(width)} "
                fmt_cols.append(padded)

        formatted.append("|" + "|".join(fmt_cols) + "|")
    return formatted


def format_markdown_document(window):
    scroll_pos = window.live_editor.verticalScrollBar().value()

    old_text = window.live_editor.toPlainText()
    lines = old_text.splitlines()

    formatted_lines = []
    in_table = False
    table_buffer = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('|') and '|' in stripped:
            if not in_table:
                in_table = True
                table_buffer = [line]
            else:
                table_buffer.append(line)
        else:
            if in_table:
                try:
                    formatted_table = format_markdown_table(table_buffer)
                    formatted_lines.extend(formatted_table)
                except Exception:
                    formatted_lines.extend(table_buffer)
                in_table = False
                table_buffer = []
            formatted_lines.append(line.rstrip())

    if in_table:
        try:
            formatted_table = format_markdown_table(table_buffer)
            formatted_lines.extend(formatted_table)
        except Exception:
            formatted_lines.extend(table_buffer)

    idx = 0
    while idx < len(formatted_lines):
        line = formatted_lines[idx]
        if line.strip().startswith('#') and idx > 0:
            if formatted_lines[idx - 1].strip() != "":
                formatted_lines.insert(idx, "")
                idx += 1
        idx += 1

    new_text = "\n".join(formatted_lines)

    if new_text != old_text:
        window.live_editor.blockSignals(True)
        window.live_editor.setPlainText(new_text)
        window.live_editor.blockSignals(False)
        window._render_live_preview()
        window.update_text_statistics()
        window.live_editor.verticalScrollBar().setValue(scroll_pos)


def handle_event_filter(window, obj, event):
    """Handle auto-completion and key events for the editor. Returns True if handled."""
    if obj != window.live_editor or event.type() != QEvent.Type.KeyPress:
        return False

    key = event.key()
    text = event.text()

    pairs = {
        "(": ")", "[": "]", "{": "}",
        "\"": "\"", "'": "'", "`": "`", "<": ">"
    }
    wrap_pairs = {**pairs, "*": "*", "_": "_"}

    cursor = window.live_editor.textCursor()
    has_sel = cursor.hasSelection()

    # Backspace deletion of empty pairs
    if key == Qt.Key.Key_Backspace and not has_sel:
        pos = cursor.position()
        full_text = window.live_editor.toPlainText()
        if pos > 0 and pos < len(full_text):
            left_char = full_text[pos - 1]
            right_char = full_text[pos]
            if left_char in pairs and pairs[left_char] == right_char:
                cursor.deleteChar()
                cursor.deletePreviousChar()
                return True

    # Wrapping selection
    if has_sel and text in wrap_pairs:
        selected = cursor.selectedText()
        cursor.insertText(text + selected + wrap_pairs[text])
        return True

    # Autoclosing when typing opening character
    if not has_sel and text in pairs:
        cursor.insertText(text + pairs[text])
        cursor.movePosition(cursor.MoveOperation.PreviousCharacter)
        window.live_editor.setTextCursor(cursor)
        return True

    # Overtyping closing character
    if not has_sel and text in [")", "]", "}", "\"", "'", "`", ">"]:
        cursor.movePosition(cursor.MoveOperation.NextCharacter, cursor.MoveMode.KeepAnchor)
        next_char = cursor.selectedText()
        if next_char == text:
            cursor = window.live_editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.NextCharacter)
            window.live_editor.setTextCursor(cursor)
            return True

    return False
