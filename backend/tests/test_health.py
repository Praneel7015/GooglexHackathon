import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
async def test_health() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/health")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "nammacity-backend"


@pytest.mark.asyncio
async def test_info() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v1/info")

    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == "0.1.0"
    assert "reporter" in data["agents"]
    assert len(data["agents"]) == 10
