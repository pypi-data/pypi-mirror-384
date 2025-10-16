#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "${ROOT_DIR}/.envrc" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ROOT_DIR}/.envrc"
  set +a
fi

cd "${ROOT_DIR}"

VENV_BIN="${ROOT_DIR}/.venv/bin"

resolve_tool() {
  local bin_name="$1"
  if [[ -x "${VENV_BIN}/${bin_name}" ]]; then
    echo "${VENV_BIN}/${bin_name}"
  else
    command -v "${bin_name}" || true
  fi
}

RUFF="$(resolve_tool ruff)"
MYPY="$(resolve_tool mypy)"
PYTEST="$(resolve_tool pytest)"
PYTHON="$(resolve_tool python3)"

if [[ -z "${RUFF}" ]]; then
  echo "⚠️  ruff not found; install it or run 'make install' first." >&2
  exit 1
fi
if [[ -z "${MYPY}" ]]; then
  echo "⚠️  mypy not found; install it or run 'make install' first." >&2
  exit 1
fi
if [[ -z "${PYTEST}" ]]; then
  echo "⚠️  pytest not found; install it or run 'make install' first." >&2
  exit 1
fi
if [[ -z "${PYTHON}" ]]; then
  echo "⚠️  Python interpreter not found. Activate your virtualenv or install Python 3.12." >&2
  exit 1
fi

RUN_MIGRATIONS="${PREPUSH_RUN_MIGRATIONS:-false}"
RUN_TESTS="${PREPUSH_RUN_TESTS:-false}"

ALEMBIC_CMD="$(resolve_tool alembic)"

if [[ "${RUN_MIGRATIONS}" == "true" && -n "${ALEMBIC_CMD}" ]]; then
  if [[ -z "${PYTEST_DATABASE_URL:-}" ]]; then
    if [[ -n "${DATABASE_URL:-}" ]]; then
      export PYTEST_DATABASE_URL="${DATABASE_URL}"
    else
      echo "ℹ️  No PYTEST_DATABASE_URL/DATABASE_URL set; skipping migrations." >&2
      RUN_MIGRATIONS="false"
    fi
  fi
  if [[ -n "${PYTEST_DATABASE_URL:-}" && -z "${DATABASE_URL:-}" ]]; then
    export DATABASE_URL="${PYTEST_DATABASE_URL}"
  fi
fi

if [[ "${RUN_MIGRATIONS}" == "true" && -n "${ALEMBIC_CMD}" ]]; then
  echo "⏱ Waiting for database..."
  "${PYTHON}" - <<'PY'
import asyncio
import os

import asyncpg


async def wait_for_db(dsn: str) -> None:
    retries = 10
    for attempt in range(1, retries + 1):
        try:
            conn = await asyncpg.connect(dsn)
        except Exception:
            if attempt == retries:
                raise
            await asyncio.sleep(2)
        else:
            await conn.close()
            return


dsn = os.environ["PYTEST_DATABASE_URL"].replace("+asyncpg", "")
asyncio.run(wait_for_db(dsn))
PY

  if [[ "${PREPUSH_RESET_DB:-false}" == "true" ]]; then
    echo "🧨 Resetting database (alembic downgrade base)..."
    PYTHONPATH="${ROOT_DIR}${PYTHONPATH:+:${PYTHONPATH}}" "${ALEMBIC_CMD}" downgrade base
  fi

  echo "📦 Running Alembic migrations..."
  PYTHONPATH="${ROOT_DIR}${PYTHONPATH:+:${PYTHONPATH}}" "${ALEMBIC_CMD}" upgrade head
else
  echo "ℹ️  Skipping migrations (PREPUSH_RUN_MIGRATIONS=${RUN_MIGRATIONS})."
fi

if [[ -n "${ALEMBIC_CMD}" ]]; then
  echo "🧪 Dry-running Alembic migrations..."
  PYTHONPATH="${ROOT_DIR}${PYTHONPATH:+:${PYTHONPATH}}" "${ALEMBIC_CMD}" upgrade --sql head >/dev/null
fi

if [[ -f "scripts/check_migration_domains.py" ]]; then
  echo "🧾 Checking migration naming..."
  "${PYTHON}" scripts/check_migration_domains.py
fi

echo "🔍 Running lint..."
"${RUFF}" check src tests

echo "🧠 Running mypy..."
"${MYPY}" src

if [[ "${RUN_TESTS}" == "true" ]]; then
  echo "🧪 Running tests..."
  "${PYTEST}"
else
  echo "ℹ️  Skipping tests (PREPUSH_RUN_TESTS=${RUN_TESTS})."
fi

echo "✅ Pre-push checks passed."
