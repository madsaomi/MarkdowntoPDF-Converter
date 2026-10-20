"""Тесты конфигурации релиза (PLAN-009 / веха M4).

Проверяет без внешних зависимостей (PyYAML не нужен):
1. Версия `src/__version__.py` совпадает с `installer.iss` (`AppVersion`).
2. Существует релизный workflow `.github/workflows/release.yml` с нужными триггерами и шагами.
3. Существует скрипт `scripts/build_release.ps1`.
4. README ссылается на актуальные workflow/тесты (бейдж + число тест-файлов).
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

VERSION_PY = os.path.join(ROOT, "src", "__version__.py")
INSTALLER_ISS = os.path.join(ROOT, "installer.iss")
RELEASE_YML = os.path.join(ROOT, ".github", "workflows", "release.yml")
BUILD_PS1 = os.path.join(ROOT, "scripts", "build_release.ps1")
README = os.path.join(ROOT, "README.md")


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _project_version() -> str:
    m = re.search(r'__version__\s*=\s*"([^"]+)"', _read(VERSION_PY))
    assert m, "Не найдена __version__ в src/__version__.py"
    return m.group(1)


def test_version_matches_installer():
    """Версия проекта совпадает с AppVersion в installer.iss (синхронизируется build.py)."""
    version = _project_version()
    m = re.search(r"AppVersion=(\S+)", _read(INSTALLER_ISS))
    assert m, "Не найден AppVersion в installer.iss"
    assert m.group(1) == version, (
        f"Рассинхрон версий: __version__={version}, installer AppVersion={m.group(1)}"
    )
    print(f"[PASS] test_version_matches_installer ({version})")


def test_release_workflow_exists_and_valid():
    """Релизный workflow существует, триггерится по тегам и собирает .exe + инсталлятор."""
    assert os.path.isfile(RELEASE_YML), "Нет .github/workflows/release.yml"
    src = _read(RELEASE_YML)

    # Триггер по тегам
    assert "tags:" in src, "Нет триггера tags:"
    assert re.search(r"['\"]?v\*['\"]?", src), "Триггер тега должен быть 'v*'"

    # Ключевые шаги
    checks = {
        "runs-on windows": "windows-latest" in src,
        "тесты перед сборкой": "run_all.py" in src,
        "PyInstaller": "build.py" in src,
        "Inno Setup": "installer.iss" in src,
        "публикация артефактов": "upload-artifact" in src,
        "GitHub Release": "action-gh-release" in src,
    }
    missing = [name for name, ok in checks.items() if not ok]
    assert not missing, f"В release.yml отсутствуют шаги: {missing}"

    # Базовая проверка структуры YAML (отступы, отсутствие табов)
    assert "\t" not in src, "release.yml содержит табы — невалидный YAML"
    print("[PASS] test_release_workflow_exists_and_valid")


def test_release_workflow_referenced_files_exist():
    """Файлы, на которые ссылается workflow/скрипт, реально существуют."""
    for rel in ("build.py", "installer.iss", "requirements.txt", "tests/run_all.py"):
        assert os.path.isfile(os.path.join(ROOT, rel)), f"Отсутствует {rel} (упомянут в release)"
    print("[PASS] test_release_workflow_referenced_files_exist")


def test_build_script_exists():
    """Локальный скрипт сборки существует и вызывает build.py."""
    assert os.path.isfile(BUILD_PS1), "Нет scripts/build_release.ps1"
    src = _read(BUILD_PS1)
    assert "build.py" in src, "Скрипт не вызывает build.py"
    assert "installer.iss" in src, "Скрипт не собирает инсталлятор"
    assert "__version__" in src, "Скрипт не читает версию"
    print("[PASS] test_build_script_exists")


def test_build_script_has_utf8_bom():
    """Скрипт должен иметь UTF-8 BOM, иначе PowerShell 5.1 декодирует кириллицу
    как ANSI и ломает строковые литералы (проверено: без BOM — 5 ложных ошибок парсинга)."""
    with open(BUILD_PS1, "rb") as f:
        head = f.read(3)
    assert head == b"\xef\xbb\xbf", (
        "scripts/build_release.ps1 без UTF-8 BOM — PowerShell 5.1 не распарсит кириллицу. "
        "Сохрани файл в UTF-8 with BOM."
    )
    print("[PASS] test_build_script_has_utf8_bom")


def test_readme_updated():
    """README: актуальный бейдж CI, упоминание релиза и корректное число тест-файлов."""
    src = _read(README)

    # Корректный владелец в бейдже (не плейсхолдер)
    assert "github.com/madsaomi/MarkdowntoPDF-Converter/actions" in src, "Бейдж CI указывает на плейсхолдер"
    assert "user/markdown-to-pdf-converter" not in src, "Остался плейсхолдер-бейдж"

    # Релизный раздел
    assert "scripts/build_release.ps1" in src, "README не упоминает скрипт сборки"
    assert "release.yml" in src, "README не ссылается на релизный workflow"

    # Число тест-файлов совпадает с реальностью — считаем по списку в run_all.py
    runner = _read(os.path.join(ROOT, "tests", "run_all.py"))
    real_count = len(re.findall(r'"test_[^"]+\.py"', runner))
    assert re.search(rf"{real_count} test files", src), (
        f"README не указывает актуальное число тестов ({real_count})"
    )
    print(f"[PASS] test_readme_updated ({real_count} тест-файлов)")


def main():
    tests = [
        test_version_matches_installer,
        test_release_workflow_exists_and_valid,
        test_release_workflow_referenced_files_exist,
        test_build_script_exists,
        test_build_script_has_utf8_bom,
        test_readme_updated,
    ]
    for t in tests:
        t()
    print("\nAll release-config tests passed!")


if __name__ == "__main__":
    main()
