import tomllib
from logging import Logger
from pathlib import Path
from typing import TypedDict

import tomli_w
from pydantic import BaseModel as _BaseModel
from pydantic import ConfigDict

from funstall import system_paths
from funstall.config import Settings
from funstall.packages.model import Package
from funstall.packages.package_definitions import get_package


class BaseModel(_BaseModel):
    model_config = ConfigDict(extra="forbid")


class InstalledPackage(BaseModel):
    name: str
    source_kind: str


class PackageInstalls(BaseModel):
    installed: list[InstalledPackage]


class AddInstalledContext(TypedDict):
    logger: Logger


def is_installed(package_name: str) -> bool:
    return package_name in (p.name for p in _load_installs().installed)


def add_installed(
    ctx: AddInstalledContext,
    package: Package,
    source_kind: str,
) -> None:
    ctx["logger"].debug("Adding %s to installed packages", package.name)

    if is_installed(package.name):
        ctx["logger"].warning(
            (
                "Package %s is already installed, not adding again to the "
                "installed list"
            ),
            package.name,
        )
        return

    installs = _load_installs()
    installs.installed.append(
        InstalledPackage(name=package.name, source_kind=source_kind)
    )
    new_content = tomli_w.dumps(installs.model_dump())
    _installed_packages_file().write_text(new_content)


class InstalledPackagesContext(TypedDict):
    logger: Logger
    settings: Settings


def installed_packages(ctx: InstalledPackagesContext) -> list[Package]:
    logger = ctx["logger"]
    settings = ctx["settings"]

    packages = []
    for p in _load_installs().installed:
        package = get_package(settings, p.name)
        if not package:
            logger.warning(
                (
                    "Package %s is installed, but it does not appear to be in "
                    "the package definition file"
                ),
                p,
            )
        else:
            packages.append(package)
    return packages


def get_install_source(package_name: str) -> str | None:
    return next(
        (
            p.source_kind
            for p in _load_installs().installed
            if p.name == package_name
        ),
        None,
    )


def _installed_packages_file() -> Path:
    installs_file = system_paths.user_data_dir() / "installed.toml"

    if not installs_file.parent.exists():
        installs_file.parent.mkdir(parents=True)
    if not installs_file.exists():
        installs_file.write_text("installed=[]")

    return installs_file


def _load_installs() -> PackageInstalls:
    installs_file = _installed_packages_file()
    content = tomllib.loads(installs_file.read_text())
    return PackageInstalls.model_validate(content)
