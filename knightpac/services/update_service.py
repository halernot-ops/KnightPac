"""Update service facade."""

from __future__ import annotations

from knightpac.models.package import Package
from knightpac.services.package_service import PackageService


class UpdateService:
    def __init__(self, package_service: PackageService) -> None:
        self._packages = package_service

    async def list_repo_updates(self) -> list[Package]:
        repo, _ = await self._packages.list_updates()
        return repo

    async def list_aur_updates(self) -> list[Package]:
        _, aur = await self._packages.list_updates()
        return aur

    async def list_all(self) -> tuple[list[Package], list[Package]]:
        return await self._packages.list_updates()
