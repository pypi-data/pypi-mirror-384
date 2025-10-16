from __future__ import annotations

import asyncio

import pytest

from spaps_server_quickstart.auth import AuthenticatedUser
from spaps_server_quickstart.secure_messaging import (
    SecureMessagingContext,
    SecureMessagingGateway,
    SecureMessagingGatewayError,
    build_secure_messaging_gateway,
    provide_secure_messaging_gateway,
)
from spaps_server_quickstart.settings import BaseServiceSettings


class StubSecureMessagesError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = "UPSTREAM"
        self.request_id = "req-123"


class StubSecureMessagesClient:
    def __init__(self, *, response: dict | None = None) -> None:
        self.response = response or {"id": "msg-1"}
        self.calls: list[tuple[str, SecureMessagingContext, dict, float]] = []
        self.raise_on_send: Exception | None = None
        self.raise_on_list: Exception | None = None

    async def send_message(
        self,
        *,
        context: SecureMessagingContext,
        payload: dict,
        timeout: float,
    ) -> dict:
        await asyncio.sleep(0)
        if self.raise_on_send is not None:
            raise self.raise_on_send
        self.calls.append(("send", context, payload, timeout))
        return self.response

    async def list_messages(
        self,
        *,
        context: SecureMessagingContext,
        filters: dict,
        timeout: float,
    ) -> list[dict]:
        await asyncio.sleep(0)
        if self.raise_on_list is not None:
            raise self.raise_on_list
        self.calls.append(("list", context, filters, timeout))
        return [self.response]


class StubSettings(BaseServiceSettings):
    secure_messages_enabled: bool = True
    spaps_api_key: str = "api-key"
    spaps_application_id: str = "app-123"
    spaps_request_timeout: float = 5.5
    secure_messages_timeout: float | None = None
    secure_messages_default_page_size: int = 31


@pytest.fixture(name="settings")
def fixture_settings() -> StubSettings:
    return StubSettings()


@pytest.fixture(name="user")
def fixture_user() -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id="user-1",
        session_id="sess-1",
        application_id="app-123",
        roles={"practitioner"},
    )


@pytest.mark.asyncio
async def test_gateway_send_and_list() -> None:
    client = StubSecureMessagesClient()
    gateway = SecureMessagingGateway(
        client=client,
        default_timeout=7.5,
        default_page_size=42,
    )

    context = SecureMessagingContext(
        practitioner_id="prac-1",
        patient_id="pat-1",
        access_token="token-1",
    )

    payload = {"content": "very secret note"}
    result = await gateway.send_message(context=context, payload=payload)
    assert result == client.response
    assert client.calls == [("send", context, payload, 7.5)]

    listed = await gateway.list_messages(context=context, filters={"cursor": "abc"})
    assert listed == [client.response]
    assert client.calls[-1] == (
        "list",
        context,
        {"practitioner_id": "prac-1", "patient_id": "pat-1", "cursor": "abc", "limit": 42},
        7.5,
    )


@pytest.mark.asyncio
async def test_gateway_translates_errors() -> None:
    client = StubSecureMessagesClient()
    client.raise_on_send = StubSecureMessagesError("upstream exploded", status_code=500)
    gateway = SecureMessagingGateway(
        client=client,
        default_timeout=3.0,
        default_page_size=25,
    )

    context = SecureMessagingContext(practitioner_id="prac-1", patient_id="pat-1")

    with pytest.raises(SecureMessagingGatewayError) as excinfo:
        await gateway.send_message(context=context, payload={"content": "boom"})

    error = excinfo.value
    assert error.status_code == 502
    assert error.error_code == "SECURE_MESSAGES_UPSTREAM_ERROR"


def test_provide_gateway_requires_feature_flag(settings: StubSettings, user: AuthenticatedUser) -> None:
    settings.secure_messages_enabled = False

    with pytest.raises(RuntimeError) as excinfo:
        provide_secure_messaging_gateway(settings=settings, user=user)

    assert "disabled" in str(excinfo.value).lower()


def test_provide_gateway_requires_role(settings: StubSettings, user: AuthenticatedUser) -> None:
    settings.secure_messages_enabled = True
    user.roles.clear()

    with pytest.raises(RuntimeError) as excinfo:
        provide_secure_messaging_gateway(settings=settings, user=user)

    assert "role" in str(excinfo.value).lower()


@pytest.mark.asyncio
async def test_build_gateway_uses_settings(monkeypatch, settings: StubSettings, user: AuthenticatedUser) -> None:
    constructed: dict[str, object] = {}

    class FakeSyncClient:
        def __init__(self, *, base_url: str, api_key: str, request_timeout: float) -> None:
            constructed["kwargs"] = {
                "base_url": base_url,
                "api_key": api_key,
                "request_timeout": request_timeout,
            }

        def create_message(self, **kwargs: object) -> object:
            constructed["create"] = kwargs
            return type("Message", (), {"model_dump": lambda self: {"id": "created"}})()

        def list_messages(self, **kwargs: object) -> list[object]:
            constructed["list"] = kwargs
            return [
                type("Message", (), {"model_dump": lambda self: {"id": "listed"}})(),
            ]

    monkeypatch.setattr(
        "spaps_server_quickstart.secure_messaging.SecureMessagesClient",
        FakeSyncClient,
    )
    monkeypatch.setattr(
        "spaps_server_quickstart.secure_messaging.SecureMessagesError",
        StubSecureMessagesError,
    )

    gateway = build_secure_messaging_gateway(settings=settings, user=user)

    context = SecureMessagingContext(
        practitioner_id="prac-9",
        patient_id="pat-7",
        access_token="token-abc",
    )

    result = await gateway.send_message(
        context=context,
        payload={"answer_preview": "classified", "severity": "high"},
    )
    assert result == {"id": "created"}
    assert constructed["create"] == {
        "practitioner_id": "prac-9",
        "patient_id": "pat-7",
        "content": "classified",
        "metadata": {
            "application_id": "app-123",
            "practitioner_user_id": "user-1",
            "severity": "high",
        },
        "access_token_override": "token-abc",
    }

    listed = await gateway.list_messages(context=context, filters=None)
    assert listed == [{"id": "listed"}]
    assert constructed["list"] == {"access_token_override": "token-abc"}
