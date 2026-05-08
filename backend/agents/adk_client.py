"""
ADK-native Gemini client for NammaCity.
Replaces raw google-genai calls with Google ADK LlmAgent-backed inference.
Exposes generate_text, generate_multimodal, and embed_text used by all agents.
"""

import base64
import logging
import os
import time
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai import types as genai_types
from google.genai.types import Content, Part

from config import settings

logger = logging.getLogger("nammacity.adk_client")

# Ensure ADK can find the API key.
# Precedence:
# 1. Existing GOOGLE_API_KEY in the environment
# 2. settings.gemini_api_key
# 3. settings.google_api_key
_adk_google_api_key = (
    settings.gemini_api_key
    or getattr(settings, "google_api_key", None)
)
if _adk_google_api_key and not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = _adk_google_api_key

DEFAULT_MODEL = "gemini-2.5-flash"
EMBED_MODEL = "text-embedding-004"

# ─────────────────────────────────────────────────────────────────────────────
# Shared singleton session service
# ─────────────────────────────────────────────────────────────────────────────

_session_service = InMemorySessionService()
_session_counter = 0


def _next_session_id() -> str:
    global _session_counter
    _session_counter += 1
    return f"nammacity-inference-{_session_counter}"


# ─────────────────────────────────────────────────────────────────────────────
# Internal: run a single-turn ADK LlmAgent and return the text response
# ─────────────────────────────────────────────────────────────────────────────

async def _run_agent_once(
    agent: LlmAgent,
    message_parts: list[Part],
    app_name: str = "nammacity_inference",
) -> str:
    """
    Run an LlmAgent for a single turn and return its text response.
    Creates a fresh ephemeral session per call (stateless inference).
    """
    runner = Runner(
        agent=agent,
        app_name=app_name,
        session_service=_session_service,
    )

    session_id = _next_session_id()
    session = await _session_service.create_session(
        app_name=app_name,
        user_id="nammacity_system",
        session_id=session_id,
    )

    message = Content(role="user", parts=message_parts)
    response_text = ""

    async for event in runner.run_async(
        user_id="nammacity_system",
        session_id=session.id,
        new_message=message,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            response_text = "".join(
                part.text for part in event.content.parts if getattr(part, "text", None)
            )

    return response_text


# ─────────────────────────────────────────────────────────────────────────────
# Public API — drop-in replacements for gemini_client functions
# ─────────────────────────────────────────────────────────────────────────────

async def generate_text(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system_instruction: str | None = None,
) -> str:
    """
    Generate text via an ADK LlmAgent.
    Drop-in replacement for gemini_client.generate_text.
    """
    start = time.perf_counter()
    agent = LlmAgent(
        name="text_generator",
        model=model,
        instruction=system_instruction or "You are a precise assistant. Follow instructions exactly. Return only what is asked for.",
    )
    result = await _run_agent_once(agent, [Part(text=prompt)])
    latency = (time.perf_counter() - start) * 1000
    logger.debug("generate_text model=%s latency_ms=%.1f", model, latency)
    return result


async def generate_multimodal(
    prompt: str,
    image_bytes: bytes,
    model: str = DEFAULT_MODEL,
    system_instruction: str | None = None,
) -> str:
    """
    Generate text from a prompt + image via an ADK LlmAgent.
    Drop-in replacement for gemini_client.generate_multimodal.
    """
    start = time.perf_counter()
    agent = LlmAgent(
        name="multimodal_analyzer",
        model=model,
        instruction=system_instruction or "You are a precise visual analyst. Return only valid JSON when asked for JSON.",
    )

    image_part = Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
    result = await _run_agent_once(agent, [Part(text=prompt), image_part])
    latency = (time.perf_counter() - start) * 1000
    logger.debug("generate_multimodal model=%s latency_ms=%.1f", model, latency)
    return result


async def generate_multimodal_audio(
    prompt: str,
    audio_bytes: bytes,
    mime_type: str = "audio/webm",
    model: str = DEFAULT_MODEL,
) -> str:
    """Transcribe or reason over audio bytes via ADK LlmAgent."""
    start = time.perf_counter()
    agent = LlmAgent(
        name="audio_transcriber",
        model=model,
        instruction="You are an accurate audio transcription assistant.",
    )
    audio_part = Part.from_bytes(data=audio_bytes, mime_type=mime_type)
    result = await _run_agent_once(agent, [Part(text=prompt), audio_part])
    latency = (time.perf_counter() - start) * 1000
    logger.debug("generate_multimodal_audio model=%s latency_ms=%.1f", model, latency)
    return result


async def embed_text(
    text: str,
    model: str = EMBED_MODEL,
) -> list[float]:
    """
    Embed text using the google-genai client directly (ADK does not wrap embeddings).
    Falls back to google.genai for embedding-specific models.
    """
    from google import genai as _genai
    start = time.perf_counter()
    client = _genai.Client(api_key=settings.gemini_api_key)
    response = client.models.embed_content(model=model, contents=text)
    latency = (time.perf_counter() - start) * 1000
    logger.debug("embed_text model=%s latency_ms=%.1f", model, latency)
    return response.embeddings[0].values


# ─────────────────────────────────────────────────────────────────────────────
# Factory: build a named ADK LlmAgent for use inside a NammaCity agent class
# ─────────────────────────────────────────────────────────────────────────────

def make_agent(
    name: str,
    instruction: str,
    model: str = DEFAULT_MODEL,
    tools: list[FunctionTool] | None = None,
) -> LlmAgent:
    """
    Build a named ADK LlmAgent for a NammaCity sub-agent.
    Pass tools=[] explicitly if you want a tool-calling agent.
    """
    return LlmAgent(
        name=name,
        model=model,
        instruction=instruction,
        tools=tools or [],
    )
