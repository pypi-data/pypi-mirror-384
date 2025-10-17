import os
import shutil
from logging import Logger
from pathlib import Path
from textwrap import indent
from typing import TypedDict

from funstall.config import Settings
from funstall.installation.model import InstallError
from funstall.packages.model import NpmDef
from funstall.proc_utils import execute


class _InstallContext(TypedDict):
    logger: Logger
    settings: Settings


def install(
    ctx: _InstallContext,
    package_name: str,
    npm_definition: NpmDef,
) -> None:
    # Node package setup
    # install-dir
    # |- node/bin/node
    # |- node_modules/.bin/the_package
    # |- package.json

    installation_dir = ctx["settings"].base_installation_dir / package_name
    node_version = npm_definition.config.node_version

    try:
        installation_dir.mkdir()
    except FileExistsError:
        if os.listdir(installation_dir):
            msg = f"Installation directory {installation_dir} is not empty"
            raise InstallError(msg)

    _install_node(ctx, installation_dir, node_version)
    _install_package(ctx, installation_dir, npm_definition)


class _LoggerContext(TypedDict):
    logger: Logger


def _install_node(
    ctx: _LoggerContext,
    installation_dir: Path,
    version: str,
) -> None:
    ctx["logger"].debug("Installing Node to %s", installation_dir)
    success, _, output = execute(
        ctx,
        [
            "fnm",
            "--fnm-dir",
            installation_dir.__str__(),
            "install",
            version,
        ],
    )
    if not success:
        msg = (
            f"Installation of Node version '{version}' failed:\n"
            f"{indent(output, '  ')}"
        )
        raise InstallError(msg)

    version_dir_parent = installation_dir / "node-versions"
    ctx["logger"].debug(
        "Installation dir content: %s",
        ", ".join(os.listdir(version_dir_parent)),
    )
    version_dir_name = next(
        d
        for d in os.listdir(version_dir_parent)
        if d.startswith("v" + version)
    )
    ctx["logger"].debug("Node is installed in %s", version_dir_name)
    shutil.move(
        version_dir_parent / version_dir_name / "installation",
        installation_dir / "node",
    )


def _install_package(
    ctx: _InstallContext,
    installation_dir: Path,
    npm_definition: NpmDef,
) -> None:
    npm_cmd = (installation_dir / "node" / "bin" / "npm").resolve().__str__()

    packages = [
        npm_definition.config.name,
        *(npm_definition.config.additional_packages or []),
    ]
    execute(
        ctx,
        [
            npm_cmd,
            "add",
            *packages,
        ],
        working_dir=installation_dir,
    )

    for exe in npm_definition.config.executables:
        src = installation_dir / "node_modules" / ".bin" / exe
        dst = ctx["settings"].bin_dir / exe
        ctx["logger"].debug("Creating symlink '%s' -> '%s'", src, dst)
        os.symlink(src, dst)


class _UpdateContext(TypedDict):
    logger: Logger
    settings: Settings


def update(
    ctx: _UpdateContext,
    package_name: str,
    npm_definition: NpmDef,
) -> None:
    installation_dir = ctx["settings"].base_installation_dir / package_name

    npm_cmd = (installation_dir / "node" / "bin" / "npm").resolve().__str__()

    packages = [
        npm_definition.config.name,
        *(npm_definition.config.additional_packages or []),
    ]
    execute(
        ctx,
        [
            npm_cmd,
            "update",
            *packages,
        ],
        working_dir=installation_dir,
    )
