"""Shared repository base."""

from __future__ import annotations

from datetime import datetime, timezone

from db.connection import Database
from security.crypto import CryptoBox


class BaseRepository:
    """Common helpers for all repositories.

    Subclasses receive a Database and a CryptoBox. The CryptoBox is used for
    fields that must be encrypted at rest.
    """

    def __init__(self, db: Database, crypto: CryptoBox) -> None:
        self._db = db
        self._crypto = crypto

    # ------------------------------------------------------------------
    # Time helpers (UTC, ISO 8601, seconds precision)
    # ------------------------------------------------------------------
    @staticmethod
    def utcnow() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def iso(dt: datetime) -> str:
        return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()

    @staticmethod
    def parse_iso(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    # ------------------------------------------------------------------
    # Convenience wrappers
    # ------------------------------------------------------------------
    def read(self, fn):
        return self._db.read(fn)

    def write(self, fn):
        return self._db.write(fn)

    # ------------------------------------------------------------------
    # Row -> dict helper
    # ------------------------------------------------------------------
    @staticmethod
    def row_to_dict(row) -> dict | None:
        if row is None:
            return None
        return {k: row[k] for k in row.keys()}