#!/usr/bin/env bash
set -euo pipefail

# Usage: scripts/backup-db.sh [output_dir]
# Requires docker compose access to the stack (local or production).

OUTPUT_DIR="${1:-backups}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
COMPOSE_CMD="${COMPOSE_CMD:-docker compose}"
DB_SERVICE="${DB_SERVICE:-db}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-service}"
PROJECT_SLUG="${PROJECT_SLUG:-service}"
BACKUP_STORAGE_URL="${BACKUP_STORAGE_URL:-}"
BACKUP_STORAGE_ENDPOINT="${BACKUP_STORAGE_ENDPOINT:-${AWS_ENDPOINT_URL:-}}"
AWS_CLI_BIN="${AWS_CLI_BIN:-aws}"
BACKUP_STORAGE_PREFIX="${BACKUP_STORAGE_PREFIX:-${PROJECT_SLUG}/}"

normalize_destination() {
  local base="${1}"
  local prefix="${2}"
  local filename="$(basename "${BACKUP_PATH}")"

  if [[ -n "${prefix}" ]]; then
    prefix="${prefix#/}"
    prefix="${prefix%/}/"
  fi

  if [[ "${base}" != */ ]]; then
    base="${base}/"
  fi

  printf '%s%s%s' "${base}" "${prefix}" "${filename}"
}

upload_backup() {
  local destination="$1"
  local target
  target="$(normalize_destination "${destination}" "${BACKUP_STORAGE_PREFIX}")"

  local -a cmd=("${AWS_CLI_BIN}" "s3" "cp" "${BACKUP_PATH}" "${target}")
  if [[ -n "${BACKUP_STORAGE_ENDPOINT}" ]]; then
    cmd+=("--endpoint-url" "${BACKUP_STORAGE_ENDPOINT}")
  fi

  if [[ "${DRY_RUN:-0}" == "1" ]]; then
    echo "DRY RUN: ${cmd[*]}"
  else
    "${cmd[@]}"
  fi
}

mkdir -p "${OUTPUT_DIR}"
BACKUP_PATH="${OUTPUT_DIR}/${PROJECT_SLUG}-${TIMESTAMP}.sql.gz"

echo "📦 Dumping ${POSTGRES_DB} from service '${DB_SERVICE}'..."
if [[ "${DRY_RUN:-0}" == "1" ]]; then
  echo "DRY RUN: ${COMPOSE_CMD} exec -T ${DB_SERVICE} pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} | gzip > ${BACKUP_PATH}"
  echo "" | gzip > "${BACKUP_PATH}"  # create empty artifact for validation
else
  ${COMPOSE_CMD} exec -T "${DB_SERVICE}" pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" | gzip > "${BACKUP_PATH}"
fi

echo "✅ Backup written to ${BACKUP_PATH}"

if [[ -n "${BACKUP_STORAGE_URL}" ]]; then
  echo "☁️  Uploading backup to ${BACKUP_STORAGE_URL}"
  upload_backup "${BACKUP_STORAGE_URL}"
fi
