from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.testclient import TestClient

from spaps_server_quickstart.middleware import RequestLoggingMiddleware


class FakeLogger:
    def __init__(self) -> None:
        self.records: list[tuple[str, dict[str, Any]]] = []

    def info(self, event: str, **kwargs: Any) -> None:
        self.records.append((event, kwargs))


def test_request_logging_middleware_binds_request_id(monkeypatch) -> None:
    fake_logger = FakeLogger()

    import structlog

    monkeypatch.setattr(structlog, "get_logger", lambda *_, **__: fake_logger)

    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware, logger_name="test.request")

    @app.get("/ping")
    async def ping(request: Request) -> JSONResponse:  # pragma: no cover - executed via test client
        user_request_id = request.headers.get("X-Request-ID")
        return JSONResponse({"request_id": user_request_id})

    client = TestClient(app)
    response = client.get("/ping")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert fake_logger.records, "request log should be emitted"
    event, payload = fake_logger.records[0]
    assert event == "request.completed"
    assert payload["method"] == "GET"
    assert payload["status"] == 200
