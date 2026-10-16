"""Application container. Wires settings, db, crypto, logging, audit, health."""

from __future__ import annotations

from dataclasses import dataclass

from config.settings import Settings
from core.health import HealthCheck
from db.connection import Database
from db.migrations.runner import MigrationRunner
from ops.audit import AuditLog
from ops.logging import LoggingSetup
from security.crypto import CryptoBox
from security.keyring import Keyring


@dataclass
class Application:
    settings: Settings
    db: Database
    migrations: MigrationRunner
    keyring: Keyring
    crypto: CryptoBox
    audit: AuditLog
    health: HealthCheck

    @classmethod
    def build(cls) -> "Application":
        settings = Settings.load()
        settings.ensure_dirs()

        LoggingSetup(settings).configure()

        db = Database(settings.db_path)
        migrations = MigrationRunner(db)
        migrations.upgrade()

        keyring = Keyring(settings.master_key)
        crypto = CryptoBox(keyring.master)

        audit = AuditLog(db, crypto)
        health = HealthCheck(db, migrations)

        return cls(
            settings=settings,
            db=db,
            migrations=migrations,
            keyring=keyring,
            crypto=crypto,
            audit=audit,
            health=health,
        )

