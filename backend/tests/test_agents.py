"""
Tests for Reporter, Geo, and Routing agents + end-to-end /api/v1/report.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import ASGITransport, AsyncClient

from agents.base import AgentInput
from agents.reporter import ReporterAgent, ISSUE_TYPES
from agents.geo import GeoAgent, _find_ward, load_ward_boundaries
from agents.routing import RoutingAgent
from config import settings

FIXTURES = Path(__file__).parent / "fixtures"

# Skip Gemini-dependent tests if no API key
skip_no_gemini = pytest.mark.skipif(
    not settings.gemini_api_key,
    reason="GEMINI_API_KEY not set",
)


# --- Reporter Agent Tests ---

@skip_no_gemini
@pytest.mark.asyncio
async def test_reporter_classifies_image() -> None:
    """Reporter agent should classify a pothole image."""
    photo = (FIXTURES / "pothole.jpg").read_bytes()
    agent = ReporterAgent()
    result = await agent.execute(AgentInput(data={"photo_bytes": photo}))

    assert result.success
    assert result.data["issue_type"] in ISSUE_TYPES
    assert 1 <= result.data["severity"] <= 5
    assert 0.0 <= result.data["spam_score"] <= 1.0
    assert len(result.data["raw_description"]) > 0


@pytest.mark.asyncio
async def test_reporter_rejects_empty_photo() -> None:
    """Reporter agent returns error with no photo."""
    agent = ReporterAgent()
    result = await agent.execute(AgentInput(data={"photo_bytes": b""}))

    assert not result.success
    assert "No photo" in result.error


# --- Geo Agent Tests ---

@pytest.mark.asyncio
async def test_geo_with_fallback_coords() -> None:
    """Geo agent uses fallback coords when no EXIF GPS."""
    photo = (FIXTURES / "pothole_no_exif.jpg").read_bytes()
    agent = GeoAgent()

    result = await agent.execute(AgentInput(data={
        "photo_bytes": photo,
        "fallback_lat": 12.9716,
        "fallback_lng": 77.5646,
    }))

    assert result.success
    assert result.data["lat"] == 12.9716
    assert result.data["lng"] == 77.5646
    assert result.data["source"] == "fallback"


@pytest.mark.asyncio
async def test_geo_no_location_fails() -> None:
    """Geo agent fails when no EXIF and no fallback."""
    photo = (FIXTURES / "pothole_no_exif.jpg").read_bytes()
    agent = GeoAgent()
    result = await agent.execute(AgentInput(data={"photo_bytes": photo}))

    assert not result.success
    assert "No location" in result.error


@pytest.mark.asyncio
async def test_geo_ward_lookup() -> None:
    """Ward lookup returns correct ward for MSRIT area coords."""
    load_ward_boundaries()
    # 12.98, 77.56 is inside ward 95 bbox [77.55, 12.97, 77.58, 13.00]
    ward = _find_ward(12.98, 77.56)
    assert ward is not None
    assert ward["ward_number"] == 95


# --- Routing Agent Tests ---

_MOCK_AGENCIES = [
    {"id": "a1", "name": "BBMP", "twitter_handle": "@BBMPCOMM", "email_pattern": "jc.{zone}@bbmp.gov.in"},
    {"id": "a2", "name": "BESCOM", "twitter_handle": "@bescomofficial", "email_pattern": "helpdesk@bescom.co.in"},
    {"id": "a3", "name": "BWSSB", "twitter_handle": "@bwssb_official", "email_pattern": "comp@bwssb.gov.in"},
    {"id": "a4", "name": "BMTC", "twitter_handle": "@BMTC_BENGALURU", "email_pattern": "mdbmtc@gmail.com"},
    {"id": "a5", "name": "Bangalore Traffic Police", "twitter_handle": "@blrcitytraffic", "email_pattern": "addlcptraffic-blr@ksp.gov.in"},
]

_MOCK_OFFICER = {"officer_name": "Ramesh Kumar", "email": "ward95@bbmp.gov.in", "phone": "+919900000095"}


@pytest.mark.asyncio
@pytest.mark.parametrize("issue_type,expected_agency", [
    ("pothole", "BBMP"),
    ("water_leak", "BWSSB"),
    ("power_outage", "BESCOM"),
    ("bus_stop_damage", "BMTC"),
    ("traffic_signal_broken", "Bangalore Traffic Police"),
])
async def test_routing_maps_correctly(issue_type: str, expected_agency: str) -> None:
    """Routing agent maps issue types to correct agencies."""
    agent = RoutingAgent()

    with patch("agents.routing.get_agencies", new_callable=AsyncMock, return_value=_MOCK_AGENCIES):
        with patch("agents.routing.get_ward_officer", new_callable=AsyncMock, return_value=_MOCK_OFFICER):
            result = await agent.execute(AgentInput(data={
                "issue_type": issue_type,
                "ward_number": 95,
            }))

    assert result.success
    assert result.data["primary_agency"]["name"] == expected_agency
    assert result.data["ward_officer"]["name"] == "Ramesh Kumar"


# --- End-to-End Test ---

@pytest.mark.asyncio
async def test_report_endpoint_e2e() -> None:
    """
    POST /api/v1/report runs the full pipeline end-to-end.
    ReporterAgent is mocked so the synthetic fixture image doesn't get
    flagged as spam — the test validates pipeline wiring, not Gemini output.
    """
    from main import app
    from agents.base import AgentOutput

    photo_bytes = (FIXTURES / "pothole.jpg").read_bytes()

    mock_reporter_output = AgentOutput(
        agent_name="ReporterAgent",
        success=True,
        data={
            "issue_type": "pothole",
            "severity": 4,
            "spam_score": 0.02,
            "raw_description": "Large pothole near MSRIT gate causing traffic hazard.",
            "transcribed_text": "",
        },
    )

    with patch("main.reporter_agent.execute", new_callable=AsyncMock, return_value=mock_reporter_output):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/report",
                files={"photo": ("pothole.jpg", photo_bytes, "image/jpeg")},
                data={"fallback_lat": "12.9869", "fallback_lng": "77.5519"},
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["reporter"]["issue_type"] in ISSUE_TYPES
    assert 1 <= data["reporter"]["severity"] <= 5
    assert "lat" in data["geo"] or "error" in data["geo"]
    assert "primary_agency" in data["routing"] or "error" in data["routing"]
