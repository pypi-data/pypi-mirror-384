"""
Utilities for summarising Alembic migration status.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("spaps.migrations")


def _candidate_alembic_paths() -> list[Path]:
    paths: list[Path] = []
    env_path = os.getenv("ALEMBIC_CONFIG")
    if env_path:
        candidate = Path(env_path)
        if candidate.is_file():
            paths.append(candidate)

    cwd_candidate = Path.cwd() / "alembic.ini"
    if cwd_candidate.is_file():
        paths.append(cwd_candidate)

    module_root = Path(__file__).resolve().parents[2]
    search_roots = (module_root, *module_root.parents[:3])
    for root in search_roots:
        ini_candidate = root / "alembic.ini"
        if ini_candidate.is_file():
            paths.append(ini_candidate)

    seen: set[Path] = set()
    unique_paths: list[Path] = []
    for path in paths:
        if path not in seen:
            unique_paths.append(path)
            seen.add(path)
    return unique_paths


@lru_cache(maxsize=1)
def _load_heads() -> list[str]:
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory
    except ImportError:  # pragma: no cover - alembic not installed
        logger.debug("alembic unavailable; cannot determine head revision")
        return []

    for ini_path in _candidate_alembic_paths():
        try:
            config = Config(str(ini_path))
            script = ScriptDirectory.from_config(config)
            heads = list(script.get_heads())
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.debug("alembic.heads.error: path=%s error=%s", ini_path, exc)
            continue
        if heads:
            return sorted(heads)
    logger.debug("alembic.heads.missing_config")
    return []


def _format_head_revision(heads: list[str]) -> str | None:
    if not heads:
        return None
    if len(heads) == 1:
        return heads[0]
    return ", ".join(sorted(heads))


async def collect_migration_status(session: AsyncSession | None) -> dict[str, object]:
    """
    Summarise Alembic state for observability surfaces.
    """

    heads = _load_heads()
    head_revision = _format_head_revision(heads)
    head_set = set(heads)

    database_version: str | None = None
    if session is not None:
        try:
            result = await session.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar_one_or_none()
            if version is not None:
                database_version = str(version)
        except SQLAlchemyError as exc:
            logger.warning("alembic.status.query_failed: %s", exc)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("alembic.status.unexpected_error: %s", exc)

    current_set = {database_version} if database_version is not None else set()
    is_current = bool(head_set) and current_set == head_set
    if not head_set and database_version is not None:
        is_current = True

    pending_revisions = sorted(head_set - current_set) if head_set else []

    return {
        "head_revision": head_revision,
        "database_version": database_version,
        "is_current": is_current,
        "pending_revisions": pending_revisions,
    }


__all__ = ["collect_migration_status"]
