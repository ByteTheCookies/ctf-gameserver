#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$ROOT_DIR/docker-compose.vms.yml}"

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "[!] Compose file not found: $COMPOSE_FILE" >&2
  exit 1
fi

echo "[+] Using compose file: $COMPOSE_FILE"
echo "[+] Stopping and removing containers/networks/volumes..."
docker compose -f "$COMPOSE_FILE" down -v --remove-orphans

echo "[+] Removing old VM image (if present)..."
docker image rm -f vulnbox-dind:local >/dev/null 2>&1 || true

echo "[+] Rebuilding VM images from scratch (no cache)..."
docker compose -f "$COMPOSE_FILE" build --no-cache

echo "[+] Starting VMs..."
docker compose -f "$COMPOSE_FILE" up -d

echo "[+] Done."
