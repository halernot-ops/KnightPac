"""Settings page."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from knightpac.services.settings_service import SettingsService
from knightpac.ui.theme import COLORS

_THEME_ITEMS = ("dark", "system")
_THEME_LABELS = ("Dark (KnightPac)", "System")
_LANG_ITEMS = ("en", "ru")
_LANG_LABELS = ("English", "Русский")


class SettingsPage(QWidget):
    def __init__(self, settings: SettingsService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        title = QLabel("Settings")
        title.setObjectName("title")
        layout.addWidget(title)

        form = QFormLayout()
        self.theme = QComboBox()
        self.theme.addItems(_THEME_LABELS)
        form.addRow("Theme:", self.theme)

        self.auto_update = QComboBox()
        self.auto_update.addItems(["Disabled", "Enabled"])
        form.addRow("Auto-update:", self.auto_update)

        self.update_interval = QSpinBox()
        self.update_interval.setRange(1, 168)
        self.update_interval.setSuffix(" hours")
        form.addRow("Update check interval:", self.update_interval)

        self.log_size = QSpinBox()
        self.log_size.setRange(1, 100)
        self.log_size.setSuffix(" MB")
        form.addRow("Log size limit:", self.log_size)

        self.language = QComboBox()
        self.language.addItems(_LANG_LABELS)
        form.addRow("Interface language:", self.language)

        self.minimize_tray = QComboBox()
        self.minimize_tray.addItems(["Disabled", "Enabled"])
        form.addRow("Minimize to tray:", self.minimize_tray)

        self.notifications = QComboBox()
        self.notifications.addItems(["Disabled", "Enabled"])
        form.addRow("Notifications:", self.notifications)

        layout.addLayout(form)
        note = QLabel("Settings are stored locally.")
        note.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(note)
        layout.addStretch()

        self._load_from_settings()
        self.theme.currentIndexChanged.connect(self._save_theme)
        self.auto_update.currentIndexChanged.connect(self._save_auto_update)
        self.update_interval.valueChanged.connect(self._save_interval)
        self.log_size.valueChanged.connect(self._save_log_size)
        self.language.currentIndexChanged.connect(self._save_language)
        self.minimize_tray.currentIndexChanged.connect(self._save_tray)
        self.notifications.currentIndexChanged.connect(self._save_notifications)

    def _load_from_settings(self) -> None:
        theme_idx = _THEME_ITEMS.index(self._settings.theme) if self._settings.theme in _THEME_ITEMS else 0
        self.theme.setCurrentIndex(theme_idx)
        self.auto_update.setCurrentIndex(1 if self._settings.auto_update else 0)
        self.update_interval.setValue(self._settings.update_interval)
        self.log_size.setValue(self._settings.max_log_size)
        lang_idx = _LANG_ITEMS.index(self._settings.language) if self._settings.language in _LANG_ITEMS else 0
        self.language.setCurrentIndex(lang_idx)
        self.minimize_tray.setCurrentIndex(1 if self._settings.minimize_to_tray else 0)
        self.notifications.setCurrentIndex(1 if self._settings.notifications_enabled else 0)

    def _save_theme(self, index: int) -> None:
        self._settings.theme = _THEME_ITEMS[index]
        self._settings.sync()

    def _save_auto_update(self, index: int) -> None:
        self._settings.auto_update = index == 1
        self._settings.sync()

    def _save_interval(self, value: int) -> None:
        self._settings.update_interval = value
        self._settings.sync()

    def _save_log_size(self, value: int) -> None:
        self._settings.max_log_size = value
        self._settings.sync()

    def _save_language(self, index: int) -> None:
        self._settings.language = _LANG_ITEMS[index]
        self._settings.sync()

    def _save_tray(self, index: int) -> None:
        self._settings.minimize_to_tray = index == 1
        self._settings.sync()
        if self.window():
            self.window()._apply_tray_setting()

    def _save_notifications(self, index: int) -> None:
        self._settings.notifications_enabled = index == 1
        self._settings.sync()
        if self.window():
            self.window()._apply_notification_setting()
