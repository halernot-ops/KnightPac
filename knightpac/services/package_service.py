"""Unified package service — GUI talks only to this layer."""

from __future__ import annotations

import asyncio
import logging
import time

from knightpac.backend.registry import PackageManagerRegistry, autodiscover
from knightpac.backend.plugin import PackageManagerPlugin
from knightpac.core.process_runner import ProcessRunner
from knightpac.models.dependency import DependencyNode
from knightpac.models.package import Package, SourceType

logger = logging.getLogger("knightpac.service")
_UPDATES_TTL_SEC = 20.0
_CACHE_SIZE_TTL_SEC = 30.0

_SOURCE_FILTER_MANAGER: dict[str, str | None] = {
    "Official": "pacman",
    "AUR": "paru",
}


class PackageService:
    def __init__(self, runner: ProcessRunner, registry: PackageManagerRegistry | None = None) -> None:
        self._runner = runner
        self._registry = registry or autodiscover(runner)
        self._updates_cache: tuple[float, tuple[list[Package], list[Package]]] | None = None
        self._cache_size_cache: tuple[float, str] | None = None

    @property
    def registry(self) -> PackageManagerRegistry:
        return self._registry

    def _invalidate_runtime_caches(self) -> None:
        self._updates_cache = None
        self._cache_size_cache = None

    def _manager_for(self, package: Package) -> PackageManagerPlugin | None:
        if package.manager:
            mgr = self._registry.get(package.manager)
            if mgr:
                return mgr
        if package.source_type == SourceType.AUR:
            return self._registry.get("paru")
        if package.source_type == SourceType.FLATPAK:
            return self._registry.get("flatpak")
        return self._registry.get("pacman") or self._registry.primary()

    def _managers_for_filter(self, source_filter: str) -> list[PackageManagerPlugin]:
        if source_filter == "All":
            return self._registry.list_managers()
        target = _SOURCE_FILTER_MANAGER.get(source_filter)
        if target:
            mgr = self._registry.get(target)
            return [mgr] if mgr else []
        return self._registry.list_managers()

    async def search(self, query: str, source_filter: str = "All") -> list[Package]:
        results: list[Package] = []
        seen: set[str] = set()
        for manager in self._managers_for_filter(source_filter):
            try:
                found = await manager.search(query, source_filter)
                for pkg in found:
                    key = f"{pkg.manager}:{pkg.name}"
                    if key not in seen:
                        seen.add(key)
                        results.append(pkg)
            except Exception as exc:
                logger.exception("Search failed on %s: %s", manager.name, exc)
        return results

    async def list_installed(self) -> list[Package]:
        primary = self._registry.get("pacman")
        if not primary:
            return []
        return await primary.list_installed()

    async def list_updates(self) -> tuple[list[Package], list[Package]]:
        cached = self._updates_cache
        now = time.monotonic()
        if cached is not None and (now - cached[0]) < _UPDATES_TTL_SEC:
            repo, aur = cached[1]
            return list(repo), list(aur)

        repo: list[Package] = []
        aur: list[Package] = []
        managers = self._registry.list_managers()
        results = await asyncio.gather(
            *(manager.list_updates() for manager in managers),
            return_exceptions=True,
        )
        for manager, updates in zip(managers, results, strict=False):
            if isinstance(updates, Exception):
                logger.exception("Update listing failed on %s: %s", manager.name, updates)
                continue
            if manager.name == "paru":
                aur.extend(updates)
            else:
                repo.extend(updates)
        self._updates_cache = (now, (list(repo), list(aur)))
        return repo, aur

    async def enrich_package(self, package: Package) -> Package:
        manager = self._manager_for(package)
        if not manager:
            return package
        return await manager.enrich_package(package)

    async def list_files(self, package: Package) -> list[str]:
        manager = self._manager_for(package)
        if not manager:
            return []
        return await manager.get_files(package.name)

    async def get_changelog(self, package: Package) -> str:
        manager = self._manager_for(package)
        if not manager:
            return ""
        return await manager.get_changelog(package.name)

    async def get_dependency_tree(self, package: Package) -> DependencyNode:
        manager = self._manager_for(package)
        if not manager:
            return DependencyNode(name=package.name)
        return await manager.get_dependencies(package.name)

    async def install(self, package: Package) -> bool:
        manager = self._manager_for(package)
        if not manager:
            return False
        ok = await manager.install(package)
        if ok:
            self._invalidate_runtime_caches()
        return ok

    async def remove(self, package: Package) -> bool:
        manager = self._manager_for(package)
        if not manager:
            return False
        ok = await manager.remove(package)
        if ok:
            self._invalidate_runtime_caches()
        return ok

    async def reinstall(self, package: Package) -> bool:
        manager = self._manager_for(package)
        if not manager:
            return False
        ok = await manager.update(package)
        if ok:
            self._invalidate_runtime_caches()
        return ok

    async def sync_databases(self) -> bool:
        primary = self._registry.get("pacman")
        if not primary:
            return False
        ok = await primary.sync_databases()
        if ok:
            self._invalidate_runtime_caches()
        return ok

    async def cache_size(self) -> str:
        cached = self._cache_size_cache
        now = time.monotonic()
        if cached is not None and (now - cached[0]) < _CACHE_SIZE_TTL_SEC:
            return cached[1]
        primary = self._registry.get("pacman")
        if not primary:
            return "unknown"
        size = await primary.cache_size()
        self._cache_size_cache = (now, size)
        return size

    async def clear_cache(self, *, all_packages: bool = False) -> bool:
        primary = self._registry.get("pacman")
        if not primary:
            return False
        ok = await primary.clear_cache(all_packages=all_packages)
        if ok:
            self._invalidate_runtime_caches()
        return ok
