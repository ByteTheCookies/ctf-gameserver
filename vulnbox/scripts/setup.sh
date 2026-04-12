#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v wg >/dev/null 2>&1; then
  echo "[!] wireguard-tools is required (wg not found)." >&2
  exit 1
fi

python3 "$ROOT_DIR/scripts/generate_vpn_profiles.py" \
  --config "$ROOT_DIR/config/vpn_config.json" \
  --output-dir "$ROOT_DIR/output/wireguard"

python3 "$ROOT_DIR/scripts/generate_vm_compose.py" \
  --config "$ROOT_DIR/config/vpn_config.json" \
  --output "$ROOT_DIR/docker-compose.vms.yml"

echo "[+] Generated VPN profiles under $ROOT_DIR/output/wireguard"
echo "[+] Generated multi-team compose at $ROOT_DIR/docker-compose.vms.yml"
echo "[+] Next: copy per-team host configs to TEAM_DOWNLOADS_ROOT/<team>/"
