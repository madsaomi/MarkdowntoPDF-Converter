"""Диалоги GitHub-синхронизации и менеджера плагинов.

``GitHubSyncDialog``, ``PluginManagerDialog``. Выделено из
``src/gui/dialogs.py`` (TASK-011/PLAN-011), тела перенесены вербатим.
"""

import os

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QListWidget, QTextBrowser,
)


class GitHubSyncDialog(QDialog):
    """GitHub Sync dialog for push/pull/commit operations."""

    def __init__(self, parent=None, folder: str = "", lang="ru"):
        super().__init__(parent)
        self.lang = lang
        self.folder = folder
        self.setWindowTitle("🐙 GitHub Sync")
        self.setMinimumSize(520, 420)

        layout = QVBoxLayout(self)

        # Status
        self.status_label = QLabel(f"📁 {folder}")
        self.status_label.setStyleSheet("font-weight: bold; color: #e2e8f0; padding: 5px;")
        layout.addWidget(self.status_label)

        # Git status output
        self.status_output = QTextBrowser()
        self.status_output.setStyleSheet("font-family: monospace; font-size: 12px;")
        layout.addWidget(self.status_output)

        # Commit message
        msg_layout = QHBoxLayout()
        self.commit_input = QLineEdit()
        self.commit_input.setPlaceholderText("Commit message...")
        msg_layout.addWidget(self.commit_input)
        layout.addLayout(msg_layout)

        # Buttons
        btn_layout = QHBoxLayout()

        btn_status = QPushButton("🔄 Status")
        btn_status.clicked.connect(self._git_status)
        btn_layout.addWidget(btn_status)

        btn_init = QPushButton("📁 git init")
        btn_init.clicked.connect(self._git_init)
        btn_layout.addWidget(btn_init)

        btn_commit = QPushButton("✅ Commit All")
        btn_commit.setStyleSheet("QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #059669,stop:1 #10b981); color: white; font-weight: bold; border: none; padding: 4px 12px; border-radius: 6px; } QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #047857,stop:1 #059669); }")
        btn_commit.clicked.connect(self._git_commit)
        btn_layout.addWidget(btn_commit)

        btn_push = QPushButton("⬆ Push")
        btn_push.setStyleSheet("QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2563eb,stop:1 #60a5fa); color: white; font-weight: bold; border: none; padding: 4px 12px; border-radius: 6px; } QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1d4ed8,stop:1 #2563eb); }")
        btn_push.clicked.connect(self._git_push)
        btn_layout.addWidget(btn_push)

        btn_pull = QPushButton("⬇ Pull")
        btn_pull.clicked.connect(self._git_pull)
        btn_layout.addWidget(btn_pull)

        layout.addLayout(btn_layout)

        # Log
        btn_log = QPushButton("📜 Show Log")
        btn_log.clicked.connect(self._git_log)
        layout.addWidget(btn_log)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

        self._git_status()

    def _git_status(self):
        from src.core.github_sync import git_status, is_git_repo
        if not is_git_repo(self.folder):
            self.status_output.setHtml("<p style='color:#e74c3c;'>Not a git repository. Click 'git init' first.</p>")
            return
        status = git_status(self.folder)
        lines = [f"<b>Git Status:</b><br>"]
        if status["staged"]:
            lines.append(f"<span style='color:#27ae60;'>Staged:</span> {', '.join(status['staged'])}<br>")
        if status["modified"]:
            lines.append(f"<span style='color:#e67e22;'>Modified:</span> {', '.join(status['modified'])}<br>")
        if status["untracked"]:
            lines.append(f"<span style='color:#95a5a6;'>Untracked:</span> {', '.join(status['untracked'])}<br>")
        if not any([status["staged"], status["modified"], status["untracked"]]):
            lines.append("<span style='color:#27ae60;'>Working tree clean</span>")
        self.status_output.setHtml("".join(lines))

    def _git_init(self):
        from src.core.github_sync import git_init
        result = git_init(self.folder)
        if result["success"]:
            self.status_output.setHtml(f"<span style='color:#27ae60;'>✅ {result['output']}</span>")
        else:
            self.status_output.setHtml(f"<span style='color:#e74c3c;'>❌ {result.get('error', 'Failed')}</span>")

    def _git_commit(self):
        from src.core.github_sync import git_commit
        msg = self.commit_input.text().strip()
        if not msg:
            msg = "Update from MarkdownToPDF Converter"
        result = git_commit(self.folder, msg)
        if result["success"]:
            self.status_output.setHtml(f"<span style='color:#27ae60;'>✅ Committed: {msg}</span>")
        else:
            self.status_output.setHtml(f"<span style='color:#e74c3c;'>❌ {result.get('error', 'Failed')}</span>")
        self._git_status()

    def _git_push(self):
        from src.core.github_sync import git_push
        result = git_push(self.folder)
        if result["success"]:
            self.status_output.setHtml(f"<span style='color:#27ae60;'>✅ Pushed successfully</span>")
        else:
            self.status_output.setHtml(f"<span style='color:#e74c3c;'>❌ {result.get('error', 'Failed')}</span>")

    def _git_pull(self):
        from src.core.github_sync import git_pull
        result = git_pull(self.folder)
        if result["success"]:
            self.status_output.setHtml(f"<span style='color:#27ae60;'>✅ Pulled successfully</span>")
        else:
            self.status_output.setHtml(f"<span style='color:#e74c3c;'>❌ {result.get('error', 'Failed')}</span>")

    def _git_log(self):
        from src.core.github_sync import git_log
        commits = git_log(self.folder)
        if not commits:
            self.status_output.setHtml("No commits found")
            return
        lines = ["<b>Recent Commits:</b><br>"]
        for c in commits:
            lines.append(f"<code>{c['hash']}</code> {c['message']} <span style='color:#999'>({c['date'][:10]})</span><br>")
        self.status_output.setHtml("".join(lines))


