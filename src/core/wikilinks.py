"""Wikilinks, Graph View, and Transclusions support for Markdown."""

import os
import re
import logging
from collections import defaultdict

logger = logging.getLogger("MarkdownToPDF.wikilinks")


class WikiLinkProcessor:
    """Processes [[wikilinks]] in Markdown content."""

    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.getcwd()
        self.link_pattern = re.compile(r'\[\[([^\]|]+?)(?:\|([^\]]+))?\]\]')

    def resolve_links(self, text: str, current_file: str = None) -> str:
        """Replace [[wikilinks]] with actual Markdown links."""
        def replace_link(match):
            target = match.group(1).strip()
            display = match.group(2).strip() if match.group(2) else target

            # Try to find the target file
            target_file = self._find_file(target)
            if target_file:
                rel_path = os.path.relpath(target_file, self.base_dir)
                return f'[{display}]({rel_path})'
            else:
                return f'[{display}]({target}.md)'

        return self.link_pattern.sub(replace_link, text)

    def _find_file(self, name: str) -> str:
        """Find a .md file by name in the workspace."""
        if not self.base_dir or not os.path.exists(self.base_dir):
            return None

        for root, dirs, files in os.walk(self.base_dir):
            for f in files:
                if f.endswith('.md'):
                    stem = os.path.splitext(f)[0]
                    if stem.lower() == name.lower() or f.lower() == name.lower():
                        return os.path.join(root, f)
        return None

    def extract_links(self, text: str) -> list:
        """Extract all wikilinks from text."""
        links = []
        for match in self.link_pattern.finditer(text):
            target = match.group(1).strip()
            display = match.group(2).strip() if match.group(2) else target
            links.append({'target': target, 'display': display})
        return links

    def extract_tags(self, text: str) -> list:
        """Extract #tags from text."""
        return list(set(re.findall(r'(?:^|\s)#([a-zA-Zа-яА-ЯёЁ][\wа-яА-ЯёЁ/-]*)', text)))

    def process_transclusions(self, text: str) -> str:
        """Process {{include:filename}} transclusions."""
        pattern = re.compile(r'\{\{include:([^\}]+)\}\}')

        def replace_include(match):
            filename = match.group(1).strip()
            filepath = self._find_file(filename)
            if filepath and os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Strip front matter
                    content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)
                    return content.strip()
                except Exception as e:
                    logger.warning("Failed to include %s: %s", filepath, e)
                    return f"[Include failed: {filename}]"
            return f"[File not found: {filename}]"

        return pattern.sub(replace_include, text)


class GraphBuilder:
    """Builds a graph of note connections from wikilinks."""

    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.getcwd()
        self.processor = WikiLinkProcessor(base_dir)

    def build_graph(self) -> dict:
        """
        Build graph data from all .md files in the workspace.
        Returns: {nodes: [{id, label, size}], edges: [{source, target}]}
        """
        nodes = {}
        edges = []
        link_counts = defaultdict(int)

        if not os.path.exists(self.base_dir):
            return {'nodes': [], 'edges': []}

        # First pass: collect all files
        md_files = []
        for root, dirs, files in os.walk(self.base_dir):
            for f in files:
                if f.endswith('.md') and not f.startswith('.'):
                    filepath = os.path.join(root, f)
                    stem = os.path.splitext(f)[0]
                    md_files.append((filepath, stem))
                    nodes[stem] = {'id': stem, 'label': stem, 'size': 1}

        # Second pass: extract links
        for filepath, stem in md_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                links = self.processor.extract_links(content)
                for link in links:
                    target = link['target']
                    if target in nodes:
                        edges.append({'source': stem, 'target': target})
                        link_counts[target] += 1
                        link_counts[stem] += 1
            except Exception:
                continue

        # Update node sizes based on link count
        for node_id, count in link_counts.items():
            if node_id in nodes:
                nodes[node_id]['size'] = 1 + count

        return {
            'nodes': list(nodes.values()),
            'edges': edges
        }

    def build_graph_html(self) -> str:
        """Build an interactive HTML graph visualization."""
        graph = self.build_graph()

        if not graph['nodes']:
            return "<p>Нет файлов для отображения</p>"

        import json
        nodes_json = json.dumps(graph['nodes'])
        edges_json = json.dumps(graph['edges'])

        return f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ margin: 0; background: #1a1a2e; overflow: hidden; }}
        #graph {{ width: 100vw; height: 100vh; }}
        .node-label {{ font: 12px sans-serif; fill: #cdd6f4; pointer-events: none; }}
    </style>
</head>
<body>
    <canvas id="graph"></canvas>
    <script>
        const nodes = {nodes_json};
        const edges = {edges_json};
        const canvas = document.getElementById('graph');
        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        // Simple force-directed layout
        const W = canvas.width, H = canvas.height;
        nodes.forEach((n, i) => {{
            n.x = W/2 + (Math.random() - 0.5) * 400;
            n.y = H/2 + (Math.random() - 0.5) * 400;
            n.vx = 0; n.vy = 0;
        }});

        function simulate() {{
            for (let i = 0; i < 100; i++) {{
                // Repulsion
                for (let a of nodes) {{
                    for (let b of nodes) {{
                        if (a === b) continue;
                        let dx = a.x - b.x, dy = a.y - b.y;
                        let d = Math.sqrt(dx*dx + dy*dy) || 1;
                        let f = 500 / (d * d);
                        a.vx += dx/d * f; a.vy += dy/d * f;
                    }}
                }}
                // Attraction (edges)
                for (let e of edges) {{
                    let a = nodes.find(n => n.id === e.source);
                    let b = nodes.find(n => n.id === e.target);
                    if (a && b) {{
                        let dx = b.x - a.x, dy = b.y - a.y;
                        let d = Math.sqrt(dx*dx + dy*dy) || 1;
                        let f = (d - 100) * 0.01;
                        a.vx += dx/d * f; a.vy += dy/d * f;
                        b.vx -= dx/d * f; b.vy -= dy/d * f;
                    }}
                }}
                // Center gravity
                for (let n of nodes) {{
                    n.vx += (W/2 - n.x) * 0.001;
                    n.vy += (H/2 - n.y) * 0.001;
                    n.vx *= 0.9; n.vy *= 0.9;
                    n.x += n.vx; n.y += n.vy;
                }}
            }}
        }}

        function draw() {{
            ctx.clearRect(0, 0, W, H);
            // Edges
            ctx.strokeStyle = '#45475a'; ctx.lineWidth = 1;
            for (let e of edges) {{
                let a = nodes.find(n => n.id === e.source);
                let b = nodes.find(n => n.id === e.target);
                if (a && b) {{
                    ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
                }}
            }}
            // Nodes
            for (let n of nodes) {{
                let r = 5 + n.size * 3;
                ctx.beginPath(); ctx.arc(n.x, n.y, r, 0, Math.PI*2);
                ctx.fillStyle = '#89b4fa'; ctx.fill();
                ctx.strokeStyle = '#cba6f7'; ctx.stroke();
                ctx.fillStyle = '#cdd6f4'; ctx.font = '12px sans-serif';
                ctx.textAlign = 'center'; ctx.fillText(n.label, n.x, n.y - r - 5);
            }}
        }}

        simulate(); draw();
    </script>
</body>
</html>"""
