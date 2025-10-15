from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from typing import Any

import httpx
import pytest

from spaps_server_quickstart.auth_channels import (
    AuthChannelError,
    AuthError,
    SpapsAuthChannelService,
    build_spaps_auth_channel_service,
)
from spaps_server_quickstart.settings import BaseServiceSettings


class ChannelSettings(BaseServiceSettings):
    spaps_api_key: str | None = "api-key"
    spaps_application_id: str | None = "app-id"
    spaps_auth_enabled: bool = True


class StubAsyncAuthClient:
    def __init__(self, *, base_url: str, api_key: str, **_: Any) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.closed = False
        self._responses: dict[str, Any] = {}
        self._errors: dict[str, Exception] = {}

    def queue_response(self, method: str, response: Any) -> None:
        self._responses[method] = response

    def queue_error(self, method: str, error: Exception) -> None:
        self._errors[method] = error

    async def send_magic_link(self, *, email: str) -> Any:
        self.calls.append(("send_magic_link", {"email": email}))
        if "send_magic_link" in self._errors:
            raise self._errors["send_magic_link"]
        return self._responses.get(
            "send_magic_link",
            SimpleNamespace(message="sent", email=email, sent_at=datetime(2025, 1, 1)),
        )

    async def verify_magic_link(self, *, token: str, type: str = "magiclink") -> Any:
        self.calls.append(("verify_magic_link", {"token": token, "type": type}))
        if "verify_magic_link" in self._errors:
            raise self._errors["verify_magic_link"]
        return self._responses.get(
            "verify_magic_link",
            SimpleNamespace(
                message="ok",
                tokens=SimpleNamespace(access_token="access", refresh_token="refresh", expires_in=900),
                user=SimpleNamespace(id="user-1", email="user@example.com"),
            ),
        )

    async def request_nonce(self, *, wallet_address: str, chain: str | None = None) -> Any:
        self.calls.append(("request_nonce", {"wallet_address": wallet_address, "chain": chain}))
        if "request_nonce" in self._errors:
            raise self._errors["request_nonce"]
        return self._responses.get(
            "request_nonce",
            SimpleNamespace(
                nonce="Sign this message to authenticate with Sweet Potato: nonce",
                message="Sign this message to authenticate with Sweet Potato: nonce",
                wallet_address=wallet_address,
                expires_at=datetime(2025, 1, 1),
            ),
        )

    async def verify_wallet(
        self,
        *,
        wallet_address: str,
        signature: str,
        message: str,
        chain: str | None = None,
    ) -> Any:
        self.calls.append(
            (
                "verify_wallet",
                {
                    "wallet_address": wallet_address,
                    "signature": signature,
                    "message": message,
                    "chain": chain,
                },
            )
        )
        if "verify_wallet" in self._errors:
            raise self._errors["verify_wallet"]
        return self._responses.get(
            "verify_wallet",
            SimpleNamespace(
                access_token="wallet-access",
                refresh_token="wallet-refresh",
                expires_in=900,
                token_type="Bearer",
                user=SimpleNamespace(id="user-1", wallet_address=wallet_address, chain=chain),
            ),
        )

    async def aclose(self) -> None:
        self.closed = True


@pytest.mark.asyncio()
async def test_send_magic_link_success() -> None:
    client = StubAsyncAuthClient(base_url="https://api.test", api_key="key")
    service = SpapsAuthChannelService(
        base_url="https://api.test",
        api_key="key",
        request_timeout=5.0,
        auth_client=client,
    )

    result = await service.send_magic_link(email="user@example.com")

    assert client.calls == [("send_magic_link", {"email": "user@example.com"})]
    assert result.email == "user@example.com"
    assert result.message == "sent"


@pytest.mark.asyncio()
async def test_send_magic_link_wraps_auth_error() -> None:
    client = StubAsyncAuthClient(base_url="https://api.test", api_key="key")
    client.queue_error(
        "send_magic_link",
        AuthError("Invalid email", status_code=422, error_code="INVALID_EMAIL"),
    )
    service = SpapsAuthChannelService(
        base_url="https://api.test",
        api_key="key",
        request_timeout=5.0,
        auth_client=client,
    )

    with pytest.raises(AuthChannelError) as excinfo:
        await service.send_magic_link(email="bad")

    error = excinfo.value
    assert error.status_code == 422
    assert error.error_code == "INVALID_EMAIL"
    assert "Invalid email" in str(error)


