LIGHT_STYLE = """
/* ── Glassmorphism Light Theme (2026) ── */
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #e8eaf6, stop:0.3 #f3e5f5, stop:0.6 #e0f7fa, stop:1 #e8f5e9);
}
QWidget {
    background-color: transparent;
    color: #1a1a2e;
    font-family: 'Segoe UI', 'SF Pro Display', -apple-system, sans-serif;
}
QLabel {
    color: #1a1a2e;
    font-size: 13px;
}
QLabel[styleSheet*="font-size: 18px"] {
    color: #1a1a2e;
}
/* ── Glassmorphism inputs ── */
QLineEdit, QTextEdit, QTextBrowser {
    background-color: rgba(255, 255, 255, 0.72);
    border: 1px solid rgba(255, 255, 255, 0.5);
    border-radius: 10px;
    padding: 8px 12px;
    color: #1a1a2e;
    selection-background-color: rgba(99, 102, 241, 0.3);
}
QLineEdit:focus, QTextEdit:focus {
    border: 1.5px solid rgba(99, 102, 241, 0.5);
    background-color: rgba(255, 255, 255, 0.85);
}
/* ── Glassmorphism ComboBox ── */
QComboBox {
    background-color: rgba(255, 255, 255, 0.72);
    border: 1px solid rgba(255, 255, 255, 0.5);
    border-radius: 10px;
    padding: 6px 12px;
    color: #1a1a2e;
    font-weight: 500;
}
QComboBox:hover {
    background-color: rgba(255, 255, 255, 0.85);
    border-color: rgba(99, 102, 241, 0.3);
}
QComboBox QAbstractItemView {
    background-color: rgba(255, 255, 255, 0.95);
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 8px;
    padding: 4px;
    selection-background-color: rgba(99, 102, 241, 0.15);
    selection-color: #1a1a2e;
    outline: none;
}
/* ── Glassmorphism GroupBox ── */
QGroupBox {
    font-weight: 600;
    border: 1px solid rgba(255, 255, 255, 0.4);
    border-radius: 12px;
    margin-top: 14px;
    padding-top: 18px;
    color: #1a1a2e;
    background-color: rgba(255, 255, 255, 0.35);
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 8px;
    color: #4a4a6a;
}
/* ── Progress bar ── */
QProgressBar {
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 6px;
    background-color: rgba(255, 255, 255, 0.5);
    height: 8px;
    text-align: center;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366f1, stop:1 #8b5cf6);
    border-radius: 5px;
}
/* ── Menu bar ── */
QMenuBar {
    background-color: rgba(255, 255, 255, 0.6);
    color: #1a1a2e;
    border-bottom: 1px solid rgba(0, 0, 0, 0.06);
    font-weight: 500;
}
QMenuBar::item {
    padding: 6px 10px;
    border-radius: 6px;
}
QMenuBar::item:selected {
    background-color: rgba(99, 102, 241, 0.1);
}
QMenu {
    background-color: rgba(255, 255, 255, 0.92);
    color: #1a1a2e;
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 10px;
    padding: 6px;
}
QMenu::item {
    padding: 7px 24px 7px 12px;
    border-radius: 6px;
}
QMenu::item:selected {
    background-color: rgba(99, 102, 241, 0.12);
}
/* ── Tab widget ── */
QTabWidget::pane {
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 10px;
    background-color: rgba(255, 255, 255, 0.4);
    top: -1px;
}
QTabBar::tab {
    background-color: rgba(255, 255, 255, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.3);
    padding: 8px 18px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    color: #6b7280;
    font-weight: 500;
}
QTabBar::tab:selected {
    background-color: rgba(255, 255, 255, 0.85);
    color: #1a1a2e;
    font-weight: 600;
    border-bottom: 2px solid #6366f1;
}
QTabBar::tab:hover:!selected {
    background-color: rgba(255, 255, 255, 0.7);
}
/* ── Scrollbar ── */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: rgba(0, 0, 0, 0.15);
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(0, 0, 0, 0.25);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: transparent;
    height: 8px;
}
QScrollBar::handle:horizontal {
    background: rgba(0, 0, 0, 0.15);
    border-radius: 4px;
    min-width: 30px;
}
/* ── Tooltips ── */
QToolTip {
    background-color: rgba(26, 26, 46, 0.9);
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12px;
}
/* ── Splitter ── */
QSplitter::handle {
    background-color: rgba(0, 0, 0, 0.06);
    width: 2px;
}
QSplitter::handle:hover {
    background-color: rgba(99, 102, 241, 0.3);
}
"""

