"""Rate limit repository. Token bucket via row per key."""

from __future__ import annotations

import sqlite3
from datetime import timedelta

from db.repositories.base import BaseRepository


class RateLimitRepository(BaseRepository):
    """Counts requests per key inside a rolling window.

    Each key is a string like 'ip:1.2.3.4' or 'user:42'.
    Window is fixed: the first hit sets window_start, and count is incremented
    until expires_at. After expires_at the row is reset on next hit.
    """

    def hit(
        self,
        key: str,
        window_seconds: int,
        max_hits: int,
    ) -> tuple[bool, int, str]:
        """Record a hit and return (allowed, remaining, expires_at)."""
        now = self.utcnow()
        now_iso = self.iso(now)
        new_expires = self.iso(now + timedelta(seconds=window_seconds))

        def work(conn: sqlite3.Connection):
            row = conn.execute(
                "SELECT key, window_start, count, expires_at FROM rate_limits WHERE key = ?;",
                (key,),
            ).fetchone()

            if row is None or self.parse_iso(row["expires_at"]) is None or \
                    self.parse_iso(row["expires_at"]) < now:
                conn.execute(
                    """
                    INSERT INTO rate_limits (key, window_start, count, expires_at)
                    VALUES (?, ?, 1, ?)
                    ON CONFLICT(key) DO UPDATE SET
                        window_start = excluded.window_start,
                        count        = 1,
                        expires_at   = excluded.expires_at;
                    """,
                    (key, now_iso, new_expires),
                )
                return True, max_hits - 1, new_expires

            count = int(row["count"])
            if count >= max_hits:
                return False, 0, row["expires_at"]

            conn.execute(
                "UPDATE rate_limits SET count = count + 1 WHERE key = ?;",
                (key,),
            )
            return True, max_hits - count - 1, row["expires_at"]

        return self.write(work)

    def reset(self, key: str) -> None:
        def work(conn: sqlite3.Connection) -> None:
            conn.execute("DELETE FROM rate_limits WHERE key = ?;", (key,))

        self.write(work)

    def cleanup_expired(self) -> int:
        now_iso = self.iso(self.utcnow())

        def work(conn: sqlite3.Connection) -> int:
            cur = conn.execute(
                "DELETE FROM rate_limits WHERE expires_at < ?;", (now_iso,)
            )
            return int(cur.rowcount or 0)

        return self.write(work)