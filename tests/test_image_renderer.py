"""Поведенческие тесты экспорта в изображения (core/image_renderer).

WeasyPrint (CLI) и PyMuPDF — внешние зависимости, которых нет в обычном
окружении. Здесь они подменяются заглушками, а проверяется оркестрация
рендера: запуск движка, конвертация страниц, имена выходных файлов,
отмена, ошибка движка и уборка временных файлов.
"""
import os
import sys
import tempfile
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import image_renderer
from src.core.image_renderer import ImageRenderer


# ─── заглушки внешних зависимостей ────────────────────────────────────────────

class _FakePixmap:
    def __init__(self, width=100, height=100):
        self.width = width
        self.height = height
        self.samples = b"\x00" * (width * height * 3)

    def save(self, path):
        with open(path, "wb") as f:
            f.write(b"FAKE-PNG-DATA")


class _FakePage:
    def get_pixmap(self, matrix=None):
        return _FakePixmap()


class _FakePdfDoc:
    def __init__(self, pages):
        self._pages = pages
        self.closed = False

    def __len__(self):
        return self._pages

    def __getitem__(self, index):
        return _FakePage()

    def close(self):
        self.closed = True


class _FakeMatrix:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def _install_fake_fitz(pages=1):
    fake = types.ModuleType("fitz")
    fake.Matrix = _FakeMatrix
    fake.open = lambda path, *a, **k: _FakePdfDoc(pages)
    sys.modules["fitz"] = fake
    return fake


def _install_fake_pil():
    image_mod = types.ModuleType("PIL.Image")
    created = []

    class _FakeImage:
        def save(self, path, fmt=None, **kwargs):
            with open(path, "wb") as f:
                f.write(b"FAKE-JPEG-DATA")

    def frombytes(mode, size, data):
        created.append((mode, tuple(size)))
        return _FakeImage()

    # В Pillow frombytes — функция уровня модуля PIL.Image
    image_mod.frombytes = frombytes
    image_mod.Image = _FakeImage
    pil_mod = types.ModuleType("PIL")
    pil_mod.Image = image_mod
    sys.modules["PIL"] = pil_mod
    sys.modules["PIL.Image"] = image_mod
    return created


