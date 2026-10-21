"""Тест синхронизации зависимостей (PLAN-006/TASK-006).

Проверяет, что requirements.txt и pyproject.toml объявляют один и тот же
набор сторонних библиотек (без учёта версий, регистра и extras) и что
реально импортируемые в коде библиотеки задекларированы.
"""
import ast
import os
import re
import sys

try:
    import tomllib
except ImportError:  # Python < 3.11
    tomllib = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

REQUIREMENTS = os.path.join(ROOT, "requirements.txt")
PYPROJECT = os.path.join(ROOT, "pyproject.toml")

# Имена пакетов, чьё import-имя отличается от имени распределения
IMPORT_TO_PACKAGE = {
    "docx": "python-docx",
    "htmldocx": "htmldocx",
    "ebooklib": "ebooklib",
    "pptx": "python-pptx",
    "fitz": "pymupdf",
    "PIL": "pillow",
    "pypdf": "pypdf",
    "pytesseract": "pytesseract",
    "pyttsx3": "pyttsx3",
    "speech_recognition": "speechrecognition",
    "PyQt6": "pyqt6",
    "jinja2": "jinja2",
    "markdown": "markdown",
    "pygments": "pygments",
    "markupsafe": "markupsafe",
    "pymdownx": "pymdown-extensions",
    "weasyprint": "weasyprint",
    "pyinstaller": "pyinstaller",
}

# Импорты, которые НЕ являются внешними зависимостями
STDLIB_OR_LOCAL = {
    "argparse", "ast", "base64", "collections", "csv", "dataclasses", "datetime",
    "difflib", "enum", "functools", "hashlib", "html", "importlib", "json", "logging",
    "math", "mimetypes", "os", "pathlib", "random", "re", "shutil", "socket",
    "subprocess", "sys", "tempfile", "threading", "time", "traceback", "typing",
    "urllib", "winreg", "zlib", "src", "brain", "project_name",
}


def _norm(name: str) -> str:
    """Нормализация имени пакета: нижний регистр, без extras и операторов версии."""
    name = name.split("[")[0]
    name = re.split(r"[<>=!~; ]", name)[0]
    return name.strip().lower().replace("_", "-")


