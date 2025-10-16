# Changelog

All notable changes to this project will be documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- _No changes yet._

## [0.1.1] - 2025-10-14

- Maintenance release bumping the package version to unblock the automated PyPI publish workflow.

## [0.1.0] - 2025-10-14

- Added FastAPI lifespan handling for SPAPS auth cleanup.
- Introduced migration guide and upgrading instructions for downstream services.
- Established comprehensive unit tests across settings, middleware, DB, Celery, and auth helpers.
- Centralised refresh-cookie configuration on `BaseServiceSettings` and exported reusable
  helpers (`set_refresh_cookie`, `clear_refresh_cookie`) for browser flows.
- Repacked auth helpers under `spaps_server_quickstart.auth` and expanded top-level exports to
  simplify downstream imports.
- Extended documentation and readiness notes to cover shared refresh-cookie env vars, FastAPI
  factory helpers, and auth integration expectations ahead of service migrations.
- Added `spaps_server_quickstart.rbac` role helpers plus sample domain routers and ensured
  packaged templates remain available via regression and contract tests.
- Added operational templates (Makefile, GHCR deploy script, compose/reverse-proxy stubs, env
  example) plus documentation to standardise the GHCR + proxy deployment flow across services.

## [0.0.2] - 2025-10-12

- Declared the `spaps` Python client dependency so downstream installs and CI runs have `spaps_client` available.

## [0.0.1] - 2025-10-14

- Initial scaffold of `spaps-server-quickstart` with shared FastAPI/Celery/DB utilities.
