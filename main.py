"""Entrypoint. Phase 0: boot, migrate, report health, exit cleanly."""

from __future__ import annotations

import argparse
import logging
import sys

from core.app import Application
from install_init import LayoutInstaller
from pathlib import Path


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
        LayoutInstaller(Path(__file__).resolve().parent).run()
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
    log.info("phase 0 complete: foundation ready")

    # Phase 1+ will start the aiohttp server here.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