@pytest.mark.asyncio()
async def test_send_magic_link_wraps_http_error() -> None:
    client = StubAsyncAuthClient(base_url="https://api.test", api_key="key")
    client.queue_error("send_magic_link", httpx.HTTPError("boom"))
    service = SpapsAuthChannelService(
        base_url="https://api.test",
        api_key="key",
        request_timeout=5.0,
        auth_client=client,
    )

    with pytest.raises(AuthChannelError) as excinfo:
        await service.send_magic_link(email="user@example.com")

    assert excinfo.value.status_code == 503
    assert "unavailable" in str(excinfo.value)


@pytest.mark.asyncio()
async def test_verify_magic_link_success() -> None:
    response = SimpleNamespace(
        message="success",
        tokens=SimpleNamespace(access_token="access", refresh_token="refresh", expires_in=900),
        user=SimpleNamespace(id="user-1"),
    )
    client = StubAsyncAuthClient(base_url="https://api.test", api_key="key")
    client.queue_response("verify_magic_link", response)

    service = SpapsAuthChannelService(
        base_url="https://api.test",
        api_key="key",
        request_timeout=5.0,
        auth_client=client,
    )

    result = await service.verify_magic_link(token="token", link_type="magiclink")

    assert client.calls[-1] == ("verify_magic_link", {"token": "token", "type": "magiclink"})
    assert result is response
    assert result.tokens.access_token == "access"


@pytest.mark.asyncio()
async def test_request_nonce_success() -> None:
    client = StubAsyncAuthClient(base_url="https://api.test", api_key="key")
    service = SpapsAuthChannelService(
        base_url="https://api.test",
        api_key="key",
        request_timeout=5.0,
        auth_client=client,
    )

    result = await service.request_wallet_nonce(wallet_address="0xabc", chain="ethereum")

    assert client.calls[-1] == ("request_nonce", {"wallet_address": "0xabc", "chain": "ethereum"})
    assert result.wallet_address == "0xabc"
    assert "Sign this message" in result.message


@pytest.mark.asyncio()
async def test_verify_wallet_success() -> None:
    response = SimpleNamespace(
        access_token="access",
        refresh_token="refresh",
        expires_in=900,
        token_type="Bearer",
        user=SimpleNamespace(id="user-1", wallet_address="0xabc", chain="solana"),
    )
    client = StubAsyncAuthClient(base_url="https://api.test", api_key="key")
    client.queue_response("verify_wallet", response)

    service = SpapsAuthChannelService(
        base_url="https://api.test",
        api_key="key",
        request_timeout=5.0,
        auth_client=client,
    )

    result = await service.verify_wallet(
        wallet_address="0xabc",
        signature="signature",
        message="message",
        chain="solana",
    )

    assert client.calls[-1] == (
        "verify_wallet",
        {
            "wallet_address": "0xabc",
            "signature": "signature",
            "message": "message",
            "chain": "solana",
        },
    )
    assert result is response
    assert result.user.wallet_address == "0xabc"


@pytest.mark.asyncio()
async def test_verify_wallet_wraps_auth_error() -> None:
    client = StubAsyncAuthClient(base_url="https://api.test", api_key="key")
    client.queue_error(
        "verify_wallet",
        AuthError("Signature invalid", status_code=401, error_code="SIGNATURE_INVALID"),
    )

    service = SpapsAuthChannelService(
        base_url="https://api.test",
        api_key="key",
        request_timeout=5.0,
        auth_client=client,
    )

    with pytest.raises(AuthChannelError) as excinfo:
        await service.verify_wallet(
            wallet_address="0xabc",
            signature="bad",
            message="message",
            chain="solana",
        )

    error = excinfo.value
    assert error.status_code == 401
    assert error.error_code == "SIGNATURE_INVALID"
    assert "Signature invalid" in str(error)


def test_build_spaps_auth_channel_service_requires_keys() -> None:
    settings = BaseServiceSettings()

    with pytest.raises(ValueError):
        build_spaps_auth_channel_service(settings)

    configured = ChannelSettings()
    service = build_spaps_auth_channel_service(configured, logger_namespace="custom")
    assert isinstance(service, SpapsAuthChannelService)
