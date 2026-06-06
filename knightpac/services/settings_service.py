"""Application settings via QSettings."""

from __future__ import annotations

from PySide6.QtCore import QSettings


class SettingsService:
    _ORG = "KnightPac"
    _APP = "KnightPac"

    def __init__(self) -> None:
        self._settings = QSettings(self._ORG, self._APP)

    @property
    def theme(self) -> str:
        return self._settings.value("theme", "dark", type=str)

    @theme.setter
    def theme(self, value: str) -> None:
        self._settings.setValue("theme", value)

    @property
    def language(self) -> str:
        return self._settings.value("language", "en", type=str)

    @language.setter
    def language(self, value: str) -> None:
        self._settings.setValue("language", value)

    @property
    def auto_update(self) -> bool:
        return self._settings.value("auto_update", False, type=bool)

    @auto_update.setter
    def auto_update(self, value: bool) -> None:
        self._settings.setValue("auto_update", value)

    @property
    def update_interval(self) -> int:
        return self._settings.value("update_interval", 24, type=int)

    @update_interval.setter
    def update_interval(self, hours: int) -> None:
        self._settings.setValue("update_interval", hours)

    @property
    def max_log_size(self) -> int:
        return self._settings.value("max_log_size", 5, type=int)

    @max_log_size.setter
    def max_log_size(self, megabytes: int) -> None:
        self._settings.setValue("max_log_size", megabytes)

    @property
    def minimize_to_tray(self) -> bool:
        return self._settings.value("minimize_to_tray", True, type=bool)

    @minimize_to_tray.setter
    def minimize_to_tray(self, value: bool) -> None:
        self._settings.setValue("minimize_to_tray", value)

    @property
    def notifications_enabled(self) -> bool:
        return self._settings.value("notifications_enabled", True, type=bool)

    @notifications_enabled.setter
    def notifications_enabled(self, value: bool) -> None:
        self._settings.setValue("notifications_enabled", value)

    @property
    def operation_timeout(self) -> int:
        return self._settings.value("operation_timeout", 3600, type=int)

    @operation_timeout.setter
    def operation_timeout(self, seconds: int) -> None:
        self._settings.setValue("operation_timeout", seconds)

    def sync(self) -> None:
        self._settings.sync()
