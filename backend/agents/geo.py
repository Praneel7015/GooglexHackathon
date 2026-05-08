"""
Geo Agent — Location intelligence.
Extracts GPS from EXIF, reverse-geocodes via Nominatim,
maps to BBMP ward using ward boundaries.
"""

import asyncio
import io
import json
import logging
from pathlib import Path

import httpx
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

from agents.base import AgentInput, AgentOutput, BaseAgent

logger = logging.getLogger("nammacity.agents.geo")

# Nominatim rate limit: 1 req/sec
_nominatim_semaphore = asyncio.Semaphore(1)

# Ward boundaries loaded once at module level
_ward_boundaries: list[dict] | None = None
_WARD_FILE = Path(__file__).parent.parent / "db" / "bangalore_wards.json"


def load_ward_boundaries() -> list[dict]:
    """Load ward GeoJSON into memory. Called once at startup."""
    global _ward_boundaries
    if _ward_boundaries is not None:
        return _ward_boundaries

    if _WARD_FILE.exists():
        data = json.loads(_WARD_FILE.read_text())
        _ward_boundaries = data.get("features", data) if isinstance(data, dict) else data
    else:
        # Fallback: hardcoded wards near MSRIT for demo
        _ward_boundaries = _demo_wards()

    logger.info("Loaded %d ward boundaries", len(_ward_boundaries))
    return _ward_boundaries


def _demo_wards() -> list[dict]:
    """Hardcoded wards covering major Bangalore areas for demo."""
    return [
        {"ward_number": 4, "name": "Yelahanka", "zone": "Yelahanka",
         "mla": "Yelahanka", "bbox": [77.56, 13.08, 77.62, 13.12]},
        {"ward_number": 18, "name": "Hebbal", "zone": "Yelahanka",
         "mla": "Hebbal", "bbox": [77.57, 13.02, 77.62, 13.06]},
        {"ward_number": 44, "name": "Peenya", "zone": "Dasarahalli",
         "mla": "Dasarahalli", "bbox": [77.49, 13.01, 77.54, 13.05]},
        {"ward_number": 80, "name": "Shivajinagar", "zone": "East",
         "mla": "Shivajinagar", "bbox": [77.59, 12.97, 77.62, 13.00]},
        {"ward_number": 86, "name": "Mahadevapura", "zone": "Mahadevapura",
         "mla": "Mahadevapura", "bbox": [77.68, 12.96, 77.72, 13.00]},
        {"ward_number": 95, "name": "Malleshwaram", "zone": "West",
         "mla": "Malleshwaram", "bbox": [77.55, 12.97, 77.58, 13.00]},
        {"ward_number": 96, "name": "Rajajinagar", "zone": "West",
         "mla": "Rajajinagar", "bbox": [77.53, 12.96, 77.56, 12.99]},
        {"ward_number": 110, "name": "Yeshwanthpur", "zone": "West",
         "mla": "Yeshwanthpur", "bbox": [77.53, 12.99, 77.56, 13.02]},
        {"ward_number": 118, "name": "Indiranagar", "zone": "East",
         "mla": "Shantinagar", "bbox": [77.63, 12.97, 77.66, 13.00]},
        {"ward_number": 126, "name": "Jayanagar", "zone": "South",
         "mla": "Jayanagar", "bbox": [77.58, 12.92, 77.61, 12.95]},
        {"ward_number": 134, "name": "BTM Layout", "zone": "Bommanahalli",
         "mla": "BTM Layout", "bbox": [77.60, 12.90, 77.63, 12.93]},
        {"ward_number": 145, "name": "Whitefield", "zone": "Mahadevapura",
         "mla": "Mahadevapura", "bbox": [77.73, 12.95, 77.77, 12.99]},
        {"ward_number": 150, "name": "HSR Layout", "zone": "Bommanahalli",
         "mla": "Bommanahalli", "bbox": [77.63, 12.90, 77.66, 12.93]},
        {"ward_number": 151, "name": "Koramangala", "zone": "South",
         "mla": "BTM Layout", "bbox": [77.61, 12.93, 77.64, 12.96]},
        {"ward_number": 167, "name": "Banashankari", "zone": "South",
         "mla": "Basavanagudi", "bbox": [77.56, 12.91, 77.59, 12.94]},
        {"ward_number": 174, "name": "JP Nagar", "zone": "South",
         "mla": "Jayanagar", "bbox": [77.57, 12.89, 77.60, 12.92]},
        {"ward_number": 188, "name": "Bommanahalli", "zone": "Bommanahalli",
         "mla": "Bommanahalli", "bbox": [77.61, 12.88, 77.64, 12.91]},
    ]


