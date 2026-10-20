"""Тесты разбиения `dialogs.py` на пакет (TASK-011 / PLAN-011).

Проверяет, что перенос 17 классов в `src/gui/dialogs/` НЕ потерял и НЕ
продублировал ничего, что фасад совместимости работает и что ни один
модуль пакета не превратился в нового «монстра».
"""
import ast
import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _install_qt_stub():
    """Ставит заглушки PyQt6, если настоящий не установлен (см. test_gui_stubs.py)."""
    try:
        import PyQt6  # noqa: F401
        return False
    except ImportError:
        pass

    class _Anything:
        def __init__(self, *args, **kwargs):
            pass

        def __getattr__(self, item):
            return _Anything()

        def __call__(self, *args, **kwargs):
            return _Anything()

        def __getitem__(self, item):
            return _Anything()

    class _Base:
        """Заглушка, пригодная как базовый класс (можно наследоваться)."""

        def __init__(self, *args, **kwargs):
            pass

        def __getattr__(self, item):
            return _Anything()

    for mod_name in (
        "PyQt6", "PyQt6.QtWidgets", "PyQt6.QtCore", "PyQt6.QtGui",
        "PyQt6.QtPrintSupport", "PyQt6.QtSvg", "PyQt6.QtNetwork",
    ):
        mod = types.ModuleType(mod_name)

        def _getattr(name, _m=mod):
            # все виджеты/сигналы — классы, чтобы от них можно было наследоваться
            cls = type(name, (_Base,), {})
            setattr(_m, name, cls)
            return cls

        mod.__getattr__ = _getattr
        sys.modules[mod_name] = mod

    core = sys.modules["PyQt6.QtCore"]
    core.Qt = _Anything()
    core.QSettings = type("QSettings", (_Base,), {})
    gui = sys.modules["PyQt6.QtGui"]
    gui.QColor = type("QColor", (_Base,), {})
    return True


STUB_ACTIVE = _install_qt_stub()

GUI = os.path.join(ROOT, "src", "gui")
PKG = os.path.join(GUI, "dialogs")

# Эталонный список 17 классов из исходного dialogs.py (снят AST-замером).
BASELINE_CLASSES = [
    "GitHubSyncDialog",
    "PluginManagerDialog",
    "MultiExportDialog",
    "CitationManagerDialog",
    "DocumentBuilderDialog",
    "ReadabilityDashboardDialog",
    "DocumentAuditorDialog",
    "MarkdownTOCDialog",
    "SnippetsDialog",
    "MarkdownTableDialog",
    "ColorButton",
    "PDFStyleEditorDialog",
    "RevisionHistoryDialog",
    "DiffDialog",
    "SnippetsManagerDialog",
    "CloudTemplatesDialog",
    "ShortcutsDialog",
]

# Классы, которые обязаны существовать (публичный API пакета).
CONSUMERS = [
    os.path.join(GUI, "main_window.py"),
    os.path.join(GUI, "document_tools.py"),
    os.path.join(GUI, "window_tools.py"),
]


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _pkg_modules():
    return [
        os.path.join(PKG, fn)
        for fn in sorted(os.listdir(PKG))
        if fn.endswith(".py") and fn != "__init__.py"
    ]


def _class_defs_in_pkg():
    """{class_name: [modules]} — где определён каждый класс."""
    out = {}
    for path in _pkg_modules():
        for node in ast.walk(ast.parse(_read(path), path)):
            if isinstance(node, ast.ClassDef):
                out.setdefault(node.name, []).append(os.path.basename(path))
    return out


def test_all_classes_present():
    """Все 17 классов определены в пакете ровно по разу."""
    defs = _class_defs_in_pkg()
    missing = [c for c in BASELINE_CLASSES if c not in defs]
    assert not missing, f"Потеряны классы при разбиении: {missing}"
    print(f"[PASS] test_all_classes_present ({len(BASELINE_CLASSES)} классов на месте)")


def test_no_duplicate_definitions():
    """Ни один класс не определён более чем в одном модуле пакета."""
    defs = _class_defs_in_pkg()
    dupes = {k: v for k, v in defs.items() if len(v) > 1}
    assert not dupes, f"Классы определены несколько раз: {dupes}"
    print("[PASS] test_no_duplicate_definitions")


