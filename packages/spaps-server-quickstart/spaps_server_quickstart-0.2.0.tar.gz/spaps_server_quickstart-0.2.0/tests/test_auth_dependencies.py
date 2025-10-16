from __future__ import annotations

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from spaps_server_quickstart.auth import AuthenticatedUser
from spaps_server_quickstart.auth.dependencies import (
    require_authenticated_role,
    require_authenticated_user,
)


def build_request(user: AuthenticatedUser | None) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
    }
    request = Request(scope)
    if user is not None:
        request.state.authenticated_user = user
    return request


def test_require_authenticated_user_returns_user() -> None:
    user = AuthenticatedUser(
        user_id="user-1",
        session_id="sess-1",
        application_id="app-abc",
        roles={"admin"},
    )
    request = build_request(user)

    result = require_authenticated_user(request)
    assert result is user


def test_require_authenticated_user_raises_when_missing() -> None:
    request = build_request(None)

    with pytest.raises(HTTPException) as excinfo:
        require_authenticated_user(request)

    assert excinfo.value.status_code == 401
    assert "Authentication required" in excinfo.value.detail


def test_require_authenticated_role_allows_role() -> None:
    user = AuthenticatedUser(
        user_id="user-1",
        session_id="sess-1",
        application_id="app-abc",
        roles={"Practitioner", "Support"},
    )
    request = build_request(user)

    dependency = require_authenticated_role("practitioner")
    assert dependency(request) is user


def test_require_authenticated_role_rejects_missing_role() -> None:
    user = AuthenticatedUser(
        user_id="user-2",
        session_id="sess-1",
        application_id="app-abc",
        roles={"patient"},
    )
    request = build_request(user)

    dependency = require_authenticated_role("admin", detail="Admins only")
    with pytest.raises(HTTPException) as excinfo:
        dependency(request)

    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "Admins only"
