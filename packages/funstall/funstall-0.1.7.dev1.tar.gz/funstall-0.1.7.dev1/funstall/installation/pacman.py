import shutil
from logging import Logger
from textwrap import indent
from typing import TypedDict

from funstall.config import Settings
from funstall.installation.model import InstallError
from funstall.packages.model import PacmanDef
from funstall.proc_utils import execute


class UpdateContext(TypedDict):
    logger: Logger
    settings: Settings


def install(
    ctx: UpdateContext,
    package_name: str,
    pacman_definition: PacmanDef,
) -> None:
    success, exit_code, output = _run_pacman_install(
        ctx, package_name, pacman_definition
    )

    if not success:
        msg = (
            f"Failed to install {pacman_definition.config.name}, pacman "
            f"process returned {exit_code}. Process output:\n"
            f"{indent(output, '    ')}"
        )
        raise InstallError(msg)


def update(
    ctx: UpdateContext,
    package_name: str,
    pacman_definition: PacmanDef,
) -> None:
    success, exit_code, output = _run_pacman_install(
        ctx, package_name, pacman_definition
    )

    if not success:
        msg = (
            f"Failed to update {pacman_definition.config.name}, pacman "
            f"process returned {exit_code}. Process output:\n"
            f"{indent(output, '    ')}"
        )
        raise InstallError(msg)


def _run_pacman_install(
    ctx: UpdateContext,
    package_name: str,
    pacman_definition: PacmanDef,
) -> tuple[bool, int, str]:
    if shutil.which("pacman") is None:
        raise InstallError(
            "The 'pacman' command was not found on the system's PATH."
        )

    cmd = [
        "sudo",
        "pacman",
        "-S",
        "--noconfirm",
        pacman_definition.config.name,
    ]
    return execute(ctx, cmd)
