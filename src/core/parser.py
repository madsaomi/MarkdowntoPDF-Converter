import markdown
from markdown.extensions.toc import TocExtension
from typing import Tuple, Dict, Any, Optional

class MarkdownParser:
    def __init__(self):
        # We use a comprehensive list of extensions for GitHub-flavored Markdown
        self.extensions = [
            'meta',
            'tables',
            'fenced_code',
            'codehilite',
            'nl2br',
            'sane_lists',
            'admonition',
            'footnotes',
            'pymdownx.magiclink',
            'pymdownx.betterem',
            'pymdownx.tilde',
            'pymdownx.tasklist',
            'pymdownx.superfences',
            'pymdownx.details',
            'pymdownx.mark',
            'pymdownx.caret',
            'pymdownx.keys',
            TocExtension(permalink=False)
        ]
        
    def preprocess_mermaid(self, text: str) -> str:
        """
        Extracts ```mermaid ... ``` blocks, compresses using raw deflate,
        and encodes to Base64 to generate Kroki SVG image URL replacements.
        """
        if not getattr(self, 'kroki_available', True):
            return text

        import re
        import zlib
        import base64

        pattern = re.compile(r'```mermaid\s*\n(.*?)\n```', re.DOTALL)

        def replace(match):
            code = match.group(1).strip()
            if not code:
                return ""
            try:
                compressed = zlib.compress(code.encode('utf-8'), 9)
                encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')
                url = f"https://kroki.io/mermaid/svg/{encoded}"
                return f'<div class="mermaid-diagram" style="text-align: center; margin: 1.5em 0;"><img src="{url}" alt="Mermaid Diagram" style="max-width: 100%; height: auto;"></div>'
            except Exception:
                return match.group(0)

        return pattern.sub(replace, text)

    def preprocess_diagrams(self, text: str) -> str:
        """
        Extracts diagram blocks (plantuml, graphviz, dot, ditaa, c4) and generates Kroki URLs.
        """
        if not getattr(self, 'kroki_available', True):
            return text

        import re
        import zlib
        import base64
        
        engine_map = {
            'plantuml': 'plantuml',
            'graphviz': 'graphviz',
            'dot': 'graphviz',
            'ditaa': 'ditaa',
            'c4': 'c4plantuml'
        }
        
        pattern = re.compile(r'```(plantuml|graphviz|dot|ditaa|c4)\s*\n(.*?)\n```', re.DOTALL | re.IGNORECASE)
        
        def replace(match):
            tag = match.group(1).lower()
            code = match.group(2).strip()
            engine = engine_map.get(tag, tag)
            if not code:
                return ""
            try:
                compressed = zlib.compress(code.encode('utf-8'), 9)
                encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')
                url = f"https://kroki.io/{engine}/svg/{encoded}"
                return f'<div class="diagram-{tag}" style="text-align: center; margin: 1.5em 0;"><img src="{url}" alt="{tag} Diagram" style="max-width: 100%; height: auto;"></div>'
            except Exception:
                return match.group(0)
                
        return pattern.sub(replace, text)

    def preprocess_latex(self, text: str) -> str:
        """
        Extracts block math ($$ ... $$) and inline math ($ ... $) and replaces
        them with CodeCogs vector SVG image tags for high-definition rendering.
        """
        import re
        import urllib.parse

        # Mask code blocks to prevent latex from messing up JS/Bash syntax ($)
        code_blocks = {}
        def mask_code(match):
            key = f"__CODE_BLOCK_{len(code_blocks)}__"
            code_blocks[key] = match.group(0)
            return key
            
        text = re.sub(r'```.*?```', mask_code, text, flags=re.DOTALL)
        text = re.sub(r'`[^`]+`', mask_code, text)

        # 1. Block equations
        block_pattern = re.compile(r'\$\$(.*?)\$\$', re.DOTALL)
        
        def replace_block(match):
            formula = match.group(1).strip()
            if not formula:
                return ""
            encoded = urllib.parse.quote(formula)
            url = f"https://latex.codecogs.com/svg.image?{encoded}"
            return f'<div class="math-latex-block"><img class="math-latex" src="{url}" alt="Equation: {formula}"></div>'

        text = block_pattern.sub(replace_block, text)

        # 2. Inline equations
        inline_pattern = re.compile(r'(?<!\$)\$(?!\s)(.*?)(?<!\s)\$(?!\$)', re.DOTALL)

        def replace_inline(match):
            formula = match.group(1).strip()
            if not formula:
                return ""
            # Prevent matching standard currency amounts like $10 or $100
            if re.match(r'^\d+(\.\d+)?$', formula):
                return match.group(0)
            encoded = urllib.parse.quote(formula)
            url = f"https://latex.codecogs.com/svg.image?\\inline&space;{encoded}"
            return f'<img class="math-latex math-latex-inline" src="{url}" alt="{formula}">'

        text = inline_pattern.sub(replace_inline, text)

        # Restore code blocks
        for key, value in code_blocks.items():
            text = text.replace(key, value)

        return text

    def preprocess_media(self, html: str, base_dir: str = None) -> str:
        """
        Scans all <img> tags in the generated HTML.
        Downloads external HTTP/HTTPS images and encodes them to Base64.
        Encodes local images found on disk to Base64.
        Replaces image src with Base64 data URIs.
        Uses a file-based cache for downloaded images (7-day TTL).
        """
        import re
        import os
        import base64
        import mimetypes
        import urllib.request
        import urllib.parse
        import hashlib
        import time
        import logging
        
        logger = logging.getLogger("MarkdownToPDF.Parser")
        
        # Image cache directory
        try:
            from src.config import AppConfig
            cache_dir = AppConfig.cache_dir()
        except Exception:
            cache_dir = os.path.join(os.getenv("APPDATA", "."), "MarkdownToPDF_Pro", "cache", "images")
            os.makedirs(cache_dir, exist_ok=True)
        
        img_pattern = re.compile(r'<img\s+([^>]*?)src=["\'](.*?)["\']([^>]*?)>', re.IGNORECASE)
        
        def get_cached_or_download(url: str) -> bytes:
            """Download URL with file-based cache (7-day TTL)."""
            url_hash = hashlib.md5(url.encode()).hexdigest()
            cache_path = os.path.join(cache_dir, f"{url_hash}.bin")
            
            # Check cache
            if os.path.exists(cache_path):
                try:
                    mtime = os.path.getmtime(cache_path)
                    if (time.time() - mtime) < 7 * 86400:
                        with open(cache_path, 'rb') as f:
                            return f.read()
                except Exception:
                    logger.warning("Failed to check cache mtime for %s", cache_path)
            
            # Download
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                data = response.read()
            
            # Save to cache
            try:
                with open(cache_path, 'wb') as f:
                    f.write(data)
            except Exception:
                logger.warning("Failed to save image to cache: %s", cache_path)
            
            return data
        
        def get_base64_data_uri(path_or_url: str) -> str:
            if path_or_url.startswith('data:'):
                return path_or_url
                
            content_type, _ = mimetypes.guess_type(path_or_url)
            if not content_type:
                content_type = 'image/png'
                
            try:
                # 1. Handle HTTP/HTTPS URLs (with cache)
                if path_or_url.startswith(('http://', 'https://')):
                    img_data = get_cached_or_download(path_or_url)
                    encoded_data = base64.b64encode(img_data).decode('utf-8')
                    return f"data:{content_type};base64,{encoded_data}"
                    
                # 2. Handle Local Files
                else:
                    full_path = path_or_url
                    if base_dir and not os.path.isabs(path_or_url):
                        full_path = os.path.join(base_dir, path_or_url)
                        
                    full_path = urllib.parse.unquote(full_path)
                    
                    if os.path.exists(full_path) and os.path.isfile(full_path):
                        with open(full_path, 'rb') as f:
                            img_data = f.read()
                        encoded_data = base64.b64encode(img_data).decode('utf-8')
                        return f"data:{content_type};base64,{encoded_data}"
                        
            except Exception as e:
                logger.error("Failed to base64 encode image %s: %s", path_or_url, e)
                
            return path_or_url
            
        def replace_img(match):
            attrs_before = match.group(1)
            src = match.group(2)
            attrs_after = match.group(3)
            
            base64_src = get_base64_data_uri(src)
            return f'<img {attrs_before}src="{base64_src}"{attrs_after}>'
            
        return img_pattern.sub(replace_img, html)

    def _ensure_table_spacing(self, text: str) -> str:
        lines = text.split('\n')
        result = []
        in_code = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('```'):
                in_code = not in_code
            if not in_code and stripped.startswith('|') and i > 0:
                prev = lines[i - 1].strip()
                if prev and not prev.startswith('|') and not prev.startswith('```'):
                    result.append('')
            result.append(line)
        return '\n'.join(result)

    def parse(self, text: str, base_dir: Optional[str] = None, is_presentation: bool = False, kroki_available: bool = True) -> Tuple[str, Dict[str, Any]]:
        """
        Parses Markdown text into HTML and extracts YAML metadata.
        Returns a tuple of (html_string, metadata_dict).
        """
        self.kroki_available = kroki_available
        text = self._ensure_table_spacing(text)
        if is_presentation:
            lines = text.splitlines()
            slides_md = []
            current_slide = []
            in_code_block = False
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("```"):
                    in_code_block = not in_code_block
                if stripped == "---" and not in_code_block:
                    slides_md.append("\n".join(current_slide))
                    current_slide = []
                else:
                    current_slide.append(line)
            if current_slide or not slides_md:
                slides_md.append("\n".join(current_slide))
                
            slides_html = []
            flat_meta = {}
            for s_md in slides_md:
                processed = self.preprocess_mermaid(s_md)
                processed = self.preprocess_diagrams(processed)
                processed = self.preprocess_latex(processed)
                
                md = markdown.Markdown(extensions=self.extensions)
                s_html = md.convert(processed)
                
                metadata = md.Meta if hasattr(md, 'Meta') else {}
                slide_meta = {k: v[0] for k, v in metadata.items() if v}
                flat_meta.update(slide_meta)
                
                slides_html.append(f'<section class="slide">{s_html}</section>')
                
            html = "\n".join(slides_html)
        else:
            processed_text = self.preprocess_mermaid(text)
            processed_text = self.preprocess_diagrams(processed_text)
            processed_text = self.preprocess_latex(processed_text)
            
            md = markdown.Markdown(extensions=self.extensions)
            html = md.convert(processed_text)
            
            metadata = md.Meta if hasattr(md, 'Meta') else {}
            flat_meta = {k: v[0] for k, v in metadata.items() if v}
            
        # Protect and inline all media resources
        html = self.preprocess_media(html, base_dir=base_dir)
        return html, flat_meta
