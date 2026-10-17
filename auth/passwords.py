"""Password hashing with Argon2id."""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)

from config.constants import (
    ARGON2_HASH_LEN,
    ARGON2_MEMORY_COST,
    ARGON2_PARALLELISM,
    ARGON2_SALT_LEN,
    ARGON2_TIME_COST,
)


class PasswordHasherService:
    """Wraps argon2-cffi's PasswordHasher.

    The underlying hasher is thread-safe and stateless between calls.
    """

    def __init__(self) -> None:
        self._hasher = PasswordHasher(
            time_cost=ARGON2_TIME_COST,
            memory_cost=ARGON2_MEMORY_COST,
            parallelism=ARGON2_PARALLELISM,
            hash_len=ARGON2_HASH_LEN,
            salt_len=ARGON2_SALT_LEN,
        )

    def hash(self, password: str) -> str:
        if not password:
            raise ValueError("Password must not be empty")
        return self._hasher.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        if not password or not password_hash:
            return False
        try:
            return self._hasher.verify(password_hash, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False
        except Exception:  # noqa: BLE001
            return False

    def needs_rehash(self, password_hash: str) -> bool:
        if not password_hash:
            return True
        try:
            return self._hasher.check_needs_rehash(password_hash)
        except Exception:  # noqa: BLE001
            return True