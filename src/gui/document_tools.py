"""Document tools: audit, TOC, snippets, table generator, readability, design style, merge, stats, revision history."""

import os
import re
import hashlib
import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QMessageBox, QInputDialog, QMenu, QDialog
)
from PyQt6.QtGui import QCursor
from PyQt6.QtCore import Qt
from src.gui.translations import TRANSLATIONS
from src.gui.dialogs import (
    DocumentAuditorDialog, ReadabilityDashboardDialog,
    MarkdownTOCDialog, SnippetsDialog, MarkdownTableDialog,
    PDFStyleEditorDialog, RevisionHistoryDialog
)

logger = logging.getLogger("MarkdownToPDF.document_tools")


def goto_editor_line(window, line_num: int):
    cursor = window.live_editor.textCursor()
    cursor.movePosition(cursor.MoveOperation.Start)
    for _ in range(line_num - 1):
        cursor.movePosition(cursor.MoveOperation.Down)
    cursor.movePosition(cursor.MoveOperation.StartOfLine)
    cursor.movePosition(cursor.MoveOperation.EndOfLine, cursor.MoveMode.KeepAnchor)
    window.live_editor.setTextCursor(cursor)
    window.live_editor.setFocus()


def show_document_audit(window):
    text = window.live_editor.toPlainText()
    lines = text.splitlines()
    issues = []
    t = lambda k: TRANSLATIONS[window.current_lang].get(k, k)

    last_level = 0

    base_dir = None
    if window.current_workspace_file:
        base_dir = os.path.dirname(window.current_workspace_file)
    elif window.selected_files:
        base_dir = os.path.dirname(window.selected_files[0])
    else:
        base_dir = os.getcwd()

    for idx, line in enumerate(lines):
        line_num = idx + 1

        header_match = re.match(r'^(#{1,6})\s+(.*)$', line)
        if header_match:
            level = len(header_match.group(1))
            title = header_match.group(2).strip()

            if not title:
                issues.append({
                    "line": line_num,
                    "type": t('audit_type_struct'),
                    "desc": "Пустой заголовок" if window.current_lang == "ru" else "Empty header level"
                })
            else:
                if level > last_level + 1:
                    issues.append({
                        "line": line_num,
                        "type": t('audit_type_struct'),
                        "desc": f"Пропуск уровня заголовка: переход с H{last_level} на H{level}" if window.current_lang == "ru" else f"Skipped header level: H{last_level} to H{level}"
                    })
                last_level = level

        if '"' in line:
            issues.append({
                "line": line_num,
                "type": t('audit_type_typo'),
                "desc": 'Использование прямых кавычек " вместо «»' if window.current_lang == "ru" else 'Straight quotes (") used instead of curly/angled quotes'
            })

        if re.search(r'[^ ] {2,}[^ ]', line):
            issues.append({
                "line": line_num,
                "type": t('audit_type_typo'),
                "desc": 'Обнаружено несколько последовательных пробелов' if window.current_lang == "ru" else 'Multiple consecutive spaces detected'
            })

        punc_matches = re.finditer(r'([,;:])([^\s\d])', line)
        for m in punc_matches:
            char = m.group(1)
            issues.append({
                "line": line_num,
                "type": t('audit_type_typo'),
                "desc": f'Пропущен пробел после знака препинания "{char}"' if window.current_lang == "ru" else f'Missing space after punctuation "{char}"'
            })

        if line.endswith(' ') and not line.endswith('  '):
            issues.append({
                "line": line_num,
                "type": t('audit_type_typo'),
                "desc": 'Лишний висячий пробел в конце строки' if window.current_lang == "ru" else 'Trailing space at end of line'
            })

        img_matches = re.finditer(r'!\[.*?\]\((.*?)\)', line)
        for m in img_matches:
            img_path = m.group(1).strip()
            if not img_path:
                issues.append({
                    "line": line_num,
                    "type": t('audit_type_media'),
                    "desc": 'Пустая ссылка на изображение' if window.current_lang == "ru" else 'Empty image reference link'
                })
            elif not img_path.startswith(('http://', 'https://', 'data:')):
                full_img_path = img_path
                if base_dir and not os.path.isabs(img_path):
                    full_img_path = os.path.join(base_dir, img_path)

                if not os.path.exists(full_img_path):
                    issues.append({
                        "line": line_num,
                        "type": t('audit_type_media'),
                        "desc": f'Локальный файл изображения не найден на диске: {img_path}' if window.current_lang == "ru" else f'Local image file not found on disk: {img_path}'
                    })

        link_matches = re.finditer(r'\[.*?\]\(\s*\)', line)
        for m in link_matches:
            issues.append({
                "line": line_num,
                "type": t('audit_type_media'),
                "desc": 'Обнаружена пустая гиперссылка []()' if window.current_lang == "ru" else 'Empty hyperlink []() detected'
            })

    dialog = DocumentAuditorDialog(issues, parent=window, lang=window.current_lang)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        if dialog.selected_line is not None:
            goto_editor_line(window, dialog.selected_line)


