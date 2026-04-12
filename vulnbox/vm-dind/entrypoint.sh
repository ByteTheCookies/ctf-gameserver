#!/usr/bin/env bash
set -euo pipefail

mkdir -p /var/run

# Start Docker daemon in the background (DinD)
dockerd --host=unix:///var/run/docker.sock --storage-driver=overlay2 >/var/log/dockerd.log 2>&1 &

for _ in $(seq 1 60); do
  if docker info >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! docker info >/dev/null 2>&1; then
  echo "dockerd failed to start. See /var/log/dockerd.log" >&2
  exit 1
fi

exec "$@"
