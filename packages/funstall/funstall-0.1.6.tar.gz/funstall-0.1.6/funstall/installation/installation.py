import os
import shutil
import sys
from logging import Logger
from pathlib import Path
from typing import TypedDict

from funstall.config import SelfUpdateStrategy, Settings
from funstall.installation import npm, nushell, pacman, pip
from funstall.installation.model import InstallError
from funstall.installation.source_priorities import select_preferred_source
from funstall.packages.installs import (
    add_installed,
    get_install_source,
    installed_packages,
    is_installed,
)
from funstall.packages.model import (
    Package,
    PackageError,
    PipConfig,
    PipDef,
)
from funstall.packages.package_definitions import (
    get_package,
    update_package_definitions,
)


class InstallContext(TypedDict):
    settings: Settings
    logger: Logger


def install(ctx: InstallContext, package_name: str) -> None:
    _update_funstall(ctx)
    _warn_if_exe_dir_not_on_path(ctx)

    ctx["settings"].base_installation_dir.mkdir(parents=True, exist_ok=True)

    ctx["logger"].info("Installing package '%s'", package_name)

    pkg = get_package(ctx["settings"], package_name)
    if not pkg:
        msg = f"Package '{package_name}' not found"
        raise InstallError(msg)

    if is_installed(pkg.name):
        ctx["logger"].info("Package %s is already installed", pkg.name)

    source = select_preferred_source(ctx, pkg)
    if not source:
        msg = f"No available source for '{package_name}' on this system"
        raise InstallError(msg)
    if source.kind == "pip":
        pip.install(ctx, pkg.name, source)
    if source.kind == "npm":
        _ensure_fnm(ctx)
        npm.install(ctx, pkg.name, source)
    elif source.kind == "pacman":
        pacman.install(ctx, pkg.name, source)
    elif source.kind == "nushell-script":
        nushell.install(ctx, pkg.name, source)
    # TODO brew

    add_installed(ctx, pkg, source.kind)


class UpdateContext(TypedDict):
    settings: Settings
    logger: Logger


def update(ctx: UpdateContext, package_names: list[str]) -> None:
    logger = ctx["logger"]

    _update_funstall(ctx)

    # TODO if the source of a package changes in packages.yaml, we should
    # remove the old package and install the new one. This is a tough nut to
    # crack because the format of packages.yaml may also change. I will not
    # handle this edge case for now, but I added a version field in the
    # packages definition file in preparation.

    packages: list[Package] = []
    for name in package_names:
        pkg = get_package(ctx["settings"], name)
        if not pkg:
            logger.warning(
                (
                    "Package %s does not exist, it may have been deleted from "
                    "the package definitions file."
                ),
                name,
            )
        else:
            packages.append(pkg)

    logger.debug("Updating %d packages", len(packages))
    for package in packages:
        _update_package(ctx, package)


def update_all(ctx: UpdateContext) -> None:
    _update_funstall(ctx)

    for package in installed_packages(ctx):
        _update_package(ctx, package)


def _update_funstall(ctx: UpdateContext) -> None:
    self_update_successful = True
    if ctx["settings"].skip_self_update:
        ctx["logger"].debug("Skipping self update")
    else:
        try:
            _update_self(ctx)
            ctx["logger"].debug("Self update complete")

            # Restart with new code
            args = sys.argv + ["--skip-self-update"]
            ctx["logger"].debug(
                "Restarting %s as `%s`",
                sys.executable,
                " ".join([sys.executable] + args),
            )
            for h in ctx["logger"].handlers:
                h.flush()
            os.execv(sys.executable, [sys.executable] + args)
        except InstallError as e:
            ctx["logger"].warning(
                "Self update failed, will not update package list" + e.msg
            )
            self_update_successful = False

    # If the self-update was not successful, we don't need to fail the
    # entire program, but we should not update the package list in case the
    # format has changed and our current version cannot handle the new format.
    if (
        self_update_successful
        and not ctx["settings"].skip_package_definitions_file_download
    ):
        ctx["logger"].info("Updating package list ...")
        try:
            update_package_definitions(ctx["settings"])
            ctx["logger"].debug("Package list updated")
        except PackageError as e:
            ctx["logger"].warning(
                "Could not update package list, continuing with old package "
                "definitions. This will lead to a crash if the new funstall "
                "version is not compatible with the old package list."
            )
            ctx["logger"].debug("Cause: %s", e)
    else:
        if not self_update_successful:
            ctx["logger"].debug("Self update not successful")
        if ctx["settings"].skip_package_definitions_file_download:
            ctx["logger"].debug("Set to skip package file download")
        ctx["logger"].debug("Skipping package definitions file download")


def _update_self(ctx: UpdateContext) -> None:
    logger = ctx["logger"]

    logger.info("Updating funstall")

    if ctx["settings"].self_update_strategy == SelfUpdateStrategy.NOOP:
        logger.info("Noop update strategy")
    elif ctx["settings"].self_update_strategy == SelfUpdateStrategy.PYPI:
        logger.debug("Updating funstall using pip")
        pip_path = Path(sys.executable).parent / "pip"
        logger.debug(
            "funstall is installed at %s", str(pip_path.parent.parent)
        )

        p = PipDef(
            kind="pip",
            config=PipConfig(
                name="funstall",
                python_version="3.13",
                executables=["funstall"],
            ),
        )
        pip.update(ctx, "funstall", p, pip_bin=pip_path.__str__())


class UpdatePackageContext(TypedDict):
    logger: Logger
    settings: Settings


def _update_package(ctx: UpdatePackageContext, package: Package) -> None:
    installed_from_source = get_install_source(package.name)
    if not installed_from_source:
        msg = (
            "Could not determine installation source for package "
            f"{package.name}. Has this package been installed?"
        )
        raise InstallError(msg)

    source_def = next(
        (s for s in package.sources if s.kind == installed_from_source),
        None,
    )
    if not source_def:
        msg = (
            f"Package {package.name} has been installed via "
            f"{installed_from_source}, but installation via "
            f"{installed_from_source} is not available anymore. "
            "Try re-installing the package."
        )
        raise InstallError(msg)

    if source_def.kind == "pip":
        pip.update(ctx, package.name, source_def)
    if source_def.kind == "npm":
        npm.update(ctx, package.name, source_def)
    elif source_def.kind == "pacman":
        pacman.update(ctx, package.name, source_def)
    elif source_def.kind == "nushell-script":
        nushell.update(ctx, package.name, source_def)
    # TODO brew


def _ensure_fnm(ctx: InstallContext) -> None:
    if fnm_path := shutil.which("fnm"):
        ctx["logger"].debug("fnm found at %s", fnm_path)
        return

    ctx["logger"].info("Installing fnm")
    install(ctx, "fnm")


class _WarnIfExeNotOnPathCtx(TypedDict):
    logger: Logger
    settings: Settings


def _warn_if_exe_dir_not_on_path(ctx: _WarnIfExeNotOnPathCtx) -> None:
    bin_dir = ctx["settings"].bin_dir
    if os_path := os.environ.get("PATH"):
        on_path = False
        d = str(bin_dir.resolve())
        for p in os_path.split(os.pathsep):
            if str(Path(p).resolve()) == d:
                on_path = True
                break

        if not on_path:
            ctx["logger"].warning(
                f"The user binary directory '{d}' is not found in the "
                "system's PATH. You may need to add it manually to run "
                "executables installed here."
            )
