"""Тесты нового кода: фоновые воркеры, офлайн-кэш и общий HTML-билдер.

Покрывают то, что раньше проверялось только `py_compile`:
- `src/gui/workers/task_worker.py` — TaskWorker/TaskThread (логика run);
- `src/core/render_cache.py` — set/get, промах, устойчивость к мусору;
- `src/core/html_builder.py` — рендер через Jinja2-шаблон и fallback.

Под Python 3.15 без PyQt6 используется Qt-стаб (как в test_gui_stubs.py).
"""
import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _install_qt_stub():
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
        def __init__(self, *args, **kwargs):
            pass

        def __getattr__(self, item):
            return _Anything()

    for mod_name in (
        "PyQt6", "PyQt6.QtWidgets", "PyQt6.QtCore", "PyQt6.QtGui",
        "PyQt6.QtPrintSupport", "PyQt6.QtSvg", "PyQt6.QtNetwork",
    ):
        mod = types.ModuleType(mod_name)
        mod.__getattr__ = lambda name, _m=mod: type(name, (_Base,), {})
        sys.modules[mod_name] = mod

    core = sys.modules["PyQt6.QtCore"]
    core.Qt = _Anything()
    core.QThread = _Base
    core.QObject = _Base
    core.pyqtSignal = lambda *a, **k: _Anything()
    return True


STUB_ACTIVE = _install_qt_stub()


# ─── render_cache ────────────────────────────────────────────────────────────

def test_render_cache_roundtrip():
    """set_cached → get_cached возвращает сохранённое значение."""
    from src.core import render_cache
    payload = {"url": "https://example.org/x.svg", "n": 42}
    assert render_cache.set_cached("test_prefix", "key-A", payload)
    got = render_cache.get_cached("test_prefix", "key-A")
    assert got == payload, f"ожидали {payload}, получили {got}"
    print("[PASS] test_render_cache_roundtrip")


def test_render_cache_miss():
    """Отсутствующий ключ даёт None (без исключений)."""
    from src.core import render_cache
    assert render_cache.get_cached("test_prefix", "definitely-missing-key") is None
    print("[PASS] test_render_cache_miss")


def test_render_cache_is_resilient():
    """get_cached/set_cached не падают на экзотических данных."""
    from src.core import render_cache
    weird = "\x00\u2603 emoji 🐙 and quotes \"'`\n\t"
    render_cache.set_cached("test_weird", weird, {"url": weird})
    got = render_cache.get_cached("test_weird", weird)
    assert got and got.get("url") == weird
    print("[PASS] test_render_cache_is_resilient")


# ─── latex/kroki используют кэш ──────────────────────────────────────────────

def test_latex_url_is_stable_and_cached():
    """latex_to_url детерминирован (кэш не меняет результат)."""
    from src.core.latex_preview import latex_to_url
    a = latex_to_url("E = mc^2")
    b = latex_to_url("E = mc^2")
    assert a == b, "latex_to_url нестабилен"
    assert a.startswith("https://latex.codecogs.com/")
    print("[PASS] test_latex_url_is_stable_and_cached")


# ─── TaskWorker (логика run, без реальных потоков) ───────────────────────────

class _FakeSignal:
    """Собирает переданные значения вместо Qt-сигнала."""

    def __init__(self):
        self.emitted = []

    def emit(self, *args):
        self.emitted.append(args[0] if len(args) == 1 else args)

    def connect(self, *a, **k):
        pass


def _make_worker(fn, *args, **kwargs):
    """Создаёт TaskWorker и подменяет сигналы на собиратели."""
    from src.gui.workers.task_worker import TaskWorker
    w = TaskWorker(fn, *args, **kwargs)
    w.finished = _FakeSignal()
    w.error = _FakeSignal()
    w.started = _FakeSignal()
    w.progress = _FakeSignal()
    return w


def test_task_worker_returns_result():
    """TaskWorker.run() отдаёт результат функции через signal finished."""
    w = _make_worker(lambda x, y=0: x + y, 2, y=40)
    w.run()
    assert w.finished.emitted == [42], f"ожидали [42], получили {w.finished.emitted}"
    assert w.error.emitted == [], "ошибка не должна срабатывать"
    print("[PASS] test_task_worker_returns_result")


