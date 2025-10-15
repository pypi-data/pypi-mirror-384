from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.middleware.cors import CORSMiddleware
from starlette.testclient import TestClient

from spaps_server_quickstart import app_factory
from starlette.middleware.base import BaseHTTPMiddleware

from spaps_server_quickstart.settings import BaseServiceSettings


class ExampleSettings(BaseServiceSettings):
    app_name: str = "App Factory"
    service_slug: str = "app-factory"
    database_url: str = "postgresql+asyncpg://user:pass@host:5432/app-factory"
    spaps_auth_enabled: bool = False


def test_create_app_includes_router_and_request_logging(monkeypatch) -> None:
    router = APIRouter()

    @router.get("/hello")
    def hello() -> dict[str, str]:  # pragma: no cover - executed via client
        return {"message": "hi"}

    loader_calls: list[int] = []

    def settings_loader() -> ExampleSettings:
        loader_calls.append(1)
        return ExampleSettings()

    monkeypatch.setattr(app_factory, "configure_logging", lambda *_: None)

    class CustomMiddleware(BaseHTTPMiddleware):
        def __init__(self, app, flag: bool = False):  # type: ignore[override]
            self.flag = flag
            super().__init__(app)

        async def dispatch(self, request, call_next):  # type: ignore[override]
            return await call_next(request)

    app = app_factory.create_app(
        settings_loader=settings_loader,
        api_router=router,
        additional_middlewares=[(CustomMiddleware, {"flag": True})],
    )

    client = TestClient(app)
    response = client.get("/hello")

    assert response.status_code == 200
    assert response.json()["message"] == "hi"
    assert loader_calls, "settings loader should be invoked"

    middleware_classes = [mw.cls for mw in app.user_middleware]
    assert app_factory.RequestLoggingMiddleware in middleware_classes
    assert CustomMiddleware in middleware_classes


def test_create_app_configures_spaps_auth(monkeypatch) -> None:
    router = APIRouter()

    class DummySettings(ExampleSettings):
        spaps_auth_enabled: bool = False
        spaps_api_key: str | None = "key"
        spaps_application_id: str | None = "app"
        spaps_auth_exempt_paths: tuple[str, ...] = ("/settings-only",)

    recorded_kwargs: dict[str, Any] = {}

    class DummyAuthService:
        def __init__(self) -> None:
            self.closed = False

        async def aclose(self) -> None:
            self.closed = True

    dummy_service = DummyAuthService()

    def fake_settings_loader() -> DummySettings:
        return DummySettings()

    def fake_build_auth(settings: BaseServiceSettings) -> object:
        recorded_kwargs["settings"] = settings
        return dummy_service

    class DummyAuthMiddleware(BaseHTTPMiddleware):
        def __init__(self, app, **kwargs):  # type: ignore[override]
            recorded_kwargs.update(kwargs)
            super().__init__(app)

        async def dispatch(self, request, call_next):  # type: ignore[override]
            return await call_next(request)

    monkeypatch.setattr(app_factory, "SpapsAuthMiddleware", DummyAuthMiddleware)

    monkeypatch.setattr(app_factory, "configure_logging", lambda *_: None)
    monkeypatch.setattr(app_factory, "build_spaps_auth_service", fake_build_auth)
    app = app_factory.create_app(
        settings_loader=fake_settings_loader,
        api_router=router,
        enable_spaps_auth=True,
        auth_exempt_paths={"/custom"},
    )

    assert app.state.spaps_auth_service is dummy_service
    assert isinstance(recorded_kwargs["settings"], DummySettings)

    middleware_entry = next(
        mw for mw in app.user_middleware if mw.cls is DummyAuthMiddleware
    )
    options = middleware_entry.kwargs
    assert options["auth_service"] is dummy_service
    assert {"/health", "/docs", "/redoc"}.issubset(options["exempt_paths"])
    assert "/settings-only" in options["exempt_paths"]
    assert "/custom" in options["exempt_paths"]

    assert dummy_service.closed is False
    with TestClient(app):
        pass

    assert dummy_service.closed is True


def test_create_app_applies_cors_configuration(monkeypatch) -> None:
    router = APIRouter()

    class CorsSettings(ExampleSettings):
        spaps_auth_enabled: bool = False
        cors_allow_origins: tuple[str, ...] = ("https://app.example.com",)
        cors_allow_methods: tuple[str, ...] = ("GET", "POST")
        cors_allow_headers: tuple[str, ...] = ("Authorization", "X-Request-ID")
        cors_expose_headers: tuple[str, ...] = ("X-Trace",)
        cors_allow_credentials: bool = False
        cors_max_age: int = 3600

    def loader() -> CorsSettings:
        return CorsSettings()

    monkeypatch.setattr(app_factory, "configure_logging", lambda *_: None)

    app = app_factory.create_app(
        settings_loader=loader,
        api_router=router,
    )

    cors_entry = next((mw for mw in app.user_middleware if mw.cls is CORSMiddleware), None)
    assert cors_entry is not None, "CORS middleware should be registered from settings"
    options = cors_entry.kwargs
    assert options["allow_origins"] == ["https://app.example.com"]
    assert options["allow_methods"] == ["GET", "POST"]
    assert options["allow_headers"] == ["Authorization", "X-Request-ID"]
    assert options["expose_headers"] == ["X-Trace"]
    assert options["allow_credentials"] is False
    assert options["max_age"] == 3600
