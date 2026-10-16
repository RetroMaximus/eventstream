

"""SQLite connection factory with WAL, foreign keys, and row factory."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import Lock


class Database:
    """Owns a single SQLite file and hands out connections.

    SQLite is thread-safe with check_same_thread=False + serialized access.
    We use a lock for writes and rely on WAL for concurrent reads.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._path

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self._path,
            check_same_thread=False,
            isolation_level=None,   # autocommit; we manage transactions
            timeout=30.0,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=30000;")
        return conn

    def write(self, fn):
        """Run fn(conn) inside a serialized transaction."""
        with self._lock:
            conn = self.connect()
            try:
                conn.execute("BEGIN IMMEDIATE;")
                result = fn(conn)
                conn.execute("COMMIT;")
                return result
            except Exception:
                conn.execute("ROLLBACK;")
                raise
            finally:
                conn.close()

    def read(self, fn):
        conn = self.connect()
        try:
            return fn(conn)
        finally:
            conn.close()

