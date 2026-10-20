"""Агрегатор тематических миксинов ``ToolMethodsMixin``.

Ранее — один класс на 730 строк с 68 методами (TASK-012/PLAN-012).
Методы разнесены по тематическим миксинам в ``src/gui/mixins/``;
здесь они собираются обратно в публичное имя ``ToolMethodsMixin``,
поэтому ``from src.gui.window_tools import ToolMethodsMixin`` и
наследование в ``MainWindow`` работают без изменений.
"""

from src.gui.mixins.help_dialogs import HelpDialogsMixin
from src.gui.mixins.view_dialogs import ViewDialogsMixin
from src.gui.mixins.export_tools import ExportToolsMixin
from src.gui.mixins.editor_view_modes import EditorViewModesMixin
from src.gui.mixins.editor_formatting import EditorFormattingMixin
from src.gui.mixins.tts_media import TtsMediaMixin
from src.gui.mixins.education import EducationMixin
from src.gui.mixins.convert_tools import ConvertToolsMixin
from src.gui.mixins.integrations import IntegrationsMixin
from src.gui.mixins.workspace import WorkspaceMixin


class ToolMethodsMixin(
    HelpDialogsMixin,
    ViewDialogsMixin,
    ExportToolsMixin,
    EditorViewModesMixin,
    EditorFormattingMixin,
    TtsMediaMixin,
    EducationMixin,
    ConvertToolsMixin,
    IntegrationsMixin,
    WorkspaceMixin,
):
    """Публичный агрегатор тематических миксинов окна."""
