"""aiohttp middleware: error, security headers, request id, session, csrf, rate limit."""

from __future__ import annotations

import logging
import uuid

from aiohttp import web

from config.constants import (
    RATE_LIMIT_DEFAULT_MAX,
    RATE_LIMIT_DEFAULT_WINDOW_SECONDS,
)
from core.app_keys import (
    APP_RATE_LIMITS,
    APP_ROLES,
    APP_SESSIONS,
    APP_USERS,
)
from core.csrf import CsrfService
from core.errors import (
    CsrfFailed,
    HttpError,
    RateLimited,
    json_error,
)
from core.ratelimit import RateLimitService
from core.request_context import REQUEST_CTX_KEY, RequestContext
from core.session import SessionService

log = logging.getLogger("eventstream.http")

RATE_LIMIT_POLICY: dict[str, tuple[int, int]] = {
    "*": (RATE_LIMIT_DEFAULT_MAX, RATE_LIMIT_DEFAULT_WINDOW_SECONDS),
    "login_post": (10, 900),
    "register_post": (5, 3600),
    "forgot_password_post": (3, 3600),
    "reset_password_post": (5, 3600),
    "twofa_post": (5, 900),
}

FORM_CONTENT_TYPES = {
    "application/x-www-form-urlencoded",
    "multipart/form-data",
}

EXEMPT_PATHS = {
    "/healthz",
    "/readyz",
}


def _client_ip(request: web.Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    peername = request.transport.get_extra_info("peername") if request.transport else None
    if peername and isinstance(peername, tuple):
        return peername[0]
    return "unknown"


def _is_form(request: web.Request) -> bool:
    ctype = request.headers.get("Content-Type", "")
    base = ctype.split(";")[0].strip().lower()
    return base in FORM_CONTENT_TYPES


async def _read_form_cached(request: web.Request) -> dict:
    cached = request.get("_eventstream_form")
    if cached is not None:
        return cached
    data: dict = {}
    if _is_form(request):
        try:
            post = await request.post()
            data = {k: post[k] for k in post.keys()}
        except Exception:  # noqa: BLE001
            data = {}
    request["_eventstream_form"] = data
    return data


async def read_form(request: web.Request) -> dict:
    """Public helper so handlers get the same cached form data."""
    return await _read_form_cached(request)


@web.middleware
async def error_middleware(request: web.Request, handler):
    try:
        return await handler(request)
    except HttpError as err:
        return json_error(err)
    except web.HTTPException as err:
        return web.Response(status=err.status, text=err.reason or "HTTP error")
    except Exception:
        log.exception("unhandled error")
        return web.Response(status=500, text="Internal server error")


@web.middleware
async def security_headers_middleware(request: web.Request, handler):
    response = await handler(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; img-src 'self' data:; "
        "style-src 'self' 'unsafe-inline'; script-src 'self'; "
        "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'",
    )
    return response


@web.middleware
async def request_id_middleware(request: web.Request, handler):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    ctx = RequestContext(
        request_id=request_id,
        client_ip=_client_ip(request),
        user_agent=request.headers.get("User-Agent", ""),
    )
    request[REQUEST_CTX_KEY] = ctx
    response = await handler(request)
    response.headers["X-Request-ID"] = request_id
    return response


@web.middleware
async def session_middleware(request: web.Request, handler):
    app = request.app
    session_service: SessionService = app[APP_SESSIONS]
    users = app[APP_USERS]
    roles = app[APP_ROLES]

    ctx: RequestContext = request[REQUEST_CTX_KEY]
    session_id = request.cookies.get(session_service.cookie_name)
    if session_id:
        row = session_service.load(session_id)
        if row is not None:
            ctx.session_id = session_id
            ctx.csrf_token = row.get("csrf_token")
            ctx.user_id = row.get("user_id")
            ctx.is_authenticated = True
            user = users.by_id(ctx.user_id)
            if user is not None:
                ctx.user = user
                roles_map = roles.roles_for_user(ctx.user_id)
                ctx.roles = roles_map.get(0, set())
                ctx.event_roles = {k: v for k, v in roles_map.items() if k != 0}
    return await handler(request)


@web.middleware
async def csrf_middleware(request: web.Request, handler):
    if CsrfService.is_safe_method(request.method):
        return await handler(request)
    if request.path in EXEMPT_PATHS:
        return await handler(request)
    if request.path.startswith("/auth/") and request.path.endswith("/callback"):
        return await handler(request)

    ctx: RequestContext = request[REQUEST_CTX_KEY]
    form = await _read_form_cached(request)
    provided = CsrfService.extract_from_request(request, form)
    if not CsrfService.verify(provided, ctx.csrf_token):
        log.warning("csrf rejected path=%s ip=%s", request.path, ctx.client_ip)
        raise CsrfFailed()
    return await handler(request)


@web.middleware
async def rate_limit_middleware(request: web.Request, handler):
    app = request.app
    rl: RateLimitService = app[APP_RATE_LIMITS]

    ctx: RequestContext = request[REQUEST_CTX_KEY]
    route_name = request.match_info.route.name or "*"
    window, max_hits = RATE_LIMIT_POLICY.get(route_name, RATE_LIMIT_POLICY["*"])

    key = f"ip:{ctx.client_ip}"
    result = rl.check(key, window, max_hits)
    if not result.allowed:
        raise RateLimited(retry_after=window)

    if ctx.user_id:
        user_key = f"user:{ctx.user_id}"
        user_result = rl.check(user_key, window, max_hits)
        if not user_result.allowed:
            raise RateLimited(retry_after=window)

    return await handler(request)