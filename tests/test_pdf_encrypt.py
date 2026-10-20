"""Тесты pdf_encrypt (PLAN-005/TASK-005).

encrypt_pdf обязан возвращать False (а не бросать исключение) при любой
ошибке: отсутствующий файл, отсутствие pypdf, нечитаемый PDF.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.pdf_encrypt import encrypt_pdf


def test_missing_file_returns_false():
    """Несуществующий файл → False без исключения."""
    assert encrypt_pdf("nonexistent_file_12345.pdf", "pw") is False
    print("[PASS] test_missing_file_returns_false")


def test_non_pdf_file_returns_false():
    """Не-PDF содержимое → False (ошибка чтения изолирована)."""
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "not_a_pdf.pdf")
        with open(path, "w", encoding="utf-8") as f:
            f.write("это точно не PDF")
        assert encrypt_pdf(path, "pw") is False
    print("[PASS] test_non_pdf_file_returns_false")


def test_directory_path_returns_false():
    """Путь к каталогу → False без исключения."""
    with tempfile.TemporaryDirectory() as d:
        assert encrypt_pdf(d, "pw") is False
    print("[PASS] test_directory_path_returns_false")


def test_output_path_variant_degrades_safely():
    """Явный output_path также обрабатывается безопасно при плохом входе."""
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "in.pdf")
        with open(src, "w", encoding="utf-8") as f:
            f.write("bad")
        out = os.path.join(d, "out.pdf")
        result = encrypt_pdf(src, "pw", out)
        assert result is False
        assert not os.path.exists(out), "При ошибке выходной файл создаваться не должен"
    print("[PASS] test_output_path_variant_degrades_safely")


def main():
    tests = [
        test_missing_file_returns_false,
        test_non_pdf_file_returns_false,
        test_directory_path_returns_false,
        test_output_path_variant_degrades_safely,
    ]
    for t in tests:
        t()
    print("\nAll pdf encrypt tests passed!")


if __name__ == "__main__":
    main()
