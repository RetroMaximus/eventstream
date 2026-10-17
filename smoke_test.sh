python - <<'PY'
from core.app import Application

app = Application.build()
print("migration version:", app.migrations.current_version())

# user
uid = app.users.create("smoke_user", "smoke@example.com", "not-a-real-hash")
row = app.users.by_id(uid)
print("user:", row["username"], row["email"])

# session
import secrets
sid = secrets.token_urlsafe(32)
app.sessions.create(sid, uid, 3600, csrf_token="csrf-smoke", ip="127.0.0.1")
loaded = app.sessions.by_id(sid)
print("session user:", loaded["user_id"], "csrf:", loaded["csrf_token"])
app.sessions.revoke(sid)
print("revoked:", app.sessions.by_id(sid)["revoked"])

# rate limit
for i in range(3):
    allowed, remaining, expires = app.rate_limits.hit("ip:127.0.0.1", 60, 2)
    print("hit", i, "allowed:", allowed, "remaining:", remaining)

# oauth
app.oauth.upsert(uid, "twitch", "access-abc", "refresh-xyz", 3600, "chat:read", "tw-provider-1")
tok = app.oauth.by_user_and_provider(uid, "twitch")
print("oauth access:", tok["access_token"])

# audit
app.audits.write_entry("smoke", actor_id=uid, details={"ok": True}, ip="127.0.0.1")
print("audit rows:", len(app.audits.recent(5)))

app.users.set_active(uid, False)

print("done")
PY