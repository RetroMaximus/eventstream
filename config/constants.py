"""Project-wide constants. Keep small and dependency-free."""

from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    ORGANIZER = "organizer"
    MODERATOR = "moderator"
    SPONSOR = "sponsor"
    PARTICIPANT = "participant"
    VOLUNTEER = "volunteer"
    VENDOR = "vendor"
    ATTENDEE = "attendee"
    SPECTATOR = "spectator"


class Permission(str, Enum):
    USERS_MANAGE = "users.manage"
    ROLES_MANAGE = "roles.manage"
    EVENT_CREATE = "event.create"
    EVENT_EDIT = "event.edit"
    BRACKET_MANAGE = "bracket.manage"
    STAT_ENTER = "stat.enter"
    MATCH_CONFIRM = "match.confirm"
    DISPUTE_RAISE = "dispute.raise"
    OBS_SCENE = "obs.scene"
    OBS_SOURCE = "obs.source"
    OBS_FILTER = "obs.filter"
    OBS_TRANSFORM = "obs.transform"
    OBS_MEDIA = "obs.media"
    STREAM_START = "stream.start"
    STREAM_STOP = "stream.stop"
    RECORD_START = "record.start"
    RECORD_STOP = "record.stop"
    CLIP_TRIGGER = "clip.trigger"
    ADBREAK_TRIGGER = "adbreak.trigger"
    ALERT_TRIGGER = "alert.trigger"
    CHAT_MODERATE = "chat.moderate"
    CHAT_SPECTATE = "chat.spectate"
    SPONSOR_PROPERTIES = "sponsor.properties"
    CHARITY_MANAGE = "charity.manage"
    AUDIT_VIEW = "audit.view"
    BACKUP_MANAGE = "backup.manage"


class AuditAction(str, Enum):
    LOGIN = "login"
    LOGIN_FAILED = "login.failed"
    LOGOUT = "logout"
    REGISTER = "register"
    EMAIL_VERIFIED = "email.verified"
    EMAIL_VERIFY_SENT = "email.verify.sent"
    PASSWORD_RESET_REQUESTED = "password.reset.requested"
    PASSWORD_RESET_DONE = "password.reset.done"
    TOTP_ENABLED = "totp.enabled"
    TOTP_DISABLED = "totp.disabled"
    TOTP_FAILED = "totp.failed"
    OAUTH_LOGIN = "oauth.login"
    OAUTH_LINK = "oauth.link"
    ROLE_CHANGE = "role.change"
    PERMISSION_CHANGE = "permission.change"
    SESSION_REVOKED = "session.revoked"
    RATE_LIMIT_HIT = "rate_limit.hit"
    CSRF_REJECTED = "csrf.rejected"
    # Phase 2+ placeholders kept so the enum is stable
    EVENT_CREATE = "event.create"
    EVENT_EDIT = "event.edit"
    OBS_COMMAND = "obs.command"
    STREAM_COMMAND = "stream.command"
    CLIP_CREATE = "clip.create"
    ADBREAK_TRIGGER = "adbreak.trigger"
    ALERT_TRIGGER = "alert.trigger"
    EXPORT = "export"
    BACKUP = "backup"
    KEY_ROTATE = "key.rotate"


class OAuthProvider(str, Enum):
    TWITCH = "twitch"
    GOOGLE = "google"


DEFAULT_ENCODING = "utf-8"

# ---------------------------------------------------------------------------
# Crypto
# ---------------------------------------------------------------------------
AES_GCM_NONCE_BYTES = 12
AES_GCM_TAG_BYTES = 16
PER_EVENT_KEY_INFO = b"eventstream:event:v1"
MASTER_KEY_MIN_BYTES = 32

# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------
DEFAULT_COOKIE_NAME = "eventstream_session"
SESSION_ID_BYTES = 32  # token_urlsafe(32) -> ~43 chars
SESSION_TOUCH_INTERVAL_SECONDS = 300  # update last_seen at most every 5 min
SESSION_CLEANUP_INTERVAL_SECONDS = 3600

# ---------------------------------------------------------------------------
# CSRF
# ---------------------------------------------------------------------------
CSRF_HEADER = "X-CSRF-Token"
CSRF_FORM_FIELD = "csrf_token"
CSRF_TOKEN_BYTES = 32
CSRF_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
RATE_LIMIT_DEFAULT_WINDOW_SECONDS = 60
RATE_LIMIT_DEFAULT_MAX = 120
RATE_LIMIT_CLEANUP_INTERVAL_SECONDS = 600

# ---------------------------------------------------------------------------
# Passwords (Argon2id)
# ---------------------------------------------------------------------------
ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 32768  # 32 MiB — safe on a Pi 3 with 1 GB RAM
ARGON2_PARALLELISM = 2
ARGON2_HASH_LEN = 32
ARGON2_SALT_LEN = 16

# ---------------------------------------------------------------------------
# TOTP
# ---------------------------------------------------------------------------
TOTP_DIGITS = 6
TOTP_INTERVAL_SECONDS = 30
TOTP_SECRET_BYTES = 20
TOTP_BACKUP_CODE_COUNT = 10
TOTP_BACKUP_CODE_BYTES = 8

# ---------------------------------------------------------------------------
# Email verification and password reset
# ---------------------------------------------------------------------------
VERIFY_TOKEN_BYTES = 32
VERIFY_TOKEN_TTL_SECONDS = 86400        # 24 hours
RESET_TOKEN_BYTES = 32
RESET_TOKEN_TTL_SECONDS = 3600          # 1 hour

# ---------------------------------------------------------------------------
# OAuth
# ---------------------------------------------------------------------------
OAUTH_STATE_BYTES = 32
OAUTH_PKCE_VERIFIER_BYTES = 32
OAUTH_TOKEN_REFRESH_SKEW_SECONDS = 60