"""Smoke tests ensuring the server quickstart package is importable."""

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")
pytest.importorskip("structlog")
pytest.importorskip("celery")
pytest.importorskip("psycopg")
pytest.importorskip("pgvector")
pytest.importorskip("email_validator")
pytest.importorskip("dotenv")


def test_import_package() -> None:
    import spaps_server_quickstart  # noqa: F401


def test_import_submodules() -> None:
    import spaps_server_quickstart.app_factory  # noqa: F401
    import spaps_server_quickstart.settings  # noqa: F401
    import spaps_server_quickstart.middleware  # noqa: F401
    import spaps_server_quickstart.logging  # noqa: F401
    import spaps_server_quickstart.api.health  # noqa: F401
    import spaps_server_quickstart.api.router  # noqa: F401
    import spaps_server_quickstart.auth  # noqa: F401
    import spaps_server_quickstart.auth.cookies  # noqa: F401
    import spaps_server_quickstart.db.session  # noqa: F401
    import spaps_server_quickstart.db.migration_runner  # noqa: F401
    import spaps_server_quickstart.alembic.naming  # noqa: F401
    import spaps_server_quickstart.tasks.celery_factory  # noqa: F401
    import spaps_server_quickstart.tasks.health  # noqa: F401
    import spaps_server_quickstart.tasks.notifications  # noqa: F401
