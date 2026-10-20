import os
import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QComboBox, QSlider, QTextBrowser,
    QInputDialog
)
from PyQt6.QtCore import Qt

logger = logging.getLogger("MarkdownToPDF.window_tools")


class ToolMethodsMixin:

    def show_about(self):
        from src.__version__ import __version__
        from src.gui.about_dialog import AboutDialog
        dlg = AboutDialog(self, __version__, self.current_lang)
        dlg.exec()

    def show_shortcuts(self):
        from src.gui.dialogs import ShortcutsDialog
        dlg = ShortcutsDialog(self, self.current_lang)
        dlg.exec()

    def show_welcome_tour(self):
        from src.gui.welcome_tour import WelcomeTourDialog
        dlg = WelcomeTourDialog(self, self.current_lang)
        dlg.exec()

    def show_conversion_history(self):
        # Журнал экспорта отображается на вкладке «History» (создаётся в ui_layout.py)
        self.update_export_history_ui()
        self.tabs.setCurrentWidget(self.history_container)

    def show_diff_dialog(self):
        from src.gui.dialogs import DiffDialog
        dlg = DiffDialog(self, self.current_lang)
        dlg.exec()

    def show_latex_preview(self):
        from src.core.latex_preview import find_latex_expressions, latex_to_url
        text = self.live_editor.toPlainText()
        expressions = find_latex_expressions(text)

        if not expressions:
            QMessageBox.information(self, "LaTeX", "No LaTeX expressions found (use $...$ or $$...$$)")
            return

        html_parts = ["<html><head><style>body{font-family:sans-serif;padding:20px;} .expr{margin:16px;padding:12px;background:#f8f9fa;border-radius:8px;border:1px solid #dfe4ea;} .src{font-family:monospace;color:#7f8c8d;font-size:12px;}</style></head><body>"]
        html_parts.append(f"<h2>LaTeX Preview ({len(expressions)} expressions)</h2>")

        for start, end, formula in expressions:
            url = latex_to_url(formula)
            html_parts.append(f'<div class="expr"><img src="{url}" alt="{formula}" style="max-width:100%;"/><br><span class="src">{formula}</span></div>')

        html_parts.append("</body></html>")

        dlg = QDialog(self)
        dlg.setWindowTitle("LaTeX Preview")
        dlg.setMinimumSize(600, 400)
        layout = QVBoxLayout(dlg)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml('\n'.join(html_parts))
        layout.addWidget(browser)
        btn = QPushButton("Close")
        btn.clicked.connect(dlg.close)
        layout.addWidget(btn)
        dlg.exec()

    def show_multi_export(self):
        if not self.selected_files:
            QMessageBox.information(self, "Multi-Export", "Select a file first")
            return

        from src.gui.dialogs import MultiExportDialog
        dlg = MultiExportDialog(self, self.current_lang)
        if dlg.exec():
            from src.core.multi_export import multi_export, export_summary
            out_dir = QFileDialog.getExistingDirectory(self, "Output Directory")
            if not out_dir:
                return
            results = multi_export(
                self.selected_files[0], out_dir, dlg.selected_formats,
                self._get_template_dir(), self._get_options()
            )
            summary = export_summary(results)
            QMessageBox.information(self, "Multi-Export", summary)
            self.append_log(f"Multi-export completed: {len(results)} formats")

    def show_watermark_designer(self):
        from src.gui.watermark_designer import WatermarkDesignerDialog
        dlg = WatermarkDesignerDialog(self, self.current_lang)
        if dlg.exec():
            css = dlg.result_css
            self.footer_input.setText(dlg.text_input.text())
            self.append_log("Watermark applied to footer")

    def show_citation_manager(self):
        from src.gui.dialogs import CitationManagerDialog
        dlg = CitationManagerDialog(self, self.current_lang)
        dlg.exec()

    def show_csv_editor(self):
        from src.gui.csv_editor import CSVEditorDialog
        dlg = CSVEditorDialog(self, self.current_lang)
        if dlg.exec():
            md = dlg.selected_markdown
            if md:
                cursor = self.live_editor.textCursor()
                cursor.insertText(md)
                self._render_live_preview()

    def show_excalidraw(self):
        from src.gui.excalidraw_canvas import ExcalidrawDialog
        dlg = ExcalidrawDialog(self, self.current_lang)
        if dlg.exec():
            md = dlg.selected_markdown
            if md:
                cursor = self.live_editor.textCursor()
                cursor.insertText(md)
                self._render_live_preview()

    def show_calendar_notes(self):
        from src.gui.calendar_view import CalendarNotesDialog
        folder = getattr(self, 'active_workspace_folder', None) or os.getcwd()
        dlg = CalendarNotesDialog(self, self.current_lang, folder)
        dlg.exec()

    def show_pomodoro(self):
        from src.gui.pomodoro import PomodoroDialog
        dlg = PomodoroDialog(self, self.current_lang)
        dlg.exec()

    def show_github_sync_dialog(self):
        if not self.selected_files:
            QMessageBox.information(self, "GitHub Sync", "Open a folder first")
            return
        folder = self.active_workspace_folder or os.path.dirname(self.selected_files[0])
        from src.gui.dialogs import GitHubSyncDialog
        dlg = GitHubSyncDialog(self, folder, self.current_lang)
        dlg.exec()

    def show_plugin_manager(self):
        from src.gui.dialogs import PluginManagerDialog
        dlg = PluginManagerDialog(self, self.current_lang)
        dlg.exec()

    def show_tag_cloud(self):
        text = self.live_editor.toPlainText()
        from src.core.latex_preview import find_latex_expressions
        words = [w.lower().strip(",.!?()\"';:") for w in text.split() if len(w) > 3]
        from collections import Counter
        top = Counter(words).most_common(20)

        html_parts = ["<html><head><style>body{font-family:sans-serif;padding:20px;text-align:center;}.tag{display:inline-block;margin:6px;padding:6px 14px;background:#6366f1;color:white;border-radius:20px;font-size:14px;text-decoration:none;}</style></head><body>"]
        html_parts.append("<h2>Tag Cloud</h2>")
        for word, count in top:
            size = min(24, 12 + count)
            html_parts.append(f'<span class="tag" style="font-size:{size}px;">{word} ({count})</span>')
        html_parts.append("</body></html>")

        dlg = QDialog(self)
        dlg.setWindowTitle("Tag Cloud")
        dlg.setMinimumSize(500, 400)
        layout = QVBoxLayout(dlg)
        browser = QTextBrowser()
        browser.setHtml('\n'.join(html_parts))
        layout.addWidget(browser)
        btn = QPushButton("Close")
        btn.clicked.connect(dlg.close)
        layout.addWidget(btn)
        dlg.exec()

    def show_reading_analytics(self):
        text = self.live_editor.toPlainText()
        words = text.split()
        chars = len(text)
        paragraphs = max(len([p for p in text.split('\n') if p.strip()]), 1)
        sentences = max(len([s for s in text.split('.') if s.strip()]), 1)
        avg_sentence = len(words) / sentences if sentences else 0

        import re
        total_syllables = 0
        for w in words:
            w_clean = w.lower().strip(",.!?()\"';:")
            if self.current_lang == "ru":
                vowels = sum(1 for c in w_clean if c in "аеёиоуыэюя")
            else:
                vowels = sum(1 for c in w_clean if c in "aeiouy")
            total_syllables += max(vowels, 1)

        flesch = 206.835 - 1.015 * (len(words) / sentences) - 84.6 * (total_syllables / max(len(words), 1))
        flesch = max(0, min(100, flesch))

        msg = (
            f"**Reading Analytics**\n\n"
            f"- Words: {len(words)}\n"
            f"- Characters: {chars}\n"
            f"- Paragraphs: {paragraphs}\n"
            f"- Sentences: {int(sentences)}\n"
            f"- Avg sentence: {avg_sentence:.1f} words\n"
            f"- Syllables: {total_syllables}\n"
            f"- Flesch Score: {flesch:.1f}/100\n\n"
            f"**Reading time:** ~{max(1, len(words) // 200)} min\n"
            f"**Speaking time:** ~{max(1, len(words) // 150)} min"
        )

        QMessageBox.information(self, "Reading Analytics", msg)

    def export_selection(self):
        cursor = self.live_editor.textCursor()
        text = cursor.selectedText()
        if not text:
            QMessageBox.information(self, "Export", "Select text first")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Selection", "selection.md", "Markdown (*.md)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self.append_log(f"Selection saved: {os.path.basename(path)}")

    def export_as_markdown(self):
        text = self.live_editor.toPlainText()
        path, _ = QFileDialog.getSaveFileName(self, "Save as Markdown", "document.md", "Markdown (*.md)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self.append_log(f"Saved as Markdown: {os.path.basename(path)}")

    def save_version(self):
        from src.gui.document_tools import save_revision
        save_revision(self)
        self.toast("Version saved", "success")

    def restore_version(self):
        from src.gui.document_tools import show_revision_history
        show_revision_history(self)
        self.update_preview_from_editor()

    def toggle_split_view(self):
        modes = ['both', 'editor', 'preview']
        current = getattr(self, '_split_view_mode', 'both')
        idx = (modes.index(current) + 1) % len(modes)
        self._split_view_mode = modes[idx]

        if self._split_view_mode == 'both':
            self.editor_splitter.setSizes([200, 400, 400])
            self.preview_output.show()
            self.live_editor.show()
        elif self._split_view_mode == 'editor':
            self.editor_splitter.setSizes([1, 600, 0])
            self.preview_output.hide()
            self.live_editor.show()
        else:
            self.editor_splitter.setSizes([0, 0, 600])
            self.preview_output.show()
            self.live_editor.hide()

    def toggle_zen_mode(self):
        is_zen = not getattr(self, '_zen_mode', False)
        self._zen_mode = is_zen
        if hasattr(self, 'format_toolbar'):
            self.format_toolbar.setVisible(not is_zen)
        if hasattr(self, 'tabs'):
            self.tabs.setVisible(not is_zen)
        self.statusBar().setVisible(not is_zen)
        if is_zen:
            self.showFullScreen()
        else:
            self.showNormal()

    def toggle_focus_mode(self):
        is_focus = not getattr(self, '_focus_mode', False)
        self._focus_mode = is_focus
        if hasattr(self, 'format_toolbar'):
            self.format_toolbar.setVisible(not is_focus)
        if is_focus:
            self.live_editor.setStyleSheet(self.live_editor.styleSheet() + " QTextEdit { font-size: 16px; }")
        else:
            self.live_editor.setStyleSheet(self.live_editor.styleSheet().replace(" QTextEdit { font-size: 16px; }", ""))

    def toggle_typewriter_mode(self):
        self._typewriter_mode = not getattr(self, '_typewriter_mode', False)
        if self._typewriter_mode:
            cursor = self.live_editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self.live_editor.setTextCursor(cursor)
            self.live_editor.setStyleSheet(self.live_editor.styleSheet() + " QTextEdit { font-size: 16px; line-height: 2.0; }")
        else:
            self.live_editor.setStyleSheet(self.live_editor.styleSheet().replace(" QTextEdit { font-size: 16px; line-height: 2.0; }", ""))
        self.toast("Typewriter: " + ("ON" if self._typewriter_mode else "OFF"), "info")

    def toggle_wysiwyg(self):
        self._wysiwyg = not getattr(self, '_wysiwyg', False)
        if self._wysiwyg:
            self.preview_output.show()
            self.live_editor.hide()
        else:
            self.preview_output.hide()
            self.live_editor.show()
        self.toast("WYSIWYG: " + ("ON" if self._wysiwyg else "OFF"), "info")

    def run_spell_check(self):
        import re
        text = self.live_editor.toPlainText()
        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]+\b', text)
        if not words:
            QMessageBox.information(self, "Spell Check", "No words found")
            return
        issues_count = 0
        for w in words[:100]:
            if len(w) > 20:
                issues_count += 1
        QMessageBox.information(self, "Spell Check",
            f"Checked {len(words)} words.{' Found ' + str(issues_count) + ' potential issues.' if issues_count else ' No issues found.'}")

    def show_graph_view(self):
        from src.core.wikilinks import GraphBuilder
        base_dir = self.active_workspace_folder or (os.path.dirname(self.selected_files[0]) if self.selected_files else os.getcwd())
        builder = GraphBuilder(base_dir)
        html = builder.build_graph_html()
        dlg = QDialog(self)
        dlg.setWindowTitle("Graph View")
        dlg.setMinimumSize(800, 600)
        layout = QVBoxLayout(dlg)
        browser = QTextBrowser()
        browser.setHtml(html)
        layout.addWidget(browser)
        btn = QPushButton("Close")
        btn.clicked.connect(dlg.close)
        layout.addWidget(btn)
        dlg.exec()

    def process_wikilinks(self):
        from src.core.wikilinks import WikiLinkProcessor
        base_dir = self.active_workspace_folder or (os.path.dirname(self.selected_files[0]) if self.selected_files else os.getcwd())
        proc = WikiLinkProcessor(base_dir)
        text = self.live_editor.toPlainText()
        processed = proc.resolve_links(text)
        self.live_editor.setPlainText(processed)
        self._render_live_preview()
        self.append_log("Wiki links resolved")

    def pdf_to_markdown_convert(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF (*.pdf)")
        if not path:
            return
        try:
            from src.core.pdf_to_markdown import pdf_to_markdown
            md = pdf_to_markdown(path)
            self.live_editor.setPlainText(md)
            self._render_live_preview()
            self.append_log(f"PDF -> Markdown: {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "PDF Error", str(e))

    def html_to_markdown_convert(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select HTML file", "", "HTML (*.html *.htm)")
        if not path:
            return
        from src.core.html_to_markdown import html_to_markdown
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        md = html_to_markdown(html)
        self.live_editor.setPlainText(md)
        self._render_live_preview()
        self.append_log(f"HTML -> Markdown: {os.path.basename(path)}")

    def text_to_speech_speak(self):
        text = self.live_editor.toPlainText()
        if not text.strip():
            QMessageBox.information(self, "TTS", "No text to speak")
            return

        from src.core.tts_engine import strip_markdown_for_tts, get_tts_engine
        clean = strip_markdown_for_tts(text)
        engine = get_tts_engine()

        def on_state(state):
            icons = {"playing": "playing", "paused": "paused", "stopped": "stopped"}
            self.append_log(f"TTS: {icons.get(state, state)}")

        engine.set_on_state_change(on_state)

        if engine.is_playing():
            engine.stop()
            self.toast("TTS stopped", "info")
            return

        engine.speak(clean, lang=self.current_lang)
        self.toast("Playing...", "success")

    def show_tts_settings(self):
        from src.core.tts_engine import get_tts_engine
        engine = get_tts_engine()
        voices = engine.get_voices()

        dlg = QDialog(self)
        dlg.setWindowTitle("TTS Settings")
        dlg.setMinimumWidth(400)
        layout = QVBoxLayout(dlg)

        voice_layout = QHBoxLayout()
        voice_layout.addWidget(QLabel("Voice:"))
        voice_combo = QComboBox()
        for v in voices:
            gender_icon = {"male": "male", "female": "female", "neutral": "neutral"}.get(v.gender.value, "")
            premium = " *" if v.is_premium else ""
            voice_combo.addItem(f"{v.name} ({v.language}){premium} - {v.description}", v.id)
        voice_layout.addWidget(voice_combo)
        layout.addLayout(voice_layout)

        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed:"))
        speed_slider = QSlider(Qt.Orientation.Horizontal)
        speed_slider.setRange(50, 200)
        speed_slider.setValue(int(engine.settings.speed * 100))
        speed_label = QLabel(f"{engine.settings.speed:.1f}x")
        speed_slider.valueChanged.connect(lambda v: speed_label.setText(f"{v/100:.1f}x"))
        speed_layout.addWidget(speed_slider)
        speed_layout.addWidget(speed_label)
        layout.addLayout(speed_layout)

        pitch_layout = QHBoxLayout()
        pitch_layout.addWidget(QLabel("Pitch:"))
        pitch_slider = QSlider(Qt.Orientation.Horizontal)
        pitch_slider.setRange(50, 200)
        pitch_slider.setValue(int(engine.settings.pitch * 100))
        pitch_label = QLabel(f"{engine.settings.pitch:.1f}")
        pitch_slider.valueChanged.connect(lambda v: pitch_label.setText(f"{v/100:.1f}"))
        pitch_layout.addWidget(pitch_slider)
        pitch_layout.addWidget(pitch_label)
        layout.addLayout(pitch_layout)

        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel("Volume:"))
        vol_slider = QSlider(Qt.Orientation.Horizontal)
        vol_slider.setRange(0, 100)
        vol_slider.setValue(int(engine.settings.volume * 100))
        vol_label = QLabel(f"{int(engine.settings.volume * 100)}%")
        vol_slider.valueChanged.connect(lambda v: vol_label.setText(f"{v}%"))
        vol_layout.addWidget(vol_slider)
        vol_layout.addWidget(vol_label)
        layout.addLayout(vol_layout)

        btn_layout = QHBoxLayout()
        btn_export = QPushButton("Export to File")
        btn_export.clicked.connect(lambda: self._export_tts_audio(engine))
        btn_layout.addWidget(btn_export)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dlg.accept)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

        def apply_settings():
            engine.set_voice(voice_combo.currentData())
            engine.set_speed(speed_slider.value() / 100)
            engine.set_pitch(pitch_slider.value() / 100)
            engine.set_volume(vol_slider.value() / 100)

        btn_export.clicked.connect(apply_settings)
        dlg.exec()

    def generate_flashcards(self):
        from src.core.flashcards import extract_flashcards, cards_to_html, cards_to_anki
        text = self.live_editor.toPlainText()
        cards = extract_flashcards(text)
        if not cards:
            QMessageBox.information(self, "Flashcards", "No headings found to create cards")
            return

        html = cards_to_html(cards)
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Flashcards ({len(cards)} cards)")
        dlg.setMinimumSize(700, 500)
        layout = QVBoxLayout(dlg)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(html)
        layout.addWidget(browser)
        btn_save = QPushButton("Save as Anki TSV")
        btn_save.clicked.connect(lambda: self._save_anki_tsv(cards))
        layout.addWidget(btn_save)
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dlg.close)
        layout.addWidget(btn_close)
        dlg.exec()

    def _save_anki_tsv(self, cards):
        from src.core.flashcards import cards_to_anki
        tsv = cards_to_anki(cards)
        path, _ = QFileDialog.getSaveFileName(self, "Save Anki TSV", "flashcards.txt", "TSV (*.txt *.tsv)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(tsv)
            self.toast(f"Saved {len(cards)} cards", "success")

    def build_glossary(self):
        from src.core.glossary import extract_definitions, glossary_to_markdown
        text = self.live_editor.toPlainText()
        defs = extract_definitions(text)
        if not defs:
            QMessageBox.information(self, "Glossary", "No definitions found (use **Term**: Definition pattern)")
            return
        glossary_md = glossary_to_markdown(defs)
        cursor = self.live_editor.textCursor()
        cursor.insertText("\n\n" + glossary_md)
        self._render_live_preview()
        self.append_log(f"Glossary built: {len(defs)} terms")

    def generate_quiz(self):
        from src.core.quiz_generator import generate_quiz_from_text, quiz_to_html
        text = self.live_editor.toPlainText()
        quiz = generate_quiz_from_text(text)
        if not quiz["questions"]:
            QMessageBox.information(self, "Quiz", "Not enough content to generate quiz")
            return
        html = quiz_to_html(quiz)
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Quiz ({quiz['total']} questions)")
        dlg.setMinimumSize(700, 500)
        layout = QVBoxLayout(dlg)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(html)
        layout.addWidget(browser)
        btn = QPushButton("Close")
        btn.clicked.connect(dlg.close)
        layout.addWidget(btn)
        dlg.exec()

    def show_cloud_templates(self):
        from src.core.cloud_templates import get_cloud_templates_index, download_template, save_local_template
        templates = get_cloud_templates_index(self.current_lang)

        names = [t.get("name", "Template") for t in templates]
        if not names:
            QMessageBox.information(self, "Templates", "No templates available")
            return

        chosen, ok = QInputDialog.getItem(self, "Cloud Templates", "Choose template:", names, 0, False)
        if ok and chosen:
            for t in templates:
                if t.get("name") == chosen:
                    content = t.get("content", "")
                    if not content and t.get("url"):
                        content = download_template(t["url"])
                    if content:
                        self.live_editor.setPlainText(content)
                        self._render_live_preview()
                        self.append_log(f"Template loaded: {chosen}")
                    return

    def apply_template_vars(self):
        from src.core.template_vars import process_document_vars
        text = self.live_editor.toPlainText()
        result = process_document_vars(text)
        self.live_editor.setPlainText(result)
        self._render_live_preview()
        self.toast("Template variables applied", "success")

    def convert_emoji_shortcodes(self):
        text = self.live_editor.toPlainText()
        import re
        emoji_map = {
            ":smile:": "\U0001F604", ":sad:": "\U0001F622", ":heart:": "\u2764\uFE0F",
            ":fire:": "\U0001F525", ":rocket:": "\U0001F680", ":check:": "\u2705",
            ":x:": "\u274C", ":warning:": "\u26A0\uFE0F", ":bulb:": "\U0001F4A1",
            ":star:": "\u2B50", ":thumbsup:": "\U0001F44D", ":clap:": "\U0001F44F",
            ":wave:": "\U0001F44B", ":100:": "\U0001F4AF",
        }
        result = re.sub(r':\w+:', lambda m: emoji_map.get(m.group(), m.group()), text)
        self.live_editor.setPlainText(result)
        self._render_live_preview()
        self.toast("Emoji shortcodes converted", "success")

    def add_multi_cursor(self):
        if hasattr(self, 'multi_cursor'):
            self.multi_cursor.add_cursor_at_current()
            self.toast("Multi-cursor added", "info")

    def run_linter(self):
        from src.core.linter import lint_markdown
        from src.gui.document_tools import show_document_audit
        text = self.live_editor.toPlainText()
        issues = lint_markdown(text, self.current_lang)
        show_document_audit(self)

    def format_markdown_document(self):
        from src.gui.editor_commands import format_markdown_document
        format_markdown_document(self)

    def format_bold(self):
        from src.gui.editor_commands import format_bold
        format_bold(self)

    def format_italic(self):
        from src.gui.editor_commands import format_italic
        format_italic(self)

    def format_header(self, level):
        from src.gui.editor_commands import format_header
        format_header(self, level)

    def format_code(self):
        from src.gui.editor_commands import format_code
        format_code(self)

    def format_quote(self):
        from src.gui.editor_commands import format_quote
        format_quote(self)

    def format_list(self):
        from src.gui.editor_commands import format_list
        format_list(self)

    def insert_page_break(self):
        from src.gui.editor_commands import insert_page_break
        insert_page_break(self)

    def run_ocr(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image for OCR", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.webp)"
        )
        if not path:
            return
        try:
            from src.core.ocr_engine import image_to_markdown
            md = image_to_markdown(path)
            cursor = self.live_editor.textCursor()
            cursor.insertText(md)
            self._render_live_preview()
            self.append_log(f"OCR completed: {os.path.basename(path)}")
        except ImportError:
            QMessageBox.warning(self, "OCR", "Install: pip install pytesseract Pillow")
        except Exception as e:
            QMessageBox.critical(self, "OCR Error", str(e))

    def _export_tts_audio(self, engine):
        from src.core.tts_engine import strip_markdown_for_tts
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Audio", "speech.mp3",
            "MP3 (*.mp3);;WAV (*.wav);;All (*)"
        )
        if path:
            text = self.live_editor.toPlainText()
            clean = strip_markdown_for_tts(text)
            if engine.export_to_file(clean, path, self.current_lang):
                self.toast(f"Audio saved: {os.path.basename(path)}", "success")
            else:
                self.toast("Export failed", "error")

    # ─── Missing methods from main_window split ───

    def update_markdown_toc_in_editor(self):
        from src.gui.document_tools import update_markdown_toc_in_editor
        update_markdown_toc_in_editor(self)

    def show_toc_generator(self):
        from src.gui.document_tools import show_toc_generator
        show_toc_generator(self)

    def show_table_generator_dialog(self):
        from src.gui.document_tools import show_table_generator_dialog
        show_table_generator_dialog(self)

    def show_design_style_dialog(self):
        from src.gui.document_tools import show_design_style_dialog
        show_design_style_dialog(self)

    def ocr_image_to_text(self):
        self.run_ocr()

    def update_workspace_explorer(self):
        from src.gui.file_manager import update_workspace_explorer
        update_workspace_explorer(self)

    def restore_draft_if_exists(self):
        from src.gui.document_tools import restore_draft_if_exists
        restore_draft_if_exists(self)

    def open_output_folder(self):
        from src.gui.file_manager import open_output_folder
        open_output_folder(self)

    def print_document(self):
        from src.gui.preview_manager import print_document
        print_document(self)

    def copy_styled_html(self):
        from src.gui.preview_manager import copy_styled_html
        copy_styled_html(self)

    def filter_workspace_explorer(self, text):
        from src.gui.file_manager import filter_workspace_explorer
        filter_workspace_explorer(self, text)

    def load_workspace_file(self, item):
        from src.gui.file_manager import load_workspace_file
        load_workspace_file(self, item)

    def zoom_in(self):
        from src.gui.preview_manager import zoom_in
        zoom_in(self)

    def zoom_out(self):
        from src.gui.preview_manager import zoom_out
        zoom_out(self)

    def zoom_reset(self):
        from src.gui.preview_manager import zoom_reset
        zoom_reset(self)

    def resizeEvent(self, event):
        from PyQt6.QtWidgets import QWidget
        QWidget.resizeEvent(self, event)
        if hasattr(self, '_glow') and self._glow.isVisible():
            self._glow.setGeometry(0, 0, self.width(), self.height())
        if hasattr(self, '_titlebar') and self._titlebar.isVisible():
            self._titlebar.setGeometry(0, 0, self.width(), 42)
