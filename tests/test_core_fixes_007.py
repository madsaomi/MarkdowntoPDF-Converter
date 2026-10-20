"""Регрессионные тесты мелких багов ядра (PLAN-007/TASK-007).

Проверяет 4 исправления:
1. Дублирующийся лог «saved» в `ConversionThread` (один файл -> одна строка).
2. Шэдоуинг `QThread.finished` в `KrokiCheckThread` (сигнал переименован в `checked`).
3. Busy-wait паузы в TTS (заменён на блокирующее ожидание события).
4. Захардкоженный `<html lang="en">` в `templates/base.html` (теперь из `lang`).
"""
import ast
import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

THREADS_PY = os.path.join(ROOT, "src", "gui", "threads.py")
TTS_PY = os.path.join(ROOT, "src", "core", "tts_engine.py")
BASE_HTML = os.path.join(ROOT, "templates", "base.html")


def _install_qt_stub():
    """Ставит заглушки PyQt6, если настоящий не установлен."""
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

    for mod_name in (
        "PyQt6", "PyQt6.QtWidgets", "PyQt6.QtCore", "PyQt6.QtGui",
        "PyQt6.QtPrintSupport", "PyQt6.QtSvg", "PyQt6.QtNetwork",
    ):
        mod = types.ModuleType(mod_name)
        mod.__getattr__ = lambda name, _m=mod: _Anything()
        sys.modules[mod_name] = mod

    core = sys.modules["PyQt6.QtCore"]
    core.Qt = _Anything()
    core.QThread = _Anything
    core.pyqtSignal = lambda *a, **k: _Anything()
    core.QMutex = _Anything
    return True


STUB_ACTIVE = _install_qt_stub()


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


# ─────────────────── 1. Дублирующийся лог «saved» ───────────────────

def test_no_duplicate_saved_log():
    """В `run()` ровно один emit `log_saved` — суффикс собирается в переменную."""
    tree = ast.parse(_read(THREADS_PY), THREADS_PY)
    run_fn = None
    for cls in ast.walk(tree):
        if isinstance(cls, ast.ClassDef) and cls.name == "ConversionThread":
            for node in cls.body:
                if isinstance(node, ast.FunctionDef) and node.name == "run":
                    run_fn = node
    assert run_fn is not None, "Не найден ConversionThread.run"

    emits = []
    for node in ast.walk(run_fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "emit":
            # Разворачиваем self.log.emit(...)
            inner = node.func.value
            if isinstance(inner, ast.Attribute) and inner.attr == "log":
                arg = node.args[0] if node.args else None
                emits.append(ast.unparse(arg) if arg else "")

    saved = [e for e in emits if "log_saved" in e]
    assert len(saved) == 1, (
        f"Ожидался ровно один emit log_saved, найдено {len(saved)}: {saved}"
    )
    assert "saved_suffix" in saved[0], "Единый emit должен включать saved_suffix"
    print("[PASS] test_no_duplicate_saved_log")


# ─────────────────── 2. Шэдоуинг QThread.finished ───────────────────

def test_kroki_signal_not_shadowing_finished():
    """KrokiCheckThread не переопределяет QThread.finished; сигнал называется `checked`."""
    src = _read(THREADS_PY)
    tree = ast.parse(src, THREADS_PY)
    signals = {}
    for cls in ast.walk(tree):
        if isinstance(cls, ast.ClassDef) and cls.name == "KrokiCheckThread":
            for node in cls.body:
                if isinstance(node, ast.Assign):
                    target = node.targets[0]
                    if isinstance(target, ast.Name):
                        signals[target.id] = ast.unparse(node.value)
    assert "finished" not in signals, "KrokiCheckThread не должен переопределять QThread.finished"
    assert "checked" in signals, "Ожидается сигнал `checked`"
    # Потребитель обновлён
    main_window = _read(os.path.join(ROOT, "src", "gui", "main_window.py"))
    assert "kroki_thread.checked.connect" in main_window, "main_window не подключён к `checked`"
    assert "kroki_thread.finished.connect" not in main_window
    print("[PASS] test_kroki_signal_not_shadowing_finished")


# ─────────────────── 3. Busy-wait в TTS ───────────────────

def test_tts_pause_not_busy_wait():
    """В `_speak_thread` пауза ожидает событие, а не крутит пустой цикл."""
    src = _read(TTS_PY)
    assert "_resume_event" in src, "Отсутствует threading.Event для пробуждения"
    # Запрещён старый пустой шаблон busy-wait
    assert "while self._is_paused:\n                    if not self._is_playing:\n                        break" not in src
    # Должно быть ожидание события
    assert "_resume_event.wait(" in src, "Пауза должна ждать событие (_resume_event.wait)"
    assert "self._resume_event.set()" in src, "resume()/stop() должны будить поток"
    print("[PASS] test_tts_pause_not_busy_wait")


def test_tts_pause_resume_semantics():
    """pause() блокирует ожидание, resume() снимает паузу (без Qt)."""
    # Импортируем без Qt — tts_engine не зависит от PyQt6
    from src.core.tts_engine import AdvancedTTSEngine
    engine = AdvancedTTSEngine()
    assert not engine.is_paused()
    engine.pause()
    assert engine.is_paused()
    assert not engine._resume_event.is_set(), "pause() должен сбрасывать событие"
    engine.resume()
    assert not engine.is_paused()
    assert engine._resume_event.is_set(), "resume() должен устанавливать событие"
    print("[PASS] test_tts_pause_resume_semantics")


# ─────────────────── 4. lang в шаблоне ───────────────────

def test_base_html_lang_not_hardcoded():
    """base.html использует переменную lang, а не захардкоженный 'en'."""
    src = _read(BASE_HTML)
    assert '<html lang="en">' not in src, "<html lang> захардкожен"
    assert '{{ lang' in src, "Ожидается подстановка {{ lang }}"
    print("[PASS] test_base_html_lang_not_hardcoded")


def test_rendered_html_lang_matches():
    """PDFRenderer.render_html прокидывает lang в атрибут <html lang=...>."""
    from src.core.renderer import PDFRenderer
    renderer = PDFRenderer(os.path.join(ROOT, "templates"))
    html_ru = renderer.render_html("<p>x</p>", {}, lang="ru")
    html_en = renderer.render_html("<p>x</p>", {}, lang="en")
    assert '<html lang="ru">' in html_ru, "lang=ru не проброшен"
    assert '<html lang="en">' in html_en, "lang=en не проброшен"
    print("[PASS] test_rendered_html_lang_matches")


def main():
    tests = [
        test_no_duplicate_saved_log,
        test_kroki_signal_not_shadowing_finished,
        test_tts_pause_not_busy_wait,
        test_tts_pause_resume_semantics,
        test_base_html_lang_not_hardcoded,
        test_rendered_html_lang_matches,
    ]
    for t in tests:
        t()
    print(f"\nAll TASK-007 core-fix tests passed! (Qt stub: {STUB_ACTIVE})")


if __name__ == "__main__":
    main()
