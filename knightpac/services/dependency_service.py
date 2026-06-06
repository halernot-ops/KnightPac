"""Dependency service facade."""

from __future__ import annotations

from knightpac.models.dependency import DependencyNode
from knightpac.models.package import Package
from knightpac.services.package_service import PackageService


class DependencyService:
    def __init__(self, package_service: PackageService) -> None:
        self._packages = package_service

    async def get_tree(self, package: Package) -> DependencyNode:
        return await self._packages.get_dependency_tree(package)
