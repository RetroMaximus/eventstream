"""User repository. Handles encrypted email, password hash, TOTP secret."""

from __future__ import annotations

import hashlib
import sqlite3
import uuid
from typing import Any

from db.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    """CRUD for the users table.

    Email is stored two ways:
      - email_hash: SHA-256 of normalized email, for lookup and uniqueness.
      - email_enc : AES-GCM encrypted email, for display and recovery.
    Password hash is stored as-is (Argon2id string). TOTP secret is encrypted.
    """

    @staticmethod
    def normalize_email(email: str) -> str:
        return email.strip().lower()

    @staticmethod
    def hash_email(email: str) -> str:
        return hashlib.sha256(
            UserRepository.normalize_email(email).encode("utf-8")
        ).hexdigest()

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------
    def create(
        self,
        username: str,
        email: str,
        password_hash: str | None,
        display_name: str | None = None,
        email_verified: bool = False,
    ) -> int:
        email_hash = self.hash_email(email)
        email_enc = self._crypto.encrypt_str(self.normalize_email(email))
        user_uuid = str(uuid.uuid4())

        def work(conn: sqlite3.Connection) -> int:
            cur = conn.execute(
                """
                INSERT INTO users
                    (uuid, username, display_name, email_enc, email_hash,
                     password_hash, email_verified, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1);
                """,
                (
                    user_uuid,
                    username,
                    display_name or username,
                    email_enc,
                    email_hash,
                    password_hash,
                    1 if email_verified else 0,
                ),
            )
            return int(cur.lastrowid)

        return self.write(work)

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------
    def by_id(self, user_id: int) -> dict | None:
        def work(conn: sqlite3.Connection):
            return conn.execute(
                "SELECT * FROM users WHERE id = ?;", (user_id,)
            ).fetchone()

        row = self.read(work)
        return self._decode(row)

    def by_username(self, username: str) -> dict | None:
        def work(conn: sqlite3.Connection):
            return conn.execute(
                "SELECT * FROM users WHERE username = ?;", (username,)
            ).fetchone()

        row = self.read(work)
        return self._decode(row)

    def by_email(self, email: str) -> dict | None:
        email_hash = self.hash_email(email)

        def work(conn: sqlite3.Connection):
            return conn.execute(
                "SELECT * FROM users WHERE email_hash = ?;", (email_hash,)
            ).fetchone()

        row = self.read(work)
        return self._decode(row)

    def by_uuid(self, user_uuid: str) -> dict | None:
        def work(conn: sqlite3.Connection):
            return conn.execute(
                "SELECT * FROM users WHERE uuid = ?;", (user_uuid,)
            ).fetchone()

        row = self.read(work)
        return self._decode(row)

    # ------------------------------------------------------------------
    # Updates
    # ------------------------------------------------------------------
    def set_password_hash(self, user_id: int, password_hash: str) -> None:
        def work(conn: sqlite3.Connection) -> None:
            conn.execute(
                """
                UPDATE users
                SET password_hash = ?, updated_at = datetime('now')
                WHERE id = ?;
                """,
                (password_hash, user_id),
            )

        self.write(work)

    def set_email(self, user_id: int, email: str, verified: bool = False) -> None:
        email_hash = self.hash_email(email)
        email_enc = self._crypto.encrypt_str(self.normalize_email(email))

        def work(conn: sqlite3.Connection) -> None:
            conn.execute(
                """
                UPDATE users
                SET email_enc = ?, email_hash = ?, email_verified = ?,
                    updated_at = datetime('now')
                WHERE id = ?;
                """,
                (email_enc, email_hash, 1 if verified else 0, user_id),
            )

        self.write(work)

    def set_email_verified(self, user_id: int, verified: bool = True) -> None:
        def work(conn: sqlite3.Connection) -> None:
            conn.execute(
                """
                UPDATE users
                SET email_verified = ?, updated_at = datetime('now')
                WHERE id = ?;
                """,
                (1 if verified else 0, user_id),
            )

        self.write(work)

    def set_totp_secret(self, user_id: int, secret: str | None) -> None:
        enc = self._crypto.encrypt_str(secret) if secret else None

        def work(conn: sqlite3.Connection) -> None:
            conn.execute(
                """
                UPDATE users
                SET totp_secret_enc = ?, updated_at = datetime('now')
                WHERE id = ?;
                """,
                (enc, user_id),
            )

        self.write(work)

    def set_active(self, user_id: int, active: bool) -> None:
        def work(conn: sqlite3.Connection) -> None:
            conn.execute(
                """
                UPDATE users
                SET is_active = ?, updated_at = datetime('now')
                WHERE id = ?;
                """,
                (1 if active else 0, user_id),
            )

        self.write(work)

    # ------------------------------------------------------------------
    # Decode helpers
    # ------------------------------------------------------------------
    def _decode(self, row) -> dict | None:
        if row is None:
            return None
        data: dict[str, Any] = {k: row[k] for k in row.keys()}
        if data.get("email_enc"):
            try:
                data["email"] = self._crypto.decrypt_str(data["email_enc"])
            except Exception:  # noqa: BLE001
                data["email"] = None
        else:
            data["email"] = None
        if data.get("totp_secret_enc"):
            try:
                data["totp_secret"] = self._crypto.decrypt_str(
                    data["totp_secret_enc"]
                )
            except Exception:  # noqa: BLE001
                data["totp_secret"] = None
        else:
            data["totp_secret"] = None
        return data