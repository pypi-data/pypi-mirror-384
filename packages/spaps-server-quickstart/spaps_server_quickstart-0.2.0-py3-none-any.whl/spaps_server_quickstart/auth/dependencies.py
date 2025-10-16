"""
Dependency helpers for accessing the authenticated user from request state.
"""

from __future__ import annotations

from typing import Callable

from fastapi import HTTPException, status
from starlette.requests import Request

from . import AuthenticatedUser


def require_authenticated_user(request: Request) -> AuthenticatedUser:
    """
    Retrieve the authenticated user stored by `SpapsAuthMiddleware`.
    """

    user = getattr(request.state, "authenticated_user", None)
    if not isinstance(user, AuthenticatedUser):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_authenticated_role(
    role: str,
    *,
    detail: str | None = None,
) -> Callable[[Request], AuthenticatedUser]:
    """
    Build a dependency that ensures the authenticated subject carries the given role.
    """

    required_role = role.lower()
    failure_detail = detail or f"{role.capitalize()} role required"

    def _dependency(request: Request) -> AuthenticatedUser:
        user = require_authenticated_user(request)
        roles = {value.lower() for value in user.roles}
        if required_role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=failure_detail)
        return user

    return _dependency


__all__ = ["require_authenticated_user", "require_authenticated_role"]
