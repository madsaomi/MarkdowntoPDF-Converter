"""AI-инструменты и голосовой ввод (локальные, без ML/сети)."""

import os
import re

from PyQt6.QtWidgets import (
    QApplication, QMessageBox, QDialog, QVBoxLayout, QPushButton,
    QTextBrowser, QFileDialog,
)

from src.gui import editor_commands


class AiToolsMixin:
    """Методы ``MainWindow`` для AI-ассистента, Kanban-доски и генератора API-доков.

    Перенесено из ``src/gui/main_window.py`` (группа D плана PLAN-010).
    Требует от хоста: ``live_editor``, ``current_lang``, ``append_log``,
    ``toast``, ``update_preview_from_editor``.
    """

    def start_voice_input(self):
        try:
            from src.gui.workers.task_worker import TaskThread

            def _task():
                import speech_recognition as sr
                recognizer = sr.Recognizer()
                with sr.Microphone() as source:
                    audio = recognizer.listen(source, timeout=10)
                    return recognizer.recognize_google(audio, language='ru-RU')

            self.append_log("🎤 Слушаю (фоновый)...")

            def _on_finish(text):
                try:
                    if text:
                        cursor = self.live_editor.textCursor()
                        cursor.insertText(text)
                    self.append_log("🎤 Готово")
                except Exception as e:
                    self.append_log(f"🎤 Ошибка: {e}")

            def _on_error(e):
                if "Microphone" in str(e) or "No module" in str(e):
                    QMessageBox.information(self, "Voice", "Установите: pip install SpeechRecognition pyaudio")
                    return
                self.append_log(f"🎤 Ошибка: {e}")

            TaskThread(_task).start(on_finish=_on_finish, on_error=_on_error, parent=self)
        except Exception:
            try:
                import speech_recognition as sr
                recognizer = sr.Recognizer()
                with sr.Microphone() as source:
                    self.append_log("🎤 Слушаю...")
                    QApplication.processEvents()
                    audio = recognizer.listen(source, timeout=10)
                    text = recognizer.recognize_google(audio, language='ru-RU')
                    cursor = self.live_editor.textCursor()
                    cursor.insertText(text)
            except ImportError:
                QMessageBox.information(self, "Voice", "Установите: pip install SpeechRecognition pyaudio")
            except Exception as e:
                self.append_log(f"🎤 Ошибка: {e}")

    def ai_improve_text(self):
        cursor = self.live_editor.textCursor()
        selected = cursor.selectedText()
        if not selected:
            QMessageBox.information(self, "AI", "Выделите текст")
            return
        from src.core.ai_assistant import get_ai_assistant
        assistant = get_ai_assistant()
        suggestions = assistant.analyze(selected, self.current_lang)
        if suggestions:
            lines = []
            for s in suggestions[:5]:
                lines.append(f"• [{s.category}] {s.explanation}")
            QMessageBox.information(self, "AI Suggestions", "\n".join(lines))
        else:
            improved = selected.strip()
            improved = ' '.join(improved.split())
            cursor.insertText(improved)
            self.toast("Текст обработан", "success")

    def ai_generate_outline(self):
        text = self.live_editor.toPlainText()
        from src.core.ai_assistant import get_ai_assistant
        assistant = get_ai_assistant()
        outline = assistant.generate_outline(text, self.current_lang)
        cursor = self.live_editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        cursor.insertText(outline + "\n\n")
        self.toast("Оглавление сгенерировано", "success")

    def show_ai_assistant(self):
        from src.core.ai_assistant import get_ai_assistant
        assistant = get_ai_assistant()
        text = self.live_editor.toPlainText()
        if not text.strip():
            self.toast("Нет текста для анализа", "warning")
            return
        suggestions = assistant.analyze(text, self.current_lang)
        if not suggestions:
            self.toast("Проблем не найдено! Текст хороший.", "success")
            return
        lines = [f"🔍 Найдено {len(suggestions)} предложений:\n"]
        for s in suggestions[:10]:
            emoji = {"grammar": "📝", "style": "✨", "readability": "📖", "structure": "🏗️"}.get(s.category, "💡")
            lines.append(f"{emoji} Строка {s.line}: {s.explanation}")
        QMessageBox.information(self, "AI Writing Assistant", "\n".join(lines))

    def export_task_board(self):
        text = self.live_editor.toPlainText()
        import re
        todo, done = [], []
        for line in text.split('\n'):
            stripped = line.strip()
            if re.match(r'^- \[[ x]\]\s', stripped):
                content = re.sub(r'^- \[[ x]\]\s*', '', stripped)
                (done if '[x]' in stripped else todo).append(content)
        html = f"""<html><head><style>
body{{font-family:sans-serif;padding:20px;}}
.board{{display:flex;gap:20px;}}
.column{{background:white;border-radius:8px;padding:16px;min-width:250px;box-shadow:0 2px 8px rgba(0,0,0,0.1);}}
.todo{{border-top:3px solid #3498db;}}.done{{border-top:3px solid #27ae60;}}
.task{{background:#f8f9fa;padding:8px;margin:6px 0;border-radius:4px;font-size:14px;}}
</style></head><body><h2>📋 Task Board</h2><div class="board">
<div class="column todo"><h3>To Do ({len(todo)})</h3>{''.join(f'<div class="task">{t}</div>' for t in todo)}</div>
<div class="column done"><h3>Done ({len(done)})</h3>{''.join(f'<div class="task" style="text-decoration:line-through;color:#999">{t}</div>' for t in done)}</div>
</div></body></html>"""
        dlg = QDialog(self); dlg.setWindowTitle("Task Board"); dlg.setMinimumSize(700, 400)
        layout = QVBoxLayout(dlg)
        browser = QTextBrowser(); browser.setHtml(html); layout.addWidget(browser)
        btn = QPushButton("Закрыть"); btn.clicked.connect(dlg.close); layout.addWidget(btn)
        dlg.exec()

    def generate_api_docs(self):
        path, _ = QFileDialog.getOpenFileName(self, "Python файл", "", "Python (*.py)")
        if not path: return
        try:
            import ast
            with open(path, 'r', encoding='utf-8') as f: source = f.read()
            tree = ast.parse(source)
            docs = [f"# API: {os.path.basename(path)}\n"]
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef):
                    docs.append(f"\n## class {node.name}\n")
                    if ast.get_docstring(node): docs.append(f"{ast.get_docstring(node)}\n")
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            args = [a.arg for a in item.args.args if a.arg != 'self']
                            docs.append(f"### {item.name}({', '.join(args)})\n")
                            if ast.get_docstring(item): docs.append(f"{ast.get_docstring(item)}\n")
                elif isinstance(node, ast.FunctionDef):
                    args = [a.arg for a in node.args.args]
                    docs.append(f"\n## def {node.name}({', '.join(args)})\n")
                    if ast.get_docstring(node): docs.append(f"{ast.get_docstring(node)}\n")
            self.live_editor.setPlainText('\n'.join(docs))
            self.update_preview_from_editor()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
