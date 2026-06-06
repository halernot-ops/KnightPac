"""System environment diagnostics."""

from __future__ import annotations

import asyncio
import platform
import shutil
from dataclasses import dataclass

from knightpac.core.process_runner import ProcessRunner


@dataclass
class DiagnosticItem:
    name: str
    value: str
    status: str


class DiagnosticsService:
    def __init__(self, runner: ProcessRunner) -> None:
        self._runner = runner

    async def collect(self) -> list[DiagnosticItem]:
        items = [
            DiagnosticItem("Linux version", self._linux_version(), "OK"),
            DiagnosticItem("Kernel", platform.release(), "OK"),
        ]
        tools = (
            ("pacman", "pacman --version"),
            ("paru", "paru --version"),
            ("flatpak", "flatpak --version"),
            ("snap", "snap --version"),
            ("apt", "apt --version"),
            ("dnf", "dnf --version"),
            ("zypper", "zypper --version"),
            ("pkexec", "pkexec --version"),
        )
        for name, version_cmd in tools:
            items.append(await self._tool_status(name, version_cmd))
        return items

    @staticmethod
    def _linux_version() -> str:
        try:
            return platform.freedesktop_os_release().get("PRETTY_NAME", platform.platform())
        except OSError:
            return platform.platform()

    async def _tool_status(self, name: str, version_cmd: str) -> DiagnosticItem:
        binary = version_cmd.split()[0]
        if not shutil.which(binary):
            return DiagnosticItem(name, "not found", "MISSING")
        program, *args = version_cmd.split()
        code, stdout, stderr = await self._runner.run(
            program, args, timeout=15.0, echo_terminal=False
        )
        if code == 0:
            first_line = (stdout or stderr).strip().splitlines()
            value = first_line[0][:120] if first_line else "OK"
            return DiagnosticItem(name, value, "OK")
        return DiagnosticItem(name, "failed to run", "MISSING")
