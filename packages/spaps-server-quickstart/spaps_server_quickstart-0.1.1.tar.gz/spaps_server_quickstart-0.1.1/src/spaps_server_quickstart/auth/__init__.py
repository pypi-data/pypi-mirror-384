"""
SPAPS authentication helpers shared across services.
"""

from __future__ import annotations

import importlib
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import httpx
import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from ..settings import BaseServiceSettings


def _locate_python_client_src() -> Path | None:
    """
    Walk up the filesystem to find the monorepo python-client source directory.
    """

    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "packages" / "python-client" / "src"
        if candidate.exists():
            return candidate
    return None


def _import_spaps_client() -> tuple[type[Any], type[Exception]]:
    """
    Import the SPAPS client, falling back to the monorepo source tree when running locally.
    """

    try:
        module = importlib.import_module("spaps_client")
    except ImportError:  # pragma: no cover - exercised via fallback test
        fallback = _locate_python_client_src()
        if fallback is None:
            raise
        if str(fallback) not in sys.path:
            sys.path.append(str(fallback))
        module = importlib.import_module("spaps_client")
    return module.AsyncSessionsClient, module.SessionError  # type: ignore[attr-defined]


AsyncSessionsClient, SessionError = _import_spaps_client()


class AuthenticationError(Exception):
    """Raised when a request cannot be authenticated via SPAPS."""

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


@dataclass(slots=True)
class AuthenticatedUser:
    """Represents the authenticated subject and subscription context."""

    user_id: str
    session_id: str
    application_id: str
    roles: set[str] = field(default_factory=set)
    subscription_active: bool = False
    subscription_plan: str | None = None
    tier: str | None = None
    session_expires_at: datetime | None = None