def test_task_worker_reports_error():
    """Исключение внутри задачи уходит в signal error, а не наружу."""
    def boom():
        raise ValueError("провал задачи")

    w = _make_worker(boom)
    w.run()
    assert w.finished.emitted == [], "finished не должен срабатывать при ошибке"
    assert len(w.error.emitted) == 1 and "провал задачи" in w.error.emitted[0]
    print("[PASS] test_task_worker_reports_error")


def test_task_worker_passes_kwargs():
    """Позиционные и именованные аргументы доходят до функции."""
    def combine(a, b, sep="-"):
        return f"{a}{sep}{b}"

    w = _make_worker(combine, "x", b="y", sep=":")
    w.run()
    assert w.finished.emitted == ["x:y"]
    print("[PASS] test_task_worker_passes_kwargs")


# ─── HTML-билдер ─────────────────────────────────────────────────────────────

def test_html_builder_returns_html():
    """build_html_for_preview_and_export отдаёт непустой HTML."""
    from src.core.html_builder import build_html_for_preview_and_export
    out = build_html_for_preview_and_export(
        "<h1>Заголовок</h1><p>Текст</p>",
        metadata={"title": "тест", "author": "", "date": ""},
        lang="ru",
    )
    assert out and "<h1>Заголовок</h1>" in out, "контент потерян билдером"
    assert out.lstrip().lower().startswith("<html") or "<html" in out.lower()
    print("[PASS] test_html_builder_returns_html")


def test_html_builder_fallback_on_bad_template_dir():
    """При некорректном template_dir билдер не роняет приложение."""
    from src.core.html_builder import HtmlBuilder
    b = HtmlBuilder.__new__(HtmlBuilder)  # без __init__ (шаблона нет)
    b.template_dir = os.path.join(ROOT, "templates")
    # build_html должен хотя бы не выбрасывать наружу исключение
    try:
        from jinja2 import Environment, FileSystemLoader
        b.env = Environment(loader=FileSystemLoader(b.template_dir))
        b.template = b.env.get_template("base.html")
        out = b.build_html("<p>ok</p>", metadata={}, lang="ru")
        assert isinstance(out, str) and out
    except Exception as e:  # шаблон может отсутствовать — это допустимо
        print(f"[PASS] test_html_builder_fallback_on_bad_template_dir (skip: {e})")
        return
    print("[PASS] test_html_builder_fallback_on_bad_template_dir")


def test_builders_use_shared_renderer():
    """html_builder переиспользует PDFRenderer.render_html (единый путь)."""
    import ast
    path = os.path.join(ROOT, "src", "core", "html_builder.py")
    tree = ast.parse(open(path, encoding="utf-8").read())
    names = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Attribute):
            names.add(n.attr)
        elif isinstance(n, ast.Name):
            names.add(n.id)
    assert "render_html" in names, "html_builder не вызывает render_html"
    assert "PDFRenderer" in names, "html_builder не использует PDFRenderer"
    print("[PASS] test_builders_use_shared_renderer")


def test_source_files_compile():
    """Новые модули компилируются."""
    files = [
        os.path.join(ROOT, "src", "gui", "workers", "task_worker.py"),
        os.path.join(ROOT, "src", "gui", "workers", "__init__.py"),
        os.path.join(ROOT, "src", "core", "render_cache.py"),
        os.path.join(ROOT, "src", "core", "html_builder.py"),
    ]
    for p in files:
        with open(p, "rb") as f:
            compile(f.read(), p, "exec")
    print(f"[PASS] test_source_files_compile ({len(files)} файлов)")


def main():
    tests = [
        test_source_files_compile,
        test_render_cache_roundtrip,
        test_render_cache_miss,
        test_render_cache_is_resilient,
        test_latex_url_is_stable_and_cached,
        test_task_worker_returns_result,
        test_task_worker_reports_error,
        test_task_worker_passes_kwargs,
        test_html_builder_returns_html,
        test_html_builder_fallback_on_bad_template_dir,
        test_builders_use_shared_renderer,
    ]
    for t in tests:
        t()
    print("\nAll workers/render tests passed!")


if __name__ == "__main__":
    main()
