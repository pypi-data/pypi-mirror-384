"""
Helpers for interacting with the SPAPS secure messaging service.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Iterable, Protocol

import structlog

from .auth import AuthenticatedUser
from .settings import BaseServiceSettings

logger = structlog.get_logger("spaps.secure_messaging")


class SecureMessagesClientProtocol(Protocol):
    async def send_message(
        self,
        *,
        context: SecureMessagingContext,
        payload: dict[str, Any],
        timeout: float,
    ) -> dict[str, Any]:
        ...

    async def list_messages(
        self,
        *,
        context: SecureMessagingContext,
        filters: dict[str, Any],
        timeout: float,
    ) -> list[dict[str, Any]]:
        ...


@dataclass(slots=True)
class SecureMessagingContext:
    practitioner_id: str
    patient_id: str
    access_token: str | None = None


class SecureMessagingGatewayError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        error_code: str,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.request_id = request_id

    def __str__(self) -> str:  # pragma: no cover - inherited behaviour validates
        return self.message


class SecureMessagingGateway:
    def __init__(
        self,
        *,
        client: SecureMessagesClientProtocol,
        default_timeout: float,
        default_page_size: int = 25,
    ) -> None:
        self._client = client
        self._default_timeout = default_timeout
        self._default_page_size = default_page_size
        self._logger = logger

    async def send_message(
        self,
        *,
        context: SecureMessagingContext,
        payload: dict[str, Any],
        timeout: float | None = None,
    ) -> dict[str, Any]:
        sanitized_content = payload.get("content") or payload.get("answer_preview") or ""
        self._logger.info(
            "secure_messaging.send",
            practitioner_id=context.practitioner_id,
            patient_id=context.patient_id,
            message_length=len(sanitized_content),
        )
        effective_timeout = timeout or self._default_timeout

        try:
            return await self._client.send_message(
                context=context,
                payload=payload,
                timeout=effective_timeout,
            )
        except Exception as exc:  # pragma: no cover - translated by gateway
            raise self._translate_error(exc) from exc

    async def list_messages(
        self,
        *,
        context: SecureMessagingContext,
        filters: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> list[dict[str, Any]]:
        effective_filters: dict[str, Any] = {
            "practitioner_id": context.practitioner_id,
            "patient_id": context.patient_id,
            "limit": self._default_page_size,
        }
        if filters:
            effective_filters.update(filters)
            effective_filters.setdefault("limit", self._default_page_size)

        effective_timeout = timeout or self._default_timeout

        try:
            return await self._client.list_messages(
                context=context,
                filters=effective_filters,
                timeout=effective_timeout,
            )
        except Exception as exc:  # pragma: no cover - translated by gateway
            raise self._translate_error(exc) from exc

    @staticmethod
    def _translate_error(exc: Exception) -> SecureMessagingGatewayError:
        status_code = getattr(exc, "status_code", None) or 500
        request_id = getattr(exc, "request_id", None)
        upstream_message = str(exc)

        if status_code >= 500:
            return SecureMessagingGatewayError(
                upstream_message or "Secure messaging upstream error",
                status_code=502,
                error_code="SECURE_MESSAGES_UPSTREAM_ERROR",
                request_id=request_id,
            )

        error_code = getattr(exc, "error_code", "SECURE_MESSAGES_ERROR")
        return SecureMessagingGatewayError(
            upstream_message or "Secure messaging error",
            status_code=status_code,
            error_code=str(error_code).upper(),
            request_id=request_id,
        )


SecureMessagesClient: type[Any] | None
SecureMessagesError: type[Exception]


class GatewayFactory(Protocol):
    def __call__(
        self,
        *,
        settings: BaseServiceSettings,
        user: AuthenticatedUser,
    ) -> SecureMessagingGateway:
        ...


try:  # pragma: no cover - executed when dependency available
    from spaps_client import SecureMessagesClient as _SecureMessagesClient
    from spaps_client.secure_messages import SecureMessagesError as _SecureMessagesError
except Exception:  # pragma: no cover - fallback for local development
    SecureMessagesClient = None
    SecureMessagesError = Exception
else:  # pragma: no cover - executed when dependency imported
    SecureMessagesClient = _SecureMessagesClient
    SecureMessagesError = _SecureMessagesError


def provide_secure_messaging_gateway(
    *,
    settings: BaseServiceSettings,
    user: AuthenticatedUser,
    required_roles: Iterable[str] | None = ("practitioner",),
    gateway_factory: GatewayFactory | None = None,
) -> SecureMessagingGateway:
    if not settings.secure_messages_enabled:
        raise RuntimeError("Secure messaging is disabled for this service")

    if required_roles:
        normalized_required = {role.lower() for role in required_roles}
        user_roles = {role.lower() for role in user.roles}
        if not normalized_required.intersection(user_roles):
            raise RuntimeError("Required role missing for secure messaging access")

    factory = gateway_factory or build_secure_messaging_gateway
    return factory(settings=settings, user=user)


def build_secure_messaging_gateway(
    *,
    settings: BaseServiceSettings,
    user: AuthenticatedUser,
    metadata_overrides: dict[str, Any] | None = None,
) -> SecureMessagingGateway:
    if SecureMessagesClient is None:
        raise RuntimeError("SecureMessagesClient dependency is not available")

    if not settings.spaps_api_key or not settings.spaps_application_id:
        raise RuntimeError("SPAPS secure messaging requires API credentials to be configured")

    timeout = settings.secure_messages_timeout or settings.spaps_request_timeout

    client = SecureMessagesClient(
        base_url=settings.spaps_api_url,
        api_key=settings.spaps_api_key,
        request_timeout=timeout,
    )

    adapter: SecureMessagesClientProtocol = _AsyncSecureMessagesClientAdapter(
        client=client,
        default_metadata={
            "application_id": settings.spaps_application_id,
            "practitioner_user_id": user.user_id,
            **(metadata_overrides or {}),
        },
    )

    return SecureMessagingGateway(
        client=adapter,
        default_timeout=timeout,
        default_page_size=settings.secure_messages_default_page_size,
    )


class _AsyncSecureMessagesClientAdapter(SecureMessagesClientProtocol):
    def __init__(
        self,
        *,
        client: Any,
        default_metadata: dict[str, Any] | None = None,
    ) -> None:
        self._client = client
        self._default_metadata = default_metadata or {}

    async def send_message(
        self,
        *,
        context: SecureMessagingContext,
        payload: dict[str, Any],
        timeout: float,
    ) -> dict[str, Any]:
        message_payload = payload.copy()
        practitioner_id = message_payload.pop("practitioner_id", context.practitioner_id)
        patient_id = message_payload.pop("patient_id", context.patient_id)
        content = message_payload.pop("content", None) or message_payload.pop("answer_preview", "")
        metadata = message_payload.pop("metadata", None)

        if metadata is None and message_payload:
            metadata = message_payload

        try:
            message = await asyncio.to_thread(
                self._client.create_message,
                practitioner_id=practitioner_id,
                patient_id=patient_id,
                content=str(content),
                metadata=self._merge_metadata(metadata),
                access_token_override=context.access_token,
            )
        except SecureMessagesError:  # pragma: no cover - translated by gateway
            raise

        return _coerce_to_dict(message)

    async def list_messages(
        self,
        *,
        context: SecureMessagingContext,
        filters: dict[str, Any],
        timeout: float,
    ) -> list[dict[str, Any]]:
        try:
            messages = await asyncio.to_thread(
                self._client.list_messages,
                access_token_override=context.access_token,
            )
        except SecureMessagesError:  # pragma: no cover - translated by gateway
            raise

        return [_coerce_to_dict(message) for message in messages]

    def _merge_metadata(self, metadata: dict[str, Any] | None) -> dict[str, Any] | None:
        if metadata is None:
            return self._default_metadata or None
        if not self._default_metadata:
            return metadata
        merged = {**self._default_metadata}
        merged.update(metadata)
        return merged


def _coerce_to_dict(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    if hasattr(payload, "model_dump"):
        return dict(payload.model_dump())  # type: ignore[arg-type]
    if hasattr(payload, "__dict__"):
        return dict(vars(payload))
    raise TypeError("Secure messaging payload must be convertible to dict")


__all__ = [
    "SecureMessagesClientProtocol",
    "SecureMessagingContext",
    "SecureMessagingGateway",
    "SecureMessagingGatewayError",
    "build_secure_messaging_gateway",
    "provide_secure_messaging_gateway",
]
