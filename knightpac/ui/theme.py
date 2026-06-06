"""KnightPac visual theme — design tokens and global stylesheet."""

COLORS = {
    "bg": "#111111",
    "panel": "#181818",
    "panel_elevated": "#1E1E1E",
    "panel_soft": "#202020",
    "accent": "#D4A54C",
    "hover": "#E0B45C",
    "text": "#F0F0F0",
    "text_secondary": "#AAAAAA",
    "text_muted": "#777777",
    "error": "#D9534F",
    "success": "#5CB85C",
    "warning": "#F0AD4E",
    "info": "#5BC0DE",
    "border": "#2A2A2A",
    "border_light": "#333333",
    "selected_bg": "#1F1F1F",
    "terminal_bg": "#0D0D0D",
}

RADIUS = {"sm": 6, "md": 10, "lg": 16}

BADGE_VARIANTS = {
    "default": {"fg": COLORS["text_secondary"], "bg": "#1A1A1A", "border": COLORS["border"]},
    "official": {"fg": COLORS["accent"], "bg": "#2A2418", "border": COLORS["accent"]},
    "aur": {"fg": "#C9A0FF", "bg": "#221A2E", "border": "#9B59B6"},
    "installed": {"fg": COLORS["success"], "bg": "#152015", "border": COLORS["success"]},
    "flatpak": {"fg": "#7EB8FF", "bg": "#152030", "border": "#4A90D9"},
}

LOG_COLORS = {
    "INFO": COLORS["info"],
    "SUCCESS": COLORS["success"],
    "WARNING": COLORS["warning"],
    "ERROR": COLORS["error"],
    "DEFAULT": COLORS["text_secondary"],
}


def stylesheet() -> str:
    c = COLORS
    r = RADIUS
    return f"""
    QMainWindow, QWidget {{
        background-color: {c['bg']};
        color: {c['text']};
        font-family: "Segoe UI", "Noto Sans", "Ubuntu", sans-serif;
        font-size: 13px;
    }}
    QLineEdit, QComboBox, QTextEdit, QPlainTextEdit, QListWidget, QTreeWidget {{
        background-color: {c['panel']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: {r['md']}px;
        padding: 8px 12px;
        selection-background-color: {c['accent']};
        selection-color: #111111;
    }}
    QLineEdit:focus, QComboBox:focus {{
        border-color: {c['accent']};
        background-color: {c['panel_elevated']};
    }}
    QPushButton {{
        background-color: {c['panel_elevated']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: {r['md']}px;
        padding: 9px 16px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {c['panel_soft']};
        border-color: {c['hover']};
        color: {c['hover']};
    }}
    QPushButton#accentButton {{
        background-color: {c['accent']};
        color: #111111;
        border: none;
        font-weight: 600;
    }}
    QPushButton#accentButton:hover {{
        background-color: {c['hover']};
        color: #111111;
    }}
    QPushButton#ghostButton {{
        background: transparent;
        border: 1px solid {c['border_light']};
        color: {c['text_secondary']};
    }}
    QPushButton#ghostButton:hover {{
        border-color: {c['accent']};
        color: {c['accent']};
    }}
    QPushButton#dangerButton {{
        border-color: {c['error']};
        color: {c['error']};
        background: transparent;
    }}
    QPushButton#dangerButton:hover {{
        background-color: {c['error']};
        color: {c['text']};
    }}
    QPushButton#smallButton {{
        padding: 4px 12px;
        font-size: 11px;
        min-height: 24px;
    }}
    QPushButton#navButton {{
        text-align: left;
        padding: 12px 14px 12px 14px;
        border: 1px solid transparent;
        border-radius: 12px;
        background: transparent;
        color: {c['text_secondary']};
    }}
    QPushButton#navButton:hover {{
        background-color: {c['selected_bg']};
        border-color: {c['border_light']};
        color: {c['text']};
    }}
    QPushButton#navButtonActive {{
        text-align: left;
        padding: 12px 14px 12px 14px;
        border: 1px solid {c['accent']};
        border-radius: 12px;
        background-color: #241F16;
        color: {c['text']};
        font-weight: 600;
    }}
    QLineEdit#headerSearch {{
        background-color: {c['panel_elevated']};
        border-radius: 14px;
        padding-left: 12px;
        font-size: 13px;
    }}
    QComboBox#headerFilter {{
        background-color: {c['panel_elevated']};
        border-radius: 14px;
        padding-right: 26px;
    }}
    QComboBox#headerFilter::drop-down {{
        border: none;
        width: 22px;
    }}
    QComboBox#headerFilter::down-arrow {{
        image: none;
        width: 0px;
        height: 0px;
    }}
    QScrollBar:vertical {{
        background: {c['bg']};
        width: 10px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {c['border']};
        border-radius: 5px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {c['accent']};
    }}
    QLabel#secondary {{
        color: {c['text_secondary']};
    }}
    QLabel#title {{
        font-size: 24px;
        font-weight: 700;
        color: {c['accent']};
        letter-spacing: 0.3px;
    }}
    QLabel#sectionTitle {{
        color: {c['accent']};
        font-weight: 600;
    }}
    QTabWidget::pane {{
        border: 1px solid {c['border']};
        background: {c['panel']};
        border-radius: {r['sm']}px;
    }}
    QTabBar::tab {{
        background: {c['bg']};
        color: {c['text_secondary']};
        padding: 8px 16px;
        border: none;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        color: {c['accent']};
        border-bottom: 2px solid {c['accent']};
    }}
    QSplitter::handle {{
        background: {c['border']};
    }}
    QPlainTextEdit#terminalOutput {{
        background-color: {c['terminal_bg']};
        border: 1px solid {c['border']};
        border-radius: 14px;
        padding: 10px;
        font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
        font-size: 12px;
        selection-background-color: #4A4000;
    }}
    QLineEdit#terminalSearch {{
        min-height: 34px;
        background-color: {c['panel_elevated']};
    }}
    QLabel#terminalProgress {{
        background-color: {c['selected_bg']};
        border: 1px solid {c['border_light']};
        border-radius: 10px;
        padding: 4px 10px;
    }}
    """
