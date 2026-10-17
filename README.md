# eventstream

A production-ready event and tournament streaming control plane for the
Raspberry Pi. eventstream drives OBS, manages tournaments, brackets, teams,
players, sponsors, charity, ad breaks, alerts, chat, and live feeds - all from
one headless Python application accessed over SSH and a web browser.

Designed for a solo operator running public charity and esports streams.

---

## Status

Phase 0 complete: foundation, config, database, migrations, encryption,
logging, audit, and health checks.

Phase 1 in progress: web server, sessions, auth, roles, permissions.

See [Roadmap](#roadmap) for the full plan.

---

## Purpose

eventstream exists to make it possible for one person on a Raspberry Pi 3 to:

- Plan and run a public tournament or charity event.
- Register attendees, participants, sponsors, volunteers, vendors, and moderators.
- Manage brackets across single elim, double elim, round robin, Swiss, and groups.
- Collect and validate match results, screenshots, and disputes.
- Drive OBS scenes, sources, filters, transforms, and media over WebSocket.
- Start and stop streams and recordings on the streaming PC.
- Trigger clips on Twitch and YouTube via their APIs.
- Serve sponsor rotations, charity totals, and ad breaks.
- Provide moderator, player, team, sponsor, and spectator dashboards.
- Expose per-widget browser source routes for OBS overlays.
- Keep data encrypted at rest and auditable end to end.

eventstream does **not** transcode video, does **not** fan out to tens of
thousands of viewers, and does **not** replace Twitch or YouTube. Public video
stays on the platforms. The Pi runs the control plane.

---

## Design principles

- **Object-oriented first.** Every subsystem is a class with a clear contract.
- **Minimal dependencies.** Small, well-maintained packages only. No frameworks
  that pull 40 MB to do a 40-line job. Helpers are written in-house when
  reasonable.
- **Raw Python where it matters.** `sqlite3`, `asyncio`, `hmac`, `hashlib`,
  `json`, `logging` are used directly.
- **Clone-safe.** Every directory and `__init__.py` is created by
  `install_init.py`, which runs on first clone and on every application boot.
- **Encrypted at rest.** Secrets, PII, and event data are encrypted with
  AES-GCM. Master key lives in an environment variable.
- **Auditable.** Every privileged action is written to `audit_log` and to a
  dedicated audit log file.
- **Role-based with a permission matrix.** Roles are coarse; permissions are
  fine. Both are enforced on every privileged route and every OBS command.
- **Per-event isolation.** Each event has its own encrypted JSON store, its own
  branding, its own widgets, and its own role assignments.
- **Platform-agnostic integrations.** Twitch, YouTube, Google Forms, PayPal,
  Stripe, and Ko-fi are providers behind stable interfaces. Any one can be
  disabled per event.
- **Graceful degradation.** If Twitch is down, the event still runs with manual
  controls. If OAuth fails, local email/password still works.

---

## Architecture

Raspberry Pi 3 
(headless) 

Browser > aiohttp > Router > Handlers
(SSH tunnel) 
    Auth + Sessions
    Roles + Perms
    Domain services
    Widgets
    OBS bridge

SQLite (WAL)
Encrypted JSON per event
Audit log
Health + metrics

OBS WebSocket Twitch API YouTube API
(LAN laptop) (clips, (clips, live,
chat) chat, stats)

The Pi is the control plane. OBS runs on a separate laptop on the same LAN.
Twitch and YouTube own the public video.

---

## Repository layout

```text
eventstream/
config/ env loader, settings, constants
core/ app container, router, request/response, middleware
db/ sqlite connection, migrations, models, repositories
json_store/ encrypted per-event JSON + public API export
auth/ passwords, sessions, 2FA, OAuth providers
domain/ events, tournaments, matches, stats, sponsors,
charity, adbreak, alerts
integrations/ obs, twitch, youtube, google_forms, smtp, uptime
live/ feed, WebRTC, embed, fanout, latency, recording
chat/ hub, moderation, spectator, twitch/youtube bridges
widgets/ registry, templates, config panels, renderer
web/ routes, templates, static, i18n, theme
security/ crypto, keyring, rotation, headers, xss, gdpr
storage/ uploads, screenshots, clips, backups
ops/ logging, audit, metrics, alerts, tasks
scripts/ init_db, create_admin, rotate_keys, export/import, backup
tests/ unit, integration, e2e, fixtures

deploy/ nginx.conf, systemd, cloudflare tunnel, backup cron
docs/ architecture, permissions, routes, obs naming, runbook
var/ runtime data (untracked): db, logs, uploads, backups
install_init.py creates the directory tree, idempotent
setup.sh clone + venv + install + init on a fresh Pi
main.py entrypoint
pyproject.toml
README.md
```

Every Python package has an `__init__.py`. `install_init.py` creates them if
missing so a fresh clone always boots.

---

## Requirements

- Raspberry Pi 3 or newer, headless Raspberry Pi OS (64-bit recommended).
- Python 3.11+.
- OBS Studio with WebSocket 5.x enabled, on the same LAN.
- Twitch, Google/YouTube, and PayPal developer credentials (optional per event).
- nginx for reverse proxy (Phase 9).
- Cloudflare Tunnel optional (Phase 9).

---

## Quick start

On a fresh Raspberry Pi over SSH:

```bash
git clone https://github.com/YOUR_ORG/eventstream.git
cd eventstream
bash setup.sh
source .venv/bin/activate
```

Generate secrets and paste them into .env:
```bash
python -c "import os,base64;print(base64.b64encode(os.urandom(32)).decode())"
```

Run the layout installer and health check:
```bash

python main.py --install-layout
python main.py --check
```
You should see JSON with "status":"ok", db ok, and migrations version 1.

Boot the application:
```bash

python main.py
```

```text
Phase 0 logs the boot and exits cleanly. Phase 1+ will start the web server on
EVENTSTREAM_HOST:EVENTSTREAM_PORT.
```

Configuration

```text
All configuration is environment variables, loaded from .env via
python-dotenv.
Variable	Purpose	Default
EVENTSTREAM_ROOT	project root	.
EVENTSTREAM_APP_NAME	app name	eventstream
EVENTSTREAM_ENV	development or production	development
EVENTSTREAM_DEBUG	debug flag	true
EVENTSTREAM_HOST	bind address	0.0.0.0
EVENTSTREAM_PORT	bind port	8080
EVENTSTREAM_MASTER_KEY	base64 32+ bytes, AES-GCM master key	required
EVENTSTREAM_SESSION_SECRET	base64, session signing	required
EVENTSTREAM_SESSION_TTL	session lifetime seconds	86400
EVENTSTREAM_VAR_DIR	runtime root	./var
EVENTSTREAM_LOG_LEVEL	DEBUG..CRITICAL	INFO
EVENTSTREAM_LOG_MAX_BYTES	rotating log size	5242880
EVENTSTREAM_LOG_BACKUP_COUNT	rotating log count	5

Never commit .env. The master key must be backed up separately; losing it
means losing access to encrypted data.
```
Security

    Passwords hashed with Argon2id.

    Sessions are HttpOnly, Secure, SameSite=Lax cookies.

    CSRF tokens on every state-changing route.

    Rate limiting per IP and per user.

    AES-GCM field encryption for secrets and PII.

    Per-event AES-GCM keys derived from the master key.

    Audit log for every privileged action.

    Security headers: CSP, HSTS, X-Frame-Options, Referrer-Policy.

    OBS browser sources authenticate via persistent session cookie.

    Sponsors customize branding via a properties page, not raw CSS.

    GDPR: export, delete, and retention rules per event.

Report vulnerabilities privately to the maintainer. Do not open public issues
for security bugs.
Roles and permissions

Roles: admin, organizer, moderator, sponsor, participant,
volunteer, vendor, attendee, spectator.

Permissions are fine-grained and mapped to roles in a permission matrix.
Examples: obs.scene, obs.source, stream.start, clip.trigger,
adbreak.trigger, alert.trigger, chat.moderate, charity.manage,
audit.view, backup.manage.

The full matrix lives in docs/permissions.md and is enforced in code.
Roadmap

Phase 0 - Foundation (done)

    Directory tree, config, SQLite, migrations, encryption, logging, audit,
    health.

Phase 1 - Auth, roles, permissions

    aiohttp server, sessions, CSRF, rate limiting, local + Twitch + Google
    providers, 2FA, email verify, password reset, permission matrix.

Phase 2 - Core domain

    Events, tournaments, brackets, matches, teams, players, stats, standings,
    tiebreakers, per-event encrypted JSON.

Phase 3 - Public site and registration

    Landing, events, event detail, registration, login, schedule, standings,
    sponsors/charity, About, FAQ, Contact, per-event branding, i18n, WCAG AA.

Phase 4 - Player and team dashboards

    Profiles, stats, matches, submissions, screenshot upload, disputes,
    half-team confirmation rule, CSV import.

Phase 5 - Moderator and admin dashboards

    Stream view, OBS controls, chat, moderation queue, clip buttons, VOD
    markers, ad breaks, user/role management, audit view, backups, exports.

Phase 6 - OBS integration

    WebSocket 5.x client, scene/source/transition/filter/transform/media
    control, naming convention enforcement, per-widget browser source routes.

Phase 7 - Live feed, chat, clips

    Twitch/YouTube embeds for moderators, optional WebRTC low-latency, chat
    ingest, website moderator and spectator chat, clip trigger via platform API,
    stream/record start/stop.

Phase 8 - Charity, sponsors, ad breaks, widgets

    Charity totals and sync, sponsor rotation and tiers, ad break triggers,
    widget templates and config panels, per-event branding propagation.

Phase 9 - Hardening and deployment

    Rate limiting, CSRF, XSS, secret rotation, nginx, Cloudflare Tunnel,
    backups, uptime monitoring, GDPR tooling, dry run.

Post-launch - Backlog

    Drag-and-drop widget builder, additional game APIs, more providers, richer
    analytics.

Deployment

Target: headless Raspberry Pi 3, nginx reverse proxy, systemd service,
optional Cloudflare Tunnel.

    Service unit: deploy/systemd/eventstream.service

    Reverse proxy: deploy/nginx.conf

    Tunnel: deploy/cloudflare_tunnel.md

    Backups: deploy/backup_cron.md

Domain and TLS are optional until a domain is purchased. Local IP plus hosts
file works for the first event.
Development
bash

source .venv/bin/activate
python main.py --check

Tests live in tests/. Phase 0 has no test suite yet; Phase 1 introduces
pytest as a dev dependency.

Coding rules:

    One class per file where reasonable.

    Type hints on every public method.

    No print statements in library code; use logging.

    No secrets in code or git.

    Every privileged action goes through the audit logger.

    Every OBS command goes through the permission matrix.

Contributing

This is currently a solo project. If you contribute:

    Open an issue describing the change.

    Keep the dependency footprint minimal.

    Follow the OOP structure and file layout.

    Add or update tests.

    Update docs/ when behavior changes.

License

TBD. Until a license is chosen, all rights reserved by the author.

```text
Acknowledgements

Built for the Deadlock community and for charity events that deserve
production-grade tooling without production-grade infrastructure.
text


---

## Notes on the README

1. **Status section** is honest: Phase 0 done, Phase 1 in progress. Update it each phase.
2. **Roadmap** matches the 30-day plan and names every phase.
3. **Roles list** includes all nine roles from the permission matrix.
4. **Permissions examples** include `alert.trigger` now that Alerts is in the domain.
5. **Quick start** matches `setup.sh`, `install_init.py`, and `main.py` exactly.
6. **Configuration table** matches `.env.example`.
7. **License** is TBD; tell me which license you want and I'll finalize it.
8. **Acknowledgements** mentions Deadlock and charity; change if you prefer.

---

## What I need from you

1. Confirm the README is good to commit.
2. Confirm the repo URL placeholder `YOUR_ORG/eventstream` or give me the real one.
3. Confirm the license: MIT, Apache-2.0, GPL-3.0, or keep "all rights reserved".
4. Confirm the acknowledgement line or give me your preferred wording.
5. Then we proceed to **Phase 1: aiohttp server, sessions, CSRF, rate limiting, auth providers, 2FA, email verify, password reset, roles, permissions, and the permission matrix loader.**
```
