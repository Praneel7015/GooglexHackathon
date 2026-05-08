"""
Escalation Agent — 30-day enforcement ladder for unresolved complaints.
Generates day 0/7/14/21/30 actions and persists them in the escalations table.
"""

import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from agents.base import AgentInput, AgentOutput, BaseAgent
from agents.gemini_client import generate_text
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
# Draft generators (one per ladder rung)
# ─────────────────────────────────────────────────────────────────────────────

async def _draft_councillor_tweet(complaint: dict) -> str:
    prompt = (
        f"Write a firm escalation tweet (max 270 chars). Tone: assertive, cite lack of response.\n"
        f"Issue: {complaint['issue_type'].replace('_',' ')} in Ward {complaint['ward_number']} "
        f"({complaint.get('ward_name','')}).\n"
        f"Agency: {complaint.get('agency_name','BBMP')}.\n"
        f"Complaint ID: {complaint['id']}.\n"
        f"Start with: @BBMPCOMM @CMofKarnataka\n"
        f"End with: #FixBangalore nammacity.in/c/{complaint['id']}\n"
        f"Output ONLY the tweet text."
    )
    return (await generate_text(prompt)).strip()[:280]


async def _draft_rti(complaint: dict) -> str:
    prompt = (
        f"Draft a short RTI application under Karnataka RTI Act for:\n"
        f"Issue: {complaint['issue_type'].replace('_',' ')} at Ward {complaint['ward_number']}, "
        f"{complaint.get('address','Bangalore')}.\n"
        f"Reference: NammaCity #{complaint['id']}.\n"
        f"Request: action-taken report, responsible officer, expected timeline.\n"
        f"Keep it under 200 words. Include RTI Act Section 6 citation."
    )
    return await generate_text(prompt)


async def _draft_mla_tweet(complaint: dict) -> str:
    prompt = (
        f"Write an escalation tweet tagging MLA and media (max 270 chars).\n"
        f"Issue unresolved for 21 days: {complaint['issue_type'].replace('_',' ')} "
        f"in Ward {complaint['ward_number']}.\n"
        f"Start with: @CMofKarnataka @TimesofIndia_blr @DeccanHerald\n"
        f"End with: #FixBangalore #BangaloreCorruption nammacity.in/c/{complaint['id']}\n"
        f"Output ONLY the tweet text."
    )
    return (await generate_text(prompt)).strip()[:280]


async def _draft_pil_outline(complaint: dict) -> str:
    prompt = (
        f"Draft a 150-word PIL outline for filing in Karnataka High Court.\n"
        f"Civic issue: {complaint['issue_type'].replace('_',' ')} at Ward {complaint['ward_number']}, "
        f"Bangalore. Unresolved for 30+ days despite formal RTI.\n"
        f"Cite: Article 21 (right to life), Karnataka Municipal Corporations Act 1976.\n"
        f"Include: prayer, petitioner description, relief sought."
    )
    return await generate_text(prompt)


_DRAFT_FUNCS = {
    "initial": None,  # handled by SubmissionAgent
    "councillor_tag": _draft_councillor_tweet,
    "rti": _draft_rti,
    "mla_media": _draft_mla_tweet,
    "pil": _draft_pil_outline,
}


# ─────────────────────────────────────────────────────────────────────────────
# EscalationAgent
# ─────────────────────────────────────────────────────────────────────────────

class EscalationAgent(BaseAgent):
    """
    Plans and persists the full 30-day escalation ladder for a complaint.
    Call once after submission; each rung is scheduled for future execution.
    """

    def __init__(self) -> None:
        super().__init__(
            name="EscalationAgent",
            description="Plans and persists the 30-day civic enforcement ladder",
        )

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        complaint = agent_input.data.get("complaint", {})
        complaint_id = complaint.get("id") or agent_input.data.get("complaint_id", "")
        cluster_id: str | None = agent_input.data.get("cluster_id")

        if not complaint_id:
            return AgentOutput(
                agent_name=self.name,
                success=False,
                error="complaint_id is required",
            )

        created_at_raw = complaint.get("created_at")
        if created_at_raw:
            try:
                if isinstance(created_at_raw, str):
                    created_at = datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
                else:
                    created_at = created_at_raw
            except ValueError:
                created_at = datetime.now(timezone.utc)
        else:
            created_at = datetime.now(timezone.utc)

        timeline: list[dict] = []
        inserted = 0

        for rung in ESCALATION_LADDER:
            scheduled_for = created_at + timedelta(days=rung["day"])
            idempotency_key = f"{complaint_id}:{rung['action']}"

            # Generate draft for non-initial rungs
            draft_text: str | None = None
            draft_fn = _DRAFT_FUNCS.get(rung["action"])
            if draft_fn:
                try:
                    draft_text = await draft_fn({
                        **complaint,
                        "id": complaint_id,
                        "ward_name": agent_input.data.get("ward_name", ""),
                        "address": agent_input.data.get("address", "Bangalore"),
                        "agency_name": agent_input.data.get("agency_name", "BBMP"),
                    })
                except Exception as e:
                    logger.warning("Draft generation failed for %s: %s", rung["action"], e)
                    draft_text = f"[Draft pending — {rung['label']}]"

            row = {
                "id": str(uuid4()),
                "complaint_id": complaint_id,
                "cluster_id": cluster_id,
                "day": rung["day"],
                "action": rung["action"],
                "status": "sent" if rung["day"] == 0 else "pending",
                "draft_text": draft_text,
                "idempotency_key": idempotency_key,
                "scheduled_for": scheduled_for.isoformat(),
                "executed_at": datetime.now(timezone.utc).isoformat() if rung["day"] == 0 else None,
            }

            try:
                db = get_supabase()
                db.table("escalations").upsert(row, on_conflict="idempotency_key").execute()
                inserted += 1
            except Exception as e:
                logger.warning("Escalation DB insert failed (day %d): %s", rung["day"], e)

            timeline.append({
                "day": rung["day"],
                "action": rung["action"],
                "label": rung["label"],
                "scheduled_for": scheduled_for.isoformat(),
                "status": row["status"],
                "draft_preview": (draft_text or "")[:200] if draft_text else None,
            })

        return AgentOutput(
            agent_name=self.name,
            success=True,
            data={
                "complaint_id": complaint_id,
                "escalation_count": inserted,
                "timeline": timeline,
            },
        )


# ─────────────────────────────────────────────────────────────────────────────
# Standalone: query escalation timeline for a complaint (used by API)
# ─────────────────────────────────────────────────────────────────────────────

async def get_escalation_timeline(complaint_id: str) -> list[dict]:
    """Return the full escalation timeline for a complaint, ordered by day."""
    try:
        db = get_supabase()
        result = (
            db.table("escalations")
            .select("day,action,status,draft_text,scheduled_for,executed_at")
            .eq("complaint_id", complaint_id)
            .order("day")
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.warning("Timeline fetch failed: %s", e)
        return []
