from __future__ import annotations

import importlib
from datetime import datetime
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from spaps_server_quickstart.auth import (
    AuthenticationError,
    SpapsAuthMiddleware,
    SpapsAuthService,
    build_spaps_auth_service,
)
from spaps_server_quickstart.settings import BaseServiceSettings


class AuthSettings(BaseServiceSettings):
    spaps_api_key: str | None = "api-key"
    spaps_application_id: str | None = "app-id"


def test_build_spaps_auth_service_requires_keys() -> None:
    settings = BaseServiceSettings()
    with pytest.raises(ValueError):
        build_spaps_auth_service(settings)

    auth_settings = AuthSettings()
    service = build_spaps_auth_service(auth_settings)
    assert service  # instantiated without hitting network


class DummyAuthService:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def authenticate(self, token: str) -> dict[str, str]:
        if token == "denied":
            raise AuthenticationError("Authentication failed", status_code=401)
        if token == "service-down":
            raise AuthenticationError("Authentication service unavailable", status_code=503)
        self.calls.append(token)
        return {"user_id": "user"}

    async def aclose(self) -> None:  # pragma: no cover - not invoked in test
        return None


def test_spaps_auth_middleware_enforces_headers() -> None:
    app = FastAPI()
    auth_service = DummyAuthService()

    app.add_middleware(SpapsAuthMiddleware, auth_service=auth_service, exempt_paths={"/open"})

    @app.get("/open")
    async def open_endpoint() -> dict[str, str]:  # pragma: no cover - executed via client
        return {"status": "ok"}

    @app.get("/secure")
    async def secure_endpoint(request: Request) -> dict[str, Any]:  # pragma: no cover - executed via client
        return {"user": getattr(request.state, "authenticated_user", None)}

    client = TestClient(app)

    assert client.get("/open").status_code == 200
    assert client.get("/secure").status_code == 401
    assert client.get("/secure", headers={"Authorization": "Basic foo"}).status_code == 401

    response = client.get("/secure", headers={"Authorization": "Bearer token"})
    assert response.status_code == 200
    assert auth_service.calls == ["token"]

    denied = client.get("/secure", headers={"Authorization": "Bearer denied"})
    assert denied.status_code == 401
    assert denied.json()["detail"] == "Authentication failed"

    service_down = client.get("/secure", headers={"Authorization": "Bearer service-down"})
    assert service_down.status_code == 503
    assert service_down.json()["detail"] == "Authentication service unavailable"


def test_import_spaps_client_falls_back_to_monorepo(monkeypatch) -> None:
    import spaps_server_quickstart.auth as auth

    real_import = importlib.import_module
    state = {"raised": False, "calls": []}

    def fake_import(name: str, package: str | None = None):
        state["calls"].append(name)
        if name == "spaps_client" and not state["raised"]:
            state["raised"] = True
            raise ImportError("missing dependency")
        return real_import(name, package)

    monkeypatch.setattr(auth.importlib, "import_module", fake_import)

    client_cls, error_cls = auth._import_spaps_client()

    assert state["raised"] is True
    assert state["calls"].count("spaps_client") >= 2
    assert client_cls is auth.AsyncSessionsClient
    assert error_cls is auth.SessionError


@pytest.mark.asyncio()
async def test_spaps_auth_service_authenticate_assigns_roles(monkeypatch) -> None:
    import spaps_server_quickstart.auth as auth

    class StubAsyncSessionsClient:
        def __init__(self, *, access_token: str, **_: Any) -> None:
            self._token = access_token
            self._session_id = "session-1"

        async def validate_session(self) -> SimpleNamespace:
            return SimpleNamespace(valid=True, session_id=self._session_id, renewed=False)

        async def get_current_session(self) -> SimpleNamespace:
            tier = "Practitioner Premium" if self._token != "no-tier" else None
            return SimpleNamespace(
                user_id="user-1",
                session_id="session-1",
                application_id="app-id",
                tier=tier,
                expires_at=datetime(2025, 1, 1),
            )

    monkeypatch.setattr(auth, "AsyncSessionsClient", StubAsyncSessionsClient)

    service = SpapsAuthService(
        base_url="https://api",
        api_key="key",
        application_id="app-id",
        role_hints=("practitioner", "patient"),
    )

    user = await service.authenticate("token")
    assert user.user_id == "user-1"
    assert user.roles == {"practitioner"}
    assert user.subscription_active is True

    user_without_tier = await service.authenticate("no-tier")
    assert user_without_tier.roles == {"patient"}
    assert user_without_tier.subscription_active is False

    await service.aclose()
    assert service._client.is_closed  # type: ignore[attr-defined]


@pytest.mark.asyncio()
async def test_spaps_auth_service_rejects_application_mismatch(monkeypatch) -> None:
    import spaps_server_quickstart.auth as auth

    class MismatchClient:
        def __init__(self, *, access_token: str, **_: Any) -> None:
            self._token = access_token

        async def validate_session(self) -> SimpleNamespace:
            return SimpleNamespace(valid=True, session_id="session-2", renewed=False)

        async def get_current_session(self) -> SimpleNamespace:
            return SimpleNamespace(
                user_id="user-2",
                session_id="session-2",
                application_id="other-app",
                tier=None,
                expires_at=datetime(2025, 1, 1),
            )

    monkeypatch.setattr(auth, "AsyncSessionsClient", MismatchClient)

    service = SpapsAuthService(
        base_url="https://api",
        api_key="key",
        application_id="app-id",
    )

    with pytest.raises(AuthenticationError):
        await service.authenticate("token")


