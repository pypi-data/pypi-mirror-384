# Quickstart Alignment TDD Tracker

This checklist keeps the shared `spaps-server-quickstart` package aligned with the
Ingredient and HTMA services. Each item follows a TDD flow: write/extend tests →
implement minimal code → update docs → rerun suites in the local `.venv`.

## Completed

- ✅ **Runtime parity**: bumped to Python 3.12, synced dependency matrix, expanded import smoke tests. (`tests/test_imports.py`, `pyproject.toml`)
- ✅ **Release hygiene groundwork**: cleaned stale `dist/` artefacts and ensured future builds are ignored. (Follow-up version bump still pending.)
- ✅ **Auth parity with live services**: ported validation + error handling from `htma_server/core/auth.py`, added regression coverage for invalid/renewed sessions and upstream 5xx fallbacks. (`src/spaps_server_quickstart/auth/__init__.py`, `tests/test_auth.py`)
- ✅ **Shared settings/application scaffolding**: expanded settings to cover CORS/auth exemption options and wired `create_app` to mirror live service middleware defaults with regression tests. (`src/spaps_server_quickstart/settings.py`, `src/spaps_server_quickstart/app_factory.py`, `tests/test_app_factory.py`, `tests/test_settings.py`)
- ✅ **Auth channel support**: added async magic-link and wallet helpers backed by `spaps_client`, with structured error handling and regression tests plus migration guidance. (`src/spaps_server_quickstart/auth_channels.py`, `tests/test_auth_channels.py`, `docs/MIGRATION_GUIDE.md`)
- ✅ **RBAC & starter modules**: introduced shared role helpers (`spaps_server_quickstart.rbac`), domain templates using them, and regression coverage plus downstream contract tests. (`src/spaps_server_quickstart/rbac/__init__.py`, `templates/domains/`, `tests/test_rbac.py`, `tests/test_operations_templates.py`)
- ✅ **Operational templates**
  - Added `templates/operations/` with Makefile targets, `.env.production.example`, production docker-compose, and GHCR-backed deploy/proxy scripts.
  - Documented adoption guidance in `README.md` and `docs/MIGRATION_GUIDE.md` (including GHCR secrets, `SPAPS_IMAGE`, and reverse-proxy refresh steps).
  - Added regression coverage ensuring templates stay packaged (`tests/test_operations_templates.py`) and downstream contract tests in HTMA/Ingredient plans.

## In Progress

- ☐ **Downstream coordination**
  - Publish a reference table of environment variables (auth exemptions, CORS) in `docs/MIGRATION_GUIDE.md` / `README.md`. ✅
  - Sync HTMA/Ingredient migration plans and docs once the shared release is cut. ✅
- ✅ **Release bookkeeping**
  - Added changelog entry for `0.1.0` and bumped `pyproject.toml` / `__version__` to match.
- ☐ **Infrastructure/testing guidance**
  - Provide Testcontainers-driven examples or fixtures plus documentation for Postgres/Redis integration tests.
  - Stand up a shared FastAPI + Celery smoke test harness to validate the app factory with auth/CORS toggles.

## Guardrail Pattern

- Before marking a quickstart capability as “ready”, ensure:
  - ✅ Quickstart regression tests cover the behaviour (`tests/...` inside this package).
  - ✅ Service TDD plans call out the shared helper and reference those tests.
  - ✅ Each consuming service has a lightweight `tests/external/test_quickstart_*_contract.py`
    suite that imports the helper directly (smoke test) so future quickstart changes break
    early in downstream CI.
- Keep the pattern consistent for new features (RBAC, database resources, Celery, operations)
  to avoid patch releases after migrations start.

## Working Notes

- Always run `pytest` inside the package `.venv`.
- Keep service references handy:
  - Settings/Auth: `ingredient_server/core/settings.py`, `htma_server/core/auth.py`
  - Testcontainers: `ingredient_server/tests/conftest.py`, `htma_server/tests/conftest.py`
