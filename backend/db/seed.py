"""
Seed script for NammaCity database.
Loads agencies and ward officers from JSON files.
Idempotent — safe to run multiple times (upserts by unique key).

Usage:
    python db/seed.py
"""

import json
import sys
from pathlib import Path

# Add parent dir so we can import config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from supabase import create_client

SEED_DIR = Path(__file__).parent / "seed_data"


def seed_agencies(client) -> int:
    """Load agencies from JSON. Upserts by name."""
    data = json.loads((SEED_DIR / "agencies.json").read_text())
    count = 0
    for agency in data:
        client.table("agencies").upsert(
            agency, on_conflict="name"
        ).execute()
        count += 1
    print(f"  Seeded {count} agencies")
    return count


def seed_ward_officers(client) -> int:
    """Load ward officers from JSON. Links to BBMP agency."""
    data = json.loads((SEED_DIR / "ward_officers.json").read_text())

    # Look up BBMP agency id for ward officers
    bbmp = (
        client.table("agencies")
        .select("id")
        .eq("name", "BBMP")
        .execute()
    )
    bbmp_id = bbmp.data[0]["id"] if bbmp.data else None

    count = 0
    for officer in data:
        row = {**officer, "agency_id": bbmp_id}
        client.table("ward_officers").upsert(
            row, on_conflict="ward_number"
        ).execute()
        count += 1
    print(f"  Seeded {count} ward officers")
    return count


def main() -> None:
    if not settings.supabase_url or not settings.supabase_key:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        sys.exit(1)

    print(f"Connecting to Supabase: {settings.supabase_url[:40]}...")
    client = create_client(settings.supabase_url, settings.supabase_key)

    print("Seeding agencies...")
    seed_agencies(client)

    print("Seeding ward officers...")
    seed_ward_officers(client)

    print("Done.")


if __name__ == "__main__":
    main()
