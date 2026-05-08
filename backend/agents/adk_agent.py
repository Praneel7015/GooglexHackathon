"""
Google ADK integration layer for NammaCity.
Wraps the complaint pipeline as ADK FunctionTools under a central LlmAgent.
"""

import asyncio
import json
import logging
from typing import Any

from google.adk import Runner
from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai.types import Content, Part

from agents.base import AgentInput
from agents.crowd_validation import CrowdValidationAgent
from agents.drafting import DraftingAgent
from agents.escalation import EscalationAgent
from agents.geo import GeoAgent
from agents.prediction import PredictionAgent
from agents.reporter import ReporterAgent
from agents.routing import RoutingAgent
from agents.submission import SubmissionAgent
from config import settings

logger = logging.getLogger("nammacity.adk")

# ─────────────────────────────────────────────────────────────────────────────
# Agent singletons (shared with main.py via import)
# ─────────────────────────────────────────────────────────────────────────────

_reporter = ReporterAgent()
_geo = GeoAgent()
_routing = RoutingAgent()
_crowd = CrowdValidationAgent()
_drafting = DraftingAgent()
_submission = SubmissionAgent()
_escalation = EscalationAgent()
_prediction = PredictionAgent()

# ─────────────────────────────────────────────────────────────────────────────
# Tool functions (each wraps one NammaCity agent)
# ADK FunctionTools must be synchronous or async plain functions.
# ─────────────────────────────────────────────────────────────────────────────

async def classify_civic_issue(
    issue_description: str,
    ward_number: int | None = None,
    severity_hint: int | None = None,
) -> dict[str, Any]:
    """
    Classify a civic issue from a text description.
    Returns issue_type, severity (1-5), and spam_score.
    Use this when you have a description but no photo bytes available.
    """
    result = await _reporter.execute(AgentInput(data={
        "photo_bytes": b"",
        "language": "en",
        "_text_override": issue_description,
    }))
    return result.data if result.success else {"error": result.error}


async def route_complaint(issue_type: str, ward_number: int | None = None) -> dict[str, Any]:
    """
    Route a civic complaint to the correct agency.
    Given an issue_type (e.g. 'pothole', 'water_leak') and optional ward number,
    returns the primary agency, secondary agency, and ward officer contact.
    """
    result = await _routing.execute(AgentInput(data={
        "issue_type": issue_type,
        "ward_number": ward_number,
    }))
    return result.data if result.success else {"error": result.error}


async def check_crowd_validation(
    complaint_id: str,
    description: str,
    lat: float,
    lng: float,
    issue_type: str,
    ward_number: int | None = None,
) -> dict[str, Any]:
    """
    Check whether a new complaint can be bundled with similar nearby ones.
    Returns is_bundled (bool), member_count, cluster_id, and aggregated_description.
    Bundling amplifies civic pressure — 38 complaints get fixed, 1 gets ignored.
    """
    result = await _crowd.execute(AgentInput(data={
        "complaint_id": complaint_id,
        "description": description,
        "lat": lat,
        "lng": lng,
        "issue_type": issue_type,
        "ward_number": ward_number,
    }))
    return result.data if result.success else {"error": result.error}


async def draft_complaint_content(
    complaint_id: str,
    issue_type: str,
    severity: int,
    description: str,
    ward_number: int | None = None,
    ward_name: str = "",
    agency_name: str = "BBMP",
    twitter_handle: str = "@BBMPCOMM",
    officer_name: str = "Ward Officer",
    officer_email: str | None = None,
    is_bundled: bool = False,
    member_count: int = 1,
) -> dict[str, Any]:
    """
    Generate formal complaint content in multiple formats simultaneously.
    Returns: email_subject, email_body_en, email_body_kn (Kannada), tweet_text,
    whatsapp_text, and rti_template (RTI application under Karnataka RTI Act).
    """
    result = await _drafting.execute(AgentInput(data={
        "complaint_id": complaint_id,
        "issue_type": issue_type,
        "severity": severity,
        "description": description,
        "location": {"ward_number": ward_number, "ward_name": ward_name, "address": ""},
        "routing": {
            "primary_agency": {"name": agency_name},
            "twitter_handle": twitter_handle,
            "ward_officer": {"name": officer_name, "email": officer_email},
        },
        "crowd_validation": {
            "is_bundled": is_bundled,
            "member_count": member_count,
            "aggregated_description": description,
        },
    }))
    return result.data if result.success else {"error": result.error}


async def submit_complaint(
    complaint_id: str,
    tweet_text: str,
    email_subject: str,
    email_body: str,
    whatsapp_text: str,
    officer_email: str | None = None,
    officer_phone: str | None = None,
    twitter_handle: str = "@BBMPCOMM",
    is_bundled: bool = False,
    member_count: int = 1,
    cluster_id: str | None = None,
) -> dict[str, Any]:
    """
    Dispatch the complaint across Twitter, Gmail, and WhatsApp simultaneously.
    Returns per-channel status (success/failed/stub), reference IDs, and overall status.
    Applies milestone suppression for bundled complaints.
    """
    result = await _submission.execute(AgentInput(data={
        "complaint_id": complaint_id,
        "drafting": {
            "tweet_text": tweet_text,
            "email_subject": email_subject,
            "email_body_en": email_body,
            "email_body_kn": "",
            "whatsapp_text": whatsapp_text,
        },
        "routing": {
            "twitter_handle": twitter_handle,
            "ward_officer": {"email": officer_email, "phone": officer_phone},
        },
        "crowd_validation": {
            "is_bundled": is_bundled,
            "member_count": member_count,
            "cluster_id": cluster_id,
        },
    }))
    return result.data if result.success else {"error": result.error}


