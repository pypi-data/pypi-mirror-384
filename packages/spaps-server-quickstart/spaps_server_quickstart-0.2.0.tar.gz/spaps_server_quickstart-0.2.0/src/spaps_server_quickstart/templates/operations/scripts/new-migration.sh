#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${ROOT_DIR}"

export PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"

usage() {
  cat <<'USAGE' >&2
Usage: scripts/new-migration.sh <domain> "<title>"

Creates a new Alembic revision enforcing the migration domain naming convention.
USAGE
}

if [[ $# -lt 2 ]]; then
  usage
  exit 1
fi

DOMAIN="$1"
shift
TITLE="$*"

if [[ -z "${TITLE}" ]]; then
  echo "⚠️  Migration title must not be empty." >&2
  exit 1
fi

VENV_BIN="${ROOT_DIR}/.venv/bin"

if [[ -x "${VENV_BIN}/python" ]]; then
  PYTHON="${VENV_BIN}/python"
else
  PYTHON="$(command -v python3 || command -v python || true)"
fi

if [[ -z "${PYTHON}" ]]; then
  echo "⚠️  Python interpreter not found. Activate your virtualenv or install Python 3.12+." >&2
  exit 1
fi

if [[ -x "${VENV_BIN}/alembic" ]]; then
  ALEMBIC="${VENV_BIN}/alembic"
else
  ALEMBIC="$(command -v alembic || true)"
fi

if [[ -z "${ALEMBIC}" ]]; then
  echo "⚠️  Alembic command not found. Did you install this project with test extras?" >&2
  exit 1
fi

mapfile -t PY_OUTPUT < <("${PYTHON}" - <<'PY' "${DOMAIN}" "${TITLE}"
from spaps_server_quickstart.alembic import naming
import sys

domain = naming.ensure_known_domain(sys.argv[1])
title = sys.argv[2]

slug = naming.slugify_title(title)
message = naming.build_revision_message(domain, title)

print(domain)
print(message)
print(f"{domain}_{slug}")
PY
)

NORMALIZED_DOMAIN="${PY_OUTPUT[0]}"
REVISION_MESSAGE="${PY_OUTPUT[1]}"
FILE_SUFFIX="${PY_OUTPUT[2]}"

REVISION_ID="$(date -u +"%Y%m%d%H%M")"
TARGET_FILE="alembic/versions/${REVISION_ID}_${FILE_SUFFIX}.py"

if [[ -e "${TARGET_FILE}" ]]; then
  echo "⚠️  Migration file ${TARGET_FILE} already exists. Choose a different title or wait a minute." >&2
  exit 1
fi

"${ALEMBIC}" revision --rev-id "${REVISION_ID}" -m "${REVISION_MESSAGE}"

if [[ -f "${TARGET_FILE}" ]]; then
  echo "✅ Created migration ${TARGET_FILE}"
  exit 0
fi

GENERATED_CANDIDATES=()
while IFS= read -r -d $'\0' candidate; do
  GENERATED_CANDIDATES+=("${candidate}")
done < <(find "alembic/versions" -maxdepth 1 -type f -name "${REVISION_ID}_*.py" -print0)

if [[ ${#GENERATED_CANDIDATES[@]} -eq 1 ]]; then
  mv "${GENERATED_CANDIDATES[0]}" "${TARGET_FILE}"
  echo "✅ Created migration ${TARGET_FILE}"
  exit 0
fi

echo "⚠️  Unable to locate generated Alembic file for revision ${REVISION_ID}." >&2
if [[ ${#GENERATED_CANDIDATES[@]} -gt 1 ]]; then
  printf 'Found candidates:\n' >&2
  printf '  - %s\n' "${GENERATED_CANDIDATES[@]}" >&2
fi
exit 1
