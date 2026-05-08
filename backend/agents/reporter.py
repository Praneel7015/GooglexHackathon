"""
Reporter Agent — Multimodal entry point.
Classifies civic issues from photo + optional voice, assigns severity,
detects spam. Uses Gemini structured output.
"""

import json
import logging

from google import genai
from google.genai import types

from agents.base import AgentInput, AgentOutput, BaseAgent
from agents.gemini_client import get_client, DEFAULT_TIMEOUT

logger = logging.getLogger("nammacity.agents.reporter")

ISSUE_TYPES = [
    "pothole", "road_damage", "garbage_pile", "sanitation", "streetlight_out",
    "broken_footpath", "open_drain", "sewage_overflow", "water_leak",
    "electrical_wire_dangerous", "power_outage", "broken_pole", "bus_stop_damage",
    "traffic_signal_broken", "illegal_parking", "encroachment", "illegal_construction",
    "air_pollution", "noise_pollution", "water_pollution", "tree_fall",
    "illegal_tree_cutting", "stray_animals", "dengue_breeding", "metro_issue",
    "builder_fraud", "broken_railing", "flooding", "manhole_open", "other",
]

CLASSIFY_PROMPT = """You are NammaCity's civic issue classifier for Bangalore.

Analyze this photo of a civic issue and return a JSON classification.

ISSUE TYPES (pick exactly one):
pothole, road_damage, garbage_pile, sanitation, streetlight_out, broken_footpath,
open_drain, sewage_overflow, water_leak, electrical_wire_dangerous, power_outage,
broken_pole, bus_stop_damage, traffic_signal_broken, illegal_parking, encroachment,
illegal_construction, air_pollution, noise_pollution, water_pollution, tree_fall,
illegal_tree_cutting, stray_animals, dengue_breeding, metro_issue, builder_fraud,
broken_railing, flooding, manhole_open, other

SEVERITY SCALE:
1 = Minor cosmetic issue
2 = Noticeable but not urgent
3 = Needs attention within a week
4 = Urgent — affects safety or daily life
5 = Hazardous — immediate danger to life

SPAM DETECTION:
Score 0.0 to 1.0: 0.0 = clearly real photo, 1.0 = clearly AI-generated/spam/irrelevant

{extra_context}

Return valid JSON with these exact fields:
- issue_type (string, one of the types above)
- severity (integer 1-5)
- spam_score (float 0.0-1.0)
- description (string, 1-2 sentence description of the issue)
"""


class ReporterAgent(BaseAgent):
    """Classify civic issues from photos using Gemini multimodal."""

    def __init__(self) -> None:
        super().__init__(
            name="ReporterAgent",
            description="Multimodal civic issue classifier",
        )

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        photo_bytes: bytes = agent_input.data.get("photo_bytes", b"")
        voice_bytes: bytes | None = agent_input.data.get("voice_note_bytes")
        language: str = agent_input.data.get("language", "en")

        if not photo_bytes:
            return AgentOutput(
                agent_name=self.name,
                success=False,
                error="No photo provided",
            )

        # Build extra context from voice note
        extra_context = ""
        if voice_bytes:
            extra_context = await self._transcribe_voice(voice_bytes, language)

        prompt = CLASSIFY_PROMPT.format(
            extra_context=f"CITIZEN VOICE NOTE: {extra_context}" if extra_context else ""
        )

        client = get_client()
        image_part = types.Part.from_bytes(data=photo_bytes, mime_type="image/jpeg")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, image_part],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "object",
                    "properties": {
                        "issue_type": {"type": "string"},
                        "severity": {"type": "integer"},
                        "spam_score": {"type": "number"},
                        "description": {"type": "string"},
                    },
                    "required": ["issue_type", "severity", "spam_score", "description"],
                },
                http_options=types.HttpOptions(timeout=DEFAULT_TIMEOUT * 1000),
            ),
        )

        result = json.loads(response.text)

        # Validate issue_type
        if result.get("issue_type") not in ISSUE_TYPES:
            result["issue_type"] = "other"

        # Clamp severity
        result["severity"] = max(1, min(5, result.get("severity", 3)))

        # TODO: Duplicate-check against existing complaints (Phase 5)

        return AgentOutput(
            agent_name=self.name,
            success=True,
            data={
                "issue_type": result["issue_type"],
                "severity": result["severity"],
                "spam_score": result.get("spam_score", 0.0),
                "raw_description": result.get("description", ""),
                "transcribed_text": extra_context,
            },
        )

    async def _transcribe_voice(self, audio_bytes: bytes, language: str) -> str:
        """Transcribe voice note using Gemini."""
        try:
            client = get_client()
            audio_part = types.Part.from_bytes(data=audio_bytes, mime_type="audio/webm")
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    f"Transcribe this audio in {language}. Return only the transcription text.",
                    audio_part,
                ],
                config=types.GenerateContentConfig(
                    http_options=types.HttpOptions(timeout=DEFAULT_TIMEOUT * 1000),
                ),
            )
            return response.text or ""
        except Exception as e:
            logger.warning("Voice transcription failed: %s", e)
            return ""
