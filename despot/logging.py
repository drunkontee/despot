from __future__ import annotations

import logging
import logging.config
from typing import TYPE_CHECKING

from loguru import logger
from rich.logging import RichHandler

from . import __name__ as name

if TYPE_CHECKING:
    from loguru import Record


class LoguruHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        depth = 2
        frame = logging.currentframe()
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def _remove_exception_ctx(record: Record) -> None:
    if record["exception"]:
        record["exception"] = None


def configure_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.WARNING
    logger.configure(
        handlers=[
            {
                "sink": RichHandler(
                    rich_tracebacks=debug,
                    tracebacks_show_locals=True,
                    log_time_format="[%X]",
                    markup=True,
                ),
                "format": "{message}",
                "level": level,
                "backtrace": False,  # unnecessary with `rich_tracebacks`
                "diagnose": False,  # unnecessary with `rich_tracebacks`
            }
        ],
        patcher=_remove_exception_ctx if level > logging.DEBUG else None,
        activation=[
            ("", False),
            (name, True),
        ],
    )

    logging.basicConfig(handlers=[LoguruHandler()], level=level)
    logger.debug("Running in debug mode.")
