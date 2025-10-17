from collections.abc import Callable
from dataclasses import dataclass
from functools import cache
from logging import Logger
from shutil import which
from typing import TypedDict

from funstall.packages.model import Package, PackageSource


class SelectSourceContext(TypedDict):
    logger: Logger


def select_preferred_source(
    ctx: SelectSourceContext,
    package: Package,
) -> PackageSource | None:
    logger = ctx["logger"]

    for k in _preferred_kinds():
        source = next((s for s in package.sources if s.kind == k), None)
        if source:
            logger.debug(
                "Selecting source %s for package %s", source.kind, package.name
            )
            return source
    return None


@cache
def _preferred_kinds() -> list[str]:
    return [s.kind for s in _PREFERRED if s.is_available()]


def _pacman_available() -> bool:
    return which("pacman") is not None


def _brew_available() -> bool:
    return which("brew") is not None


def _nushell_available() -> bool:
    return which("nu") is not None


def _always():
    return True


@dataclass(frozen=True)
class _Source:
    kind: str
    is_available: Callable[[], bool]


# The first source supported by the system will be selected
_PREFERRED = [
    _Source("pip", _always),
    _Source("npm", _always),
    _Source("nushell-script", _nushell_available),
    # System package managers usually wrap other tools like pip or npm, so
    # prefer the latter
    _Source("pacman", _pacman_available),
    _Source("brew", _brew_available),
]
