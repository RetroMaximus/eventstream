"""Rotating file + console logger factory."""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

from config.settings import Settings


class LoggingSetup:
    FORMAT = "%(asctime)s %(levelname)-8s %(name)s %(message)s"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def configure(self) -> logging.Logger:
        settings = self._settings
        root = logging.getLogger()
        root.setLevel(settings.log_level.upper())

        if root.handlers:
            return root

        formatter = logging.Formatter(self.FORMAT)

        console = logging.StreamHandler()
        console.setFormatter(formatter)
        root.addHandler(console)

        file_path: Path = settings.log_dir / "eventstream.log"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=settings.log_max_bytes,
            backupCount=settings.log_backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

        audit_path = settings.log_dir / "audit.log"
        audit_handler = logging.handlers.RotatingFileHandler(
            audit_path,
            maxBytes=settings.log_max_bytes,
            backupCount=settings.log_backup_count,
            encoding="utf-8",
        )
        audit_handler.setFormatter(formatter)
        audit_logger = logging.getLogger("eventstream.audit")
        audit_logger.addHandler(audit_handler)
        audit_logger.propagate = False

        return root

