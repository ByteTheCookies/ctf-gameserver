#!/usr/bin/env bash
set -euo pipefail

SERVICE_SRC="/opt/services/CCForms"
STATE_DIR="/etc/vulnbox"
SECRET_FILE="${STATE_DIR}/ccforms_jwt_secret"
MARKER_FILE="${STATE_DIR}/ccforms_bootstrapped"

if [[ ! -d "$SERVICE_SRC" ]]; then
  echo "[vulnbox] CCForms source not found at $SERVICE_SRC, skipping bootstrap" >&2
  exit 0
fi

mkdir -p "$STATE_DIR"

if [[ ! -f "$SECRET_FILE" ]]; then
  od -An -N16 -tx1 /dev/urandom | tr -d ' \n' >"$SECRET_FILE"
  chmod 600 "$SECRET_FILE"
fi
JWT_SECRET="$(cat "$SECRET_FILE")"

if ! docker network inspect ccforms-net >/dev/null 2>&1; then
  docker network create ccforms-net >/dev/null
fi

if [[ ! -f "$MARKER_FILE" ]]; then
  # Build images once on first boot (can be forced by deleting marker in the VM).
  docker build -t ccforms-db:local "$SERVICE_SRC/db" >/var/log/ccforms-build-db.log 2>&1
  docker build -t ccforms-api:local "$SERVICE_SRC/api" >/var/log/ccforms-build-api.log 2>&1
  docker build -t ccforms-frontend:local "$SERVICE_SRC/form" >/var/log/ccforms-build-frontend.log 2>&1
fi

if ! docker ps -a --format '{{.Names}}' | grep -qx 'ccforms-db'; then
  docker run -d \
    --name ccforms-db \
    --restart unless-stopped \
    --network ccforms-net \
    -e POSTGRES_PASSWORD=password \
    -v ccforms-db-data:/var/lib/postgresql/data \
    ccforms-db:local >/dev/null
fi

if ! docker ps -a --format '{{.Names}}' | grep -qx 'ccforms-backend'; then
  docker run -d \
    --name ccforms-backend \
    --restart unless-stopped \
    --network ccforms-net \
    -e JWT_SECRET="$JWT_SECRET" \
    -v ccforms-api-forms:/app/forms \
    -p 3001:3001 \
    ccforms-api:local >/dev/null
fi

if ! docker ps -a --format '{{.Names}}' | grep -qx 'ccforms-frontend'; then
  docker run -d \
    --name ccforms-frontend \
    --restart unless-stopped \
    --network ccforms-net \
    -p 3000:3000 \
    ccforms-frontend:local >/dev/null
fi

# Ensure containers are running after restart/recreate events.
docker start ccforms-db ccforms-backend ccforms-frontend >/dev/null 2>&1 || true

touch "$MARKER_FILE"
echo "[vulnbox] CCForms bootstrap completed"
