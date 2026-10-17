"""Session service. Ties cookies, DB rows, and request context together."""

from __future__ import annotations

import secrets

from aiohttp import web

from config.constants import (
    CSRF_TOKEN_BYTES,
    SESSION_ID_BYTES,
    SESSION_TOUCH_INTERVAL_SECONDS,
)
from db.repositories.session_repo import SessionRepository


class SessionService:
    """Creates, loads, touches, and destroys sessions.

    The cookie carries only the opaque session id. All state lives in SQLite.
    """

    def __init__(
        self,
        sessions: SessionRepository,
        cookie_name: str,
        cookie_secure: bool,
        cookie_samesite: str,
        ttl_seconds: int,
    ) -> None:
        self._sessions = sessions
        self.cookie_name = cookie_name
        self.cookie_secure = cookie_secure
        self.cookie_samesite = cookie_samesite
        self.ttl_seconds = ttl_seconds

    # ------------------------------------------------------------------
    # Token helpers
    # ------------------------------------------------------------------
    @staticmethod
    def new_session_id() -> str:
        return secrets.token_urlsafe(SESSION_ID_BYTES)

    @staticmethod
    def new_csrf_token() -> str:
        return secrets.token_urlsafe(CSRF_TOKEN_BYTES)

    # ------------------------------------------------------------------
    # Cookie helpers
    # ------------------------------------------------------------------
    def set_cookie(self, response: web.StreamResponse, session_id: str) -> None:
        response.set_cookie(
            self.cookie_name,
            session_id,
            max_age=self.ttl_seconds,
            httponly=True,
            secure=self.cookie_secure,
            samesite=self.cookie_samesite,
            path="/",
        )

    def clear_cookie(self, response: web.StreamResponse) -> None:
        response.del_cookie(self.cookie_name, path="/")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def create(
        self,
        user_id: int,
        ip: str | None,
        user_agent: str | None,
    ) -> tuple[str, str]:
        session_id = self.new_session_id()
        csrf_token = self.new_csrf_token()
        self._sessions.create(
            session_id=session_id,
            user_id=user_id,
            ttl_seconds=self.ttl_seconds,
            csrf_token=csrf_token,
            ip=ip,
            user_agent=user_agent,
        )
        return session_id, csrf_token

    def load(self, session_id: str) -> dict | None:
        row = self._sessions.by_id(session_id)
        if row is None:
            return None
        if row.get("revoked"):
            return None
        return row

    def touch(self, session_id: str) -> None:
        self._sessions.touch(session_id, self.ttl_seconds)

    def destroy(self, session_id: str) -> None:
        self._sessions.revoke(session_id)

    def destroy_all_for_user(self, user_id: int) -> None:
        self._sessions.revoke_all_for_user(user_id)

    def cleanup_expired(self) -> int:
        return self._sessions.cleanup_expired()