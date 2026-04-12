#!/usr/bin/env bash
set -euo pipefail

# Configure host-level forwarding between VPN and vulnbox subnet on same VPS.
# Run as root.

VPN_IF="${VPN_IF:-wg0}"
VM_SUBNET="${VM_SUBNET:-10.60.0.0/16}"
HOST_SUBNET="${HOST_SUBNET:-10.81.0.0/16}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "[!] Run as root: sudo VPN_IF=wg0 ./vulnbox/scripts/setup_vps_routing.sh" >&2
  exit 1
fi

echo "[+] Enabling IPv4 forwarding"
sysctl -w net.ipv4.ip_forward=1 >/dev/null

ensure_iptables_rule() {
  local table="$1"
  shift
  if ! iptables -t "$table" -C "$@" 2>/dev/null; then
    iptables -t "$table" -A "$@"
  fi
}

echo "[+] Installing FORWARD rules for ${VPN_IF} <-> ${VM_SUBNET}/${HOST_SUBNET}"
ensure_iptables_rule filter FORWARD -i "$VPN_IF" -d "$VM_SUBNET" -j ACCEPT
ensure_iptables_rule filter FORWARD -o "$VPN_IF" -s "$VM_SUBNET" -j ACCEPT
ensure_iptables_rule filter FORWARD -i "$VPN_IF" -d "$HOST_SUBNET" -j ACCEPT
ensure_iptables_rule filter FORWARD -o "$VPN_IF" -s "$HOST_SUBNET" -j ACCEPT

echo "[+] Installing MASQUERADE for outbound from ${VM_SUBNET} and ${HOST_SUBNET} via ${VPN_IF}"
ensure_iptables_rule nat POSTROUTING -s "$VM_SUBNET" -o "$VPN_IF" -j MASQUERADE
ensure_iptables_rule nat POSTROUTING -s "$HOST_SUBNET" -o "$VPN_IF" -j MASQUERADE

echo "[+] Done. Persist rules with your distro method (iptables-persistent/nftables)."
