# Vulnbox Setup (Single VPS)

This setup runs Gameserver + WireGuard + team vulnbox VMs on the same VPS.

## Addressing

- `gameserver`: `10.10.0.1`
- `team VM`: `10.60.<team>.1`
- `player host`: `10.81.<team>.<host>`

## Files

- `config/vpn_config.json`: teams/hosts and VPN endpoint config
- `scripts/setup.sh`: generate VPN profiles + multi-team compose
- `scripts/setup_vps_routing.sh`: apply/check VPS routing+iptables rules
- `scripts/check_vm_connectivity.sh`: check `10.60.<team>.1` reachability

## From Scratch

1. Generate config and compose artifacts:

```bash
./vulnbox/scripts/setup.sh
```

2. Start vulnbox VMs (rootful Docker):

```bash
sudo DOCKER_HOST=unix:///var/run/docker.sock \
  docker compose -f vulnbox/docker-compose.vms.yml up -d --build
```

3. Install server WireGuard config:

```bash
sudo cp vulnbox/output/wireguard/gameserver/wg0.conf /etc/wireguard/wg0.conf
sudo wg-quick down wg0 2>/dev/null || true
sudo wg-quick up wg0
```

4. Apply VPS network rules:

```bash
sudo ./vulnbox/scripts/setup_vps_routing.sh --apply
```

5. Verify:

```bash
sudo ./vulnbox/scripts/setup_vps_routing.sh --check
./vulnbox/scripts/check_vm_connectivity.sh
```

## Notes

- `local_vulnboxes: true` in `vpn_config.json` keeps `10.60.x.1` local on VPS and avoids WG route conflicts.
- Host profiles are generated with `AllowedIPs = 10.10.0.1/32, 10.60.0.0/16, 10.81.0.0/16`.
- Distribute only per-team host profiles from `output/wireguard/teams/teamXX/hosts/`.
- Each VM starts `sshd` on port `22` with `root` password auth enabled.
- Root password is auto-generated at container start (unless `SSH_ROOT_PASSWORD` is set).
- Retrieve password with `sudo docker logs vulnbox-teamXX` or `sudo docker exec vulnbox-teamXX cat /etc/vulnbox/root_password`.
