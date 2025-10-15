from __future__ import annotations

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from starlette.requests import Request

from spaps_server_quickstart.auth import AuthenticatedUser
from spaps_server_quickstart.rbac import has_required_roles, require_roles


def _make_user(*roles: str) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id="user-1",
        session_id="session-1",
        application_id="app",
        roles=set(roles),
        subscription_active=True,
    )


@pytest.mark.parametrize(
    ("user_roles", "required", "match", "expected"),
    [
        ({"admin", "staff"}, ["admin"], "any", True),
        ({"admin", "staff"}, ["ADMIN"], "any", True),
        ({"staff"}, ["admin"], "any", False),
        ({"staff", "analyst"}, ["staff", "analyst"], "all", True),
        ({"staff"}, ["staff", "analyst"], "all", False),
        (set(), [], "any", True),
    ],
)
def test_has_required_roles(user_roles, required, match, expected) -> None:
    assert has_required_roles(user_roles, required, match=match) is expected


@pytest.mark.asyncio
async def test_require_roles_returns_user_on_success() -> None:
    dependency = require_roles(["admin"])
    scope = {"type": "http", "state": {}}
    request = Request(scope)
    user = _make_user("admin")
    request.state.authenticated_user = user

    resolved = await dependency(request)
    assert resolved is user


@pytest.mark.asyncio
async def test_require_roles_raises_forbidden_when_missing_role() -> None:
    dependency = require_roles(["admin"])
    scope = {"type": "http", "state": {}}
    request = Request(scope)
    request.state.authenticated_user = _make_user("staff")

    with pytest.raises(Exception) as exc:
        await dependency(request)
    assert getattr(exc.value, "status_code", None) == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_require_roles_raises_unauthorized_when_missing_user() -> None:
    dependency = require_roles(["admin"])
    scope = {"type": "http", "state": {}}
    request = Request(scope)

    with pytest.raises(Exception) as exc:
        await dependency(request)
    assert getattr(exc.value, "status_code", None) == status.HTTP_401_UNAUTHORIZED


def test_require_roles_in_fastapi_route() -> None:
    from fastapi import Depends, FastAPI

    app = FastAPI()

    @app.get("/admin")
    async def admin_endpoint(user: AuthenticatedUser = Depends(require_roles(["admin"]))):
        return {"user_id": user.user_id}

    # Manually inject authenticated user via middleware stub.
    @app.middleware("http")
    async def inject_user(request, call_next):  # type: ignore[override]
        request.state.authenticated_user = _make_user("admin")
        return await call_next(request)

    client = TestClient(app)

    response = client.get("/admin")
    assert response.status_code == 200
    assert response.json() == {"user_id": "user-1"}
