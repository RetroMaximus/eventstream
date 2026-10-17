"""CSRF token issuance and verification."""

from __future__ import annotations

import hmac

from aiohttp import web

from config.constants import (
    CSRF_FORM_FIELD,
    CSRF_HEADER,
    CSRF_SAFE_METHODS,
)


class CsrfService:
    """Checks CSRF tokens on state-changing requests.

    Token comes from either the X-CSRF-Token header or the csrf_token form
    field. The expected value is the session's csrf_token. Comparison uses
    constant time.
    """

    @staticmethod
    def is_safe_method(method: str) -> bool:
        return method.upper() in CSRF_SAFE_METHODS

    @staticmethod
    def extract_from_request(request: web.Request, form: dict | None = None) -> str | None:
        header_token = request.headers.get(CSRF_HEADER)
        if header_token:
            return header_token.strip()
        if form and CSRF_FORM_FIELD in form:
            value = form[CSRF_FORM_FIELD]
            if isinstance(value, str):
                return value.strip()
        return None

    @staticmethod
    def verify(provided: str | None, expected: str | None) -> bool:
        if not provided or not expected:
            return False
        return hmac.compare_digest(provided, expected)