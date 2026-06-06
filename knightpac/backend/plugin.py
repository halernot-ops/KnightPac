"""Package manager plugin interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from knightpac.core.process_runner import ProcessRunner
from knightpac.models.dependency import DependencyNode
from knightpac.models.package import Package


class PackageManagerPlugin(ABC):
    """Contract for all package manager backends (pacman, paru, apt, …)."""

    def __init__(self, runner: ProcessRunner) -> None:
        self._runner = runner

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    async def search(self, query: str, source_filter: str = "All") -> list[Package]:
        ...

    @abstractmethod
    async def install(self, package: Package) -> bool:
        ...

    @abstractmethod
    async def remove(self, package: Package) -> bool:
        ...

    @abstractmethod
    async def update(self, package: Package) -> bool:
        ...

    @abstractmethod
    async def list_installed(self) -> list[Package]:
        ...

    @abstractmethod
    async def get_dependencies(self, name: str) -> DependencyNode:
        ...

    @abstractmethod
    async def get_files(self, name: str) -> list[str]:
        ...

    @abstractmethod
    async def get_changelog(self, name: str) -> str:
        ...

    async def list_updates(self) -> list[Package]:
        return []

    async def enrich_package(self, package: Package) -> Package:
        return package

    async def sync_databases(self) -> bool:
        return False

    async def cache_size(self) -> str:
        return ""

    async def clear_cache(self, *, all_packages: bool = False) -> bool:
        return False

    def _parse_depends_line(self, line: str) -> list[str]:
        if "Depends On" not in line:
            return []
        if ":" not in line:
            return []
        _, raw = line.split(":", 1)
        deps: list[str] = []
        for part in raw.split():
            dep = part.strip().split(">")[0].split("<")[0].split("=")[0]
            if dep and dep not in ("None", "|"):
                deps.append(dep.rstrip(","))
        return deps
