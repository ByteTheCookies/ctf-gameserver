#!/usr/bin/env bash
set -euo pipefail

STATE_DIR="/etc/vulnbox"
SECRET_FILE="${STATE_DIR}/ccforms_jwt_secret"
ENV_FILE=".env"
MARKER_FILE="${STATE_DIR}/ccforms_bootstrapped"

mkdir -p "$STATE_DIR"

if ! docker compose version >/dev/null 2>&1; then
    echo "[ccforms] docker compose plugin is required but not available" >&2
    exit 1
fi

if [[ ! -f "$SECRET_FILE" ]]; then
    od -An -N16 -tx1 /dev/urandom | tr -d ' \n' >"$SECRET_FILE"
    chmod 600 "$SECRET_FILE"
fi
JWT_SECRET="$(cat "$SECRET_FILE")"

if [[ ! -f "$ENV_FILE" ]]; then
    printf 'JWT_SECRET=%s\n' "$JWT_SECRET" >"$ENV_FILE"
    chmod 600 "$ENV_FILE"
fi

if [[ ! -f "$MARKER_FILE" ]]; then
    docker compose up -d --build
    touch "$MARKER_FILE"
else
    docker compose up -d
fi
