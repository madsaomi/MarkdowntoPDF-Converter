"""Поведенческие тесты диалогов GitHub-синхронизации и менеджера плагинов.

Покрывает ``GitHubSyncDialog`` (статус репозитория, commit/push/pull/log)
и ``PluginManagerDialog`` (список плагинов и хуков).
"""
import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QListWidget

app = QApplication.instance() or QApplication([])

import src.core.github_sync as gs
import src.gui.dialogs.github_plugin as gp
from src.gui.dialogs.github_plugin import GitHubSyncDialog, PluginManagerDialog


def test_github_status_not_a_repo():
    """Вне git-репозитория показывается подсказка «Not a git repository»."""
    with tempfile.TemporaryDirectory() as d:
        dlg = GitHubSyncDialog(folder=d, lang="ru")
        html = dlg.status_output.toHtml()
        assert "Not a git repository" in html, html
        dlg.close()
    print("[PASS] test_github_status_not_a_repo")


def test_github_status_reports_changes():
    """Статус показывает staged/modified/untracked файлы."""
    with tempfile.TemporaryDirectory() as d:
        dlg = GitHubSyncDialog(folder=d, lang="ru")
        orig_status, orig_is_repo = gs.git_status, gs.is_git_repo
        gs.is_git_repo = lambda folder: True
        gs.git_status = lambda folder: {
            "staged": ["a.md"],
            "modified": ["b.md"],
            "untracked": ["c.md"],
        }
        try:
            dlg._git_status()
        finally:
            gs.git_status, gs.is_git_repo = orig_status, orig_is_repo
        html = dlg.status_output.toHtml()
        assert "a.md" in html
        assert "b.md" in html
        assert "c.md" in html
        assert "Staged" in html
        dlg.close()
    print("[PASS] test_github_status_reports_changes")


def test_github_status_clean_tree():
    """Чистое рабочее дерево сообщает об этом."""
    with tempfile.TemporaryDirectory() as d:
        dlg = GitHubSyncDialog(folder=d, lang="ru")
        orig_status, orig_is_repo = gs.git_status, gs.is_git_repo
        gs.is_git_repo = lambda folder: True
        gs.git_status = lambda folder: {"staged": [], "modified": [], "untracked": []}
        try:
            dlg._git_status()
        finally:
            gs.git_status, gs.is_git_repo = orig_status, orig_is_repo
        assert "Working tree clean" in dlg.status_output.toHtml()
        dlg.close()
    print("[PASS] test_github_status_clean_tree")


def test_github_commit_uses_default_message():
    """Пустое сообщение коммита заменяется значением по умолчанию."""
    with tempfile.TemporaryDirectory() as d:
        dlg = GitHubSyncDialog(folder=d, lang="ru")
        seen = {}

        def fake_commit(folder, msg):
            seen["msg"] = msg
            return {"success": True, "output": "ok"}

        orig = gs.git_commit
        gs.git_commit = fake_commit
        # _git_commit в конце вызывает _git_status() и перетирает вывод —
        # отключаем его, чтобы проверить именно текст сообщения.
        dlg._git_status = lambda: None
        try:
            dlg.commit_input.setText("   ")
            dlg._git_commit()
        finally:
            gs.git_commit = orig
        assert seen["msg"] == "Update from MarkdownToPDF Converter", seen
        assert "Committed" in dlg.status_output.toHtml()
        dlg.close()
    print("[PASS] test_github_commit_uses_default_message")


def test_github_commit_uses_custom_message():
    """Введённое сообщение коммита передаётся как есть."""
    with tempfile.TemporaryDirectory() as d:
        dlg = GitHubSyncDialog(folder=d, lang="ru")
        seen = {}
        orig = gs.git_commit
        gs.git_commit = lambda folder, msg: (seen.update(msg=msg), {"success": True, "output": "ok"})[1]
        dlg._git_status = lambda: None
        try:
            dlg.commit_input.setText("Мой коммит")
            dlg._git_commit()
        finally:
            gs.git_commit = orig
        assert seen["msg"] == "Мой коммит", seen
        dlg.close()
    print("[PASS] test_github_commit_uses_custom_message")


