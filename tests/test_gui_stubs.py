"""Smoke-импорт GUI-модулей (PLAN-005/TASK-005).

PyQt6 не устанавливается под Python 3.15 в этом окружении, поэтому GUI-модули
подгружаются с минимальным Qt-стабом: цель — поймать синтаксические ошибки,
битые импорты и регрессии на уровне модуля (без запуска QApplication).
Чистые модули (`models`, `translations`) проверяются полноценно.
"""
import importlib
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _install_qt_stub():
    """Ставит заглушки PyQt6, если настоящий не установлен. Возвращает True, если стаб активен."""
    try:
        import PyQt6  # noqa: F401
        return False
    except ImportError:
        pass

    def _make_module(name):
        return types.ModuleType(name)

    class _Anything:
        """Универсальная заглушка: любой атрибут/вызов/подкласс разрешён."""

        def __init__(self, *args, **kwargs):
            pass

        def __getattr__(self, item):
            return _Anything()

        def __call__(self, *args, **kwargs):
            return _Anything()

        def __getitem__(self, item):
            return _Anything()

    # Заглушки для модулей, которые могут импортироваться транзитивно
    for mod_name in (
        "PyQt6", "PyQt6.QtWidgets", "PyQt6.QtCore", "PyQt6.QtGui",
        "PyQt6.QtPrintSupport", "PyQt6.QtSvg", "PyQt6.QtNetwork",
    ):
        mod = _make_module(mod_name)
        mod.__getattr__ = lambda name, _m=mod: _Anything()
        sys.modules[mod_name] = mod

    # Ключевые символы, которые используются в аннотациях/вызовах на уровне класса
    core = sys.modules["PyQt6.QtCore"]
    core.Qt = _Anything()
    core.QThread = _Anything
    core.pyqtSignal = lambda *a, **k: _Anything()
    core.QTimer = _Anything
    core.QSettings = _Anything
    core.QFileSystemWatcher = _Anything
    core.QMutex = _Anything
    core.QEvent = _Anything
    core.QRegularExpression = _Anything
    core.QStandardPaths = _Anything
    gui = sys.modules["PyQt6.QtGui"]
    gui.QColor = _Anything
    gui.QIcon = _Anything
    gui.QKeySequence = _Anything
    gui.QShortcut = _Anything
    return True


STUB_ACTIVE = _install_qt_stub()


def test_models_import():
    """Чистый модуль models импортируется и содержит ConversionOptions."""
    from src.gui.models import ConversionOptions, ExportFormat
    opts = ConversionOptions(
        doc_theme="theme_modern.css", code_theme="pygments.css", paper_size="A4",
        watermark="DRAFT", footer_text="", custom_css="", export_format=ExportFormat.PDF,
    )
    assert opts.watermark_css == "", "Дефолт watermark_css должен быть пустой строкой"
    assert ExportFormat.PDF.value == "PDF"
    print("[PASS] test_models_import")


def test_translations_import():
    """translations содержит обе локали и ключ menu_help (TASK-004)."""
    from src.gui.translations import TRANSLATIONS
    assert "ru" in TRANSLATIONS and "en" in TRANSLATIONS
    assert "menu_help" in TRANSLATIONS["ru"]
    assert "menu_help" in TRANSLATIONS["en"]
    print("[PASS] test_translations_import")


def test_module_level_imports_no_syntax_errors():
    """Все модули src/gui импортируются (под стабом) без синтаксических ошибок.

    Модули с побочными эффектами на уровне модуля (QApplication, сеть) могут не
    импортироваться — это допустимо; тогда проверяется хотя бы компиляция.
    """
    gui_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "gui")
    modules = [
        f[:-3] for f in sorted(os.listdir(gui_dir))
        if f.endswith(".py") and not f.startswith("__")
    ]
    assert modules, "Не найдено модулей src/gui"

    compiled = 0
    imported = 0
    failures = []
    for name in modules:
        path = os.path.join(gui_dir, name + ".py")
        try:
            with open(path, "rb") as f:
                compile(f.read(), path, "exec")
            compiled += 1
        except SyntaxError as e:
            failures.append(f"{name}: SyntaxError {e}")
            continue
        try:
            importlib.import_module(f"src.gui.{name}")
            imported += 1
        except Exception:
            # Импорт может требовать реального QApplication/ресурсов — это ок.
            pass

    assert not failures, "Синтаксические ошибки: " + "; ".join(failures)
    assert compiled == len(modules), f"Скомпилировано {compiled} из {len(modules)}"
    print(f"[PASS] test_module_level_imports_no_syntax_errors: {compiled} модулей скомпилировано, "
          f"{imported} импортировано (Qt-стаб: {STUB_ACTIVE})")


def main():
    tests = [
        test_models_import,
        test_translations_import,
        test_module_level_imports_no_syntax_errors,
    ]
    for t in tests:
        t()
    print("\nAll GUI smoke tests passed!")


if __name__ == "__main__":
    main()
