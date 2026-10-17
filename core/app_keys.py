"""Typed aiohttp AppKey constants shared across the codebase."""

from __future__ import annotations

from aiohttp import web

APP_SETTINGS: web.AppKey = web.AppKey("settings")
APP_USERS: web.AppKey = web.AppKey("users")
APP_ROLES: web.AppKey = web.AppKey("roles")
APP_SESSIONS: web.AppKey = web.AppKey("sessions")
APP_RATE_LIMITS: web.AppKey = web.AppKey("rate_limits")