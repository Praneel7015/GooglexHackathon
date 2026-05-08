"""
Async Supabase client and helper functions for NammaCity DB operations.
"""

from supabase import create_client, Client

from config import settings

_client: Client | None = None


def get_client() -> Client:
    """Get or create the Supabase client singleton."""
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client


async def insert_complaint(
    description: str,
    lat: float,
    lng: float,
    ward_number: int | None = None,
    zone: str | None = None,
    agency_id: str | None = None,
    issue_type: str | None = None,
    severity: int = 3,
    photo_url: str | None = None,
    voice_note_url: str | None = None,
) -> dict:
    """Insert a new complaint with PostGIS point geometry."""
    client = get_client()
    point_wkt = f"SRID=4326;POINT({lng} {lat})"

    row = {
        "description": description,
        "location": point_wkt,
        "ward_number": ward_number,
        "zone": zone,
        "agency_id": agency_id,
        "issue_type": issue_type,
        "severity": severity,
        "photo_url": photo_url,
        "voice_note_url": voice_note_url,
        "status": "open",
    }
    result = client.table("complaints").insert(row).execute()
    return result.data[0] if result.data else {}


async def get_complaints_in_radius(
    lat: float,
    lng: float,
    radius_meters: float = 500.0,
    issue_type: str | None = None,
) -> list[dict]:
    """Get complaints within a radius using PostGIS ST_DWithin."""
    client = get_client()
    params: dict = {"lat": lat, "lng": lng, "radius_m": radius_meters}
    if issue_type:
        params["filter_issue_type"] = issue_type
    result = client.rpc("get_complaints_in_radius", params).execute()
    return result.data or []


async def get_complaints_by_ward(ward_number: int) -> list[dict]:
    """Get all complaints for a specific ward."""
    client = get_client()
    result = (
        client.table("complaints")
        .select("*")
        .eq("ward_number", ward_number)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


async def update_complaint_status(complaint_id: str, status: str) -> dict:
    """Update a complaint's status."""
    client = get_client()
    result = (
        client.table("complaints")
        .update({"status": status, "updated_at": "now()"})
        .eq("id", complaint_id)
        .execute()
    )
    return result.data[0] if result.data else {}


async def get_agencies() -> list[dict]:
    """Get all agencies."""
    client = get_client()
    result = client.table("agencies").select("*").execute()
    return result.data or []


async def get_ward_officer(ward_number: int) -> dict | None:
    """Get the officer for a specific ward."""
    client = get_client()
    result = (
        client.table("ward_officers")
        .select("*")
        .eq("ward_number", ward_number)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None
