"""Migration runner. Applies ordered migrations, tracks version."""

from __future__ import annotations

import importlib
import sqlite3
from pathlib import Path

from db.connection import Database


class MigrationRunner:
    MIGRATIONS_PKG = "db.migrations"

    def __init__(self, db: Database) -> None:
        self._db = db

    def _discover(self) -> list[tuple[int, str, object]]:
        pkg_path = Path(__file__).resolve().parent
        found: list[tuple[int, str, object]] = []
        for file in sorted(pkg_path.glob("[0-9][0-9][0-9][0-9]_*.py")):
            mod_name = f"{self.MIGRATIONS_PKG}.{file.stem}"
            module = importlib.import_module(mod_name)
            version = int(getattr(module, "VERSION"))
            name = getattr(module, "NAME", file.stem)
            found.append((version, name, module))
        found.sort(key=lambda item: item[0])
        return found

    def _ensure_table(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version     INTEGER PRIMARY KEY,
                name        TEXT NOT NULL,
                applied_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )

    def _applied(self, conn: sqlite3.Connection) -> set[int]:
        rows = conn.execute("SELECT version FROM schema_migrations;").fetchall()
        return {row["version"] for row in rows}

    def upgrade(self) -> list[str]:
        applied_names: list[str] = []

        def work(conn: sqlite3.Connection) -> list[str]:
            self._ensure_table(conn)
            done = self._applied(conn)
            names: list[str] = []
            for version, name, module in self._discover():
                if version in done:
                    continue
                module.up(conn)
                conn.execute(
                    "INSERT INTO schema_migrations(version, name) VALUES (?, ?);",
                    (version, name),
                )
                names.append(name)
            return names

        applied_names = self._db.write(work)
        return applied_names

    def current_version(self) -> int:
        def work(conn: sqlite3.Connection) -> int:
            self._ensure_table(conn)
            row = conn.execute(
                "SELECT MAX(version) AS v FROM schema_migrations;"
            ).fetchone()
            return int(row["v"] or 0)

        return self._db.read(work)

