from __future__ import annotations


COLORS = {
    "bg": "#101418",
    "panel": "#171D22",
    "panel_alt": "#1E252B",
    "panel_alt_2": "#263039",
    "panel_border": "#33404A",
    "text": "#F2F5F7",
    "muted": "#A6B1BA",
    "accent": "#2D9CDB",
    "accent_hover": "#45ACE7",
    "success": "#62BE7B",
    "warning": "#E8B84D",
    "danger": "#E85D75",
    "danger_soft": "#D94E66",
    "info": "#43A5E6",
    "selection": "#213241",
    "disabled": "#596570",
}


def get_stylesheet() -> str:
    c = COLORS
    return f"""
    QMainWindow {{
        background-color: {c['bg']};
        color: {c['text']};
        font-family: "Segoe UI";
        font-size: 10pt;
    }}
    QWidget {{
        color: {c['text']};
        font-family: "Segoe UI";
        font-size: 10pt;
    }}
    QWidget#app_root, QWidget#app_shell, QStackedWidget#content_stack {{
        background-color: {c['bg']};
    }}
    QFrame#sidebar {{
        background-color: {c['panel_alt']};
        border: 1px solid {c['panel_border']};
        border-radius: 8px;
    }}
    QFrame#card {{
        background-color: {c['panel']};
        border: 1px solid {c['panel_border']};
        border-radius: 8px;
    }}
    QFrame#panel {{
        background-color: {c['panel_alt']};
        border: 1px solid {c['panel_border']};
        border-radius: 6px;
    }}
    QPushButton#nav_button {{
        background-color: transparent;
        color: {c['muted']};
        border: none;
        border-radius: 6px;
        padding: 9px 14px;
        text-align: left;
        font-size: 10pt;
    }}
    QPushButton#nav_button:hover {{
        background-color: {c['panel_alt_2']};
        color: {c['text']};
    }}
    QPushButton#nav_button[active="true"] {{
        background-color: {c['selection']};
        color: {c['text']};
        font-weight: 600;
        border-left: 3px solid {c['accent']};
    }}
    QPushButton {{
        background-color: {c['accent']};
        color: #FFFFFF;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 10pt;
    }}
    QPushButton:hover {{
        background-color: {c['accent_hover']};
    }}
    QPushButton:disabled {{
        background-color: #303942;
        color: {c['muted']};
    }}
    QPushButton:focus, QLineEdit:focus, QComboBox:focus {{
        border: 1px solid {c['accent']};
    }}
    QPushButton#subtle {{
        background-color: {c['panel_alt']};
        color: {c['muted']};
        border: 1px solid {c['panel_border']};
    }}
    QPushButton#subtle:hover {{
        background-color: {c['panel_alt_2']};
        color: {c['text']};
    }}
    QPushButton#danger {{
        background-color: {c['danger']};
        color: #FFFFFF;
    }}
    QPushButton#danger:hover {{
        background-color: {c['danger_soft']};
    }}
    QPushButton#pill_button {{
        padding: 4px 10px;
    }}
    QTableWidget, QTreeWidget, QPlainTextEdit, QTextEdit {{
        background-color: {c['panel']};
        alternate-background-color: {c['panel_alt']};
        color: {c['text']};
        border: 1px solid {c['panel_border']};
        border-radius: 6px;
        gridline-color: {c['panel_border']};
        selection-background-color: {c['selection']};
        outline: none;
    }}
    QTableWidget::item, QTreeWidget::item {{
        padding: 4px 8px;
        border: none;
    }}
    QTableWidget::item:hover, QTreeWidget::item:hover {{
        background-color: {c['panel_alt_2']};
    }}
    QTableWidget::item:selected, QTreeWidget::item:selected {{
        background-color: {c['selection']};
        color: {c['text']};
    }}
    QHeaderView::section {{
        background-color: {c['panel_alt']};
        color: {c['muted']};
        border: none;
        border-bottom: 1px solid {c['panel_border']};
        padding: 6px 8px;
        font-size: 9pt;
        font-weight: 600;
    }}
    QTableCornerButton::section {{
        background-color: {c['panel_alt']};
        border: none;
    }}
    QScrollBar:vertical {{
        background: {c['bg']};
        width: 8px;
        border: none;
    }}
    QScrollBar:horizontal {{
        background: {c['bg']};
        height: 8px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background: {c['panel_border']};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:horizontal {{
        background: {c['panel_border']};
        border-radius: 4px;
        min-width: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {c['muted']};
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {c['muted']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        border: none;
        background: none;
    }}
    QScrollArea {{
        border: none;
        background-color: {c['bg']};
    }}
    QScrollArea > QWidget > QWidget {{
        background-color: {c['bg']};
    }}
    QComboBox {{
        background-color: {c['panel_alt']};
        color: {c['text']};
        border: 1px solid {c['panel_border']};
        border-radius: 6px;
        padding: 5px 10px;
        min-height: 20px;
    }}
    QComboBox::drop-down {{
        border: none;
    }}
    QComboBox QAbstractItemView {{
        background-color: {c['panel_alt']};
        color: {c['text']};
        selection-background-color: {c['selection']};
        border: 1px solid {c['panel_border']};
    }}
    QLineEdit {{
        background-color: {c['panel_alt']};
        color: {c['text']};
        border: 1px solid {c['panel_border']};
        border-radius: 6px;
        padding: 5px 10px;
        min-height: 20px;
    }}
    QLineEdit:focus {{
        border: 1px solid {c['accent']};
    }}
    QCheckBox {{
        color: {c['text']};
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {c['panel_border']};
        border-radius: 3px;
        background: {c['panel_alt']};
    }}
    QCheckBox::indicator:checked {{
        background: {c['accent']};
        border-color: {c['accent']};
    }}
    QLabel {{
        color: {c['text']};
        background: transparent;
    }}
    QLabel#muted {{
        color: {c['muted']};
        font-size: 9pt;
    }}
    QLabel#title {{
        font-size: 18pt;
        font-weight: 600;
    }}
    QLabel#subtitle {{
        font-size: 11pt;
        color: {c['muted']};
    }}
    QToolTip {{
        background-color: {c['panel_alt_2']};
        color: {c['text']};
        border: 1px solid {c['panel_border']};
        padding: 4px 8px;
    }}
    QGroupBox {{
        color: {c['muted']};
        border: 1px solid {c['panel_border']};
        border-radius: 6px;
        margin-top: 8px;
        padding: 14px 12px 12px 12px;
        font-size: 9pt;
        background-color: {c['panel']};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 6px;
        color: {c['text']};
        font-weight: 600;
        background-color: {c['bg']};
    }}
    QTabWidget::pane {{
        border: 1px solid {c['panel_border']};
        border-radius: 8px;
        background: {c['panel']};
    }}
    QTabBar::tab {{
        background: {c['panel_alt']};
        color: {c['muted']};
        padding: 8px 14px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        margin-right: 4px;
    }}
    QTabBar::tab:selected {{
        background: {c['selection']};
        color: {c['text']};
    }}
    QStatusBar {{
        background-color: {c['panel']};
        border-top: 1px solid {c['panel_border']};
    }}
    """
