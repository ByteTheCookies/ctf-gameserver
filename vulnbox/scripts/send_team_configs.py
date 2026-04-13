#!/usr/bin/env python3
"""Package and send per-team vulnbox configs via Resend."""

from __future__ import annotations

import argparse
import base64
import json
import os
import tempfile
import zipfile
from pathlib import Path

import resend
from dotenv import load_dotenv


def parse_config(path: Path) -> tuple[list[int], dict[int, list[str]], str]:
    raw = json.loads(path.read_text())
    start = int(raw["teams"]["start"])
    count = int(raw["teams"]["count"])
    endpoint = str(raw.get("endpoint", "vpn.example.ctf:51820"))

    if start < 1 or start > 254:
        raise ValueError("teams.start must be in [1, 254]")
    if count < 1 or start + count - 1 > 254:
        raise ValueError("teams.start + teams.count - 1 must be <= 254")

    team_ids = list(range(start, start + count))
    contacts_raw = raw.get("team_contacts", {})
    contacts: dict[int, list[str]] = {}
    for team in team_ids:
        values = contacts_raw.get(f"{team:02d}", contacts_raw.get(str(team), []))
        if not isinstance(values, list) or not all(
            isinstance(v, str) and v.strip() for v in values
        ):
            raise ValueError(
                f"team_contacts[{team:02d}] must be a list of non-empty email strings"
            )
        contacts[team] = values

    return team_ids, contacts, endpoint


def load_passwords(path: Path) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"Passwords file not found: {path}")
    raw = json.loads(path.read_text())
    return {str(k): str(v) for k, v in raw.items()}


def require_file(path: Path, label: str) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")
    return path


def build_team_zip(
    team_id: int,
    endpoint: str,
    team_dir: Path,
    password: str | None,
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"team{team_id:02d}-configs.zip"

    host_dir = require_file(
        team_dir / "hosts", f"Host config directory for team {team_id:02d}"
    )

    contents = [
        f"Team {team_id:02d} configuration bundle",
        "",
        "Contents:",
        "- hosts/: WireGuard configs for player hosts",
        "- vm_root_password.txt: VM root password",
        "",
        f"VPN endpoint: {endpoint}",
        f"VM IP: 10.60.{team_id}.1",
        "Host IP pattern: 10.81.<team>.<host>",
    ]
    if password is None:
        contents[5] = "- vm_root_password.txt: not included"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("README.txt", "\n".join(contents) + "\n")
        archive.write(vm_conf, arcname="vm/wg0.conf")
        for host_conf in sorted(host_dir.glob("*.conf")):
            archive.write(host_conf, arcname=f"hosts/{host_conf.name}")
        if password is not None:
            archive.writestr("vm_root_password.txt", password + "\n")

    return zip_path


def send_email(
    api_key: str,
    sender: str,
    recipients: list[str],
    subject: str,
    html: str,
    attachment_path: Path,
) -> None:
    resend.api_key = api_key
    payload = {
        "from": sender,
        "to": recipients,
        "subject": subject,
        "html": html,
        "attachments": [
            {
                "filename": attachment_path.name,
                "content": base64.b64encode(attachment_path.read_bytes()).decode(
                    "ascii"
                ),
            }
        ],
    }
    resend.Emails.send(payload)


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    root_dir = script_dir.parent
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Zip and send per-team WireGuard and VM configuration bundles via Resend"
    )
    parser.add_argument(
        "--config",
        default=str(root_dir / "config" / "vpn_config.json"),
        help="Path to vulnbox JSON config",
    )
    parser.add_argument(
        "--wireguard-dir",
        default=str(root_dir / "output" / "wireguard" / "teams"),
        help="Path to generated team WireGuard configs",
    )
    parser.add_argument(
        "--passwords-json",
        default=str(root_dir / "output" / "vm_passwords.json"),
        help="Path to generated team VM passwords JSON",
    )
    parser.add_argument(
        "--zip-output-dir",
        default="",
        help="Optional directory where generated ZIPs should be kept",
    )
    parser.add_argument(
        "--resend-api-key",
        default=os.environ.get("RESEND_API_KEY", ""),
        help="Resend API key, defaults to RESEND_API_KEY",
    )
    parser.add_argument(
        "--from",
        dest="sender",
        default=os.environ.get("RESEND_FROM", ""),
        help="Sender email, defaults to RESEND_FROM",
    )
    parser.add_argument(
        "--subject-prefix",
        default="[CTF A/D Vulnbox]",
        help="Prefix used in the email subject",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only generate ZIPs and print what would be sent",
    )
    args = parser.parse_args()

    team_ids, contacts, endpoint = parse_config(Path(args.config))
    passwords = load_passwords(Path(args.passwords_json))
    wireguard_dir = Path(args.wireguard_dir)

    if not args.dry_run:
        if not args.resend_api_key:
            raise ValueError(
                "Missing Resend API key. Use --resend-api-key or RESEND_API_KEY."
            )
        if not args.sender:
            raise ValueError("Missing sender address. Use --from or RESEND_FROM.")

    keep_zips = bool(args.zip_output_dir)
    if keep_zips:
        zip_root = Path(args.zip_output_dir)
        zip_root.mkdir(parents=True, exist_ok=True)
        temp_cm = None
    else:
        temp_cm = tempfile.TemporaryDirectory(prefix="team-config-zips-")
        zip_root = Path(temp_cm.name)

    try:
        for team_id in team_ids:
            recipients = contacts.get(team_id, [])
            if not recipients:
                print(f"No recipient emails configured for team {team_id:02d}")
                continue

            team_dir = require_file(
                wireguard_dir / f"team{team_id:02d}",
                f"WireGuard directory for team {team_id:02d}",
            )
            password = passwords.get(f"{team_id:02d}")
            zip_path = build_team_zip(team_id, endpoint, team_dir, password, zip_root)

            subject = f"{args.subject_prefix} Team {team_id:02d} configuration bundle"
            html = (
                f"<p>Attached you can find the configuration bundle for team <strong>{team_id:02d}</strong>.</p>"
                f"<p>Game Server: <code>10.10.0.1</code><br>"
                f"<p>Scoreboard: <code>http://10.10.0.1:8011/competition/scoreboard/</code><br>"
                f"<p>Flag ids: <code>http://10.10.0.1:8011/competition/scoreboard/</code><br>"
                f"VM IP: <code>10.60.{team_id}.1</code></p>"
                f"<p>IP format for host is: <code>10.81.{team_id}.host </code><br>"
            )

            if args.dry_run:
                print(
                    f"[DRY-RUN] team {team_id:02d}: {zip_path} -> {', '.join(recipients)}"
                )
                continue

            send_email(
                args.resend_api_key, args.sender, recipients, subject, html, zip_path
            )
            print(
                f"[OK] Sent team {team_id:02d} config bundle to {', '.join(recipients)}"
            )
    finally:
        if temp_cm is not None:
            temp_cm.cleanup()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
