"""Small helpers for returning HTML or JSON from handlers."""

from __future__ import annotations

from aiohttp import web

from core.request_context import REQUEST_CTX_KEY
from web.template_engine import TemplateEngine


class View:
    """Common response helpers bound to a template engine."""

    def __init__(self, templates: TemplateEngine) -> None:
        self.templates = templates

    def html(
        self,
        request: web.Request,
        template: str,
        status: int = 200,
        headers: dict | None = None,
        **context,
    ) -> web.Response:
        ctx = request.get(REQUEST_CTX_KEY)
        base_context = {
            "csrf_token": getattr(ctx, "csrf_token", None) if ctx else None,
            "current_user": getattr(ctx, "user", None) if ctx else None,
            "is_authenticated": bool(getattr(ctx, "is_authenticated", False))
            if ctx
            else False,
            "request_id": getattr(ctx, "request_id", "") if ctx else "",
            "flash": request.get("flash"),
        }
        base_context.update(context)
        body = self.templates.render(template, **base_context)
        return web.Response(
            status=status,
            text=body,
            content_type="text/html",
            headers=headers,
        )

    @staticmethod
    def json(payload: dict, status: int = 200) -> web.Response:
        return web.json_response(payload, status=status)