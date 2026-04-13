#!/usr/bin/env python3
"""Generate per-team SSH root passwords for vulnbox VMs."""

from __future__ import annotations

import argparse
import json
import secrets
import string
from pathlib import Path


def parse_teams(config_path: Path) -> list[int]:
    raw = json.loads(config_path.read_text())
    start = int(raw["teams"]["start"])
    count = int(raw["teams"]["count"])
    if start < 0 or start > 254:
        raise ValueError("teams.start must be in [1, 254]")
    if count < 0 or start + count - 1 > 254:
        raise ValueError("teams.start + teams.count - 1 must be <= 254")
    return list(range(start, start + count))


def generate_password(length: int = 40) -> str:
    alphabet = string.hexdigits.lower()
    return "".join(secrets.choice(alphabet) for _ in range(length))


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    root_dir = script_dir.parent

    parser = argparse.ArgumentParser(
        description="Generate per-team VM SSH root passwords"
    )
    parser.add_argument(
        "--config", default=str(root_dir / "config" / "vpn_config.json")
    )
    parser.add_argument(
        "--json-output", default=str(root_dir / "output" / "vm_passwords.json")
    )
    parser.add_argument(
        "--env-output", default=str(root_dir / "output" / "vm_passwords.env")
    )
    args = parser.parse_args()

    teams = parse_teams(Path(args.config))

    password_map: dict[str, str] = {}
    for team in teams:
        password_map[f"{team:02d}"] = generate_password()

    out_json = Path(args.json_output)
    out_env = Path(args.env_output)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_env.parent.mkdir(parents=True, exist_ok=True)

    out_json.write_text(json.dumps(password_map, indent=2) + "\n")

    env_lines = []
    for team_id, password in password_map.items():
        env_lines.append(f"TEAM{team_id}_SSH_ROOT_PASSWORD={password}")
    out_env.write_text("\n".join(env_lines) + "\n")

    print(f"Generated {out_json}")
    print(f"Generated {out_env}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
