"""Поведенческие тесты диалогов анализа (gui/dialogs/analysis).

Покрывает ``ReadabilityDashboardDialog`` (статистика текста, топ-слова) и
``DocumentAuditorDialog`` (таблица проблем, выбор строки, пустой случай).
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QLabel, QTableWidget

app = QApplication.instance() or QApplication([])

from src.gui.dialogs.analysis import DocumentAuditorDialog, ReadabilityDashboardDialog

TEXT = (
    "Это тестовый текст для анализа. Он содержит несколько предложений. "
    "Каждое предложение имеет разную длину, что удобно для проверки. "
    "Markdown разметка тоже присутствует, например **жирный** текст."
)


def _labels(dialog):
    return [lbl.text() for lbl in dialog.findChildren(QLabel)]


def test_readability_dashboard_computes_stats():
    """Дашборд считает слова, символы, абзацы и предложения."""
    d = ReadabilityDashboardDialog(TEXT, lang="ru")
    labels = " | ".join(_labels(d))
    assert "Слов" in labels or "слов" in labels, labels
    # Количество слов в тексте
    assert str(len(TEXT.split())) in labels, labels
    assert "Абзацы" in labels or "абзацы" in labels.lower()
    d.close()
    print("[PASS] test_readability_dashboard_computes_stats")


def test_readability_dashboard_shows_top_words():
    """Дашборд показывает топ-5 частых слов (без стоп-слов)."""
    text = "alpha alpha alpha beta beta gamma delta epsilon zeta omega"
    d = ReadabilityDashboardDialog(text, lang="ru")
    labels = " | ".join(_labels(d))
    assert "alpha" in labels, labels
    # Стоп-слова не должны попадать в топ
    assert "🔑 <b>the</b>" not in labels
    d.close()
    print("[PASS] test_readability_dashboard_shows_top_words")


def test_readability_dashboard_handles_empty_text():
    """Пустой текст не вызывает деление на ноль."""
    d = ReadabilityDashboardDialog("", lang="ru")
    labels = " | ".join(_labels(d))
    assert labels, "должны быть подписи статистики"
    d.close()
    print("[PASS] test_readability_dashboard_handles_empty_text")


def test_readability_dashboard_title_by_lang():
    """Заголовок дашборда берётся из перевода и зависит от языка."""
    d_ru = ReadabilityDashboardDialog(TEXT, lang="ru")
    d_en = ReadabilityDashboardDialog(TEXT, lang="en")
    assert d_ru.windowTitle() != "", d_ru.windowTitle()
    assert d_en.windowTitle() != "", d_en.windowTitle()
    d_ru.close()
    d_en.close()
    print("[PASS] test_readability_dashboard_title_by_lang")


def test_auditor_empty_issues_shows_placeholder():
    """Без проблем показывается сообщение «проблем не обнаружено»."""
    d = DocumentAuditorDialog([], lang="ru")
    labels = " | ".join(_labels(d))
    assert "Проблем не обнаружено" in labels, labels
    tables = d.findChildren(QTableWidget)
    assert not tables, "таблица не должна создаваться без проблем"
    d.close()
    print("[PASS] test_auditor_empty_issues_shows_placeholder")


def test_auditor_builds_table_with_issues():
    """Проблемы выводятся таблицей: строка, тип, описание."""
    issues = [
        {"line": 12, "type": "Структура", "desc": "Пустой заголовок"},
        {"line": 40, "type": "Типографика", "desc": "Двойной пробел"},
    ]
    d = DocumentAuditorDialog(issues, lang="ru")
    tables = d.findChildren(QTableWidget)
    assert len(tables) == 1
    table = tables[0]
    assert table.rowCount() == 2
    assert table.columnCount() == 3
    assert table.item(0, 0).text() == "12"
    assert table.item(1, 0).text() == "40"
    assert "Пустой заголовок" in table.item(0, 2).text()
    d.close()
    print("[PASS] test_auditor_builds_table_with_issues")


def test_auditor_double_click_sets_selected_line():
    """Двойной клик по строке запоминает номер строки и закрывает диалог."""
    issues = [
        {"line": 12, "type": "Структура", "desc": "Пустой заголовок"},
        {"line": 40, "type": "Типографика", "desc": "Двойной пробел"},
    ]
    d = DocumentAuditorDialog(issues, lang="ru")
    table = d.findChildren(QTableWidget)[0]
    idx = table.model().index(1, 0)
    d.on_row_double_clicked(idx)
    assert d.selected_line == 40, d.selected_line
    d.close()
    print("[PASS] test_auditor_double_click_sets_selected_line")


def test_auditor_autofix_calls_parent_hook():
    """Кнопка авто-исправления вызывает метод родительского окна."""
    from PyQt6.QtWidgets import QWidget

    issues = [{"line": 1, "type": "Типографика", "desc": "d"}]
    calls = []

    class _Parent(QWidget):
        def auto_fix_document_issues(self):
            calls.append(1)

    parent = _Parent()  # держим ссылку: иначе Qt удалит родителя вместе с диалогом
    d = DocumentAuditorDialog(issues, parent=parent, lang="ru")
    d.on_autofix_clicked()
    assert calls == [1], calls
    d.close()
    print("[PASS] test_auditor_autofix_calls_parent_hook")


def main():
    tests = [
        test_readability_dashboard_computes_stats,
        test_readability_dashboard_shows_top_words,
        test_readability_dashboard_handles_empty_text,
        test_readability_dashboard_title_by_lang,
        test_auditor_empty_issues_shows_placeholder,
        test_auditor_builds_table_with_issues,
        test_auditor_double_click_sets_selected_line,
        test_auditor_autofix_calls_parent_hook,
    ]
    for t in tests:
        t()
    print("\nAll analysis-dialog tests passed!")


if __name__ == "__main__":
    main()
