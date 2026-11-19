"""Temas (claro/escuro) e estilos modernos."""
from PySide6.QtWidgets import QApplication

DARK_QSS = r"""
* { font-family: "Inter", "Segoe UI", "Ubuntu", sans-serif; font-size: 13px; }
QMainWindow, QWidget { background: #0f1115; color: #e6e8eb; }
QTabWidget::pane { border: 1px solid #2a2f3a; border-radius: 10px; background: #151821; margin-top: 6px; }
QTabBar::tab { background: #1c202b; color: #9aa3b2; padding: 8px 16px; margin-right: 4px; border-top-left-radius: 8px; border-top-right-radius: 8px; }
QTabBar::tab:selected { background: #252a36; color: #ffffff; font-weight: 600; }
QTabBar::tab:hover { background: #232836; color: #ffffff; }
QGroupBox { border: 1px solid #2a2f3a; border-radius: 10px; margin-top: 12px; padding: 12px; font-weight: 600; color: #c9d1d9; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #7aa2f7; }
QLineEdit, QTextEdit, QComboBox, QSpinBox, QListWidget, QTableWidget { background: #1c202b; border: 1px solid #2a2f3a; border-radius: 8px; padding: 6px 8px; color: #e6e8eb; selection-background-color: #3b82f6; }
QLineEdit:focus, QTextEdit:focus, QComboBox:focus { border: 1px solid #3b82f6; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView { background: #1c202b; border: 1px solid #2a2f3a; selection-background-color: #3b82f6; color: #e6e8eb; }
QPushButton { background: #252a36; color: #e6e8eb; border: 1px solid #2a2f3a; border-radius: 8px; padding: 8px 14px; font-weight: 600; }
QPushButton:hover { background: #2f3545; border-color: #3b82f6; }
QPushButton:pressed { background: #1c202b; }
QPushButton:disabled { background: #151821; color: #5a6270; border-color: #1f2330; }
QPushButton#primary { background: #3b82f6; color: #ffffff; border: none; }
QPushButton#primary:hover { background: #2563eb; }
QPushButton#primary:disabled { background: #1e3a6e; color: #8aa0c8; }
QPushButton#danger { background: #ef4444; color: #ffffff; border: none; }
QPushButton#danger:hover { background: #dc2626; }
QHeaderView::section { background: #1c202b; color: #9aa3b2; padding: 8px; border: none; border-bottom: 1px solid #2a2f3a; font-weight: 600; }
QTableWidget { gridline-color: #2a2f3a; alternate-background-color: #181b24; }
QTableWidget::item { padding: 6px; }
QTableWidget::item:selected { background: #253248; color: #ffffff; }
QListWidget::item { padding: 6px; border-radius: 6px; }
QListWidget::item:selected { background: #253248; color: #ffffff; }
QListWidget::item:hover { background: #1f2330; }
QProgressBar { background: #1c202b; border: 1px solid #2a2f3a; border-radius: 8px; text-align: center; color: #e6e8eb; height: 18px; }
QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #3b82f6, stop:1 #8b5cf6); border-radius: 7px; }
QScrollBar:vertical { background: #0f1115; width: 12px; margin: 0; }
QScrollBar::handle:vertical { background: #2a2f3a; border-radius: 6px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: #3b82f6; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QLabel#title { font-size: 18px; font-weight: 700; color: #ffffff; }
QLabel#subtitle { color: #9aa3b2; font-size: 12px; }
QToolTip { background: #1c202b; color: #e6e8eb; border: 1px solid #2a2f3a; border-radius: 6px; padding: 4px; }
"""

LIGHT_QSS = r"""
* { font-family: "Inter", "Segoe UI", "Ubuntu", sans-serif; font-size: 13px; }
QMainWindow, QWidget { background: #f5f7fa; color: #1f2937; }
QTabWidget::pane { border: 1px solid #e2e8f0; border-radius: 10px; background: #ffffff; margin-top: 6px; }
QTabBar::tab { background: #edf0f5; color: #64748b; padding: 8px 16px; margin-right: 4px; border-top-left-radius: 8px; border-top-right-radius: 8px; }
QTabBar::tab:selected { background: #ffffff; color: #1f2937; font-weight: 600; }
QTabBar::tab:hover { background: #e8ecf3; color: #1f2937; }
QGroupBox { border: 1px solid #e2e8f0; border-radius: 10px; margin-top: 12px; padding: 12px; font-weight: 600; color: #334155; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #2563eb; }
QLineEdit, QTextEdit, QComboBox, QSpinBox, QListWidget, QTableWidget { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px 8px; color: #1f2937; selection-background-color: #3b82f6; }
QLineEdit:focus, QTextEdit:focus, QComboBox:focus { border: 1px solid #3b82f6; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView { background: #ffffff; border: 1px solid #e2e8f0; selection-background-color: #3b82f6; color: #1f2937; }
QPushButton { background: #ffffff; color: #1f2937; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 14px; font-weight: 600; }
QPushButton:hover { background: #f1f5f9; border-color: #3b82f6; }
QPushButton:pressed { background: #e2e8f0; }
QPushButton:disabled { background: #f8fafc; color: #94a3b8; border-color: #e2e8f0; }
QPushButton#primary { background: #3b82f6; color: #ffffff; border: none; }
QPushButton#primary:hover { background: #2563eb; }
QPushButton#primary:disabled { background: #93c5fd; color: #ffffff; }
QPushButton#danger { background: #ef4444; color: #ffffff; border: none; }
QPushButton#danger:hover { background: #dc2626; }
QHeaderView::section { background: #f1f5f9; color: #64748b; padding: 8px; border: none; border-bottom: 1px solid #e2e8f0; font-weight: 600; }
QTableWidget { gridline-color: #e2e8f0; alternate-background-color: #f8fafc; }
QTableWidget::item { padding: 6px; }
QTableWidget::item:selected { background: #dbeafe; color: #1f2937; }
QListWidget::item { padding: 6px; border-radius: 6px; }
QListWidget::item:selected { background: #dbeafe; color: #1f2937; }
QListWidget::item:hover { background: #f1f5f9; }
QProgressBar { background: #e2e8f0; border: 1px solid #e2e8f0; border-radius: 8px; text-align: center; color: #1f2937; height: 18px; }
QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #3b82f6, stop:1 #8b5cf6); border-radius: 7px; }
QScrollBar:vertical { background: #f5f7fa; width: 12px; margin: 0; }
QScrollBar::handle:vertical { background: #cbd5e1; border-radius: 6px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: #3b82f6; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QLabel#title { font-size: 18px; font-weight: 700; color: #0f172a; }
QLabel#subtitle { color: #64748b; font-size: 12px; }
QToolTip { background: #ffffff; color: #1f2937; border: 1px solid #e2e8f0; border-radius: 6px; padding: 4px; }
"""


def apply_theme(app, theme: str):
    qss = DARK_QSS if theme == "dark" else LIGHT_QSS
    app.setStyleSheet(qss)
    app.setProperty("theme", theme)
