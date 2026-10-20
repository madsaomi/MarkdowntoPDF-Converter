import markdown
from markdown.extensions.toc import TocExtension
from typing import Tuple, Dict, Any, Optional
import socket
from urllib.parse import urlparse


def _is_private_url(url: str) -> bool:
    """Check if URL points to a private/reserved IP (SSRF protection)."""
    try:
        host = urlparse(url).hostname or ""
        if host in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
            return True
        host_lower = host.lower()
        if host_lower.endswith(".local") or host_lower.endswith(".internal"):
            return True
        ip = socket.gethostbyname(host)
        if ip.startswith(("10.", "172.16.", "172.17.", "172.18.", "172.19.",
                          "172.20.", "172.21.", "172.22.", "172.23.",
                          "172.24.", "172.25.", "172.26.", "172.27.",
                          "172.28.", "172.29.", "172.30.", "172.31.",
                          "192.168.", "169.254.", "127.")):
            return True
    except Exception:
        pass
    return False


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
        from src.core.render_cache import get_cached, set_cached
        
        engine_map = {
            'plantuml': 'plantuml',
            'graphviz': 'graphviz',
            'dot': 'graphviz',
            'ditaa': 'ditaa',
            'c4': 'c4plantuml',
            'mermaid': 'mermaid',
        }
        
        pattern = re.compile(r'```(plantuml|graphviz|dot|ditaa|c4|mermaid)\s*\n(.*?)\n```', re.DOTALL | re.IGNORECASE)
        
        def replace(match):
            tag = match.group(1).lower()
            code = match.group(2).strip()
            engine = engine_map.get(tag, tag)
            if not code:
                return ""
            try:
                compressed = zlib.compress(code.encode('utf-8'), 9)
                encoded = base64.urlsafe_b64encode(compressed).decode('utf-8').rstrip('=')
                key = f"{engine}|{encoded}"
                cached = get_cached('kroki_url', key)
                if cached and cached.get('url'):
                    url = cached['url']
                else:
                    url = f"https://kroki.io/{engine}/svg/{encoded}"
                    try:
                        set_cached('kroki_url', key, {'url': url})
                    except Exception:
                        pass
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
        from src.config import AppConfig
        cache_dir = AppConfig.cache_dir()
        
        img_pattern = re.compile(r'<img\s+([^>]*?)src=["\'](.*?)["\']([^>]*?)\s*/?>', re.IGNORECASE)
        
        def get_cached_or_download(url: str) -> bytes:
            """Download URL with file-based cache (7-day TTL)."""
            if not url.startswith(("http://", "https://")):
                raise ValueError(f"Only HTTP/HTTPS URLs allowed: {url}")
            if _is_private_url(url):
                raise ValueError(f"Blocked private/reserved URL: {url}")
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
                    # Skip SVG images - WeasyPrint handles remote SVGs better than data URIs
                    if content_type and 'svg' in content_type:
                        return path_or_url
                    img_data = get_cached_or_download(path_or_url)
                    encoded_data = base64.b64encode(img_data).decode('utf-8')
                    return f"data:{content_type};base64,{encoded_data}"
                    
                # 2. Handle Local Files
                else:
                    full_path = urllib.parse.unquote(path_or_url)
                    if base_dir:
                        if not os.path.isabs(full_path):
                            full_path = os.path.normpath(os.path.join(base_dir, full_path))
                        resolved = os.path.realpath(full_path)
                        base_resolved = os.path.realpath(base_dir)
                        if not resolved.startswith(base_resolved + os.sep) and resolved != base_resolved:
                            logger.warning("Path traversal blocked: %s", path_or_url)
                            return path_or_url
                    
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

    def _sanitize_html(self, html: str) -> str:
        import re
        safe = html
        # Remove <script> and </script> tags (even without matching close/open)
        safe = re.sub(r'<script[^>]*>', '', safe, flags=re.IGNORECASE)
        safe = re.sub(r'</script[^>]*>', '', safe, flags=re.IGNORECASE)
        # Remove event handlers (onclick, onerror, onload, onmouseover, etc.)
        safe = re.sub(r'\bon\w+\s*=\s*["\'][^"\']*["\']', '', safe, flags=re.IGNORECASE)
        safe = re.sub(r'\bon\w+\s*=\s*\S+', '', safe, flags=re.IGNORECASE)
        # Block javascript: in href, src, action, data, formaction, xlink:href
        safe = re.sub(r'\b(href|src|action|data|formaction|xlink:href)\s*=\s*["\']\s*javascript\s*:', r'\1="#blocked-javascript:', safe, flags=re.IGNORECASE)
        # Block <object>, <embed>, <applet> tags
        safe = re.sub(r'<object[^>]*>.*?</object>', '', safe, flags=re.DOTALL | re.IGNORECASE)
        safe = re.sub(r'<embed[^>]*>', '', safe, flags=re.IGNORECASE)
        safe = re.sub(r'<applet[^>]*>.*?</applet>', '', safe, flags=re.DOTALL | re.IGNORECASE)
        # Block <iframe>, <frame>, <frameset>
        safe = re.sub(r'<iframe[^>]*>.*?</iframe>', '', safe, flags=re.DOTALL | re.IGNORECASE)
        safe = re.sub(r'<frame[^>]*>', '', safe, flags=re.IGNORECASE)
        safe = re.sub(r'<frameset[^>]*>.*?</frameset>', '', safe, flags=re.DOTALL | re.IGNORECASE)
        # Block <base> tag (can hijack relative URLs)
        safe = re.sub(r'<base[^>]*>', '', safe, flags=re.IGNORECASE)
        return safe

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
            html = self._sanitize_html(html)
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
        html = self._sanitize_html(html)
        return html, flat_meta
