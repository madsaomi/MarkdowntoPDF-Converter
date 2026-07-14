LIGHT_STYLE = """
QMainWindow { background: #ffffff; }
QWidget { color: #1e293b; font-family: 'Segoe UI', system-ui, sans-serif; }
QLabel { color: #1e293b; }
QLineEdit, QTextEdit, QTextBrowser {
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 10px; color: #1e293b;
    selection-background-color: #bfdbfe;
}
QLineEdit:focus, QTextEdit:focus { border: 1px solid #3b82f6; }
QComboBox {
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 4px 8px; color: #1e293b;
}
QComboBox:hover { border-color: #3b82f6; }
QComboBox QAbstractItemView {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 4px;
    selection-background-color: #bfdbfe; selection-color: #1e293b;
}
QGroupBox { font-weight: 600; border: 1px solid #e2e8f0; border-radius: 8px; margin-top: 10px; padding-top: 14px; color: #64748b; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 6px; }
QProgressBar { border: none; background: #f1f5f9; border-radius: 2px; text-align: center; }
QProgressBar::chunk { background: #3b82f6; border-radius: 2px; }
QMenuBar { background: #ffffff; color: #1e293b; border-bottom: 1px solid #e2e8f0; padding: 2px; }
QMenuBar::item { padding: 4px 10px; border-radius: 4px; }
QMenuBar::item:selected { background: #f1f5f9; }
QMenu { background: #ffffff; color: #1e293b; border: 1px solid #e2e8f0; border-radius: 8px; padding: 4px; }
QMenu::item { padding: 6px 24px 6px 12px; border-radius: 4px; }
QMenu::item:selected { background: #f1f5f9; }
QMenu::separator { height: 1px; background: #e2e8f0; margin: 4px 8px; }
QTabWidget::pane { border: 1px solid #e2e8f0; border-radius: 6px; background: transparent; }
QTabBar::tab { background: transparent; border: none; padding: 6px 14px; color: #64748b; font-weight: 500; }
QTabBar::tab:selected { color: #1e293b; border-bottom: 2px solid #3b82f6; }
QTabBar::tab:hover:!selected { color: #475569; }
QScrollBar:vertical { background: transparent; width: 6px; margin: 0; }
QScrollBar::handle:vertical { background: #e2e8f0; border-radius: 3px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: #cbd5e1; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 6px; }
QScrollBar::handle:horizontal { background: #e2e8f0; border-radius: 3px; min-width: 24px; }
QToolTip { background: #1e293b; color: #f8fafc; border: none; border-radius: 4px; padding: 4px 8px; font-size: 11px; }
QSplitter::handle { background: #e2e8f0; }
QSplitter::handle:hover { background: #3b82f6; }
"""

DARK_STYLE = """
QMainWindow { background: #0f172a; }
QWidget { color: #e2e8f0; font-family: 'Segoe UI', system-ui, sans-serif; }
QLabel { color: #e2e8f0; }
QLineEdit, QTextEdit, QTextBrowser {
    background: #1e293b; border: 1px solid rgba(255,255,255,0.06); border-radius: 6px; padding: 6px 10px; color: #e2e8f0;
    selection-background-color: #3b82f6;
}
QLineEdit:focus, QTextEdit:focus { border: 1px solid #3b82f6; }
QComboBox {
    background: #1e293b; border: 1px solid rgba(255,255,255,0.06); border-radius: 6px; padding: 4px 8px; color: #e2e8f0;
}
QComboBox:hover { border-color: #3b82f6; }
QComboBox QAbstractItemView {
    background: #1e293b; border: 1px solid rgba(255,255,255,0.06); border-radius: 6px; padding: 4px;
    color: #e2e8f0; selection-background-color: #3b82f6; selection-color: #ffffff;
}
QGroupBox { font-weight: 600; border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; margin-top: 10px; padding-top: 14px; color: #64748b; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 6px; }
QProgressBar { border: none; background: rgba(255,255,255,0.04); border-radius: 2px; text-align: center; }
QProgressBar::chunk { background: #3b82f6; border-radius: 2px; }
QMenuBar { background: #0f172a; color: #e2e8f0; border-bottom: 1px solid rgba(255,255,255,0.04); padding: 2px; }
QMenuBar::item { padding: 4px 10px; border-radius: 4px; }
QMenuBar::item:selected { background: rgba(255,255,255,0.06); }
QMenu { background: #1e293b; color: #e2e8f0; border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 4px; }
QMenu::item { padding: 6px 24px 6px 12px; border-radius: 4px; }
QMenu::item:selected { background: rgba(59,130,246,0.15); }
QMenu::separator { height: 1px; background: rgba(255,255,255,0.06); margin: 4px 8px; }
QTabWidget::pane { border: 1px solid rgba(255,255,255,0.04); border-radius: 6px; background: transparent; }
QTabBar::tab { background: transparent; border: none; padding: 6px 14px; color: #64748b; font-weight: 500; }
QTabBar::tab:selected { color: #e2e8f0; border-bottom: 2px solid #3b82f6; }
QTabBar::tab:hover:!selected { color: #94a3b8; }
QScrollBar:vertical { background: transparent; width: 6px; margin: 0; }
QScrollBar::handle:vertical { background: rgba(255,255,255,0.08); border-radius: 3px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: rgba(255,255,255,0.15); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 6px; }
QScrollBar::handle:horizontal { background: rgba(255,255,255,0.08); border-radius: 3px; min-width: 24px; }
QToolTip { background: #1e293b; color: #e2e8f0; border: 1px solid rgba(255,255,255,0.06); border-radius: 4px; padding: 4px 8px; font-size: 11px; }
QSplitter::handle { background: rgba(255,255,255,0.06); }
QSplitter::handle:hover { background: #3b82f6; }
"""
