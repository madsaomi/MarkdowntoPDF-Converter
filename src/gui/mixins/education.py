"""Обучение: карточки, Anki TSV, глоссарий, квиз.

Выделено из ``src/gui/window_tools.py`` (TASK-012/PLAN-012), тела вербатим.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QFileDialog, QMessageBox, QTextBrowser,
)


class EducationMixin:
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

