"""
Celery application factory utilities.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from celery import Celery

from ..settings import BaseServiceSettings


def create_celery_app(
    settings: BaseServiceSettings,
    *,
    task_modules: Sequence[str],
    extra_config: dict[str, Any] | None = None,
) -> Celery:
    """
    Build a Celery application configured from service settings.
    """

    app = Celery(
        settings.celery_app_name,
        broker=settings.resolved_celery_broker_url,
        backend=settings.resolved_celery_result_backend,
    )
    config: dict[str, Any] = {
        "task_default_queue": "default",
        "task_ignore_result": True,
        "timezone": "UTC",
    }
    if extra_config:
        config.update(extra_config)
    app.conf.update(config)
    if task_modules:
        app.autodiscover_tasks(list(task_modules))
    return app
