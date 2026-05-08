"""
Drafting Agent — Generate complaint content in multiple formats.
Produces email (EN+KN), tweet, WhatsApp message, and RTI template
in parallel via ADK LlmAgent-backed generate_text calls.
"""

import asyncio
import logging

from agents.adk_client import generate_text, make_agent, _run_agent_once
from agents.base import AgentInput, AgentOutput, BaseAgent
from google.adk.agents import LlmAgent
from google.genai.types import Part

logger = logging.getLogger("nammacity.agents.drafting")

_EMAIL_INSTRUCTION = (
    "You are a formal civic complaint email writer for Bangalore citizens. "
    "Write professional HTML emails citing relevant Karnataka legislation. "
    "Be assertive but respectful. Return only the email body HTML."
)

_TWEET_INSTRUCTION = (
    "You are a civic advocacy tweet writer. "
    "Write concise tweets (max 270 characters) that demand government action. "
    "Return ONLY the tweet text — no quotes, no commentary."
)

_WHATSAPP_INSTRUCTION = (
    "You are a civic messaging assistant. "
    "Write bilingual (English + Kannada) WhatsApp messages to ward officers. "
    "Tone: friendly but firm. Return only the message text."
)

_KANNADA_INSTRUCTION = (
    "You are a Kannada translator. Translate civic complaint emails to Kannada. "
    "Keep legal citations in English. Maintain the formal register. "
    "Return only the translated text."
)

_RTI_INSTRUCTION = (
    "You are a legal document drafter specializing in Karnataka RTI applications. "
    "Cite RTI Act Section 6. Return only the complete RTI application text."
)


def _severity_label(s: int) -> str:
    return {
        1: "Minor", 2: "Noticeable", 3: "Needs attention",
        4: "Urgent", 5: "Hazardous/Dangerous",
    }.get(s, "Unknown")


