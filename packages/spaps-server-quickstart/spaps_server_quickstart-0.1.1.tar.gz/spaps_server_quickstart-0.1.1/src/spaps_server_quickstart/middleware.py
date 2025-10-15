"""
Middleware utilities shared across Sweet Potato services.
"""

from __future__ import annotations

import time
from contextvars import ContextVar
from uuid import uuid4

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

REQUEST_ID_HEADER = "X-Request-ID"
request_id_ctx_var: ContextVar[str | None] = ContextVar("request_id", default=None)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Emit structured logs for each request/response cycle."""

    def __init__(self, app: ASGIApp, logger_name: str = "service.request") -> None:
        super().__init__(app)
        self.logger = structlog.get_logger(logger_name)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response: Response | None = None
        request_id = request.headers.get(REQUEST_ID_HEADER, str(uuid4()))
        token = request_id_ctx_var.set(request_id)
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response = await call_next(request)
            if response is not None:
                response.headers.setdefault(REQUEST_ID_HEADER, request_id)
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            self.logger.info(
                "request.completed",
                method=request.method,
                path=request.url.path,
                status=response.status_code if response else None,
                duration_ms=round(duration_ms, 2),
                request_id=request_id,
            )
            structlog.contextvars.clear_contextvars()
            request_id_ctx_var.reset(token)
