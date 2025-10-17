import logging
import sys
from typing import TypedDict

from funstall.config import Settings, Verbosity


class ApplicationContext(TypedDict):
    logger: logging.Logger
    settings: Settings


def create_application_context(settings: Settings) -> ApplicationContext:
    logger = _create_logger(settings)
    return {"logger": logger, "settings": settings}


class _CliFormatter(logging.Formatter):
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"

    FORMATTERS = {
        logging.WARNING: logging.Formatter(
            f"{YELLOW}Warning: %(message)s{RESET}"
        ),
        logging.ERROR: logging.Formatter(f"{RED}Error: %(message)s{RESET}"),
        logging.CRITICAL: logging.Formatter(f"{RED}Error: %(message)s{RESET}"),
        "DEFAULT": logging.Formatter("%(message)s"),
    }

    def format(self, record):
        formatter = self.FORMATTERS.get(
            record.levelno, self.FORMATTERS["DEFAULT"]
        )
        return formatter.format(record)


def _create_logger(settings: Settings) -> logging.Logger:
    if settings.verbosity == Verbosity.SILENT:
        level = logging.CRITICAL
    if settings.verbosity == Verbosity.ERROR:
        level = logging.WARNING
    if settings.verbosity == Verbosity.INFO:
        level = logging.INFO
    if settings.verbosity == Verbosity.DEBUG:
        level = logging.DEBUG

    root = logging.getLogger()
    # Silence all loggers
    if root.hasHandlers():
        root.handlers.clear()

    logger = logging.getLogger("funstall")
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_CliFormatter())
    logger.addHandler(handler)

    return logger
