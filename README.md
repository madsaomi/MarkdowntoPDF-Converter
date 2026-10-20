# Markdown to PDF Converter Pro

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)
![WeasyPrint](https://img.shields.io/badge/PDF_Engine-WeasyPrint-red.svg)
![Tests](https://github.com/user/markdown-to-pdf-converter/actions/workflows/test.yml/badge.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

Desktop application for converting Markdown to PDF, DOCX, HTML, EPUB, PPTX, PNG, JPG with live preview.

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

## Export Formats

| Format | Engine | Notes |
|--------|--------|-------|
| PDF | WeasyPrint | Professional typography, CJK support |
| DOCX | python-docx | With reference template support |
| HTML | Jinja2 | Standalone HTML with full CSS |
| EPUB | ebooklib | E-book format |
| PPTX | python-pptx | PowerPoint presentations |
| Reveal.js | Built-in | HTML presentations |
| PNG/JPG | WeasyPrint + PyMuPDF | Image export |

## Features

### Editor
- Split view: Markdown editor + live preview (500ms debounce)
- Syntax highlighting (Markdown + code blocks)
- Minimal toolbar: B, I, H1, H2, code, quote, list, page break
- Search & Replace (Ctrl+F, RegEx support)
- Auto-closing brackets and quotes
- Multi-cursor editing

### PDF
- Page themes: modern, classic, presentation, dark
- Code highlighting: light (Tango) / dark (Monokai)
- Custom CSS stylesheets
- Watermark + footer with variables (`{date}`, `{filename}`, `{title}`, `{word_count}`)
- Encryption with password
- Page numbers (simple 1, slash 1/5, text "Page 1 of 5")
- PDF compression

### Tools
- Markdown linter (8 rules)
- LaTeX formula preview (via CodeCogs)
- HTML to Markdown converter
- Flashcards, Quiz generator, Glossary builder
- Citation manager (APA/MLA)
- TTS (text-to-speech, 22 voices)
- OCR (image to text via Tesseract)
- PDF to Markdown extraction
- Wiki links `[[wikilinks]]` + knowledge graph
- Cloud templates (built-in + GitHub)
- GitHub sync (init, commit, push, pull, log)
- Drawing canvas (Excalidraw SVG)
- CSV/TSV table editor
- Calendar notes view
- Pomodoro timer
- Watermark designer
- Multi-export (batch to multiple formats)

### UI
- Minimal design: editor + preview, toolbar with essentials
- Dark/light themes
- Toast notifications
- Zen mode (fullscreen, hide chrome)
- Focus mode (hide toolbar)
- Typewriter mode
- WYSIWYG toggle (hide editor, show preview only)
- Feature tour on first launch
- Drag & drop files/folders
- Export history (last 5 files)

### Internationalization
- Russian and English interfaces
- Switch language without restart

## CLI Mode

Run without GUI for automation (PyQt6 not required):

```bash
python main.py input.md -f pdf --theme modern -p "password"
python main.py input.md -f png --page-numbers
python main.py doc1.md doc2.md --theme classic
```

Full CLI arguments: `python main.py --help`

## Project Structure

```
src/
├── core/                          # Business logic
│   ├── config.py                  # Paths, cache, app data
│   ├── parser.py                  # MD→HTML with XSS/SSRF sanitization
│   ├── renderer.py                # PDF via WeasyPrint subprocess
│   ├── docx_renderer.py           # DOCX export
│   ├── epub_renderer.py           # EPUB export
│   ├── pptx_renderer.py           # PPTX export
│   ├── image_renderer.py          # PNG/JPG via WeasyPrint+PyMuPDF
│   ├── reveal_exporter.py         # Reveal.js export
│   ├── pdf_encrypt.py             # PDF password encryption
│   ├── pdf_to_markdown.py         # PDF text extraction
│   ├── linter.py                  # 8 Markdown lint rules
│   ├── tts_engine.py              # Text-to-speech (22 voices)
│   ├── ocr_engine.py              # OCR via Tesseract
│   ├── ai_assistant.py            # Style/grammar checker
│   ├── flashcards.py              # Flashcard extraction
│   ├── citation_manager.py        # BibTeX citations
│   ├── glossary.py                # Auto-glossary builder
│   ├── quiz_generator.py          # Quiz from headings
│   ├── latex_preview.py           # LaTeX to CodeCogs URL
│   ├── html_to_markdown.py        # HTML→MD converter
│   ├── wikilinks.py               # [[links]] + graph view
│   ├── cloud_templates.py         # Remote template fetcher
│   ├── github_sync.py             # Git operations
│   ├── plugin_system.py           # Plugin loader
│   ├── template_vars.py           # {{variable}} substitution
│   └── multi_export.py            # Batch export
└── gui/                           # PyQt6 interface
    ├── main_window.py             # (~1330 lines)
    ├── window_tools.py            # Tool methods mixin (~746 lines)
    ├── ui_layout.py               # Minimal UI layout (~496 lines)
    ├── styles.py                  # Clean light/dark themes (~162 lines)
    ├── dialogs.py                 # All dialogs
    ├── translations.py            # RU/EN (205 keys each)
    ├── highlighter.py             # Syntax highlighting
    ├── models.py                  # Data models
    ├── threads.py                 # Background threads
    ├── toast.py                   # Toast notifications
    ├── editor_commands.py         # Editor formatting
    ├── file_manager.py            # File operations
    ├── preview_manager.py         # Live preview
    ├── document_tools.py          # Document utilities
    ├── templates_data.py          # Built-in templates
    └── ...                        # Other GUI modules
tests/                             # 77 tests (pytest)
├── test_parser.py                 # 14 parser tests
├── test_linter.py                 # 8 linter tests
├── test_translations.py           # 5 translation tests
├── test_core.py                   # 11 core module tests
├── test_ai_assistant.py           # 14 AI tests
├── test_wikilinks.py              # 8 wikilinks tests
├── test_template_vars.py          # 10 template var tests
└── run_all.py                     # Test runner
```

## PDF Engine (WeasyPrint)

PDF/PNG/JPG export needs the WeasyPrint engine. Resolution order:

1. **Portable `weasyprint.exe`** in `weasyprint-windows/dist/` (priority; the only option for frozen `.exe` builds).
2. **pip package** `weasyprint` (`python -m weasyprint`) — for development on a clean clone; on Windows also requires GTK3 ([install guide](https://doc.courtbouillon.org/weasyprint/stable/first_install.html)).

Run the built-in diagnostics/setup script:

```powershell
powershell -ExecutionPolicy Bypass -File setup_pdf_engine.ps1
```

## Build

```bash
python build.py                          # PyInstaller .exe (requires weasyprint.exe, see above)
python build.py --console                # with console for debugging
python build.py --skip-pdf-engine        # build WITHOUT PDF support
```

`build.py` stops with a clear error if `weasyprint-windows/dist/weasyprint.exe` is missing, because a frozen build cannot use the pip fallback.

## Tests

```bash
python -m pytest tests/ -q       # pytest (69 tests)
python tests/run_all.py           # custom runner
```

## Requirements

- Python 3.10+
- PyQt6, WeasyPrint, python-markdown, pymdown-extensions, Jinja2, Pygments
- See `requirements.txt` or `pyproject.toml` for full list

## License

MIT License - see [LICENSE](LICENSE) file.
