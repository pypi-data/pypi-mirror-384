from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy.pool import NullPool

from spaps_server_quickstart.db.session import DatabaseResources, create_async_sessionmaker, session_dependency_factory
from spaps_server_quickstart.settings import BaseServiceSettings


class DevSettings(BaseServiceSettings):
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/dev"


class ProdSettings(BaseServiceSettings):
    env: str = "prod"
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/prod"


class DummySessionContext:
    async def __aenter__(self) -> str:
        return "session"

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class DummySessionFactory:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> DummySessionContext:
        self.calls += 1
        return DummySessionContext()


def test_database_resources_dev_uses_null_pool(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    def fake_create_async_engine(url: str, **kwargs: Any) -> str:
        captured["url"] = url
        captured["kwargs"] = kwargs
        return "engine"

    def fake_sessionmaker(engine: Any, expire_on_commit: bool) -> DummySessionFactory:
        captured["engine"] = engine
        captured["expire_on_commit"] = expire_on_commit
        return DummySessionFactory()

    from spaps_server_quickstart.db import session as session_module

    monkeypatch.setattr(session_module, "create_async_engine", fake_create_async_engine)
    monkeypatch.setattr(session_module, "async_sessionmaker", fake_sessionmaker)

    resources = DatabaseResources(DevSettings())

    factory = resources.get_session_factory()
    assert captured["url"].endswith("/dev")
    assert captured["kwargs"]["poolclass"] is NullPool

    async def consume_session() -> None:
        async for session in resources.session_dependency():
            assert session == "session"

    asyncio.run(consume_session())
    assert isinstance(factory, DummySessionFactory)


def test_database_resources_prod_uses_pool(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    def fake_create_async_engine(url: str, **kwargs: Any) -> str:
        captured["url"] = url
        captured["kwargs"] = kwargs
        return "engine"

    def fake_sessionmaker(engine: Any, expire_on_commit: bool) -> DummySessionFactory:
        captured["engine"] = engine
        captured["expire_on_commit"] = expire_on_commit
        return DummySessionFactory()

    from spaps_server_quickstart.db import session as session_module

    monkeypatch.setattr(session_module, "create_async_engine", fake_create_async_engine)
    monkeypatch.setattr(session_module, "async_sessionmaker", fake_sessionmaker)

    resources = DatabaseResources(ProdSettings())
    resources.get_session_factory()

    kwargs = captured["kwargs"]
    assert "pool_size" in kwargs and "max_overflow" in kwargs and "pool_timeout" in kwargs
    assert "poolclass" not in kwargs


def test_session_dependency_factory_wraps_session(monkeypatch) -> None:
    dummy_factory = DummySessionFactory()
    dependency = session_dependency_factory(dummy_factory)  # type: ignore[arg-type]

    async def consume_dependency() -> None:
        async for session in dependency():
            assert session == "session"

    asyncio.run(consume_dependency())
    assert dummy_factory.calls == 1


def test_create_async_sessionmaker_delegates(monkeypatch) -> None:
    created = {}

    def fake_init(self, settings, engine_overrides=None):
        created["settings"] = settings
        created["engine_overrides"] = engine_overrides

    monkeypatch.setattr(DatabaseResources, "__init__", fake_init)
    monkeypatch.setattr(
        DatabaseResources,
        "get_session_factory",
        lambda self: "factory",  # type: ignore[no-untyped-def]
    )

    factory = create_async_sessionmaker(DevSettings(), echo=True)
    assert factory == "factory"
    assert created["engine_overrides"] == {"echo": True}


def test_database_resources_dispose_resets_engine(monkeypatch) -> None:
    engines: list[Any] = []

    class DummyEngine:
        def __init__(self) -> None:
            self.disposed = False

        async def dispose(self) -> None:
            self.disposed = True

    def fake_create_async_engine(url: str, **kwargs: Any) -> DummyEngine:
        engine = DummyEngine()
        engines.append(engine)
        return engine

    def fake_sessionmaker(engine: Any, expire_on_commit: bool) -> DummySessionFactory:
        return DummySessionFactory()

    from spaps_server_quickstart.db import session as session_module

    monkeypatch.setattr(session_module, "create_async_engine", fake_create_async_engine)
    monkeypatch.setattr(session_module, "async_sessionmaker", fake_sessionmaker)

    resources = DatabaseResources(DevSettings())
    resources.get_session_factory()

    assert len(engines) == 1

    asyncio.run(resources.dispose())
    assert engines[0].disposed is True

    resources.get_engine()
    assert len(engines) == 2
