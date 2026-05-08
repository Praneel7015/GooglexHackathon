"""
Drafting Agent — Generate complaint content in multiple formats.
Produces email (EN+KN), tweet, WhatsApp message, and RTI template
in parallel via Gemini.
"""

import asyncio
import logging

from agents.base import AgentInput, AgentOutput, BaseAgent
from agents.gemini_client import generate_text

logger = logging.getLogger("nammacity.agents.drafting")


def _severity_label(s: int) -> str:
    return {1: "Minor", 2: "Noticeable", 3: "Needs attention", 4: "Urgent", 5: "Hazardous/Dangerous"}.get(s, "Unknown")


class DraftingAgent(BaseAgent):
    """Generate multi-format complaint content via parallel Gemini calls."""

    def __init__(self) -> None:
        super().__init__(name="DraftingAgent", description="Multi-format complaint content generator")

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
        agency_name = routing.get("primary_agency", {}).get("name", "BBMP")

        is_bundled = crowd.get("is_bundled", False)
        member_count = crowd.get("member_count", 1)
        agg_desc = crowd.get("aggregated_description") or description

        tone = "ASSERTIVE and urgent" if is_bundled else "respectful but concrete"
        count_phrase = f"on behalf of {member_count} verified residents" if is_bundled else "as a concerned citizen"

        # Build prompts
        email_prompt = self._email_prompt(
            officer_name, issue_type, severity, description, agg_desc,
            ward, ward_name, address, zone, agency_name,
            is_bundled, member_count, count_phrase, tone,
            user_name, user_email, complaint_id,
        )
        kannada_prompt = f"Translate this formal civic complaint email to Kannada. Keep legal citations in English. Maintain the formal register:\n\n{email_prompt[:1500]}"
        tweet_prompt = self._tweet_prompt(twitter_handle, issue_type, severity, ward, ward_name, is_bundled, member_count, complaint_id)
        whatsapp_prompt = self._whatsapp_prompt(officer_name, issue_type, ward, ward_name, description, is_bundled, member_count)
        rti_prompt = self._rti_prompt(issue_type, ward, ward_name, address, agency_name, complaint_id)

        # Run ALL 5 in parallel
        results = await asyncio.gather(
            generate_text(email_prompt),
            generate_text(kannada_prompt),
            generate_text(tweet_prompt),
            generate_text(whatsapp_prompt),
            generate_text(rti_prompt),
            return_exceptions=True,
        )

        email_en = results[0] if isinstance(results[0], str) else f"Civic complaint regarding {issue_type} at Ward {ward}."
        email_kn = results[1] if isinstance(results[1], str) else ""
        tweet = results[2] if isinstance(results[2], str) else ""
        whatsapp = results[3] if isinstance(results[3], str) else ""
        rti = results[4] if isinstance(results[4], str) else ""

        # Ensure tweet fits 280 chars
        tweet = tweet.strip().replace("\n", " ")[:280]

        if is_bundled:
            email_subject = f"Joint Civic Complaint — Ward {ward} {issue_type.replace('_', ' ').title()} — {member_count} Verified Residents"
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

    def _email_prompt(self, officer, issue, severity, desc, agg_desc, ward, ward_name, address, zone, agency, bundled, count, count_phrase, tone, user_name, user_email, cid) -> str:
        user_line = f"\n\nSubmitted by: {user_name or 'Anonymous'}" + (f" <{user_email}>" if user_email else "")
        citation = self._get_citation(issue)
        return f"""Write a formal civic complaint email in HTML format. Tone: {tone}.

Dear Officer {officer},

I am writing {count_phrase} to bring to your attention:
Issue: {issue.replace('_', ' ')} (Severity: {severity}/5 — {_severity_label(severity)})
Location: Ward {ward} ({ward_name}), {address}, Zone: {zone}
Agency: {agency}

Description: {agg_desc}

{"This issue has been reported by " + str(count) + " independent residents in the same area, indicating a widespread problem requiring immediate attention." if bundled else ""}

{citation}

Photo evidence and live tracking: nammacity.in/c/{cid}
{user_line}

Sincerely,
NammaCity — Civic Coordination Platform

Format as proper HTML email with paragraphs. Include all the details above."""

    def _tweet_prompt(self, handle, issue, severity, ward, ward_name, bundled, count, cid) -> str:
        if bundled:
            return f"Write a single tweet (max 270 chars). MUST start with {handle}. Format: '{handle} Joint Complaint: {count} verified residents report {issue.replace('_',' ')} in Ward {ward} ({ward_name}). Severity {severity}/5. Action requested. nammacity.in/c/{cid} #FixBangalore'. Output ONLY the tweet text."
        return f"Write a single tweet (max 270 chars). MUST start with {handle}. Format: '{handle} {issue.replace('_',' ')} reported in Ward {ward} ({ward_name}). Severity {severity}/5. Citizen action requested. nammacity.in/c/{cid} #FixBangalore'. Output ONLY the tweet text."

    def _whatsapp_prompt(self, officer, issue, ward, ward_name, desc, bundled, count) -> str:
        return f"""Write a WhatsApp message (bilingual English + Kannada) to a ward officer.
Tone: friendly but firm. Start with: "Namaste {officer},"
Mention: {issue.replace('_',' ')} issue in Ward {ward} ({ward_name}).
{"Mention: " + str(count) + " residents have reported this." if bundled else ""}
Description: {desc[:200]}
End with: "We request prompt action. — NammaCity Team"
Output ONLY the message text."""

    def _rti_prompt(self, issue, ward, ward_name, address, agency, cid) -> str:
        return f"""Generate a formal RTI application under the Karnataka RTI Act.
To: Public Information Officer, {agency}
Subject: Action-taken report on {issue.replace('_',' ')} at Ward {ward} ({ward_name}), {address}
Reference: NammaCity #{cid}
Ask for: 1) Action taken report 2) Timeline 3) Officer responsible
Cite Karnataka RTI Act sections. Output the complete application."""

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
