# Vulnbox Setup

This folder contains a standalone setup for team vulnboxes and VPN profile generation.

## Addressing plan

- `gameserver`: `10.10.0.1`
- `team VM`: `10.60.<team>.1`
- `single host`: `10.81.<team>.<host>`

## 1) Generate VPN profiles (WireGuard)

Prerequisites:

- `python3`
- `wg` from `wireguard-tools`

Configure teams and members in `config/vpn_config.json`.
Set `local_vulnboxes: true` when team VMs are local Docker containers on the same VPS as gameserver/VPN.

Run:

```bash
./scripts/setup.sh
```

Generated files:

- `output/wireguard/gameserver/wg0.conf`
- `output/wireguard/teams/teamXX/vm/wg0.conf`
- `output/wireguard/teams/teamXX/hosts/hostYY.conf`
- `docker-compose.vms.yml` (multi-team DinD compose generated from the same team range)

With `local_vulnboxes: true`, `gameserver/wg0.conf` does not include VM peers (`10.60.<team>.1/32`),
so `wg-quick` will not conflict with local Docker routes.

## 2) Start a single Debian DinD vulnbox VM (manual)

The compose stack builds a Debian-based container with Docker daemon inside (DinD).

```bash
TEAM_ID=7 docker compose -f vulnbox/docker-compose.yml up -d --build
```

Result:

- VM container gets IP `10.60.7.1` on the compose network.
- You can run internal service containers inside it via Docker-in-Docker.

Example:

```bash
docker exec -it vulnbox-team7 docker run -d --name internal-nginx -p 8080:80 nginx:alpine
```

## 3) Start all team vulnboxes on one VPS (recommended for your case)

The generated compose file creates one DinD container per team (`10.60.<team>.1`).

```bash
docker compose -f vulnbox/docker-compose.vms.yml up -d --build
```

Check:

```bash
docker compose -f vulnbox/docker-compose.vms.yml ps
```

## 4) Enable routing/forwarding on the VPS

If the same VPS hosts gameserver + VPN + vulnboxes, enable forwarding rules:

```bash
sudo VPN_IF=wg0 ./vulnbox/scripts/setup_vps_routing.sh
```

This script enables:

- IPv4 forwarding (`net.ipv4.ip_forward=1`)
- `FORWARD` rules between `wg0` and `10.60.0.0/16` + `10.81.0.0/16`
- NAT (`MASQUERADE`) for those subnets out of `wg0`

## 5) Run connectivity checks from VPS/gameserver side

Use the helper script to test each `10.60.<team>.1`:

```bash
./vulnbox/scripts/check_vm_connectivity.sh
```

Optional checks:

```bash
./vulnbox/scripts/check_vm_connectivity.sh --tcp-port 8080
./vulnbox/scripts/check_vm_connectivity.sh --http-path /healthz
```

Dry-run target list:

```bash
./vulnbox/scripts/check_vm_connectivity.sh --dry-run
```

If all VM pings fail but `gameserver` is reachable, you likely have route overlap on `10.60.0.0/16`
(e.g. `wg0` wins over Docker bridge). Install local `/32` routes for each VM IP:

```bash
sudo ./vulnbox/scripts/setup_local_vm_routes.sh
```

If more than one Docker network uses `10.60.0.0/16`, force the right one:

```bash
docker network ls
NETWORK_NAME=<your_vulnbox_network> sudo ./vulnbox/scripts/setup_local_vm_routes.sh
```

Then re-run:

```bash
./vulnbox/scripts/check_vm_connectivity.sh
```

## Notes

- DinD requires `privileged: true`.
- The generated VPN profiles are key material; handle and distribute them securely.
- This setup is isolated from the main project compose stack.
- Persist firewall rules after reboot (`iptables-persistent` or equivalent).

## 6) One-shot fix for external host -> VM ping

Run on VPS:

```bash
sudo ./vulnbox/scripts/fix_external_host_to_vm.sh --apply
```

Check mode:

```bash
sudo ./vulnbox/scripts/fix_external_host_to_vm.sh --check
```
