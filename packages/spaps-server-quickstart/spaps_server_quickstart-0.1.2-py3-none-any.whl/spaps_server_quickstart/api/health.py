"""
Shared health endpoint factory.
"""

from __future__ import annotations

import inspect
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.health import HealthResponse
from ..settings import BaseServiceSettings

ExtraMetrics = Mapping[str, Any] | dict[str, Any]
ExtraMetricsProvider = Callable[[BaseServiceSettings, AsyncSession | None], Awaitable[ExtraMetrics] | ExtraMetrics]


class HealthRouterFactory:
    """
    Compose a standard `/health` endpoint with optional database checks.
    """

    def __init__(
        self,
        *,
        settings_loader: Callable[[], BaseServiceSettings],
        session_dependency: Callable[[], AsyncIterator[AsyncSession]] | None = None,
        extra_metrics_provider: ExtraMetricsProvider | None = None,
    ) -> None:
        self._settings_loader = settings_loader
        self._session_dependency = session_dependency
        self._extra_metrics_provider = extra_metrics_provider

    def create_router(self) -> APIRouter:
        router = APIRouter()
        dependency = self._session_dependency
        extra_provider = self._extra_metrics_provider
        settings_loader = self._settings_loader

        if dependency is not None:

            async def health_endpoint(
                session: AsyncSession = Depends(dependency),
            ) -> HealthResponse:
                return await self._build_response(settings_loader(), session, extra_provider)

            router.add_api_route(
                "/health",
                health_endpoint,
                response_model=HealthResponse,
                tags=["health"],
            )
        else:

            async def health_endpoint_no_db() -> HealthResponse:
                return await self._build_response(settings_loader(), None, extra_provider)

            router.add_api_route(
                "/health",
                health_endpoint_no_db,
                response_model=HealthResponse,
                tags=["health"],
            )

        return router

    async def _build_response(
        self,
        settings: BaseServiceSettings,
        session: AsyncSession | None,
        extra_provider: ExtraMetricsProvider | None,
    ) -> HealthResponse:
        database_ready = True
        if session is not None:
            try:
                await session.execute(text("SELECT 1"))
            except SQLAlchemyError:
                database_ready = False

        details: dict[str, Any] = {}
        if extra_provider is not None:
            result = extra_provider(settings, session)
            if inspect.isawaitable(result):
                result = await result  # type: ignore[assignment]
            details.update(dict(result))

        return HealthResponse(
            status="ok" if database_ready else "degraded",
            service=settings.resolved_service_slug,
            version=settings.version,
            database_ready=database_ready,
            details=details,
        )
