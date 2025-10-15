"""
Notification task helpers.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import structlog

from ..settings import BaseServiceSettings


def build_notification_task(
    settings_loader: Callable[[], BaseServiceSettings],
    *,
    logger_namespace: str | None = None,
) -> Callable[[str, str, dict[str, Any] | None], None]:
    """
    Create a notification-sending Celery task placeholder.
    """

    settings = settings_loader()
    logger_name = logger_namespace or f"{settings.logger_namespace}.tasks.notifications"
    logger = structlog.get_logger(logger_name)

    def send_notification(
        recipient: str,
        template: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        logger.info(
            "notification.send",
            recipient=recipient,
            template=template,
            env=settings_loader().env,
            context=context or {},
        )

    return send_notification