def _extract_gps_from_exif(photo_bytes: bytes) -> tuple[float, float] | None:
    """Extract GPS coordinates from photo EXIF data."""
    try:
        image = Image.open(io.BytesIO(photo_bytes))
        exif_data = image._getexif()
        if not exif_data:
            return None

        gps_info = {}
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == "GPSInfo":
                for key in value:
                    gps_tag = GPSTAGS.get(key, key)
                    gps_info[gps_tag] = value[key]

        if "GPSLatitude" not in gps_info:
            return None

        lat = _dms_to_decimal(gps_info["GPSLatitude"])
        lng = _dms_to_decimal(gps_info["GPSLongitude"])

        if gps_info.get("GPSLatitudeRef") == "S":
            lat = -lat
        if gps_info.get("GPSLongitudeRef") == "W":
            lng = -lng

        return (lat, lng)
    except Exception:
        return None


def _dms_to_decimal(dms: tuple) -> float:
    """Convert (degrees, minutes, seconds) to decimal degrees."""
    d, m, s = [float(x) for x in dms]
    return d + m / 60.0 + s / 3600.0


async def _reverse_geocode(lat: float, lng: float) -> dict:
    """Reverse-geocode via OpenStreetMap Nominatim. Respects 1 req/sec."""
    async with _nominatim_semaphore:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={"lat": lat, "lon": lng, "format": "json", "zoom": 18},
                headers={"User-Agent": "NammaCity/1.0"},
                timeout=10.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "address": data.get("display_name", ""),
                    "suburb": data.get("address", {}).get("suburb", ""),
                    "city_district": data.get("address", {}).get("city_district", ""),
                }
    return {}


def _find_ward(lat: float, lng: float) -> dict | None:
    """Find which ward a point falls in using bounding boxes."""
    wards = load_ward_boundaries()
    for ward in wards:
        bbox = ward.get("bbox")
        if bbox and bbox[0] <= lng <= bbox[2] and bbox[1] <= lat <= bbox[3]:
            return ward
    return None


class GeoAgent(BaseAgent):
    """Extract location from photo and map to BBMP ward."""

    def __init__(self) -> None:
        super().__init__(
            name="GeoAgent",
            description="Location intelligence — GPS, geocoding, ward mapping",
        )

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        photo_bytes: bytes = agent_input.data.get("photo_bytes", b"")
        fallback_lat: float | None = agent_input.data.get("fallback_lat")
        fallback_lng: float | None = agent_input.data.get("fallback_lng")

        # Step 1: Try EXIF GPS
        coords = _extract_gps_from_exif(photo_bytes) if photo_bytes else None
        source = "exif"

        # Step 2: Fallback to provided coordinates
        if coords is None and fallback_lat is not None and fallback_lng is not None:
            coords = (fallback_lat, fallback_lng)
            source = "fallback"

        if coords is None:
            return AgentOutput(
                agent_name=self.name,
                success=False,
                error="No location available — no EXIF GPS and no fallback coordinates",
            )

        lat, lng = coords

        # Step 3: Reverse geocode
        geo_data = await _reverse_geocode(lat, lng)

        # Step 4: Map to ward
        ward = _find_ward(lat, lng)

        return AgentOutput(
            agent_name=self.name,
            success=True,
            data={
                "lat": lat,
                "lng": lng,
                "source": source,
                "ward_number": ward["ward_number"] if ward else None,
                "ward_name": ward["name"] if ward else None,
                "zone": ward["zone"] if ward else None,
                "mla_constituency": ward["mla"] if ward else None,
                "address": geo_data.get("address", ""),
            },
        )
