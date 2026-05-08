"""
Tests for db/client.py.
Uses unittest.mock to patch the Supabase client so tests run without
a live Supabase instance.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from db.client import (
    get_client,
    insert_complaint,
    get_complaints_in_radius,
    get_complaints_by_ward,
    update_complaint_status,
    get_agencies,
)


def _make_complaint(
    lat: float = 12.9716,
    lng: float = 77.5946,
    ward: int = 95,
    issue: str = "pothole",
) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "description": f"Test {issue}",
        "photo_url": None,
        "voice_note_url": None,
        "location": f"SRID=4326;POINT({lng} {lat})",
        "ward_number": ward,
        "zone": "East",
        "agency_id": None,
        "issue_type": issue,
        "severity": 3,
        "status": "open",
        "cluster_id": None,
        "created_at": "2026-05-08T00:00:00+00:00",
        "updated_at": "2026-05-08T00:00:00+00:00",
    }


@pytest.fixture
def mock_supabase():
    """Patch the Supabase client singleton."""
    mock_client = MagicMock()
    with patch("db.client._client", mock_client):
        with patch("db.client.get_client", return_value=mock_client):
            yield mock_client


@pytest.mark.asyncio
async def test_connection(mock_supabase: MagicMock) -> None:
    """Test that client singleton returns a client object."""
    client = get_client()
    assert client is not None


@pytest.mark.asyncio
async def test_insert_complaint(mock_supabase: MagicMock) -> None:
    """Test inserting a complaint and retrieving it."""
    fake = _make_complaint()

    # Mock: insert returns the row
    mock_supabase.table.return_value.insert.return_value.execute.return_value = (
        MagicMock(data=[fake])
    )

    result = await insert_complaint(
        description="Test pothole",
        lat=12.9716,
        lng=77.5946,
        ward_number=95,
        issue_type="pothole",
    )

    assert result["id"] == fake["id"]
    assert result["issue_type"] == "pothole"
    assert result["ward_number"] == 95
    assert result["status"] == "open"
    mock_supabase.table.assert_called_with("complaints")


@pytest.mark.asyncio
async def test_get_complaints_in_radius(mock_supabase: MagicMock) -> None:
    """
    Insert 5 complaints around MSRIT (12.9716, 77.5946).
    3 within 500m, 2 outside. Query should return 3.
    """
    # 3 nearby complaints (within ~200m of center)
    nearby = [
        _make_complaint(lat=12.9716, lng=77.5946),
        _make_complaint(lat=12.9720, lng=77.5950),
        _make_complaint(lat=12.9712, lng=77.5940),
    ]

    # Mock RPC returns only the 3 nearby ones
    mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=nearby)

    results = await get_complaints_in_radius(lat=12.9716, lng=77.5946, radius_meters=500.0)

    assert len(results) == 3
    mock_supabase.rpc.assert_called_once_with(
        "get_complaints_in_radius",
        {"lat": 12.9716, "lng": 77.5946, "radius_m": 500.0},
    )


@pytest.mark.asyncio
async def test_get_complaints_by_ward(mock_supabase: MagicMock) -> None:
    """Test fetching complaints by ward number."""
    ward_95 = [_make_complaint(ward=95), _make_complaint(ward=95)]

    mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = (
        MagicMock(data=ward_95)
    )

    results = await get_complaints_by_ward(95)
    assert len(results) == 2
    assert all(c["ward_number"] == 95 for c in results)


@pytest.mark.asyncio
async def test_update_complaint_status(mock_supabase: MagicMock) -> None:
    """Test updating complaint status."""
    updated = _make_complaint()
    updated["status"] = "resolved"

    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = (
        MagicMock(data=[updated])
    )

    result = await update_complaint_status(updated["id"], "resolved")
    assert result["status"] == "resolved"


@pytest.mark.asyncio
async def test_get_agencies(mock_supabase: MagicMock) -> None:
    """Test fetching agencies list."""
    agencies = [
        {"id": str(uuid.uuid4()), "name": "BBMP", "twitter_handle": "@BBMPCOMM"},
        {"id": str(uuid.uuid4()), "name": "BESCOM", "twitter_handle": "@bescomofficial"},
    ]

    mock_supabase.table.return_value.select.return_value.execute.return_value = (
        MagicMock(data=agencies)
    )

    results = await get_agencies()
    assert len(results) == 2
    assert results[0]["name"] == "BBMP"
