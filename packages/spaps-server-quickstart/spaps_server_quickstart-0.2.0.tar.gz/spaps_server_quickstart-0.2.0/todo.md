# Step Tracking

This checklist keeps the Step 1 / Step 2 work explicit while we stand up the
`python-server-quickstart` package.

## Step 1 – Package Scaffold

- [x] Create `packages/python-server-quickstart` directory.
- [x] Add `pyproject.toml` with build metadata and dependencies.
- [x] Add project `README.md` describing purpose and dev workflow.
- [x] Create initial source package with namespace `spaps_server_quickstart`.
- [x] Add `__init__.py` and module stubs for shared components.
- [x] Set up placeholder tests verifying importability.

## Step 2 – Populate Shared Modules

- [x] Copy shared FastAPI app factory from service repos.
- [x] Copy shared settings base class and configuration helpers.
- [x] Copy shared Celery bootstrap/runtime configuration.
- [x] Migrate middleware, logging, DB session, alembic naming utilities.
- [x] Add consolidated health schema + router helpers.
- [x] Backfill unit tests covering shared behaviours.

## Step 3 – Stabilise Lifecycle & Infrastructure Hooks

- [x] Replace `@app.on_event` usage in `app_factory` with FastAPI lifespan handlers.
- [x] Update tests to exercise lifespan shutdown (ensure SPAPS auth service closes cleanly).
- [x] Document lifespan expectations in `README.md` so consumers adopt the pattern.

## Step 4 – Service Templates & Roles

- [x] Provide optional starter modules (e.g., `domains/users`, `domains/admin`) demonstrating shared patterns.
- [x] Include sample RBAC/role helpers so services can distinguish user vs. admin paths.
- [x] Wire example routes into the shared quickstart README to guide new service authors.

## Step 5 – Migration Playbooks & Release Hygiene

- [x] Add a downstream migration guide outlining the exact steps HTMA/Ingredient must follow.
- [x] Introduce `CHANGELOG.md` and a release checklist/script for publishing `spaps-server-quickstart`.
- [x] Document database/Celery helper usage conventions so services know how to adopt `DatabaseResources` and task factories.

## Step 6 – Unified Release Automation

- [x] Generalise version management tooling (shared `scripts/manage_python_package_version.py`).
- [x] Add reusable GitHub Actions workflow for publishing Python packages.
- [x] Ensure the workflow handles first-time releases (fallback to 0.0.0 published version).
- [x] Update release documentation to point maintainers at the unified workflow.

## To Discuss

- Align on a timeline for removing duplicated middleware/auth/logging from HTMA and Ingredient once migrations land.
- Create a service compatibility matrix (which quickstart version pairs with which service release).
- Add guidance for provisioning separate databases and environment variables per downstream service.
- Decide how downstream CI pipelines will install/test the shared package (prepush hooks, GitHub Actions updates).
- Plan cross-service smoke tests that instantiate the shared app and celery worker to catch future regressions.
- Confirm how role-based access (labs/admin) should hook into the shared auth helpers to avoid divergent implementations.
- Capture pgvector/Postgres parity gaps vs. Ingredient/HTMA (extension migration, docker-compose templates, integration fixtures) so we can backfill shared scaffolding later.
