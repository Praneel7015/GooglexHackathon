"""
Reporter Agent — Multimodal entry point for NammaCity.
Classifies civic issues from photo + optional voice using a Google ADK LlmAgent.
"""

import json
import logging

from agents.adk_client import generate_multimodal, generate_multimodal_audio, make_agent, _run_agent_once
from agents.base import AgentInput, AgentOutput, BaseAgent
from google.adk.agents import LlmAgent
from google.genai.types import Part

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

_SYSTEM_INSTRUCTION = """You are NammaCity's civic issue classifier for Bangalore.
Analyze photos and classify civic issues. Always return valid JSON only — no markdown, no explanation.
Pick exactly one issue_type from the allowed list. Be strict and accurate."""

_CLASSIFY_PROMPT = """Analyze this photo of a civic issue in Bangalore. Return a JSON object with exactly these fields:

{{
  "issue_type": "<one of: {issue_types}>",
  "severity": <integer 1-5>,
  "spam_score": <float 0.0-1.0>,
  "description": "<1-2 sentence description of the specific issue visible>"
}}

SEVERITY:
1=Minor cosmetic, 2=Noticeable, 3=Needs attention within a week,
4=Urgent (affects safety/daily life), 5=Hazardous (immediate danger to life)

SPAM SCORE: 0.0=clearly real civic photo, 1.0=AI-generated/spam/irrelevant

{extra_context}

Return ONLY the JSON object. No markdown fences."""

_TRANSCRIBE_INSTRUCTION = """You are an audio transcription assistant.
Transcribe the given audio accurately. Return only the transcription text, nothing else."""


class ReporterAgent(BaseAgent):
    """Classify civic issues from photos using a Google ADK LlmAgent."""

    def __init__(self) -> None:
        super().__init__(
            name="ReporterAgent",
            description="Multimodal civic issue classifier powered by ADK LlmAgent",
        )
        # ADK LlmAgent dedicated to civic issue classification
        self._classifier: LlmAgent = make_agent(
            name="civic_classifier",
            instruction=_SYSTEM_INSTRUCTION,
        )
        # ADK LlmAgent for voice transcription
        self._transcriber: LlmAgent = make_agent(
            name="voice_transcriber",
            instruction=_TRANSCRIBE_INSTRUCTION,
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

        # Step 1: Transcribe voice note via ADK if provided
        extra_context = ""
        if voice_bytes:
            extra_context = await self._transcribe_voice(voice_bytes, language)

        # Step 2: Classify image via ADK LlmAgent
        prompt = _CLASSIFY_PROMPT.format(
            issue_types=", ".join(ISSUE_TYPES),
            extra_context=f"CITIZEN VOICE NOTE: {extra_context}" if extra_context else "",
        )

        image_part = Part.from_bytes(data=photo_bytes, mime_type="image/jpeg")
        raw = await _run_agent_once(
            self._classifier,
            [Part(text=prompt), image_part],
            app_name="nammacity_reporter",
        )

        # Step 3: Parse and validate JSON output
        result = self._parse_classification(raw)

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

    def _parse_classification(self, raw: str) -> dict:
        """Parse and validate the JSON output from the ADK classifier agent."""
        # Strip markdown fences if the model added them
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("ReporterAgent: JSON parse failed, raw=%r", raw[:200])
            result = {"issue_type": "other", "severity": 3, "spam_score": 0.0, "description": raw[:200]}

        # Validate issue_type
        if result.get("issue_type") not in ISSUE_TYPES:
            result["issue_type"] = "other"

        # Clamp severity
        result["severity"] = max(1, min(5, int(result.get("severity", 3))))

        # Clamp spam_score
        result["spam_score"] = max(0.0, min(1.0, float(result.get("spam_score", 0.0))))

        return result

    async def _transcribe_voice(self, audio_bytes: bytes, language: str) -> str:
        """Transcribe voice note using the ADK transcriber LlmAgent."""
        try:
            audio_part = Part.from_bytes(data=audio_bytes, mime_type="audio/webm")
            prompt_part = Part(text=f"Transcribe this audio in {language}. Return only the transcription text.")
            return await _run_agent_once(
                self._transcriber,
                [prompt_part, audio_part],
                app_name="nammacity_reporter",
            )
        except Exception as e:
            logger.warning("Voice transcription failed: %s", e)
            return ""
