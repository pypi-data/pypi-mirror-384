from __future__ import annotations

import pytest

from spaps_server_quickstart.db.migration_runner import AlembicMigrationRunner


def test_migration_runner_success() -> None:
    runner = AlembicMigrationRunner("test.migrations")
    assert runner.run_upgrade(object(), "head", upgrade_func=lambda config, rev: None) is True


def test_migration_runner_connection_failure() -> None:
    runner = AlembicMigrationRunner("test.migrations")

    def failing_upgrade(config, revision):
        raise ConnectionError("no database")

    assert runner.run_upgrade(object(), "head", upgrade_func=failing_upgrade) is False


def test_migration_runner_resurfaces_other_errors() -> None:
    runner = AlembicMigrationRunner("test.migrations")

    with pytest.raises(ValueError):
        runner.run_upgrade(object(), "head", upgrade_func=lambda config, rev: (_ for _ in ()).throw(ValueError("boom")))


def test_migration_runner_handles_greenlet_error() -> None:
    runner = AlembicMigrationRunner("test.migrations")

    def greenlet_failure(config, revision):
        raise ValueError("greenlet is required")

    assert runner.run_upgrade(object(), "head", upgrade_func=greenlet_failure) is False
