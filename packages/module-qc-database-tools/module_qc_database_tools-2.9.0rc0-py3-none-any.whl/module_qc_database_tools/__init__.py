from __future__ import annotations

import logging
import logging.config
from importlib import resources
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

from module_qc_database_tools._version import __version__

data = resources.files("module_qc_database_tools") / "data"


class AppFilter(logging.Filter):
    """
    AppFilter for adding filename stem to the logging entry.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.filenameStem = Path(record.filename).stem
        return True


def rich_handler_factory() -> RichHandler:
    """
    Provide the ability to create a RichHandler on the fly as needed.
    """
    return RichHandler(
        console=Console(width=160),
        rich_tracebacks=True,
        tracebacks_suppress=[],
        markup=True,
    )


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "filters": {
        "appfilter": {
            "()": AppFilter,
        }
    },
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
        "pretty": {"format": "[[yellow]%(filenameStem)s[/]] %(message)s"},
    },
    "handlers": {
        "default": {
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",  # Default is stderr
        },
        "rich": {
            "()": rich_handler_factory,
            "formatter": "pretty",
            "filters": ["appfilter"],
        },
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": "WARNING",
            "propagate": False,
        },
        "module_qc_database_tools": {
            "handlers": ["rich"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)

__all__ = ("__version__", "data")
