"""
Seed ~200 synthetic historical complaints around Bangalore for demo.
Inserts into Supabase (PostGIS) and upserts embeddings into Qdrant.
"""

import asyncio
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from supabase import create_client

# ─────────────────────────────────────────────────────────
# Bangalore demo zones: ward number, name, zone, bbox
# ─────────────────────────────────────────────────────────

WARDS = [
    {"ward_number": 95,  "name": "Malleshwaram",      "zone": "West",  "bbox": [77.550, 12.970, 77.580, 13.000]},
    {"ward_number": 96,  "name": "Rajajinagar",        "zone": "West",  "bbox": [77.530, 12.960, 77.560, 12.990]},
    {"ward_number": 97,  "name": "Subramanyanagar",    "zone": "West",  "bbox": [77.540, 12.950, 77.570, 12.980]},
    {"ward_number": 110, "name": "Yeshwanthpur",       "zone": "North", "bbox": [77.530, 12.990, 77.560, 13.020]},
    {"ward_number": 44,  "name": "Hebbal",             "zone": "North", "bbox": [77.570, 13.020, 77.600, 13.050]},
    {"ward_number": 81,  "name": "Shivajinagar",       "zone": "East",  "bbox": [77.590, 12.980, 77.620, 13.010]},
    {"ward_number": 150, "name": "JP Nagar",           "zone": "South", "bbox": [77.580, 12.890, 77.610, 12.920]},
    {"ward_number": 174, "name": "BTM Layout",         "zone": "South", "bbox": [77.600, 12.910, 77.630, 12.940]},
    {"ward_number": 87,  "name": "Koramangala",        "zone": "East",  "bbox": [77.610, 12.930, 77.640, 12.960]},
    {"ward_number": 126, "name": "Indiranagar",        "zone": "East",  "bbox": [77.630, 12.960, 77.660, 12.990]},
]

# Heavier distribution near MSRIT (Ward 95/96/97) for demo cluster effect
WARD_WEIGHTS = [30, 20, 20, 10, 5, 5, 5, 3, 1, 1]

ISSUE_TYPES = [
    "pothole", "road_damage", "garbage_pile", "sanitation", "streetlight_out",
    "broken_footpath", "open_drain", "sewage_overflow", "water_leak",
    "electrical_wire_dangerous", "power_outage", "tree_fall",
    "flooding", "manhole_open", "stray_animals",
]

ISSUE_WEIGHTS = [25, 15, 15, 10, 8, 7, 5, 4, 4, 2, 2, 1, 1, 1, 0]

DESCRIPTIONS: dict[str, list[str]] = {
    "pothole": [
        "Large pothole near {ward} main road causing accidents.",
        "Deep pothole outside {ward} bus stop, vehicles swerving dangerously.",
        "Multiple potholes on {ward} road, especially bad after rain.",
        "Pothole near MSRIT gate blocking cycle lane.",
        "Pothole on main road has been there for 3 months, getting bigger.",
    ],
    "road_damage": [
        "Road completely broken after last monsoon, no repair done.",
        "Huge crack on {ward} road, dangerous for two-wheelers.",
        "Road surface damaged near {ward} flyover.",
    ],
    "garbage_pile": [
        "Garbage not collected for 5 days near {ward} market.",
        "Overflowing dustbin near {ward} park, smell spreading to houses.",
        "Illegal dumping site growing near {ward} ground.",
        "Mixed waste pile near residential area, dengue risk.",
    ],
    "sanitation": [
        "Open sewage on {ward} road, children playing nearby.",
        "No sanitation pickup since last week.",
    ],
    "streetlight_out": [
        "Streetlight not working on {ward} main road for 2 weeks.",
        "Three consecutive streetlights down near {ward} junction.",
        "Dark stretch on {ward} road, safety risk at night.",
    ],
    "broken_footpath": [
        "Footpath completely broken near {ward}, pedestrians on road.",
        "Tiles missing from footpath, senior citizens falling.",
    ],
    "open_drain": [
        "Open drain near {ward} school, health hazard for children.",
        "Drain overflowing onto road during heavy rain.",
    ],
    "sewage_overflow": [
        "Sewage overflowing on {ward} road, unbearable smell.",
        "Manhole overflowing after rain near {ward} area.",
    ],
    "water_leak": [
        "Water pipe leaking on {ward} road for 10 days, water wasted.",
        "Broken water main near {ward} junction, road waterlogged.",
    ],
    "electrical_wire_dangerous": [
        "Hanging live wire near {ward} school, extremely dangerous.",
        "Broken electric pole with loose wires on {ward} road.",
    ],
    "power_outage": [
        "Power cut in {ward} area for 6 hours, no update from BESCOM.",
        "Frequent power outages in {ward} every evening.",
    ],
    "tree_fall": [
        "Fallen tree blocking {ward} road, traffic jam.",
        "Old tree fell on compound wall near {ward} park.",
    ],
    "flooding": [
        "Entire {ward} road flooded after 1 hour of rain.",
        "Underpass near {ward} floods every monsoon, nothing done.",
    ],
    "manhole_open": [
        "Open manhole near {ward} school, child fell in yesterday.",
        "Uncovered manhole on {ward} main road at night, very dangerous.",
    ],
    "stray_animals": [
        "Pack of stray dogs attacking pedestrians near {ward}.",
        "Injured stray cow blocking traffic near {ward} junction.",
    ],
}