def auto_fix_document_issues(window):
    text = window.live_editor.toPlainText()
    lines = text.splitlines()
    fixed_lines = []

    for line in lines:
        if line.endswith(' ') and not line.endswith('  '):
            line = line.rstrip()

        if window.current_lang == "ru":
            line = re.sub(r'(?<=[\s(^])"', '«', line)
            line = re.sub(r'"(?=[\s,.:;!?)$]|$)', '»', line)
            while '"' in line:
                line = line.replace('"', '«', 1).replace('"', '»', 1)
        else:
            line = re.sub(r'(?<=[\s(^])"', '\u201c', line)
            line = re.sub(r'"(?=[\s,.:;!?)$]|$)', '\u201d', line)
            while '"' in line:
                line = line.replace('"', '\u201c', 1).replace('"', '\u201d', 1)

        line = re.sub(r'([,;:])([^\s\d])', r'\1 \2', line)

        fixed_lines.append(line)

    new_text = "\n".join(fixed_lines)
    if new_text != text:
        scroll_pos = window.live_editor.verticalScrollBar().value()
        window.live_editor.blockSignals(True)
        window.live_editor.setPlainText(new_text)
        window.live_editor.blockSignals(False)
        window._render_live_preview()
        window.update_text_statistics()
        window.live_editor.verticalScrollBar().setValue(scroll_pos)

        t = lambda k: TRANSLATIONS[window.current_lang].get(k, k)
        QMessageBox.information(
            window,
            t('msg_autofix_done_title'),
            t('msg_autofix_done_desc')
        )


def show_toc_generator(window):
    dialog = MarkdownTOCDialog(parent=window, lang=window.current_lang)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        max_depth = dialog.depth_combo.currentData()
        list_style = dialog.style_combo.currentData()
        use_anchors = dialog.anchors_chk.isChecked()

        text = window.live_editor.toPlainText()
        lines = text.splitlines()

        toc_lines = []
        h1_count = 0
        h2_count = 0
        h3_count = 0

        toc_lines.append("## Оглавление" if window.current_lang == "ru" else "## Table of Contents")
        toc_lines.append("")

        for line in lines:
            m = re.match(r'^(#{1,3})\s+(.*)$', line)
            if m:
                level = len(m.group(1))
                title = m.group(2).strip()

                if level > max_depth or not title:
                    continue

                anchor_name = re.sub(r'[^\w\s-]', '', title.lower()).strip().replace(' ', '-')

                if list_style == "bullet":
                    indent = "  " * (level - 1)
                    if use_anchors:
                        item_text = f"{indent}- [{title}](#{anchor_name})"
                    else:
                        item_text = f"{indent}- {title}"
                else:
                    if level == 1:
                        h1_count += 1
                        h2_count = 0
                        h3_count = 0
                        num_str = f"{h1_count}."
                        indent = ""
                    elif level == 2:
                        h2_count += 1
                        h3_count = 0
                        num_str = f"{h1_count}.{h2_count}."
                        indent = "  "
                    else:
                        h3_count += 1
                        num_str = f"{h1_count}.{h2_count}.{h3_count}."
                        indent = "    "

                    if use_anchors:
                        item_text = f"{indent}{num_str} [{title}](#{anchor_name})"
                    else:
                        item_text = f"{indent}{num_str} {title}"

                toc_lines.append(item_text)

        if len(toc_lines) <= 2:
            QMessageBox.warning(
                window,
                "Оглавление" if window.current_lang == "ru" else "TOC Builder",
                "Заголовки для построения оглавления не найдены!" if window.current_lang == "ru" else "No headings found to generate Table of Contents!"
            )
            return

        toc_content = "\n".join(toc_lines) + "\n\n"
        cursor = window.live_editor.textCursor()
        cursor.insertText(toc_content)
        window.live_editor.setTextCursor(cursor)
        window.live_editor.setFocus()


