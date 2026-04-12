#!/usr/bin/env bash
set -euo pipefail

# Ensure local host routes for vulnbox VM IPs (10.60.<team>.1/32) point to Docker bridge.
# Useful when wg0 or other routes also claim 10.60.0.0/16.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_FILE="${ROOT_DIR}/config/vpn_config.json"
COMPOSE_FILE="${ROOT_DIR}/docker-compose.vms.yml"
NETWORK_NAME="${NETWORK_NAME:-}"
VM_SUBNET="${VM_SUBNET:-10.60.0.0/16}"

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

find_network_for_subnet() {
    local wanted_subnet="$1"
    local net
    while IFS= read -r net; do
        [[ -z "$net" ]] && continue
        if docker network inspect "$net" -f '{{range .IPAM.Config}}{{println .Subnet}}{{end}}' 2>/dev/null | grep -Fxq "$wanted_subnet"; then
            echo "$net"
            return 0
        fi
    done < <(docker network ls --format '{{.Name}}')
    return 1
}

find_bridge_from_kernel_route() {
  local wanted_subnet="$1"
  ip -4 route show "$wanted_subnet" 2>/dev/null | awk '
    {
      for (i = 1; i <= NF; i++) {
        if ($i == "dev" && (i + 1) <= NF) {
          print $(i + 1)
          exit
        }
      }
    }
  '
}

if [[ -z "$NETWORK_NAME" ]]; then
  NETWORK_NAME="$(find_network_for_subnet "$VM_SUBNET" || true)"
fi

if [[ -z "$NETWORK_NAME" ]]; then
    echo "[!] Could not find a Docker network with subnet $VM_SUBNET." >&2
    echo "    Start VM compose first: docker compose -f vulnbox/docker-compose.vms.yml up -d --build" >&2
    echo "    Or pass the network explicitly: NETWORK_NAME=<name> sudo ./vulnbox/scripts/setup_local_vm_routes.sh" >&2
    exit 1
fi

if ! docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
    echo "[!] Docker network not found: $NETWORK_NAME" >&2
    exit 1
fi

BR_IF="$(docker network inspect "$NETWORK_NAME" -f '{{index .Options "com.docker.network.bridge.name"}}' 2>/dev/null || true)"
if [[ -z "$BR_IF" || "$BR_IF" == "<no value>" ]]; then
  BR_IF="$(find_bridge_from_kernel_route "$VM_SUBNET" || true)"
fi
if [[ -z "$BR_IF" || "$BR_IF" == "<no value>" ]]; then
  NET_ID="$(docker network inspect "$NETWORK_NAME" -f '{{.Id}}' | cut -c1-12)"
  BR_IF="br-${NET_ID}"
fi

if ! ip link show "$BR_IF" >/dev/null 2>&1; then
    echo "[!] Bridge interface not found: $BR_IF (network: $NETWORK_NAME)" >&2
    echo "    Available bridge interfaces:" >&2
    ip -o link show | awk -F': ' '{print $2}' | grep '^br-' || true
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

echo "[+] Using Docker network: ${NETWORK_NAME}"
echo "[+] Installing /32 local routes via ${BR_IF}"
for t in "${TEAM_IDS[@]}"; do
    ip route replace "10.60.${t}.1/32" dev "$BR_IF"
    echo "    10.60.${t}.1/32 -> ${BR_IF}"
done

echo "[+] Done"
