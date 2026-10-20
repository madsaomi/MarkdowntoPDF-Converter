"""Tests for AppConfig.resolve_weasyprint_cmd (PDF engine resolver, PLAN-002)."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import AppConfig


def test_portable_exe_has_priority():
    """Существующий exe возвращается как приоритетный движок."""
    with tempfile.TemporaryDirectory() as td:
        exe = os.path.join(td, "weasyprint.exe")
        with open(exe, "w") as f:
            f.write("stub")
        cmd = AppConfig.resolve_weasyprint_cmd(exe_path=exe)
        assert cmd == [exe], f"Ожидался [{exe}], получено {cmd}"


def test_pip_fallback_when_no_exe():
    """Без exe, но с pip-пакетом -> команда python -m weasyprint."""
    with tempfile.TemporaryDirectory() as td:
        exe = os.path.join(td, "weasyprint.exe")  # не существует
        cmd = AppConfig.resolve_weasyprint_cmd(exe_path=exe, module_available=True)
        assert cmd == [sys.executable, "-m", "weasyprint"], f"Получено {cmd}"


def test_empty_path_uses_default_resolution():
    """Пустая строка (движок не задан) не ломает резолвер -> pip-fallback."""
    cmd = AppConfig.resolve_weasyprint_cmd(exe_path="", module_available=True)
    assert cmd == [sys.executable, "-m", "weasyprint"], f"Получено {cmd}"


def test_error_when_nothing_available():
    """Ни exe, ни пакета -> FileNotFoundError с инструкцией."""
    with tempfile.TemporaryDirectory() as td:
        exe = os.path.join(td, "weasyprint.exe")
        try:
            AppConfig.resolve_weasyprint_cmd(exe_path=exe, module_available=False)
        except FileNotFoundError as e:
            msg = str(e)
            assert "weasyprint" in msg.lower()
            assert "pip install weasyprint" in msg
            assert "GTK3" in msg
        else:
            raise AssertionError("Ожидался FileNotFoundError")


def test_frozen_build_has_no_pip_fallback():
    """В frozen-сборке pip-fallback недоступен -> FileNotFoundError."""
    with tempfile.TemporaryDirectory() as td:
        exe = os.path.join(td, "weasyprint.exe")
        sys.frozen = True
        try:
            AppConfig.resolve_weasyprint_cmd(exe_path=exe, module_available=True)
            raise AssertionError("Ожидался FileNotFoundError в frozen-режиме")
        except FileNotFoundError:
            pass
        finally:
            del sys.frozen


def main():
    tests = [
        test_portable_exe_has_priority,
        test_pip_fallback_when_no_exe,
        test_empty_path_uses_default_resolution,
        test_error_when_nothing_available,
        test_frozen_build_has_no_pip_fallback,
    ]
    for t in tests:
        t()
        print(f"[PASS] {t.__name__}: {t.__doc__.strip()}")
    print("\nAll weasyprint resolver tests passed!")


if __name__ == "__main__":
    main()
