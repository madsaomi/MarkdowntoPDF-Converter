"""File and folder selection, recent files, workspace explorer management."""

import os
import logging
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QListWidgetItem
from PyQt6.QtCore import Qt

logger = logging.getLogger("MarkdownToPDF.file_manager")


def select_custom_css(window):
    filepath, _ = QFileDialog.getOpenFileName(
        window, "Выберите CSS файл", "", "CSS Files (*.css);;All Files (*)"
    )
    if filepath:
        window.custom_css_input.setText(filepath)


def select_docx_template(window):
    filepath, _ = QFileDialog.getOpenFileName(
        window, "Выберите шаблон DOCX", "", "Word Documents (*.docx);;All Files (*)"
    )
    if filepath:
        window.docx_template_input.setText(filepath)


def select_files(window):
    files, _ = QFileDialog.getOpenFileNames(
        window, "Выберите Markdown файлы", "",
        "Markdown Files (*.md);;All Files (*)"
    )
    if files:
        window.selected_files = files
        window.active_workspace_folder = None
        window.explorer_group.hide()
        for f in files:
            add_to_recent(window, f)
        names = ", ".join(os.path.basename(f) for f in files)
        window.file_label.setText(window.tr_msg("files_selected", len(files), names))
        window.btn_convert.setEnabled(True)
        window.btn_watch.setEnabled(len(files) == 1)
        window.log_output.clear()
        window.progress_bar.setValue(0)
        window.append_log(window.tr_msg("log_selected", len(files)))
        window.update_preview(files[0])


def select_folder(window):
    folder = QFileDialog.getExistingDirectory(window, "Выберите папку с .md файлами")
    if folder:
        md_files = [
            os.path.join(folder, f)
            for f in os.listdir(folder) if f.endswith('.md')
        ]
        if not md_files:
            QMessageBox.warning(window, window.tr_msg("msg_folder_empty_title"), window.tr_msg("msg_folder_empty"))
            return
        window.selected_files = md_files
        window.active_workspace_folder = folder
        window.file_label.setText(window.tr_msg("folder_selected", os.path.basename(folder), len(md_files)))
        window.btn_convert.setEnabled(True)
        window.btn_watch.setEnabled(False)
        window.log_output.clear()
        window.progress_bar.setValue(0)
        window.append_log(window.tr_msg("log_found_folder", len(md_files)))

        update_workspace_explorer(window)
        window.explorer_group.show()
        window.update_preview(md_files[0])


def add_to_recent(window, filepath: str):
    recent = window.settings.value("recent_files", [], list)
    if filepath in recent:
        recent.remove(filepath)
    recent.insert(0, filepath)
    recent = recent[:window.MAX_RECENT]
    window.settings.setValue("recent_files", recent)
    update_recent_menu(window)


def update_recent_menu(window):
    window.recent_menu.clear()
    recent = window.settings.value("recent_files", [], list)
    if not recent:
        act = window.recent_menu.addAction(window.tr_msg("menu_empty"))
        act.setEnabled(False)
        return
    for filepath in recent:
        act = window.recent_menu.addAction(os.path.basename(filepath))
        act.setData(filepath)
        act.triggered.connect(lambda checked, p=filepath: open_recent(window, p))


def open_recent(window, filepath: str):
    if not os.path.exists(filepath):
        QMessageBox.warning(window, window.tr_msg("msg_file_not_found"), window.tr_msg("msg_file_moved", filepath))
        return
    window.selected_files = [filepath]
    window.active_workspace_folder = None
    window.explorer_group.hide()
    window.file_label.setText(os.path.basename(filepath))
    window.btn_convert.setEnabled(True)
    window.btn_watch.setEnabled(True)
    window.log_output.clear()
    window.progress_bar.setValue(0)
    window.append_log(window.tr_msg("log_opened_recent", filepath))
    window.update_preview(filepath)


def open_output_folder(window):
    out_dir = window.last_output_dir
    if not out_dir:
        if window.selected_files:
            out_dir = os.path.dirname(window.selected_files[0])
        else:
            out_dir = os.getcwd()

    if os.path.exists(out_dir):
        try:
            os.startfile(out_dir)
        except Exception as e:
            logger.error("Failed to open output folder: %s", e)
    else:
        QMessageBox.warning(window, window.tr_msg("msg_file_not_found"), f"Folder not found:\n{out_dir}")


def update_workspace_explorer(window):
    if not window.active_workspace_folder or not os.path.exists(window.active_workspace_folder):
        window.explorer_group.hide()
        return

    window.explorer_list.blockSignals(True)
    window.explorer_list.clear()

    md_files = []
    try:
        for f in os.listdir(window.active_workspace_folder):
            if f.endswith('.md'):
                md_files.append(os.path.join(window.active_workspace_folder, f))
    except Exception as e:
        logger.error("Failed to list files in folder %s: %s", window.active_workspace_folder, e)

    md_files.sort(key=lambda x: os.path.basename(x).lower())
    window.selected_files = md_files

    for file_path in md_files:
        item = QListWidgetItem(os.path.basename(file_path))
        item.setData(Qt.ItemDataRole.UserRole, file_path)
        window.explorer_list.addItem(item)

    if md_files:
        if not window.current_workspace_file or window.current_workspace_file not in md_files:
            window.current_workspace_file = md_files[0]
            try:
                with open(window.current_workspace_file, "r", encoding="utf-8") as f:
                    content = f.read()
                window.is_welcome_doc_active = False
                window.live_editor.blockSignals(True)
                window.live_editor.setPlainText(content)
                window.live_editor.blockSignals(False)
                window._render_live_preview()
                window.update_text_statistics()
            except Exception as e:
                logger.error("Failed to load initial file in explorer: %s", e)

        for row in range(window.explorer_list.count()):
            li = window.explorer_list.item(row)
            if li.data(Qt.ItemDataRole.UserRole) == window.current_workspace_file:
                li.setSelected(True)
                window.explorer_list.setCurrentItem(li)
                break

    window.explorer_list.blockSignals(False)


def load_workspace_file(window, item):
    file_path = item.data(Qt.ItemDataRole.UserRole)
    if not file_path or not os.path.exists(file_path):
        return

    save_current_workspace_file(window)
    window.current_workspace_file = file_path

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        window.is_welcome_doc_active = False
        window.live_editor.blockSignals(True)
        window.live_editor.setPlainText(content)
        window.live_editor.blockSignals(False)
        window._render_live_preview()
        window.update_text_statistics()

        for row in range(window.explorer_list.count()):
            li = window.explorer_list.item(row)
            if li.data(Qt.ItemDataRole.UserRole) == file_path:
                window.explorer_list.blockSignals(True)
                window.explorer_list.setCurrentItem(li)
                li.setSelected(True)
                window.explorer_list.blockSignals(False)
                break
    except Exception as e:
        logger.error("Failed to load workspace file %s: %s", file_path, e)


def save_current_workspace_file(window):
    if window.current_workspace_file and os.path.exists(window.current_workspace_file):
        try:
            content = window.live_editor.toPlainText()
            with open(window.current_workspace_file, "w", encoding="utf-8") as f:
                f.write(content)
            from src.gui.document_tools import save_revision
            save_revision(window)
        except Exception as e:
            logger.error("Failed to save workspace file: %s", e)


def filter_workspace_explorer(window, text):
    query = text.lower().strip()
    for row in range(window.explorer_list.count()):
        item = window.explorer_list.item(row)
        if not query or query in item.text().lower():
            item.setHidden(False)
        else:
            item.setHidden(True)
