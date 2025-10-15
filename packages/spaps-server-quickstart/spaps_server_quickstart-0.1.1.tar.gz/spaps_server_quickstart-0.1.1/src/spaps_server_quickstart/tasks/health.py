"""
Celery health task helpers.
"""

from __future__ import annotations

from collections.abc import Callable

import structlog

from ..settings import BaseServiceSettings


def build_ping_task(
    settings_loader: Callable[[], BaseServiceSettings],
    *,
    logger_namespace: str | None = None,
) -> Callable[[str], str]:
    """
    Create a simple Celery task that logs a heartbeat message.
    """

    settings = settings_loader()
    logger_name = logger_namespace or f"{settings.logger_namespace}.tasks.health"
    logger = structlog.get_logger(logger_name)

    def ping(message: str = "ok") -> str:
        logger.info("celery.ping", message=message, env=settings_loader().env)
        return message

    return ping
