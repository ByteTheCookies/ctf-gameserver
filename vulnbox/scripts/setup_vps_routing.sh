#!/usr/bin/env bash
set -euo pipefail

# Configure host-level forwarding between WireGuard hosts and local vulnbox VM subnets.
# This is the single script to apply/check network rules on a single-VPS setup.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

VPN_IF="${VPN_IF:-wg0}"
VM_SUBNET="${VM_SUBNET:-10.60.0.0/16}"
SUPPORT_VM_SUBNET="${SUPPORT_VM_SUBNET:-10.30.0.0/16}"
HOST_SUBNET="${HOST_SUBNET:-10.81.0.0/16}"
NETWORK_NAME="${NETWORK_NAME:-vulnbox_vm_net}"
CONFIG_FILE="${CONFIG_FILE:-$ROOT_DIR/config/vpn_config.json}"
MODE="--apply"

usage() {
  cat <<'EOF'
Usage: setup_vps_routing.sh [--apply|--check] [--config FILE]

Applies or checks host routes and iptables rules for WireGuard clients to reach
local Docker vulnbox subnets. Support VM routing is enabled only when
teams.support_teams in vpn_config.json is greater than 0.

Environment overrides:
  VPN_IF              WireGuard interface (default: wg0)
  NETWORK_NAME        Docker network name (default: vulnbox_vm_net)
  VM_SUBNET           Team VM subnet (default: 10.60.0.0/16)
  SUPPORT_VM_SUBNET   Support VM subnet (default: 10.30.0.0/16)
  HOST_SUBNET         Player host subnet (default: 10.81.0.0/16)
  SUPPORT_TEAMS       Override support team count from config
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply|--check)
      MODE="$1"
      shift
      ;;
    -c|--config)
      if [[ $# -lt 2 ]]; then
        echo "[!] Missing value for $1" >&2
        usage >&2
        exit 1
      fi
      CONFIG_FILE="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[!] Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ "${EUID}" -ne 0 ]]; then
  echo "[!] Run as root: sudo ./vulnbox/scripts/setup_vps_routing.sh --apply" >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "[!] docker not found" >&2
  exit 1
fi
if ! command -v iptables >/dev/null 2>&1; then
  echo "[!] iptables not found" >&2
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "[!] python3 not found" >&2
  exit 1
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "[!] Config file not found: $CONFIG_FILE" >&2
  exit 1
fi

read_support_teams() {
  if [[ -n "${SUPPORT_TEAMS:-}" ]]; then
    echo "$SUPPORT_TEAMS"
    return 0
  fi

  python3 - "$CONFIG_FILE" <<'PY'
import json
import sys
from pathlib import Path

cfg = json.loads(Path(sys.argv[1]).read_text())
print(int(cfg.get("teams", {}).get("support_teams", 0)))
PY
}

SUPPORT_TEAMS="$(read_support_teams)"
if ! [[ "$SUPPORT_TEAMS" =~ ^[0-9]+$ ]]; then
  echo "[!] teams.support_teams must be a non-negative integer" >&2
  exit 1
fi

VM_SUBNETS=("$VM_SUBNET")
if (( SUPPORT_TEAMS > 0 )); then
  VM_SUBNETS+=("$SUPPORT_VM_SUBNET")
fi

ensure_rule() {
  local table="$1"
  local chain="$2"
  local insert_pos="$3"
  shift 3
  if ! iptables -t "$table" -C "$chain" "$@" 2>/dev/null; then
    iptables -t "$table" -I "$chain" "$insert_pos" "$@"
  fi
}

delete_conflicting_raw_drop_rules() {
  local bridge_if="$1"
  local vm_octets="60"
  local line
  if (( SUPPORT_TEAMS > 0 )); then
    vm_octets="30|60"
  fi
  mapfile -t line < <(iptables -t raw -S PREROUTING | grep -E -- "-A PREROUTING -d 10\\.(${vm_octets})\\.[0-9]+\\.1/32? ! -i ${bridge_if} -j DROP|-A PREROUTING -d 10\\.(${vm_octets})\\.[0-9]+\\.1 ! -i ${bridge_if} -j DROP" || true)
  for l in "${line[@]}"; do
    iptables -t raw ${l/-A /-D } || true
  done
}

detect_bridge() {
  local br
  br="$(docker network inspect "$NETWORK_NAME" -f '{{index .Options "com.docker.network.bridge.name"}}' 2>/dev/null || true)"
  if [[ -n "$br" && "$br" != "<no value>" ]]; then
    echo "$br"
    return 0
  fi
  local net_id
  net_id="$(docker network inspect "$NETWORK_NAME" -f '{{.Id}}' 2>/dev/null | cut -c1-12 || true)"
  if [[ -n "$net_id" ]]; then
    echo "br-${net_id}"
    return 0
  fi
  return 1
}

BR_IF="$(detect_bridge || true)"
if [[ -z "$BR_IF" ]]; then
  echo "[!] Cannot detect bridge for Docker network $NETWORK_NAME" >&2
  echo "    Start vulnboxes first: sudo docker compose -f vulnbox/docker-compose.vms.yml up -d --build" >&2
  exit 1
fi
if ! ip link show "$BR_IF" >/dev/null 2>&1; then
  echo "[!] Bridge interface not found: $BR_IF" >&2
  exit 1
fi

echo "[+] VPN IF: $VPN_IF"
echo "[+] BRIDGE IF: $BR_IF"
echo "[+] CONFIG: $CONFIG_FILE"
echo "[+] VM SUBNET: $VM_SUBNET"
echo "[+] SUPPORT TEAMS: $SUPPORT_TEAMS"
if (( SUPPORT_TEAMS > 0 )); then
  echo "[+] SUPPORT VM SUBNET: $SUPPORT_VM_SUBNET"
fi
echo "[+] HOST SUBNET: $HOST_SUBNET"

if [[ "$MODE" == "--check" ]]; then
  echo "[+] Check mode"
  for subnet in "${VM_SUBNETS[@]}"; do
    ip -4 route show "$subnet" || true
  done
  ip -4 route get 10.60.1.1 from 10.81.1.1 iif "$VPN_IF" || true
  if (( SUPPORT_TEAMS > 0 )); then
    ip -4 route get 10.30.1.1 from 10.81.1.1 iif "$VPN_IF" || true
  fi
  iptables -S FORWARD | grep -E "(${VPN_IF}|${BR_IF}|10\\.(30|60|81)\\.)" || true
  iptables -S DOCKER-USER | grep -E "(${VPN_IF}|${BR_IF}|10\\.(30|60|81)\\.)" || true
  iptables -t raw -S PREROUTING | grep -E "(10\\.(30|60)\\.|${VPN_IF}|${BR_IF})" || true
  iptables -t nat -S POSTROUTING | grep -E "(10\\.(30|60|81)\\.|${VPN_IF}|${BR_IF})" || true
  exit 0
fi

if [[ "$MODE" != "--apply" ]]; then
  echo "[!] Unknown mode: $MODE (use --apply or --check)" >&2
  exit 1
fi

echo "[+] Enabling forwarding + rp_filter settings"
sysctl -w net.ipv4.ip_forward=1 >/dev/null
sysctl -w net.ipv4.conf.all.rp_filter=0 >/dev/null
sysctl -w net.ipv4.conf.default.rp_filter=0 >/dev/null
sysctl -w "net.ipv4.conf.${VPN_IF}.rp_filter=0" >/dev/null || true
sysctl -w "net.ipv4.conf.${BR_IF}.rp_filter=0" >/dev/null || true

echo "[+] Ensuring routes for VM subnets use bridge"
for subnet in "${VM_SUBNETS[@]}"; do
  ip route replace "$subnet" dev "$BR_IF"
done

echo "[+] Removing conflicting raw/PREROUTING drops for VM addresses"
delete_conflicting_raw_drop_rules "$BR_IF"

echo "[+] Allowing WG ingress for VM subnets at raw/PREROUTING"
for subnet in "${VM_SUBNETS[@]}"; do
  ensure_rule raw PREROUTING 1 -i "$VPN_IF" -d "$subnet" -j ACCEPT
done

echo "[+] Installing FORWARD + DOCKER-USER rules"
for subnet in "${VM_SUBNETS[@]}"; do
  ensure_rule filter FORWARD 1 -i "$VPN_IF" -o "$BR_IF" -s "$HOST_SUBNET" -d "$subnet" -j ACCEPT
  ensure_rule filter FORWARD 1 -i "$BR_IF" -o "$VPN_IF" -s "$subnet" -d "$HOST_SUBNET" -j ACCEPT
  ensure_rule filter DOCKER-USER 1 -i "$VPN_IF" -o "$BR_IF" -d "$subnet" -j ACCEPT
  ensure_rule filter DOCKER-USER 1 -i "$BR_IF" -o "$VPN_IF" -s "$subnet" -j ACCEPT
done

echo "[+] Installing NAT rules"
for subnet in "${VM_SUBNETS[@]}"; do
  ensure_rule nat POSTROUTING 1 -s "$HOST_SUBNET" -d "$subnet" -o "$BR_IF" -j MASQUERADE
  ensure_rule nat POSTROUTING 1 -s "$subnet" -o "$VPN_IF" -j MASQUERADE
done

echo "[+] Done. Persist rules with your distro method (iptables-persistent/nftables)."
