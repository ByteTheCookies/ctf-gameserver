#!/usr/bin/env python3
"""Generate a multi-team docker compose for Debian DinD vulnboxes.

Each team gets one privileged DinD container with static IP 10.60.<team>.1.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def parse_teams(config_path: Path) -> list[int]:
    raw = json.loads(config_path.read_text())
    start = int(raw["teams"]["start"])
    count = int(raw["teams"]["count"])

    if start < 1 or start > 254:
        raise ValueError("teams.start must be in [1, 254]")
    if count < 1 or start + count - 1 > 254:
        raise ValueError("teams.start + teams.count - 1 must be <= 254")

    return list(range(start, start + count))


def load_passwords(path: Path) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"Passwords file not found: {path}")
    raw = json.loads(path.read_text())
    return {str(k): str(v) for k, v in raw.items()}


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    root_dir = script_dir.parent

    parser = argparse.ArgumentParser(description="Generate docker-compose file for all team vulnboxes")
    parser.add_argument(
        "--config",
        default=str(root_dir / "config" / "vpn_config.json"),
        help="Path to vpn/team config",
    )
    parser.add_argument(
        "--output",
        default=str(root_dir / "docker-compose.vms.yml"),
        help="Output compose file",
    )
    parser.add_argument(
        "--passwords-json",
        default=str(root_dir / "output" / "vm_passwords.json"),
        help="Path to JSON map of team -> SSH root password",
    )
    args = parser.parse_args()

    teams = parse_teams(Path(args.config))
    passwords = load_passwords(Path(args.passwords_json))
    missing = [f"{team:02d}" for team in teams if f"{team:02d}" not in passwords]
    if missing:
        raise ValueError(f"Missing passwords for team IDs: {', '.join(missing)}")

    out = Path(args.output).resolve()
    context_rel = os.path.relpath(root_dir.resolve(), out.parent)

    lines: list[str] = []
    lines.append("name: vulnbox-vms")
    lines.append("")
    lines.append("services:")

    for team in teams:
        team_s = f"{team:02d}"
        lines.extend(
            [
                f"  vulnbox-team{team_s}:",
                "    build:",
                f"      context: {context_rel}",
                "      dockerfile: vm-dind/Dockerfile",
                "    image: vulnbox-dind:local",
                f"    container_name: vulnbox-team{team_s}",
                f"    hostname: vm-team{team_s}",
                "    privileged: true",
                "    restart: unless-stopped",
                "    environment:",
                f"      TEAM_ID: \"{team}\"",
                "      DOCKER_TLS_CERTDIR: \"\"",
                f"      SSH_ROOT_PASSWORD: \"{passwords[team_s]}\"",
                "    volumes:",
                f"      - dind-data-team{team_s}:/var/lib/docker",
                "    networks:",
                "      vulnbox_vm_net:",
                f"        ipv4_address: 10.60.{team}.1",
            ]
        )

    lines.append("")
    lines.append("volumes:")
    for team in teams:
        lines.append(f"  dind-data-team{team:02d}:")

    lines.extend(
        [
            "",
            "networks:",
            "  vulnbox_vm_net:",
            "    name: vulnbox_vm_net",
            "    driver: bridge",
            "    ipam:",
            "      config:",
            "        - subnet: 10.60.0.0/16",
        ]
    )

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")

    print(f"Generated {out} for teams: {', '.join(str(t) for t in teams)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
