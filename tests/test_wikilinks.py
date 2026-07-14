import os
import sys
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.wikilinks import WikiLinkProcessor, GraphBuilder


def test_extract_links():
    proc = WikiLinkProcessor()
    links = proc.extract_links("See [[note]] and [[page|display]]")
    assert len(links) == 2
    assert links[0]['target'] == 'note'
    assert links[1]['target'] == 'page'
    assert links[1]['display'] == 'display'
    print("[PASS] test_extract_links")


def test_resolve_links_no_file():
    proc = WikiLinkProcessor()
    result = proc.resolve_links("See [[missing]]")
    assert "missing.md" in result
    print("[PASS] test_resolve_links_no_file")


def test_extract_tags():
    proc = WikiLinkProcessor()
    tags = proc.extract_tags("#hello #world embedded")
    assert "hello" in tags
    assert "world" in tags
    print("[PASS] test_extract_tags")


def test_resolve_links_with_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        md_path = os.path.join(tmpdir, "test.md")
        with open(md_path, "w") as f:
            f.write("content")
        proc = WikiLinkProcessor(base_dir=tmpdir)
        result = proc.resolve_links("[[test.md]]")
        assert "test.md" in result
        print("[PASS] test_resolve_links_with_file")


def test_transclusion():
    with tempfile.TemporaryDirectory() as tmpdir:
        inc_path = os.path.join(tmpdir, "include.md")
        with open(inc_path, "w") as f:
            f.write("Included content")
        proc = WikiLinkProcessor(base_dir=tmpdir)
        result = proc.process_transclusions("{{include:include.md}}")
        assert "Included content" in result
        print("[PASS] test_transclusion")


def test_transclusion_not_found():
    proc = WikiLinkProcessor()
    result = proc.process_transclusions("{{include:nonexistent.md}}")
    assert "not found" in result
    print("[PASS] test_transclusion_not_found")


def test_graph_builder_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        gb = GraphBuilder(base_dir=tmpdir)
        graph = gb.build_graph()
        assert 'nodes' in graph
        assert 'edges' in graph
        print("[PASS] test_graph_builder_empty")


def test_graph_builder_with_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        a_path = os.path.join(tmpdir, "a.md")
        b_path = os.path.join(tmpdir, "b.md")
        with open(a_path, "w") as f:
            f.write("Link to [[b]]")
        with open(b_path, "w") as f:
            f.write("Link to [[a]]")
        gb = GraphBuilder(base_dir=tmpdir)
        graph = gb.build_graph()
        assert len(graph['nodes']) >= 2
        assert len(graph['edges']) >= 1
        print(f"[PASS] test_graph_builder_with_files: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")


if __name__ == '__main__':
    test_extract_links()
    test_resolve_links_no_file()
    test_extract_tags()
    test_resolve_links_with_file()
    test_transclusion()
    test_transclusion_not_found()
    test_graph_builder_empty()
    test_graph_builder_with_files()
    print("\nAll wikilinks tests passed!")
