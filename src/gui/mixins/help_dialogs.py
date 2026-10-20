"""Диалоги справки: about, шорткаты, приветственный тур.

Выделено из ``src/gui/window_tools.py`` (TASK-012/PLAN-012), тела вербатим.
"""


class HelpDialogsMixin:
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

