"""Диалоги просмотра: LaTeX-превью, tag cloud, аналитика, граф, журнал, diff.

Выделено из ``src/gui/window_tools.py`` (TASK-012/PLAN-012), тела вербатим.
"""

import os

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QMessageBox, QTextBrowser,
)


class ViewDialogsMixin:
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

