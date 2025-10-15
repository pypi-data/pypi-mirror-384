from __future__ import annotations

from typing import Any, AsyncIterator

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from spaps_server_quickstart.api.health import HealthRouterFactory
from spaps_server_quickstart.settings import BaseServiceSettings


class ExampleSettings(BaseServiceSettings):
    app_name: str = "Health Service"
    service_slug: str = "health-service"
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/health"


class SuccessfulSession:
    async def execute(self, *_: Any, **__: Any) -> None:  # pragma: no cover - executed via router
        return None


class FailingSession:
    async def execute(self, *_: Any, **__: Any) -> None:  # pragma: no cover - executed via router
        raise SQLAlchemyError()


async def successful_dependency() -> AsyncIterator[SuccessfulSession]:
    yield SuccessfulSession()


async def failing_dependency() -> AsyncIterator[FailingSession]:
    yield FailingSession()


def extra_metrics(settings: BaseServiceSettings, session: Any) -> dict[str, Any]:
    return {"service": settings.app_name, "session_type": type(session).__name__ if session else None}


def test_health_router_with_database_success() -> None:
    factory = HealthRouterFactory(
        settings_loader=lambda: ExampleSettings(),
        session_dependency=successful_dependency,
        extra_metrics_provider=extra_metrics,
    )
    app = FastAPI()
    app.include_router(factory.create_router())

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database_ready"] is True
    assert payload["details"]["service"] == "Health Service"


def test_health_router_with_database_failure() -> None:
    factory = HealthRouterFactory(
        settings_loader=lambda: ExampleSettings(),
        session_dependency=failing_dependency,
    )
    app = FastAPI()
    app.include_router(factory.create_router())

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["database_ready"] is False


def test_health_router_without_database_async_metrics() -> None:
    async def async_metrics(settings: BaseServiceSettings, session: Any) -> dict[str, Any]:
        return {"service": settings.service_slug, "session": session}

    factory = HealthRouterFactory(
        settings_loader=lambda: ExampleSettings(),
        extra_metrics_provider=async_metrics,
    )
    app = FastAPI()
    app.include_router(factory.create_router())

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["database_ready"] is True
    assert payload["details"]["service"] == "health-service"
