# Vulnbox Setup (Single VPS)

This setup runs Gameserver + WireGuard + team vulnbox VMs on the same VPS.

## Addressing

- `gameserver`: `10.10.0.1`
- `team VM`: `10.60.<team>.1`
- `player host`: `10.81.<team>.<host>`

## Files

- `config/vpn_config.json`: teams/hosts and VPN endpoint config
- `scripts/setup.sh`: generate VPN profiles + multi-team compose
- `scripts/generate_vm_passwords.py`: generate per-team VM root passwords
- `scripts/setup_vps_routing.sh`: apply/check VPS routing+iptables rules
- `scripts/check_vm_connectivity.sh`: check `10.60.<team>.1` reachability

## From Scratch

1. Generate config and compose artifacts:

```bash
./vulnbox/scripts/setup.sh
```

This also generates:

- `vulnbox/output/vm_passwords.json`
- `vulnbox/output/vm_passwords.env`

and injects per-team `SSH_ROOT_PASSWORD` into `docker-compose.vms.yml`.

2. Start vulnbox VMs (rootful Docker):

```bash
sudo DOCKER_HOST=unix:///var/run/docker.sock \
  docker compose -f vulnbox/docker-compose.vms.yml up -d --build
```

If you need a real reset from zero (remove persistent DinD data volumes too):

```bash
sudo ./vulnbox/scripts/recreate_vms_from_zero.sh
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
- Treat `output/vm_passwords.json` and `output/vm_passwords.env` as secrets.
- Each VM starts `sshd` on port `22` with `root` password auth enabled.
- VM data is persistent by default because each team uses a named volume (`dind-data-teamXX`).
- Root password is initialized only on first boot (unless `SSH_ROOT_PASSWORD` is set on first boot).
- Password is stored in `/etc/vulnbox/root_password` inside VM and not printed in logs.
- Retrieve it with `sudo docker exec vulnbox-teamXX cat /etc/vulnbox/root_password`.
- CCForms is bootstrapped automatically inside each VM via DinD:
  - source path in VM: `/root/CCForms`
  - started by default on VM boot using `/root/CCForms/deploy.sh`
  - requires `docker compose` plugin inside VM
  - backend: `10.60.<team>.1:3001`
  - frontend: `10.60.<team>.1:3000`
