"""Вербатим-переносчик классов/методов между модулями (инструмент декомпозиции).

Копирует указанные классы (или методы класса) ВЕРБАТИМ — по диапазонам строк
из AST, поэтому содержимое гарантированно не меняется. Используется при
разбиении крупных модулей (PLAN-010, PLAN-011 и далее).

Использование:
    python scripts/extract_code.py class <src.py> <out.py> <ClassName> [<ClassName> ...]
    python scripts/extract_code.py method <src.py> <out.py> <Class> <meth> [<meth> ...]

Для `class`: переносит классы целиком и удаляет их из src.
Для `method`: переносит методы в новый класс-заглушку и удаляет их из src.

Печатает границы перенесённого — для сверки.
"""
import ast
import os
import sys


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _bodies(tree):
    """{name: node} для верхнеуровневых классов и функций."""
    out = {}
    for n in tree.body:
        if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            out[n.name] = n
    return out


def move_classes(src_path, out_path, names):
    src = _read(src_path)
    lines = src.splitlines(keepends=True)
    bodies = _bodies(ast.parse(src))

    missing = [n for n in names if n not in bodies]
    if missing:
        raise SystemExit(f"Не найдены классы: {missing}")

    chunks = []
    spans = []
    for n in names:
        node = bodies[n]
        a, b = node.lineno, node.end_lineno
        chunks.append("".join(lines[a - 1:b]))
        spans.append((n, a, b))

    header = (
        '"""Автоматически перенесено инструментом scripts/extract_code.py.\n\n'
        f"Источник: {src_path}. Тела перенесены вербатим (без изменений).\n"
        '"""\n\n'
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header)
        for c in chunks:
            f.write(c)
            if not c.endswith("\n\n"):
                f.write("\n\n")

    for n, a, b in sorted(spans, key=lambda s: s[1], reverse=True):
        del lines[a - 1:b]

    with open(src_path, "w", encoding="utf-8") as f:
        f.write("".join(lines))

    for n, a, b in spans:
        print(f"перенесён class {n}: строки {a}-{b}")


def move_methods(src_path, out_path, cls_name, names):
    """Переносит методы класса в новый класс-заглушку (вербатим)."""
    src = _read(src_path)
    lines = src.splitlines(keepends=True)
    tree = ast.parse(src)

    cls = None
    for n in tree.body:
        if isinstance(n, ast.ClassDef) and n.name == cls_name:
            cls = n
            break
    if cls is None:
        raise SystemExit(f"Класс не найден: {cls_name}")

    methods = {
        m.name: m
        for m in cls.body
        if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    missing = [n for n in names if n not in methods]
    if missing:
        raise SystemExit(f"Не найдены методы: {missing}")

    chunks = []
    spans = []
    order = [m.name for m in cls.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for n in order:
        if n not in names:
            continue
        node = methods[n]
        a, b = node.lineno, node.end_lineno
        chunks.append("".join(lines[a - 1:b]))
        spans.append((n, a, b))

    header = (
        '"""Автоматически перенесено инструментом scripts/extract_code.py.\n\n'
        f"Источник: {src_path}, класс {cls_name}. Тела перенесены вербатим.\n"
        '"""\n\n\n'
        f"class {out_class_name(out_path)}:\n"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header)
        for c in chunks:
            f.write(c)
            if not c.endswith("\n\n"):
                f.write("\n")

    for n, a, b in sorted(spans, key=lambda s: s[1], reverse=True):
        del lines[a - 1:b]

    with open(src_path, "w", encoding="utf-8") as f:
        f.write("".join(lines))

    for n, a, b in spans:
        print(f"перенесён method {n}: строки {a}-{b}")


def out_class_name(out_path):
    """Имя класса из имени файла: editor_tools.py -> EditorToolsMixin."""
    base = os.path.splitext(os.path.basename(out_path))[0]
    return "".join(part.capitalize() for part in base.split("_")) + "Mixin"


def main():
    mode = sys.argv[1]
    if mode == "class":
        src_path, out_path = sys.argv[2], sys.argv[3]
        names = sys.argv[4:]
        move_classes(src_path, out_path, names)
    elif mode == "method":
        src_path, out_path, cls_name = sys.argv[2], sys.argv[3], sys.argv[4]
        names = sys.argv[5:]
        move_methods(src_path, out_path, cls_name, names)
    else:
        raise SystemExit("Режимы: class | method")


if __name__ == "__main__":
    main()
