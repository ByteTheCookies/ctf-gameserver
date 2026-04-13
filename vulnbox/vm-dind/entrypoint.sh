#!/usr/bin/env bash
set -euo pipefail

mkdir -p /var/run
mkdir -p /run/sshd /etc/vulnbox

# Keep VM networking permissive for CTF service exposure.
iptables -P INPUT ACCEPT || true
iptables -P FORWARD ACCEPT || true
iptables -P OUTPUT ACCEPT || true

generate_password() {
  tr -dc 'A-Za-z0-9@#%+=' </dev/urandom | head -c 20
}

ROOT_PASSWORD="${SSH_ROOT_PASSWORD:-}"
if [[ ! -f /etc/vulnbox/root_password_initialized ]]; then
  if [[ -z "${ROOT_PASSWORD}" ]]; then
    ROOT_PASSWORD="$(generate_password)"
  fi

  echo "root:${ROOT_PASSWORD}" | chpasswd
  echo "${ROOT_PASSWORD}" >/etc/vulnbox/root_password
  chmod 600 /etc/vulnbox/root_password
  touch /etc/vulnbox/root_password_initialized
  echo "[vulnbox] root password initialized (first boot)"
else
  echo "[vulnbox] root password already initialized"
fi

if [[ ! -f /etc/ssh/ssh_host_rsa_key ]]; then
  ssh-keygen -A
fi

/usr/sbin/sshd
echo "[vulnbox] SSH active on 0.0.0.0:22"

# Start Docker daemon in the background (DinD)
rm -f /var/run/docker.pid /var/run/docker.sock
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

# Require compose plugin and bootstrap CCForms through its native deploy script.
if ! docker compose version >/dev/null 2>&1; then
  echo "[vulnbox] docker compose plugin missing inside VM" >&2
  exit 1
fi


if ! cd /root/CCForms; /root/CCForms/deploy.sh >/var/log/ccforms-compose.log 2>&1; then
  echo "[vulnbox] CCForms deploy failed. See /var/log/ccforms-compose.log" >&2
fi

exec "$@"
