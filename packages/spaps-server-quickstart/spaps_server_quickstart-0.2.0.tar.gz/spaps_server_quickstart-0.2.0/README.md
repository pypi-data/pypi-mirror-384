# SPAPS Server Quickstart

Reusable scaffolding for Sweet Potato service backends. This package gathers the FastAPI
application factory, Celery bootstrap, Pydantic settings base classes, and other utilities
that HTMA, Ingredient, and future services can share.

## Installation

Use either Poetry (preferred inside this repo) or pip editable installs:

```bash
# with poetry
poetry install -C packages/python-server-quickstart

# or with pip (installs package + dev extras)
python3 -m pip install -e 'packages/python-server-quickstart[dev]'
```

The editable install ensures FastAPI, SQLAlchemy, Celery, and other dependencies are
available when the pre-push scripts execute.

## Local Development

```bash
poetry run -C packages/python-server-quickstart pytest
```

The shared modules are designed to be imported by individual service packages. Tests live
alongside the shared code to guard the common behaviour.

## Operational Templates

For infrastructure parity with live SPAPS services, the directory
`templates/operations` contains a ready-to-copy bundle that now includes:

- Makefile with lint/test/deploy shortcuts
- Production `.env.production.example`
- Docker Compose + reverse-proxy stubs
- Deploy script that refreshes the shared proxy
- Database maintenance scripts (`backup-db.sh`, `restore-db.sh`, `new-migration.sh`)
- Pre-push hook + `scripts/prepush.sh` matching live automation

Copy the folder into a service repository when adopting the quickstart so CI/CD, GHCR pulls, backup automation,
and the shared reverse proxy follow the same playbook used by Ingredient, HTMA, and Sweet Potato. Update the provided
environment variables (`PROJECT_SLUG`, `DB_SERVICE`, etc.) after copying to match the new service naming.

## RBAC Helpers & Sample Routers

- Use `spaps_server_quickstart.rbac.require_roles` as a FastAPI dependency to guard admin/staff-only
  routes. It returns the authenticated user when the role check passes and raises `HTTPException`
  (401/403) otherwise.
- `spaps_server_quickstart.rbac.has_required_roles` provides a lightweight predicate when you need to
  branch on roles outside of dependency injection.
- Copy the sample routers under `spaps_server_quickstart.templates.domains` (users/admin) when spinning
  up new services—they demonstrate how to wire the RBAC helpers into typical CRUD endpoints.

## Configuration Highlights

Services configure behaviour by subclassing `BaseServiceSettings`. Override fields like
`spaps_auth_exempt_paths` to expose unauthenticated endpoints or set `cors_allow_origins`
(and related CORS knobs) to attach the shared `CORSMiddleware` without writing per-service
plumbing. All list-like settings accept comma-separated environment variables for easy deployment.

### Auth Channels (Magic Link & Wallet)

- `SpapsAuthChannelService` wraps SPAPS magic-link and wallet authentication so services can drop the boilerplate client calls.
- Use `send_magic_link` / `verify_magic_link` for email links and `request_wallet_nonce` / `verify_wallet` for Solana or Ethereum sign-ins.
- The helpers raise `AuthChannelError` with `status_code` and `error_code`, giving your routes enough context to map responses cleanly.
- Lifecycle management mirrors the main auth service—call `await service.aclose()` during shutdown if you create a long-lived instance.

### Secure Messaging Gateway

- `spaps_server_quickstart.secure_messaging.build_secure_messaging_gateway` returns an async gateway mirroring HTMA’s
  SPAPS secure messaging integration. It logs send/list operations and normalises upstream failures into
  `SecureMessagingGatewayError`.
- `provide_secure_messaging_gateway` enforces feature flags and required roles before returning a configured gateway.
  Wire it into FastAPI dependencies to replicate practitioner-only messaging flows without bespoke plumbing.
- `SecureMessagingContext` carries practitioner/patient identifiers and optional access tokens; the helper merges default
  metadata (`application_id`, `practitioner_user_id`) so downstream analytics remain consistent across services.
- Settings expose `secure_messages_enabled`, `secure_messages_timeout`, and
  `secure_messages_default_page_size`, letting each service toggle secure messaging per environment.

### Auth Dependencies

- `spaps_server_quickstart.auth.dependencies.require_authenticated_user` retrieves the `AuthenticatedUser`
  assigned by `SpapsAuthMiddleware`, raising a 401 when the request lacks credentials.
