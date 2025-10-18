import logging
import sys

import structlog
from rich.console import Console
from rich.traceback import Traceback

from ..config import settings


def get_traceback_msg(exc_info: tuple) -> Traceback:
    """Generates the custom traceback message."""
    return Traceback.from_exception(
        *exc_info,
        show_locals=False,
        extra_lines=0,
        max_frames=1,
    )


def console_exception_formatter(sio, exc_info):
    """Custom console exception formatter."""
    sio.write("\n")
    Console(file=sio, color_system="auto").print(get_traceback_msg(exc_info))


def get_logger(name: str = "apheris"):
    """Creates a logger using structlog."""
    if settings.DEBUG:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.processors.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(
                repr_native_str=True, exception_formatter=console_exception_formatter
            ),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    return structlog.get_logger(name)


logger = get_logger()
