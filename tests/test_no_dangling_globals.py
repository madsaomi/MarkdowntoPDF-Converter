"""Статическая проверка: «висячие» имена (использованы, но не определены).

Ловит класс дефектов, который не видят `py_compile` и Qt-стаб: имя читается
как глобал (базис атрибута или само по себе), но нигде не импортировано и не
определено — типичная поломка после вербатим-переноса кода между модулями
(см. BUG_003, BUG_004).

Для каждого .py в `src/` строим таблицу определённых имён (импорты, присваивания,
def/class, аргументы, comprehension-переменные, walrus, except-as) с учётом
областей видимости и ищем Load-имена, которых нет ни в локальной, ни в
модульной области, ни во встроенных.

Ограничения (сознательные, чтобы не было ложных срабатываний):
- имена из `globals()`/`locals()`/`eval`/`exec` не анализируются динамически;
- `__all__` и звёздочные импорты трактуются как «всё разрешено» для модуля.
"""
import ast
import builtins
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

BUILTINS = set(dir(builtins))
# Дундер-атрибуты модуля, которые интерпретатор подставляет автоматически.
MODULE_MAGIC = {"__file__", "__name__", "__doc__", "__package__", "__spec__",
                "__loader__", "__builtins__", "__dict__"}


class _Scope:
    def __init__(self, parent=None, kind="function"):
        self.parent = parent
        self.kind = kind
        self.defined = set()
        self.loads = {}  # name -> lineno


class _Collector(ast.NodeVisitor):
    """Собирает для каждого модуля определённые имена и Load-имена по областям."""

    def __init__(self):
        self.module_scope = _Scope(None, "module")
        self.scopes = [self.module_scope]
        self.all_scopes = [self.module_scope]
        self.star_import = False

    @property
    def cur(self):
        return self.scopes[-1]

    def _push(self, scope):
        self.scopes.append(scope)
        self.all_scopes.append(scope)

    def _define(self, name):
        self.cur.defined.add(name)

    def _load(self, name, lineno):
        self.cur.loads.setdefault(name, lineno)

    # --- области видимости ---
    def visit_FunctionDef(self, node):
        self._define(node.name)
        args = node.args
        scope = _Scope(self.cur, "function")
        for a in list(args.posonlyargs) + list(args.args) + list(args.kwonlyargs):
            scope.defined.add(a.arg)
        if args.vararg:
            scope.defined.add(args.vararg.arg)
        if args.kwarg:
            scope.defined.add(args.kwarg.arg)
        self._push(scope)
        for child in node.body:
            self.visit(child)
        self.scopes.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Lambda(self, node):
        scope = _Scope(self.cur, "function")
        args = node.args
        for a in list(args.posonlyargs) + list(args.args) + list(args.kwonlyargs):
            scope.defined.add(a.arg)
        if args.vararg:
            scope.defined.add(args.vararg.arg)
        if args.kwarg:
            scope.defined.add(args.kwarg.arg)
        self._push(scope)
        self.visit(node.body)
        self.scopes.pop()

    def visit_ClassDef(self, node):
        self._define(node.name)
        scope = _Scope(self.cur, "class")
        self._push(scope)
        for child in node.body:
            self.visit(child)
        self.scopes.pop()

    def visit_Import(self, node):
        for alias in node.names:
            self._define((alias.asname or alias.name.split(".")[0]))

    def visit_ImportFrom(self, node):
        if any(a.name == "*" for a in node.names):
            self.star_import = True
        for alias in node.names:
            if alias.name != "*":
                self._define(alias.asname or alias.name)

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self._define(node.id)
        elif isinstance(node.ctx, ast.Load):
            self._load(node.id, node.lineno)

    def visit_Global(self, node):
        for n in node.names:
            self.module_scope.defined.add(n)

    def visit_Nonlocal(self, node):
        for n in node.names:
            self.cur.defined.add(n)

    def visit_ExceptHandler(self, node):
        if node.name:
            self._define(node.name)
        self.generic_visit(node)

    def visit_comprehension(self, node):
        # цель comprehension видна только внутри самого comprehension;
        # трактуем как локальную переменную текущей области (достаточно, чтобы
        # не было ложных «висячих» для типичных случаев).
        if isinstance(node.target, ast.Name):
            self._define(node.target.id)
        elif isinstance(node.target, (ast.Tuple, ast.List)):
            for elt in ast.walk(node.target):
                if isinstance(elt, ast.Name):
                    self._define(elt.id)
        self.visit(node.iter)
        for cond in node.ifs:
            self.visit(cond)

    def visit_MatchAs(self, node):
        if node.name:
            self._define(node.name)
        self.generic_visit(node)

    def visit_MatchStar(self, node):
        if node.name:
            self._define(node.name)

    def visit_MatchMapping(self, node):
        if node.rest:
            self._define(node.rest)
        self.generic_visit(node)


