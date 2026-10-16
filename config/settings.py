"""Immutable settings object built from Env."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from config.constants import DEFAULT_COOKIE_NAME
from config.env import Env


@dataclass(frozen=True)
class Settings:
    # ------------------------------------------------------------------
    # App
    # ------------------------------------------------------------------
    app_name: str
    app_env: str
    app_debug: bool
    host: str
    port: int

    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------
    project_root: Path
    var_dir: Path
    log_dir: Path
    db_path: Path
    events_dir: Path
    uploads_dir: Path
    screenshots_dir: Path
    clips_dir: Path
    backups_dir: Path
    cache_dir: Path
    run_dir: Path

    # ------------------------------------------------------------------
    # Secrets
    # ------------------------------------------------------------------
    master_key: str
    session_secret: str
    session_ttl: int

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    log_level: str
    log_max_bytes: int
    log_backup_count: int

    # ------------------------------------------------------------------
    # Sessions and cookies
    # ------------------------------------------------------------------
    cookie_name: str
    cookie_secure: bool
    cookie_samesite: str

    # ------------------------------------------------------------------
    # Rate limiting
    # ------------------------------------------------------------------
    rate_limit_enabled: bool

    # ------------------------------------------------------------------
    # Public URL
    # ------------------------------------------------------------------
    public_base_url: str

    # ------------------------------------------------------------------
    # SMTP
    # ------------------------------------------------------------------
    smtp_host: str | None
    smtp_port: int
    smtp_user: str | None
    smtp_password: str | None
    smtp_from: str
    smtp_tls: bool
    smtp_enabled: bool

    # ------------------------------------------------------------------
    # OAuth
    # ------------------------------------------------------------------
    twitch_client_id: str | None
    twitch_client_secret: str | None
    twitch_redirect_uri: str | None
    twitch_scopes: tuple[str, ...] = field(default_factory=tuple)

    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str | None = None
    google_scopes: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def load(cls, env: Env | None = None) -> "Settings":
        env = env or Env()
        root = Path(env.str("EVENTSTREAM_ROOT", ".") or ".").resolve()
        var = env.path("EVENTSTREAM_VAR_DIR", str(root / "var"))

        app_env = env.str("EVENTSTREAM_ENV", "development") or "development"
        default_secure = "true" if app_env == "production" else "false"

        twitch_scopes = tuple(
            s.strip()
            for s in (env.str("EVENTSTREAM_TWITCH_SCOPES", "") or "").split(",")
            if s.strip()
        )
        google_scopes = tuple(
            s.strip()
            for s in (env.str("EVENTSTREAM_GOOGLE_SCOPES", "") or "").split(",")
            if s.strip()
        )

        return cls(
            # app
            app_name=env.str("EVENTSTREAM_APP_NAME", "eventstream") or "eventstream",
            app_env=app_env,
            app_debug=env.bool("EVENTSTREAM_DEBUG", app_env != "production"),
            host=env.str("EVENTSTREAM_HOST", "0.0.0.0") or "0.0.0.0",
            port=env.int("EVENTSTREAM_PORT", 8080),

            # paths
            project_root=root,
            var_dir=var,
            log_dir=var / "log",
            db_path=var / "db" / "eventstream.sqlite3",
            events_dir=var / "events",
            uploads_dir=var / "uploads",
            screenshots_dir=var / "uploads" / "screenshots",
            clips_dir=var / "uploads" / "clips",
            backups_dir=var / "backups",
            cache_dir=var / "cache",
            run_dir=var / "run",

            # secrets
            master_key=env.required("EVENTSTREAM_MASTER_KEY"),
            session_secret=env.required("EVENTSTREAM_SESSION_SECRET"),
            session_ttl=env.int("EVENTSTREAM_SESSION_TTL", 86400),

            # logging
            log_level=env.str("EVENTSTREAM_LOG_LEVEL", "INFO") or "INFO",
            log_max_bytes=env.int("EVENTSTREAM_LOG_MAX_BYTES", 5_242_880),
            log_backup_count=env.int("EVENTSTREAM_LOG_BACKUP_COUNT", 5),

            # cookies
            cookie_name=env.str("EVENTSTREAM_COOKIE_NAME", DEFAULT_COOKIE_NAME)
            or DEFAULT_COOKIE_NAME,
            cookie_secure=env.bool("EVENTSTREAM_SECURE_COOKIES", default_secure == "true"),
            cookie_samesite=env.str("EVENTSTREAM_COOKIE_SAMESITE", "Lax") or "Lax",

            # rate limiting
            rate_limit_enabled=env.bool("EVENTSTREAM_RATE_LIMIT_ENABLED", True),

            # public URL
            public_base_url=env.str(
                "EVENTSTREAM_PUBLIC_BASE_URL", "http://localhost:8080"
            ) or "http://localhost:8080",

            # SMTP
            smtp_host=env.str("EVENTSTREAM_SMTP_HOST") or None,
            smtp_port=env.int("EVENTSTREAM_SMTP_PORT", 587),
            smtp_user=env.str("EVENTSTREAM_SMTP_USER") or None,
            smtp_password=env.str("EVENTSTREAM_SMTP_PASSWORD") or None,
            smtp_from=env.str("EVENTSTREAM_SMTP_FROM", "eventstream@localhost")
            or "eventstream@localhost",
            smtp_tls=env.bool("EVENTSTREAM_SMTP_TLS", True),
            smtp_enabled=env.bool(
                "EVENTSTREAM_SMTP_ENABLED",
                bool(env.str("EVENTSTREAM_SMTP_HOST")),
            ),

            # OAuth
            twitch_client_id=env.str("EVENTSTREAM_TWITCH_CLIENT_ID") or None,
            twitch_client_secret=env.str("EVENTSTREAM_TWITCH_CLIENT_SECRET") or None,
            twitch_redirect_uri=env.str("EVENTSTREAM_TWITCH_REDIRECT_URI") or None,
            twitch_scopes=twitch_scopes,
            google_client_id=env.str("EVENTSTREAM_GOOGLE_CLIENT_ID") or None,
            google_client_secret=env.str("EVENTSTREAM_GOOGLE_CLIENT_SECRET") or None,
            google_redirect_uri=env.str("EVENTSTREAM_GOOGLE_REDIRECT_URI") or None,
            google_scopes=google_scopes,
        )

    def ensure_dirs(self) -> None:
        for path in (
            self.var_dir, self.log_dir, self.db_path.parent,
            self.events_dir, self.uploads_dir, self.screenshots_dir,
            self.clips_dir, self.backups_dir, self.cache_dir, self.run_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)