@pytest.mark.asyncio()
async def test_spaps_auth_service_wraps_session_error(monkeypatch) -> None:
    import spaps_server_quickstart.auth as auth

    class ErrorClient:
        def __init__(self, **_: Any) -> None:
            pass

        async def validate_session(self) -> SimpleNamespace:
            return SimpleNamespace(valid=True, session_id="session-1", renewed=False)

        async def get_current_session(self) -> None:
            raise auth.SessionError(
                "remote failure",
                status_code=401,
                error_code="denied",
                request_id="req-123",
            )

    monkeypatch.setattr(auth, "AsyncSessionsClient", ErrorClient)

    service = SpapsAuthService(
        base_url="https://api",
        api_key="key",
        application_id="app-id",
    )

    with pytest.raises(AuthenticationError) as exc:
        await service.authenticate("token")

    error = exc.value
    assert "remote failure" in str(error)
    assert error.status_code == 401
    assert error.error_code == "denied"


@pytest.mark.asyncio()
async def test_spaps_auth_service_handles_validate_session_errors(monkeypatch) -> None:
    import spaps_server_quickstart.auth as auth

    class ErrorClient:
        def __init__(self, **_: Any) -> None:
            pass

        async def validate_session(self) -> None:
            raise auth.SessionError(
                "upstream exploded",
                status_code=502,
                error_code="GATEWAY_TIMEOUT",
                request_id="req-502",
            )

    monkeypatch.setattr(auth, "AsyncSessionsClient", ErrorClient)

    service = SpapsAuthService(
        base_url="https://api",
        api_key="key",
        application_id="app-id",
    )

    with pytest.raises(AuthenticationError) as exc:
        await service.authenticate("token")

    error = exc.value
    assert str(error) == "Authentication service unavailable"
    assert error.status_code == 503
    assert error.error_code == "GATEWAY_TIMEOUT"


@pytest.mark.asyncio()
async def test_spaps_auth_service_rejects_invalid_session(monkeypatch) -> None:
    import spaps_server_quickstart.auth as auth

    class InvalidSessionClient:
        def __init__(self, *, access_token: str, **_: Any) -> None:
            self._token = access_token

        async def validate_session(self) -> SimpleNamespace:
            return SimpleNamespace(valid=False, session_id="sess-invalid", renewed=False)

        async def get_current_session(self) -> None:  # pragma: no cover - should not be reached
            raise AssertionError("get_current_session should not run when session invalid")

    monkeypatch.setattr(auth, "AsyncSessionsClient", InvalidSessionClient)

    service = SpapsAuthService(
        base_url="https://api",
        api_key="key",
        application_id="app-id",
    )

    with pytest.raises(AuthenticationError) as exc:
        await service.authenticate("token")

    error = exc.value
    assert str(error) == "Authentication required"
    assert error.status_code == 401
    assert error.error_code == "SESSION_INVALID"


@pytest.mark.asyncio()
async def test_spaps_auth_service_detects_renewed_session(monkeypatch) -> None:
    import spaps_server_quickstart.auth as auth

    class RenewedSessionClient:
        def __init__(self, *, access_token: str, **_: Any) -> None:
            self._token = access_token

        async def validate_session(self) -> SimpleNamespace:
            return SimpleNamespace(valid=False, session_id="sess-renew", renewed=True)

        async def get_current_session(self) -> None:  # pragma: no cover - should not be reached
            raise AssertionError("get_current_session should not run when session renewed")

    monkeypatch.setattr(auth, "AsyncSessionsClient", RenewedSessionClient)

    service = SpapsAuthService(
        base_url="https://api",
        api_key="key",
        application_id="app-id",
    )

    with pytest.raises(AuthenticationError) as exc:
        await service.authenticate("token")

    error = exc.value
    assert str(error) == "Authentication required"
    assert error.status_code == 401
    assert error.error_code == "SESSION_INVALID"


@pytest.mark.asyncio()
async def test_spaps_auth_service_maps_session_fetch_503(monkeypatch) -> None:
    import spaps_server_quickstart.auth as auth

    class FetchErrorClient:
        def __init__(self, *, access_token: str, **_: Any) -> None:
            self._token = access_token

        async def validate_session(self) -> SimpleNamespace:
            return SimpleNamespace(valid=True, session_id="sess-123", renewed=False)

        async def get_current_session(self) -> None:
            raise auth.SessionError(
                "backend down",
                status_code=500,
                error_code="SERVER_ERROR",
                request_id="req-500",
            )

    monkeypatch.setattr(auth, "AsyncSessionsClient", FetchErrorClient)

    service = SpapsAuthService(
        base_url="https://api",
        api_key="key",
        application_id="app-id",
    )

    with pytest.raises(AuthenticationError) as exc:
        await service.authenticate("token")

    error = exc.value
    assert str(error) == "Authentication service unavailable"
    assert error.status_code == 503
    assert error.error_code == "SERVER_ERROR"
