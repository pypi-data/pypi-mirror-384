from __future__ import annotations

import pytest
from sqlalchemy.exc import SQLAlchemyError

from spaps_server_quickstart.db.alembic_status import collect_migration_status


@pytest.fixture(autouse=True)
def stub_heads(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "spaps_server_quickstart.db.alembic_status._load_heads",
        lambda: ["a1b2c3d4e5f6"],
    )


@pytest.mark.asyncio
async def test_collect_status_without_session() -> None:
    status = await collect_migration_status(None)

    assert status["head_revision"] == "a1b2c3d4e5f6"
    assert status["database_version"] is None
    assert status["is_current"] is False
    assert status["pending_revisions"] == ["a1b2c3d4e5f6"]


@pytest.mark.asyncio
async def test_collect_status_matches_database_revision() -> None:
    class StubResult:
        def scalar_one_or_none(self):
            return "a1b2c3d4e5f6"

    class StubSession:
        async def execute(self, statement):
            return StubResult()

    status = await collect_migration_status(StubSession())
    assert status["database_version"] == "a1b2c3d4e5f6"
    assert status["is_current"] is True
    assert status["pending_revisions"] == []


@pytest.mark.asyncio
async def test_collect_status_handles_query_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class Boom(SQLAlchemyError):
        pass

    class FailingSession:
        async def execute(self, statement):
            raise Boom("fail")

    warnings: list[str] = []
    monkeypatch.setattr(
        "spaps_server_quickstart.db.alembic_status.logger.warning",
        lambda msg, *args: warnings.append(msg),
    )

    status = await collect_migration_status(FailingSession())
    assert status["database_version"] is None
    assert status["is_current"] is False
    assert "alembic.status.query_failed" in warnings[0]
