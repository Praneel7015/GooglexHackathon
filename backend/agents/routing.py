"""
Routing Agent — Maps issue type + ward to the correct civic agency.
Uses issue_routing.json config and Supabase agencies/ward_officers tables.
"""

import json
import logging
import time
from pathlib import Path

from agents.base import AgentInput, AgentOutput, BaseAgent
from db.client import get_agencies, get_ward_officer

logger = logging.getLogger("nammacity.agents.routing")

_ROUTING_FILE = Path(__file__).parent.parent / "db" / "issue_routing.json"

# Cached routing table and agencies
_routing_table: dict | None = None
_agencies_cache: list[dict] = []
_agencies_cache_ts: float = 0.0
_CACHE_TTL = 60.0  # seconds


def _load_routing_table() -> dict:
    """Load issue -> agency routing from JSON config."""
    global _routing_table
    if _routing_table is None:
        _routing_table = json.loads(_ROUTING_FILE.read_text())
    return _routing_table


async def _get_cached_agencies() -> list[dict]:
    """Get agencies with 60-second cache."""
    global _agencies_cache, _agencies_cache_ts
    now = time.time()
    if not _agencies_cache or (now - _agencies_cache_ts) > _CACHE_TTL:
        _agencies_cache = await get_agencies()
        _agencies_cache_ts = now
    return _agencies_cache


def _find_agency(agencies: list[dict], name: str) -> dict | None:
    """Find agency by name."""
    for a in agencies:
        if a["name"] == name:
            return a
    return None


class RoutingAgent(BaseAgent):
    """Route complaints to the correct civic agency."""

    def __init__(self) -> None:
        super().__init__(
            name="RoutingAgent",
            description="Maps issue type + ward to correct civic agency from 30+",
        )

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        issue_type: str = agent_input.data.get("issue_type", "other")
        ward_number: int | None = agent_input.data.get("ward_number")

        # Load routing config
        routing = _load_routing_table()
        route = routing.get(issue_type, routing.get("other", {}))

        # Get agencies from DB (cached)
        agencies = await _get_cached_agencies()

        primary_name = route.get("primary", "BBMP")
        secondary_name = route.get("secondary")

        primary = _find_agency(agencies, primary_name)
        secondary = _find_agency(agencies, secondary_name) if secondary_name else None

        # Get ward officer
        officer = None
        if ward_number:
            officer = await get_ward_officer(ward_number)

        return AgentOutput(
            agent_name=self.name,
            success=True,
            data={
                "primary_agency": {
                    "id": primary["id"] if primary else None,
                    "name": primary_name,
                    "department": route.get("department", "General"),
                    "twitter_handle": primary.get("twitter_handle") if primary else None,
                    "email_pattern": primary.get("email_pattern") if primary else None,
                },
                "secondary_agency": {
                    "name": secondary_name,
                    "twitter_handle": secondary.get("twitter_handle") if secondary else None,
                } if secondary else None,
                "ward_officer": {
                    "name": officer.get("officer_name"),
                    "email": officer.get("email"),
                    "phone": officer.get("phone"),
                } if officer else None,
                "twitter_handle": primary.get("twitter_handle") if primary else None,
                "email": officer.get("email") if officer else (
                    primary.get("email_pattern") if primary else None
                ),
            },
        )
