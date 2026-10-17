"""Audit repository. Writes to audit_log and reads recent entries."""

from __future__ import annotations

import sqlite3

from db.repositories.base import BaseRepository


class AuditRepository(BaseRepository):
    def write_entry(
        self,
        action: str,
        actor_id: int | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        details: dict | None = None,
        ip: str | None = None,
    ) -> int:
        details_enc = self._crypto.encrypt_json(details) if details else None

        def work(conn: sqlite3.Connection) -> int:
            cur = conn.execute(
                """
                INSERT INTO audit_log
                    (actor_id, action, target_type, target_id, details_enc, ip)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (actor_id, action, target_type, target_id, details_enc, ip),
            )
            return int(cur.lastrowid)

        return self.write(work)

    def recent(self, limit: int = 100) -> list[dict]:
        def work(conn: sqlite3.Connection):
            return conn.execute(
                """
                SELECT id, actor_id, action, target_type, target_id,
                       details_enc, ip, created_at
                FROM audit_log
                ORDER BY id DESC
                LIMIT ?;
                """,
                (limit,),
            ).fetchall()

        rows = self.read(work)
        out: list[dict] = []
        for row in rows:
            entry = {k: row[k] for k in row.keys()}
            if entry.get("details_enc"):
                try:
                    entry["details"] = self._crypto.decrypt_json(
                        entry["details_enc"]
                    )
                except Exception:  # noqa: BLE001
                    entry["details"] = None
            out.append(entry)
        return out

    def for_actor(self, actor_id: int, limit: int = 100) -> list[dict]:
        def work(conn: sqlite3.Connection):
            return conn.execute(
                """
                SELECT id, actor_id, action, target_type, target_id,
                       details_enc, ip, created_at
                FROM audit_log
                WHERE actor_id = ?
                ORDER BY id DESC
                LIMIT ?;
                """,
                (actor_id, limit),
            ).fetchall()

        rows = self.read(work)
        out: list[dict] = []
        for row in rows:
            entry = {k: row[k] for k in row.keys()}
            if entry.get("details_enc"):
                try:
                    entry["details"] = self._crypto.decrypt_json(
                        entry["details_enc"]
                    )
                except Exception:  # noqa: BLE001
                    entry["details"] = None
            out.append(entry)
        return out