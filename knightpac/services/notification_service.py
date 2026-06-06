"""Desktop notifications via system tray."""

from __future__ import annotations

import logging

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QSystemTrayIcon

logger = logging.getLogger("knightpac.notifications")


class NotificationService:
    def __init__(self, tray: QSystemTrayIcon | object) -> None:
        self._tray = tray
        self._enabled = True

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    def notify(self, title: str, message: str, icon: QIcon | None = None) -> None:
        if not self.enabled:
            return
        try:
            self._tray.showMessage(
                title,
                message,
                icon or self._tray.icon(),
                5000,
            )
        except Exception as exc:
            logger.warning("Notification failed: %s", exc)

    def install_finished(self, package: str, success: bool) -> None:
        if success:
            self.notify("KnightPac", f"Installed: {package}")
        else:
            self.notify("KnightPac", f"Install failed: {package}")

    def remove_finished(self, package: str, success: bool) -> None:
        if success:
            self.notify("KnightPac", f"Removed: {package}")
        else:
            self.notify("KnightPac", f"Remove failed: {package}")

    def updates_available(self, count: int) -> None:
        if count > 0:
            self.notify("KnightPac", f"{count} update(s) available")

    def operation_error(self, message: str) -> None:
        self.notify("KnightPac", message)
