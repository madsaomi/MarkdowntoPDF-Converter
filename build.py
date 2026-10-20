import PyInstaller.__main__
import os
import sys

# Add project root to path so we can import version
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.__version__ import __version__


def update_installer_version(version):
    installer_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'installer.iss')
    if not os.path.exists(installer_path):
        return
    import re
    with open(installer_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = re.sub(r'AppVersion=.*', f'AppVersion={version}', content)
    
    with open(installer_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Updated installer.iss version to {version}")


def build_executable(windowed=True, skip_pdf_engine=False):
    # Define paths
    src_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(src_dir, 'main.py')
    templates_dir = os.path.join(src_dir, 'templates')

    print(f"Building Standalone Executable v{__version__} with PyInstaller...")
    mode = "GUI (--windowed)" if windowed else "CLI (console)"
    print(f"Mode: {mode}")
    
    # Sync Inno Setup version
    update_installer_version(__version__)

    # WeasyPrint requires adding data for templates
    # In Windows, the separator for --add-data is ';' (in Linux it is ':')
    sep = ';' if os.name == 'nt' else ':'
    add_data_templates = f'{templates_dir}{sep}templates'
    # WeasyPrint engine directory (optional — PDF engine must be present for a frozen build)
    weasyprint_dir = os.path.join(src_dir, 'weasyprint-windows', 'dist')
    weasyprint_exe = os.path.join(weasyprint_dir, 'weasyprint.exe')
    add_data_weasyprint = f'{weasyprint_dir}{sep}weasyprint-windows/dist'
    if not os.path.isfile(weasyprint_exe) and not skip_pdf_engine:
        print("\n" + "=" * 70)
        print("ERROR: PDF engine not found!")
        print(f"  Expected: {weasyprint_exe}")
        print("  A frozen (PyInstaller) build cannot use the pip fallback —")
        print("  it MUST bundle the portable weasyprint.exe.")
        print("  Download/place it there first, or pass --skip-pdf-engine")
        print("  to build WITHOUT PDF support.\n")
        print("  See README.md section 'Build' for details.")
        print("=" * 70 + "\n")
        sys.exit(1)
    # Assets (icon)
    assets_dir = os.path.join(src_dir, 'assets')
    add_data_assets = f'{assets_dir}{sep}assets'
    icon_path = os.path.join(assets_dir, 'icon.ico')

    args = [
        main_script,
        '--name=MarkdownToPDF',
        '--onefile',
    ]
    if windowed:
        args.append('--windowed')

    args += [
        '--noconfirm',
        '--clean',
        f'--icon={icon_path}',
        f'--add-data={add_data_templates}',
        f'--add-data={add_data_assets}',
        '--collect-all=pymdownx',
        '--hidden-import=PyQt6.QtWidgets',
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=PyQt6.QtPrintSupport',
        '--hidden-import=fitz',
        '--hidden-import=pygments.lexers',
        '--hidden-import=pygments.styles',
        '--hidden-import=pygments.formatters',
        '--hidden-import=pypdf',
        '--hidden-import=ebooklib',
        '--hidden-import=PIL',
        '--hidden-import=pytesseract',
        '--hidden-import=pptx',
        '--hidden-import=pyttsx3',
        '--hidden-import=src',
        '--hidden-import=src.core',
        '--hidden-import=src.gui',
        '--hidden-import=src.core.parser',
        '--hidden-import=src.core.renderer',
        '--hidden-import=src.core.docx_renderer',
        '--hidden-import=src.gui.main_window',
        '--hidden-import=src.gui.ui_layout',
        '--hidden-import=src.gui.translations',
        '--hidden-import=src.gui.highlighter',
        '--hidden-import=src.gui.dialogs',
        '--hidden-import=src.gui.dialogs.common',
        '--hidden-import=src.gui.dialogs.github_plugin',
        '--hidden-import=src.gui.dialogs.export',
        '--hidden-import=src.gui.dialogs.content',
        '--hidden-import=src.gui.dialogs.analysis',
        '--hidden-import=src.gui.dialogs.versions',
        '--hidden-import=src.gui.document_tools',
        '--hidden-import=src.gui.file_manager',
        '--hidden-import=src.gui.preview_manager',
        '--hidden-import=src.gui.editor_commands',
        '--hidden-import=src.gui.models',
        '--hidden-import=src.gui.welcome_docs',
        '--hidden-import=src.gui.translator',
        '--hidden-import=src.gui.templates_data',
        '--hidden-import=src.gui.multi_cursor',
        '--hidden-import=src.gui.excalidraw_canvas',
        '--hidden-import=src.gui.csv_editor',
        '--hidden-import=src.gui.calendar_view',
        '--hidden-import=src.gui.pomodoro',
        '--hidden-import=src.gui.welcome_tour',
        '--hidden-import=src.gui.watermark_designer',
        '--hidden-import=src.core.ai_assistant',
        '--hidden-import=src.core.wikilinks',
        '--hidden-import=src.core.pdf_to_markdown',
        '--hidden-import=src.core.ocr_engine',
        '--hidden-import=src.core.latex_preview',
        '--hidden-import=src.core.multi_export',
        '--hidden-import=src.core.tts_engine',
        '--hidden-import=src.core.flashcards',
        '--hidden-import=src.core.glossary',
        '--hidden-import=src.core.quiz_generator',
        '--hidden-import=src.core.snippets',
        '--hidden-import=src.core.cloud_templates',
        '--hidden-import=src.core.citation_manager',
        '--hidden-import=src.core.github_sync',
        '--hidden-import=src.core.linter',
        '--hidden-import=src.core.template_vars',
        '--hidden-import=src.core.html_to_markdown',
        '--hidden-import=src.core.reveal_exporter',
        '--hidden-import=src.core.image_renderer',
        '--hidden-import=src.core.epub_renderer',
        '--hidden-import=src.core.pptx_renderer',
        '--hidden-import=src.core.pdf_encrypt',
        '--hidden-import=speech_recognition',
    ]

    if not skip_pdf_engine:
        args.append(f'--add-data={add_data_weasyprint}')

    PyInstaller.__main__.run(args)

    print(f"Build complete! v{__version__} executable is in the 'dist' folder.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build MarkdownToPDF standalone executable")
    parser.add_argument('--console', action='store_true', help='Build with console (for CLI debugging)')
    parser.add_argument('--debug', action='store_true', help='Build with debug mode')
    parser.add_argument('--skip-pdf-engine', action='store_true',
                        help='Build without bundling weasyprint.exe (PDF export will NOT work in the built app)')
    parsed = parser.parse_args()

    build_executable(windowed=not parsed.console, skip_pdf_engine=parsed.skip_pdf_engine)

    if parsed.debug:
        print("\nNote: --debug flag passed. Consider adding '--debug' PyInstaller flag for more verbose output.")