- `require_authenticated_role("role")` returns a dependency that asserts the subject holds a given role (case-insensitive),
  raising a 403 otherwise. Use it for common admin/practitioner guardrails without reimplementing role checks.

### Environment Reference

| Variable | Description | Notes |
| --- | --- | --- |
| `SPAPS_API_URL` | Base URL for SPAPS API requests | Defaults to `https://api.sweetpotato.dev` |
| `SPAPS_API_KEY` | Service API key used for auth + channel helpers | Required when `spaps_auth_enabled` is true |
| `SPAPS_APPLICATION_ID` | Application identifier enforced during session validation | Required when `spaps_auth_enabled` is true |
| `SPAPS_AUTH_ENABLED` | Toggle for the auth middleware | Enables `SpapsAuthMiddleware` when `true` |
| `SPAPS_AUTH_EXEMPT_PATHS` | Comma-separated paths that bypass auth | Parsed into a tuple automatically |
| `SPAPS_REQUEST_TIMEOUT` | Timeout (seconds) for SPAPS HTTP calls | Applies to both auth and channel helpers |
| `CORS_ALLOW_ORIGINS` / `CORS_ALLOW_METHODS` / `CORS_ALLOW_HEADERS` | Comma-separated CORS configuration | Leave empty to skip the middleware |
| `CORS_EXPOSE_HEADERS` | Headers exposed to clients | Defaults to empty tuple |
| `CORS_ALLOW_CREDENTIALS` | Whether CORS requests include credentials | Defaults to `true` |
| `CORS_MAX_AGE` | CORS preflight cache duration | Must be non-negative |
| `SECURE_MESSAGES_ENABLED` | Toggle SPAPS secure messaging gateway wiring | Defaults to `false` |
| `SECURE_MESSAGES_TIMEOUT` | Override secure messaging request timeout | Falls back to `SPAPS_REQUEST_TIMEOUT` |
| `SECURE_MESSAGES_DEFAULT_PAGE_SIZE` | Default `list_messages` page size | Must be positive |

## Lifecycle Hooks

`create_app` now uses FastAPI's lifespan context to close shared resources (e.g., SPAPS auth
clients). When you need additional startup/shutdown logic, extend the lifespan in your service
by wrapping the provided app with your own context manager or closing resources within your
domain packages. Running tests with `TestClient(app)` will automatically exercise the shutdown path and catch missing
`aclose()` implementations. Pair this with `spaps_server_quickstart.db.collect_migration_status` inside custom health
metrics providers to surface Alembic drift on `/health` (mirroring HTMA’s practitioner metrics).

## Upgrading Downstream Services

Guidance for publishing new versions and upgrading consumer services lives in
[`docs/UPGRADING.md`](docs/UPGRADING.md). Review those steps before bumping the package or
pulling a newer release into `htma_server`, `ingredient_server`, or other SPAPS services.

## Migrating an Existing Service

See [`docs/MIGRATION_GUIDE.md`](docs/MIGRATION_GUIDE.md) for a step-by-step walkthrough of
adopting the shared package inside an existing FastAPI/Celery service. It covers settings
integration, router wiring, database session management, Celery bootstraps, and the final
cleanup checklist.

## Release Workflow

- Use the GitHub Action **Publish Python Server Quickstart** (`.github/workflows/python-server-quickstart-release.yml`) to cut releases. It reuses the generic `python-package-release` workflow alongside `scripts/manage_python_package_version.py`.
- Ensure the repository secret `PYPI_SERVER_QUICKSTART_TOKEN` holds the PyPI API token for this package.
- For manual bumps, dispatch the workflow and choose the bump type (major/minor/patch). For automated publishes, pushing a commit that updates `packages/python-server-quickstart/pyproject.toml` will trigger the workflow.

## Status

- [x] Initial package scaffold
- [x] Shared application factories
- [x] Shared Celery bootstrap
- [x] Shared middleware, logging, and settings base classes
- [x] Health endpoint helpers
- [x] Documentation and usage examples

## Repository Integration

The root `package.json` includes `lint:python-server-quickstart`, `typecheck:python-server-quickstart`,
and `test:python-server-quickstart` commands. These run automatically via `npm run prepush`, and the npm
scripts install `packages/python-server-quickstart[dev]` on demand so the editable install step is handled
for you.
