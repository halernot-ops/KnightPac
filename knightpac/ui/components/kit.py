"""KnightPac design system primitives."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, Property, QPropertyAnimation, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from knightpac.ui.iconography import icon


class KnightButton(QPushButton):
    def __init__(self, text: str = "", parent: QWidget | None = None, *, variant: str = "secondary") -> None:
        super().__init__(text, parent)
        self._elevation = 0.0
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("knightClass", "button")
        self.setProperty("variant", variant)
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(18)
        self._shadow.setOffset(0, 8)
        self._shadow.setColor(QColor(0, 0, 0, 0))
        self.setGraphicsEffect(self._shadow)
        self._anim = QPropertyAnimation(self, b"elevation", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def enterEvent(self, event) -> None:
        self._animate(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._animate(0.0)
        super().leaveEvent(event)

    def _animate(self, value: float) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._elevation)
        self._anim.setEndValue(value)
        self._anim.start()

    def _get_elevation(self) -> float:
        return self._elevation

    def _set_elevation(self, value: float) -> None:
        self._elevation = value
        self._shadow.setBlurRadius(18 + value * 10)
        self._shadow.setOffset(0, 8 + value * 2)
        self._shadow.setColor(QColor(0, 0, 0, int(28 + value * 24)))

    elevation = Property(float, _get_elevation, _set_elevation)


class KnightCard(QFrame):
    def __init__(self, parent: QWidget | None = None, *, elevated: bool = False) -> None:
        super().__init__(parent)
        self._glow = 0.0
        self._hoverable = elevated
        self.setProperty("knightClass", "card")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._body = QVBoxLayout(self)
        self._body.setContentsMargins(18, 18, 18, 18)
        self._body.setSpacing(12)
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(28)
        self._shadow.setOffset(0, 14)
        self._shadow.setColor(QColor(0, 0, 0, 70))
        self.setGraphicsEffect(self._shadow)
        self._anim = QPropertyAnimation(self, b"glow", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def body_layout(self) -> QVBoxLayout:
        return self._body

    def enterEvent(self, event) -> None:
        if self._hoverable:
            self._animate(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        if self._hoverable:
            self._animate(0.0)
        super().leaveEvent(event)

    def _animate(self, value: float) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._glow)
        self._anim.setEndValue(value)
        self._anim.start()

    def _get_glow(self) -> float:
        return self._glow

    def _set_glow(self, value: float) -> None:
        self._glow = value
        self.setProperty("hovered", value > 0.4)
        self.style().unpolish(self)
        self.style().polish(self)
        self._shadow.setBlurRadius(28 + value * 10)
        self._shadow.setOffset(0, 14 + value * 2)
        self._shadow.setColor(QColor(0, 0, 0, int(70 + value * 24)))

    glow = Property(float, _get_glow, _set_glow)


class KnightBadge(QLabel):
    def __init__(self, text: str, parent: QWidget | None = None, *, tone: str = "neutral") -> None:
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setProperty("knightClass", "badge")
        self.set_tone(tone)

    def set_tone(self, tone: str) -> None:
        self.setProperty("tone", tone)
        self.style().unpolish(self)
        self.style().polish(self)


class KnightSearchBox(QWidget):
    textChanged = Signal(str)
    returnPressed = Signal()

    def __init__(self, parent: QWidget | None = None, *, placeholder: str = "Search") -> None:
        super().__init__(parent)
        self.setProperty("knightClass", "searchBox")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)
        self._field = QLineEdit()
        self._field.setProperty("knightClass", "searchField")
        self._field.setPlaceholderText(placeholder)
        self._field.setClearButtonEnabled(True)
        self._field.addAction(icon("search"), QLineEdit.ActionPosition.LeadingPosition)
        self._field.textChanged.connect(self.textChanged.emit)
        self._field.returnPressed.connect(self.returnPressed.emit)
        layout.addWidget(self._field)

    def text(self) -> str:
        return self._field.text()

    def setText(self, text: str) -> None:
        self._field.setText(text)


class KnightSidebarItem(QPushButton):
    def __init__(self, label: str, icon_name: str, parent: QWidget | None = None) -> None:
        super().__init__(label, parent)
        self._selection = 0.0
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setIcon(icon(icon_name))
        self.setProperty("knightClass", "sidebarItem")
        self._anim = QPropertyAnimation(self, b"selectionProgress", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def setChecked(self, checked: bool) -> None:
        super().setChecked(checked)
        self._anim.stop()
        self._anim.setStartValue(self._selection)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    def _get_selection(self) -> float:
        return self._selection

    def _set_selection(self, value: float) -> None:
        self._selection = value
        self.setProperty("selected", value > 0.4)
        self.style().unpolish(self)
        self.style().polish(self)

    selectionProgress = Property(float, _get_selection, _set_selection)


class KnightSection(KnightCard):
    def __init__(self, title: str, parent: QWidget | None = None, *, subtitle: str = "", elevated: bool = False) -> None:
        super().__init__(parent, elevated=elevated)
        self.setProperty("knightClass", "section")
        self._header = QHBoxLayout()
        self._header.setContentsMargins(0, 0, 0, 0)
        self._header.setSpacing(12)
        header_text = QVBoxLayout()
        header_text.setContentsMargins(0, 0, 0, 0)
        header_text.setSpacing(2)
        self._title = QLabel(title)
        self._title.setProperty("knightClass", "sectionTitle")
        self._subtitle = QLabel(subtitle)
        self._subtitle.setProperty("knightClass", "muted")
        self._subtitle.setVisible(bool(subtitle))
        header_text.addWidget(self._title)
        header_text.addWidget(self._subtitle)
        self._header.addLayout(header_text, 1)
        self._actions = QHBoxLayout()
        self._actions.setContentsMargins(0, 0, 0, 0)
        self._actions.setSpacing(8)
        self._header.addLayout(self._actions)
        self.body_layout().addLayout(self._header)
        self._content = QVBoxLayout()
        self._content.setContentsMargins(0, 0, 0, 0)
        self._content.setSpacing(12)
        self.body_layout().addLayout(self._content)

    def content_layout(self) -> QVBoxLayout:
        return self._content

    def actions_layout(self) -> QHBoxLayout:
        return self._actions

    def set_subtitle(self, subtitle: str) -> None:
        self._subtitle.setText(subtitle)
        self._subtitle.setVisible(bool(subtitle))


class KnightTabWidget(QTabWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("knightClass", "tabWidget")
        self.setDocumentMode(True)


class KnightDialog(QDialog):
    def __init__(self, title: str, parent: QWidget | None = None, *, subtitle: str = "") -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle(title)
        self.setProperty("knightClass", "dialog")
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)
        self._title = QLabel(title)
        self._title.setProperty("knightClass", "dialogTitle")
        self._subtitle = QLabel(subtitle)
        self._subtitle.setProperty("knightClass", "muted")
        self._subtitle.setVisible(bool(subtitle))
        root.addWidget(self._title)
        root.addWidget(self._subtitle)
        self._content = QVBoxLayout()
        self._content.setContentsMargins(0, 0, 0, 0)
        self._content.setSpacing(12)
        root.addLayout(self._content)

    def content_layout(self) -> QVBoxLayout:
        return self._content


class KnightStateView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("knightClass", "stateView")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 36, 36, 36)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._badge = KnightBadge("IDLE")
        self._title = QLabel("Ready")
        self._title.setProperty("knightClass", "stateTitle")
        self._body = QLabel("")
        self._body.setProperty("knightClass", "muted")
        self._body.setWordWrap(True)
        self._body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._badge, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._title, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._body, 0, Qt.AlignmentFlag.AlignCenter)

    def set_state(self, state: str, title: str, body: str = "") -> None:
        tones = {
            "loading": "accent",
            "empty": "neutral",
            "error": "danger",
            "success": "success",
        }
        self._badge.setText(state.upper())
        self._badge.set_tone(tones.get(state, "neutral"))
        self._title.setText(title)
        self._body.setText(body)


class KnightMetricCard(KnightCard):
    def __init__(self, title: str, parent: QWidget | None = None, *, tone: str = "accent") -> None:
        super().__init__(parent, elevated=True)
        self.setProperty("knightClass", "metricCard")
        layout = self.body_layout()
        self._badge = KnightBadge(title, tone=tone)
        self._value = QLabel("--")
        self._value.setProperty("knightClass", "metricValue")
        self._caption = QLabel("")
        self._caption.setProperty("knightClass", "muted")
        layout.addWidget(self._badge)
        layout.addWidget(self._value)
        layout.addWidget(self._caption)

    def set_metric(self, value: str, caption: str = "") -> None:
        self._value.setText(value)
        self._caption.setText(caption)
