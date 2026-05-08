"""
Escalation Agent — 30-day enforcement ladder for unresolved complaints.
Generates day 0/7/14/21/30 actions and persists them in the escalations table.
All draft generation runs in parallel via ADK adk_client.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Callable, Awaitable
from uuid import uuid4

from agents.adk_client import generate_text
from agents.base import AgentInput, AgentOutput, BaseAgent
from db.client import get_client as get_supabase

logger = logging.getLogger("nammacity.agents.escalation")

# ─────────────────────────────────────────────────────────────────────────────
# Escalation ladder definition
# ─────────────────────────────────────────────────────────────────────────────

ESCALATION_LADDER: list[dict] = [
    {
        "day": 0,
        "action": "initial",
        "label": "Initial multi-channel submission",
    },
    {
        "day": 7,
        "action": "councillor_tag",
        "label": "Ward councillor tagged on Twitter",
        "twitter_targets": ["@BBMPCOMM", "@CMofKarnataka"],
    },
    {
        "day": 14,
        "action": "rti",
        "label": "RTI application drafted and ready",
        "twitter_targets": ["@BBMPCOMM", "@CMofKarnataka"],
    },
    {
        "day": 21,
        "action": "mla_media",
        "label": "MLA + local media tagged",
        "twitter_targets": ["@CMofKarnataka", "@TimesofIndia_blr", "@DeccanHerald", "@TheNewsMinute"],
    },
    {
        "day": 30,
        "action": "pil",
        "label": "PIL outline drafted, NGO partners notified",
        "twitter_targets": ["@CMofKarnataka", "@bcpbengaluru", "@ICCCBLR"],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# Draft generators — each returns prompt text only; generation is parallelised
# ─────────────────────────────────────────────────────────────────────────────

def _councillor_tweet_prompt(c: dict) -> str:
    ward = c.get("ward_number", "N/A")
    ward_name = c.get("ward_name", "")
    issue = (c.get("issue_type") or "civic issue").replace("_", " ")
    agency = c.get("agency_name") or "BBMP"
    cid = c["id"]
    return (
        f"Write a firm escalation tweet (max 270 chars). Tone: assertive, cite lack of response.\n"
        f"Issue: {issue} in Ward {ward}"
        + (f" ({ward_name})" if ward_name else "")
        + f".\nAgency: {agency}. Complaint ID: {cid}.\n"
        f"Start with: @BBMPCOMM @CMofKarnataka\n"
        f"End with: #FixBangalore nammacity.in/c/{cid}\n"
        f"Output ONLY the tweet text."
    )


def _rti_prompt(c: dict) -> str:
    ward = c.get("ward_number", "N/A")
    issue = (c.get("issue_type") or "civic issue").replace("_", " ")
    address = c.get("address") or "Bangalore"
    cid = c["id"]
    return (
        f"Draft a short RTI application under Karnataka RTI Act.\n"
        f"Issue: {issue} at Ward {ward}, {address}.\n"
        f"Reference: NammaCity #{cid}.\n"
        f"Request: action-taken report, responsible officer, expected timeline.\n"
        f"Keep it under 200 words. Include RTI Act Section 6 citation."
    )


def _mla_tweet_prompt(c: dict) -> str:
    ward = c.get("ward_number", "N/A")
    issue = (c.get("issue_type") or "civic issue").replace("_", " ")
    cid = c["id"]
    return (
        f"Write an escalation tweet tagging MLA and media (max 270 chars).\n"
        f"Issue unresolved for 21 days: {issue} in Ward {ward}.\n"
        f"Start with: @CMofKarnataka @TimesofIndia_blr @DeccanHerald\n"
        f"End with: #FixBangalore #BangaloreCorruption nammacity.in/c/{cid}\n"
        f"Output ONLY the tweet text."
    )


def _pil_prompt(c: dict) -> str:
    ward = c.get("ward_number", "N/A")
    issue = (c.get("issue_type") or "civic issue").replace("_", " ")
    cid = c["id"]
    return (
        f"Draft a 150-word PIL outline for filing in Karnataka High Court.\n"
        f"Civic issue: {issue} at Ward {ward}, Bangalore. "
        f"Unresolved for 30+ days despite formal RTI.\n"
        f"Reference: NammaCity #{cid}.\n"
        f"Cite: Article 21 (right to life), Karnataka Municipal Corporations Act 1976.\n"
        f"Include: prayer, petitioner description, relief sought."
    )


# Maps action → prompt builder function
_PROMPT_BUILDERS: dict[str, Callable[[dict], str]] = {
    "councillor_tag": _councillor_tweet_prompt,
    "rti":            _rti_prompt,
    "mla_media":      _mla_tweet_prompt,
    "pil":            _pil_prompt,
}

# Char limits per action for tweet-type outputs
_TWEET_ACTIONS = {"councillor_tag", "mla_media"}


async def _generate_draft(action: str, complaint: dict) -> str | None:
    """Generate a single escalation draft. Returns None for 'initial' rung."""
    builder = _PROMPT_BUILDERS.get(action)
    if builder is None:
        return None
    try:
        text = await generate_text(builder(complaint))
        # Truncate tweet-style outputs to platform limit
        if action in _TWEET_ACTIONS:
            text = text.strip()[:280]
        return text
    except Exception as e:
        logger.warning("Draft generation failed for action=%s: %s", action, e)
        rung = next((r for r in ESCALATION_LADDER if r["action"] == action), {})
        return f"[Draft pending — {rung.get('label', action)}]"


# ─────────────────────────────────────────────────────────────────────────────
# EscalationAgent
# ─────────────────────────────────────────────────────────────────────────────

class EscalationAgent(BaseAgent):
    """
    Plans and persists the full 30-day escalation ladder for a complaint.
    All draft generation is parallelised. Each rung is idempotent via
    (complaint_id, action) unique key.
    """

    def __init__(self) -> None:
        super().__init__(
            name="EscalationAgent",
            description="Plans and persists the 30-day civic enforcement ladder",
        )

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        complaint = agent_input.data.get("complaint") or {}
        complaint_id: str = (
            complaint.get("id")
            or agent_input.data.get("complaint_id")
            or ""
        )
        cluster_id: str | None = agent_input.data.get("cluster_id")

        if not complaint_id:
            return AgentOutput(
                agent_name=self.name,
                success=False,
                error="complaint_id is required",
            )

        # Enrich complaint dict with extra context from agent_input
        enriched = {
            **complaint,
            "id": complaint_id,
            "ward_name":   agent_input.data.get("ward_name", ""),
            "address":     agent_input.data.get("address", "Bangalore"),
            "agency_name": agent_input.data.get("agency_name", "BBMP"),
        }

        # Parse created_at — default to now (UTC) if missing/invalid
        created_at = _parse_datetime(complaint.get("created_at"))

        # ── Phase 1: Generate all drafts in parallel ──────────────────────────
        non_initial_rungs = [r for r in ESCALATION_LADDER if r["action"] != "initial"]
        draft_tasks = [_generate_draft(r["action"], enriched) for r in non_initial_rungs]
        drafts_list = await asyncio.gather(*draft_tasks, return_exceptions=True)

        # Map action → draft text (None for exceptions → fallback label)
        drafts: dict[str, str | None] = {"initial": None}
        for rung, result in zip(non_initial_rungs, drafts_list):
            if isinstance(result, Exception):
                logger.warning("Draft gather exception for %s: %s", rung["action"], result)
                drafts[rung["action"]] = f"[Draft pending — {rung['label']}]"
            else:
                drafts[rung["action"]] = result

        # ── Phase 2: Persist all rungs ────────────────────────────────────────
        db = get_supabase()  # single client for all inserts
        timeline: list[dict] = []
        inserted = 0

        for rung in ESCALATION_LADDER:
            action = rung["action"]
            scheduled_for = created_at + timedelta(days=rung["day"])
            idempotency_key = f"{complaint_id}:{action}"
            draft_text = drafts.get(action)
            is_day_zero = rung["day"] == 0

            row = {
                "id":               str(uuid4()),
                "complaint_id":     complaint_id,
                "cluster_id":       cluster_id,
                "day":              rung["day"],
                "action":           action,
                "status":           "sent" if is_day_zero else "pending",
                "draft_text":       draft_text,
                "idempotency_key":  idempotency_key,
                "scheduled_for":    scheduled_for.isoformat(),
                "executed_at":      datetime.now(timezone.utc).isoformat() if is_day_zero else None,
            }

            try:
                db.table("escalations").upsert(row, on_conflict="idempotency_key").execute()
                inserted += 1
            except Exception as e:
                logger.error(
                    "Escalation DB upsert failed (complaint=%s day=%d): %s",
                    complaint_id, rung["day"], e,
                )

            timeline.append({
                "day":            rung["day"],
                "action":         action,
                "label":          rung["label"],
                "scheduled_for":  scheduled_for.isoformat(),
                "status":         row["status"],
                "draft_preview":  (draft_text or "")[:200] if draft_text else None,
                "twitter_targets": rung.get("twitter_targets", []),
            })

        logger.info(
            "Escalation ladder for %s: %d/%d rungs persisted",
            complaint_id, inserted, len(ESCALATION_LADDER),
        )

        return AgentOutput(
            agent_name=self.name,
            success=True,
            data={
                "complaint_id":     complaint_id,
                "escalation_count": inserted,
                "timeline":         timeline,
            },
        )


# ─────────────────────────────────────────────────────────────────────────────
# Standalone: query escalation timeline for a complaint (used by API)
# ─────────────────────────────────────────────────────────────────────────────

async def get_escalation_timeline(complaint_id: str) -> list[dict]:
    """Return the full escalation timeline for a complaint, ordered by day."""
    if not complaint_id:
        return []
    try:
        db = get_supabase()
        result = (
            db.table("escalations")
            .select("day,action,label,status,draft_text,scheduled_for,executed_at,twitter_targets")
            .eq("complaint_id", complaint_id)
            .order("day")
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.warning("Timeline fetch failed for %s: %s", complaint_id, e)
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────────

def _parse_datetime(value: object) -> datetime:
    """Parse a datetime from ISO string, datetime object, or fall back to now."""
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        logger.warning("Could not parse created_at=%r, defaulting to now", value)
        return datetime.now(timezone.utc)
