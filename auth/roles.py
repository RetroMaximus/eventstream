"""Role and permission seeder. Upserts roles and permission matrix into DB."""

from __future__ import annotations

from config.constants import Permission, Role
from db.connection import Database


class RoleSeeder:
    """Loads roles and permissions into the database.

    Idempotent: safe to call on every boot. It upserts roles and permissions,
    then rebuilds role_permissions to match the static matrix.
    """

    def __init__(self, db: Database) -> None:
        self._db = db

    def seed(self) -> None:
        from auth.permissions import PermissionMatrix

        def work(conn):
            # Roles
            for role in Role:
                conn.execute(
                    """
                    INSERT INTO roles (name, description)
                    VALUES (?, ?)
                    ON CONFLICT(name) DO UPDATE SET description = excluded.description;
                    """,
                    (role.value, role.value),
                )

            # Permissions
            for perm in Permission:
                conn.execute(
                    """
                    INSERT INTO permissions (name, description)
                    VALUES (?, ?)
                    ON CONFLICT(name) DO UPDATE SET description = excluded.description;
                    """,
                    (perm.value, perm.value),
                )

            # Clear existing mappings then rebuild
            conn.execute("DELETE FROM role_permissions;")

            for role in Role:
                role_row = conn.execute(
                    "SELECT id FROM roles WHERE name = ?;", (role.value,)
                ).fetchone()
                if role_row is None:
                    continue
                role_id = role_row["id"]
                for perm in PermissionMatrix.permissions_for(role):
                    perm_row = conn.execute(
                        "SELECT id FROM permissions WHERE name = ?;", (perm.value,)
                    ).fetchone()
                    if perm_row is None:
                        continue
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
                        VALUES (?, ?);
                        """,
                        (role_id, perm_row["id"]),
                    )

        self._db.write(work)

    def role_id(self, role: Role) -> int | None:
        def work(conn):
            return conn.execute(
                "SELECT id FROM roles WHERE name = ?;", (role.value,)
            ).fetchone()

        row = self._db.read(work)
        return int(row["id"]) if row else None

    def permission_id(self, permission: Permission) -> int | None:
        def work(conn):
            return conn.execute(
                "SELECT id FROM permissions WHERE name = ?;", (permission.value,)
            ).fetchone()

        row = self._db.read(work)
        return int(row["id"]) if row else None

    def assign_role(
        self,
        user_id: int,
        role: Role,
        event_id: int = 0,
    ) -> None:
        def work(conn):
            role_row = conn.execute(
                "SELECT id FROM roles WHERE name = ?;", (role.value,)
            ).fetchone()
            if role_row is None:
                return
            conn.execute(
                """
                INSERT OR IGNORE INTO user_roles (user_id, role_id, event_id)
                VALUES (?, ?, ?);
                """,
                (user_id, role_row["id"], event_id),
            )

        self._db.write(work)

    def unassign_role(
        self,
        user_id: int,
        role: Role,
        event_id: int = 0,
    ) -> None:
        def work(conn):
            role_row = conn.execute(
                "SELECT id FROM roles WHERE name = ?;", (role.value,)
            ).fetchone()
            if role_row is None:
                return
            conn.execute(
                """
                DELETE FROM user_roles
                WHERE user_id = ? AND role_id = ? AND event_id = ?;
                """,
                (user_id, role_row["id"], event_id),
            )

        self._db.write(work)

    def roles_for_user(self, user_id: int) -> dict[int, set[Role]]:
        """Return {event_id: {roles}} for the user, including event_id=0."""
        def work(conn):
            return conn.execute(
                """
                SELECT r.name AS role_name, ur.event_id AS event_id
                FROM user_roles ur
                JOIN roles r ON r.id = ur.role_id
                WHERE ur.user_id = ?;
                """,
                (user_id,),
            ).fetchall()

        rows = self._db.read(work)
        out: dict[int, set[Role]] = {}
        for row in rows:
            try:
                role = Role(row["role_name"])
            except ValueError:
                continue
            out.setdefault(int(row["event_id"]), set()).add(role)
        return out