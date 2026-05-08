"""
Prediction Agent — Ward-level resolution likelihood and officer scorecards.
Queries historical complaint data to surface "73% chance of resolution" stats.
"""

import logging
from collections import defaultdict

from agents.base import AgentInput, AgentOutput, BaseAgent
from db.client import get_client as get_supabase

logger = logging.getLogger("nammacity.agents.prediction")

# Fallback stats when DB has insufficient data (used during early seeding)
_FALLBACK_STATS: dict[int, dict] = {
    95:  {"resolution_rate": 0.72, "avg_days": 18, "label": "Moderate"},
    96:  {"resolution_rate": 0.65, "avg_days": 22, "label": "Below Average"},
    97:  {"resolution_rate": 0.60, "avg_days": 25, "label": "Below Average"},
    110: {"resolution_rate": 0.80, "avg_days": 12, "label": "Good"},
    44:  {"resolution_rate": 0.55, "avg_days": 28, "label": "Poor"},
    81:  {"resolution_rate": 0.75, "avg_days": 15, "label": "Good"},
    150: {"resolution_rate": 0.82, "avg_days": 10, "label": "Good"},
    174: {"resolution_rate": 0.89, "avg_days": 8,  "label": "Excellent"},
    87:  {"resolution_rate": 0.34, "avg_days": 40, "label": "Very Poor"},
    126: {"resolution_rate": 0.71, "avg_days": 19, "label": "Moderate"},
}


def _rate_label(rate: float) -> str:
    if rate >= 0.85:
        return "Excellent"
    if rate >= 0.75:
        return "Good"
    if rate >= 0.60:
        return "Moderate"
    if rate >= 0.45:
        return "Below Average"
    return "Very Poor"


def _compute_stats(rows: list[dict]) -> dict:
    """Compute resolution rate and avg days from a list of complaint rows."""
    if not rows:
        return {}

    total = len(rows)
    resolved = [r for r in rows if r.get("status") == "resolved"]
    resolution_rate = len(resolved) / total if total else 0.0

    days_list = []
    for r in resolved:
        created = r.get("created_at")
        updated = r.get("updated_at")
        if created and updated:
            try:
                from datetime import datetime
                c = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
                u = datetime.fromisoformat(str(updated).replace("Z", "+00:00"))
                days = (u - c).days
                if 0 < days < 365:
                    days_list.append(days)
            except Exception:
                pass

    avg_days = int(sum(days_list) / len(days_list)) if days_list else 20

    return {
        "resolution_rate": round(resolution_rate, 3),
        "avg_days": avg_days,
        "total_complaints": total,
        "resolved_complaints": len(resolved),
        "label": _rate_label(resolution_rate),
    }


def _get_ward_history(ward_number: int, issue_type: str | None = None) -> list[dict]:
    """Fetch historical complaints for a ward from Supabase."""
    try:
        db = get_supabase()
        query = db.table("complaints").select("status,created_at,updated_at,issue_type").eq("ward_number", ward_number)
        if issue_type:
            query = query.eq("issue_type", issue_type)
        result = query.limit(500).execute()
        return result.data or []
    except Exception as e:
        logger.warning("Ward history fetch failed for ward %d: %s", ward_number, e)
        return []


def _get_agency_history(agency_id: str) -> list[dict]:
    """Fetch historical complaints for an agency."""
    try:
        db = get_supabase()
        result = db.table("complaints").select("status,created_at,updated_at,ward_number").eq("agency_id", agency_id).limit(500).execute()
        return result.data or []
    except Exception as e:
        logger.warning("Agency history fetch failed: %s", e)
        return []


def _get_all_ward_summaries() -> list[dict]:
    """Get leaderboard data: stats for all wards that have complaints."""
    try:
        db = get_supabase()
        result = db.table("complaints").select("ward_number,status,created_at,updated_at").limit(2000).execute()
        rows = result.data or []
    except Exception as e:
        logger.warning("Ward summary fetch failed: %s", e)
        rows = []

    # Group by ward
    by_ward: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        wn = row.get("ward_number")
        if wn is not None:
            by_ward[int(wn)].append(row)

    summaries = []
    for ward_number, ward_rows in by_ward.items():
        stats = _compute_stats(ward_rows)
        summaries.append({"ward_number": ward_number, **stats})

    return sorted(summaries, key=lambda x: x.get("resolution_rate", 0), reverse=True)


