#!/usr/bin/env python3
"""KnightPac — graphical package manager entry point."""

from __future__ import annotations

import asyncio
import sys

from PySide6.QtWidgets import QApplication

from knightpac.core.logging_config import setup_logging
from knightpac.services.settings_service import SettingsService
from knightpac.ui.main_window import MainWindow
from knightpac.ui.splash_screen import KnightSplashScreen
from knightpac.ui.theme import stylesheet


def main() -> int:
    settings = SettingsService()
    setup_logging(max_bytes=settings.max_log_size * 1_000_000, backup_count=2)

    app = QApplication(sys.argv)
    app.setApplicationName("KnightPac")
    app.setStyleSheet(stylesheet())
    app.setQuitOnLastWindowClosed(not settings.minimize_to_tray)

    try:
        import qasync
    except ImportError:
        print("qasync is required: pip install qasync", file=sys.stderr)
        return 1

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    splash = KnightSplashScreen()
    splash.show_message("Starting KnightPac…")
    splash.show()
    app.processEvents()

    window = MainWindow()
    splash.show_message("Loading dashboard…")
    app.processEvents()
    window.show()
    splash.finish(window)

    with loop:
        loop.create_task(window._load_page_data("overview"))
        loop.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
