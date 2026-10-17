"""Permission matrix and checks."""

from __future__ import annotations

from config.constants import Permission, Role


class PermissionMatrix:
    """Static mapping of roles to permissions.

    Values are sets of Permission for O(1) lookups. The matrix is the source
    of truth for seeding the DB and for runtime checks when a DB is not used
    (e.g. unit tests).
    """

    MATRIX: dict[Role, set[Permission]] = {
        Role.ADMIN: {
            Permission.USERS_MANAGE,
            Permission.ROLES_MANAGE,
            Permission.EVENT_CREATE,
            Permission.EVENT_EDIT,
            Permission.BRACKET_MANAGE,
            Permission.STAT_ENTER,
            Permission.MATCH_CONFIRM,
            Permission.DISPUTE_RAISE,
            Permission.OBS_SCENE,
            Permission.OBS_SOURCE,
            Permission.OBS_FILTER,
            Permission.OBS_TRANSFORM,
            Permission.OBS_MEDIA,
            Permission.STREAM_START,
            Permission.STREAM_STOP,
            Permission.RECORD_START,
            Permission.RECORD_STOP,
            Permission.CLIP_TRIGGER,
            Permission.ADBREAK_TRIGGER,
            Permission.ALERT_TRIGGER,
            Permission.CHAT_MODERATE,
            Permission.CHAT_SPECTATE,
            Permission.SPONSOR_PROPERTIES,
            Permission.CHARITY_MANAGE,
            Permission.AUDIT_VIEW,
            Permission.BACKUP_MANAGE,
        },
        Role.ORGANIZER: {
            Permission.EVENT_CREATE,
            Permission.EVENT_EDIT,
            Permission.BRACKET_MANAGE,
            Permission.STAT_ENTER,
            Permission.MATCH_CONFIRM,
            Permission.DISPUTE_RAISE,
            Permission.OBS_SCENE,
            Permission.OBS_SOURCE,
            Permission.OBS_FILTER,
            Permission.OBS_TRANSFORM,
            Permission.OBS_MEDIA,
            Permission.STREAM_START,
            Permission.STREAM_STOP,
            Permission.RECORD_START,
            Permission.RECORD_STOP,
            Permission.CLIP_TRIGGER,
            Permission.ADBREAK_TRIGGER,
            Permission.ALERT_TRIGGER,
            Permission.CHAT_MODERATE,
            Permission.CHAT_SPECTATE,
            Permission.SPONSOR_PROPERTIES,
            Permission.CHARITY_MANAGE,
            Permission.AUDIT_VIEW,
        },
        Role.MODERATOR: {
            Permission.STAT_ENTER,
            Permission.MATCH_CONFIRM,
            Permission.DISPUTE_RAISE,
            Permission.OBS_SCENE,
            Permission.OBS_SOURCE,
            Permission.OBS_FILTER,
            Permission.OBS_TRANSFORM,
            Permission.OBS_MEDIA,
            Permission.STREAM_START,
            Permission.STREAM_STOP,
            Permission.RECORD_START,
            Permission.RECORD_STOP,
            Permission.CLIP_TRIGGER,
            Permission.ADBREAK_TRIGGER,
            Permission.ALERT_TRIGGER,
            Permission.CHAT_MODERATE,
            Permission.CHAT_SPECTATE,
            Permission.CHARITY_MANAGE,
        },
        Role.SPONSOR: {
            Permission.CHAT_SPECTATE,
            Permission.SPONSOR_PROPERTIES,
        },
        Role.PARTICIPANT: {
            Permission.STAT_ENTER,
            Permission.MATCH_CONFIRM,
            Permission.DISPUTE_RAISE,
            Permission.CHAT_SPECTATE,
        },
        Role.VOLUNTEER: {
            Permission.CHAT_MODERATE,
            Permission.CHAT_SPECTATE,
        },
        Role.VENDOR: {
            Permission.CHAT_SPECTATE,
        },
        Role.ATTENDEE: {
            Permission.CHAT_SPECTATE,
        },
        Role.SPECTATOR: {
            Permission.CHAT_SPECTATE,
        },
    }

    @classmethod
    def permissions_for(cls, role: Role) -> set[Permission]:
        return set(cls.MATRIX.get(role, set()))

    @classmethod
    def has(cls, role: Role, permission: Permission) -> bool:
        return permission in cls.MATRIX.get(role, set())


class PermissionChecker:
    """Runtime permission checks for a user.

    Inputs are roles (global and per-event) and the permissions requested.
    Output is a boolean. If no user is present, returns False.
    """

    def __init__(self, global_roles: set[Role], event_roles: dict[int, set[Role]] | None = None) -> None:
        self.global_roles = set(global_roles or set())
        self.event_roles = dict(event_roles or {})

    def _roles_for(self, event_id: int | None) -> set[Role]:
        roles = set(self.global_roles)
        if event_id is not None and event_id in self.event_roles:
            roles |= self.event_roles[event_id]
        return roles

    def has(self, permission: Permission, event_id: int | None = None) -> bool:
        for role in self._roles_for(event_id):
            if PermissionMatrix.has(role, permission):
                return True
        return False

    def all_of(self, permissions: list[Permission], event_id: int | None = None) -> bool:
        return all(self.has(p, event_id) for p in permissions)

    def any_of(self, permissions: list[Permission], event_id: int | None = None) -> bool:
        return any(self.has(p, event_id) for p in permissions)