#!/usr/bin/env bash
set -euo pipefail

# Ensure local host routes for vulnbox VM IPs (10.60.<team>.1/32) point to Docker bridge.
# Useful when wg0 or other routes also claim 10.60.0.0/16.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_FILE="${ROOT_DIR}/config/vpn_config.json"
COMPOSE_FILE="${ROOT_DIR}/docker-compose.vms.yml"
NETWORK_NAME="vulnbox-vms_vulnbox_vm_net"

if [[ "${EUID}" -ne 0 ]]; then
  echo "[!] Run as root: sudo ./vulnbox/scripts/setup_local_vm_routes.sh" >&2
  exit 1
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "[!] Config not found: $CONFIG_FILE" >&2
  exit 1
fi
if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "[!] Compose file not found: $COMPOSE_FILE" >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "[!] docker not found" >&2
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "[!] python3 not found" >&2
  exit 1
fi

if ! docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
  echo "[!] Docker network $NETWORK_NAME not found. Start VM compose first:" >&2
  echo "    docker compose -f vulnbox/docker-compose.vms.yml up -d --build" >&2
  exit 1
fi

NET_ID="$(docker network inspect "$NETWORK_NAME" -f '{{.Id}}' | cut -c1-12)"
BR_IF="br-${NET_ID}"

if ! ip link show "$BR_IF" >/dev/null 2>&1; then
  echo "[!] Bridge interface not found: $BR_IF" >&2
  exit 1
fi

mapfile -t TEAM_IDS < <(
  python3 - "$CONFIG_FILE" <<'PY'
import json
import sys
from pathlib import Path
cfg = json.loads(Path(sys.argv[1]).read_text())
start = int(cfg["teams"]["start"])
count = int(cfg["teams"]["count"])
for t in range(start, start + count):
    print(t)
PY
)

echo "[+] Installing /32 local routes via ${BR_IF}"
for t in "${TEAM_IDS[@]}"; do
  ip route replace "10.60.${t}.1/32" dev "$BR_IF"
  echo "    10.60.${t}.1/32 -> ${BR_IF}"
done

echo "[+] Done"