# Historical resolution patterns per ward (for Prediction Agent)
WARD_RESOLUTION_RATES: dict[int, float] = {
    95: 0.72,   # Malleshwaram — decent
    96: 0.65,
    97: 0.60,
    110: 0.80,  # Yeshwanthpur — better
    44: 0.55,
    81: 0.75,
    150: 0.82,  # JP Nagar — high
    174: 0.89,  # BTM — best
    87: 0.34,   # Koramangala — poor
    126: 0.71,
}

WARD_AVG_DAYS: dict[int, int] = {
    95: 18, 96: 22, 97: 25, 110: 12, 44: 28,
    81: 15, 150: 10, 174: 8, 87: 40, 126: 19,
}


def _random_point(bbox: list[float]) -> tuple[float, float]:
    """Generate a random GPS point within a bounding box [minLng, minLat, maxLng, maxLat]."""
    lng = random.uniform(bbox[0], bbox[2])
    lat = random.uniform(bbox[1], bbox[3])
    return lat, lng


def _random_date(days_back: int = 90) -> datetime:
    """Random datetime within the last N days."""
    offset = random.randint(0, days_back * 24 * 60 * 60)
    return datetime.now(timezone.utc) - timedelta(seconds=offset)


def _build_complaint(ward: dict, agencies: list[dict]) -> dict:
    """Build a single synthetic complaint row."""
    issue_type = random.choices(ISSUE_TYPES, weights=ISSUE_WEIGHTS[:len(ISSUE_TYPES)], k=1)[0]
    lat, lng = _random_point(ward["bbox"])
    created_at = _random_date(90)

    templates = DESCRIPTIONS.get(issue_type, ["Issue reported at {ward}."])
    description = random.choice(templates).format(ward=ward["name"])

    resolution_rate = WARD_RESOLUTION_RATES.get(ward["ward_number"], 0.6)
    avg_days = WARD_AVG_DAYS.get(ward["ward_number"], 20)
    is_resolved = random.random() < resolution_rate
    days_to_resolve = int(random.gauss(avg_days, avg_days * 0.3))

    if is_resolved:
        status = "resolved"
        updated_at = created_at + timedelta(days=max(1, days_to_resolve))
    else:
        status = random.choices(["open", "in_progress"], weights=[70, 30])[0]
        updated_at = created_at + timedelta(days=random.randint(0, 30))

    # Match agency by issue type routing
    agency_id = None
    agency_map = {a["name"]: a.get("id") for a in agencies}
    routing = {
        "pothole": "BBMP", "road_damage": "BBMP", "garbage_pile": "BBMP",
        "sanitation": "BBMP", "streetlight_out": "BBMP", "broken_footpath": "BBMP",
        "open_drain": "BWSSB", "sewage_overflow": "BWSSB", "water_leak": "BWSSB",
        "electrical_wire_dangerous": "BESCOM", "power_outage": "BESCOM",
        "tree_fall": "BBMP", "flooding": "BBMP", "manhole_open": "BWSSB",
        "stray_animals": "BBMP",
    }
    agency_name = routing.get(issue_type, "BBMP")
    agency_id = agency_map.get(agency_name)

    return {
        "id": str(uuid.uuid4()),
        "description": description,
        "location": f"SRID=4326;POINT({lng} {lat})",
        "ward_number": ward["ward_number"],
        "zone": ward["zone"],
        "agency_id": agency_id,
        "issue_type": issue_type,
        "severity": random.randint(2, 5),
        "status": status,
        "photo_url": None,
        "voice_note_url": None,
        "created_at": created_at.isoformat(),
        "updated_at": updated_at.isoformat(),
        # stored for seeding Qdrant later
        "_lat": lat,
        "_lng": lng,
    }


