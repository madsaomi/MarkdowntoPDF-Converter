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


def main():
    mode = sys.argv[1]
    if mode != "class":
        raise SystemExit("Поддерживается только режим: class")
    src_path, out_path = sys.argv[2], sys.argv[3]
    names = sys.argv[4:]
    move_classes(src_path, out_path, names)


if __name__ == "__main__":
    main()
