# Upgrading Downstream Services

When `spaps-server-quickstart` publishes new releases, dependent services (e.g.
`htma_server`, `ingredient_server`) need a predictable upgrade cadence. Follow this
checklist whenever we cut a release or adopt a newer version downstream.

## For the Quickstart Maintainer (Publishing a Release)

1. **Triage changes** – confirm whether the release is a patch, minor, or major bump.
   - Patch (x.y.Z) for bug fixes and strictly backwards-compatible tweaks.
   - Minor (x.Y.0) for new features that keep existing APIs stable.
   - Major (X.0.0) for breaking changes; document migration steps clearly.
2. **Update metadata**
   - Bump `version` in `pyproject.toml`.
   - Add release notes to `CHANGELOG.md` (include migration guidance for non-trivial upgrades).
3. **Run validation locally**
   - `python3 -m pip install -e '.[dev]'`
   - `python3 -m pytest -q`
   - `python3 -m ruff check src tests`
   - `python3 -m mypy src`
4. **Publish the package**
   - `npm run build:python-client` is **not** required here; instead run:
     ```bash
     cd packages/python-server-quickstart
     python -m build
     python -m twine upload dist/*
     ```
   - If the package is private, upload to the internal index configured for SPAPS.
5. **Announce the release**
   - Share the version, changelog highlights, and any upgrade notes in the engineering
     channel or release tracker.

## For Downstream Services (Consuming a Release)

1. **Update dependencies**
   - In the service `pyproject.toml`, bump the `spaps-server-quickstart` requirement.
   - Run `poetry update spaps-server-quickstart` (or `pip-compile` if using pip-tools).
2. **Re-install local environment**
   - `poetry install` (or `python3 -m pip install -e '.[dev]'`) to ensure the new version +
     transitive deps are in the virtualenv.
3. **Run the validation stack**
   - `npm run prepush` from repo root (covers lint, typecheck, pytest, docs health).  
     Minimum checks:
     ```bash
     poetry run pytest
     poetry run ruff check src tests
     poetry run mypy src
      poetry run python - <<'PY'
      from spaps_server_quickstart.db import DatabaseResources
      from <service>.core.settings import get_settings

      resources = DatabaseResources(get_settings())
      assert resources.get_session_factory()
      PY
     ```
   - If the service uses Docker images, rebuild them locally to catch runtime regressions.
4. **Exercise lifecycles**
   - Confirm the FastAPI app starts and shuts down cleanly (`uvicorn`, `pytest` with `TestClient`).
   - Verify Celery workers boot and call `create_celery_app(settings, task_modules=["<service>.tasks"])`.
5. **Merge and deploy**
   - Once CI is green, merge the dependency bump PR.
   - Roll out through the standard deployment pipeline (staging → production) while watching
     health checks. The shared `HealthRouterFactory` will surface database readiness issues.

## Handling Breaking Changes

- **Major releases** should ship with migration utilities or example diffs in
  `docs/UPGRADING.md`.
- If removing or renaming APIs, deprecate in one release cycle first (log a warning),
  then remove in the next major version.
- Add integration tests in both the quickstart package and dependent services to guard
  behaviour that might regress.

## Version Pinning Guidelines

- Each service should pin `spaps-server-quickstart` to a compatible minor range,
  e.g. `^0.2.0`.
- Avoid `*` or wide specifiers. This prevents surprise upgrades when publishing other packages.
- For hotfixes, release a patch version and bump immediately downstream.

By following this flow, the quickstart can evolve confidently while keeping HTMA, Ingredient,
and future services stable.