def update_markdown_toc_in_editor(window):
    text = window.live_editor.toPlainText()
    lines = text.splitlines()
    headings = []

    in_code_block = False

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        m = re.match(r'^(#{1,3})\s+(.*)$', line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            if title and not title.startswith("<!--") and not title.endswith("-->"):
                headings.append((level, title))

    toc_lines = []
    toc_lines.append("## " + ("Оглавление" if window.current_lang == "ru" else "Table of Contents"))
    toc_lines.append("")

    for level, title in headings:
        anchor_name = re.sub(r'[^\w\s-]', '', title.lower()).strip().replace(' ', '-')
        indent = "  " * (level - 1)
        toc_lines.append(f"{indent}- [{title}](#{anchor_name})")

    toc_body = "\n".join(toc_lines)

    start_marker = "<!-- TOC START -->"
    end_marker = "<!-- TOC END -->"

    if start_marker in text and end_marker in text:
        start_idx = text.find(start_marker)
        end_idx = text.find(end_marker) + len(end_marker)

        new_text = (
            text[:start_idx] +
            start_marker + "\n\n" +
            toc_body + "\n\n" +
            text[end_idx:]
        )
    else:
        cursor = window.live_editor.textCursor()
        insert_text = f"\n{start_marker}\n\n{toc_body}\n\n{end_marker}\n"

        cursor.insertText(insert_text)
        window.live_editor.setFocus()
        new_text = window.live_editor.toPlainText()

    if new_text != text:
        scroll_pos = window.live_editor.verticalScrollBar().value()
        cursor_pos = window.live_editor.textCursor().position()

        window.live_editor.blockSignals(True)
        window.live_editor.setPlainText(new_text)
        window.live_editor.blockSignals(False)

        window._render_live_preview()
        window.update_text_statistics()

        window.live_editor.verticalScrollBar().setValue(scroll_pos)

        cursor = window.live_editor.textCursor()
        cursor.setPosition(min(cursor_pos, len(new_text)))
        window.live_editor.setTextCursor(cursor)

    t = lambda k: TRANSLATIONS[window.current_lang].get(k, k)
    QMessageBox.information(
        window,
        t('msg_toc_updated_title'),
        t('msg_toc_updated_desc')
    )


def show_table_generator_dialog(window):
    from src.gui.dialogs import MarkdownTableDialog
    dialog = MarkdownTableDialog(window, lang=window.current_lang)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        rows = dialog.rows_spin.value()
        cols = dialog.cols_spin.value()

        table_md = "\n"
        table_md += "| " + " | ".join(f"Header {i+1}" for i in range(cols)) + " |\n"
        table_md += "| " + " | ".join("---" for _ in range(cols)) + " |\n"
        for r in range(rows):
            table_md += "| " + " | ".join(f"Row {r+1} Col {c+1}" for c in range(cols)) + " |\n"
        table_md += "\n"

        cursor = window.live_editor.textCursor()
        cursor.insertText(table_md)
        window.live_editor.setTextCursor(cursor)
        window.live_editor.setFocus()


def show_snippets_dialog(window):
    from src.gui.dialogs import SnippetsDialog
    dialog = SnippetsDialog(window, lang=window.current_lang)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        selected_markdown = dialog.get_selected_snippet()
        if selected_markdown:
            cursor = window.live_editor.textCursor()
            cursor.insertText(selected_markdown)
            window.live_editor.setFocus()


def show_readability_dashboard(window):
    text = window.live_editor.toPlainText()
    dialog = ReadabilityDashboardDialog(text, window, lang=window.current_lang)
    dialog.exec()


def show_design_style_dialog(window):
    from src.gui.dialogs import PDFStyleEditorDialog
    dialog = PDFStyleEditorDialog(window, lang=window.current_lang)

    current_paper = window.paper_combo.currentText()
    if current_paper in ["A4", "Letter", "A5"]:
        dialog.paper_combo.setCurrentText(current_paper)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        m_top = dialog.margin_top.value()
        m_right = dialog.margin_right.value()
        m_bottom = dialog.margin_bottom.value()
        m_left = dialog.margin_left.value()
        paper_size = dialog.paper_combo.currentText()

        window.margins_input.setText(f"{m_top}mm {m_right}mm {m_bottom}mm {m_left}mm")
        window.paper_combo.setCurrentText(paper_size)

        font_family = dialog.font_combo.currentText()
        font_size = dialog.font_size_spin.value()
        line_height = dialog.line_height_combo.currentText()
        align = dialog.align_combo.currentData()

        h_color = dialog.h_color_btn.color.name()
        quote_color = dialog.quote_color_btn.color.name()
        code_bg = dialog.code_bg_btn.color.name()

        css_content = f"""/* Custom PDF Theme Generated visually by PDF Layout & Style Designer */
@page {{
    size: {paper_size};
    margin: {m_top}mm {m_right}mm {m_bottom}mm {m_left}mm;
}}

body {{
    font-family: "{font_family}", "Helvetica Neue", Arial, sans-serif;
    font-size: {font_size}px;
    line-height: {line_height};
    text-align: {align};
    color: #2c3e50;
    background-color: #ffffff;
}}

h1, h2, h3, h4, h5, h6 {{
    color: {h_color};
    font-family: "{font_family}", sans-serif;
    font-weight: bold;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}}

h1 {{
    border-bottom: 2px solid {h_color};
    padding-bottom: 5px;
    font-size: 2em;
}}

h2 {{
    font-size: 1.5em;
}}

blockquote {{
    border-left: 5px solid {quote_color};
    background-color: #fcfcfc;
    padding: 10px 15px;
    margin: 1.5em 0;
    color: #555555;
    font-style: italic;
}}

pre, code {{
    font-family: "Courier New", Courier, monospace;
    font-size: 0.9em;
}}

pre {{
    background-color: {code_bg};
    border: 1px solid #dfe4ea;
    border-radius: 4px;
    padding: 12px;
    overflow-x: auto;
    margin: 1.5em 0;
}}

code {{
    background-color: {code_bg};
    padding: 2px 4px;
    border-radius: 3px;
}}
"""
        os.makedirs("templates", exist_ok=True)
        theme_path = os.path.abspath("templates/custom_theme.css")
        try:
            with open(theme_path, "w", encoding="utf-8") as f:
                f.write(css_content)
            window.custom_css_input.setText(theme_path)
            window._render_live_preview()
            QMessageBox.information(
                window,
                window.tr_msg("msg_theme_created_title"),
                window.tr_msg("msg_theme_created_desc").format(theme_path)
            )
        except Exception as e:
            logger.error("Failed to save custom theme: %s", e)
            QMessageBox.critical(window, "Error", f"Failed to save custom theme:\n{e}")


def show_merge_dialog(window):
    from src.gui.dialogs import DocumentBuilderDialog
    dialog = DocumentBuilderDialog(window, lang=window.current_lang)
    dialog.exec()


def show_stats_menu(window):
    menu = QMenu(window)
    t = lambda k: TRANSLATIONS[window.current_lang].get(k, k)

    act_dashboard = menu.addAction(t('dashboard_title'))
    act_goal = menu.addAction("🎯 " + t('goal_title') + "...")

    action = menu.exec(QCursor.pos())
    if action == act_dashboard:
        show_readability_dashboard(window)
    elif action == act_goal:
        set_writing_goal(window)


def set_writing_goal(window):
    t = lambda k: TRANSLATIONS[window.current_lang].get(k, k)
    val, ok = QInputDialog.getInt(
        window, t('goal_title'), t('goal_prompt'), window.writing_goal, min=0
    )
    if ok:
        window.writing_goal = val
        window.goal_celebrated = False
        window.update_text_statistics()


def show_revision_history(window):
    filepath = window.current_workspace_file
    if not filepath and window.selected_files:
        filepath = window.selected_files[0]

    if not filepath:
        QMessageBox.warning(window, window.tr_msg("msg_file_not_found"), window.tr_msg("history_empty"))
        return

    from src.config import AppConfig
    file_hash = hashlib.md5(os.path.abspath(filepath).encode('utf-8')).hexdigest()
    file_backup_dir = os.path.join(AppConfig.backups_dir(), file_hash)

    dialog = RevisionHistoryDialog(file_backup_dir, parent=window, lang=window.current_lang)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        if dialog.selected_content is not None:
            window.live_editor.blockSignals(True)
            window.live_editor.setPlainText(dialog.selected_content)
            window.live_editor.blockSignals(False)
            window._render_live_preview()
            window.update_text_statistics()
            window.append_log(window.tr_msg("log_draft_restored"))


def save_revision(window):
    filepath = window.current_workspace_file
    if not filepath and window.selected_files:
        filepath = window.selected_files[0]

    if not filepath or not os.path.exists(filepath):
        return

    text = window.live_editor.toPlainText()
    if not text.strip() or window.is_welcome_doc_active:
        return

    try:
        from src.config import AppConfig

        file_hash = hashlib.md5(os.path.abspath(filepath).encode('utf-8')).hexdigest()
        file_backup_dir = os.path.join(AppConfig.backups_dir(), file_hash)
        os.makedirs(file_backup_dir, exist_ok=True)

        backups = sorted(os.listdir(file_backup_dir))
        if backups:
            latest_backup_path = os.path.join(file_backup_dir, backups[-1])
            try:
                with open(latest_backup_path, "r", encoding="utf-8") as f:
                    latest_content = f.read()
                if latest_content == text:
                    return
            except Exception:
                pass

        if len(backups) >= 20:
            for b in backups[:-19]:
                try:
                    os.remove(os.path.join(file_backup_dir, b))
                except Exception:
                    pass

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        words = len([w for w in text.split() if w.strip()])
        backup_filename = f"{timestamp}_{words}.md"
        backup_filepath = os.path.join(file_backup_dir, backup_filename)
        with open(backup_filepath, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception as e:
        logger.error("Failed to save revision backup: %s", e)


def autosave_draft(window):
    if window.is_welcome_doc_active:
        return
    text = window.live_editor.toPlainText().strip()
    if not text:
        if os.path.exists(window.draft_path):
            try:
                os.remove(window.draft_path)
            except Exception:
                pass
        return
    try:
        with open(window.draft_path, "w", encoding="utf-8") as f:
            f.write(window.live_editor.toPlainText())
    except Exception as e:
        logger.error("Failed to autosave draft: %s", e)

    if window.current_workspace_file and os.path.exists(window.current_workspace_file):
        try:
            with open(window.current_workspace_file, "w", encoding="utf-8") as f:
                f.write(window.live_editor.toPlainText())
        except Exception as e:
            logger.error("Failed to autosave workspace file: %s", e)

    save_revision(window)


def restore_draft_if_exists(window):
    if os.path.exists(window.draft_path):
        try:
            with open(window.draft_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content:
                window.is_welcome_doc_active = False
                window.live_editor.blockSignals(True)
                window.live_editor.setPlainText(content)
                window.live_editor.blockSignals(False)
                window._render_live_preview()
                window.append_log(window.tr_msg("log_draft_restored"))
        except Exception as e:
            logger.error("Failed to restore draft: %s", e)


def estimate_readability(text, lang):
    words = [w.strip(",.!?()\"';:") for w in text.split() if w.strip()]
    if not words:
        return 100, "N/A"

    sentences = [s for s in re.split(r'[.!?]+', text) if s.strip()]
    total_words = len(words)
    total_sentences = max(len(sentences), 1)

    vowels_ru = set("аоэиуыеёюяаоэиуыеёюя")
    vowels_en = set("aeiouy")

    syllables = 0
    for word in words:
        word_lower = word.lower()
        if lang == "ru":
            count = sum(1 for c in word_lower if c in vowels_ru)
        else:
            count = sum(1 for c in word_lower if c in vowels_en)
        syllables += max(count, 1)

    if lang == "ru":
        score = 206.835 - 1.3 * (total_words / total_sentences) - 60.1 * (syllables / total_words)
    else:
        score = 206.835 - 1.015 * (total_words / total_sentences) - 84.6 * (syllables / total_words)

    score = max(0, min(100, score))

    if score >= 70:
        lvl = TRANSLATIONS[lang].get('dashboard_readability_easy', 'Easy')
    elif score >= 40:
        lvl = TRANSLATIONS[lang].get('dashboard_readability_medium', 'Standard')
    else:
        lvl = TRANSLATIONS[lang].get('dashboard_readability_hard', 'Difficult')

    return round(score, 1), lvl
