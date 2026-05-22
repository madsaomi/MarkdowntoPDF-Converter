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


def build_executable():
    # Define paths
    src_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(src_dir, 'main.py')
    templates_dir = os.path.join(src_dir, 'templates')

    print(f"Building Standalone Executable v{__version__} with PyInstaller...")
    
    # Sync Inno Setup version
    update_installer_version(__version__)

    # WeasyPrint requires adding data for templates
    # In Windows, the separator for --add-data is ';' (in Linux it's ':')
    sep = ';' if os.name == 'nt' else ':'
    add_data_templates = f'{templates_dir}{sep}templates'
    # WeasyPrint engine directory
    weasyprint_dir = os.path.join(src_dir, 'weasyprint-windows', 'dist')
    add_data_weasyprint = f'{weasyprint_dir}{sep}weasyprint-windows/dist'
    # Assets (icon)
    assets_dir = os.path.join(src_dir, 'assets')
    add_data_assets = f'{assets_dir}{sep}assets'
    icon_path = os.path.join(assets_dir, 'icon.ico')

    PyInstaller.__main__.run([
        main_script,
        '--name=MarkdownToPDF',
        '--windowed',
        '--noconfirm',
        '--clean',
        f'--icon={icon_path}',
        f'--add-data={add_data_templates}',
        f'--add-data={add_data_weasyprint}',
        f'--add-data={add_data_assets}',
        '--hidden-import=pygments.lexers',
        '--hidden-import=pygments.styles',
        '--hidden-import=pypdf',
        '--hidden-import=src',
        '--hidden-import=src.core',
        '--hidden-import=src.gui',
        '--hidden-import=src.core.parser',
        '--hidden-import=src.core.renderer',
        '--hidden-import=src.core.docx_renderer',
        '--hidden-import=src.gui.main_window',
        '--hidden-import=src.gui.ui_layout',
        '--hidden-import=src.gui.translations',
    ])

    print(f"Build complete! v{__version__} executable is in the 'dist' folder.")


if __name__ == "__main__":
    build_executable()
