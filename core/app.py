"""Application container. Wires settings, db, crypto, logging, audit, health,
sessions, csrf, rate limits, and the aiohttp application.
"""


from __future__ import annotations

from pathlib import Path

from dataclasses import dataclass

from aiohttp import web


APP_SETTINGS: web.AppKey = web.AppKey("settings")
APP_USERS: web.AppKey = web.AppKey("users")
APP_ROLES: web.AppKey = web.AppKey("roles")
APP_SESSIONS: web.AppKey = web.AppKey("sessions")
APP_RATE_LIMITS: web.AppKey = web.AppKey("rate_limits")

from core.app_keys import (
    APP_SETTINGS, APP_USERS, APP_ROLES, APP_SESSIONS, APP_RATE_LIMITS,
)

from auth.passwords import PasswordHasherService
from auth.roles import RoleSeeder
from auth.totp import TOTP
from config.settings import Settings
from core.health import HealthCheck
from core.middleware import (
    error_middleware,
    make_csrf_middleware,
    make_rate_limit_middleware,
    make_session_middleware,
    request_id_middleware,
    security_headers_middleware,
)
from core.ratelimit import RateLimitService
from core.router import Router
from core.session import SessionService
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
from web.routes.health import HealthRoutes
from web.routes.public import PublicRoutes
from web.template_engine import TemplateEngine
from web.view import View

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
    rate_limits_repo: RateLimitRepository

    passwords: PasswordHasherService
    totp: TOTP
    roles: RoleSeeder

    session_service: SessionService
    rate_limit_service: RateLimitService
    router: Router
    web_app: web.Application

    templates: TemplateEngine
    view: View

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
        rate_limits_repo = RateLimitRepository(db, crypto)

        passwords = PasswordHasherService()
        totp = TOTP()
        roles = RoleSeeder(db)
        roles.seed()

        session_service = SessionService(
            sessions=sessions,
            cookie_name=settings.cookie_name,
            cookie_secure=settings.cookie_secure,
            cookie_samesite=settings.cookie_samesite,
            ttl_seconds=settings.session_ttl,
        )
        rate_limit_service = RateLimitService(rate_limits_repo)
        router = Router()

        web_app = web.Application(
            middlewares=[
                error_middleware,
                security_headers_middleware,
                request_id_middleware,
                make_session_middleware,      # factory
                make_csrf_middleware,         # factory
                make_rate_limit_middleware,   # factory
            ],
            client_max_size=2 * 1024 * 1024,
        )
        web_app[APP_SETTINGS] = settings
        web_app[APP_USERS] = users
        web_app[APP_ROLES] = roles
        web_app[APP_SESSIONS] = session_service
        web_app[APP_RATE_LIMITS] = rate_limit_service

        templates = TemplateEngine(settings.project_root / "web" / "templates")
        view = View(templates)

        web_app.router.add_static(
            "/static/",
            path=str(settings.project_root / "web" / "static"),
            name="static",
        )

        health_routes = HealthRoutes(health)
        health_routes.register(router)

        public_routes = PublicRoutes(view)
        public_routes.register(router)

        # Register the accumulated routes on the aiohttp app
        router.apply(web_app)

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
            rate_limits_repo=rate_limits_repo,
            passwords=passwords,
            totp=totp,
            roles=roles,
            session_service=session_service,
            rate_limit_service=rate_limit_service,
            router=router,
            web_app=web_app,
            templates=templates,
            view=view,
        )

    def finalize_routes(self) -> None:
        self.router.apply(self.web_app)