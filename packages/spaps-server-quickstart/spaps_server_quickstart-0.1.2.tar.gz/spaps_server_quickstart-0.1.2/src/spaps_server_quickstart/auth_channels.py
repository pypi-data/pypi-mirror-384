"""
Helpers for interacting with SPAPS magic-link and wallet authentication flows.
"""

from __future__ import annotations

import importlib
import sys
from typing import Any, Protocol, cast

import httpx
import structlog

from .auth import _locate_python_client_src
from .settings import BaseServiceSettings


class AsyncAuthClientProtocol(Protocol):
    async def send_magic_link(self, *, email: str) -> Any: ...

    async def verify_magic_link(self, *, token: str, type: str = "magiclink") -> Any: ...

    async def request_nonce(self, *, wallet_address: str, chain: str | None = None) -> Any: ...

    async def verify_wallet(
        self,
        *,
        wallet_address: str,
        signature: str,
        message: str,
        chain: str | None = None,
    ) -> Any: ...

    async def aclose(self) -> None: ...


def _import_spaps_auth_client() -> tuple[type[Any], type[Exception]]:
    """
    Import the SPAPS async auth client with a monorepo fallback.
    """

    try:
        module = importlib.import_module("spaps_client")
    except ImportError:  # pragma: no cover - exercised via fallback tests elsewhere
        fallback = _locate_python_client_src()
        if fallback is None:
            raise
        if str(fallback) not in sys.path:
            sys.path.append(str(fallback))
        module = importlib.import_module("spaps_client")
    return module.AsyncAuthClient, module.AuthError  # type: ignore[attr-defined]


_AsyncAuthClient, _AuthError = _import_spaps_auth_client()
# Expose for downstream tests/backwards compatibility
AuthError = _AuthError



class AuthChannelError(Exception):
    """
    Raised when magic-link or wallet operations fail.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


class SpapsAuthChannelService:
    """
    Provides magic-link and wallet helpers backed by the SPAPS Auth API.
    """

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        request_timeout: float = 10.0,
        auth_client: AsyncAuthClientProtocol | None = None,
        logger_namespace: str = "service.auth.channels",
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.request_timeout = request_timeout
        self._logger = structlog.get_logger(logger_namespace)
        self._client: AsyncAuthClientProtocol

        if auth_client is None:
            client = _AsyncAuthClient(
                base_url=self.base_url,
                api_key=self.api_key,
                request_timeout=self.request_timeout,
            )
            self._owns_client = True
            self._client = cast(AsyncAuthClientProtocol, client)
        else:
            self._client = auth_client
            self._owns_client = False

    async def send_magic_link(self, *, email: str) -> Any:
        """
        Request a magic link for the supplied email address.
        """

        try:
            return await self._client.send_magic_link(email=email)
        except _AuthError as exc:  # pragma: no cover - handled via unit tests
            raise self._handle_auth_error(
                exc,
                event="spaps.magic_link_send_failed",
                default_detail="Magic link request failed",
            ) from exc
        except httpx.HTTPError as exc:  # pragma: no cover - network failures
            self._logger.error("spaps.http_error", error=str(exc))
            raise AuthChannelError("Authentication service unavailable", status_code=503) from exc

    async def verify_magic_link(self, *, token: str, link_type: str = "magiclink") -> Any:
        """
        Exchange a magic link token for SPAPS session tokens.
        """

        try:
            return await self._client.verify_magic_link(token=token, type=link_type)
        except _AuthError as exc:
            raise self._handle_auth_error(
                exc,
                event="spaps.magic_link_verify_failed",
                default_detail="Magic link verification failed",
            ) from exc
        except httpx.HTTPError as exc:
            self._logger.error("spaps.http_error", error=str(exc))
            raise AuthChannelError("Authentication service unavailable", status_code=503) from exc

    async def request_wallet_nonce(self, *, wallet_address: str, chain: str | None = None) -> Any:
        """
        Request a wallet nonce that the client must sign before verification.
        """

        try:
            return await self._client.request_nonce(wallet_address=wallet_address, chain=chain)
        except _AuthError as exc:
            raise self._handle_auth_error(
                exc,
                event="spaps.wallet_nonce_failed",
                default_detail="Wallet nonce request failed",
            ) from exc
        except httpx.HTTPError as exc:
            self._logger.error("spaps.http_error", error=str(exc))
            raise AuthChannelError("Authentication service unavailable", status_code=503) from exc

    async def verify_wallet(
        self,
        *,
        wallet_address: str,
        signature: str,
        message: str,
        chain: str | None = None,
    ) -> Any:
        """
        Verify a signed wallet nonce and return session tokens.
        """

        try:
            return await self._client.verify_wallet(
                wallet_address=wallet_address,
                signature=signature,
                message=message,
                chain=chain,
            )
        except _AuthError as exc:
            raise self._handle_auth_error(
                exc,
                event="spaps.wallet_sign_in_failed",
                default_detail="Wallet verification failed",
            ) from exc
        except httpx.HTTPError as exc:
            self._logger.error("spaps.http_error", error=str(exc))
            raise AuthChannelError("Authentication service unavailable", status_code=503) from exc

    async def aclose(self) -> None:
        """
        Close the underlying auth client if managed by this service.
        """

        if self._owns_client:
            await self._client.aclose()

    def _handle_auth_error(
        self,
        exc: Exception,
        *,
        event: str,
        default_detail: str,
    ) -> AuthChannelError:
        detail = exc.args[0] if exc.args else default_detail
        status_code_attr = cast(int | None, getattr(exc, "status_code", None))
        error_code = cast(str | None, getattr(exc, "error_code", None))
        request_id = cast(str | None, getattr(exc, "request_id", None))

        status_code = status_code_attr or 400
        if status_code >= 500:
            status_code = 503
            detail = "Authentication service unavailable"

        self._logger.warning(
            event,
            status_code=status_code_attr,
            error_code=error_code,
            request_id=request_id,
        )
        return AuthChannelError(
            detail,
            status_code=status_code,
            error_code=error_code,
        )


def build_spaps_auth_channel_service(
    settings: BaseServiceSettings,
    *,
    auth_client: AsyncAuthClientProtocol | None = None,
    logger_namespace: str | None = None,
    **extra: Any,
) -> SpapsAuthChannelService:
    """
    Factory mirroring :func:`build_spaps_auth_service` for channel helpers.
    """

    if not settings.spaps_api_key:
        raise ValueError("SPAPS_API_KEY is not configured")
    if not settings.spaps_application_id:
        raise ValueError("SPAPS_APPLICATION_ID is not configured")

    return SpapsAuthChannelService(
        base_url=settings.spaps_api_url,
        api_key=settings.spaps_api_key,
        request_timeout=settings.spaps_request_timeout,
        auth_client=auth_client,
        logger_namespace=logger_namespace or f"{settings.logger_namespace}.auth.channels",
        **extra,
    )


__all__ = [
    "AuthChannelError",
    "AuthError",
    "SpapsAuthChannelService",
    "build_spaps_auth_channel_service",
]
