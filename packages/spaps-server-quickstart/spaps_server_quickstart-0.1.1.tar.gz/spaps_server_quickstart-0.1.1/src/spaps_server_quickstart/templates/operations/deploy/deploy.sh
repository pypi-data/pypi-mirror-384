#!/usr/bin/env bash
# Shared GHCR deployment helper copied by services adopting quickstart

set -euo pipefail

SERVER_IP=${1:-${SERVER_IP:-"your-server-ip"}}
SERVER_USER=${2:-${SERVER_USER:-"root"}}
DEPLOY_PATH=${DEPLOY_PATH:-/opt/quickstart}
REGISTRY_IMAGE=${REGISTRY_IMAGE:-ghcr.io/example/service}
IMAGE_TAG=${IMAGE_TAG:-latest}

GHCR_USER=${GHCR_DEPLOY_USER:-${GHCR_USER:-}}
GHCR_TOKEN=${GHCR_DEPLOY_TOKEN:-${GHCR_TOKEN:-}}
SSH_OPTIONS=${SSH_OPTIONS:-${SSH_OPTS:-}}

SSH_COMMAND=(ssh)
if [[ -n "$SSH_OPTIONS" ]]; then
  # shellcheck disable=SC2206
  SSH_COMMAND+=( $SSH_OPTIONS )
fi

if [[ -z "$SERVER_IP" ]]; then
  echo "SERVER_IP not provided" >&2
  exit 1
fi

if [[ -z "$GHCR_USER" || -z "$GHCR_TOKEN" ]]; then
  echo "GHCR credentials must be provided via GHCR_DEPLOY_USER / GHCR_DEPLOY_TOKEN" >&2
  exit 1
fi

printf '🚀 Deploying %s:%s to %s@%s\n' "$REGISTRY_IMAGE" "$IMAGE_TAG" "$SERVER_USER" "$SERVER_IP"

printf -v REGISTRY_IMAGE_ESC '%q' "$REGISTRY_IMAGE"
printf -v IMAGE_TAG_ESC '%q' "$IMAGE_TAG"
printf -v DEPLOY_PATH_ESC '%q' "$DEPLOY_PATH"
printf -v GHCR_USER_ESC '%q' "$GHCR_USER"
printf -v GHCR_TOKEN_ESC '%q' "$GHCR_TOKEN"

"${SSH_COMMAND[@]}" "$SERVER_USER@$SERVER_IP" \
  "REGISTRY_IMAGE=$REGISTRY_IMAGE_ESC IMAGE_TAG=$IMAGE_TAG_ESC DEPLOY_PATH=$DEPLOY_PATH_ESC GHCR_DEPLOY_USER=$GHCR_USER_ESC GHCR_DEPLOY_TOKEN=$GHCR_TOKEN_ESC bash -s" <<'REMOTE'
  set -euo pipefail

  IMAGE="${REGISTRY_IMAGE}:${IMAGE_TAG}"

  if ! command -v docker >/dev/null 2>&1; then
    echo "Docker is required on the target host" >&2
    exit 1
  fi

  echo "🔐 Authenticating with ghcr.io"
  echo "${GHCR_DEPLOY_TOKEN}" | docker login ghcr.io -u "${GHCR_DEPLOY_USER}" --password-stdin >/dev/null

  mkdir -p "${DEPLOY_PATH}"
  cd "${DEPLOY_PATH}"

  echo "📥 Pulling ${IMAGE}"
  docker pull "${IMAGE}"

  echo "🛑 Stopping previous container"
  docker stop quickstart-api >/dev/null 2>&1 || true
  docker rm quickstart-api >/dev/null 2>&1 || true

  if [[ ! -f .env.production ]]; then
    echo ".env.production is required in ${DEPLOY_PATH}" >&2
    exit 1
  fi

  echo "🚢 Starting container"
  docker run -d \
    --name quickstart-api \
    --restart unless-stopped \
    -p 8000:8000 \
    --env-file .env.production \
    -e NODE_ENV=production \
    -e PORT=8000 \
    "${IMAGE}"

  docker image prune -f >/dev/null

  if [[ -d deploy/reverse-proxy ]]; then
    echo "🔄 Refreshing reverse proxy"
    (cd deploy/reverse-proxy && ./up.sh)
  fi

  echo "⏳ Waiting for health endpoint"
  for _ in {1..15}; do
    if curl -fsS http://localhost:8000/health >/dev/null; then
      echo "✅ Deployment successful"
      exit 0
    fi
    sleep 2
  done

  echo "❌ Service failed health check" >&2
  docker logs quickstart-api --tail 200 || true
  exit 1
REMOTE
