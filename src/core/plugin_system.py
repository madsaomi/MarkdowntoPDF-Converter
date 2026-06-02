import importlib
import importlib.util
import logging
import os
from typing import Callable

logger = logging.getLogger("MarkdownToPDF.plugins")

_plugins: dict[str, dict] = {}
_hooks: dict[str, list[Callable]] = {
    "on_convert_start": [],
    "on_convert_end": [],
    "on_editor_change": [],
    "on_file_open": [],
    "on_export": [],
    "pre_process_markdown": [],
    "post_process_html": [],
}


def register_plugin(name: str, version: str = "1.0", author: str = "Unknown"):
    """Decorator to register a plugin class."""
    def decorator(cls):
        _plugins[name] = {
            "class": cls,
            "version": version,
            "author": author,
            "instance": None,
        }
        logger.info("Plugin registered: %s v%s", name, version)
        return cls
    return decorator


def hook(name: str):
    """Decorator to register a function as a hook handler."""
    def decorator(func):
        if name in _hooks:
            _hooks[name].append(func)
        return func
    return decorator


def emit_hook(name: str, *args, **kwargs):
    """Call all handlers for a hook."""
    for handler in _hooks.get(name, []):
        try:
            handler(*args, **kwargs)
        except Exception as e:
            logger.error("Hook %s handler %s failed: %s", name, handler.__name__, e)


def load_plugins_from_dir(directory: str):
    """Load all .py files in directory as plugins."""
    if not os.path.isdir(directory):
        return

    for fname in os.listdir(directory):
        if fname.endswith(".py") and not fname.startswith("_"):
            path = os.path.join(directory, fname)
            try:
                spec = importlib.util.spec_from_file_location(fname[:-3], path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                logger.info("Loaded plugin file: %s", fname)
            except Exception as e:
                logger.error("Failed to load plugin %s: %s", fname, e)


def get_all_plugins() -> dict:
    """Return dict of registered plugins."""
    return dict(_plugins)


def get_all_hooks() -> dict:
    """Return dict of registered hooks."""
    return {k: list(v) for k, v in _hooks.items()}


def init_plugin(name: str, window=None):
    """Instantiate and initialize a plugin."""
    info = _plugins.get(name)
    if not info:
        return None
    try:
        instance = info["class"](window)
        info["instance"] = instance
        if hasattr(instance, "on_load"):
            instance.on_load()
        return instance
    except Exception as e:
        logger.error("Failed to init plugin %s: %s", name, e)
        return None


class PluginBase:
    """Base class for plugins."""
    name = "Unnamed Plugin"
    version = "1.0"

    def __init__(self, window=None):
        self.window = window

    def on_load(self):
        pass

    def on_unload(self):
        pass

    def get_info(self) -> dict:
        return {"name": self.name, "version": self.version}


# ──────────────────────── Plugin Marketplace ────────────────────────

class PluginMarketplace:
    """Plugin marketplace for discovering and managing plugins."""

    OFFICIAL_PLUGINS = [
        {
            "name": "Mermaid Diagrams",
            "version": "1.2.0",
            "author": "MarkdownToPDF Team",
            "description": "Рендеринг Mermaid диаграмм в PDF",
            "description_en": "Render Mermaid diagrams in PDF",
            "category": "diagrams",
            "downloads": 15420,
            "rating": 4.8,
            "installed": True,
            "url": "https://github.com/md2pdf/plugins/mermaid",
        },
        {
            "name": "LaTeX Math",
            "version": "1.1.0",
            "author": "MarkdownToPDF Team",
            "description": "Поддержка математических формул LaTeX",
            "description_en": "LaTeX math formula support",
            "category": "math",
            "downloads": 12300,
            "rating": 4.7,
            "installed": True,
            "url": "https://github.com/md2pdf/plugins/latex",
        },
        {
            "name": "Chart.js Export",
            "version": "1.0.0",
            "author": "Community",
            "description": "Экспорт графиков Chart.js в PDF",
            "description_en": "Export Chart.js charts to PDF",
            "category": "charts",
            "downloads": 8900,
            "rating": 4.5,
            "installed": False,
            "url": "https://github.com/md2pdf/plugins/chartjs",
        },
        {
            "name": "PlantUML Support",
            "version": "2.0.0",
            "author": "Community",
            "description": "Рендеринг PlantUML диаграмм",
            "description_en": "Render PlantUML diagrams",
            "category": "diagrams",
            "downloads": 6700,
            "rating": 4.3,
            "installed": False,
            "url": "https://github.com/md2pdf/plugins/plantuml",
        },
        {
            "name": "Emoji Toolkit",
            "version": "1.3.0",
            "author": "Community",
            "description": "Расширенная поддержка эмодзи",
            "description_en": "Extended emoji support",
            "category": "utilities",
            "downloads": 9200,
            "rating": 4.6,
            "installed": False,
            "url": "https://github.com/md2pdf/plugins/emoji",
        },
        {
            "name": "Code Runner",
            "version": "1.0.0",
            "author": "Community",
            "description": "Запуск кода прямо из Markdown",
            "description_en": "Run code directly from Markdown",
            "category": "development",
            "downloads": 5400,
            "rating": 4.2,
            "installed": False,
            "url": "https://github.com/md2pdf/plugins/coderunner",
        },
    ]

    def __init__(self):
        self.installed_plugins: dict[str, dict] = {}
        self._load_installed()

    def _load_installed(self):
        """Load list of installed plugins."""
        for plugin in self.OFFICIAL_PLUGINS:
            if plugin.get("installed"):
                self.installed_plugins[plugin["name"]] = plugin

    def get_plugins(self, category: str = None) -> list[dict]:
        """Get available plugins, optionally filtered by category."""
        plugins = self.OFFICIAL_PLUGINS
        if category:
            plugins = [p for p in plugins if p["category"] == category]
        return plugins

    def get_categories(self) -> list[str]:
        """Get all plugin categories."""
        cats = set(p["category"] for p in self.OFFICIAL_PLUGINS)
        return sorted(cats)

    def install_plugin(self, name: str) -> bool:
        """Install a plugin."""
        for plugin in self.OFFICIAL_PLUGINS:
            if plugin["name"] == name:
                plugin["installed"] = True
                self.installed_plugins[name] = plugin
                return True
        return False

    def uninstall_plugin(self, name: str) -> bool:
        """Uninstall a plugin."""
        if name in self.installed_plugins:
            for plugin in self.OFFICIAL_PLUGINS:
                if plugin["name"] == name:
                    plugin["installed"] = False
            del self.installed_plugins[name]
            return True
        return False

    def search_plugins(self, query: str) -> list[dict]:
        """Search plugins by name or description."""
        query_lower = query.lower()
        return [
            p for p in self.OFFICIAL_PLUGINS
            if query_lower in p["name"].lower() or query_lower in p["description"].lower()
        ]


def get_marketplace() -> PluginMarketplace:
    """Get singleton marketplace instance."""
    if not hasattr(get_marketplace, "_instance"):
        get_marketplace._instance = PluginMarketplace()
    return get_marketplace._instance
