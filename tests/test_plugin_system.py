"""Тесты plugin_system (PLAN-005/TASK-005).

Проверяем реестр плагинов, систему хуков (включая изоляцию падающих
обработчиков), загрузку из каталога и PluginMarketplace.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import plugin_system as ps


def test_register_and_get_plugins():
    """Декоратор register_plugin регистрирует класс с версией и автором."""
    @ps.register_plugin("Test Plugin", version="2.5", author="Tester")
    class MyPlugin(ps.PluginBase):
        name = "Test Plugin"

    plugins = ps.get_all_plugins()
    assert "Test Plugin" in plugins
    info = plugins["Test Plugin"]
    assert info["version"] == "2.5"
    assert info["author"] == "Tester"
    assert info["class"] is MyPlugin
    print("[PASS] test_register_and_get_plugins")


def test_init_plugin_calls_on_load():
    """init_plugin создаёт экземпляр и вызывает on_load."""
    loaded = []

    @ps.register_plugin("Lifecycle Plugin")
    class Lifecycle(ps.PluginBase):
        def on_load(self):
            loaded.append(True)

    window = object()
    instance = ps.init_plugin("Lifecycle Plugin", window)
    assert isinstance(instance, Lifecycle)
    assert instance.window is window
    assert loaded == [True]
    print("[PASS] test_init_plugin_calls_on_load")


def test_init_plugin_unknown_returns_none():
    """init_plugin для неизвестного имени возвращает None без исключения."""
    assert ps.init_plugin("Нет такого плагина") is None
    print("[PASS] test_init_plugin_unknown_returns_none")


def test_init_plugin_failure_isolated():
    """Падение в on_load изолируется — init_plugin возвращает None."""
    @ps.register_plugin("Broken Plugin")
    class Broken(ps.PluginBase):
        def on_load(self):
            raise RuntimeError("nope")

    assert ps.init_plugin("Broken Plugin") is None
    print("[PASS] test_init_plugin_failure_isolated")


def test_hooks_and_emit():
    """Хуки вызываются, падающий обработчик не мешает остальным."""
    calls = []

    @ps.hook("on_export")
    def good_handler(path):
        calls.append(path)

    @ps.hook("on_export")
    def bad_handler(path):
        raise ValueError("bad")

    @ps.hook("on_export")
    def after_handler(path):
        calls.append("after:" + path)

    ps.emit_hook("on_export", "/tmp/x.pdf")
    assert calls == ["/tmp/x.pdf", "after:/tmp/x.pdf"], calls
    print("[PASS] test_hooks_and_emit")


def test_unknown_hook_registration_ignored():
    """Регистрация на неизвестный хук не добавляет обработчик."""
    before = sum(len(v) for v in ps.get_all_hooks().values())

    @ps.hook("nonexistent_hook")
    def handler():
        pass

    after = sum(len(v) for v in ps.get_all_hooks().values())
    assert before == after
    print("[PASS] test_unknown_hook_registration_ignored")


def test_load_plugins_from_dir():
    """load_plugins_from_dir исполняет .py и игнорирует файлы на '_'."""
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "my_plugin.py"), "w", encoding="utf-8") as f:
            f.write("REGISTERED = True\n")
        with open(os.path.join(d, "_private.py"), "w", encoding="utf-8") as f:
            f.write("RAISED = True\nraise RuntimeError('must not execute')\n")
        ps.load_plugins_from_dir(d)  # не должно бросить исключение
    # Несуществующий каталог — тихий no-op
    ps.load_plugins_from_dir(os.path.join(d, "does_not_exist"))
    print("[PASS] test_load_plugins_from_dir")


def test_marketplace_install_uninstall_search():
    """Marketplace: фильтр по категории, установка, удаление, поиск."""
    mp = ps.PluginMarketplace()
    assert len(mp.get_plugins()) == len(ps.PluginMarketplace.OFFICIAL_PLUGINS)
    diagrams = mp.get_plugins(category="diagrams")
    assert all(p["category"] == "diagrams" for p in diagrams)
    assert mp.get_categories() == sorted(set(p["category"] for p in ps.PluginMarketplace.OFFICIAL_PLUGINS))

    assert mp.install_plugin("Chart.js Export") is True
    assert "Chart.js Export" in mp.installed_plugins
    assert mp.install_plugin("No Such Plugin") is False

    assert mp.uninstall_plugin("Chart.js Export") is True
    assert "Chart.js Export" not in mp.installed_plugins
    assert mp.uninstall_plugin("Chart.js Export") is False

    found = mp.search_plugins("mermaid")
    assert any(p["name"] == "Mermaid Diagrams" for p in found)
    print("[PASS] test_marketplace_install_uninstall_search")


def test_marketplace_singleton():
    """get_marketplace возвращает один и тот же экземпляр."""
    assert ps.get_marketplace() is ps.get_marketplace()
    print("[PASS] test_marketplace_singleton")


def main():
    tests = [
        test_register_and_get_plugins,
        test_init_plugin_calls_on_load,
        test_init_plugin_unknown_returns_none,
        test_init_plugin_failure_isolated,
        test_hooks_and_emit,
        test_unknown_hook_registration_ignored,
        test_load_plugins_from_dir,
        test_marketplace_install_uninstall_search,
        test_marketplace_singleton,
    ]
    for t in tests:
        t()
    print("\nAll plugin system tests passed!")


if __name__ == "__main__":
    main()
