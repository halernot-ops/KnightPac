"""Overview dashboard page for the KnightPac home screen."""

from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from knightpac.ui.components.dashboard_stat_card import DashboardStatCard
from knightpac.ui.components.knight_card import KnightCard
from knightpac.ui.components.knight_section import KnightSection
from knightpac.ui.theme import COLORS


class OverviewPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        hero = KnightCard(hover=False)
        hero_layout = hero.content_layout()
        hero_layout.setSpacing(8)
        header = QLabel("KnightPac Overview")
        header.setObjectName("title")
        hero_layout.addWidget(header)

        subtitle = QLabel(
            "A polished package dashboard with fast status checks for updates, cache, and the active manager."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 13px; line-height: 1.5;"
        )
        hero_layout.addWidget(subtitle)
        self._hero_meta = QLabel("Ready to sync repositories and manage your system.")
        self._hero_meta.setStyleSheet(
            f"color: {COLORS['accent']}; font-size: 12px; font-weight: 600;"
        )
        hero_layout.addWidget(self._hero_meta)
        root.addWidget(hero)

        grid = QGridLayout()
        grid.setSpacing(16)
        self._installed = DashboardStatCard("Installed Packages", accent=True)
        self._updates = DashboardStatCard("Available Updates")
        self._cache = DashboardStatCard("Cache Size")
        self._manager = DashboardStatCard("Active Manager")
        grid.addWidget(self._installed, 0, 0)
        grid.addWidget(self._updates, 0, 1)
        grid.addWidget(self._cache, 1, 0)
        grid.addWidget(self._manager, 1, 1)
        root.addLayout(grid)

        recent_section = KnightSection("Recent Operations")
        self._recent_card = KnightCard(hover=False)
        recent_layout = self._recent_card.content_layout()
        self._recent_label = QLabel("No operations yet")
        self._recent_label.setWordWrap(True)
        self._recent_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 12px; line-height: 1.5;"
        )
        recent_layout.addWidget(self._recent_label)
        recent_section.body_layout().addWidget(self._recent_card)
        root.addWidget(recent_section)
        root.addStretch()

    def set_stats(
        self,
        installed: int,
        updates: int,
        cache: str,
        *,
        active_manager: str,
        update_breakdown: str = "",
    ) -> None:
        self._installed.set_value(str(installed), "packages on this system")
        self._updates.set_value(str(updates), update_breakdown or "updates pending")
        self._cache.set_value(cache, "pacman package cache")
        self._manager.set_value(active_manager.upper(), "current package backend")
        self._hero_meta.setText(
            f"{installed} installed packages, {updates} updates pending, cache size {cache}."
        )

    def set_recent_operations(self, lines: list[str]) -> None:
        if not lines:
            self._recent_label.setText("No operations yet")
            return
        self._recent_label.setText("\n".join(lines))