async def predict_resolution(
    ward_number: int | None = None,
    issue_type: str | None = None,
) -> dict[str, Any]:
    """
    Predict the likelihood and timeline for a civic complaint to be resolved.
    Returns resolution_rate, avg_resolution_days, and a confidence_message like
    '72% chance of resolution in ~18 days based on Ward 95 history'.
    """
    result = await _prediction.execute(AgentInput(data={
        "ward_number": ward_number,
        "issue_type": issue_type,
        "include_leaderboard": False,
    }))
    return result.data if result.success else {"error": result.error}


async def schedule_escalation(
    complaint_id: str,
    issue_type: str,
    ward_number: int | None = None,
    agency_name: str = "BBMP",
) -> dict[str, Any]:
    """
    Schedule the 30-day enforcement ladder for an unresolved complaint.
    Day 7: ward councillor tagged. Day 14: RTI filed. Day 21: MLA + media.
    Day 30: PIL outline drafted. Returns the full timeline.
    """
    result = await _escalation.execute(AgentInput(data={
        "complaint_id": complaint_id,
        "complaint": {"id": complaint_id, "issue_type": issue_type, "ward_number": ward_number},
        "agency_name": agency_name,
    }))
    return result.data if result.success else {"error": result.error}


# ─────────────────────────────────────────────────────────────────────────────
# ADK LlmAgent — the central NammaCity coordinator
# ─────────────────────────────────────────────────────────────────────────────

NAMMACITY_INSTRUCTION = """
You are NammaCity, an AI civic operating system for Bangalore.

Your role is to help citizens report civic issues and automatically escalate them
to the right authorities to get them resolved.

You have access to these tools:
- classify_civic_issue: understand what kind of issue is being reported
- route_complaint: find the correct civic agency (BBMP, BESCOM, BWSSB, etc.)
- check_crowd_validation: check if similar nearby complaints can be bundled for more impact
- draft_complaint_content: generate formal emails, tweets, and WhatsApp messages
- submit_complaint: dispatch to Twitter, Gmail, and WhatsApp simultaneously
- predict_resolution: forecast how quickly the issue will be resolved
- schedule_escalation: set up automatic follow-ups on Day 7, 14, 21, 30

For a new complaint, you MUST:
1. Classify the issue
2. Route to the correct agency
3. Check crowd validation (bundling amplifies pressure)
4. Draft content in multiple formats
5. Submit across all channels
6. Predict resolution likelihood
7. Schedule escalation ladder

Always be specific about ward numbers, agency names, and timelines.
Respond in the citizen's language when possible (Kannada, Hindi, or English).
"""


def build_nammacity_agent() -> LlmAgent:
    """Build and return the ADK LlmAgent with all NammaCity tools registered."""
    tools = [
        FunctionTool(classify_civic_issue),
        FunctionTool(route_complaint),
        FunctionTool(check_crowd_validation),
        FunctionTool(draft_complaint_content),
        FunctionTool(submit_complaint),
        FunctionTool(predict_resolution),
        FunctionTool(schedule_escalation),
    ]

    agent = LlmAgent(
        name="nammacity_orchestrator",
        model=f"google/{settings.gemini_model}" if hasattr(settings, "gemini_model") else "gemini-2.5-flash",
        description="NammaCity civic AI — routes, bundles, and escalates Bangalore complaints",
        instruction=NAMMACITY_INSTRUCTION,
        tools=tools,
    )
    logger.info("ADK LlmAgent 'nammacity_orchestrator' built with %d tools", len(tools))
    return agent


# ─────────────────────────────────────────────────────────────────────────────
# ADK Runner — executes the agent for a single complaint description query
# ─────────────────────────────────────────────────────────────────────────────

async def run_adk_pipeline(user_message: str, session_id: str = "default") -> str:
    """
    Run the NammaCity ADK agent for a text-based complaint query.
    Returns the agent's final text response.
    Used by chat-style or voice-note-transcription flows.
    """
    agent = build_nammacity_agent()
    session_service = InMemorySessionService()

    runner = Runner(
        agent=agent,
        app_name="nammacity",
        session_service=session_service,
    )

    session = await session_service.create_session(
        app_name="nammacity",
        user_id="citizen",
        session_id=session_id,
    )

    message = Content(role="user", parts=[Part(text=user_message)])

    final_response = ""
    async for event in runner.run_async(
        user_id="citizen",
        session_id=session.id,
        new_message=message,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_response = event.content.parts[0].text or ""

    return final_response
