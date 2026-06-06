"""Updates page."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from knightpac.models.package import Package
from knightpac.ui.components.knight_card import KnightCard
from knightpac.ui.search_page import SearchPage
from knightpac.ui.theme import COLORS


class UpdatesPage(QWidget):
    package_selected = SearchPage.package_selected
    action_requested = SearchPage.action_requested

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        self._repo_label = QLabel("Repository updates")
        self._repo_label.setStyleSheet(
            f"color: {COLORS['accent']}; font-size: 14px; font-weight: 700;"
        )
        repo_card = KnightCard(hover=False)
        repo_layout = repo_card.content_layout()
        repo_layout.addWidget(self._repo_label)
        self._repo_list = SearchPage()
        repo_layout.addWidget(self._repo_list)
        layout.addWidget(repo_card, 1)

        self._aur_label = QLabel("AUR updates")
        self._aur_label.setStyleSheet(
            f"color: {COLORS['accent']}; font-size: 14px; font-weight: 700;"
        )
        aur_card = KnightCard(hover=False)
        aur_layout = aur_card.content_layout()
        aur_layout.addWidget(self._aur_label)
        self._aur_list = SearchPage()
        aur_layout.addWidget(self._aur_list)
        layout.addWidget(aur_card, 1)
        self._repo_list.package_selected.connect(self.package_selected.emit)
        self._aur_list.package_selected.connect(self.package_selected.emit)
        self._repo_list.action_requested.connect(self.action_requested.emit)
        self._aur_list.action_requested.connect(self.action_requested.emit)

    def set_updates(self, repo: list[Package], aur: list[Package]) -> None:
        self._repo_list.set_packages(repo)
        self._aur_list.set_packages(aur)
        self._repo_label.setText(f"Repository updates ({len(repo)})")
        self._aur_label.setText(f"AUR updates ({len(aur)})")

    def show_loading(self) -> None:
        self._repo_list.show_loading(
            "Loading repository updates",
            "Checking official repositories for pending package upgrades.",
        )
        self._aur_list.show_loading(
            "Loading AUR updates",
            "Checking AUR packages and build metadata for updates.",
        )

    def show_error(self, body: str) -> None:
        self._repo_list.show_error("Unable to load repository updates", body)
        self._aur_list.show_error("Unable to load AUR updates", body)