def parse_requirements() -> set:
    """Множество нормализованных имён из requirements.txt."""
    packages = set()
    with open(REQUIREMENTS, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            packages.add(_norm(line))
    return packages


def parse_pyproject() -> set:
    """Множество нормализованных имён всех зависимостей pyproject.toml (deps + extras)."""
    project = _load_pyproject()
    packages = set()
    for dep in project.get("dependencies", []):
        packages.add(_norm(dep))
    for deps in project.get("optional-dependencies", {}).values():
        for dep in deps:
            packages.add(_norm(dep))
    return packages


def _load_pyproject() -> dict:
    """Читает pyproject.toml через tomllib (py3.11+) или минимальный построчный парсер."""
    if tomllib is not None:
        with open(PYPROJECT, "rb") as f:
            return tomllib.load(f)["project"]

    # Fallback для Python 3.10: извлекаем строковые значения из массивов,
    # в том числе многострочных (dependencies = [ ... ]).
    with open(PYPROJECT, encoding="utf-8") as f:
        text = f.read()
    project: dict = {"dependencies": [], "optional-dependencies": {}}
    section = None
    current_extra = None
    array_key = None  # ключ массива, который сейчас читаем (многострочный)
    for raw in text.splitlines():
        line = raw.strip()
        if array_key is None:
            # Вне массива: смена секции
            if line.startswith("[project.optional-dependencies]"):
                section = "extras"
                continue
            if line.startswith("[project]"):
                section = "project"
                continue
            if line.startswith("[") and not line.startswith("[project"):
                section = None
                continue
            if line.startswith("name") and section == "project":
                project["name"] = line.split("=", 1)[1].strip().strip('"')
            # Старт массива:  key = [ ...   (может закрыться на этой же строке)
            m = re.match(r"^([A-Za-z0-9_.-]+)\s*=\s*\[(.*)$", line)
            if m:
                array_key = m.group(1)
                if section == "extras":
                    current_extra = array_key
                    project["optional-dependencies"].setdefault(current_extra, [])
                rest = m.group(2)
                _collect_array_items(rest, section, current_extra, project)
                if "]" in rest:
                    array_key = None
                    current_extra = None
                continue
            continue
        # Внутри массива: собираем элементы до закрывающей ]
        _collect_array_items(line, section, current_extra, project)
        if "]" in line:
            array_key = None
            current_extra = None
    return project


def _collect_array_items(fragment: str, section, current_extra, project) -> None:
    """Добавляет строковые элементы из фрагмента строки массива в project."""
    for item in re.findall(r'"([^"]+)"', fragment):
        if section == "project" and not current_extra:
            project["dependencies"].append(item)
        elif section == "extras" and current_extra:
            project["optional-dependencies"].setdefault(current_extra, []).append(item)


def collect_imports() -> set:
    """Множество внешних import-имён, встречающихся в src/ и main.py (AST)."""
    roots = [os.path.join(ROOT, "src"), os.path.join(ROOT, "main.py")]
    files = []
    for root in roots:
        if os.path.isfile(root):
            files.append(root)
        else:
            for dirpath, _dirs, filenames in os.walk(root):
                if "__pycache__" in dirpath:
                    continue
                files.extend(
                    os.path.join(dirpath, fn) for fn in filenames if fn.endswith(".py")
                )

    found = set()
    for path in files:
        try:
            with open(path, "rb") as f:
                tree = ast.parse(f.read(), path)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    found.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.level == 0:
                    found.add(node.module.split(".")[0])
    return found


def test_requirements_and_pyproject_agree():
    """Множества зависимостей совпадают (кроме dev/платформенных из pyproject-only extras)."""
    req = parse_requirements()
    py = parse_pyproject()
    # pyaudio — только в extra speech (нужен для микрофона); pytest — dev-зависимость.
    # Оба объявляются лишь в pyproject.toml, в requirements.txt их нет намеренно.
    allowed_py_only = {"pyaudio", "pytest"}
    req_only = req - py
    py_only = py - req
    assert not req_only, f"Есть в requirements.txt, но нет в pyproject.toml: {sorted(req_only)}"
    assert py_only <= allowed_py_only, (
        f"Есть в pyproject.toml, но нет в requirements.txt: {sorted(py_only - allowed_py_only)}"
    )
    print("[PASS] test_requirements_and_pyproject_agree")


def test_speech_recognition_declared():
    """SpeechRecognition используется в коде и объявлен в обоих файлах (BUG из аудита)."""
    req = parse_requirements()
    py = parse_pyproject()
    assert "speechrecognition" in req, "SpeechRecognition отсутствует в requirements.txt"
    assert "speechrecognition" in py, "SpeechRecognition отсутствует в pyproject.toml"
    print("[PASS] test_speech_recognition_declared")


def test_used_imports_are_declared():
    """Каждая внешняя библиотека, импортируемая в коде, присутствует в requirements.txt."""
    req = parse_requirements()
    used = collect_imports()

    missing = []
    for mod in sorted(used):
        if mod in STDLIB_OR_LOCAL:
            continue
        package = IMPORT_TO_PACKAGE.get(mod, mod).lower().replace("_", "-")
        if package not in req:
            missing.append(f"{mod} -> {package}")

    assert not missing, "Используются в коде, но не объявлены: " + "; ".join(missing)
    print(f"[PASS] test_used_imports_are_declared: проверено {len(used)} импортов")


def test_no_exact_pins_in_requirements():
    """requirements.txt использует диапазоны (>=), а не жёсткие пины (==) — единый стиль с pyproject."""
    pinned = []
    with open(REQUIREMENTS, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "==" in line:
                pinned.append(line)
    assert not pinned, f"Найдены жёсткие пины (==): {pinned}"
    print("[PASS] test_no_exact_pins_in_requirements")


def test_pyproject_parses():
    """pyproject.toml корректен и содержит базовые зависимости + extras."""
    project = _load_pyproject()
    assert project["name"] == "markdown-to-pdf-converter"
    assert "markdown" in {_norm(d) for d in project["dependencies"]}
    extras = project.get("optional-dependencies", {})
    for required in ("gui", "pdf", "docx", "epub", "pptx", "images", "tts", "ocr", "speech", "all"):
        assert required in extras, f"Отсутствует extra '{required}'"
    print("[PASS] test_pyproject_parses")


def test_pyproject_fallback_parser_py310():
    """Резервный парсер (без tomllib, py3.10) читает многострочные массивы.

    Регрессия CI: на Python 3.10 tomllib недоступен, и старый построчный
    парсер не видел многострочный dependencies = [ ... ] → 0 базовых
    зависимостей → падение test_dependency_sync. Проверяем оба пути.
    """
    saved = globals().get("tomllib")
    try:
        globals()["tomllib"] = None
        project = _load_pyproject()
        deps = {_norm(d) for d in project["dependencies"]}
        assert "markdown" in deps, f"fallback не собрал dependencies: {deps}"
        assert "pypdf" in deps, f"fallback не собрал dependencies: {deps}"
        extras = project.get("optional-dependencies", {})
        assert extras.get("gui") == ["PyQt6>=6.5.0"], extras.get("gui")
        assert "python-docx>=1.1" in extras.get("docx", []), extras.get("docx")
    finally:
        globals()["tomllib"] = saved
    print("[PASS] test_pyproject_fallback_parser_py310")


def main():
    tests = [
        test_pyproject_parses,
        test_pyproject_fallback_parser_py310,
        test_requirements_and_pyproject_agree,
        test_speech_recognition_declared,
        test_used_imports_are_declared,
        test_no_exact_pins_in_requirements,
    ]
    for t in tests:
        t()
    print("\nAll dependency sync tests passed!")


if __name__ == "__main__":
    main()
