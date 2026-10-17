"""Route registry. Handlers are class methods or free functions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable

from aiohttp import web

Handler = Callable[[web.Request], Awaitable[web.StreamResponse]]


@dataclass
class Route:
    method: str
    path: str
    handler: Handler
    name: str | None = None


class Router:
    """Collects routes and applies them to an aiohttp app."""

    def __init__(self) -> None:
        self._routes: list[Route] = []

    def add(self, method: str, path: str, handler: Handler, name: str | None = None) -> None:
        self._routes.append(Route(method.upper(), path, handler, name))

    def get(self, path: str, handler: Handler, name: str | None = None) -> None:
        self.add("GET", path, handler, name)

    def post(self, path: str, handler: Handler, name: str | None = None) -> None:
        self.add("POST", path, handler, name)

    def put(self, path: str, handler: Handler, name: str | None = None) -> None:
        self.add("PUT", path, handler, name)

    def delete(self, path: str, handler: Handler, name: str | None = None) -> None:
        self.add("DELETE", path, handler, name)

    def apply(self, app: web.Application) -> None:
        for r in self._routes:
            app.router.add_route(r.method, r.path, r.handler, name=r.name)