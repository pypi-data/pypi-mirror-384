"""
Logging helpers shared across Sweet Potato services.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Literal

import structlog
from structlog.dev import ConsoleRenderer
from structlog.processors import JSONRenderer
from structlog.types import Processor

from .settings import BaseServiceSettings


def _build_processors(settings: BaseServiceSettings) -> list[Processor]:
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.add_log_level,
    ]

    if settings.log_include_tracebacks:
        processors.append(structlog.processors.format_exc_info)

    if settings.log_format == "console":
        processors.append(ConsoleRenderer(colors=settings.env == "dev"))
    else:
        processors.extend(
            [
                structlog.processors.StackInfoRenderer(),
                JSONRenderer(),
            ]
        )
    return processors


def configure_logging(settings: BaseServiceSettings) -> None:
    """
    Configure structlog + standard logging bridge.
    """

    resolved_level: int | Literal[0] = logging.getLevelName(settings.log_level.upper())
    if isinstance(resolved_level, str):
        resolved_level = logging.INFO

    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if settings.log_file_path:
        log_path = Path(settings.log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(
            RotatingFileHandler(
                log_path,
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
        )

    logging.basicConfig(level=resolved_level, format="%(message)s", handlers=handlers)
    structlog.configure(
        processors=_build_processors(settings),
        wrapper_class=structlog.make_filtering_bound_logger(resolved_level),
        cache_logger_on_first_use=True,
    )