def _make_fake_weasyprint(tmpdir, exit_code=0, stderr_text=""):
    """Скрипт, имитирующий weasyprint CLI: argv[1]=html, argv[2]=pdf."""
    script = os.path.join(tmpdir, "fake_weasyprint.py")
    lines = [
        "import sys",
        "if " + repr(stderr_text) + ":",
        "    sys.stderr.write(" + repr(stderr_text) + ")",
        "if " + repr(exit_code) + " == 0:",
        "    open(sys.argv[2], 'wb').write(b'%PDF-1.4 fake')",
        "sys.exit(" + repr(exit_code) + ")",
    ]
    with open(script, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return [sys.executable, script]


class _Recorder:
    """Запоминает пути временных файлов, созданных рендерером."""

    def __init__(self):
        self.paths = []
        self._orig = image_renderer.tempfile.mkstemp

    def __enter__(self):
        def recording(*a, **k):
            fd, path = self._orig(*a, **k)
            self.paths.append(path)
            return fd, path

        image_renderer.tempfile.mkstemp = recording
        return self

    def __exit__(self, *exc):
        image_renderer.tempfile.mkstemp = self._orig
        return False


def _patch_engine(cmd):
    """Подменяет резолвер weasyprint на заданную команду."""
    from src.config import AppConfig

    orig = AppConfig.resolve_weasyprint_cmd
    AppConfig.resolve_weasyprint_cmd = staticmethod(lambda *a, **k: list(cmd))
    return orig


def _restore_engine(orig):
    from src.config import AppConfig

    AppConfig.resolve_weasyprint_cmd = orig


def _patch_render_html():
    """Подменяет рендер HTML на простую заглушку."""
    from src.core.renderer import PDFRenderer

    orig = PDFRenderer.render_html
    PDFRenderer.render_html = lambda self, html, meta, **k: f"<html><body>{html}</body></html>"
    return orig


def _restore_render_html(orig):
    from src.core.renderer import PDFRenderer

    PDFRenderer.render_html = orig


# ─── тесты ────────────────────────────────────────────────────────────────────

def test_render_single_page_png():
    """Одностраничный документ сохраняется ровно по переданному пути."""
    _install_fake_fitz(pages=1)
    with tempfile.TemporaryDirectory() as d:
        cmd = _make_fake_weasyprint(d)
        out = os.path.join(d, "out", "page.png")
        orig = _patch_engine(cmd)
        orig_html = _patch_render_html()
        try:
            r = ImageRenderer()
            count = r.render("<h1>Hi</h1>", {"title": "T"}, out)
        finally:
            _restore_engine(orig)
            _restore_render_html(orig_html)
        assert count == 1, count
        assert os.path.isfile(out), out
        assert os.path.getsize(out) > 0
    print("[PASS] test_render_single_page_png")


def test_render_multi_page_numbering():
    """Многостраничный документ даёт файлы base_1.png, base_2.png и т.д."""
    _install_fake_fitz(pages=3)
    with tempfile.TemporaryDirectory() as d:
        cmd = _make_fake_weasyprint(d)
        out = os.path.join(d, "out", "page.png")
        orig = _patch_engine(cmd)
        orig_html = _patch_render_html()
        try:
            r = ImageRenderer()
            count = r.render("<h1>Hi</h1>", {"title": "T"}, out)
        finally:
            _restore_engine(orig)
            _restore_render_html(orig_html)
        assert count == 3, count
        base = os.path.join(d, "out", "page")
        for i in (1, 2, 3):
            p = f"{base}_{i}.png"
            assert os.path.isfile(p), p
        # Исходный путь при многостраничности не создаётся
        assert not os.path.isfile(out), out
    print("[PASS] test_render_multi_page_numbering")


def test_render_creates_output_directory():
    """Отсутствующий каталог вывода создаётся."""
    _install_fake_fitz(pages=1)
    with tempfile.TemporaryDirectory() as d:
        cmd = _make_fake_weasyprint(d)
        out = os.path.join(d, "a", "b", "c", "img.png")
        orig = _patch_engine(cmd)
        orig_html = _patch_render_html()
        try:
            ImageRenderer().render("<h1>Hi</h1>", {"title": "T"}, out)
        finally:
            _restore_engine(orig)
            _restore_render_html(orig_html)
        assert os.path.isfile(out), out
    print("[PASS] test_render_creates_output_directory")


def test_render_jpg_uses_pillow():
    """Для формата jpg используется Pillow и расширение .jpg."""
    _install_fake_fitz(pages=1)
    created = _install_fake_pil()
    with tempfile.TemporaryDirectory() as d:
        cmd = _make_fake_weasyprint(d)
        out = os.path.join(d, "out", "pic.jpg")
        orig = _patch_engine(cmd)
        orig_html = _patch_render_html()
        try:
            ImageRenderer().render("<h1>Hi</h1>", {"title": "T"}, out, image_format="jpg")
        finally:
            _restore_engine(orig)
            _restore_render_html(orig_html)
        assert os.path.isfile(out), out
        assert created, "Pillow должен был использоваться"
        assert created[0][0] == "RGB", created
    print("[PASS] test_render_jpg_uses_pillow")


def test_render_engine_failure_raises():
    """Ненулевой код возврата движка превращается в RuntimeError с stderr."""
    _install_fake_fitz(pages=1)
    with tempfile.TemporaryDirectory() as d:
        cmd = _make_fake_weasyprint(d, exit_code=3, stderr_text="boom in engine")
        out = os.path.join(d, "out", "page.png")
        orig = _patch_engine(cmd)
        orig_html = _patch_render_html()
        try:
            ImageRenderer().render("<h1>Hi</h1>", {"title": "T"}, out)
        except RuntimeError as e:
            assert "boom in engine" in str(e), str(e)
        else:
            raise AssertionError("Ожидался RuntimeError")
        finally:
            _restore_engine(orig)
            _restore_render_html(orig_html)
    print("[PASS] test_render_engine_failure_raises")


def test_render_cancel_raises():
    """Флаг отмены прерывает рендер и выбрасывает RuntimeError."""
    _install_fake_fitz(pages=1)
    with tempfile.TemporaryDirectory() as d:
        # Движок «думает» секунду, чтобы флаг отмены успел сработать
        script = os.path.join(d, "slow_weasyprint.py")
        with open(script, "w", encoding="utf-8") as f:
            f.write(
                "import sys, time\n"
                "time.sleep(5)\n"
                "open(sys.argv[2], 'wb').write(b'%PDF-1.4 fake')\n"
            )
        cmd = [sys.executable, script]
        out = os.path.join(d, "out", "page.png")
        orig = _patch_engine(cmd)
        orig_html = _patch_render_html()
        try:
            ImageRenderer().render(
                "<h1>Hi</h1>", {"title": "T"}, out, cancel_flag=lambda: True
            )
        except RuntimeError as e:
            assert "отмен" in str(e).lower() or "cancel" in str(e).lower(), str(e)
        else:
            raise AssertionError("Ожидался RuntimeError при отмене")
        finally:
            _restore_engine(orig)
            _restore_render_html(orig_html)
    print("[PASS] test_render_cancel_raises")


def test_render_cleans_temp_files():
    """Временные файлы рендера удаляются даже при ошибке."""
    _install_fake_fitz(pages=1)
    with tempfile.TemporaryDirectory() as d:
        cmd = _make_fake_weasyprint(d, exit_code=3, stderr_text="err")
        out = os.path.join(d, "out", "page.png")
        orig = _patch_engine(cmd)
        orig_html = _patch_render_html()
        try:
            with _Recorder() as rec:
                try:
                    ImageRenderer().render("<h1>Hi</h1>", {"title": "T"}, out)
                except RuntimeError:
                    pass
        finally:
            _restore_engine(orig)
            _restore_render_html(orig_html)
        assert rec.paths, "должны были создаваться временные файлы"
        for p in rec.paths:
            assert not os.path.exists(p), f"временный файл не удалён: {p}"
    print("[PASS] test_render_cleans_temp_files")


def test_render_uses_dpi_for_zoom():
    """Масштаб матрицы зависит от dpi (dpi/72)."""
    _install_fake_fitz(pages=1)
    seen = {}

    class _SpyPixmap(_FakePixmap):
        pass

    class _SpyPage:
        def get_pixmap(self, matrix=None):
            seen["zoom"] = matrix.x
            return _FakePixmap()

    class _SpyDoc(_FakePdfDoc):
        def __getitem__(self, index):
            return _SpyPage()

    fake = sys.modules["fitz"]
    orig_open = fake.open
    fake.open = lambda path, *a, **k: _SpyDoc(1)
    with tempfile.TemporaryDirectory() as d:
        cmd = _make_fake_weasyprint(d)
        out = os.path.join(d, "out", "page.png")
        orig = _patch_engine(cmd)
        orig_html = _patch_render_html()
        try:
            ImageRenderer().render("<h1>Hi</h1>", {"title": "T"}, out, dpi=144)
        finally:
            _restore_engine(orig)
            _restore_render_html(orig_html)
            fake.open = orig_open
        assert abs(seen["zoom"] - 2.0) < 1e-6, seen
    print("[PASS] test_render_uses_dpi_for_zoom")


def main():
    tests = [
        test_render_single_page_png,
        test_render_multi_page_numbering,
        test_render_creates_output_directory,
        test_render_jpg_uses_pillow,
        test_render_engine_failure_raises,
        test_render_cancel_raises,
        test_render_cleans_temp_files,
        test_render_uses_dpi_for_zoom,
    ]
    for t in tests:
        t()
    print("\nAll image renderer tests passed!")


if __name__ == "__main__":
    main()
