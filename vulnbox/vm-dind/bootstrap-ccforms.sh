#!/usr/bin/env bash
set -euo pipefail

SERVICE_SRC="/root/CCForms"
STATE_DIR="/etc/vulnbox"
SECRET_FILE="${STATE_DIR}/ccforms_jwt_secret"
ENV_FILE="${SERVICE_SRC}/.env"
MARKER_FILE="${STATE_DIR}/ccforms_bootstrapped"

if [[ ! -d "$SERVICE_SRC" ]]; then
  echo "[vulnbox] CCForms source not found at $SERVICE_SRC, skipping bootstrap" >&2
  exit 0
fi

compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    echo "docker"
    return 0
  fi
  if command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose"
    return 0
  fi
  return 1
}

mkdir -p "$STATE_DIR"

if [[ ! -f "$SECRET_FILE" ]]; then
  od -An -N16 -tx1 /dev/urandom | tr -d ' \n' >"$SECRET_FILE"
  chmod 600 "$SECRET_FILE"
fi
JWT_SECRET="$(cat "$SECRET_FILE")"

if [[ ! -f "$ENV_FILE" ]]; then
  printf 'JWT_SECRET=%s\n' "$JWT_SECRET" >"$ENV_FILE"
  chmod 600 "$ENV_FILE"
fi

COMPOSE_BIN="$(compose_cmd || true)"
if [[ -z "$COMPOSE_BIN" ]]; then
  echo "[vulnbox] Docker Compose not available inside VM (need docker compose or docker-compose)." >&2
  exit 1
fi

run_compose() {
  if [[ "$COMPOSE_BIN" == "docker" ]]; then
    docker compose "$@"
  else
    docker-compose "$@"
  fi
}

cd "$SERVICE_SRC"
if [[ ! -f "$MARKER_FILE" ]]; then
  # First boot: build images and start all containers.
  run_compose up -d --build >/var/log/ccforms-compose.log 2>&1
  touch "$MARKER_FILE"
else
  # Subsequent boots: ensure containers are up.
  run_compose up -d >/var/log/ccforms-compose.log 2>&1
fi

echo "[vulnbox] CCForms bootstrap completed"
