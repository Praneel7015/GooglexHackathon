"""
Async Supabase client and repository helpers for NammaCity DB operations.
Covers complaints, clusters, submissions, escalations, agencies, and ward officers.
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


# ─────────────────────────────────────────────────────────────────────────────
# Complaint queries (dashboard + detail)
# ─────────────────────────────────────────────────────────────────────────────

async def get_complaint_by_id(complaint_id: str) -> dict | None:
    """Fetch a single complaint by UUID."""
    client = get_client()
    result = (
        client.table("complaints")
        .select("*")
        .eq("id", complaint_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


async def get_all_complaints(
    status: str | None = None,
    ward_number: int | None = None,
    issue_type: str | None = None,
    limit: int = 500,
) -> list[dict]:
    """
    Fetch complaints with optional filters.
    Returns up to `limit` rows ordered newest-first.
    """
    client = get_client()
    query = client.table("complaints").select("*").order("created_at", desc=True).limit(limit)
    if status:
        query = query.eq("status", status)
    if ward_number is not None:
        query = query.eq("ward_number", ward_number)
    if issue_type:
        query = query.eq("issue_type", issue_type)
    result = query.execute()
    return result.data or []


async def get_map_complaints() -> list[dict]:
    """
    Fetch all geo-located complaints for the dashboard map via PostGIS RPC.
    Returns id, issue_type, severity, status, ward_number, lat, lng, cluster_id.
    """
    client = get_client()
    try:
        result = client.rpc("get_open_complaints_map", {}).execute()
        return result.data or []
    except Exception:
        # Fallback: fetch without geometry extraction if RPC not yet deployed
        result = client.table("complaints").select(
            "id,issue_type,severity,status,ward_number,zone,cluster_id,created_at"
        ).limit(500).execute()
        return result.data or []


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard aggregate stats
# ─────────────────────────────────────────────────────────────────────────────

async def get_dashboard_stats() -> dict:
    """
    Compute aggregate stats for the public dashboard.
    Returns totals, status breakdown, and top issue types.
    """
    client = get_client()
    try:
        all_rows = client.table("complaints").select("status,issue_type,ward_number,severity").limit(5000).execute()
        rows = all_rows.data or []
    except Exception:
        rows = []

    total = len(rows)
    open_count = sum(1 for r in rows if r.get("status") == "open")
    in_progress = sum(1 for r in rows if r.get("status") == "in_progress")
    resolved = sum(1 for r in rows if r.get("status") == "resolved")

    from collections import Counter
    issue_counter = Counter(r.get("issue_type") for r in rows if r.get("issue_type"))
    top_issues = [{"issue_type": k, "count": v} for k, v in issue_counter.most_common(5)]

    ward_counter = Counter(r.get("ward_number") for r in rows if r.get("ward_number") is not None)
    hotspot_wards = [{"ward_number": k, "count": v} for k, v in ward_counter.most_common(5)]

    return {
        "total_complaints": total,
        "open": open_count,
        "in_progress": in_progress,
        "resolved": resolved,
        "resolution_rate": round(resolved / total, 3) if total else 0.0,
        "top_issue_types": top_issues,
        "hotspot_wards": hotspot_wards,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Cluster queries
# ─────────────────────────────────────────────────────────────────────────────

async def get_active_clusters() -> list[dict]:
    """Fetch all active crowd-validation clusters."""
    client = get_client()
    result = (
        client.table("clusters")
        .select("*")
        .eq("status", "active")
        .order("created_at", desc=True)
        .limit(200)
        .execute()
    )
    return result.data or []


# ─────────────────────────────────────────────────────────────────────────────
# Escalation queries
# ─────────────────────────────────────────────────────────────────────────────

async def get_escalations_for_complaint(complaint_id: str) -> list[dict]:
    """Fetch the full escalation timeline for a complaint, ordered by day."""
    client = get_client()
    result = (
        client.table("escalations")
        .select("day,action,status,draft_text,scheduled_for,executed_at")
        .eq("complaint_id", complaint_id)
        .order("day")
        .execute()
    )
    return result.data or []


async def upload_photo(complaint_id: str, photo_bytes: bytes) -> str | None:
    """Upload photo to Supabase Storage and return public URL."""
    try:
        client = get_client()
        path = f"complaints/{complaint_id}.jpg"
        client.storage.from_("photos").upload(
            path, photo_bytes, {"content-type": "image/jpeg"}
        )
        url = client.storage.from_("photos").get_public_url(path)
        return url
    except Exception as e:
        import logging
        logging.getLogger("nammacity.db").warning("Photo upload failed: %s", e)
        return None
