import shutil
from logging import Logger
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import indent
from typing import Protocol, TypedDict

import httpx

from funstall.config import Settings
from funstall.installation.model import InstallError
from funstall.packages.model import NuDef
from funstall.proc_utils import execute

_BASE_URL = (
    "https://raw.githubusercontent.com/hbibel/funstall/refs/heads/main/"
)


class _Context(TypedDict):
    logger: Logger
    settings: Settings


def install(
    ctx: _Context,
    package_name: str,
    nu_definition: NuDef,
) -> None:
    success, cmd_output = _install_or_update(ctx, package_name, nu_definition)
    if not success:
        msg = f"Failed to install {package_name}\n{indent(cmd_output, '    ')}"
        raise InstallError(msg)


def update(
    ctx: _Context,
    package_name: str,
    nu_definition: NuDef,
) -> None:
    success, cmd_output = _install_or_update(ctx, package_name, nu_definition)
    if not success:
        msg = f"Failed to update {package_name}\n{indent(cmd_output, '    ')}"
        raise InstallError(msg)


def _install_or_update(
    ctx: _Context,
    package_name: str,
    nu_definition: NuDef,
) -> tuple[bool, str]:
    if shutil.which("nu") is None:
        raise InstallError(
            "The 'nu' command was not found on the system's PATH."
        )

    update_script_config = nu_definition.config.update

    with TemporaryDirectory() as script_dir:
        script = _download_script(
            {"logger": ctx["logger"], "target_dir": Path(script_dir)},
            update_script_config,
        )

        if update_script_config.elevated_priviliges:
            cmd = ["sudo", "nu"]
        else:
            cmd = ["nu"]
        cmd.append(script.resolve().__str__())

        success, _, output = execute(ctx, cmd)
    return success, output


class _DlContext(TypedDict):
    logger: Logger
    target_dir: Path


class _HasSourceFile(Protocol):
    source_file: Path


def _download_script(ctx: _DlContext, conf: _HasSourceFile) -> Path:
    dl_path = ctx["target_dir"] / conf.source_file.name
    ctx["logger"].debug("Downloading installations script to %s", dl_path)

    url = _BASE_URL + str(conf.source_file)
    response = httpx.get(url)
    dl_path.write_bytes(response.content)

    return dl_path
