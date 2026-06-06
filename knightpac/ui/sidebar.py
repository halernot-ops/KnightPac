"""Left navigation sidebar with SVG icons."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Signal, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from knightpac.ui.theme import COLORS

NAV_ITEMS = [
    ("overview", "Overview"),
    ("search", "Search"),
    ("installed", "Installed"),
    ("updates", "Updates"),
    ("aur", "AUR"),
    ("history", "History"),
    ("dependencies", "Dependencies"),
    ("cache", "Cache Cleaner"),
    ("diagnostics", "Diagnostics"),
    ("settings", "Settings"),
    ("about", "About"),
]

_ICON_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"


class Sidebar(QWidget):
    page_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(220)
        self.setStyleSheet(
            f"""
            Sidebar {{
                background-color: {COLORS['panel']};
                border-right: 1px solid {COLORS['border']};
            }}
            """
        )
        self.setObjectName("Sidebar")
        self._buttons: dict[str, QPushButton] = {}
        self._build_ui()

    def _nav_icon(self, key: str) -> QIcon:
        path = _ICON_DIR / f"{key}.svg"
        if path.is_file():
            return QIcon(str(path))
        return QIcon()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 18, 10, 18)
        layout.setSpacing(6)

        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(10, 0, 10, 8)
        brand_row.setSpacing(10)
        logo = QLabel()
        logo_path = _ICON_DIR / "knightpac.svg"
        if logo_path.is_file():
            logo.setPixmap(QIcon(str(logo_path)).pixmap(30, 30))
        brand = QLabel("KnightPac")
        brand.setStyleSheet(
            f"color: {COLORS['accent']}; font-size: 18px; font-weight: 700; letter-spacing: 0.5px;"
        )
        brand_row.addWidget(logo)
        brand_row.addWidget(brand)
        brand_row.addStretch()
        layout.addLayout(brand_row)

        tagline = QLabel("Package Manager")
        tagline.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 11px; padding: 0 10px 10px 10px;"
        )
        layout.addWidget(tagline)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        for key, label in NAV_ITEMS:
            btn = QPushButton(f"  {label}")
            btn.setIcon(self._nav_icon(key))
            btn.setIconSize(QSize(18, 18))
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setObjectName("navButton")
            btn.clicked.connect(lambda checked, k=key: self._on_click(k))
            self._group.addButton(btn)
            self._buttons[key] = btn
            layout.addWidget(btn)

        layout.addStretch()
        footer = QLabel("Stable UI 0.5")
        footer.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 11px; padding: 12px 12px 0 12px;"
        )
        layout.addWidget(footer)
        self.select("overview")

    def _on_click(self, key: str) -> None:
        self.select(key)
        self.page_changed.emit(key)

    def select(self, key: str) -> None:
        for k, btn in self._buttons.items():
            active = k == key
            btn.setChecked(active)
            btn.setObjectName("navButtonActive" if active else "navButton")
