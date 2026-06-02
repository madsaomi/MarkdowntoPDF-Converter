import logging
import os
from datetime import datetime

logger = logging.getLogger("MarkdownToPDF.multi_export")


def multi_export(source_md: str, output_dir: str, formats: list[str],
                 template_dir: str = "", options=None) -> dict[str, str]:
    """Export a single .md file to multiple formats simultaneously.

    Args:
        source_md: path to source .md file
        output_dir: directory for output files
        formats: list of format strings: 'pdf', 'docx', 'html', 'epub', 'png', 'pptx'
        template_dir: path to templates
        options: ConversionOptions or None

    Returns:
        dict of format → output_path
    """
    from src.core.parser import MarkdownParser
    from src.core.renderer import PDFRenderer
    from src.core.docx_renderer import DOCXRenderer

    base_name = os.path.splitext(os.path.basename(source_md))[0]
    results = {}

    with open(source_md, "r", encoding="utf-8") as f:
        md_text = f.read()

    parser = MarkdownParser(template_dir or "", "")

    for fmt in formats:
        try:
            out_path = os.path.join(output_dir, f"{base_name}.{fmt}")

            if fmt == "html":
                html = parser.render(md_text)
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(html)
                results[fmt] = out_path

            elif fmt == "pdf":
                html = parser.render(md_text)
                renderer = PDFRenderer(template_dir or "")
                renderer.render(html, out_path, options)
                results[fmt] = out_path

            elif fmt == "docx":
                renderer = DOCXRenderer()
                renderer.render(md_text, out_path, template=options.docx_template if options else "")
                results[fmt] = out_path

            elif fmt == "epub":
                from src.core.epub_renderer import EPUBRenderer
                renderer = EPUBRenderer()
                renderer.render(md_text, out_path, title=base_name)
                results[fmt] = out_path

            elif fmt == "pptx":
                from src.core.pptx_renderer import PPTXRenderer
                renderer = PPTXRenderer()
                renderer.render(md_text, out_path)
                results[fmt] = out_path

            else:
                logger.warning("Unsupported format: %s", fmt)

        except Exception as e:
            logger.error("Multi-export failed for %s: %s", fmt, e)
            results[fmt] = f"ERROR: {e}"

    return results


def export_summary(results: dict[str, str]) -> str:
    """Generate a summary string of multi-export results."""
    lines = ["Multi-export results:"]
    for fmt, path in results.items():
        status = "✅" if not path.startswith("ERROR") else "❌"
        lines.append(f"  {status} {fmt}: {path}")
    return "\n".join(lines)