def seed_complaints_supabase(client, complaints: list[dict]) -> int:
    """Batch-insert complaints into Supabase. Returns count inserted."""
    # Strip internal keys before inserting
    rows = [{k: v for k, v in c.items() if not k.startswith("_")} for c in complaints]
    batch_size = 50
    inserted = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        client.table("complaints").insert(batch).execute()
        inserted += len(batch)
        print(f"  Inserted {inserted}/{len(rows)} complaints…")
    return inserted


async def seed_complaints_qdrant(complaints: list[dict]) -> int:
    """Embed each complaint description and upsert into Qdrant."""
    # Import here to keep script runnable even if qdrant/gemini are offline
    from agents.gemini_client import embed_text
    from integrations.qdrant_client import ensure_collection, upsert_complaint

    ensure_collection()
    upserted = 0
    for complaint in complaints:
        try:
            embedding = await embed_text(complaint["description"])
            await upsert_complaint(
                complaint_id=complaint["id"],
                embedding=embedding,
                metadata={
                    "complaint_id": complaint["id"],
                    "issue_type": complaint["issue_type"],
                    "ward_number": complaint["ward_number"],
                    "lat": complaint["_lat"],
                    "lng": complaint["_lng"],
                },
            )
            upserted += 1
            if upserted % 20 == 0:
                print(f"  Embedded {upserted}/{len(complaints)} into Qdrant…")
        except Exception as e:
            print(f"  Qdrant upsert failed for {complaint['id']}: {e}")
    return upserted


async def main() -> None:
    if not settings.supabase_url or not settings.supabase_key:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        sys.exit(1)

    client = create_client(settings.supabase_url, settings.supabase_key)

    # Fetch agency IDs from DB so we can FK-link correctly
    agencies_result = client.table("agencies").select("id,name").execute()
    agencies = agencies_result.data or []
    if not agencies:
        print("WARNING: No agencies found. Run db/seed.py first.")

    print("Building 200 synthetic complaints…")
    random.seed(42)  # deterministic output for reproducible demos
    complaints: list[dict] = []
    for ward, weight in zip(WARDS, WARD_WEIGHTS):
        count = round(200 * weight / sum(WARD_WEIGHTS))
        for _ in range(count):
            complaints.append(_build_complaint(ward, agencies))

    # Pad/trim to exactly 200
    while len(complaints) < 200:
        ward = random.choices(WARDS, weights=WARD_WEIGHTS, k=1)[0]
        complaints.append(_build_complaint(ward, agencies))
    complaints = complaints[:200]

    print(f"Seeding {len(complaints)} complaints into Supabase…")
    inserted = seed_complaints_supabase(client, complaints)
    print(f"  Done — {inserted} rows inserted.")

    if settings.qdrant_url or True:  # always attempt (falls back to in-memory)
        print("Seeding embeddings into Qdrant…")
        upserted = await seed_complaints_qdrant(complaints)
        print(f"  Done — {upserted} vectors upserted.")

    print("\nSeed complete.")
    print(f"  Ward distribution:")
    from collections import Counter
    counter = Counter(c["ward_number"] for c in complaints)
    for ward in WARDS:
        n = counter[ward["ward_number"]]
        print(f"    Ward {ward['ward_number']:>3} {ward['name']:<20} — {n:>3} complaints")


if __name__ == "__main__":
    asyncio.run(main())