class DraftingAgent(BaseAgent):
    """Generate multi-format complaint content via parallel ADK LlmAgent calls."""

    def __init__(self) -> None:
        super().__init__(
            name="DraftingAgent",
            description="Multi-format complaint content generator powered by ADK LlmAgents",
        )
        # One dedicated LlmAgent per format — injected once at init
        self._email_agent: LlmAgent = make_agent("email_drafter", _EMAIL_INSTRUCTION)
        self._tweet_agent: LlmAgent = make_agent("tweet_drafter", _TWEET_INSTRUCTION)
        self._whatsapp_agent: LlmAgent = make_agent("whatsapp_drafter", _WHATSAPP_INSTRUCTION)
        self._kannada_agent: LlmAgent = make_agent("kannada_translator", _KANNADA_INSTRUCTION)
        self._rti_agent: LlmAgent = make_agent("rti_drafter", _RTI_INSTRUCTION)

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        d = agent_input.data
        complaint_id = d.get("complaint_id", "")
        issue_type = d.get("issue_type", "other")
        severity = d.get("severity", 3)
        description = d.get("description", "")
        location = d.get("location", {})
        routing = d.get("routing", {})
        crowd = d.get("crowd_validation", {})
        user_name = d.get("user_name")
        user_email = d.get("user_email")

        ward = location.get("ward_number", "N/A")
        ward_name = location.get("ward_name", "")
        address = location.get("address", "")
        zone = location.get("zone", "")
        officer = routing.get("ward_officer", {}) or {}
        officer_name = officer.get("name", "Ward Officer")
        twitter_handle = routing.get("twitter_handle", "@BBMPCOMM")
        agency_name = (routing.get("primary_agency") or {}).get("name", "BBMP")

        is_bundled = crowd.get("is_bundled", False)
        member_count = crowd.get("member_count", 1)
        agg_desc = crowd.get("aggregated_description") or description

        tone = "ASSERTIVE and urgent" if is_bundled else "respectful but concrete"
        count_phrase = f"on behalf of {member_count} verified residents" if is_bundled else "as a concerned citizen"

        email_prompt = self._email_prompt(
            officer_name, issue_type, severity, description, agg_desc,
            ward, ward_name, address, zone, agency_name,
            is_bundled, member_count, count_phrase, tone,
            user_name, user_email, complaint_id,
        )
        kannada_prompt = (
            f"Translate this formal civic complaint email to Kannada. "
            f"Keep legal citations in English:\n\n{email_prompt[:1500]}"
        )
        tweet_prompt = self._tweet_prompt(
            twitter_handle, issue_type, severity, ward, ward_name,
            is_bundled, member_count, complaint_id,
        )
        whatsapp_prompt = self._whatsapp_prompt(
            officer_name, issue_type, ward, ward_name, description,
            is_bundled, member_count,
        )
        rti_prompt = self._rti_prompt(issue_type, ward, ward_name, address, agency_name, complaint_id)

        # Run all 5 ADK LlmAgent calls in parallel
        results = await asyncio.gather(
            _run_agent_once(self._email_agent, [Part(text=email_prompt)], "nammacity_drafting"),
            _run_agent_once(self._kannada_agent, [Part(text=kannada_prompt)], "nammacity_drafting"),
            _run_agent_once(self._tweet_agent, [Part(text=tweet_prompt)], "nammacity_drafting"),
            _run_agent_once(self._whatsapp_agent, [Part(text=whatsapp_prompt)], "nammacity_drafting"),
            _run_agent_once(self._rti_agent, [Part(text=rti_prompt)], "nammacity_drafting"),
            return_exceptions=True,
        )

        def _str(r: object, fallback: str) -> str:
            return r if isinstance(r, str) else fallback

        email_en = _str(results[0], f"Civic complaint regarding {issue_type} at Ward {ward}.")
        email_kn = _str(results[1], "")
        tweet = _str(results[2], "").strip().replace("\n", " ")[:280]
        whatsapp = _str(results[3], "")
        rti = _str(results[4], "")

        if is_bundled:
            email_subject = (
                f"Joint Civic Complaint — Ward {ward} "
                f"{issue_type.replace('_', ' ').title()} — {member_count} Verified Residents"
            )
        else:
            email_subject = f"Civic Complaint — Ward {ward} {issue_type.replace('_', ' ').title()}"

        return AgentOutput(
            agent_name=self.name,
            success=True,
            data={
                "email_subject": email_subject,
                "email_body_en": email_en,
                "email_body_kn": email_kn,
                "tweet_text": tweet,
                "whatsapp_text": whatsapp,
                "rti_template": rti,
            },
        )

    # ── Prompt builders ───────────────────────────────────────────────────────

    def _email_prompt(
        self, officer, issue, severity, desc, agg_desc, ward, ward_name,
        address, zone, agency, bundled, count, count_phrase, tone,
        user_name, user_email, cid,
    ) -> str:
        user_line = f"\n\nSubmitted by: {user_name or 'Anonymous'}" + (
            f" <{user_email}>" if user_email else ""
        )
        citation = self._get_citation(issue)
        bundled_note = (
            f"This issue has been reported by {count} independent residents in the same area, "
            f"indicating a widespread problem requiring immediate attention."
            if bundled else ""
        )
        return (
            f"Write a formal civic complaint email in HTML format. Tone: {tone}.\n\n"
            f"Dear Officer {officer},\n\n"
            f"I am writing {count_phrase} to bring to your attention:\n"
            f"Issue: {issue.replace('_', ' ')} (Severity: {severity}/5 — {_severity_label(severity)})\n"
            f"Location: Ward {ward} ({ward_name}), {address}, Zone: {zone}\n"
            f"Agency: {agency}\n\n"
            f"Description: {agg_desc}\n\n"
            f"{bundled_note}\n\n"
            f"{citation}\n\n"
            f"Photo evidence and live tracking: nammacity.in/c/{cid}"
            f"{user_line}\n\n"
            f"Sincerely,\nNammaCity — Civic Coordination Platform\n\n"
            f"Format as proper HTML email with paragraphs. Include all the details above."
        )

    def _tweet_prompt(self, handle, issue, severity, ward, ward_name, bundled, count, cid) -> str:
        if bundled:
            return (
                f"Write a single tweet (max 270 chars). MUST start with {handle}. "
                f"Format: '{handle} Joint Complaint: {count} verified residents report "
                f"{issue.replace('_',' ')} in Ward {ward} ({ward_name}). Severity {severity}/5. "
                f"Action requested. nammacity.in/c/{cid} #FixBangalore'. "
                f"Output ONLY the tweet text."
            )
        return (
            f"Write a single tweet (max 270 chars). MUST start with {handle}. "
            f"Format: '{handle} {issue.replace('_',' ')} reported in Ward {ward} ({ward_name}). "
            f"Severity {severity}/5. Citizen action requested. nammacity.in/c/{cid} #FixBangalore'. "
            f"Output ONLY the tweet text."
        )

    def _whatsapp_prompt(self, officer, issue, ward, ward_name, desc, bundled, count) -> str:
        bundled_note = f"Mention: {count} residents have reported this." if bundled else ""
        return (
            f"Write a WhatsApp message (bilingual English + Kannada) to a ward officer.\n"
            f"Tone: friendly but firm. Start with: 'Namaste {officer},'\n"
            f"Mention: {issue.replace('_',' ')} issue in Ward {ward} ({ward_name}).\n"
            f"{bundled_note}\n"
            f"Description: {desc[:200]}\n"
            f"End with: 'We request prompt action. — NammaCity Team'\n"
            f"Output ONLY the message text."
        )

    def _rti_prompt(self, issue, ward, ward_name, address, agency, cid) -> str:
        return (
            f"Generate a formal RTI application under the Karnataka RTI Act.\n"
            f"To: Public Information Officer, {agency}\n"
            f"Subject: Action-taken report on {issue.replace('_',' ')} at Ward {ward} ({ward_name}), {address}\n"
            f"Reference: NammaCity #{cid}\n"
            f"Ask for: 1) Action taken report 2) Timeline 3) Officer responsible\n"
            f"Cite Karnataka RTI Act sections. Output the complete application."
        )

    @staticmethod
    def _get_citation(issue_type: str) -> str:
        citations = {
            "pothole": "Reference: Karnataka Municipal Corporations Act, 1976 — Section 256 (Maintenance of public streets)",
            "road_damage": "Reference: Karnataka Municipal Corporations Act, 1976 — Section 256 (Maintenance of public streets)",
            "garbage_pile": "Reference: Karnataka Municipal Corporations Act, 1976 — Section 320 (Sanitation provisions)",
            "sanitation": "Reference: Karnataka Municipal Corporations Act, 1976 — Section 320 (Sanitation provisions)",
            "encroachment": "Reference: Karnataka Municipal Corporations Act, 1976 — Section 297 (Removal of unauthorized encroachments)",
            "illegal_construction": "Reference: Karnataka Municipal Corporations Act, 1976 — Section 297 (Removal of unauthorized encroachments)",
        }
        return citations.get(issue_type, "Reference: Karnataka Municipal Corporations Act, 1976")
