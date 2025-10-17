import os
import shutil
from logging import Logger
from textwrap import indent
from typing import TypedDict

from packaging.version import InvalidVersion, Version

from funstall.config import Settings
from funstall.installation.model import InstallError
from funstall.packages.model import PipDef
from funstall.proc_utils import execute
from funstall.system_paths import user_exe_dir


class UpdateContext(TypedDict):
    logger: Logger
    settings: Settings


def install(
    ctx: UpdateContext,
    package_name: str,
    pip_definition: PipDef,
) -> None:
    python_exe = f"python{pip_definition.config.python_version}"
    if shutil.which(python_exe) is None:
        python_exe = _install_python(ctx, pip_definition.config.python_version)

    installation_dir = ctx["settings"].base_installation_dir / package_name

    cmd = [python_exe, "-m", "venv", str(installation_dir.resolve())]
    success, exit_code, output = execute(ctx, cmd)
    if not success:
        msg = (
            f"Failed to create venv for {pip_definition.config.name}, {python_exe} "
            f"process returned {exit_code}. Process output:\n"
            f"{indent(output, '    ')}"
        )
        raise InstallError(msg)

    pip_bin = (
        (ctx["settings"].base_installation_dir / package_name / "bin" / "pip")
        .resolve()
        .__str__()
    )

    cmd = [
        pip_bin,
        "install",
        pip_definition.config.name,
    ]
    success, exit_code, output = execute(ctx, cmd)
    if not success:
        msg = f"""
            Failed to install {pip_definition.config.name}, {pip_bin} process returned
            {exit_code}. Pip output:
            \n{indent(output, "    ")}
        """
        raise InstallError(msg)

    for exe in pip_definition.config.executables:
        src = installation_dir / "bin" / exe
        dst = ctx["settings"].bin_dir / exe
        ctx["logger"].debug("Creating symlink '%s' -> '%s'", src, dst)
        os.symlink(src, dst)


def update(
    ctx: UpdateContext,
    package_name: str,
    pip_definition: PipDef,
    *,
    pip_bin: str | None = None,
) -> None:
    # TODO:
    # Check if Python version is still supported; if not, recreate venv
    # pip metadata for checking Python version: https://pypi.org/pypi/<package name>/json
    # https://pypi.org/pypi/funstall/json
    # -> key info.requires_python
    # Use the packaging package:
    # SpecifierSet(required).contains(Version(installed))

    if not pip_bin:
        pip_bin = (
            (
                ctx["settings"].base_installation_dir
                / package_name
                / "bin"
                / "pip"
            )
            .resolve()
            .__str__()
        )

    cmd = [
        pip_bin,
        "install",
        "--upgrade",
        pip_definition.config.name,
    ]
    success, exit_code, output = execute(ctx, cmd)
    if not success:
        msg = f"""
            Failed to update {pip_definition.config.name}, {pip_bin} process returned
            {exit_code}. Pip output:
            \n{indent(output, "    ")}
        """
        raise InstallError(msg)
    else:
        ctx["logger"].debug("Pip output:\n%s", output)


class LoggerContext(TypedDict):
    logger: Logger


def _install_python(ctx: LoggerContext, version_specifier: str) -> str:
    try:
        Version(version_specifier)
    except InvalidVersion as e:
        raise InstallError("Invalid version") from e

    cmd = [
        "pyenv",
        "install",
        "--skip-existing",
        version_specifier,
    ]
    success, exit_code, output = execute(ctx, cmd)
    if not success:
        msg = (
            "Failed to install a Python version matching specifier "
            f"'{version_specifier}'. pyenv exited with {exit_code}. "
            f"pyenv output:\n{indent(output, ' ')}"
        )
        raise InstallError(msg)

    # return path to Python
    success, exit_code, output = execute(
        ctx, ["pyenv", "which", f"python{version_specifier}"]
    )
    if not success:
        msg = (
            "Failed to install a Python version matching specifier "
            f"'{version_specifier}'. pyenv exited with {exit_code}. "
            f"pyenv output:\n{indent(output, ' ')}"
        )
        raise InstallError(msg)
    return output
