#!/usr/bin/env bash
set -euo pipefail

# Fix routing/firewall path: external WireGuard host -> VPS wg0 -> local Docker VM subnet 10.60.0.0/16.
# Safe to run multiple times (idempotent).

VPN_IF="${VPN_IF:-wg0}"
VM_SUBNET="${VM_SUBNET:-10.60.0.0/16}"
NETWORK_NAME="${NETWORK_NAME:-vulnbox-vms_vulnbox_vm_net}"
MODE="${1:---apply}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "[!] Run as root: sudo ./vulnbox/scripts/fix_external_host_to_vm.sh --apply" >&2
  exit 1
fi

if ! command -v ip >/dev/null 2>&1; then
  echo "[!] ip command not found" >&2
  exit 1
fi
if ! command -v iptables >/dev/null 2>&1; then
  echo "[!] iptables not found" >&2
  exit 1
fi
if ! command -v docker >/dev/null 2>&1; then
  echo "[!] docker not found" >&2
  exit 1
fi

ensure_rule() {
  local table="$1"
  shift
  if ! iptables -t "$table" -C "$@" 2>/dev/null; then
    iptables -t "$table" -I "$@"
  fi
}

detect_bridge_from_route() {
  ip -4 route show "$VM_SUBNET" 2>/dev/null | awk '
    {
      for (i=1; i<=NF; i++) {
        if ($i=="dev" && (i+1)<=NF) { print $(i+1); exit }
      }
    }'
}

detect_bridge_from_docker() {
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

BR_IF="$(detect_bridge_from_route || true)"
if [[ -z "$BR_IF" ]]; then
  BR_IF="$(detect_bridge_from_docker || true)"
fi

if [[ -z "$BR_IF" ]]; then
  echo "[!] Could not detect Docker bridge for ${VM_SUBNET}." >&2
  echo "    Make sure VM compose is up, or set NETWORK_NAME=<network>." >&2
  exit 1
fi

if ! ip link show "$BR_IF" >/dev/null 2>&1; then
  echo "[!] Bridge interface not found: $BR_IF" >&2
  exit 1
fi

echo "[+] VPN IF: ${VPN_IF}"
echo "[+] VM SUBNET: ${VM_SUBNET}"
echo "[+] BRIDGE IF: ${BR_IF}"

if [[ "$MODE" == "--check" ]]; then
  echo "[+] Check mode"
  ip -4 route show "$VM_SUBNET" || true
  iptables -S FORWARD | grep -E "(${VPN_IF}|${BR_IF}|${VM_SUBNET})" || true
  iptables -S DOCKER-USER | grep -E "(${VPN_IF}|${BR_IF}|${VM_SUBNET})" || true
  exit 0
fi

if [[ "$MODE" != "--apply" ]]; then
  echo "[!] Unknown mode: $MODE (use --apply or --check)" >&2
  exit 1
fi

echo "[+] Enabling kernel forwarding and disabling rp_filter on path interfaces"
sysctl -w net.ipv4.ip_forward=1 >/dev/null
sysctl -w net.ipv4.conf.all.rp_filter=0 >/dev/null
sysctl -w net.ipv4.conf.default.rp_filter=0 >/dev/null
sysctl -w "net.ipv4.conf.${VPN_IF}.rp_filter=0" >/dev/null || true
sysctl -w "net.ipv4.conf.${BR_IF}.rp_filter=0" >/dev/null || true

echo "[+] Installing FORWARD and DOCKER-USER rules"
ensure_rule filter FORWARD 1 -i "$VPN_IF" -o "$BR_IF" -d "$VM_SUBNET" -j ACCEPT
ensure_rule filter FORWARD 1 -i "$BR_IF" -o "$VPN_IF" -s "$VM_SUBNET" -j ACCEPT
ensure_rule filter DOCKER-USER 1 -i "$VPN_IF" -o "$BR_IF" -d "$VM_SUBNET" -j ACCEPT
ensure_rule filter DOCKER-USER 1 -i "$BR_IF" -o "$VPN_IF" -s "$VM_SUBNET" -j ACCEPT

echo "[+] Done"
echo "[+] Verify from client: ping 10.60.1.1"
echo "[+] Debug: sudo tcpdump -ni ${VPN_IF} icmp"