class SpapsAuthService:
    """Facilitates authentication by delegating to the Sweet Potato Sessions API."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        application_id: str,
        request_timeout: float = 10.0,
        http_client: httpx.AsyncClient | None = None,
        role_hints: Sequence[str] | None = None,
        logger_namespace: str = "service.auth",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._application_id = application_id
        self._request_timeout = request_timeout
        if http_client is None:
            self._client = httpx.AsyncClient(base_url=self._base_url, timeout=request_timeout)
            self._owns_client = True
        else:
            self._client = http_client
            self._owns_client = False
        self._role_hints = {hint.lower() for hint in role_hints or ("practitioner", "patient")}
        self._logger = structlog.get_logger(logger_namespace)

    async def authenticate(self, access_token: str) -> AuthenticatedUser:
        if not access_token:
            raise AuthenticationError("Access token missing", status_code=401)

        sessions_client = AsyncSessionsClient(
            base_url=self._base_url,
            api_key=self._api_key,
            access_token=access_token,
            client=self._client,
            request_timeout=self._request_timeout,
        )

        try:
            validation = await sessions_client.validate_session()
        except SessionError as exc:  # pragma: no cover - exercised via middleware tests
            raise self._handle_session_error(
                exc,
                event="spaps.validation_failed",
                default_detail="Authentication failed",
            )
        except httpx.HTTPError as exc:  # pragma: no cover - network failures
            self._logger.error("spaps.http_error", error=str(exc))
            raise AuthenticationError("Authentication service unavailable", status_code=503) from exc

        if not validation.valid:
            self._logger.warning(
                "spaps.session_invalid",
                session_id=validation.session_id,
                renewed=validation.renewed,
            )
            raise AuthenticationError(
                "Authentication required",
                status_code=401,
                error_code="SESSION_INVALID",
            )

        try:
            session = await sessions_client.get_current_session()
        except SessionError as exc:  # pragma: no cover - exercised via middleware tests
            raise self._handle_session_error(
                exc,
                event="spaps.session_lookup_failed",
                default_detail="Authentication failed",
            )
        except httpx.HTTPError as exc:  # pragma: no cover - network failures
            self._logger.error("spaps.http_error", error=str(exc))
            raise AuthenticationError("Authentication service unavailable", status_code=503) from exc

        if session.application_id != self._application_id:
            self._logger.warning(
                "spaps.application_mismatch",
                expected=self._application_id,
                received=session.application_id,
            )
            raise AuthenticationError(
                "Token not issued for this application",
                status_code=401,
                error_code="APPLICATION_MISMATCH",
            )

        roles = self._derive_roles(session.tier)
        subscription_active = bool(session.tier)
        authenticated = AuthenticatedUser(
            user_id=session.user_id,
            session_id=session.session_id,
            application_id=session.application_id,
            roles=roles,
            subscription_active=subscription_active,
            subscription_plan=session.tier,
            tier=session.tier,
            session_expires_at=session.expires_at,
        )
        return authenticated

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    def _derive_roles(self, tier: str | None) -> set[str]:
        if tier:
            tier_lower = tier.lower()
            roles = {hint for hint in self._role_hints if hint in tier_lower}
            if roles:
                return roles
        return {"patient"}

    def _handle_session_error(
        self,
        exc: Exception,
        *,
        event: str,
        default_detail: str,
    ) -> AuthenticationError:
        detail = exc.args[0] if exc.args else default_detail
        status_code_attr = cast(int | None, getattr(exc, "status_code", None))
        error_code = cast(str | None, getattr(exc, "error_code", None))
        request_id = cast(str | None, getattr(exc, "request_id", None))

        status_code = status_code_attr or 401
        if status_code >= 500:
            status_code = 503
            detail = "Authentication service unavailable"

        self._logger.warning(
            event,
            status_code=status_code_attr,
            error_code=error_code,
            request_id=request_id,
        )
        return AuthenticationError(
            detail,
            status_code=status_code,
            error_code=error_code,
        )


class SpapsAuthMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that authenticates requests using SPAPS."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        auth_service: SpapsAuthService,
        exempt_paths: Iterable[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.auth_service = auth_service
        self.exempt_paths = {
            self._normalize_path(path) for path in (exempt_paths or {"/health", "/docs", "/redoc"})
        }

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if self._is_exempt(request):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return self._unauthorized("Authorization header missing")

        scheme, _, token = auth_header.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return self._unauthorized("Invalid authorization scheme")

        try:
            user = await self.auth_service.authenticate(token)
        except AuthenticationError as exc:
            return self._handle_authentication_error(exc)

        request.state.authenticated_user = user
        return await call_next(request)

    def _is_exempt(self, request: Request) -> bool:
        normalized = self._normalize_path(request.url.path)
        return normalized in self.exempt_paths

    @staticmethod
    def _normalize_path(path: str) -> str:
        if not path:
            return "/"
        normalized = path if path.startswith("/") else f"/{path}"
        if len(normalized) > 1 and normalized.endswith("/"):
            normalized = normalized.rstrip("/")
        return normalized

    @staticmethod
    def _unauthorized(message: str) -> JSONResponse:
        return JSONResponse(
            {"detail": message},
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
        )

    def _handle_authentication_error(self, exc: AuthenticationError) -> JSONResponse:
        status_code = getattr(exc, "status_code", None) or 401
        if status_code == 401:
            return self._unauthorized(str(exc))
        return JSONResponse({"detail": str(exc)}, status_code=status_code)


def build_spaps_auth_service(
    settings: BaseServiceSettings,
    *,
    http_client: httpx.AsyncClient | None = None,
    role_hints: Sequence[str] | None = None,
    logger_namespace: str | None = None,
    **extra: Any,
) -> SpapsAuthService:
    """
    Build an auth service instance using the shared settings.
    """

    if not settings.spaps_api_key:
        raise ValueError("SPAPS_API_KEY is not configured")
    if not settings.spaps_application_id:
        raise ValueError("SPAPS_APPLICATION_ID is not configured")
    namespace = logger_namespace or f"{settings.logger_namespace}.auth"
    return SpapsAuthService(
        base_url=settings.spaps_api_url,
        api_key=settings.spaps_api_key,
        application_id=settings.spaps_application_id,
        request_timeout=settings.spaps_request_timeout,
        http_client=http_client,
        role_hints=role_hints,
        logger_namespace=namespace,
        **extra,
    )


__all__ = [
    "AuthenticatedUser",
    "AuthenticationError",
    "SpapsAuthMiddleware",
    "SpapsAuthService",
    "build_spaps_auth_service",
]
