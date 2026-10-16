"""Health and readiness checks."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field

from db.connection import Database
from db.migrations.runner import MigrationRunner


@dataclass
class HealthReport:
    status: str
    checks: dict[str, dict] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)

    def to_json(self) -> str:
        return json.dumps(
            {"status": self.status, "ts": self.ts, "checks": self.checks},
            separators=(",", ":"),
        )


class HealthCheck:
    def __init__(self, db: Database, migrations: MigrationRunner) -> None:
        self._db = db
        self._migrations = migrations

    def live(self) -> HealthReport:
        return HealthReport(status="ok", checks={"live": {"ok": True}})

    def ready(self) -> HealthReport:
        checks: dict[str, dict] = {}
        ok = True

        try:
            def ping(conn):
                return conn.execute("SELECT 1;").fetchone()[0]

            self._db.read(ping)
            checks["db"] = {"ok": True}
        except Exception as exc:  # noqa: BLE001
            ok = False
            checks["db"] = {"ok": False, "error": str(exc)}

        try:
            version = self._migrations.current_version()
            checks["migrations"] = {"ok": version > 0, "version": version}
            ok = ok and version > 0
        except Exception as exc:  # noqa: BLE001
            ok = False
            checks["migrations"] = {"ok": False, "error": str(exc)}

        return HealthReport(status="ok" if ok else "degraded", checks=checks)

