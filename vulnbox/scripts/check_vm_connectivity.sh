#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_FILE="${ROOT_DIR}/config/vpn_config.json"
PING_COUNT=1
PING_TIMEOUT=1
TCP_PORT=""
HTTP_PATH=""
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: check_vm_connectivity.sh [options]

Checks team VM connectivity for IP pattern 10.60.<team>.1.
Teams are read from vulnbox/config/vpn_config.json by default.

Options:
  -c, --config FILE         Config JSON path
  -p, --ping-count N        Ping count per host (default: 1)
  -t, --ping-timeout N      Ping timeout seconds (default: 1)
      --tcp-port PORT       Also test TCP connect to PORT using nc
      --http-path PATH      Also test HTTP GET on http://<ip><PATH> using curl
      --dry-run             Print targets without testing
  -h, --help                Show this help

Examples:
  ./vulnbox/scripts/check_vm_connectivity.sh
  ./vulnbox/scripts/check_vm_connectivity.sh --tcp-port 8080
  ./vulnbox/scripts/check_vm_connectivity.sh --http-path /healthz
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -c|--config)
      CONFIG_FILE="$2"
      shift 2
      ;;
    -p|--ping-count)
      PING_COUNT="$2"
      shift 2
      ;;
    -t|--ping-timeout)
      PING_TIMEOUT="$2"
      shift 2
      ;;
    --tcp-port)
      TCP_PORT="$2"
      shift 2
      ;;
    --http-path)
      HTTP_PATH="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "Config file not found: $CONFIG_FILE" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found" >&2
  exit 1
fi
if ! command -v ping >/dev/null 2>&1; then
  echo "ping not found" >&2
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

if [[ ${#TEAM_IDS[@]} -eq 0 ]]; then
  echo "No teams found in config" >&2
  exit 1
fi

if [[ -n "$TCP_PORT" ]] && ! command -v nc >/dev/null 2>&1; then
  echo "nc not found, cannot run --tcp-port checks" >&2
  exit 1
fi
if [[ -n "$HTTP_PATH" ]] && ! command -v curl >/dev/null 2>&1; then
  echo "curl not found, cannot run --http-path checks" >&2
  exit 1
fi

printf "%-8s %-13s %-6s %-6s %-6s\n" "TEAM" "IP" "PING" "TCP" "HTTP"
printf "%-8s %-13s %-6s %-6s %-6s\n" "--------" "-------------" "------" "------" "------"

ok=0
fail=0

for team in "${TEAM_IDS[@]}"; do
  ip="10.60.${team}.1"

  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf "%-8s %-13s %-6s %-6s %-6s\n" "$team" "$ip" "-" "-" "-"
    continue
  fi

  ping_res="FAIL"
  tcp_res="N/A"
  http_res="N/A"

  if ping -c "$PING_COUNT" -W "$PING_TIMEOUT" "$ip" >/dev/null 2>&1; then
    ping_res="OK"
  fi

  if [[ -n "$TCP_PORT" ]]; then
    if nc -z -w 2 "$ip" "$TCP_PORT" >/dev/null 2>&1; then
      tcp_res="OK"
    else
      tcp_res="FAIL"
    fi
  fi

  if [[ -n "$HTTP_PATH" ]]; then
    if curl -fsS --max-time 3 "http://${ip}${HTTP_PATH}" >/dev/null 2>&1; then
      http_res="OK"
    else
      http_res="FAIL"
    fi
  fi

  if [[ "$ping_res" == "OK" ]] && [[ "$tcp_res" != "FAIL" ]] && [[ "$http_res" != "FAIL" ]]; then
    ((ok+=1))
  else
    ((fail+=1))
  fi

  printf "%-8s %-13s %-6s %-6s %-6s\n" "$team" "$ip" "$ping_res" "$tcp_res" "$http_res"
done

if [[ "$DRY_RUN" -eq 1 ]]; then
  printf "\nDry-run complete.\n"
  exit 0
fi

printf "\nSummary: OK=%s FAIL=%s TOTAL=%s\n" "$ok" "$fail" "${#TEAM_IDS[@]}"
if [[ "$fail" -gt 0 ]]; then
  exit 2
fi
