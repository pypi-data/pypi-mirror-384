# Migrating a Service to `spaps-server-quickstart`

This playbook describes the concrete steps for services like `htma_server` and
`ingredient_server` to replace local scaffolding with the shared package. Expect a
single PR per service.

## 1. Prepare the Service

1. **Pin the dependency**
   - Add `spaps-server-quickstart = "^0.x"` to the service `pyproject.toml`.
   - `poetry update spaps-server-quickstart` (or pip equivalent) and commit the lockfile.
2. **Install tooling**
   - Ensure the editable install exists locally: `python3 -m pip install -e 'packages/python-server-quickstart[dev]'`.
   - Run the shared package tests once: `npm run test:python-server-quickstart`.
3. **Configure SPAPS auth defaults**
   - Set `spaps_auth_enabled = True` on the service settings subclass and ensure `SPAPS_API_URL`, `SPAPS_API_KEY`, and `SPAPS_APPLICATION_ID` are available in each environment.
   - Document these variables in the service README or deployment manifests so operators know they are required.
   - If the service needs additional unauthenticated endpoints or custom role hints, extend `spaps_auth_exempt_paths` on the settings subclass or pass `auth_exempt_paths`/`role_hints` when wiring `create_app` or `build_spaps_auth_service`. The shared factory merges both sources.
   - Capture CORS requirements by overriding `cors_allow_origins` (and related fields) on the settings subclass instead of adding per-service middleware.
   - Standardise refresh-cookie behaviour for browser flows by overriding `spaps_refresh_cookie_*` fields when custom names, domains, or `SameSite` policies are required.

## 2. Settings & Configuration

1. Replace the local `Settings` class with a subclass of `spaps_server_quickstart.settings.BaseServiceSettings`.
   ```python
   from spaps_server_quickstart.settings import BaseServiceSettings, create_settings_loader

   class Settings(BaseServiceSettings):
       app_name: str = "HTMA Server"
       service_slug: str = "htma-server"
       database_url: str = "postgresql+asyncpg://.../htma"
       # include service-specific fields (e.g., practitioners, ingredient keys)

   get_settings = create_settings_loader(Settings)
   ```
2. Update imports wherever `Settings` or `get_settings` were used (app factory, dependencies, tasks).
3. Map environment variables:
   - `SPAPS_AUTH_EXEMPT_PATHS`, `CORS_ALLOW_ORIGINS`, `CORS_ALLOW_METHODS`, and similar settings accept comma-separated lists and are parsed automatically.

### Environment Reference

| Variable | Description | Notes |
| --- | --- | --- |
| `SPAPS_API_URL` | Base URL for all SPAPS HTTP calls | Defaults to `https://api.sweetpotato.dev` |
| `SPAPS_API_KEY` | Service API key used when calling SPAPS | Required when auth is enabled |
| `SPAPS_APPLICATION_ID` | Expected application identifier when validating sessions | Required when auth is enabled |
| `SPAPS_AUTH_ENABLED` | Enables `SpapsAuthMiddleware` in the shared app factory | Set to `true` to enforce auth |
| `SPAPS_AUTH_EXEMPT_PATHS` | Comma-separated list of routes to bypass auth (e.g., `/health`) | Parsed into a tuple automatically |
| `SPAPS_REQUEST_TIMEOUT` | Timeout (seconds) for SPAPS HTTP requests | Applies to both auth and channel helpers |
| `SPAPS_REFRESH_COOKIE_NAME` | Cookie key used to store the SPAPS refresh token | Defaults to `spaps_refresh_token` |
| `SPAPS_REFRESH_COOKIE_PATH` | Cookie path scope | Defaults to `/` |
| `SPAPS_REFRESH_COOKIE_DOMAIN` | Domain attribute passed to the cookie | Optional |
| `SPAPS_REFRESH_COOKIE_SECURE` | Enables the `Secure` cookie flag | Defaults to `false` |
| `SPAPS_REFRESH_COOKIE_SAMESITE` | SameSite policy for the refresh cookie (`lax`, `strict`, or `none`) | Defaults to `lax` |
| `CORS_ALLOW_ORIGINS` / `CORS_ALLOW_METHODS` / `CORS_ALLOW_HEADERS` | Comma-separated CORS configuration values | Leave unset to skip CORS middleware |
| `CORS_EXPOSE_HEADERS` | Additional headers exposed to clients | Optional |
| `CORS_ALLOW_CREDENTIALS` | Controls `allow_credentials` for CORS middleware | Defaults to `true` |
| `CORS_MAX_AGE` | Preflight cache duration, must be non-negative | Defaults to `600` |

## 3. FastAPI Application & Routers

1. Remove the local `create_app` factory and import the shared one:
   ```python
   from spaps_server_quickstart.app_factory import create_app
   from spaps_server_quickstart.api.router import build_base_router
   from spaps_server_quickstart.api.health import HealthRouterFactory
   ```