def test_facade_reexports_all():
    """`__init__.py` импортирует все 17 имён и объявляет их в __all__."""
    src = _read(os.path.join(PKG, "__init__.py"))
    tree = ast.parse(src)
    exported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for a in node.names:
                exported.add(a.asname or a.name)
    missing = [c for c in BASELINE_CLASSES if c not in exported]
    assert not missing, f"Фасад не реэкспортирует: {missing}"
    # __all__ должен перечислять те же имена
    assert "__all__" in src, "В __init__.py нет __all__"
    for c in BASELINE_CLASSES:
        assert c in src, f"{c} отсутствует в __init__.py"
    print("[PASS] test_facade_reexports_all")


def test_modules_compile():
    """Все модули пакета компилируются."""
    paths = _pkg_modules() + [os.path.join(PKG, "__init__.py")]
    for p in paths:
        with open(p, "rb") as f:
            compile(f.read(), p, "exec")
    print(f"[PASS] test_modules_compile ({len(paths)} модулей)")


def test_no_monster_module():
    """Ни один модуль пакета не превышает разумный размер (защита от распухания).

    Порог 550 строк: самый крупный модуль (`content.py`, ~433 строки) содержит
    один 261-строчный класс `DocumentBuilderDialog` — дробить его смысла нет.
    Исходный монолит был 1534 строки, так что регресс поймается.
    """
    LIMIT = 550
    bad = []
    for p in _pkg_modules() + [os.path.join(PKG, "__init__.py")]:
        loc = len(_read(p).splitlines())
        if loc > LIMIT:
            bad.append(f"{os.path.basename(p)}: {loc} строк")
    assert not bad, f"Модуль-«монстр» в пакете: {bad}"
    print(f"[PASS] test_no_monster_module (лимит {LIMIT} строк)")


def test_old_module_removed():
    """Старый монолитный dialogs.py удалён (не осталось рядом с пакетом)."""
    assert not os.path.exists(os.path.join(GUI, "dialogs.py")), \
        "src/gui/dialogs.py не удалён — конфликт с пакетом"
    print("[PASS] test_old_module_removed")


def test_consumers_still_import_package():
    """Хотя бы одни потребители по-прежнему импортируют имена из src.gui.dialogs.

    Раньше список был жёстко задан, но после TASK-012 ленивые импорты
    переехали в миксины, поэтому проверяем весь каталог src/gui.
    """
    total = 0
    importers = []
    for root, _dirs, files in os.walk(GUI):
        if "__pycache__" in root:
            continue
        for fn in sorted(files):
            if not fn.endswith(".py"):
                continue
            src = _read(os.path.join(root, fn))
            n = src.count("from src.gui.dialogs import")
            if n:
                total += n
                importers.append(os.path.relpath(os.path.join(root, fn), GUI))
    assert total > 0, "Ни один модуль src/gui не импортирует из src.gui.dialogs"
    print(f"[PASS] test_consumers_still_import_package ({total} импортов в {len(importers)} файлах)")


def test_facade_importable_under_stub():
    """Пакет реально импортируется и отдаёт все 17 имён (под Qt-стабом)."""
    import importlib
    pkg = importlib.import_module("src.gui.dialogs")
    missing = [c for c in BASELINE_CLASSES if not hasattr(pkg, c)]
    assert not missing, f"Фасад не отдаёт имена: {missing}"
    exported = set(getattr(pkg, "__all__", []))
    assert exported >= set(BASELINE_CLASSES), \
        f"__all__ неполный: {sorted(set(BASELINE_CLASSES) - exported)}"
    # старое имя модуля больше не должно резолвиться как файл
    assert not os.path.exists(os.path.join(GUI, "dialogs.py"))
    print(f"[PASS] test_facade_importable_under_stub (Qt-стаб: {STUB_ACTIVE}, {len(BASELINE_CLASSES)} имён)")


def main():
    tests = [
        test_modules_compile,
        test_old_module_removed,
        test_all_classes_present,
        test_no_duplicate_definitions,
        test_facade_reexports_all,
        test_no_monster_module,
        test_consumers_still_import_package,
        test_facade_importable_under_stub,
    ]
    for t in tests:
        t()
    print("\nAll TASK-011 dialogs-package tests passed!")


if __name__ == "__main__":
    main()
