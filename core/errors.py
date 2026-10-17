"""Typed errors and JSON error rendering."""

from __future__ import annotations

import json
from dataclasses import dataclass

from aiohttp import web


@dataclass
class HttpError(Exception):
    status: int
    code: str
    message: str
    details: dict | None = None

    def to_payload(self) -> dict:
        payload = {"error": self.code, "message": self.message}
        if self.details:
            payload["details"] = self.details
        return payload


class BadRequest(HttpError):
    def __init__(self, message: str = "Bad request", details: dict | None = None) -> None:
        super().__init__(400, "bad_request", message, details)


class Unauthorized(HttpError):
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(401, "unauthorized", message)


class Forbidden(HttpError):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(403, "forbidden", message)


class NotFound(HttpError):
    def __init__(self, message: str = "Not found") -> None:
        super().__init__(404, "not_found", message)


class Conflict(HttpError):
    def __init__(self, message: str = "Conflict") -> None:
        super().__init__(409, "conflict", message)


class RateLimited(HttpError):
    def __init__(self, retry_after: int = 60) -> None:
        super().__init__(429, "rate_limited", "Too many requests",
                         {"retry_after": retry_after})


class CsrfFailed(HttpError):
    def __init__(self) -> None:
        super().__init__(403, "csrf_failed", "CSRF token missing or invalid")


def json_error(err: HttpError) -> web.Response:
    body = json.dumps(err.to_payload(), separators=(",", ":"))
    headers = {"Content-Type": "application/json"}
    if err.status == 429 and err.details and "retry_after" in err.details:
        headers["Retry-After"] = str(err.details["retry_after"])
    return web.Response(status=err.status, text=body, headers=headers)