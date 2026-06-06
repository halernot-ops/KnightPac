"""System tray integration."""

from __future__ import annotations

import asyncio

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

class SystemTrayController:
    def __init__(self, window, icon: QIcon) -> None:
        self._window = window
        self._tray = QSystemTrayIcon(icon)
        self._tray.setToolTip("KnightPac")
        menu = QMenu()
        show_action = QAction("Show window", menu)
        show_action.triggered.connect(self.show_window)
        menu.addAction(show_action)
        check_action = QAction("Check for updates", menu)
        check_action.triggered.connect(self._check_updates)
        menu.addAction(check_action)
        menu.addSeparator()
        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(quit_action)
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_activated)
        self._tray.show()

    @property
    def tray_icon(self) -> QSystemTrayIcon:
        return self._tray

    def show_window(self) -> None:
        self._window.showNormal()
        self._window.raise_()
        self._window.activateWindow()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()

    def _check_updates(self) -> None:
        self.show_window()
        self._window._sidebar.select("updates")
        self._window._sidebar.page_changed.emit("updates")
        self._window.schedule_async(self._window._load_page_data("updates"))
