"""Paru (AUR) plugin implementation."""

from __future__ import annotations

import re

from knightpac.backend.plugin import PackageManagerPlugin
from knightpac.core.process_runner import ProcessRunner
from knightpac.models.dependency import DependencyNode
from knightpac.models.package import Package, SourceType


class ParuManager(PackageManagerPlugin):
    @property
    def name(self) -> str:
        return "paru"

    def __init__(self, runner: ProcessRunner) -> None:
        super().__init__(runner)

    def _pkg(self, name: str, **kwargs) -> Package:
        return Package(
            name=name,
            source_type=SourceType.AUR,
            manager=self.name,
            repository=kwargs.pop("repository", "aur"),
            **kwargs,
        )

    async def search(self, query: str, source_filter: str = "All") -> list[Package]:
        if source_filter in ("Official", "Installed", "Updates"):
            return []
        code, stdout, _ = await self._runner.run(
            "paru",
            ["-Ss", query] if query else ["-Ss", "a"],
            echo_terminal=False,
            timeout=120.0,
        )
        if code != 0:
            return []
        return self._parse_search(stdout)

    def _parse_search(self, output: str) -> list[Package]:
        packages: list[Package] = []
        for line in output.splitlines():
            if not line.strip():
                continue
            if line.startswith((" ", "\t")):
                if packages:
                    packages[-1].description = line.strip()
                continue
            match = re.match(r"^aur/(\S+)\s+(\S+)", line)
            if match:
                name, version = match.groups()
                packages.append(self._pkg(name, version=version))
            elif line.startswith("aur/"):
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0].replace("aur/", "")
                    packages.append(
                        self._pkg(name, version=parts[1] if len(parts) > 1 else "")
                    )
        return packages

    async def list_installed(self) -> list[Package]:
        return []

    async def list_updates(self) -> list[Package]:
        code, stdout, _ = await self._runner.run(
            "paru", ["-Qua"], echo_terminal=False, timeout=120.0
        )
        if code != 0:
            return []
        packages: list[Package] = []
        for line in stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0].replace("aur/", "")
                packages.append(
                    self._pkg(
                        name,
                        version=parts[1],
                        description="AUR update available",
                        update_available=True,
                    )
                )
        return packages

    async def enrich_package(self, package: Package) -> Package:
        code, stdout, _ = await self._runner.run("paru", ["-Si", package.name])
        if code != 0:
            return package
        for line in stdout.splitlines():
            if line.startswith("Version"):
                package.version = line.split(":", 1)[-1].strip()
            elif line.startswith("Description"):
                package.description = line.split(":", 1)[-1].strip()
            elif line.startswith("Depends On"):
                package.dependencies.extend(self._parse_depends_line(line))
        return package

    async def get_files(self, name: str) -> list[str]:
        code, stdout, _ = await self._runner.run("pacman", ["-Ql", name])
        if code != 0:
            return []
        files: list[str] = []
        for line in stdout.splitlines():
            parts = line.split(None, 1)
            if len(parts) == 2:
                files.append(parts[1])
        return files

    async def get_changelog(self, name: str) -> str:
        code, stdout, _ = await self._runner.run("pacman", ["-Qc", name])
        return stdout if code == 0 else "(not installed — no changelog)"

    async def get_dependencies(self, name: str) -> DependencyNode:
        root = DependencyNode(name=name)
        code, stdout, _ = await self._runner.run("paru", ["-Si", name])
        if code != 0:
            return root
        for line in stdout.splitlines():
            if line.startswith("Depends On"):
                for dep in self._parse_depends_line(line):
                    root.add_child(DependencyNode(name=dep))
        return root

    async def install(self, package: Package) -> bool:
        code, _, _ = await self._runner.run(
            "paru", ["-S", "--noconfirm", package.name], use_pkexec=True
        )
        return code == 0

    async def remove(self, package: Package) -> bool:
        code, _, _ = await self._runner.run(
            "pacman", ["-R", "--noconfirm", package.name], use_pkexec=True
        )
        return code == 0

    async def update(self, package: Package) -> bool:
        code, _, _ = await self._runner.run(
            "paru", ["-S", "--noconfirm", package.name], use_pkexec=True
        )
        return code == 0
