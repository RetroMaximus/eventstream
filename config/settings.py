
"""Immutable settings object built from Env."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from config.env import Env


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    app_debug: bool
    host: str
    port: int

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

    master_key: str
    session_secret: str
    session_ttl: int

    log_level: str
    log_max_bytes: int
    log_backup_count: int

    @classmethod
    def load(cls, env: Env | None = None) -> "Settings":
        env = env or Env()
        root = Path(env.str("EVENTSTREAM_ROOT", ".") or ".").resolve()
        var = env.path("EVENTSTREAM_VAR_DIR", str(root / "var"))
        return cls(
            app_name=env.str("EVENTSTREAM_APP_NAME", "eventstream") or "eventstream",
            app_env=env.str("EVENTSTREAM_ENV", "development") or "development",
            app_debug=env.bool("EVENTSTREAM_DEBUG", True),
            host=env.str("EVENTSTREAM_HOST", "0.0.0.0") or "0.0.0.0",
            port=env.int("EVENTSTREAM_PORT", 8080),

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

            master_key=env.required("EVENTSTREAM_MASTER_KEY"),
            session_secret=env.required("EVENTSTREAM_SESSION_SECRET"),
            session_ttl=env.int("EVENTSTREAM_SESSION_TTL", 86400),

            log_level=env.str("EVENTSTREAM_LOG_LEVEL", "INFO") or "INFO",
            log_max_bytes=env.int("EVENTSTREAM_LOG_MAX_BYTES", 5_242_880),
            log_backup_count=env.int("EVENTSTREAM_LOG_BACKUP_COUNT", 5),
        )

    def ensure_dirs(self) -> None:
        for path in (
            self.var_dir, self.log_dir, self.db_path.parent,
            self.events_dir, self.uploads_dir, self.screenshots_dir,
            self.clips_dir, self.backups_dir, self.cache_dir, self.run_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

