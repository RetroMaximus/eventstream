"""Smoke test: build the aiohttp app and hit /healthz and /."""

import pytest
from aiohttp.test_utils import TestClient, TestServer

from core.app import Application


@pytest.mark.asyncio
async def test_healthz_and_home():
    app = Application.build()
    async with TestClient(TestServer(app.web_app)) as client:
        resp = await client.get("/healthz")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] in ("ok", "degraded")

        resp = await client.get("/")
        assert resp.status == 200
        text = await resp.text()
        assert "eventstream" in text