def test_github_commit_reports_failure():
    """Ошибка коммита показывается красным, без исключения."""
    with tempfile.TemporaryDirectory() as d:
        dlg = GitHubSyncDialog(folder=d, lang="ru")
        orig = gs.git_commit
        gs.git_commit = lambda folder, msg: {"success": False, "error": "nothing to commit"}
        dlg._git_status = lambda: None
        try:
            dlg.commit_input.setText("msg")
            dlg._git_commit()
        finally:
            gs.git_commit = orig
        html = dlg.status_output.toHtml()
        assert "nothing to commit" in html, html
        dlg.close()
    print("[PASS] test_github_commit_reports_failure")


def test_github_push_pull_and_log():
    """Push/Pull/Log формируют корректные сообщения."""
    with tempfile.TemporaryDirectory() as d:
        dlg = GitHubSyncDialog(folder=d, lang="ru")
        orig_push, orig_pull, orig_log = gs.git_push, gs.git_pull, gs.git_log
        gs.git_push = lambda folder: {"success": True, "output": "ok"}
        gs.git_pull = lambda folder: {"success": True, "output": "ok"}
        gs.git_log = lambda folder: [
            {"hash": "abc1234", "message": "Первый коммит", "date": "2026-01-02 10:00:00"}
        ]
        try:
            dlg._git_push()
            assert "Pushed successfully" in dlg.status_output.toHtml()
            dlg._git_pull()
            assert "Pulled successfully" in dlg.status_output.toHtml()
            dlg._git_log()
            html = dlg.status_output.toHtml()
            assert "abc1234" in html
            assert "Первый коммит" in html
        finally:
            gs.git_push, gs.git_pull, gs.git_log = orig_push, orig_pull, orig_log
        dlg.close()
    print("[PASS] test_github_push_pull_and_log")


def test_github_log_empty():
    """Без коммитов выводится «No commits found»."""
    with tempfile.TemporaryDirectory() as d:
        dlg = GitHubSyncDialog(folder=d, lang="ru")
        orig = gs.git_log
        gs.git_log = lambda folder: []
        try:
            dlg._git_log()
        finally:
            gs.git_log = orig
        assert "No commits found" in dlg.status_output.toHtml()
        dlg.close()
    print("[PASS] test_github_log_empty")


def test_plugin_manager_lists_plugins_and_hooks():
    """Менеджер плагинов показывает плагины и хуки."""
    import src.core.plugin_system as ps

    orig_plugins, orig_hooks = ps.get_all_plugins, ps.get_all_hooks
    ps.get_all_plugins = lambda: {
        "demo": {"version": "1.0", "author": "Tester"}
    }
    ps.get_all_hooks = lambda: {"on_render": [1, 2]}
    try:
        dlg = PluginManagerDialog(lang="ru")
        items = [dlg.plugin_list.item(i).text() for i in range(dlg.plugin_list.count())]
        assert any("demo" in t and "1.0" in t and "Tester" in t for t in items), items
        assert any("on_render" in t and "2 handler" in t for t in items), items
        assert "---" in items, items
        dlg.close()
    finally:
        ps.get_all_plugins, ps.get_all_hooks = orig_plugins, orig_hooks
    print("[PASS] test_plugin_manager_lists_plugins_and_hooks")


def test_plugin_manager_empty_registry():
    """Без плагинов выводится соответствующая заглушка."""
    import src.core.plugin_system as ps

    orig_plugins, orig_hooks = ps.get_all_plugins, ps.get_all_hooks
    ps.get_all_plugins = lambda: {}
    ps.get_all_hooks = lambda: {}
    try:
        dlg = PluginManagerDialog(lang="ru")
        items = [dlg.plugin_list.item(i).text() for i in range(dlg.plugin_list.count())]
        assert "No plugins registered" in items, items
        dlg.close()
    finally:
        ps.get_all_plugins, ps.get_all_hooks = orig_plugins, orig_hooks
    print("[PASS] test_plugin_manager_empty_registry")


def main():
    tests = [
        test_github_status_not_a_repo,
        test_github_status_reports_changes,
        test_github_status_clean_tree,
        test_github_commit_uses_default_message,
        test_github_commit_uses_custom_message,
        test_github_commit_reports_failure,
        test_github_push_pull_and_log,
        test_github_log_empty,
        test_plugin_manager_lists_plugins_and_hooks,
        test_plugin_manager_empty_registry,
    ]
    for t in tests:
        t()
    print("\nAll github/plugin dialog tests passed!")


if __name__ == "__main__":
    main()
