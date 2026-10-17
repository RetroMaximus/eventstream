"""Unit tests for the rate limit repository and service."""

from db.connection import Database
from db.repositories.rate_limit_repo import RateLimitRepository
from core.ratelimit import RateLimitService
from security.crypto import CryptoBox
from pathlib import Path
import tempfile


def make_service(tmp: Path) -> RateLimitService:
    db = Database(tmp / "test.sqlite3")
    db.write(lambda conn: conn.execute("""
        CREATE TABLE rate_limits (
            key TEXT PRIMARY KEY,
            window_start TEXT NOT NULL,
            count INTEGER NOT NULL DEFAULT 0,
            expires_at TEXT NOT NULL
        );
    """))
    repo = RateLimitRepository(db, CryptoBox(b"\x00" * 32))
    return RateLimitService(repo)


def test_allows_up_to_max():
    with tempfile.TemporaryDirectory() as d:
        svc = make_service(Path(d))
        for i in range(3):
            r = svc.check("ip:1.2.3.4", 60, 3)
            assert r.allowed
        r = svc.check("ip:1.2.3.4", 60, 3)
        assert not r.allowed


def test_reset_clears_counter():
    with tempfile.TemporaryDirectory() as d:
        svc = make_service(Path(d))
        svc.check("ip:1.2.3.4", 60, 1)
        r = svc.check("ip:1.2.3.4", 60, 1)
        assert not r.allowed
        svc.reset("ip:1.2.3.4")
        r = svc.check("ip:1.2.3.4", 60, 1)
        assert r.allowed