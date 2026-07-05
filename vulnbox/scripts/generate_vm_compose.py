#!/usr/bin/env python3
"""Generate a multi-team docker compose for Debian DinD vulnboxes.

Each team gets one privileged DinD container with static IP 10.60.<team>.1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


def parse_config(config_path: Path) -> tuple[list[int], int]:
    raw = json.loads(config_path.read_text())
    start = int(raw["teams"]["start"])
    count = int(raw["teams"]["count"])
    support_count = int(raw["teams"].get("support_teams", 0))

    if start < 1 or start > 254:
        raise ValueError("teams.start must be in [1, 254]")
    if count < 1 or start + count - 1 > 254:
        raise ValueError("teams.start + teams.count - 1 must be <= 254")
    if support_count < 0 or support_count > 254:
        raise ValueError("teams.support_teams must be in [0, 254]")

    return list(range(start, start + count)), support_count


def load_passwords(path: Path) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"Passwords file not found: {path}")
    raw = json.loads(path.read_text())
    return {str(k): str(v) for k, v in raw.items()}


def support_password(passwords: dict[str, str], support_index: int) -> str:
    """Return support VM password, accepting explicit keys when available.

    generate_vm_passwords.py currently creates only team passwords. Deriving a
    stable support password here keeps the existing setup flow working while
    still allowing explicit support passwords to override it.
    """
    candidate_keys = [
        f"support{support_index:02d}",
        f"support{support_index}",
    ]
    if support_index == 1:
        candidate_keys.append("support")

    for key in candidate_keys:
        if key in passwords:
            return passwords[key]

    seed = "|".join(f"{key}:{passwords[key]}" for key in sorted(passwords))
    return hashlib.sha256(f"support:{support_index}:{seed}".encode()).hexdigest()[:40]


def support_suffix(support_count: int, support_index: int) -> str:
    return "" if support_count == 1 else f"{support_index:02d}"


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    root_dir = script_dir.parent

    parser = argparse.ArgumentParser(
        description="Generate docker-compose file for all team vulnboxes"
    )
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

    teams, support_count = parse_config(Path(args.config))
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
                f'      TEAM_ID: "{team}"',
                '      DOCKER_TLS_CERTDIR: ""',
                f'      SSH_ROOT_PASSWORD: "{passwords[team_s]}"',
                "    volumes:",
                f"      - dind-data-team{team_s}:/var/lib/docker",
                "    networks:",
                "      vulnbox_vm_net:",
                f"        ipv4_address: 10.60.{team}.1",
            ]
        )

    for support_index in range(1, support_count + 1):
        suffix = support_suffix(support_count, support_index)
        lines.extend(
            [
                f"  vulnbox-support{suffix}:",
                "    build:",
                f"      context: {context_rel}",
                "      dockerfile: vm-dind/Dockerfile.support",
                "    image: vulnbox-dind-support:local",
                f"    container_name: vulnbox-support{suffix}",
                f"    hostname: vm-support{suffix}",
                "    privileged: true",
                "    restart: unless-stopped",
                "    environment:",
                f'      TEAM_ID: "{support_index}"',
                '      DOCKER_TLS_CERTDIR: ""',
                f'      SSH_ROOT_PASSWORD: "{support_password(passwords, support_index)}"',
                "    volumes:",
                f"      - dind-data-support{suffix}:/var/lib/docker",
                "    networks:",
                "      vulnbox_vm_net:",
                f"        ipv4_address: 10.30.{support_index}.1",
            ]
        )

    lines.append("")
    lines.append("volumes:")
    for team in teams:
        lines.append(f"  dind-data-team{team:02d}:")
    for support_index in range(1, support_count + 1):
        suffix = support_suffix(support_count, support_index)
        lines.append(f"  dind-data-support{suffix}:")

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
    if support_count:
        lines.append("        - subnet: 10.30.0.0/16")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")

    print(
        f"Generated {out} for teams: {', '.join(str(t) for t in teams)}"
        f" and support teams: {support_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
