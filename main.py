import os
import sys
import argparse
from src.config import AppConfig
from src.core.parser import MarkdownParser
from src.core.renderer import PDFRenderer
from src.core.docx_renderer import DOCXRenderer
from src.core.pdf_encrypt import encrypt_pdf
from src.__version__ import __version__


def get_paths():
    return AppConfig.template_dir(), AppConfig.weasyprint_exe()


def run_cli(args):
    parser = argparse.ArgumentParser(
        description=f"Markdown to PDF/DOCX Converter Pro CLI v{__version__} (Headless Mode)"
    )
    parser.add_argument("input_files", nargs="+", help="Markdown (.md) files to convert")
    parser.add_argument("-o", "--output", help="Output file path (defaults to input filename + format extension in input file's directory)")
    parser.add_argument("-f", "--format", choices=["pdf", "docx", "html", "epub", "png", "jpg", "pptx", "reveal"], default="pdf", help="Output format (default: pdf)")
    parser.add_argument("--theme", choices=["modern", "classic"], default="modern", help="Document theme (default: modern)")
    parser.add_argument("--code-theme", choices=["light", "dark"], default="light", help="Code highlights theme (default: light)")
    parser.add_argument("--paper", choices=["A4", "Letter", "Legal", "A3", "A5"], default="A4", help="Paper size (default: A4)")
    parser.add_argument("-w", "--watermark", default="", help="Watermark text")
    parser.add_argument("--footer", default="", help="Footer text")
    parser.add_argument("-m", "--margins", default="", help="Page margins (e.g. '20mm 15mm 20mm 15mm')")
    parser.add_argument("-p", "--password", default="", help="PDF encryption password")
    parser.add_argument("--docx-template", default="", help="DOCX template reference file")
    parser.add_argument("--custom-css", default="", help="Custom CSS style path")
    parser.add_argument("--page-numbers", action="store_true", help="Enable page numbers")
    parser.add_argument("--page-format", choices=["simple", "slash", "text"], default="simple", help="Page numbering format (default: simple)")
    parser.add_argument("--lang", choices=["ru", "en"], default="ru", help="Language for numbering translations (default: ru)")
    
    parsed = parser.parse_args(args)
    
    # Resolve themes
    theme_map = {"modern": "theme_modern.css", "classic": "theme_classic.css"}
    code_map = {"light": "pygments.css", "dark": "pygments_dark.css"}
    
    doc_theme = theme_map[parsed.theme]
    code_theme = code_map[parsed.code_theme]
    
    template_dir, wp_executable = get_paths()
    
    # Check if Kroki is online
    import urllib.request
    kroki_available = False
    try:
        req = urllib.request.Request("https://kroki.io", method="HEAD")
        with urllib.request.urlopen(req, timeout=1.5):
            kroki_available = True
    except Exception:
        pass
        
    print(f"--- Headless Converter Pro CLI v{__version__} ---")
    print(f"Format: {parsed.format.upper()}")
    print(f"Theme: {parsed.theme} | Code Theme: {parsed.code_theme}")
    if parsed.page_numbers:
        print(f"Page Numbers: Enabled ({parsed.page_format}) | Lang: {parsed.lang}")
    
    md_parser = MarkdownParser()
    
    for infile in parsed.input_files:
        if not os.path.exists(infile):
            print(f"Error: File not found: {infile}", file=sys.stderr)
            continue
            
        print(f"Processing: {os.path.basename(infile)} ...")
        
        try:
            with open(infile, 'r', encoding='utf-8') as f:
                md_text = f.read()
                
            html_content, metadata = md_parser.parse(
                md_text, 
                base_dir=os.path.dirname(os.path.abspath(infile)), 
                kroki_available=kroki_available
            )
            
            # Resolve output path
            if parsed.output:
                out_file = os.path.abspath(parsed.output)
            else:
                out_dir = os.path.dirname(os.path.abspath(infile))
                base_name = os.path.splitext(os.path.basename(infile))[0]
                out_file = os.path.join(out_dir, f"{base_name}.{parsed.format}")
            os.makedirs(os.path.dirname(out_file), exist_ok=True)
            
            if parsed.format == "docx":
                renderer = DOCXRenderer()
                renderer.render(html_content, metadata, out_file, reference_docx=parsed.docx_template, lang=parsed.lang)
            elif parsed.format == "epub":
                from src.core.epub_renderer import EPUBRenderer
                renderer = EPUBRenderer()
                renderer.render(html_content, metadata, out_file, lang=parsed.lang)
            elif parsed.format in ("png", "jpg"):
                from src.core.image_renderer import ImageRenderer
                renderer = ImageRenderer(wp_executable)
                count = renderer.render(
                    html_content, metadata, out_file,
                    doc_theme=doc_theme, code_theme=code_theme,
                    paper_size=parsed.paper, lang=parsed.lang,
                    image_format=parsed.format
                )
                print(f"✅ Saved {count} image(s): {out_file}")
            elif parsed.format == "pptx":
                from src.core.pptx_renderer import PPTXRenderer
                renderer = PPTXRenderer()
                count = renderer.render(html_content, metadata, out_file, lang=parsed.lang)
                print(f"✅ Saved {count} slides: {out_file}")
            elif parsed.format == "html":
                renderer = PDFRenderer(template_dir, wp_executable)
                rendered_html = renderer.render_html(
                    html_content, metadata,
                    doc_theme, code_theme,
                    parsed.paper, parsed.watermark, parsed.footer,
                    infile, parsed.custom_css, parsed.margins,
                    page_numbers=parsed.page_numbers, page_num_format=parsed.page_format, lang=parsed.lang
                )
                with open(out_file, 'w', encoding='utf-8') as f:
                    f.write(rendered_html)
            else: # PDF
                renderer = PDFRenderer(template_dir, wp_executable)
                renderer.render(
                    html_content, metadata, out_file,
                    doc_theme, code_theme,
                    parsed.paper, parsed.watermark, parsed.footer,
                    infile, parsed.custom_css, parsed.margins,
                    page_numbers=parsed.page_numbers, page_num_format=parsed.page_format, lang=parsed.lang
                )
                
                # Encrypt if password set
                if parsed.password:
                    if encrypt_pdf(out_file, parsed.password):
                        print("  Password encryption applied.")
                    else:
                        print("  Warning: PDF Encryption failed.", file=sys.stderr)
                        
            print(f"  Saved to: {out_file}")
            
        except Exception as e:
            print(f"  Error converting {infile}: {e}", file=sys.stderr)
            
    print("Done!")


def main():
    if len(sys.argv) > 1:
        sys.exit(run_cli(sys.argv[1:]))
    else:
        from PyQt6.QtWidgets import QApplication
        from src.gui.main_window import MainWindow
        from src.gui.styles import LIGHT_STYLE

        app = QApplication(sys.argv)
        app.setStyleSheet(LIGHT_STYLE)
        
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec())


if __name__ == '__main__':
    main()
