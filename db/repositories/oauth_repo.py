"""OAuth token repository. Encrypts access and refresh tokens at rest."""

from __future__ import annotations

import sqlite3
from datetime import timedelta

from db.repositories.base import BaseRepository


class OAuthRepository(BaseRepository):
    """Stores OAuth tokens per user and provider.

    Access tokens and refresh tokens are encrypted with the master key.
    Provider user id is stored plaintext to allow lookup by provider account.
    """

    def upsert(
        self,
        user_id: int,
        provider: str,
        access_token: str,
        refresh_token: str | None,
        expires_in: int | None,
        scope: str | None,
        provider_user_id: str | None = None,
    ) -> None:
        access_enc = self._crypto.encrypt_str(access_token)
        refresh_enc = (
            self._crypto.encrypt_str(refresh_token) if refresh_token else None
        )
        expires_at = (
            self.iso(self.utcnow() + timedelta(seconds=expires_in))
            if expires_in
            else None
        )

        def work(conn: sqlite3.Connection) -> None:
            conn.execute(
                """
                INSERT INTO oauth_tokens
                    (user_id, provider, provider_user_id, access_token_enc,
                     refresh_token_enc, scope, expires_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(user_id, provider) DO UPDATE SET
                    provider_user_id = excluded.provider_user_id,
                    access_token_enc = excluded.access_token_enc,
                    refresh_token_enc = excluded.refresh_token_enc,
                    scope            = excluded.scope,
                    expires_at       = excluded.expires_at,
                    updated_at       = datetime('now');
                """,
                (
                    user_id,
                    provider,
                    provider_user_id,
                    access_enc,
                    refresh_enc,
                    scope,
                    expires_at,
                ),
            )

        self.write(work)

    def by_user_and_provider(
        self, user_id: int, provider: str
    ) -> dict | None:
        def work(conn: sqlite3.Connection):
            return conn.execute(
                """
                SELECT * FROM oauth_tokens
                WHERE user_id = ? AND provider = ?;
                """,
                (user_id, provider),
            ).fetchone()

        row = self.read(work)
        return self._decode(row)

    def by_provider_user_id(
        self, provider: str, provider_user_id: str
    ) -> dict | None:
        def work(conn: sqlite3.Connection):
            return conn.execute(
                """
                SELECT * FROM oauth_tokens
                WHERE provider = ? AND provider_user_id = ?;
                """,
                (provider, provider_user_id),
            ).fetchone()

        row = self.read(work)
        return self._decode(row)

    def delete(self, user_id: int, provider: str) -> None:
        def work(conn: sqlite3.Connection) -> None:
            conn.execute(
                "DELETE FROM oauth_tokens WHERE user_id = ? AND provider = ?;",
                (user_id, provider),
            )

        self.write(work)

    def _decode(self, row) -> dict | None:
        if row is None:
            return None
        data = {k: row[k] for k in row.keys()}
        for field in ("access_token_enc", "refresh_token_enc"):
            if data.get(field):
                try:
                    data[field.replace("_enc", "")] = self._crypto.decrypt_str(
                        data[field]
                    )
                except Exception:  # noqa: BLE001
                    data[field.replace("_enc", "")] = None
        return data