"""Rate limit service. Thin wrapper over the repository."""

from __future__ import annotations

from dataclasses import dataclass

from db.repositories.rate_limit_repo import RateLimitRepository


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    expires_at: str


class RateLimitService:
    """Named buckets. Each bucket has its own window and max hits."""

    def __init__(self, repo: RateLimitRepository) -> None:
        self._repo = repo

    def check(
        self,
        key: str,
        window_seconds: int,
        max_hits: int,
    ) -> RateLimitResult:
        allowed, remaining, expires = self._repo.hit(key, window_seconds, max_hits)
        return RateLimitResult(allowed=allowed, remaining=remaining, expires_at=expires)

    def reset(self, key: str) -> None:
        self._repo.reset(key)

    def cleanup_expired(self) -> int:
        return self._repo.cleanup_expired()