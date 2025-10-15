from __future__ import annotations

import pytest

from spaps_server_quickstart.settings import (
    BaseServiceSettings,
    create_settings_loader,
)


class ExampleSettings(BaseServiceSettings):
    app_name: str = "Example Service"
    service_slug: str = "example-service"
    database_url: str = "postgresql+asyncpg://user:pass@host:5432/example"
    redis_url: str = "redis://localhost:6379/1"


class NoSlugSettings(BaseServiceSettings):
    app_name: str = "Slugless Service"
    database_url: str = "postgresql+asyncpg://user:pass@host:5432/slugless"


def test_settings_loader_caches_instances() -> None:
    loader = create_settings_loader(ExampleSettings)
    first = loader()
    second = loader()

    assert first is second
    assert first.resolved_service_slug == "example-service"
    assert first.logger_namespace == "example-service"
    assert first.celery_app_name == "example_service"
    assert first.resolved_celery_broker_url == "redis://localhost:6379/1"
    assert first.resolved_celery_result_backend == "redis://localhost:6379/1"
    assert first.sync_database_url == "postgresql+psycopg://user:pass@host:5432/example"


def test_settings_slug_falls_back_to_app_name() -> None:
    settings = NoSlugSettings()

    assert settings.resolved_service_slug == "slugless-service"
    assert settings.celery_app_name == "slugless_service"


def test_database_url_validation() -> None:
    with pytest.raises(ValueError):
        ExampleSettings(database_url="")


def test_sync_database_url_translates_asyncpg() -> None:
    settings = ExampleSettings()
    assert settings.sync_database_url.startswith("postgresql+psycopg")


def test_sync_database_url_preserves_non_async_driver() -> None:
    class SQLiteSettings(BaseServiceSettings):
        database_url: str = "sqlite:///tmp.db"

    settings = SQLiteSettings()
    assert settings.sync_database_url == "sqlite:///tmp.db"


def test_backup_storage_url_normalization() -> None:
    class BackupSettings(BaseServiceSettings):
        backup_storage_url: str | None = "https://bucket.example.com/path/"

    settings = BackupSettings()
    assert settings.backup_storage_url == "https://bucket.example.com/path"

    empty = BaseServiceSettings(backup_storage_url="")
    assert empty.backup_storage_url is None


def test_settings_parse_csv_fields() -> None:
    settings = ExampleSettings(
        cors_allow_origins="https://one.example, https://two.example",
        cors_allow_methods="GET, POST",
        cors_allow_headers="Authorization, X-Custom",
        cors_expose_headers="X-Trace",
        spaps_auth_exempt_paths="/readyz, /livez",
    )

    assert settings.cors_allow_origins == ("https://one.example", "https://two.example")
    assert settings.cors_allow_methods == ("GET", "POST")
    assert settings.cors_allow_headers == ("Authorization", "X-Custom")
    assert settings.cors_expose_headers == ("X-Trace",)
    assert settings.spaps_auth_exempt_paths == ("/readyz", "/livez")


def test_cors_max_age_validation() -> None:
    with pytest.raises(ValueError):
        ExampleSettings(cors_max_age=-5)


def test_refresh_cookie_fields_default_values() -> None:
    settings = BaseServiceSettings()

    assert settings.spaps_refresh_cookie_name == "spaps_refresh_token"
    assert settings.spaps_refresh_cookie_path == "/"
    assert settings.spaps_refresh_cookie_domain is None
    assert settings.spaps_refresh_cookie_secure is False
    assert settings.spaps_refresh_cookie_samesite == "lax"


def test_refresh_cookie_settings_accept_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPAPS_REFRESH_COOKIE_NAME", "htma_refresh")
    monkeypatch.setenv("SPAPS_REFRESH_COOKIE_PATH", "/api/auth")
    monkeypatch.setenv("SPAPS_REFRESH_COOKIE_DOMAIN", "example.com")
    monkeypatch.setenv("SPAPS_REFRESH_COOKIE_SECURE", "true")
    monkeypatch.setenv("SPAPS_REFRESH_COOKIE_SAMESITE", "strict")

    settings = BaseServiceSettings()

    assert settings.spaps_refresh_cookie_name == "htma_refresh"
    assert settings.spaps_refresh_cookie_path == "/api/auth"
    assert settings.spaps_refresh_cookie_domain == "example.com"
    assert settings.spaps_refresh_cookie_secure is True
    assert settings.spaps_refresh_cookie_samesite == "strict"
