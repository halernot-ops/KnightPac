"""KnightPac splash screen."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPixmap
from PySide6.QtWidgets import QSplashScreen

from knightpac import __version__
from knightpac.ui.theme import COLORS

_ASSETS = Path(__file__).resolve().parent.parent / "assets" / "icons"
_SIZE = (480, 280)


def _render_pixmap(status_message: str = "Loading…") -> QPixmap:
    width, height = _SIZE
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    gradient = QLinearGradient(0, 0, width, height)
    gradient.setColorAt(0, QColor("#0A0A0A"))
    gradient.setColorAt(0.5, QColor("#141414"))
    gradient.setColorAt(1, QColor("#1A1610"))
    painter.setBrush(gradient)
    painter.setPen(QColor(COLORS["border"]))
    painter.drawRoundedRect(1, 1, width - 2, height - 2, 12, 12)

    icon_path = _ASSETS / "knightpac.svg"
    if icon_path.is_file():
        icon = QIcon(str(icon_path)).pixmap(72, 72)
        painter.drawPixmap((width - 72) // 2, 36, icon)

    title_font = QFont()
    title_font.setPointSize(26)
    title_font.setWeight(QFont.Weight.Bold)
    painter.setFont(title_font)
    painter.setPen(QColor(COLORS["accent"]))
    painter.drawText(0, 118, width, 40, Qt.AlignmentFlag.AlignHCenter, "KnightPac")

    sub_font = QFont()
    sub_font.setPointSize(11)
    painter.setFont(sub_font)
    painter.setPen(QColor(COLORS["text_secondary"]))
    painter.drawText(
        0, 158, width, 24, Qt.AlignmentFlag.AlignHCenter, "Premium Linux Package Manager"
    )

    painter.setPen(QColor(COLORS["text_muted"]))
    painter.drawText(0, 182, width, 20, Qt.AlignmentFlag.AlignHCenter, f"v{__version__}")

    painter.setPen(QColor(COLORS["accent"]))
    painter.drawText(0, height - 48, width, 28, Qt.AlignmentFlag.AlignHCenter, status_message)

    painter.end()
    return pixmap


class KnightSplashScreen(QSplashScreen):
    """QSplashScreen has no setWidget — content is painted onto a pixmap."""

    def __init__(self) -> None:
        super().__init__(_render_pixmap())
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

    def show_message(self, message: str) -> None:
        self.setPixmap(_render_pixmap(message))
        self.showMessage(
            "",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
            QColor(COLORS["accent"]),
        )
