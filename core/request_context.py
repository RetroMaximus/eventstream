"""Per-request context attached to aiohttp requests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aiohttp import web

@dataclass
class RequestContext:
    request_id: str = ""
    user_id: int | None = None
    user: dict | None = None
    session_id: str | None = None
    csrf_token: str | None = None
    roles: set = field(default_factory=set)
    event_roles: dict = field(default_factory=dict)
    client_ip: str = ""
    user_agent: str = ""
    is_authenticated: bool = False
    extras: dict[str, Any] = field(default_factory=dict)


REQUEST_CTX_KEY: web.AppKey = web.AppKey("eventstream_ctx")