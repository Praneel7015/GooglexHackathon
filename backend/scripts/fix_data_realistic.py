"""
Update existing complaints with realistic Bangalore ward data,
mixed statuses, and proper distributions.

Usage:
    cd backend && source venv/bin/activate
    python scripts/fix_data_realistic.py
"""

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from supabase import create_client

# Real BBMP wards with actual names and zones
BANGALORE_WARDS = [
    {"ward_number": 4, "name": "Yelahanka Satellite Town", "zone": "Yelahanka"},
    {"ward_number": 18, "name": "Hebbal", "zone": "Yelahanka"},
    {"ward_number": 27, "name": "Vidyaranyapura", "zone": "Yelahanka"},
    {"ward_number": 44, "name": "Peenya Industrial Area", "zone": "Dasarahalli"},
    {"ward_number": 56, "name": "Rajajinagar", "zone": "Rajarajeshwari Nagar"},
    {"ward_number": 65, "name": "Basaveshwaranagar", "zone": "Rajarajeshwari Nagar"},
    {"ward_number": 80, "name": "Shivajinagar", "zone": "East"},
    {"ward_number": 86, "name": "Mahadevapura", "zone": "Mahadevapura"},
    {"ward_number": 95, "name": "Malleshwaram", "zone": "West"},
    {"ward_number": 96, "name": "Rajajinagar", "zone": "West"},
    {"ward_number": 100, "name": "Chamarajpet", "zone": "South"},
    {"ward_number": 110, "name": "Yeshwanthpur", "zone": "West"},
    {"ward_number": 118, "name": "Indiranagar", "zone": "East"},
    {"ward_number": 126, "name": "Jayanagar", "zone": "South"},
    {"ward_number": 134, "name": "BTM Layout", "zone": "Bommanahalli"},
    {"ward_number": 145, "name": "Whitefield", "zone": "Mahadevapura"},
    {"ward_number": 150, "name": "HSR Layout", "zone": "Bommanahalli"},
    {"ward_number": 151, "name": "Koramangala", "zone": "South"},
    {"ward_number": 167, "name": "Banashankari", "zone": "South"},
    {"ward_number": 174, "name": "JP Nagar", "zone": "South"},
    {"ward_number": 188, "name": "Bommanahalli", "zone": "Bommanahalli"},
]

# Status distribution: ~35% open, ~15% in_progress, ~40% resolved, ~10% escalated
STATUS_WEIGHTS = [
    ("open", 35),
    ("in_progress", 15),
    ("resolved", 40),
    ("escalated", 10),
]

# Severity distribution: weighted towards 3-4 (realistic)
SEVERITY_WEIGHTS = [
    (1, 5),
    (2, 15),
    (3, 35),
    (4, 30),
    (5, 15),
]


def pick_weighted(choices):
    items, weights = zip(*choices)
    return random.choices(items, weights=weights, k=1)[0]


def main():
    if not settings.supabase_url:
        print("ERROR: SUPABASE_URL not set")
        sys.exit(1)

    client = create_client(settings.supabase_url, settings.supabase_key)
    random.seed(42)  # deterministic for consistent demo

    # Get all complaints
    result = client.table("complaints").select("id,ward_number").limit(5000).execute()
    complaints = result.data or []
    print(f"Updating {len(complaints)} complaints...")

    for i, c in enumerate(complaints):
        # Assign to a real Bangalore ward
        ward = random.choice(BANGALORE_WARDS)
        status = pick_weighted(STATUS_WEIGHTS)
        severity = pick_weighted(SEVERITY_WEIGHTS)

        update = {
            "ward_number": ward["ward_number"],
            "zone": ward["zone"],
            "status": status,
            "severity": severity,
        }

        client.table("complaints").update(update).eq("id", c["id"]).execute()

        if (i + 1) % 20 == 0:
            print(f"  Updated {i + 1}/{len(complaints)}")

    # Verify final distribution
    result = client.table("complaints").select("status,ward_number,severity").limit(5000).execute()
    rows = result.data or []

    from collections import Counter
    status_dist = Counter(r["status"] for r in rows)
    ward_dist = Counter(r["ward_number"] for r in rows)
    sev_dist = Counter(r["severity"] for r in rows)

    print(f"\nDone! Updated {len(complaints)} complaints.")
    print(f"Status: {dict(status_dist)}")
    print(f"Severity: {dict(sorted(sev_dist.items()))}")
    print(f"Top wards: {dict(ward_dist.most_common(10))}")

    # Also update ward_officers to match real Bangalore wards
    print("\nUpdating ward officers...")
    officers = [
        {"ward_number": 95, "officer_name": "Ramesh Kumar N", "email": "ward95@bbmp.gov.in", "phone": "+919900000095"},
        {"ward_number": 118, "officer_name": "Priya Sharma", "email": "ward118@bbmp.gov.in", "phone": "+919900000118"},
        {"ward_number": 151, "officer_name": "Venkatesh Murthy", "email": "ward151@bbmp.gov.in", "phone": "+919900000151"},
        {"ward_number": 150, "officer_name": "Lakshmi Devi R", "email": "ward150@bbmp.gov.in", "phone": "+919900000150"},
        {"ward_number": 126, "officer_name": "Suresh Babu K", "email": "ward126@bbmp.gov.in", "phone": "+919900000126"},
        {"ward_number": 174, "officer_name": "Deepak Raj M", "email": "ward174@bbmp.gov.in", "phone": "+919900000174"},
        {"ward_number": 134, "officer_name": "Kavitha S", "email": "ward134@bbmp.gov.in", "phone": "+919900000134"},
        {"ward_number": 86, "officer_name": "Nagaraj H", "email": "ward86@bbmp.gov.in", "phone": "+919900000086"},
        {"ward_number": 145, "officer_name": "Anand Gowda", "email": "ward145@bbmp.gov.in", "phone": "+919900000145"},
        {"ward_number": 188, "officer_name": "Fatima Begum", "email": "ward188@bbmp.gov.in", "phone": "+919900000188"},
        {"ward_number": 110, "officer_name": "Manjunath P", "email": "ward110@bbmp.gov.in", "phone": "+919900000110"},
        {"ward_number": 80, "officer_name": "Srinivas Rao", "email": "ward80@bbmp.gov.in", "phone": "+919900000080"},
        {"ward_number": 167, "officer_name": "Chandrika M", "email": "ward167@bbmp.gov.in", "phone": "+919900000167"},
        {"ward_number": 18, "officer_name": "Vijay Lakshmi", "email": "ward18@bbmp.gov.in", "phone": "+919900000018"},
        {"ward_number": 44, "officer_name": "Gopala Krishna", "email": "ward44@bbmp.gov.in", "phone": "+919900000044"},
    ]

    for off in officers:
        client.table("ward_officers").upsert(off, on_conflict="ward_number").execute()

    print(f"  Upserted {len(officers)} ward officers for real Bangalore wards.")
    print("\nAll done! Dashboard will now show realistic Bangalore data.")


if __name__ == "__main__":
    main()
