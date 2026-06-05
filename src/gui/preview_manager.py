"""Live preview rendering, zoom, scroll sync, print, and HTML copy."""

import os
import logging
from PyQt6.QtWidgets import QApplication

logger = logging.getLogger("MarkdownToPDF.preview_manager")


def render_live_preview(window):
    md_text = window.live_editor.toPlainText()
    if not md_text:
        return
    try:
        from src.core.parser import MarkdownParser

        is_pres = window.chk_presentation_mode.isChecked()
        parser = MarkdownParser()
        html, _ = parser.parse(
            md_text,
            base_dir=window.get_current_document_dir(),
            is_presentation=is_pres,
            kroki_available=window.kroki_available
        )

        if is_pres:
            preview_html = f"""
            <html><head><style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #111827;
                margin: 0;
                padding: 20px;
                display: flex;
                flex-direction: column;
                align-items: center;
            }}
            .slide {{
                width: 90%;
                max-width: 800px;
                aspect-ratio: 16 / 9;
                background: linear-gradient(135deg, #1e1b4b 0%, #311042 100%);
                color: #f1f5f9;
                margin-bottom: 20px;
                padding: 40px;
                box-sizing: border-box;
                border-radius: 12px;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: flex-start;
                position: relative;
                overflow: hidden;
            }}
            .slide::after {{
                content: "";
                position: absolute;
                bottom: 0;
                left: 0;
                width: 100%;
                height: 4px;
                background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
            }}
            .slide h1 {{ font-size: 28pt; color: #fbbf24; margin: 0 0 10px 0; font-weight: 800; border: none; }}
            .slide h2 {{ font-size: 20pt; color: #38bdf8; margin: 0 0 10px 0; font-weight: 700; border: none; }}
            .slide p, .slide li {{ font-size: 13pt; line-height: 1.6; color: #cbd5e1; }}
            .slide blockquote {{
                margin: 10px 0;
                padding: 10px 15px;
                border-left: 4px solid #a855f7;
                background: rgba(168, 85, 247, 0.08);
                border-radius: 0 8px 8px 0;
            }}
            .slide blockquote p {{ font-style: italic; color: #e9d5ff; }}
            .slide pre, .slide .codehilite {{
                background: rgba(15, 23, 42, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 10px 15px;
                width: 100%;
                box-sizing: border-box;
            }}
            .slide code {{
                background: rgba(15, 23, 42, 0.6);
                padding: 2px 4px;
                border-radius: 4px;
                color: #38bdf8;
            }}
            .slide pre code {{ background: transparent; color: inherit; }}
            .slide img {{ max-width: 100%; max-height: 250px; height: auto; }}
            </style></head><body>{html}</body></html>
            """
        else:
            if getattr(window, 'is_dark', False):
                preview_html = f"""
                <html><head><style>
                body {{ font-family: 'Segoe UI', sans-serif; color: #e2e8f0; background: rgba(30, 41, 59, 0.95);
                        padding: 16px; line-height: 1.7; }}
                h1, h2, h3, h4, h5, h6 {{ color: #f1f5f9; margin-top: 1.2em; }}
                h1 {{ border-bottom: 2px solid rgba(99, 102, 241, 0.4); padding-bottom: 6px; }}
                h2 {{ border-bottom: 1px solid rgba(99, 102, 241, 0.2); padding-bottom: 4px; }}
                a {{ color: #818cf8; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                pre {{ background: rgba(15, 23, 42, 0.7); padding: 14px; border-radius: 8px; white-space: pre-wrap;
                       word-wrap: break-word; border: 1px solid rgba(255,255,255,0.06); }}
                code {{ background: rgba(99, 102, 241, 0.12); padding: 2px 5px; border-radius: 4px; color: #a5b4fc; font-size: 0.92em; }}
                pre code {{ background: transparent; padding: 0; color: inherit; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th {{ background: rgba(51, 65, 85, 0.6); color: #cbd5e1; }}
                th, td {{ border: 1px solid rgba(255,255,255,0.08); padding: 8px 10px; }}
                tr:nth-child(even) {{ background: rgba(51, 65, 85, 0.2); }}
                blockquote {{ border-left: 4px solid #6366f1; background: rgba(99, 102, 241, 0.06); padding: 10px 16px;
                              margin: 1em 0; border-radius: 0 8px 8px 0; color: #94a3b8; }}
                img {{ max-width: 100%; height: auto; border-radius: 8px; }}
                hr {{ border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 1.5em 0; }}
                ul, ol {{ padding-left: 1.5em; }}
                li {{ margin: 4px 0; }}
                </style></head><body>{html}</body></html>
                """
            else:
                preview_html = f"""
                <html><head><style>
                body {{ font-family: 'Segoe UI', sans-serif; color: #1e293b; background: #ffffff;
                        padding: 16px; line-height: 1.7; }}
                h1, h2, h3, h4, h5, h6 {{ color: #0f172a; margin-top: 1.2em; }}
                h1 {{ border-bottom: 2px solid rgba(99, 102, 241, 0.3); padding-bottom: 6px; }}
                h2 {{ border-bottom: 1px solid rgba(99, 102, 241, 0.15); padding-bottom: 4px; }}
                a {{ color: #6366f1; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                pre {{ background: #f1f5f9; padding: 14px; border-radius: 8px; white-space: pre-wrap;
                       word-wrap: break-word; border: 1px solid #e2e8f0; }}
                code {{ background: rgba(99, 102, 241, 0.08); padding: 2px 5px; border-radius: 4px; color: #4f46e5; font-size: 0.92em; }}
                pre code {{ background: transparent; padding: 0; color: inherit; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th {{ background: #f1f5f9; color: #334155; font-weight: 600; }}
                th, td {{ border: 1px solid #e2e8f0; padding: 8px 10px; }}
                tr:nth-child(even) {{ background: #f8fafc; }}
                blockquote {{ border-left: 4px solid #6366f1; background: rgba(99, 102, 241, 0.04); padding: 10px 16px;
                              margin: 1em 0; border-radius: 0 8px 8px 0; color: #64748b; }}
                img {{ max-width: 100%; height: auto; border-radius: 8px; }}
                hr {{ border: none; border-top: 1px solid #e2e8f0; margin: 1.5em 0; }}
                ul, ol {{ padding-left: 1.5em; }}
                li {{ margin: 4px 0; }}
                </style></head><body>{html}</body></html>
                """
        window.preview_output.setHtml(preview_html)
    except Exception as e:
        logger.error("Live preview render failed: %s", e, exc_info=True)
        window.preview_output.setHtml(f"<p style='color:red;'>Preview error: {e}</p>")


