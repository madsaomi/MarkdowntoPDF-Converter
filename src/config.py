import os
import sys


class AppConfig:
    """Centralized application configuration for paths and constants."""

    APP_NAME = "MarkdownToPDF_Pro"

    @staticmethod
    def base_path() -> str:
        if getattr(sys, 'frozen', False):
            return getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(sys.executable)))
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    @staticmethod
    def template_dir() -> str:
        return os.path.join(AppConfig.base_path(), 'templates')

    @staticmethod
    def weasyprint_exe() -> str:
        return os.path.join(AppConfig.base_path(), 'weasyprint-windows', 'dist', 'weasyprint.exe')

    @staticmethod
    def resolve_weasyprint_cmd(exe_path: str = None, module_available: bool = None) -> list:
        """
        Резолвер PDF-движка WeasyPrint (цепочка fallback):
          1. Портативный weasyprint.exe (weasyprint-windows/dist/), если существует.
          2. pip-пакет weasyprint -> команда [sys.executable, "-m", "weasyprint"].
          3. FileNotFoundError с понятной инструкцией.
        Параметры exe_path/module_available внедряются для тестов.
        Возвращает команду в виде списка (префикс argv для subprocess).
        """
        exe = exe_path if exe_path is not None else AppConfig.weasyprint_exe()
        if exe and os.path.isfile(exe):
            return [exe]

        if module_available is None:
            import importlib.util
            try:
                module_available = importlib.util.find_spec("weasyprint") is not None
            except Exception:
                module_available = False

        if module_available:
            # В frozen-сборке (PyInstaller) интерпретатор недоступен — fallback невозможен
            if not getattr(sys, 'frozen', False):
                return [sys.executable, "-m", "weasyprint"]

        raise FileNotFoundError(
            "PDF-движок WeasyPrint не найден.\n"
            "Варианты решения:\n"
            f"  1) Положить портативный weasyprint.exe в: {os.path.join(AppConfig.base_path(), 'weasyprint-windows', 'dist')}\n"
            "  2) Установить движок в окружение: pip install weasyprint\n"
            "     (на Windows дополнительно требуется GTK3 — см. "
            "https://doc.courtbouillon.org/weasyprint/stable/first_install.html,\n"
            "      либо запусти скрипт setup_pdf_engine.ps1 в корне проекта)\n"
            "В frozen-сборке (.exe) доступен только вариант 1."
        )

    @staticmethod
    def assets_dir() -> str:
        return os.path.join(AppConfig.base_path(), 'assets')

    @staticmethod
    def icon_path() -> str:
        return os.path.join(AppConfig.assets_dir(), 'icon.ico')

    @staticmethod
    def app_data_dir() -> str:
        d = os.path.join(os.getenv("APPDATA", "."), AppConfig.APP_NAME)
        os.makedirs(d, exist_ok=True)
        return d

    @staticmethod
    def log_dir() -> str:
        d = os.path.join(AppConfig.app_data_dir(), "logs")
        os.makedirs(d, exist_ok=True)
        return d

    @staticmethod
    def cache_dir() -> str:
        d = os.path.join(AppConfig.app_data_dir(), "cache", "images")
        os.makedirs(d, exist_ok=True)
        return d

    @staticmethod
    def data_dir() -> str:
        d = os.path.join(os.getenv("APPDATA", "."), AppConfig.APP_NAME)
        os.makedirs(d, exist_ok=True)
        return d

    @staticmethod
    def backups_dir() -> str:
        d = os.path.join(AppConfig.app_data_dir(), "backups")
        os.makedirs(d, exist_ok=True)
        return d
