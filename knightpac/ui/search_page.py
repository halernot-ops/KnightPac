"""Package list page with polished empty, loading, and error states."""

from __future__ import annotations

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QProgressBar,
    QScrollArea,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
    QLabel,
)

from knightpac.models.package import Package
from knightpac.ui.theme import COLORS
from knightpac.ui.widgets.package_card import PackageCard


class SearchPage(QWidget):
    package_selected = Signal(object)
    action_requested = Signal(object, str)
    _BATCH_SIZE = 40

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._cards: list[PackageCard] = []
        self._pending_packages: list[Package] = []
        self._selected_name = ""
        self._render_generation = 0
        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.timeout.connect(self._render_next_batch)
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(0)

        self._stack_host = QWidget()
        self._stack = QStackedLayout(self._stack_host)
        self._stack.setContentsMargins(0, 0, 0, 0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._container = QWidget()
        self._list_layout = QVBoxLayout(self._container)
        self._list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(14)
        self._scroll.setWidget(self._container)
        self._stack.addWidget(self._scroll)

        self._loading_state = _StatePane(
            "Loading packages",
            "Refreshing package metadata and preparing results.",
            tone="loading",
            progress=True,
        )
        self._empty_state = _StatePane(
            "No packages found",
            "Try another search query or change the active filter.",
            tone="empty",
        )
        self._error_state = _StatePane(
            "Unable to load packages",
            "The package manager returned an error. Try syncing databases or retry the query.",
            tone="error",
        )
        self._idle_state = _StatePane(
            "Start exploring packages",
            "Use the search field above to browse repository and AUR packages.",
            tone="empty",
        )
        self._stack.addWidget(self._idle_state)
        self._stack.addWidget(self._loading_state)
        self._stack.addWidget(self._empty_state)
        self._stack.addWidget(self._error_state)
        outer.addWidget(self._stack_host)
        self.show_idle()

    def set_packages(self, packages: list[Package]) -> None:
        self._render_timer.stop()
        self._clear_cards()
        self._cards.clear()
        self._pending_packages = list(packages)
        if not self._pending_packages:
            self._selected_name = ""
            self._stack.setCurrentWidget(self._empty_state)
            return
        self._stack.setCurrentWidget(self._scroll)
        self._render_next_batch()

    def _render_next_batch(self) -> None:
        if not self._pending_packages:
            if self._cards:
                self._restore_selection()
            return
        chunk = self._pending_packages[: self._BATCH_SIZE]
        self._pending_packages = self._pending_packages[self._BATCH_SIZE :]
        for pkg in chunk:
            card = PackageCard(pkg)
            card.clicked.connect(self._on_card_clicked)
            card.action_clicked.connect(self.action_requested.emit)
            self._list_layout.addWidget(card)
            self._cards.append(card)
        self._rebalance_spacer()
        if self._pending_packages:
            self._render_timer.start(0)
        else:
            self._restore_selection()

    def show_idle(self) -> None:
        self._render_timer.stop()
        self._clear_cards()
        self._pending_packages.clear()
        self._selected_name = ""
        self._stack.setCurrentWidget(self._idle_state)

    def show_loading(
        self,
        title: str = "Loading packages",
        body: str = "Refreshing package metadata and preparing results.",
    ) -> None:
        self._loading_state.set_text(title, body)
        self._stack.setCurrentWidget(self._loading_state)

    def show_empty(
        self,
        title: str = "No packages found",
        body: str = "Try another search query or change the active filter.",
    ) -> None:
        self._render_timer.stop()
        self._clear_cards()
        self._pending_packages.clear()
        self._selected_name = ""
        self._empty_state.set_text(title, body)
        self._stack.setCurrentWidget(self._empty_state)

    def show_error(
        self,
        title: str = "Unable to load packages",
        body: str = "The package manager returned an error. Try again in a moment.",
    ) -> None:
        self._render_timer.stop()
        self._clear_cards()
        self._pending_packages.clear()
        self._selected_name = ""
        self._error_state.set_text(title, body)
        self._stack.setCurrentWidget(self._error_state)

    def _on_card_clicked(self, package: Package) -> None:
        self._selected_name = package.name
        for card in self._cards:
            card.set_selected(card.package.name == package.name)
        self.package_selected.emit(package)

    def _restore_selection(self) -> None:
        if not self._cards:
            return
        selected_card = None
        for card in self._cards:
            if card.package.name == self._selected_name:
                selected_card = card
                break
        if selected_card is None:
            selected_card = self._cards[0]
            self._selected_name = selected_card.package.name
        for card in self._cards:
            card.set_selected(card is selected_card)

    def _clear_cards(self) -> None:
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _rebalance_spacer(self) -> None:
        if self._list_layout.count():
            last_item = self._list_layout.itemAt(self._list_layout.count() - 1)
            if last_item and last_item.spacerItem():
                self._list_layout.takeAt(self._list_layout.count() - 1)
        self._list_layout.addStretch(1)


class _StatePane(QFrame):
    def __init__(
        self,
        title: str,
        body: str,
        *,
        tone: str,
        progress: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("searchStatePane")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._badge = QLabel(tone.upper())
        self._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._badge.setStyleSheet(self._badge_style(tone))
        layout.addWidget(self._badge, 0, Qt.AlignmentFlag.AlignCenter)

        self._title = QLabel(title)
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setStyleSheet(
            f"color: {COLORS['text']}; font-size: 22px; font-weight: 700;"
        )
        layout.addWidget(self._title)

        self._body = QLabel(body)
        self._body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._body.setWordWrap(True)
        self._body.setMaximumWidth(520)
        self._body.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 13px; line-height: 1.5;"
        )
        layout.addWidget(self._body)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setTextVisible(False)
        self._progress.setFixedWidth(220)
        self._progress.setVisible(progress)
        self._progress.setStyleSheet(
            f"""
            QProgressBar {{
                background-color: {COLORS['panel']};
                border: 1px solid {COLORS['border']};
                border-radius: 7px;
                min-height: 10px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['accent']};
                border-radius: 7px;
            }}
            """
        )
        layout.addWidget(self._progress, 0, Qt.AlignmentFlag.AlignCenter)

        self.setStyleSheet(
            f"""
            QFrame#searchStatePane {{
                background-color: {COLORS['panel']};
                border: 1px solid {COLORS['border']};
                border-radius: 18px;
            }}
            """
        )

    def set_text(self, title: str, body: str) -> None:
        self._title.setText(title)
        self._body.setText(body)

    @staticmethod
    def _badge_style(tone: str) -> str:
        mapping = {
            "loading": (COLORS["accent"], "#2A2418"),
            "empty": (COLORS["text_secondary"], COLORS["selected_bg"]),
            "error": (COLORS["error"], "#281615"),
        }
        fg, bg = mapping.get(tone, (COLORS["text"], COLORS["panel_elevated"]))
        return (
            "QLabel {"
            f"color: {fg};"
            f"background-color: {bg};"
            f"border: 1px solid {fg};"
            "border-radius: 11px;"
            "padding: 4px 10px;"
            "font-size: 11px;"
            "font-weight: 700;"
            "letter-spacing: 0.6px;"
            "}"
        )
