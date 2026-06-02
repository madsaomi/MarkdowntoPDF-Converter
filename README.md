# Markdown to PDF Converter Pro

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)
![WeasyPrint](https://img.shields.io/badge/PDF_Engine-WeasyPrint-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

Desktop application for converting Markdown to PDF, DOCX, HTML, EPUB, PPTX, Reveal.js, PNG, JPG with live preview editor.

## Features

### Editor
- Split view: Markdown editor + live preview
- Auto-update preview (500ms debounce)
- Syntax highlighting (Markdown + code blocks)
- Multi-cursor editing
- Welcome guide on startup

### Export Formats
| Format | Engine | Notes |
|--------|--------|-------|
| PDF | WeasyPrint | Professional typography, CJK support |
| DOCX | python-docx | With reference template support |
| HTML | Built-in | Standalone HTML files |
| EPUB | ebooklib | E-book format |
| PPTX | python-pptx | PowerPoint presentations |
| Reveal.js | Built-in | HTML presentations |
| PNG/JPG | WeasyPrint | Image export |

### PDF Features
- Page themes (modern, classic, presentation)
- Code syntax highlighting (light/dark)
- Custom CSS stylesheets
- Watermark text
- Custom footer with variables: `{date}`, `{filename}`, `{title}`, `{word_count}`, `{time}`
- PDF encryption with password
- Table of contents with dot leaders

### Tools
- Markdown linter (12 rules)
- Code snippets library
- LaTeX formula preview
- HTML to Markdown converter
- Flashcard generator
- Citation manager (BibTeX)
- Auto-glossary
- Quiz generator
- TTS (text-to-speech) with 22 voices
- OCR (image to text)
- PDF to Markdown extraction
- Wiki links + knowledge graph
- Cloud templates fetcher
- GitHub sync (init, commit, push, pull, log)
- Drawing canvas (Excalidraw)
- CSV/TSV editor
- Calendar notes
- Pomodoro timer
- Watermark designer

### UI
- Glassmorphism dark/light themes
- Animated splash screen
- Custom title bar
- Toast notifications
- About dialog
- Feature tour
- Ambient glow background
- Zen mode
- Keyboard shortcuts (Ctrl+/)
- Drag & drop files

### Internationalization
- Russian and English interfaces
- Switch language without restart

## Installation

### Requirements
- Python 3.10+
- Windows 10/11 (for bundled WeasyPrint)

### Setup
```bash
git clone https://github.com/yourusername/markdown-to-pdf-converter.git
cd markdown-to-pdf-converter
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## CLI Mode

Run without GUI for automation:

```bash
python main.py test.md -f pdf --theme modern -m "20mm 15mm" -p "password"
```

| Argument | Description | Default |
|----------|-------------|---------|
| `input_files` | Markdown files to convert | Required |
| `-o`, `--output-dir` | Output directory | Same as input |
| `-f`, `--format` | Output format (pdf/docx/html/epub/pptx/png/jpg) | pdf |
| `--theme` | Document theme (modern/classic) | modern |
| `--code-theme` | Code highlighting (light/dark) | light |
| `--paper` | Page size (A4/Letter/Legal/A3/A5) | A4 |
| `-w`, `--watermark` | Watermark text | None |
| `--footer` | Custom footer | None |
| `-m`, `--margins` | Page margins (e.g. "20mm 15mm") | From theme |
| `-p`, `--password` | PDF encryption password | None |
| `--docx-template` | Reference DOCX template | None |
| `--custom-css` | Custom CSS file | None |

## Project Structure

```
markdown-to-pdf-converter/
├── assets/                  # Icons and images
├── templates/               # HTML templates and CSS themes
│   ├── base.html
│   ├── theme_modern.css
│   ├── theme_classic.css
│   ├── theme_presentation.css
│   ├── pygments.css
│   └── pygments_dark.css
├── src/
│   ├── core/                # Business logic
│   │   ├── parser.py        # Markdown parser
│   │   ├── renderer.py      # PDF generator
│   │   ├── docx_renderer.py # DOCX export
│   │   ├── epub_renderer.py # EPUB export
│   │   ├── pptx_renderer.py # PPTX export
│   │   ├── image_renderer.py# PNG/JPG export
│   │   ├── reveal_exporter.py# Reveal.js export
│   │   ├── pdf_encrypt.py   # PDF encryption
│   │   ├── pdf_to_markdown.py# PDF extraction
│   │   ├── linter.py        # Markdown linter
│   │   ├── snippets.py      # Code snippets
│   │   ├── tts_engine.py    # Text-to-speech
│   │   ├── ocr_engine.py    # OCR
│   │   ├── ai_assistant.py  # Writing assistant
│   │   ├── flashcards.py    # Flashcards
│   │   ├── citation_manager.py# Citations
│   │   ├── glossary.py      # Auto-glossary
│   │   ├── quiz_generator.py# Quiz generator
│   │   ├── latex_preview.py # LaTeX preview
│   │   ├── html_to_markdown.py# HTML conversion
│   │   ├── wikilinks.py     # Wiki links
│   │   ├── cloud_templates.py# Cloud templates
│   │   ├── github_sync.py   # Git operations
│   │   ├── plugin_system.py # Plugin system
│   │   ├── template_vars.py # Template variables
│   │   ├── multi_export.py  # Batch export
│   │   └── config.py        # App config
│   └── gui/                 # PyQt6 interface
│       ├── main_window.py   # Main window (494+ methods)
│       ├── ui_layout.py     # UI layout
│       ├── dialogs.py       # All dialogs
│       ├── translations.py  # RU/EN localization
│       ├── highlighter.py   # Syntax highlighting
│       ├── models.py        # Data models
│       ├── threads.py       # Background threads
│       ├── toast.py         # Toast notifications
│       └── ...              # 20+ GUI modules
├── plugins/                 # User plugins
├── weasyprint-windows/      # Bundled WeasyPrint
├── main.py                  # Entry point
├── build.py                 # Build script
├── installer.iss            # Inno Setup installer
├── requirements.txt
└── LICENSE
```

## Building

### Executable
```bash
python build.py
```

### Installer
Open `installer.iss` in Inno Setup Compiler and press F9.

## License

MIT License - see [LICENSE](LICENSE) file.
