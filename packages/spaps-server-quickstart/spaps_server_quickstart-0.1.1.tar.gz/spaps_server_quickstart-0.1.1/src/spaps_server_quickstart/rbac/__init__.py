"""
Role-based access control helpers shared across services.
"""

from __future__ import annotations

from typing import Awaitable, Callable, Iterable, Literal, Sequence

from fastapi import HTTPException, Request, status

from ..auth import AuthenticatedUser

RoleMatch = Literal["any", "all"]


def has_required_roles(
    user_roles: Iterable[str],
    required_roles: Sequence[str],
    *,
    match: RoleMatch = "any",
) -> bool:
    """
    Determine whether a user's roles satisfy the requirement.

    Args:
        user_roles: Roles associated with the authenticated subject.
        required_roles: Roles needed to reach the guarded resource.
        match: ``"any"`` requires at least one role, ``"all"`` requires every role.
    """

    if not required_roles:
        return True

    normalized_user_roles = {role.lower() for role in user_roles}
    normalized_required_roles = [role.lower() for role in required_roles]

    if match == "all":
        return all(role in normalized_user_roles for role in normalized_required_roles)
    return any(role in normalized_user_roles for role in normalized_required_roles)


def require_roles(
    roles: Sequence[str],
    *,
    match: RoleMatch = "any",
    forbidden_detail: str = "Forbidden",
) -> Callable[[Request], Awaitable[AuthenticatedUser]]:
    """
    FastAPI dependency that enforces role requirements.

    The dependency expects `SpapsAuthMiddleware` to store an `AuthenticatedUser`
    on `request.state.authenticated_user`. When the user is missing (middleware
    not configured or request unauthenticated) a 401 is returned; when the user
    lacks the required roles a 403 is raised.
    """

    async def _dependency(request: Request) -> AuthenticatedUser:
        user = getattr(request.state, "authenticated_user", None)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

        if not has_required_roles(user.roles, roles, match=match):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=forbidden_detail)

        return user

    return _dependency


__all__ = ["has_required_roles", "require_roles", "RoleMatch"]