def sync_scroll_preview(window, value):
    editor_scroll = window.live_editor.verticalScrollBar()
    max_editor = editor_scroll.maximum()
    if max_editor <= 0:
        return
    percentage = value / max_editor

    preview_scroll = window.preview_output.verticalScrollBar()
    max_preview = preview_scroll.maximum()
    preview_scroll.setValue(int(percentage * max_preview))


def zoom_in(window):
    window.live_editor.zoomIn(1)
    window.preview_output.zoomIn(1)
    window.zoom_level += 1


def zoom_out(window):
    window.live_editor.zoomOut(1)
    window.preview_output.zoomOut(1)
    window.zoom_level -= 1


def zoom_reset(window):
    if window.zoom_level > 0:
        window.live_editor.zoomOut(window.zoom_level)
        window.preview_output.zoomOut(window.zoom_level)
    elif window.zoom_level < 0:
        window.live_editor.zoomIn(-window.zoom_level)
        window.preview_output.zoomIn(-window.zoom_level)
    window.zoom_level = 0


def print_document(window):
    from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
    render_live_preview(window)
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    dialog = QPrintDialog(printer, window)
    if dialog.exec() == QPrintDialog.DialogCode.Accepted:
        window.preview_output.print(printer)


def copy_styled_html(window):
    html_content = window.preview_output.toHtml()
    clipboard = QApplication.clipboard()
    clipboard.setText(html_content)
    from PyQt6.QtWidgets import QMessageBox
    QMessageBox.information(
        window,
        window.tr_msg("msg_html_copied_title"),
        window.tr_msg("msg_html_copied_desc")
    )
