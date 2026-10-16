"""Audit log writer. Writes to SQLite and to a dedicated log file."""

from __future__ import annotations

import json
import logging
from typing import Any

from db.connection import Database
from security.crypto import CryptoBox


class AuditLog:
    def __init__(self, db: Database, crypto: CryptoBox) -> None:
        self._db = db
        self._crypto = crypto
        self._log = logging.getLogger("eventstream.audit")

    def record(
        self,
        action: str,
        actor_id: int | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        details: dict[str, Any] | None = None,
        ip: str | None = None,
    ) -> None:
        details_enc = self._crypto.encrypt_json(details) if details else None

        def work(conn):
            conn.execute(
                """
                INSERT INTO audit_log
                    (actor_id, action, target_type, target_id, details_enc, ip)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (actor_id, action, target_type, target_id, details_enc, ip),
            )

        self._db.write(work)
        self._log.info(
            "audit action=%s actor=%s target=%s/%s ip=%s details=%s",
            action, actor_id, target_type, target_id, ip,
            json.dumps(details, default=str) if details else "{}",
        )