class PluginManagerDialog(QDialog):
    """Plugin manager dialog."""

    def __init__(self, parent=None, lang="ru"):
        super().__init__(parent)
        self.lang = lang
        self.setWindowTitle("🧩 Plugin Manager")
        self.setMinimumSize(480, 360)

        layout = QVBoxLayout(self)

        info = QLabel("Plugins are loaded from the <code>plugins/</code> directory.")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.plugin_list = QListWidget()
        self.plugin_list.setStyleSheet("""
            QListWidget { background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: #e2e8f0; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.05); }
            QListWidget::item:hover { background-color: rgba(51, 65, 85, 0.6); }
            QListWidget::item:selected { background-color: rgba(99, 102, 241, 0.6); color: white; }
        """)
        layout.addWidget(self.plugin_list)

        self._refresh_list()

        btn_layout = QHBoxLayout()
        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.clicked.connect(self._refresh_list)
        btn_layout.addWidget(btn_refresh)

        btn_open_dir = QPushButton("📂 Open plugins/ folder")
        btn_open_dir.clicked.connect(self._open_plugins_dir)
        btn_layout.addWidget(btn_open_dir)

        btn_layout.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _refresh_list(self):
        self.plugin_list.clear()
        from src.core.plugin_system import get_all_plugins, get_all_hooks
        plugins = get_all_plugins()
        hooks = get_all_hooks()

        if plugins:
            for name, info in plugins.items():
                self.plugin_list.addItem(f"🔌 {name} v{info['version']} by {info['author']}")
        else:
            self.plugin_list.addItem("No plugins registered")

        self.plugin_list.addItem("---")
        for hook_name, handlers in hooks.items():
            self.plugin_list.addItem(f"🪝 {hook_name}: {len(handlers)} handler(s)")

    def _open_plugins_dir(self):
        import subprocess
        from src.config import AppConfig
        plugins_dir = os.path.join(AppConfig.base_path(), "plugins")
        os.makedirs(plugins_dir, exist_ok=True)
        subprocess.run(["explorer", os.path.normpath(plugins_dir)])


