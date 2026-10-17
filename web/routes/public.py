"""Public routes. Home page placeholder in 1E-1; auth forms in 1E-2."""

from __future__ import annotations

from aiohttp import web

from web.view import View


class PublicRoutes:
    def __init__(self, view: View) -> None:
        self._view = view

    async def home(self, request: web.Request) -> web.Response:
        return self._view.html(request, "index.html")

    def register(self, router) -> None:
        router.get("/", self.home, name="home")