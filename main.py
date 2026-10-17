"""Entrypoint. Phase 0: boot, migrate, report health, exit cleanly."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from aiohttp import web
# ---------------------------------------------------------------------------
# Ensure we run under the project venv, regardless of how this file is called.
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent
_VENV_DIR = _PROJECT_ROOT / os.environ.get("VENV_DIR", ".venv")
_VENV_PYTHON = _VENV_DIR / "bin" / "python"
if not _VENV_PYTHON.exists():
    # Windows fallback
    _VENV_PYTHON = _VENV_DIR / "Scripts" / "python.exe"

if _VENV_PYTHON.exists():
    _running = Path(sys.executable).resolve()
    _wanted = _VENV_PYTHON.resolve()
    if _running != _wanted:
        os.execv(str(_wanted), [str(_wanted), str(Path(__file__).resolve()), *sys.argv[1:]])
# ---------------------------------------------------------------------------

import argparse
import logging

from core.app import Application
from install_init import LayoutInstaller


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="eventstream")
    parser.add_argument("--check", action="store_true",
                        help="run health checks and exit")
    parser.add_argument("--install-layout", action="store_true",
                        help="create directory tree and exit")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    if args.install_layout:
        LayoutInstaller(_PROJECT_ROOT).run()
        return 0

    app = Application.build()
    log = logging.getLogger("eventstream")

    if args.check:
        report = app.health.ready()
        print(report.to_json())
        return 0 if report.status == "ok" else 1

    log.info("eventstream booted env=%s db=%s",
             app.settings.app_env, app.settings.db_path)
    log.info("migrations at version %s", app.migrations.current_version())
    log.info("web server listening on %s:%s",
             app.settings.host, app.settings.port)
    web.run_app(
        app.web_app,
        host=app.settings.host,
        port=app.settings.port,
        access_log=log,
        print=None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())