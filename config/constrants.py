
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
    CHAT_MODERATE = "chat.moderate"
    CHAT_SPECTATE = "chat.spectate"
    SPONSOR_PROPERTIES = "sponsor.properties"
    CHARITY_MANAGE = "charity.manage"
    ALERT_TRIGGER = "alert.trigger"
    AUDIT_VIEW = "audit.view"
    BACKUP_MANAGE = "backup.manage"


class AuditAction(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    ROLE_CHANGE = "role.change"
    PERMISSION_CHANGE = "permission.change"
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


DEFAULT_ENCODING = "utf-8"
AES_GCM_NONCE_BYTES = 12
AES_GCM_TAG_BYTES = 16
PER_EVENT_KEY_INFO = b"eventstream:event:v1"
MASTER_KEY_MIN_BYTES = 32

