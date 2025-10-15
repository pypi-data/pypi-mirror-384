"""
Async SQLAlchemy session helpers shared across services.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from ..settings import BaseServiceSettings


class DatabaseResources:
    """
    Lazily instantiate the async SQLAlchemy engine/session factory for a service.
    """

    def __init__(
        self,
        settings: BaseServiceSettings,
        *,
        engine_overrides: dict[str, Any] | None = None,
    ) -> None:
        self._settings = settings
        self._engine_overrides = engine_overrides or {}
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    def get_engine(self) -> AsyncEngine:
        if self._engine is None:
            engine_kwargs = self._build_engine_kwargs()
            engine_kwargs.update(self._engine_overrides)
            self._engine = create_async_engine(self._settings.database_url, **engine_kwargs)
        return self._engine

    def get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                self.get_engine(),
                expire_on_commit=False,
            )
        return self._session_factory

    async def dispose(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
        self._engine = None
        self._session_factory = None

    async def session_dependency(self) -> AsyncIterator[AsyncSession]:
        async with self.get_session_factory()() as session:
            yield session

    def _build_engine_kwargs(self) -> dict[str, Any]:
        poolclass = None if self._settings.env == "prod" else NullPool
        kwargs: dict[str, Any] = {
            "echo": self._settings.database_echo,
        }
        if poolclass is None:
            kwargs["pool_size"] = self._settings.database_pool_size
            kwargs["max_overflow"] = self._settings.database_max_overflow
            kwargs["pool_timeout"] = self._settings.database_pool_timeout
        else:
            kwargs["poolclass"] = poolclass
        return kwargs


def create_async_sessionmaker(
    settings: BaseServiceSettings,
    **engine_kwargs: Any,
) -> async_sessionmaker[AsyncSession]:
    """
    Convenience helper mirroring the previous service-level API.
    """

    resources = DatabaseResources(settings, engine_overrides=engine_kwargs)
    return resources.get_session_factory()


def session_dependency_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> Callable[[], AsyncIterator[AsyncSession]]:
    """
    Build a FastAPI dependency that yields an AsyncSession from the given factory.
    """

    async def _dependency() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    return _dependency
