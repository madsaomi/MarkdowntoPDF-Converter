import logging
import os

logger = logging.getLogger("MarkdownToPDF.multi_export")


def multi_export(source_md: str, output_dir: str, formats: list[str],
                 template_dir: str = "", options=None) -> dict[str, str]:
    from src.core.parser import MarkdownParser
    from src.core.renderer import PDFRenderer
    from src.core.docx_renderer import DOCXRenderer

    base_name = os.path.splitext(os.path.basename(source_md))[0]
    results = {}

    with open(source_md, "r", encoding="utf-8") as f:
        md_text = f.read()

    parser = MarkdownParser()
    html_content, metadata = parser.parse(
        md_text,
        base_dir=os.path.dirname(os.path.abspath(source_md)),
        kroki_available=True
    )

    for fmt in formats:
        try:
            out_path = os.path.join(output_dir, f"{base_name}.{fmt}")

            if fmt == "html":
                renderer = PDFRenderer(template_dir, "")
                rendered_html = renderer.render_html(
                    html_content, metadata,
                    doc_theme=options.doc_theme if options else 'theme_modern.css',
                    code_theme=options.code_theme if options else 'pygments.css',
                    paper_size=options.paper_size if options else 'A4',
                    watermark=options.watermark if options else '',
                    footer_text=options.footer_text if options else '',
                    input_filepath=source_md,
                    custom_css_path=options.custom_css if options else '',
                    margins=options.margins if options else '',
                    page_numbers=options.page_numbers if options else False,
                    page_num_format=options.page_num_format if options else 'simple',
                    lang=options.lang if hasattr(options, 'lang') else 'ru',
                )
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(rendered_html)
                results[fmt] = out_path

            elif fmt == "pdf":
                renderer = PDFRenderer(template_dir, "")
                renderer.render(
                    html_content, metadata, out_path,
                    doc_theme=options.doc_theme if options else 'theme_modern.css',
                    code_theme=options.code_theme if options else 'pygments.css',
                    paper_size=options.paper_size if options else 'A4',
                    watermark=options.watermark if options else '',
                    footer_text=options.footer_text if options else '',
                    input_filepath=source_md,
                    custom_css_path=options.custom_css if options else '',
                    margins=options.margins if options else '',
                    page_numbers=options.page_numbers if options else False,
                    page_num_format=options.page_num_format if options else 'simple',
                    lang=options.lang if hasattr(options, 'lang') else 'ru',
                    compress=options.compress if hasattr(options, 'compress') else False,
                )
                results[fmt] = out_path

            elif fmt == "docx":
                renderer = DOCXRenderer()
                renderer.render(
                    html_content, metadata, out_path,
                    reference_docx=options.docx_template if options else '',
                    lang=options.lang if hasattr(options, 'lang') else 'ru',
                )
                results[fmt] = out_path

            elif fmt == "epub":
                from src.core.epub_renderer import EPUBRenderer
                renderer = EPUBRenderer()
                renderer.render(html_content, metadata, out_path,
                                lang=options.lang if hasattr(options, 'lang') else 'ru')
                results[fmt] = out_path

            elif fmt == "pptx":
                from src.core.pptx_renderer import PPTXRenderer
                renderer = PPTXRenderer()
                renderer.render(html_content, metadata, out_path,
                                lang=options.lang if hasattr(options, 'lang') else 'ru')
                results[fmt] = out_path

            else:
                logger.warning("Unsupported format: %s", fmt)

        except Exception as e:
            logger.error("Multi-export failed for %s: %s", fmt, e, exc_info=True)
            results[fmt] = f"ERROR: {e}"

    return results


def export_summary(results: dict[str, str]) -> str:
    lines = ["Multi-export results:"]
    for fmt, path in results.items():
        status = "✅" if not path.startswith("ERROR") else "❌"
        lines.append(f"  {status} {fmt}: {path}")
    return "\n".join(lines)