def _name_in_scope(name, scope):
    s = scope
    while s is not None:
        if name in s.defined:
            return True
        s = s.parent
    return False


def find_dangling_names(path):
    """Возвращает список (name, lineno) — Load-имена, не определённые нигде."""
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), path)

    c = _Collector()
    c.visit(tree)

    if c.star_import:
        return []

    dangling = set()
    for scope in c.all_scopes:
        for name, lineno in scope.loads.items():
            if name in BUILTINS or name in MODULE_MAGIC:
                continue
            if not _name_in_scope(name, scope):
                dangling.add((name, lineno))
    return sorted(dangling, key=lambda x: x[1])


def _iter_source_files():
    """Все .py проекта: src/, scripts/, tests/ и корневые модули."""
    roots = ["src", "scripts", "tests"]
    for name in roots:
        base = os.path.join(ROOT, name)
        if not os.path.isdir(base):
            continue
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for fn in files:
                if fn.endswith(".py"):
                    yield os.path.join(root, fn)
    for fn in os.listdir(ROOT):
        p = os.path.join(ROOT, fn)
        if fn.endswith(".py") and os.path.isfile(p):
            yield p


def test_no_dangling_globals_in_project():
    """Ни один модуль проекта (src/, scripts/, tests/, корень) не использует
    неопределённые имена."""
    problems = []
    checked = 0
    for path in sorted(set(_iter_source_files())):
        checked += 1
        for name, lineno in find_dangling_names(path):
            rel = os.path.relpath(path, ROOT)
            problems.append(f"{rel}:{lineno}: '{name}'")
    assert not problems, (
        "Найдены «висячие» имена (использованы, но не импортированы/не определены):\n  "
        + "\n  ".join(problems)
    )
    print(f"[PASS] test_no_dangling_globals_in_project ({checked} файлов)")


def test_scanner_detects_known_pattern():
    """Само-проверка сканера: искусственный модуль с висячим именем ловится."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        bad = os.path.join(tmp, "bad_mod.py")
        with open(bad, "w", encoding="utf-8") as f:
            f.write("def f():\n    return missing_module.do()\n")
        found = find_dangling_names(bad)
        assert any(n == "missing_module" for n, _ in found), found

        good = os.path.join(tmp, "good_mod.py")
        with open(good, "w", encoding="utf-8") as f:
            f.write(
                "import os\n\n\n"
                "def f(xs):\n"
                "    total = 0\n"
                "    for x in xs:\n"
                "        total += x\n"
                "    return total, os.getcwd()\n"
            )
        assert find_dangling_names(good) == [], find_dangling_names(good)
    print("[PASS] test_scanner_detects_known_pattern")


def test_scanner_understands_function_locals():
    """Локальные переменные, аргументы, comprehension и walrus не считаются висячими."""
    import tempfile

    code = (
        "def outer(a):\n"
        "    b = [i * a for i in range(3)]\n"
        "    if (n := sum(b)) > 1:\n"
        "        return [x + n for x in b]\n"
        "    return b\n\n"
        "def using_global():\n"
        "    return helper()\n\n"
        "def helper():\n"
        "    return 1\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "locals_mod.py")
        with open(p, "w", encoding="utf-8") as f:
            f.write(code)
        found = find_dangling_names(p)
        assert found == [], found
    print("[PASS] test_scanner_understands_function_locals")


def main():
    tests = [
        test_scanner_detects_known_pattern,
        test_scanner_understands_function_locals,
        test_no_dangling_globals_in_project,
    ]
    for t in tests:
        t()
    print("\nAll dangling-globals tests passed!")


if __name__ == "__main__":
    main()