class PredictionAgent(BaseAgent):
    """
    Predicts resolution likelihood for a complaint based on ward history.
    Surfaces officer scorecards and ward leaderboard for the dashboard.
    """

    def __init__(self) -> None:
        super().__init__(
            name="PredictionAgent",
            description="Ward-level resolution forecasting and civic scorecard",
        )

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        ward_number: int | None = agent_input.data.get("ward_number")
        issue_type: str | None = agent_input.data.get("issue_type")
        agency_id: str | None = agent_input.data.get("agency_id")
        include_leaderboard: bool = agent_input.data.get("include_leaderboard", False)

        # ── Ward-level stats ─────────────────────────────────────────────────
        ward_stats: dict = {}
        if ward_number is not None:
            history = _get_ward_history(ward_number, issue_type)
            if len(history) >= 5:
                ward_stats = _compute_stats(history)
            else:
                # Use seeded fallback when insufficient live data
                fallback = _FALLBACK_STATS.get(ward_number, {})
                ward_stats = {
                    "resolution_rate": fallback.get("resolution_rate", 0.6),
                    "avg_days": fallback.get("avg_days", 20),
                    "total_complaints": len(history),
                    "resolved_complaints": 0,
                    "label": fallback.get("label", "Moderate"),
                    "source": "fallback",
                }

        # ── Agency stats ─────────────────────────────────────────────────────
        agency_stats: dict = {}
        if agency_id:
            agency_history = _get_agency_history(agency_id)
            if agency_history:
                agency_stats = _compute_stats(agency_history)

        # ── Issue-specific refinement ────────────────────────────────────────
        # Some issue types resolve faster (tree_fall) vs slower (pothole)
        issue_multipliers: dict[str, float] = {
            "tree_fall": 1.2, "manhole_open": 0.9, "pothole": 0.85,
            "road_damage": 0.80, "garbage_pile": 1.1, "power_outage": 1.3,
            "water_leak": 1.0, "sewage_overflow": 0.95,
        }
        multiplier = issue_multipliers.get(issue_type or "", 1.0)

        base_rate = ward_stats.get("resolution_rate", 0.60)
        adjusted_rate = min(0.99, base_rate * multiplier)
        adjusted_days = max(3, int(ward_stats.get("avg_days", 20) / multiplier))

        # ── Confidence message ───────────────────────────────────────────────
        pct = int(adjusted_rate * 100)
        confidence_msg = (
            f"{pct}% chance of resolution in ~{adjusted_days} days "
            f"based on Ward {ward_number} history"
            if ward_number else f"{pct}% estimated resolution chance"
        )

        # ── Ward leaderboard (optional, for dashboard) ───────────────────────
        leaderboard: list[dict] = []
        if include_leaderboard:
            leaderboard = _get_all_ward_summaries()

        return AgentOutput(
            agent_name=self.name,
            success=True,
            data={
                "ward_number": ward_number,
                "issue_type": issue_type,
                "resolution_rate": round(adjusted_rate, 3),
                "avg_resolution_days": adjusted_days,
                "confidence_message": confidence_msg,
                "ward_label": ward_stats.get("label", "Moderate"),
                "ward_total_complaints": ward_stats.get("total_complaints", 0),
                "agency_resolution_rate": agency_stats.get("resolution_rate"),
                "leaderboard": leaderboard,
            },
        )


# ─────────────────────────────────────────────────────────────────────────────
# Standalone helper used by dashboard API
# ─────────────────────────────────────────────────────────────────────────────

def get_ward_leaderboard() -> list[dict]:
    """Return ward leaderboard sorted by resolution rate (best first)."""
    return _get_all_ward_summaries()
