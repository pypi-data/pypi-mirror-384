"""
Utility helpers for setting and clearing SPAPS refresh cookies.
"""

from __future__ import annotations

from starlette.responses import Response

from ..settings import BaseServiceSettings


def set_refresh_cookie(
    *,
    response: Response,
    settings: BaseServiceSettings,
    refresh_token: str | None,
    expires_in: int | None,
) -> None:
    """
    Attach the SPAPS refresh token to the HTTP response using shared settings defaults.
    """

    if not refresh_token:
        return

    response.set_cookie(
        key=settings.spaps_refresh_cookie_name,
        value=refresh_token,
        max_age=expires_in,
        httponly=True,
        samesite=settings.spaps_refresh_cookie_samesite,
        secure=settings.spaps_refresh_cookie_secure,
        domain=settings.spaps_refresh_cookie_domain,
        path=settings.spaps_refresh_cookie_path,
    )


def clear_refresh_cookie(*, response: Response, settings: BaseServiceSettings) -> None:
    """
    Remove the SPAPS refresh token cookie using the shared settings defaults.
    """

    response.delete_cookie(
        key=settings.spaps_refresh_cookie_name,
        domain=settings.spaps_refresh_cookie_domain,
        path=settings.spaps_refresh_cookie_path,
    )


__all__ = ["set_refresh_cookie", "clear_refresh_cookie"]
