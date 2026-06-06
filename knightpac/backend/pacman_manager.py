"""Pacman plugin implementation."""

from __future__ import annotations

import re
import shutil
from datetime import datetime

from knightpac.backend.pactree_parser import parse_pactree
from knightpac.backend.plugin import PackageManagerPlugin
from knightpac.core.process_runner import ProcessRunner
from knightpac.models.dependency import DependencyNode
from knightpac.models.package import Package, SourceType

_QI_DATE_FORMATS = ("%a %b %d %H:%M:%S %Y", "%Y-%m-%d")


class PacmanManager(PackageManagerPlugin):
    @property
    def name(self) -> str:
        return "pacman"

    def __init__(self, runner: ProcessRunner) -> None:
        super().__init__(runner)
        self._installed_cache: list[Package] | None = None

    def _invalidate_installed_cache(self) -> None:
        self._installed_cache = None

    def _pkg(
        self,
        name: str,
        *,
        version: str = "",
        description: str = "",
        source_type: SourceType = SourceType.PACMAN,
        **kwargs,
    ) -> Package:
        return Package(
            name=name,
            version=version,
            description=description,
            source_type=source_type,
            manager=self.name,
            **kwargs,
        )

    async def search(self, query: str, source_filter: str = "All") -> list[Package]:
        if source_filter == "AUR":
            return []
        if source_filter == "Installed":
            installed = await self.list_installed()
            q = query.lower()
            return [
                p
                for p in installed
                if q in p.name.lower() or q in p.description.lower()
            ]
        if source_filter == "Updates":
            updates = await self.list_updates()
            for p in updates:
                p.update_available = True
            return updates

        code, stdout, _ = await self._runner.run(
            "pacman", ["-Ss", query] if query else ["-Ss"]
        )
        if code != 0:
            return []
        return self._parse_search(stdout)

    def _parse_search(self, output: str) -> list[Package]:
        packages: list[Package] = []
        current_repo = ""
        for line in output.splitlines():
            if not line.strip():
                continue
            if line.startswith((" ", "\t")):
                if packages:
                    packages[-1].description = line.strip()
                continue
            match = re.match(r"^(\S+)/(\S+)\s+(\S+)\s+(\S+)\s+\[", line)
            if match:
                repo, name, version, _arch = match.groups()
                size_match = re.search(r"\(([^)]+)\)", line)
                size = size_match.group(1) if size_match else ""
                current_repo = repo
                packages.append(
                    self._pkg(
                        name,
                        version=version,
                        size=size,
                        repository=repo,
                        source_type=SourceType.PACMAN,
                    )
                )
        for p in packages:
            if not p.repository:
                p.repository = current_repo
        return packages

    @staticmethod
    def _parse_install_date(raw: str) -> datetime | None:
        for fmt in _QI_DATE_FORMATS:
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
        return None

    @classmethod
    def _parse_qi_block(cls, lines: list[str]) -> tuple[str, str, datetime | None, str]:
        name = ""
        installed_size = ""
        description = ""
        installed_date: datetime | None = None
        for line in lines:
            if line.startswith("Name"):
                name = line.split(":", 1)[-1].strip()
            elif line.startswith("Installed Size"):
                installed_size = line.split(":", 1)[-1].strip()
            elif line.startswith("Install Date"):
                installed_date = cls._parse_install_date(line.split(":", 1)[-1].strip())
            elif line.startswith("Description"):
                description = line.split(":", 1)[-1].strip()
        return name, installed_size, installed_date, description

    @classmethod
    def _parse_all_qi(
        cls, output: str
    ) -> dict[str, tuple[str, datetime | None, str]]:
        """Map package name → (installed_size, install_date, description)."""
        meta: dict[str, tuple[str, datetime | None, str]] = {}
        block: list[str] = []
        for line in output.splitlines():
            if not line.strip():
                if block:
                    name, size, dt, desc = cls._parse_qi_block(block)
                    if name:
                        meta[name] = (size, dt, desc)
                block = []
            else:
                block.append(line)
        if block:
            name, size, dt, desc = cls._parse_qi_block(block)
            if name:
                meta[name] = (size, dt, desc)
        return meta

    async def list_installed(self) -> list[Package]:
        if self._installed_cache is not None:
            return list(self._installed_cache)

        self._runner.user_message("Loading installed packages...")
        code, q_stdout, _ = await self._runner.run(
            "pacman", ["-Q"], echo_terminal=False, timeout=60.0
        )
        if code != 0:
            return []

        code, qi_stdout, _ = await self._runner.run(
            "pacman", ["-Qi"], echo_terminal=False, timeout=300.0
        )
        meta = self._parse_all_qi(qi_stdout) if code == 0 else {}

        packages: list[Package] = []
        for line in q_stdout.splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            name, version = parts[0], parts[1]
            installed_size, installed_date, description = meta.get(name, ("", None, ""))
            packages.append(
                self._pkg(
                    name,
                    version=version,
                    description=description,
                    installed_size=installed_size,
                    installed=True,
                    source_type=SourceType.PACMAN,
                    installed_date=installed_date,
                )
            )

        self._installed_cache = packages
        self._runner.user_message(f"Loaded {len(packages)} packages")
        return list(packages)

    async def list_updates(self) -> list[Package]:
        code, stdout, _ = await self._runner.run(
            "pacman", ["-Qu"], echo_terminal=False, timeout=120.0
        )
        if code != 0:
            return []
        packages: list[Package] = []
        for line in stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                packages.append(
                    self._pkg(
                        parts[0],
                        version=parts[1],
                        source_type=SourceType.PACMAN,
                        description="Repository update available",
                        update_available=True,
                    )
                )
        return packages

    async def enrich_package(self, package: Package) -> Package:
        code, stdout, _ = await self._runner.run(
            "pacman", ["-Qi", package.name], echo_terminal=False, timeout=30.0
        )
        if code != 0:
            code, stdout, _ = await self._runner.run(
                "pacman", ["-Si", package.name], echo_terminal=False, timeout=30.0
            )
        if code != 0:
            return package
        block = [ln for ln in stdout.splitlines() if ln.strip()]
        _name, size, installed_date, desc = self._parse_qi_block(block)
        if desc:
            package.description = desc
        if size:
            package.installed_size = size
        if installed_date:
            package.installed_date = installed_date
            package.installed = True
        for line in block:
            if line.startswith("Version"):
                package.version = line.split(":", 1)[-1].strip()
            elif line.startswith("Repository"):
                package.repository = line.split(":", 1)[-1].strip()
            elif line.startswith("Architecture") or line.startswith("Arch"):
                package.architecture = line.split(":", 1)[-1].strip()
            elif line.startswith("Download Size"):
                package.size = line.split(":", 1)[-1].strip()
            elif line.startswith("Depends On"):
                package.dependencies.extend(self._parse_depends_line(line))
        return package

    async def get_files(self, name: str) -> list[str]:
        code, stdout, _ = await self._runner.run(
            "pacman", ["-Ql", name], echo_terminal=False, timeout=60.0
        )
        if code != 0:
            return []
        files: list[str] = []
        for line in stdout.splitlines():
            parts = line.split(None, 1)
            if len(parts) == 2:
                files.append(parts[1])
        return files

    async def get_changelog(self, name: str) -> str:
        code, stdout, _ = await self._runner.run(
            "pacman", ["-Qc", name], echo_terminal=False, timeout=60.0
        )
        return stdout if code == 0 else ""

    async def get_dependencies(self, name: str) -> DependencyNode:
        if shutil.which("pactree"):
            code, stdout, _ = await self._runner.run(
                "pactree", [name], echo_terminal=False, timeout=120.0
            )
            if code == 0 and stdout.strip():
                return parse_pactree(stdout, name)
        return await self._fallback_dependencies(name)

    async def _fallback_dependencies(self, name: str) -> DependencyNode:
        root = DependencyNode(name=name)
        code, stdout, _ = await self._runner.run(
            "pacman", ["-Qi", name], echo_terminal=False, timeout=30.0
        )
        if code != 0:
            code, stdout, _ = await self._runner.run(
                "pacman", ["-Si", name], echo_terminal=False, timeout=30.0
            )
        if code != 0:
            return root
        for line in stdout.splitlines():
            if line.startswith("Depends On"):
                for dep in self._parse_depends_line(line):
                    root.add_child(DependencyNode(name=dep))
        return root

    async def install(self, package: Package) -> bool:
        code, _, _ = await self._runner.run(
            "pacman", ["-S", "--noconfirm", package.name], use_pkexec=True
        )
        if code == 0:
            self._invalidate_installed_cache()
        return code == 0

    async def remove(self, package: Package) -> bool:
        code, _, _ = await self._runner.run(
            "pacman", ["-R", "--noconfirm", package.name], use_pkexec=True
        )
        if code == 0:
            self._invalidate_installed_cache()
        return code == 0

    async def update(self, package: Package) -> bool:
        code, _, _ = await self._runner.run(
            "pacman", ["-S", "--noconfirm", package.name], use_pkexec=True
        )
        if code == 0:
            self._invalidate_installed_cache()
        return code == 0

    async def sync_databases(self) -> bool:
        return (await self._runner.run("pacman", ["-Sy"], use_pkexec=True))[0] == 0

    async def cache_size(self) -> str:
        code, stdout, _ = await self._runner.run(
            "du", ["-sh", "/var/cache/pacman/pkg"], echo_terminal=False, timeout=30.0
        )
        if code != 0:
            return "unknown"
        return stdout.split()[0] if stdout.split() else "unknown"

    async def clear_cache(self, *, all_packages: bool = False) -> bool:
        args = ["-Sc", "--noconfirm"] if not all_packages else ["-Scc", "--noconfirm"]
        code, _, _ = await self._runner.run("pacman", args, use_pkexec=True)
        return code == 0
