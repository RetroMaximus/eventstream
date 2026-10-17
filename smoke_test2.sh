python main.py --check
# expect {"status":"ok",...,"migrations":{"ok":true,"version":2}}

python - <<'PY'
from core.app import Application
from config.constants import Role, Permission

app = Application.build()

# Seeder check
print("admin role id:", app.roles.role_id(Role.ADMIN))
print("obs.scene perm id:", app.roles.permission_id(Permission.OBS_SCENE))

# Password round trip
h = app.passwords.hash("hunter2")
print("verify ok:", app.passwords.verify("hunter2", h))
print("verify bad:", app.passwords.verify("wrong", h))

# TOTP round trip
secret = app.totp.generate_secret()
code = app.totp.now(secret)
print("totp code:", code, "verify:", app.totp.verify(secret, code))

# Role assignment
uid = app.users.create("role_user", "role@example.com", "x")
app.roles.assign_role(uid, Role.MODERATOR, event_id=0)
print("roles for user:", app.roles.roles_for_user(uid))

app.roles.unassign_role(uid, Role.MODERATOR, event_id=0)
app.users.set_active(uid, False)
print("done")
PY