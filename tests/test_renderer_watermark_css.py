"""Тест проброса watermark_css в HTML через шаблон (PLAN-004/TASK-004).

Проверяет, что PDFRenderer.render_html вставляет пользовательский CSS
watermark ПОСЛЕДНИМ блоком <style> (приоритет над встроенным .watermark).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from jinja2 import Environment, FileSystemLoader  # noqa: F401
    HAS_JINJA = True
except ImportError:
    HAS_JINJA = False


def main():
    if not HAS_JINJA:
        print("[SKIP] jinja2 не установлен — тест рендеринга watermark_css пропущен")
        return

    from src.core.renderer import PDFRenderer

    template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')
    renderer = PDFRenderer(template_dir, "")

    wm_css = ".watermark { color: rgba(255, 0, 0, 0.5); font-size: 99pt; }"
    html = renderer.render_html(
        "<p>Body</p>", {"title": "T"},
        watermark="DRAFT", watermark_css=wm_css,
    )

    assert wm_css in html, "watermark_css не попал в отрендеренный HTML"
    # CSS должен идти после базового блока <style> с встроенным .watermark
    idx_base = html.find(".watermark {")
    idx_custom = html.find(wm_css)
    assert idx_custom > idx_base, "пользовательский CSS должен идти последним (приоритет)"
    assert html.count("<style>") >= 2, html.count("<style>")
    # Пользовательский блок — самый последний <style> в документе
    assert html.rindex("<style>") < idx_custom, "блок watermark_css должен быть последним <style>"

    # Без watermark_css — последнего блока нет (обратная совместимость)
    html_plain = renderer.render_html("<p>Body</p>", {"title": "T"}, watermark="DRAFT")
    assert wm_css not in html_plain
    assert html_plain.count("<style>") == html.count("<style>") - 1

    print("[PASS] test_renderer_watermark_css: CSS проброшен и имеет приоритет (2 проверки)")
    print("\nAll renderer watermark tests passed!")


if __name__ == "__main__":
    main()
