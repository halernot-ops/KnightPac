"""Flatpak plugin implementation."""

from __future__ import annotations

from knightpac.backend.plugin import PackageManagerPlugin
from knightpac.core.process_runner import ProcessRunner
from knightpac.models.dependency import DependencyNode
from knightpac.models.package import Package, SourceType


class FlatpakManager(PackageManagerPlugin):
    @property
    def name(self) -> str:
        return "flatpak"

    def __init__(self, runner: ProcessRunner) -> None:
        super().__init__(runner)

    def _pkg(self, name: str, **kwargs) -> Package:
        return Package(
            name=name,
            source_type=SourceType.FLATPAK,
            manager=self.name,
            repository=kwargs.pop("repository", "flathub"),
            **kwargs,
        )

    async def search(self, query: str, source_filter: str = "All") -> list[Package]:
        if source_filter not in ("All",):
            return []
        args = ["search", "--columns=application,version,description", query] if query else [
            "list",
            "--columns=application,version,description",
            "--app",
        ]
        code, stdout, _ = await self._runner.run("flatpak", args, timeout=120.0)
        if code != 0:
            return []
        packages: list[Package] = []
        for line in stdout.splitlines():
            parts = line.split("\t")
            if not parts:
                continue
            app_id = parts[0].strip()
            if not app_id or app_id == "Application":
                continue
            version = parts[1].strip() if len(parts) > 1 else ""
            desc = parts[2].strip() if len(parts) > 2 else ""
            short_name = app_id.split(".")[-1] if "." in app_id else app_id
            packages.append(
                self._pkg(short_name, version=version, description=desc, repository=app_id)
            )
        return packages

    async def list_installed(self) -> list[Package]:
        code, stdout, _ = await self._runner.run(
            "flatpak",
            ["list", "--app", "--columns=application,version,description"],
            timeout=60.0,
        )
        if code != 0:
            return []
        packages: list[Package] = []
        for line in stdout.splitlines():
            parts = line.split("\t")
            if len(parts) < 1:
                continue
            app_id = parts[0].strip()
            if not app_id or app_id == "Application":
                continue
            packages.append(
                self._pkg(
                    app_id.split(".")[-1],
                    version=parts[1].strip() if len(parts) > 1 else "",
                    description=parts[2].strip() if len(parts) > 2 else "",
                    repository=app_id,
                    installed=True,
                )
            )
        return packages

    def _ref(self, package: Package) -> str:
        ref = package.repository or package.name
        if "." in ref and not ref.startswith("app/"):
            return ref
        if "." in ref:
            return ref
        return f"app/{ref}//stable"

    async def install(self, package: Package) -> bool:
        code, _, _ = await self._runner.run(
            "flatpak",
            ["install", "-y", self._ref(package)],
            use_pkexec=False,
            timeout=1800.0,
        )
        return code == 0

    async def remove(self, package: Package) -> bool:
        code, _, _ = await self._runner.run(
            "flatpak", ["uninstall", "-y", self._ref(package)], timeout=600.0
        )
        return code == 0

    async def update(self, package: Package) -> bool:
        code, _, _ = await self._runner.run(
            "flatpak", ["update", "-y", self._ref(package)], timeout=1800.0
        )
        return code == 0

    async def get_dependencies(self, name: str) -> DependencyNode:
        return DependencyNode(name=name)

    async def get_files(self, name: str) -> list[str]:
        ref = name
        code, stdout, _ = await self._runner.run(
            "flatpak", ["info", "-r", ref], timeout=30.0
        )
        return stdout.splitlines() if code == 0 else []

    async def get_changelog(self, name: str) -> str:
        return ""

    async def list_updates(self) -> list[Package]:
        code, stdout, _ = await self._runner.run(
            "flatpak", ["remote-ls", "--updates", "flathub"], timeout=120.0
        )
        if code != 0:
            return []
        packages: list[Package] = []
        for line in stdout.splitlines():
            app_id = line.strip()
            if app_id:
                packages.append(
                    self._pkg(
                        app_id.split(".")[-1],
                        repository=app_id,
                        update_available=True,
                        description="Flatpak update available",
                    )
                )
        return packages