DARK_STYLE = """
/* ── Dark Glassmorphism Theme (2026) ── */
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0f0f1a, stop:0.25 #1a0f2e, stop:0.5 #0f1a2e, stop:0.75 #0f2e1a, stop:1 #1a1a2e);
}
QWidget {
    background-color: transparent;
    color: #e2e8f0;
    font-family: 'Segoe UI', 'SF Pro Display', -apple-system, sans-serif;
}
QLabel {
    color: #e2e8f0;
    font-size: 13px;
}
/* ── Dark glassmorphism inputs ── */
QLineEdit, QTextEdit, QTextBrowser {
    background-color: rgba(30, 30, 50, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 8px 12px;
    color: #e2e8f0;
    selection-background-color: rgba(139, 92, 246, 0.35);
}
QLineEdit:focus, QTextEdit:focus {
    border: 1.5px solid rgba(139, 92, 246, 0.5);
    background-color: rgba(30, 30, 50, 0.8);
}
/* ── Dark glassmorphism ComboBox ── */
QComboBox {
    background-color: rgba(30, 30, 50, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 6px 12px;
    color: #e2e8f0;
    font-weight: 500;
}
QComboBox:hover {
    background-color: rgba(40, 40, 65, 0.8);
    border-color: rgba(139, 92, 246, 0.3);
}
QComboBox QAbstractItemView {
    background-color: rgba(20, 20, 35, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    padding: 4px;
    color: #e2e8f0;
    selection-background-color: rgba(139, 92, 246, 0.2);
    selection-color: #f0f0ff;
    outline: none;
}
/* ── Dark glassmorphism GroupBox ── */
QGroupBox {
    font-weight: 600;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
    margin-top: 14px;
    padding-top: 18px;
    color: #e2e8f0;
    background-color: rgba(30, 30, 50, 0.35);
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 8px;
    color: #a0a0c0;
}
/* ── Dark progress bar ── */
QProgressBar {
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 6px;
    background-color: rgba(30, 30, 50, 0.5);
    height: 8px;
    text-align: center;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #8b5cf6, stop:1 #06b6d4);
    border-radius: 5px;
}
/* ── Dark menu bar ── */
QMenuBar {
    background-color: rgba(15, 15, 26, 0.7);
    color: #e2e8f0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    font-weight: 500;
}
QMenuBar::item {
    padding: 6px 10px;
    border-radius: 6px;
}
QMenuBar::item:selected {
    background-color: rgba(139, 92, 246, 0.12);
}
QMenu {
    background-color: rgba(20, 20, 35, 0.92);
    color: #e2e8f0;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    padding: 6px;
}
QMenu::item {
    padding: 7px 24px 7px 12px;
    border-radius: 6px;
}
QMenu::item:selected {
    background-color: rgba(139, 92, 246, 0.15);
}
/* ── Dark tab widget ── */
QTabWidget::pane {
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    background-color: rgba(20, 20, 35, 0.4);
    top: -1px;
}
QTabBar::tab {
    background-color: rgba(30, 30, 50, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.06);
    padding: 8px 18px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    color: #6b7280;
    font-weight: 500;
}
QTabBar::tab:selected {
    background-color: rgba(30, 30, 50, 0.8);
    color: #e2e8f0;
    font-weight: 600;
    border-bottom: 2px solid #8b5cf6;
}
QTabBar::tab:hover:!selected {
    background-color: rgba(40, 40, 65, 0.6);
}
/* ── Dark scrollbar ── */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(255, 255, 255, 0.2);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: transparent;
    height: 8px;
}
QScrollBar::handle:horizontal {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    min-width: 30px;
}
/* ── Dark tooltips ── */
QToolTip {
    background-color: rgba(30, 30, 50, 0.95);
    color: #e2e8f0;
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12px;
}
/* ── Dark splitter ── */
QSplitter::handle {
    background-color: rgba(255, 255, 255, 0.04);
    width: 2px;
}
QSplitter::handle:hover {
    background-color: rgba(139, 92, 246, 0.3);
}
"""
