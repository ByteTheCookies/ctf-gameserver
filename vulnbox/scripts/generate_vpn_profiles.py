#!/usr/bin/env python3
"""Generate WireGuard configs for gameserver, team vulnboxes and team member hosts.

Addressing model:
- gameserver: 10.10.0.1
- team VM:    10.60.<team>.1
- host:       10.81.<team>.<host>
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class Host:
    host_id: int


@dataclass
class Team:
    team_id: int
    hosts: List[Host]


@dataclass
class Peer:
    name: str
    address: str
    private_key: str
    public_key: str


def run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{proc.stderr.strip()}")
    return proc.stdout.strip()


def wg_keypair() -> tuple[str, str]:
    private_key = run(["wg", "genkey"])
    proc = subprocess.run(
        ["wg", "pubkey"],
        input=private_key,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: wg pubkey\\n{proc.stderr.strip()}")
    return private_key, proc.stdout.strip()


def ensure_wg() -> None:
    if not shutil_which("wg"):
        raise RuntimeError(
            "wg binary not found. Install wireguard-tools before running this script."
        )


def shutil_which(binary: str) -> str | None:
    for path in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(path) / binary
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def parse_config(path: Path) -> tuple[str, int, int, int, int, bool]:
    raw = json.loads(path.read_text())
    endpoint = raw.get("endpoint", "vpn.example.ctf:51820")
    port = int(raw.get("listen_port", 51820))

    start_team = int(raw["teams"]["start"])
    count_team = int(raw["teams"]["count"])
    hosts_per_team = int(raw["teams"]["hosts_per_team"])
    local_vulnboxes = bool(raw.get("local_vulnboxes", True))

    if start_team < 1 or start_team > 254:
        raise ValueError("teams.start must be in [0, 254]")
    if count_team < 1 or (start_team + count_team - 1) > 254:
        raise ValueError("teams.start + teams.count - 1 must be <= 254")
    if hosts_per_team < 1 or hosts_per_team > 254:
        raise ValueError("teams.hosts_per_team must be in [1, 254]")

    return endpoint, port, start_team, count_team, hosts_per_team, local_vulnboxes


def make_teams(start_team: int, count_team: int, hosts_per_team: int) -> List[Team]:
    return [
        Team(team_id=t, hosts=[Host(host_id=h) for h in range(1, hosts_per_team + 1)])
        for t in range(start_team, start_team + count_team)
    ]


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def render_peer_block(
    public_key: str, allowed_ips: list[str], endpoint: str | None = None
) -> str:
    lines = [
        "[Peer]",
        f"PublicKey = {public_key}",
        f"AllowedIPs = {', '.join(allowed_ips)}",
    ]
    if endpoint:
        lines.append(f"Endpoint = {endpoint}")
    lines.append("PersistentKeepalive = 25")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate WireGuard VPN profiles for CTF teams"
    )
    parser.add_argument(
        "--config",
        default="vulnbox/config/vpn_config.json",
        help="Path to JSON config file",
    )
    parser.add_argument(
        "--output-dir",
        default="vulnbox/output/wireguard",
        help="Output directory for generated files",
    )
    args = parser.parse_args()

    ensure_wg()

    endpoint, listen_port, start_team, count_team, hosts_per_team, local_vulnboxes = (
        parse_config(Path(args.config))
    )
    teams = make_teams(start_team, count_team, hosts_per_team)

    out = Path(args.output_dir)

    server_priv, server_pub = wg_keypair()
    server = Peer(
        name="gameserver",
        address="10.10.0.1/32",
        private_key=server_priv,
        public_key=server_pub,
    )

    vm_peers: list[Peer] = []
    host_peers: list[Peer] = []

    for team in teams:
        vm_priv, vm_pub = wg_keypair()
        vm_peers.append(
            Peer(
                name=f"team{team.team_id:02d}_vm",
                address=f"10.60.{team.team_id}.1/32",
                private_key=vm_priv,
                public_key=vm_pub,
            )
        )
        for host in team.hosts:
            hp, hup = wg_keypair()
            host_peers.append(
                Peer(
                    name=f"team{team.team_id:02d}_host{host.host_id:02d}",
                    address=f"10.81.{team.team_id}.{host.host_id}/32",
                    private_key=hp,
                    public_key=hup,
                )
            )

    server_peers = host_peers if local_vulnboxes else (vm_peers + host_peers)
    server_conf = [
        "[Interface]",
        f"Address = {server.address}",
        f"ListenPort = {listen_port}",
        f"PrivateKey = {server.private_key}",
        "",
    ]
    for p in server_peers:
        server_conf.append(
            render_peer_block(p.public_key, [p.address.split("/")[0] + "/32"])
        )
        server_conf.append("")

    write_text(out / "gameserver" / "wg0.conf", "\n".join(server_conf).rstrip() + "\n")

    server_endpoint = endpoint

    for vm in vm_peers:
        team_num = int(vm.name.replace("team", "").split("_")[0])
        cfg = [
            "[Interface]",
            f"Address = {vm.address}",
            f"PrivateKey = {vm.private_key}",
            "",
            render_peer_block(
                server.public_key,
                ["10.10.0.1/32", f"10.60.{team_num}.1/32", f"10.81.{team_num}.0/24"],
                endpoint=server_endpoint,
            ),
            "",
        ]
        write_text(
            out / "teams" / f"team{team_num:02d}" / "vm" / "wg0.conf", "\n".join(cfg)
        )

    for host in host_peers:
        parts = host.name.replace("team", "").split("_")
        team_num = int(parts[0])
        host_num = int(parts[1].replace("host", ""))
        cfg = [
            "[Interface]",
            f"Address = {host.address}",
            f"PrivateKey = {host.private_key}",
            "",
            render_peer_block(
                server.public_key,
                ["10.10.0.1/32", "10.60.0.0/16", "10.81.0.0/16"],
                endpoint=server_endpoint,
            ),
            "",
        ]
        write_text(
            out
            / "teams"
            / f"team{team_num:02d}"
            / "hosts"
            / f"host{host_num:02d}.conf",
            "\n".join(cfg),
        )

    summary = {
        "endpoint": endpoint,
        "listen_port": listen_port,
        "local_vulnboxes": local_vulnboxes,
        "teams": [t.team_id for t in teams],
        "hosts_per_team": hosts_per_team,
        "gameserver_ip": "10.10.0.1",
        "vm_ip_pattern": "10.60.<team>.1",
        "host_ip_pattern": "10.81.<team>.<host>",
    }
    write_text(out / "SUMMARY.json", json.dumps(summary, indent=2) + "\n")

    print(f"Generated WireGuard profiles in {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
