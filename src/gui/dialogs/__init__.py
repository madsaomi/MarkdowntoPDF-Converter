"""Пакет диалогов GUI (TASK-011/PLAN-011).

Ранее — единый модуль ``src/gui/dialogs.py`` (1534 строки, 17 классов).
Разбит на тематические модули; этот ``__init__`` реэкспортирует все
классы, поэтому существующие импорты вида ::

    from src.gui.dialogs import GitHubSyncDialog

продолжают работать без изменений (фасад совместимости).
"""

from src.gui.dialogs.github_plugin import GitHubSyncDialog, PluginManagerDialog
from src.gui.dialogs.export import MultiExportDialog, PDFStyleEditorDialog
from src.gui.dialogs.content import (
    DocumentBuilderDialog,
    MarkdownTOCDialog,
    MarkdownTableDialog,
    SnippetsDialog,
    SnippetsManagerDialog,
)
from src.gui.dialogs.analysis import (
    ReadabilityDashboardDialog,
    DocumentAuditorDialog,
    CitationManagerDialog,
    CloudTemplatesDialog,
)
from src.gui.dialogs.versions import RevisionHistoryDialog, DiffDialog
from src.gui.dialogs.common import ColorButton, ShortcutsDialog

__all__ = [
    # common
    "ColorButton",
    "ShortcutsDialog",
    # github / plugins
    "GitHubSyncDialog",
    "PluginManagerDialog",
    # export
    "MultiExportDialog",
    "PDFStyleEditorDialog",
    # content
    "DocumentBuilderDialog",
    "MarkdownTOCDialog",
    "MarkdownTableDialog",
    "SnippetsDialog",
    "SnippetsManagerDialog",
    # analysis
    "ReadabilityDashboardDialog",
    "DocumentAuditorDialog",
    "CitationManagerDialog",
    "CloudTemplatesDialog",
    # versions
    "RevisionHistoryDialog",
    "DiffDialog",
]
