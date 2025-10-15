#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required" >&2
  exit 1
fi

docker compose -f "$SCRIPT_DIR/docker-compose.yml" up -d
if docker compose -f "$SCRIPT_DIR/docker-compose.yml" exec -T reverse-proxy nginx -s reload >/dev/null 2>&1; then
  echo "reverse proxy reloaded"
else
  docker compose -f "$SCRIPT_DIR/docker-compose.yml" restart reverse-proxy
fi
