
"""
install_init.py
---------------
Creates the full eventstream directory tree and required runtime folders.
Idempotent: safe to run on every application start.

Called from:
  - setup.sh (first clone)
  - main.py (before app boot)

Keeps the original shell layout, plus runtime data dirs.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


class ProjectLayout:
    """Declarative description of the project tree."""

    # Source tree (tracked in git, mirrors the shell script)
    SOURCE_DIRS: tuple[str, ...] = (
        "config",
        "core",
        "db",
        "db/migrations",
        "db/models",
        "db/repositories",
        "db/json_store",
        "auth",
        "auth/providers",
        "domain",
        "domain/events",
        "domain/tournaments",
        "domain/matches",
        "domain/stats",
        "domain/sponsors",
        "domain/charity",
        "domain/adbreak",
        "domain/alerts",
        "integrations",
        "integrations/obs",
        "integrations/twitch",
        "integrations/youtube",
        "integrations/google_forms",
        "integrations/smtp",
        "integrations/uptime",
        "live",
        "chat",
        "widgets",
        "widgets/templates",
        "web",
        "web/routes",
        "web/templates",
        "web/static",
        "web/static/css"
        "web/static/js"
        "web/i18n",
        "web/theme",
        "security",
        "ops",
        "scripts",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/e2e",
        "tests/fixtures",
        "deploy",
        "deploy/systemd",
        "docs",
    )

    # Runtime dirs (not tracked, created on disk)
    RUNTIME_DIRS: tuple[str, ...] = (
        "var",
        "var/log",
        "var/db",
        "var/uploads",
        "var/uploads/screenshots",
        "var/uploads/clips",
        "var/backups",
        "var/events",
        "var/cache",
        "var/run",
    )

    # __init__.py for every Python package
    PACKAGE_DIRS: tuple[str, ...] = tuple(
        d for d in SOURCE_DIRS
        if not d.startswith(("deploy", "docs", "tests/fixtures"))
        and d not in ("web/templates", "web/static", "web/i18n", "web/theme")
    )


class LayoutInstaller:
    """Creates directories and package markers."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def ensure_dirs(self, dirs: tuple[str, ...]) -> list[Path]:
        created: list[Path] = []
        for rel in dirs:
            path = self.root / rel
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                created.append(path)
        return created

    def ensure_package_init(self, dirs: tuple[str, ...]) -> list[Path]:
        created: list[Path] = []
        for rel in dirs:
            path = self.root / rel / "__init__.py"
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    '"""eventstream package."""\n',
                    encoding="utf-8",
                )
                created.append(path)
        return created

    def ensure_gitkeep(self, dirs: tuple[str, ...]) -> list[Path]:
        created: list[Path] = []
        for rel in dirs:
            path = self.root / rel / ".gitkeep"
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
                created.append(path)
        return created

    def run(self) -> None:
        print(f"[install_init] root: {self.root}")
        src = self.ensure_dirs(ProjectLayout.SOURCE_DIRS)
        run = self.ensure_dirs(ProjectLayout.RUNTIME_DIRS)
        pkg = self.ensure_package_init(ProjectLayout.PACKAGE_DIRS)
        keep = self.ensure_gitkeep(("var", "var/log", "var/db", "var/events",
                                    "var/uploads", "var/backups", "var/cache",
                                    "var/run"))
        print(f"[install_init] source dirs created:  {len(src)}")
        print(f"[install_init] runtime dirs created: {len(run)}")
        print(f"[install_init] __init__.py created:  {len(pkg)}")
        print(f"[install_init] .gitkeep created:     {len(keep)}")
        print("[install_init] ok")


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    root = Path(argv[0]) if argv else Path(__file__).resolve().parent
    LayoutInstaller(root).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


