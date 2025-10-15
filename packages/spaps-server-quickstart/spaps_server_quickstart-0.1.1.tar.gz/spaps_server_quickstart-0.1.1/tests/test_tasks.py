from __future__ import annotations

from typing import Any

from spaps_server_quickstart.tasks import (
    build_notification_task,
    build_ping_task,
    create_celery_app,
)
from spaps_server_quickstart.settings import BaseServiceSettings


class ExampleSettings(BaseServiceSettings):
    service_slug: str | None = "task-service"
    app_name: str = "Task Service"
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/tasks"
    redis_url: str = "redis://localhost:6380/0"


class DummyLogger:
    def __init__(self) -> None:
        self.records: list[tuple[str, dict[str, Any]]] = []

    def info(self, event: str, **kwargs: Any) -> None:
        self.records.append((event, kwargs))


def test_build_ping_task(monkeypatch) -> None:
    logger = DummyLogger()

    import structlog

    monkeypatch.setattr(structlog, "get_logger", lambda *_: logger)

    def loader() -> ExampleSettings:
        return ExampleSettings()

    ping = build_ping_task(loader)

    assert ping("pong") == "pong"
    event, payload = logger.records[0]
    assert event == "celery.ping"
    assert payload["env"] == "dev"


def test_build_notification_task(monkeypatch) -> None:
    logger = DummyLogger()

    import structlog

    monkeypatch.setattr(structlog, "get_logger", lambda *_: logger)

    def loader() -> ExampleSettings:
        return ExampleSettings()

    notify = build_notification_task(loader)

    notify("user@example.com", "welcome", {"name": "User"})
    event, payload = logger.records[0]
    assert event == "notification.send"
    assert payload["template"] == "welcome"
    assert payload["context"] == {"name": "User"}


def test_create_celery_app_uses_settings(monkeypatch) -> None:
    discovered: dict[str, Any] = {}

    def fake_autodiscover(tasks):
        discovered["tasks"] = tasks

    app = create_celery_app(ExampleSettings(), task_modules=["spaps.tasks"])
    monkeypatch.setattr(app, "autodiscover_tasks", fake_autodiscover)
    app.autodiscover_tasks(["spaps.tasks"])

    assert app.conf.task_default_queue == "default"
    assert app.conf.task_ignore_result is True
    assert app.conf.timezone == "UTC"
    assert discovered["tasks"] == ["spaps.tasks"]
