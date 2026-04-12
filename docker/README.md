# Docker Compose Infrastructure

This repository now includes a compose-based baseline deployment for CTF Gameserver.

## Included Services

- `db`: PostgreSQL 16
- `migrate`: one-shot Django DB initialization (`migrate --run-syncdb`)
- `collectstatic`: one-shot static collection for nginx
- `web`: Django web app via Gunicorn (internal)
- `nginx`: public frontend serving `/static`, `/uploads`, and proxying Django
- `controller`: `ctf-controller`
- `submission`: `ctf-submission` on port `6666`
- `checker_web` (optional profile): checker master for service slug `web`
- `checker_pwn` (optional profile): checker master for service slug `pwn`
- `vpnstatus` (optional profile): `ctf-vpnstatus`

## First Startup

1. Review and adjust `docker/env/common.env`:
   - `CTF_FLAGSECRET`
   - `DJANGO_SECRET_KEY`
   - `CTF_TEAMREGEX`
2. (Optional) set Postgres credentials in shell or a `.env` file:
   - `POSTGRES_DB`
   - `POSTGRES_USER`
   - `POSTGRES_PASSWORD`
3. Start core services:

   ```bash
   docker compose up -d --build
   ```

4. Create an admin user:

   ```bash
   docker compose exec web python -m django createsuperuser
   ```

5. Open:
   - Web admin: `http://localhost:8000/admin`
   - Submission TCP: `localhost:6666`

## Admin Setup (Competition + Teams)

After first login in `/admin`, configure in this order:

1. `SCORING -> Game controls`
   - Create/edit the game control row.
   - Set competition name, start/end time, tick duration, valid ticks, flag prefix.
2. `SCORING -> Services`
   - Add each service.
   - Service slug must match checker env `CTF_SERVICE`.
3. `REGISTRATION -> Teams`
   - Add teams manually, or enable registration workflow.
4. Optional content pages:
   - `FLATPAGES -> Categories`
   - `FLATPAGES -> Flatpages`
   - For homepage `/`, create a flatpage with empty title.

## Optional Profiles

- Checkers (two sample services):

  ```bash
  docker compose --profile checker up -d checker_web checker_pwn
  ```

  Configure:
  - `docker/env/checker-web.env`
  - `docker/env/checker-pwn.env`

- VPN Status:

  ```bash
  docker compose --profile vpnstatus up -d vpnstatus
  ```

  Configure `docker/env/vpnstatus.env` for your network checks.

## Running More Checkers

You can scale checker masters independently per service:

```bash
docker compose up -d --scale checker_web=2 --scale checker_pwn=3 checker_web checker_pwn
```

Important rule:

- `CTF_CHECKERCOUNT` in each checker env file must equal the total running instances for that specific service.
- Example:
  - `checker_web=2` -> set `CTF_CHECKERCOUNT=2` in `checker-web.env`
  - `checker_pwn=3` -> set `CTF_CHECKERCOUNT=3` in `checker-pwn.env`

To add a new service checker:

1. Copy one checker service block in `docker-compose.yml`.
2. Point it to a new env file (for example `docker/env/checker-crypto.env`).
3. Set `CTF_SERVICE=<service-slug>` and checker script path in that env file.
4. Add matching service slug in admin under `SCORING -> Services`.

## Notes

- The web settings module is `docker/web-settings/prod_settings.py`.
- Public HTTP entrypoint is `nginx` on host port `8000`.
- Uploaded files and team downloads are persisted via compose volumes.
- `migrate` runs once; if schema changes, run it again:

  ```bash
  docker compose run --rm migrate
  ```
