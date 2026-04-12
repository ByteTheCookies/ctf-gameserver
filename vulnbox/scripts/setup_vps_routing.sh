#!/usr/bin/env bash
set -euo pipefail

# Configure host-level forwarding between WireGuard hosts and local vulnbox VM subnet.
# This is the single script to apply/check network rules on a single-VPS setup.

VPN_IF="${VPN_IF:-wg0}"
VM_SUBNET="${VM_SUBNET:-10.60.0.0/16}"
HOST_SUBNET="${HOST_SUBNET:-10.81.0.0/16}"
NETWORK_NAME="${NETWORK_NAME:-vulnbox-vms_vulnbox_vm_net}"
MODE="${1:---apply}"

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

ensure_rule() {
  local table="$1"
  shift
  if ! iptables -t "$table" -C "$@" 2>/dev/null; then
    iptables -t "$table" -I "$@"
  fi
}

delete_conflicting_raw_drop_rules() {
  local bridge_if="$1"
  local line
  mapfile -t line < <(iptables -t raw -S PREROUTING | grep -E -- "-A PREROUTING -d 10\\.60\\.[0-9]+\\.1/32? ! -i ${bridge_if} -j DROP|-A PREROUTING -d 10\\.60\\.[0-9]+\\.1 ! -i ${bridge_if} -j DROP" || true)
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
echo "[+] VM SUBNET: $VM_SUBNET"
echo "[+] HOST SUBNET: $HOST_SUBNET"

if [[ "$MODE" == "--check" ]]; then
  echo "[+] Check mode"
  ip -4 route show "$VM_SUBNET" || true
  ip -4 route get 10.60.1.1 from 10.81.1.1 iif "$VPN_IF" || true
  iptables -S FORWARD | grep -E "(${VPN_IF}|${BR_IF}|10\\.60\\.|10\\.81\\.)" || true
  iptables -S DOCKER-USER | grep -E "(${VPN_IF}|${BR_IF}|10\\.60\\.|10\\.81\\.)" || true
  iptables -t raw -S PREROUTING | grep -E "(10\\.60\\.|${VPN_IF}|${BR_IF})" || true
  iptables -t nat -S POSTROUTING | grep -E "(10\\.60\\.|10\\.81\\.|${VPN_IF}|${BR_IF})" || true
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

echo "[+] Ensuring route for VM subnet uses bridge"
ip route replace "$VM_SUBNET" dev "$BR_IF"

echo "[+] Removing conflicting raw/PREROUTING drops for 10.60.x.1"
delete_conflicting_raw_drop_rules "$BR_IF"

echo "[+] Allowing WG ingress for VM subnet at raw/PREROUTING"
ensure_rule raw PREROUTING 1 -i "$VPN_IF" -d "$VM_SUBNET" -j ACCEPT

echo "[+] Installing FORWARD + DOCKER-USER rules"
ensure_rule filter FORWARD 1 -i "$VPN_IF" -o "$BR_IF" -s "$HOST_SUBNET" -d "$VM_SUBNET" -j ACCEPT
ensure_rule filter FORWARD 1 -i "$BR_IF" -o "$VPN_IF" -s "$VM_SUBNET" -d "$HOST_SUBNET" -j ACCEPT
ensure_rule filter DOCKER-USER 1 -i "$VPN_IF" -o "$BR_IF" -d "$VM_SUBNET" -j ACCEPT
ensure_rule filter DOCKER-USER 1 -i "$BR_IF" -o "$VPN_IF" -s "$VM_SUBNET" -j ACCEPT

echo "[+] Installing NAT rules"
ensure_rule nat POSTROUTING 1 -s "$HOST_SUBNET" -d "$VM_SUBNET" -o "$BR_IF" -j MASQUERADE
ensure_rule nat POSTROUTING 1 -s "$VM_SUBNET" -o "$VPN_IF" -j MASQUERADE

echo "[+] Done. Persist rules with your distro method (iptables-persistent/nftables)."
