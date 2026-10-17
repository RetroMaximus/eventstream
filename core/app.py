"""Application container. Wires settings, db, crypto, logging, audit, health."""

from __future__ import annotations

from dataclasses import dataclass

from auth.passwords import PasswordHasherService
from auth.roles import RoleSeeder
from auth.totp import TOTP
from config.settings import Settings
from core.health import HealthCheck
from db.connection import Database
from db.migrations.runner import MigrationRunner
from db.repositories.audit_repo import AuditRepository
from db.repositories.oauth_repo import OAuthRepository
from db.repositories.rate_limit_repo import RateLimitRepository
from db.repositories.session_repo import SessionRepository
from db.repositories.user_repo import UserRepository
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

    users: UserRepository
    sessions: SessionRepository
    oauth: OAuthRepository
    audits: AuditRepository
    rate_limits: RateLimitRepository

    passwords: PasswordHasherService
    totp: TOTP
    roles: RoleSeeder

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

        users = UserRepository(db, crypto)
        sessions = SessionRepository(db, crypto)
        oauth = OAuthRepository(db, crypto)
        audits = AuditRepository(db, crypto)
        rate_limits = RateLimitRepository(db, crypto)

        passwords = PasswordHasherService()
        totp = TOTP()
        roles = RoleSeeder(db)
        roles.seed()

        return cls(
            settings=settings,
            db=db,
            migrations=migrations,
            keyring=keyring,
            crypto=crypto,
            audit=audit,
            health=health,
            users=users,
            sessions=sessions,
            oauth=oauth,
            audits=audits,
            rate_limits=rate_limits,
            passwords=passwords,
            totp=totp,
            roles=roles,
        )