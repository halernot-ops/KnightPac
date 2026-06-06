"""Package list card with selection, subtle motion, and async icons."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, Property, QPropertyAnimation, Qt, Signal
from PySide6.QtGui import QColor, QEnterEvent, QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from knightpac.models.package import Package
from knightpac.ui.components.knight_badge import KnightBadge
from knightpac.ui.components.knight_button import KnightButton
from knightpac.ui.icon_resolver import create_icon_request
from knightpac.ui.theme import COLORS


class PackageCard(QFrame):
    clicked = Signal(object)
    action_clicked = Signal(object, str)

    def __init__(self, package: Package, parent=None) -> None:
        super().__init__(parent)
        self.package = package
        self._hover_progress = 0.0
        self._selected = False
        self._icon_request = None
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("packageCard")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setMinimumHeight(118)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._anim = QPropertyAnimation(self, b"hoverProgress", self)
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._build()
        self._apply_style()

    def _build(self) -> None:
        layout = self._layout
        layout.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        row.setContentsMargins(18, 16, 18, 16)
        row.setSpacing(16)

        self._icon_label = QLabel()
        self._icon_label.setFixedSize(56, 56)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._set_placeholder_icon()
        self._load_icon_async()
        row.addWidget(self._icon_label)

        col = QVBoxLayout()
        col.setSpacing(6)
        header = QHBoxLayout()
        header.setSpacing(10)
        name = QLabel(self.package.name)
        name.setStyleSheet(
            f"color: {COLORS['text']}; font-weight: 700; font-size: 15px;"
        )
        header.addWidget(name)

        self._version = QLabel(self.package.version or "Version unavailable")
        self._version.setStyleSheet(
            f"color: {COLORS['accent']}; font-size: 12px; font-weight: 600;"
        )
        header.addStretch()
        header.addWidget(self._version)
        col.addLayout(header)

        badge_row = QHBoxLayout()
        badge_row.setSpacing(8)
        badge_row.addWidget(KnightBadge.for_source(self.package.display_source))
        badge_row.addWidget(self._status_badge())
        badge_row.addStretch()
        col.addLayout(badge_row)

        desc = QLabel(self.package.description or "No description available.")
        desc.setWordWrap(True)
        desc.setMaximumHeight(40)
        desc.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 12px; line-height: 1.35;"
        )
        col.addWidget(desc)

        meta = QHBoxLayout()
        meta.setSpacing(12)
        source_text = self.package.repository or self.package.manager or self.package.display_source
        source_lbl = QLabel(source_text)
        source_lbl.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 11px; letter-spacing: 0.2px;"
        )
        meta.addWidget(source_lbl)
        if self.package.size or self.package.installed_size:
            size_text = self.package.installed_size or self.package.size
            size_lbl = QLabel(size_text)
            size_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
            meta.addWidget(size_lbl)
        meta.addStretch()
        col.addLayout(meta)
        row.addLayout(col, 1)

        action_col = QVBoxLayout()
        action_col.addStretch()
        self._action_btn = KnightButton(self._action_label(), variant="accent")
        self._action_btn.setFixedWidth(96)
        self._action_btn.setStyleSheet(
            self._action_btn.styleSheet() + "padding: 8px 12px; font-size: 11px;"
        )
        self._action_btn.clicked.connect(self._on_action)
        action_col.addWidget(self._action_btn)
        action_col.addStretch()
        row.addLayout(action_col)

        layout.addLayout(row)

    def _status_badge(self) -> KnightBadge:
        if self.package.update_available:
            return KnightBadge("Update available", variant="official")
        if self.package.installed:
            return KnightBadge("Installed", variant="installed")
        return KnightBadge("Not installed")

    def _apply_style(self) -> None:
        border = COLORS["accent"] if self._selected else COLORS["border"]
        background = self._mix_color(
            COLORS["panel"],
            COLORS["selected_bg"] if self._selected else COLORS["panel_elevated"],
            max(self._hover_progress, 0.35 if self._selected else 0.0),
        )
        shadow = "rgba(212, 165, 76, 0.08)" if self._selected else "transparent"
        self.setStyleSheet(
            f"""
            QFrame#packageCard {{
                background-color: {background};
                border: 1px solid {border};
                border-radius: 16px;
            }}
            QFrame#packageCard:hover {{
                border-color: {COLORS['accent']};
            }}
            QLabel {{
                background: transparent;
            }}
            QLabel {{
                color: {COLORS['text']};
            }}
            QLabel {{
                selection-background-color: {COLORS['accent']};
            }}
            """
        )
        self._icon_label.setStyleSheet(
            f"""
            background-color: {COLORS['bg']};
            border: 1px solid {COLORS['border_light']};
            border-radius: 14px;
            color: {COLORS['accent']};
            font-size: 11px;
            font-weight: 700;
            padding: 4px;
            """
        )
        self.setGraphicsEffect(None)
        if shadow != "transparent":
            self.setStyleSheet(self.styleSheet() + f"QFrame#packageCard {{ outline: none; }}")

    def _set_placeholder_icon(self) -> None:
        self._icon_label.setPixmap(QPixmap())
        self._icon_label.setText("PKG")

    def _load_icon_async(self) -> None:
        self._icon_request = create_icon_request(self.package.name, self.package.icon)
        self._icon_request.setParent(self)
        self._icon_request.ready.connect(self._apply_icon)

    def _apply_icon(self, icon) -> None:
        pixmap = icon.pixmap(44, 44)
        if pixmap.isNull():
            self._set_placeholder_icon()
            return
        self._icon_label.setText("")
        self._icon_label.setPixmap(pixmap)

    def _action_label(self) -> str:
        if self.package.update_available:
            return "Update"
        if self.package.installed:
            return "Remove"
        return "Install"

    def _on_action(self) -> None:
        if self.package.update_available:
            self.action_clicked.emit(self.package, "update")
        elif self.package.installed:
            self.action_clicked.emit(self.package, "remove")
        else:
            self.action_clicked.emit(self.package, "install")
        self.clicked.emit(self.package)

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self._apply_style()

    def enterEvent(self, event: QEnterEvent) -> None:
        self._animate_hover(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._animate_hover(0.0)
        super().leaveEvent(event)

    def _animate_hover(self, value: float) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._hover_progress)
        self._anim.setEndValue(value)
        self._anim.start()

    def _get_hover_progress(self) -> float:
        return self._hover_progress

    def _set_hover_progress(self, value: float) -> None:
        self._hover_progress = value
        self._apply_style()

    hoverProgress = Property(float, _get_hover_progress, _set_hover_progress)

    @staticmethod
    def _mix_color(start: str, end: str, amount: float) -> str:
        amount = max(0.0, min(1.0, amount))
        a = QColor(start)
        b = QColor(end)
        r = round(a.red() + (b.red() - a.red()) * amount)
        g = round(a.green() + (b.green() - a.green()) * amount)
        bl = round(a.blue() + (b.blue() - a.blue()) * amount)
        return QColor(r, g, bl).name()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.package)
        super().mousePressEvent(event)
