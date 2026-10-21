"""Поведенческие тесты WikiLinkProcessor и GraphBuilder (core/wikilinks).

Проверяет резолв ссылок, извлечение тегов и ссылок, трансclusions, построение графа.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.wikilinks import WikiLinkProcessor, GraphBuilder


def test_extract_links_with_display():
    """extract_links извлекает целевой файл и отображаемый текст."""
    wp = WikiLinkProcessor()
    links = wp.extract_links("См. [[Note One]] и [[Другой|альтернативное название]] тут")
    assert len(links) == 2
    assert links[0] == {"target": "Note One", "display": "Note One"}
    assert links[1] == {"target": "Другой", "display": "альтернативное название"}
    print("[PASS] test_extract_links_with_display")


def test_extract_tags():
    """extract_tags находит хештеги, игнорирует дубли."""
    wp = WikiLinkProcessor()
    tags = wp.extract_tags("Текст #проект и #todo #проект с #класс/доп")
    assert "проект" in tags
    assert "todo" in tags
    assert "класс/доп" in tags
    assert tags.count("проект") == 1  # уникальные
    print("[PASS] test_extract_tags")


def test_resolve_links_to_existing_files():
    """resolve_links превращает [[wikilink]] в Markdown-ссылку на найденный .md файл."""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "Target.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write("# Target\n")
        wp = WikiLinkProcessor(base_dir=d)
        out = wp.resolve_links("Смотри [[Target]] и [[Target|целевая страница]]")
        assert "[Target](Target.md)" in out or "[Target](target.md)" in out.lower() or "Target.md" in out
        assert "[целевая страница](" in out
    print("[PASS] test_resolve_links_to_existing_files")


def test_resolve_links_fallback_to_md():
    """Если файл не найден — ссылка ведёт на target.md."""
    with tempfile.TemporaryDirectory() as d:
        wp = WikiLinkProcessor(base_dir=d)
        out = wp.resolve_links("Смотри [[Missing]]")
        assert "[Missing](Missing.md)" in out
    print("[PASS] test_resolve_links_fallback_to_md")


def test_process_transclusions_includes_and_strips_front_matter():
    """process_transclusions вставляет содержимое файла, убирая front matter."""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "snippet.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write("---\ntitle: test\n---\n\nСодержимое сниппета\n")
        wp = WikiLinkProcessor(base_dir=d)
        out = wp.process_transclusions("Перед\n{{include:snippet}}\nПосле")
        assert "Содержимое сниппета" in out
        assert "title: test" not in out
        assert "---" not in out
    print("[PASS] test_process_transclusions_includes_and_strips_front_matter")


def test_process_transclusions_missing_file():
    """При отсутствии файла возвращается сообщение об ошибке."""
    with tempfile.TemporaryDirectory() as d:
        wp = WikiLinkProcessor(base_dir=d)
        out = wp.process_transclusions("{{include:missing.md}}")
        assert "File not found" in out
    print("[PASS] test_process_transclusions_missing_file")


def test_graph_builder_builds_nodes_and_edges():
    """GraphBuilder строит узлы по .md файлам и рёбра по wikilinks."""
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "A.md"), "w", encoding="utf-8") as f:
            f.write("# A\n\nСсылка на [[B]]")
        with open(os.path.join(d, "B.md"), "w", encoding="utf-8") as f:
            f.write("# B\n")
        with open(os.path.join(d, "C.md"), "w", encoding="utf-8") as f:
            f.write("# C\n")
        gb = GraphBuilder(base_dir=d)
        graph = gb.build_graph()
        ids = {n["id"] for n in graph["nodes"]}
        assert {"A", "B", "C"} == ids
        assert len(graph["edges"]) == 1
        assert graph["edges"][0] == {"source": "A", "target": "B"}
        # Размер узлов увеличивается при наличии ссылок
        sizes = {n["id"]: n["size"] for n in graph["nodes"]}
        assert sizes["A"] >= 2
        assert sizes["B"] >= 2
    print("[PASS] test_graph_builder_builds_nodes_and_edges")


def test_graph_builder_empty_and_html():
    """Пустая директория и build_graph_html."""
    with tempfile.TemporaryDirectory() as d:
        gb = GraphBuilder(base_dir=d)
        graph = gb.build_graph()
        assert graph == {"nodes": [], "edges": []}
        html = gb.build_graph_html()
        assert "Нет файлов" in html
    print("[PASS] test_graph_builder_empty_and_html")


def main():
    tests = [
        test_extract_links_with_display,
        test_extract_tags,
        test_resolve_links_to_existing_files,
        test_resolve_links_fallback_to_md,
        test_process_transclusions_includes_and_strips_front_matter,
        test_process_transclusions_missing_file,
        test_graph_builder_builds_nodes_and_edges,
        test_graph_builder_empty_and_html,
    ]
    for t in tests:
        t()
    print("\nAll wikilinks tests passed!")


if __name__ == "__main__":
    main()
