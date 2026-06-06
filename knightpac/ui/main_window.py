"""Main application window."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QMainWindow,
    QSplitter,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from knightpac.core.logging_config import reconfigure_log_size
from knightpac.core.process_runner import ProcessRunner
from knightpac.core.terminal_buffer import TerminalBuffer
from knightpac.models.operation import OperationType
from knightpac.models.package import Package, SourceType
from knightpac.services.dependency_service import DependencyService
from knightpac.services.diagnostics_service import DiagnosticsService
from knightpac.services.history_service import HistoryService
from knightpac.services.notification_service import NotificationService
from knightpac.services.operation_queue import OperationQueue, QueuedOperation, QueueStatus
from knightpac.services.package_service import PackageService
from knightpac.services.search_service import SearchService
from knightpac.services.settings_service import SettingsService
from knightpac.services.update_service import UpdateService
from knightpac.ui.about_page import AboutPage
from knightpac.ui.aur_page import AurPage
from knightpac.ui.cache_page import CachePage
from knightpac.ui.dependencies_page import DependenciesPage
from knightpac.ui.diagnostics_page import DiagnosticsPage
from knightpac.ui.header_bar import HeaderBar
from knightpac.ui.history_page import HistoryPage
from knightpac.ui.installed_page import InstalledPage
from knightpac.ui.overview_page import OverviewPage
from knightpac.ui.search_page import SearchPage
from knightpac.ui.settings_page import SettingsPage
from knightpac.ui.sidebar import Sidebar
from knightpac.ui.system_tray import SystemTrayController
from knightpac.ui.terminal_panel import TerminalPanel
from knightpac.ui.updates_page import UpdatesPage
from knightpac.ui.widgets.package_details import PackageDetailsPanel

logger = logging.getLogger("knightpac.ui")

_ICON_PATH = Path(__file__).resolve().parent.parent / "assets" / "icons" / "knightpac.png"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("KnightPac")
        self.resize(1280, 800)

        self._settings = SettingsService()
        self._terminal_buffer = TerminalBuffer(max_lines=10_000)
        self._runner = ProcessRunner(self._terminal_buffer)
        self._packages = PackageService(self._runner)
        self._search_svc = SearchService(self._packages)
        self._update_svc = UpdateService(self._packages)
        self._dep_svc = DependencyService(self._packages)
        self._history = HistoryService()
        self._diagnostics = DiagnosticsService(self._runner)
        self._queue = OperationQueue(self._runner)

        icon = self._load_icon()
        self.setWindowIcon(icon)
        self._tray: SystemTrayController | None = None
        tray_target: QSystemTrayIcon | _DummyTray
        if QSystemTrayIcon.isSystemTrayAvailable():
            self._tray = SystemTrayController(self, icon)
            tray_target = self._tray.tray_icon
        else:
            tray_target = _DummyTray(icon)
        self._notifications = NotificationService(tray_target)

        self._terminal = TerminalPanel(self._terminal_buffer)
        self._page_opacity = QGraphicsOpacityEffect(self)
        self._page_anim = QPropertyAnimation(self._page_opacity, b"opacity", self)
        self._page_anim.setDuration(180)
        self._page_anim.setStartValue(0.78)
        self._page_anim.setEndValue(1.0)
        self._page_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._build_ui()
        self._connect_signals()
        self._apply_log_limit()
        self._apply_tray_setting()
        self._apply_notification_setting()

    def schedule_async(self, coro) -> None:
        """Schedule a coroutine on the qasync loop (safe before and after app start)."""
        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
        loop.create_task(coro)

    @staticmethod
    def _load_icon() -> QIcon:
        if _ICON_PATH.exists():
            return QIcon(str(_ICON_PATH))
        return QIcon.fromTheme("system-software-install")

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._header = HeaderBar()
        root.addWidget(self._header)

        body = QHBoxLayout()
        body.setSpacing(0)
        self._sidebar = Sidebar()
        body.addWidget(self._sidebar)

        center_split = QSplitter(Qt.Orientation.Horizontal)
        self._pages = QStackedWidget()
        self._overview = OverviewPage()
        self._search_page = SearchPage()
        self._installed_page = InstalledPage()
        self._updates_page = UpdatesPage()
        self._aur_page = AurPage()
        self._history_page = HistoryPage()
        self._deps_page = DependenciesPage()
        self._cache_page = CachePage()
        self._diagnostics_page = DiagnosticsPage()
        self._settings_page = SettingsPage(self._settings)
        self._about_page = AboutPage()

        for widget in (
            self._overview,
            self._search_page,
            self._installed_page,
            self._updates_page,
            self._aur_page,
            self._history_page,
            self._deps_page,
            self._cache_page,
            self._diagnostics_page,
            self._settings_page,
            self._about_page,
        ):
            self._pages.addWidget(widget)
        self._pages.currentWidget().setGraphicsEffect(self._page_opacity)

        center_split.addWidget(self._pages)
        self._details = PackageDetailsPanel()
        center_split.addWidget(self._details)
        center_split.setStretchFactor(0, 2)
        center_split.setStretchFactor(1, 1)
        body.addWidget(center_split, 1)
        root.addLayout(body, 1)

        self._terminal.setMaximumHeight(180)
        self._terminal.setMinimumHeight(120)
        root.addWidget(self._terminal)

    def _connect_signals(self) -> None:
        self._sidebar.page_changed.connect(self._on_page_changed)
        self._header.search_requested.connect(
            lambda q, f: self.schedule_async(self._do_search(q, f))
        )
        self._header.sync_requested.connect(
            lambda: self._enqueue_system(OperationType.SYNC, "databases", self._packages.sync_databases)
        )

        list_pages = (
            self._search_page,
            self._installed_page,
            self._aur_page,
            self._updates_page._repo_list,
            self._updates_page._aur_list,
        )
        for page in list_pages:
            page.package_selected.connect(
                lambda pkg: self.schedule_async(self._show_package(pkg))
            )
            page.action_requested.connect(self._on_card_action)

        self._updates_page.action_requested.connect(self._on_card_action)

        self._details.install_clicked.connect(
            lambda pkg: self._enqueue_package(OperationType.INSTALL, pkg, self._packages.install)
        )
        self._details.reinstall_clicked.connect(
            lambda pkg: self._enqueue_package(
                OperationType.REINSTALL, pkg, self._packages.reinstall
            )
        )
        self._details.remove_clicked.connect(
            lambda pkg: self._enqueue_package(OperationType.REMOVE, pkg, self._packages.remove)
        )

        self._deps_page._load_btn.clicked.connect(
            lambda: self.schedule_async(self._load_dep_page())
        )
        self._cache_page._clear_old_btn.clicked.connect(
            lambda: self._enqueue_system(
                OperationType.CACHE_CLEAR,
                "pacman-cache",
                lambda: self._packages.clear_cache(all_packages=False),
            )
        )
        self._cache_page._clear_all_btn.clicked.connect(
            lambda: self._enqueue_system(
                OperationType.CACHE_CLEAR,
                "pacman-cache-all",
                lambda: self._packages.clear_cache(all_packages=True),
            )
        )

        self._queue.operation_finished.connect(self._on_operation_finished)
        self._queue.progress_updated.connect(self._on_progress_updated)

        self._history_page.filter_changed.connect(
            lambda *_: self.schedule_async(self._reload_history())
        )
        self._history_page.export_csv_requested.connect(
            lambda: self._export_history("csv")
        )
        self._history_page.export_json_requested.connect(
            lambda: self._export_history("json")
        )
        self._diagnostics_page._refresh_btn.clicked.connect(
            lambda: self.schedule_async(self._load_diagnostics())
        )
        self._terminal.cancel_requested.connect(self._queue.cancel_current)

    def _apply_log_limit(self) -> None:
        mb = self._settings.max_log_size
        self._terminal_buffer.trim_to_max_bytes(mb * 1_000_000)
        reconfigure_log_size(mb * 1_000_000, backup_count=2)

    def _apply_tray_setting(self) -> None:
        app = QApplication.instance()
        if app:
            app.setQuitOnLastWindowClosed(not self._settings.minimize_to_tray)

    def _apply_notification_setting(self) -> None:
        self._notifications.enabled = self._settings.notifications_enabled

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._settings.minimize_to_tray and self._tray is not None:
            event.ignore()
            self.hide()
            return
        super().closeEvent(event)

    def _enqueue_package(self, action: OperationType, package: Package, handler) -> None:
        label = action.value.lower()
        self._terminal_buffer.append_stdout(f"\n[{label} {package.name} — queued]\n")
        self._queue.enqueue(action, package, lambda: handler(package))

    def _enqueue_system(self, action: OperationType, label: str, handler) -> None:
        self._terminal_buffer.append_stdout(f"\n[{action.value} {label} — queued]\n")
        stub = Package(name=label, manager="pacman", source_type=SourceType.PACMAN)
        self._queue.enqueue(action, stub, handler)

    def _on_progress_updated(self, _op: QueuedOperation, progress) -> None:
        if progress.step_label:
            text = f"{progress.step_label} ({progress.percentage:.0f}%)"
        else:
            text = f"Step {progress.current_step}/{progress.total_steps}"
        self._terminal.set_progress_text(text)

    def _on_operation_finished(self, op: QueuedOperation) -> None:
        self._terminal.set_progress_text("")
        result = OperationQueue.result_for_status(op.status)
        self._history.record(
            manager=op.manager_name,
            action=op.action,
            package=op.package_name,
            result=result,
            duration=op.duration,
        )
        self._search_svc.invalidate_cache()
        success = op.status == QueueStatus.SUCCESS

        if op.action == OperationType.INSTALL:
            self._notifications.install_finished(op.package_name, success)
        elif op.action == OperationType.REMOVE:
            self._notifications.remove_finished(op.package_name, success)
        elif op.status in (QueueStatus.FAILED, QueueStatus.CANCELLED):
            self._notifications.operation_error(
                f"{op.action.value} {op.package_name}: {op.error or op.status.value}"
            )

        if op.action == OperationType.SYNC:
            self.schedule_async(self._refresh_overview())
        if op.action == OperationType.CACHE_CLEAR:
            self.schedule_async(self._update_cache_label())
        if self._pages.currentWidget() == self._history_page:
            self.schedule_async(self._reload_history())

    async def _update_cache_label(self) -> None:
        size = await self._packages.cache_size()
        self._cache_page.set_cache_size(size)

    def _export_history(self, fmt: str) -> None:
        key, search = self._history_page.current_filter()
        records = self._history.list_filtered(filter_key=key, search=search)
        if fmt == "csv":
            path = self._history.export_csv(records)
        else:
            path = self._history.export_json(records)
        self._terminal_buffer.append_stdout(f"\n[History exported to {path}]\n")

    async def _reload_history(self) -> None:
        key, search = self._history_page.current_filter()
        entries = self._history.list_filtered(filter_key=key, search=search)
        self._history_page.set_history(entries)

    async def _load_diagnostics(self) -> None:
        items = await self._diagnostics.collect()
        self._diagnostics_page.set_items(items)

    def _on_page_changed(self, key: str) -> None:
        index = {
            "overview": 0,
            "search": 1,
            "installed": 2,
            "updates": 3,
            "aur": 4,
            "history": 5,
            "dependencies": 6,
            "cache": 7,
            "diagnostics": 8,
            "settings": 9,
            "about": 10,
        }.get(key, 0)
        self._pages.setCurrentIndex(index)
        self._animate_current_page()
        self.schedule_async(self._load_page_data(key))

    async def _load_page_data(self, key: str) -> None:
        try:
            if key == "overview":
                await self._refresh_overview()
            elif key == "installed":
                self._installed_page.show_loading(
                    "Loading installed packages",
                    "Reading the local package database and installed metadata.",
                )
                pkgs = await self._packages.list_installed()
                self._installed_page.set_packages(pkgs)
            elif key == "updates":
                self._updates_page.show_loading()
                repo, aur = await self._update_svc.list_all()
                self._updates_page.set_updates(repo, aur)
                total = len(repo) + len(aur)
                if total > 0:
                    self._notifications.updates_available(total)
            elif key == "history":
                await self._reload_history()
            elif key == "cache":
                size = await self._packages.cache_size()
                self._cache_page.set_cache_size(size)
            elif key == "aur":
                await self._do_search("", "AUR")
            elif key == "diagnostics":
                await self._load_diagnostics()
        except Exception as exc:
            logger.exception("Failed to load page %s: %s", key, exc)
            if key == "installed":
                self._installed_page.show_error(
                    "Unable to load installed packages",
                    "Pacman data is currently unavailable. Try again after syncing databases.",
                )
            elif key == "updates":
                self._updates_page.show_error(
                    "Unable to load update information right now. Retry after refreshing package databases."
                )
            elif key == "aur":
                self._aur_page.show_error(
                    "Unable to load AUR packages",
                    "The AUR backend did not respond. Check paru and try again.",
                )

    def _on_card_action(self, package: Package, action: str) -> None:
        if action == "install":
            self._enqueue_package(OperationType.INSTALL, package, self._packages.install)
        elif action == "remove":
            self._enqueue_package(OperationType.REMOVE, package, self._packages.remove)
        elif action == "update":
            self._enqueue_package(OperationType.REINSTALL, package, self._packages.reinstall)
        self.schedule_async(self._show_package(package))

    async def _refresh_overview(self) -> None:
        installed, updates, cache = await asyncio.gather(
            self._packages.list_installed(),
            self._update_svc.list_all(),
            self._packages.cache_size(),
        )
        repo, aur = updates
        total_updates = len(repo) + len(aur)
        active_manager = self._packages.registry.primary().name if self._packages.registry.primary() else "pacman"
        breakdown = f"{len(repo)} official / {len(aur)} AUR"
        self._overview.set_stats(
            len(installed),
            total_updates,
            cache,
            active_manager=active_manager,
            update_breakdown=breakdown,
        )
        recent = self._history.list_all()[:6]
        lines = [
            f"{e.timestamp:%Y-%m-%d %H:%M}  {e.action}  {e.package}  {e.result}"
            for e in recent
        ]
        self._overview.set_recent_operations(lines)

    async def _do_search(self, query: str, source_filter: str) -> None:
        self._terminal_buffer.append_stdout(
            f"\n[Search] query={query!r} filter={source_filter}\n"
        )
        target_page = (
            self._aur_page if source_filter == "AUR" or self._pages.currentWidget() == self._aur_page else self._search_page
        )
        target_label = "AUR packages" if target_page is self._aur_page else "packages"
        target_page.show_loading(
            f"Searching {target_label}",
            "Collecting package results and matching them against the active filter.",
        )
        try:
            if target_page is self._aur_page:
                results = await self._search_svc.search(query, "AUR")
            else:
                results = await self._search_svc.search(query, source_filter)
        except Exception as exc:
            logger.exception("Search failed: %s", exc)
            target_page.show_error(
                f"Unable to search {target_label}",
                "No traceback is shown in the UI. Retry the query or sync package databases.",
            )
            return

        if not results:
            title = "No packages found"
            body = "Try another search query or change the active filter."
            if target_page is self._aur_page:
                title = "No AUR packages found"
                body = "Try a broader package name or search again after refreshing the AUR index."
            target_page.show_empty(title, body)
            return
        target_page.set_packages(results)

    async def _show_package(self, package: Package) -> None:
        detail = await self._packages.enrich_package(package)
        meta = [
            f"Version: {detail.version}",
            f"Repository: {detail.repository}",
            f"Architecture: {detail.architecture}",
            f"Size: {detail.size or detail.installed_size}",
        ]
        if detail.installed_date:
            meta.append(f"Installed: {detail.installed_date:%Y-%m-%d %H:%M}")
        self._details.show_package(detail, detail.description, [m for m in meta if not m.endswith(": ")])
        tree, files, changelog = await asyncio.gather(
            self._dep_svc.get_tree(detail),
            self._packages.list_files(detail),
            self._packages.get_changelog(detail),
        )
        self._details.set_dependency_tree(tree)
        self._details.set_files(files)
        self._details.set_changelog(changelog)

    async def _load_dep_page(self) -> None:
        name = self._deps_page.package_name
        if not name:
            return
        pkg = Package(name=name, manager="pacman", source_type=SourceType.PACMAN)
        tree = await self._dep_svc.get_tree(pkg)
        self._deps_page.set_tree(tree)

    def _animate_current_page(self) -> None:
        widget = self._pages.currentWidget()
        if widget is None:
            return
        widget.setGraphicsEffect(self._page_opacity)
        self._page_anim.stop()
        self._page_anim.start()


class _DummyTray:
    """Fallback when system tray is unavailable."""

    def __init__(self, icon: QIcon) -> None:
        self._icon = icon

    def icon(self) -> QIcon:
        return self._icon

    def showMessage(self, *args, **kwargs) -> None:
        pass
