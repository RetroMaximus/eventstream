python main.py --check

python - <<'PY'
from core.app import Application
from config.constants import Role, Permission

app = Application.build()

print("admin role id:", app.roles.role_id(Role.ADMIN))
print("obs.scene perm id:", app.roles.permission_id(Permission.OBS_SCENE))

h = app.passwords.hash("hunter2")
print("verify ok:", app.passwords.verify("hunter2", h))
print("verify bad:", app.passwords.verify("wrong", h))

secret = app.totp.generate_secret()
code = app.totp.now(secret)
print("totp code:", code, "verify:", app.totp.verify(secret, code))

uid = app.users.create("role_user", "role@example.com", "x")
app.roles.assign_role(uid, Role.MODERATOR, event_id=0)
print("roles for user:", app.roles.roles_for_user(uid))

app.roles.unassign_role(uid, Role.MODERATOR, event_id=0)
app.users.set_active(uid, False)
print("done")
PY