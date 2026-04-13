#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

KEEP_SCHEDULE=0
RESTART_RUNTIME=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep-schedule)
      KEEP_SCHEDULE=1
      shift
      ;;
    --no-restart)
      RESTART_RUNTIME=0
      shift
      ;;
    *)
      echo "[!] Unknown option: $1" >&2
      echo "Usage: $0 [--keep-schedule] [--no-restart]" >&2
      exit 1
      ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  echo "[!] docker not found" >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "[!] docker compose not available" >&2
  exit 1
fi

mapfile -t all_services < <(docker compose config --services)
runtime_services=()
for service in "${all_services[@]}"; do
  case "$service" in
    controller|submission|vpnstatus|checker_*)
      runtime_services+=("$service")
      ;;
  esac
done

if [[ ${#runtime_services[@]} -gt 0 ]]; then
  echo "[+] Stopping runtime services: ${runtime_services[*]}"
  docker compose stop "${runtime_services[@]}"
fi

gamecontrol_update="competition_name = competition_name, current_tick = -1, cancel_checks = false"
if [[ "$KEEP_SCHEDULE" -eq 0 ]]; then
  gamecontrol_update="$gamecontrol_update, services_public = NULL, start = NULL, \"end\" = NULL"
fi

read -r -d '' SQL <<EOF || true
BEGIN;
TRUNCATE TABLE
  scoring_capture,
  scoring_scoreboard,
  scoring_statuscheck,
  scoring_checkerstate,
  scoring_flag
RESTART IDENTITY CASCADE;
UPDATE scoring_gamecontrol
SET $gamecontrol_update;
COMMIT;
EOF

echo "[+] Resetting game state in database"
docker compose exec -T db sh -lc '
  psql \
    -v ON_ERROR_STOP=1 \
    -U "${POSTGRES_USER:-ctf_gameserver}" \
    -d "${POSTGRES_DB:-ctf_gameserver}" \
    <<'"'"'SQL'"'"'
'"$SQL"'
SQL
'

if [[ "$RESTART_RUNTIME" -eq 1 && ${#runtime_services[@]} -gt 0 ]]; then
  echo "[+] Restarting runtime services: ${runtime_services[*]}"
  docker compose up -d "${runtime_services[@]}"
fi

echo "[+] Game state reset complete"
if [[ "$KEEP_SCHEDULE" -eq 0 ]]; then
  echo "[+] Schedule cleared: set new GameControl start/end/services_public before restarting the game"
fi
