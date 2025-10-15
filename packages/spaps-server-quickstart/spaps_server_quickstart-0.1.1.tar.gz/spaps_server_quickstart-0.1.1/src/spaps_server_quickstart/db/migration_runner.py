"""
Alembic migration runner utilities.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any


def _optional_connection_errors() -> tuple[type[BaseException], ...]:
    errors: list[type[BaseException]] = []
    try:  # pragma: no cover - optional dependency in test environments
        from sqlalchemy.exc import OperationalError
    except ImportError:
        pass
    else:
        errors.append(OperationalError)

    try:  # pragma: no cover - optional dependency in test environments
        from asyncpg import PostgresError
    except ImportError:
        pass
    else:
        errors.append(PostgresError)

    return tuple(errors)


_CONNECTION_ERRORS: tuple[type[BaseException], ...] = (
    ConnectionError,
    ConnectionRefusedError,
    ConnectionResetError,
    OSError,
) + _optional_connection_errors()


class AlembicMigrationRunner:
    """
    Execute Alembic commands while handling transient connection issues gracefully.
    """

    def __init__(self, logger_name: str = "service.migrations") -> None:
        self.logger = logging.getLogger(logger_name)

    def run_upgrade(
        self,
        config: Any,
        revision: str,
        *,
        upgrade_func: Callable[[Any, str], None],
    ) -> bool:
        """
        Run Alembic upgrades and return True on success.

        If the database is unreachable we log and return False so callers can decide
        whether to swallow the failure (e.g., in test environments).
        """

        try:
            upgrade_func(config, revision)
        except _CONNECTION_ERRORS as exc:
            self.logger.warning("alembic.upgrade.connection_failure: %s", exc)
            return False
        except ValueError as exc:
            message = str(exc).lower()
            if "greenlet" in message and "required" in message:
                self.logger.warning("alembic.upgrade.missing_dependency: %s", exc)
                return False
            raise

        return True


def create_migration_runner(logger_name: str) -> AlembicMigrationRunner:
    """
    Convenience helper to build a runner with the given logger namespace.
    """

    return AlembicMigrationRunner(logger_name=logger_name)