2. Compose routers:
   ```python
   settings_loader = get_settings
   health_router = HealthRouterFactory(
       settings_loader=settings_loader,
       session_dependency=db_resources.session_dependency,
       extra_metrics_provider=custom_metrics,
   ).create_router()

   api_router = build_base_router(
       health_router,
       (practitioner_router, {"prefix": "/v1", "tags": ["practitioner"]}),
   )

   app = create_app(
       settings_loader=settings_loader,
       api_router=api_router,
       enable_spaps_auth=True,
       auth_exempt_paths={"/open-metrics"},
   )
   ```
3. Delete redundant local modules (auth, middleware, logging) once replaced.

## 4. Database Integration

1. Instantiate shared DB resources in a new `core/db.py` or similar:
   ```python
   from spaps_server_quickstart.db import DatabaseResources

   db_resources = DatabaseResources(get_settings())
   get_db_session = db_resources.session_dependency
   ```
2. Update dependencies in API modules (`Depends(get_db_session)`).
3. Ensure Alembic scripts reuse the shared naming validators if applicable.
4. Tie the shared engine lifecycle into your shutdown path (e.g., FastAPI lifespan or worker teardown) and call `await db_resources.dispose()` so test suites and local reloads do not leak connections.

## 5. Celery & Tasks

1. Replace the local `Celery` bootstrap with:
   ```python
   from spaps_server_quickstart.tasks import create_celery_app

   celery_app = create_celery_app(get_settings(), task_modules=["htma_server.tasks"])
   ```
2. Update shared tasks (`build_ping_task`, `build_notification_task`) or keep service-specific overrides as needed.

## 6. Magic Link & Wallet Auth

1. Import the shared helpers where you proxy SPAPS auth flows:
   ```python
   from spaps_server_quickstart.auth_channels import (
       SpapsAuthChannelService,
       build_spaps_auth_channel_service,
       AuthChannelError,
   )

   channel_service = build_spaps_auth_channel_service(get_settings())
   ```
2. Use `channel_service.send_magic_link` for email flows and
   `channel_service.request_wallet_nonce` / `channel_service.verify_wallet` for Solana/Ethereum
   sign-ins. The helpers return the underlying SPAPS client responses so you can forward tokens to
   the frontend without custom parsing.
3. Catch `AuthChannelError` to translate SPAPS error codes/status into your HTTP responses. The
   exception exposes `status_code` and `error_code` mirroring upstream values.
4. Document the new endpoints in your service (`docs/manifest.json`, feature docs) so frontend teams
   can integrate.

## 7. RBAC & Sample Domains

1. Guard sensitive routes with the shared RBAC dependency:
   ```python
   from spaps_server_quickstart.rbac import require_roles

   @router.get("/admin")
   async def admin_endpoint(current_user = Depends(require_roles(["admin"], match="all"))):
       ...
   ```
2. `require_roles` assumes `SpapsAuthMiddleware` populated `request.state.authenticated_user`; it returns the `AuthenticatedUser` instance when access is granted and raises `HTTPException` (401/403) otherwise.
3. Example domain routers live under `spaps_server_quickstart.templates.domains` (users/admin) demonstrating common patterns—copy them into your service if you need starter modules.
4. For role checks outside of dependencies, use `spaps_server_quickstart.rbac.has_required_roles(user.roles, ["staff"], match="any")`.

## 8. Test & Validate

1. Run unit/integration tests: `poetry run pytest`, `poetry run ruff`, `poetry run mypy`.
2. Run the root `npm run prepush` to cover shared checks.
3. Smoke test FastAPI and Celery locally if the service has start scripts.

## 9. Cleanup & Review

1. Remove unused files (duplicate middleware/auth/logging) and update service README docs to reference the shared package.
2. Ensure CI passes and request review. Highlight the dependency bump and key refactors in the PR summary.

## 10. Deployment & CI Integration

1. Copy the operations templates into the service repository: `cp -R packages/python-server-quickstart/templates/operations ./infrastructure` and adjust paths as required.
2. Ensure the service CI pushes container images to GHCR (for example `ghcr.io/<org>/<service>:${GITHUB_SHA}`).
3. Update redeploy scripts/workflows to:
    - Log into ghcr.io using `GHCR_DEPLOY_USER` / `GHCR_DEPLOY_TOKEN` secrets.
    - Pull the commit-tagged image and restart the app (or compose stack) with `SPAPS_IMAGE=<image:tag>` set in the environment.
    - Refresh `/opt/sweet-potato/deploy/reverse-proxy` so the shared proxy reloads certificates and vhosts.
4. Document these steps in the service README so operators can redeploy from GHCR without rebuilding locally (see `sweet-potato/deploy/production-checklist.md` for reference).

## Appendix: Checklist

- [ ] `pyproject.toml` dependency updated and installed.
- [ ] Settings subclass uses `create_settings_loader`.
- [ ] FastAPI app uses shared `create_app` and router helpers.
- [ ] Database dependencies go through `DatabaseResources`.
- [ ] Celery uses `create_celery_app` with correct task module.
- [ ] Tests + prepush suite green.
- [ ] Redundant local scaffolding removed.
