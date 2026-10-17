"""Health endpoints. JSON. No CSRF, no session."""

from __future__ import annotations

from aiohttp import web

from core.request_context import REQUEST_CTX_KEY


class HealthRoutes:
    def __init__(self, health: HealthCheck) -> None:
        self._health = health

    async def live(self, request: web.Request) -> web.Response:
        report = self._health.live()
        return web.json_response(
            {"status": report.status, "ts": report.ts, "checks": report.checks}
        )

    async def ready(self, request: web.Request) -> web.Response:
        report = self._health.ready()
        return web.json_response(
            {"status": report.status, "ts": report.ts, "checks": report.checks},
            status=200 if report.status == "ok" else 503,
        )

    def register(self, router) -> None:
        router.get("/healthz", self.live, name="health_live")
        router.get("/readyz", self.ready, name="health_ready")