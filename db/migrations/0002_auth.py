"""Auth-related tables: OAuth tokens, email verification, password reset,
TOTP backup codes, rate limits. Also adds csrf_token to sessions.
"""

from __future__ import annotations

import sqlite3

VERSION = 2
NAME = "0002_auth"


SCHEMA = """
ALTER TABLE sessions ADD COLUMN csrf_token TEXT;

CREATE TABLE IF NOT EXISTS oauth_tokens (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id            INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider           TEXT NOT NULL,
    provider_user_id   TEXT,
    access_token_enc   TEXT NOT NULL,
    refresh_token_enc  TEXT,
    scope              TEXT,
    expires_at         TEXT,
    created_at         TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at         TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (user_id, provider)
);

CREATE INDEX IF NOT EXISTS idx_oauth_user      ON oauth_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_oauth_provider  ON oauth_tokens(provider);
CREATE INDEX IF NOT EXISTS idx_oauth_prov_uid  ON oauth_tokens(provider, provider_user_id);

CREATE TABLE IF NOT EXISTS email_verifications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL UNIQUE,
    expires_at  TEXT NOT NULL,
    used_at     TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_email_ver_user    ON email_verifications(user_id);
CREATE INDEX IF NOT EXISTS idx_email_ver_expires ON email_verifications(expires_at);

CREATE TABLE IF NOT EXISTS password_resets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL UNIQUE,
    expires_at  TEXT NOT NULL,
    used_at     TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_pw_reset_user    ON password_resets(user_id);
CREATE INDEX IF NOT EXISTS idx_pw_reset_expires ON password_resets(expires_at);

CREATE TABLE IF NOT EXISTS totp_backup_codes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code_hash   TEXT NOT NULL,
    used_at     TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_totp_backup_user ON totp_backup_codes(user_id);

CREATE TABLE IF NOT EXISTS rate_limits (
    key           TEXT PRIMARY KEY,
    window_start  TEXT NOT NULL,
    count         INTEGER NOT NULL DEFAULT 0,
    expires_at    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rate_limits_expires ON rate_limits(expires_at);
"""


def _split_statements(sql: str) -> list[str]:
    statements: list[str] = []
    buffer: list[str] = []
    for line in sql.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        buffer.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(buffer).strip())
            buffer = []
    if buffer:
        statements.append("\n".join(buffer).strip())
    return statements


def up(conn: sqlite3.Connection) -> None:
    for statement in _split_statements(SCHEMA):
        try:
            conn.execute(statement)
        except sqlite3.OperationalError as exc:
            # ALTER TABLE ADD COLUMN fails if the column already exists.
            # Safe to ignore on re-run in dev; in production migrations
            # run once because of schema_migrations.
            if "duplicate column name" in str(exc).lower():
                continue
            raise


def down(conn: sqlite3.Connection) -> None:
    for table in (
        "rate_limits",
        "totp_backup_codes",
        "password_resets",
        "email_verifications",
        "oauth_tokens",
    ):
        conn.execute(f"DROP TABLE IF EXISTS {table};")
    # SQLite cannot drop a column easily; leave csrf_token in place