from __future__ import annotations

from starlette.responses import Response

from spaps_server_quickstart.settings import BaseServiceSettings
from spaps_server_quickstart.auth.cookies import clear_refresh_cookie, set_refresh_cookie


def test_set_refresh_cookie_applies_expected_attributes() -> None:
    settings = BaseServiceSettings(
        spaps_refresh_cookie_name="refresh",
        spaps_refresh_cookie_path="/auth",
        spaps_refresh_cookie_domain="htma.test",
        spaps_refresh_cookie_secure=True,
        spaps_refresh_cookie_samesite="strict",
    )

    response = Response()
    set_refresh_cookie(
        response=response,
        settings=settings,
        refresh_token="token-123",
        expires_in=900,
    )

    header = response.headers.get("set-cookie")
    assert header is not None
    assert "refresh=token-123" in header
    assert "Max-Age=900" in header
    assert "Domain=htma.test" in header
    assert "Path=/auth" in header
    assert "Secure" in header
    assert "HttpOnly" in header
    assert "SameSite=strict" in header


def test_clear_refresh_cookie_removes_cookie() -> None:
    settings = BaseServiceSettings(
        spaps_refresh_cookie_name="refresh",
        spaps_refresh_cookie_path="/auth",
        spaps_refresh_cookie_domain="htma.test",
    )
    response = Response()
    response.set_cookie("refresh", "token")

    clear_refresh_cookie(response=response, settings=settings)

    header_values = response.headers.getlist("set-cookie")
    assert header_values, "Expected at least one Set-Cookie header after clearing."
    # Deleting the cookie results in Max-Age=0 per Starlette implementation.
    assert any("Max-Age=0" in header for header in header_values)
