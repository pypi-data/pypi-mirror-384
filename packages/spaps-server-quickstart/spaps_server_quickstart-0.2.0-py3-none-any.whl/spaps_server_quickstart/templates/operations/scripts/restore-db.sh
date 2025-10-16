#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: scripts/restore-db.sh <backup.sql.gz>" >&2
  exit 1
fi

BACKUP_FILE="$1"
COMPOSE_CMD="${COMPOSE_CMD:-docker compose}"
DB_SERVICE="${DB_SERVICE:-db}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-service}"

if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "Backup file '$BACKUP_FILE' not found" >&2
  exit 1
fi

echo "⚠️  Restoring ${BACKUP_FILE} into service '${DB_SERVICE}' (database ${POSTGRES_DB})"
echo "    Ensure you are targeting the correct environment!"

if [[ "${DRY_RUN:-0}" == "1" ]]; then
  echo "DRY RUN: gunzip -c ${BACKUP_FILE} | ${COMPOSE_CMD} exec -T ${DB_SERVICE} psql -U ${POSTGRES_USER} ${POSTGRES_DB}"
  exit 0
fi

gunzip -c "${BACKUP_FILE}" | ${COMPOSE_CMD} exec -T "${DB_SERVICE}" psql -U "${POSTGRES_USER}" "${POSTGRES_DB}"

echo "✅ Restore completed"
