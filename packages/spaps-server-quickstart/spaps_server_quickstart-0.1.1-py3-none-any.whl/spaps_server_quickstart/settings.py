"""
Shared settings base classes for Sweet Potato services.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Callable, ClassVar, Iterable, Literal

from pydantic import AnyHttpUrl, TypeAdapter, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    """
    Common configuration knobs for Sweet Potato services.

    Individual services should subclass this base to add domain-specific fields
    (for example, `ingredients_api_key`) and optionally override defaults for the
    application name, database URL, and other metadata.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="allow",
    )

    env: str = "dev"
    debug: bool = False
    app_name: str = "Sweet Potato Service"
    version: str = "0.1.0"
    service_slug: str | None = None
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "json"
    log_include_tracebacks: bool = False
    log_file_path: str | None = None

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/service"
    database_echo: bool = False
    database_pool_size: int = 10
    database_max_overflow: int = 10
    database_pool_timeout: int = 30

    pgvector_schema: str = "public"
    backup_storage_url: str | None = None
    spaps_auth_enabled: bool = False
    spaps_api_url: str = "https://api.sweetpotato.dev"
    spaps_api_key: str | None = None
    spaps_application_id: str | None = None
    spaps_request_timeout: float = 10.0
    spaps_refresh_cookie_name: str = "spaps_refresh_token"
    spaps_refresh_cookie_path: str = "/"
    spaps_refresh_cookie_domain: str | None = None
    spaps_refresh_cookie_secure: bool = False
    spaps_refresh_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    spaps_auth_exempt_paths: Annotated[tuple[str, ...], NoDecode] = ("/health", "/docs", "/redoc")
    cors_allow_origins: Annotated[tuple[str, ...], NoDecode] = ()
    cors_allow_methods: Annotated[
        tuple[str, ...],
        NoDecode,
    ] = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
    cors_allow_headers: Annotated[tuple[str, ...], NoDecode] = ("Authorization", "Content-Type")
    cors_expose_headers: Annotated[tuple[str, ...], NoDecode] = ()
    cors_allow_credentials: bool = True
    cors_max_age: int = 600

    _any_http_adapter: ClassVar[TypeAdapter[AnyHttpUrl]] = TypeAdapter(AnyHttpUrl)

    @property
    def resolved_service_slug(self) -> str:
        if self.service_slug:
            return self.service_slug
        return self.app_name.lower().replace(" ", "-")

    @property
    def logger_namespace(self) -> str:
        return self.resolved_service_slug

    @property
    def celery_app_name(self) -> str:
        return self.resolved_service_slug.replace("-", "_")

    @property
    def sync_database_url(self) -> str:
        """
        Alembic runs in synchronous mode; translate the async DSN to a synchronous driver.
        """

        if self.database_url.startswith("postgresql+asyncpg"):
            return self.database_url.replace("postgresql+asyncpg", "postgresql+psycopg")
        return self.database_url

    @property
    def resolved_celery_broker_url(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def resolved_celery_result_backend(self) -> str:
        return self.celery_result_backend or self.redis_url

    @field_validator("database_url")
    @classmethod
    def _validate_database_url(cls, value: str) -> str:
        if not value:
            raise ValueError("DATABASE_URL must be provided")
        return value

    @field_validator("backup_storage_url", mode="before")
    @classmethod
    def _validate_backup_storage_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value == "":
            return None
        normalized_value = value.rstrip("/")
        cls._any_http_adapter.validate_python(normalized_value)
        return normalized_value

    @staticmethod
    def _normalize_csv(value: Iterable[str] | str | None) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, str):
            items = [item.strip() for item in value.split(",")]
        else:
            items = [str(item).strip() for item in value]
        return tuple(item for item in items if item)

    @field_validator(
        "cors_allow_origins",
        "cors_allow_methods",
        "cors_allow_headers",
        "cors_expose_headers",
        "spaps_auth_exempt_paths",
        mode="before",
    )
    @classmethod
    def _parse_csv_fields(cls, value: Iterable[str] | str | None) -> tuple[str, ...]:
        return cls._normalize_csv(value)

    @field_validator("cors_max_age")
    @classmethod
    def _validate_cors_max_age(cls, value: int) -> int:
        if value < 0:
            raise ValueError("CORS_MAX_AGE must be non-negative")
        return value


def create_settings_loader(
    settings_cls: type[BaseServiceSettings],
) -> Callable[[], BaseServiceSettings]:
    """
    Convenience helper that mirrors the `get_settings` pattern used inside the services.

    Usage:
        class IngredientSettings(BaseServiceSettings):
            ...

        get_settings = create_settings_loader(IngredientSettings)
    """

    @lru_cache(maxsize=1)
    def _loader() -> BaseServiceSettings:
        return settings_cls()

    return _loader


# Backwards-compatible alias for consumers that expect a zero-argument getter.
def get_settings() -> BaseServiceSettings:
    """
    Default settings loader for scenarios where no custom subclass is registered.

    Services are expected to call `create_settings_loader` but exposing this makes the
    shared utilities usable out of the box (with generic defaults).
    """

    return _DEFAULT_SETTINGS_LOADER()


@lru_cache(maxsize=1)
def _DEFAULT_SETTINGS_LOADER() -> BaseServiceSettings:
    return BaseServiceSettings()
