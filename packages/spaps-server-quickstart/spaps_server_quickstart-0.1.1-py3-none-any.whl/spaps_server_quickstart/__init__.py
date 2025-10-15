"""
Shared service scaffolding for Sweet Potato backend applications.

The package gathers reusable FastAPI, Celery, settings, database, logging, and
authentication helpers that individual services (HTMA, Ingredient, etc.) can consume.
"""

from .alembic import allowed_domains, collect_directory_errors, ensure_known_domain, slugify_title, validate_migration_filename
from .app_factory import create_app
from .auth import (
    AuthenticationError,
    AuthenticatedUser,
    SpapsAuthMiddleware,
    SpapsAuthService,
    build_spaps_auth_service,
)
from .auth.cookies import clear_refresh_cookie, set_refresh_cookie
from .auth_channels import (
    AuthChannelError,
    SpapsAuthChannelService,
    build_spaps_auth_channel_service,
)
from .rbac import RoleMatch, has_required_roles, require_roles
from .api.health import HealthRouterFactory
from .api.router import build_base_router
from .db import (
    AlembicMigrationRunner,
    DatabaseResources,
    create_async_sessionmaker,
    create_migration_runner,
    session_dependency_factory,
)
from .logging import configure_logging
from .middleware import RequestLoggingMiddleware
from .schemas import HealthResponse
from .settings import BaseServiceSettings, create_settings_loader, get_settings
from .tasks import create_celery_app, build_notification_task, build_ping_task

__version__ = "0.1.1"

__all__ = [
    "create_app",
    "BaseServiceSettings",
    "create_settings_loader",
    "get_settings",
    "configure_logging",
    "RequestLoggingMiddleware",
    "AuthenticationError",
    "AuthenticatedUser",
    "SpapsAuthService",
    "SpapsAuthMiddleware",
    "build_spaps_auth_service",
    "set_refresh_cookie",
    "clear_refresh_cookie",
    "SpapsAuthChannelService",
    "AuthChannelError",
    "build_spaps_auth_channel_service",
    "has_required_roles",
    "require_roles",
    "RoleMatch",
    "HealthRouterFactory",
    "HealthResponse",
    "build_base_router",
    "DatabaseResources",
    "create_async_sessionmaker",
    "session_dependency_factory",
    "AlembicMigrationRunner",
    "create_migration_runner",
    "create_celery_app",
    "build_ping_task",
    "build_notification_task",
    "validate_migration_filename",
    "collect_directory_errors",
    "ensure_known_domain",
    "allowed_domains",
    "slugify_title",
    "__version__",
]
