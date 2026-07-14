import os
import sys


class AppConfig:
    """Centralized application configuration for paths and constants."""

    APP_NAME = "MarkdownToPDF_Pro"

    @staticmethod
    def base_path() -> str:
        if getattr(sys, 'frozen', False):
            return sys._MEIPASS
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    @staticmethod
    def template_dir() -> str:
        return os.path.join(AppConfig.base_path(), 'templates')

    @staticmethod
    def weasyprint_exe() -> str:
        return os.path.join(AppConfig.base_path(), 'weasyprint-windows', 'dist', 'weasyprint.exe')

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
