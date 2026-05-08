"""
ADK-native Gemini client for NammaCity.
Replaces raw google-genai calls with Google ADK LlmAgent-backed inference.
Implements automatic model fallback chain on 429 rate limits.
"""

import asyncio
import logging
import os
import re
import time
import uuid

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai.types import Content, Part

from config import settings

logger = logging.getLogger("nammacity.adk_client")

# ── API key setup ─────────────────────────────────────────────────────────────
_api_key = settings.gemini_api_key or settings.google_api_key
if _api_key and not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = _api_key

# ── Model fallback chain ──────────────────────────────────────────────────────
# Only gemini-2.5-flash is confirmed available for this API key via ADK (v1beta).
MODEL_FALLBACK_CHAIN = [
    "gemini-2.5-flash",
]
DEFAULT_MODEL = MODEL_FALLBACK_CHAIN[0]
# gemini-embedding-001 is the available embedding model on the Gemini API.
# It produces 3072-dimensional vectors — must match Qdrant collection VECTOR_SIZE.
EMBED_MODEL = "models/gemini-embedding-001"

# ── Session service singleton ─────────────────────────────────────────────────
_session_service = InMemorySessionService()

# ── Embedding client singleton ────────────────────────────────────────────────
_embed_client = None


def _get_embed_client():
    """Return a shared google-genai client for embedding calls."""
    global _embed_client
    if _embed_client is None:
        from google import genai as _genai
        _embed_client = _genai.Client(api_key=_api_key or settings.gemini_api_key)
    return _embed_client


# ── Retry delay parser ────────────────────────────────────────────────────────
# Matches both  "retryDelay": "23s"  and  retryDelay=23.0s  in ADK error strings
_RETRY_DELAY_RE = re.compile(r'retryDelay["\s:=]+(\d+(?:\.\d+)?)')


def _is_rate_limit_error(exc: Exception) -> bool:
    msg = str(exc)
    return "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower()


def _parse_retry_delay(exc: Exception) -> float:
    match = _RETRY_DELAY_RE.search(str(exc))
    if match:
        return min(float(match.group(1)), 10.0)  # cap at 10s during demo
    return 5.0


# ─────────────────────────────────────────────────────────────────────────────
# Core: run one LlmAgent turn with automatic model fallback on 429
# ─────────────────────────────────────────────────────────────────────────────

async def _run_agent_once(
    agent: LlmAgent,
    message_parts: list[Part],
    app_name: str = "nammacity_inference",
) -> str:
    """
    Run an LlmAgent for a single turn.
    On 429, waits the retry delay then tries the next model in the fallback chain.
    Sessions are deleted after use to prevent unbounded memory growth.
    """
    requested = agent.model or DEFAULT_MODEL
    chain = [requested] + [m for m in MODEL_FALLBACK_CHAIN if m != requested]

    last_exc: Exception | None = None

    for model in chain:
        # Each attempt gets a collision-free session ID
        session_id = f"nc-{uuid.uuid4().hex}"
        session = None
        try:
            current_agent = LlmAgent(
                name=agent.name,
                model=model,
                instruction=agent.instruction or "",
                tools=list(agent.tools) if agent.tools else [],
            )
            runner = Runner(
                agent=current_agent,
                app_name=app_name,
                session_service=_session_service,
            )
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
                        part.text
                        for part in event.content.parts
                        if getattr(part, "text", None)
                    )

            if model != requested:
                logger.info("Model fallback succeeded: %s → %s", requested, model)
            return response_text

        except Exception as exc:
            last_exc = exc
            if _is_rate_limit_error(exc):
                delay = _parse_retry_delay(exc)
                if model != chain[-1]:
                    next_model = chain[chain.index(model) + 1]
                    logger.warning(
                        "429 on %s (retryDelay=%.1fs) — falling back to %s",
                        model, delay, next_model,
                    )
                    await asyncio.sleep(min(delay, 2.0))
                    continue
                else:
                    logger.error("All models rate-limited. Last error: %s", exc)
                    raise
            else:
                raise
        finally:
            # Clean up session to prevent InMemorySessionService growing unboundedly
            if session is not None:
                try:
                    await _session_service.delete_session(
                        app_name=app_name,
                        user_id="nammacity_system",
                        session_id=session_id,
                    )
                except Exception:
                    pass

    raise last_exc or RuntimeError("All models in fallback chain failed")


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

async def generate_text(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system_instruction: str | None = None,
) -> str:
    """Generate text via an ADK LlmAgent with automatic model fallback."""
    start = time.perf_counter()
    agent = LlmAgent(
        name="text_generator",
        model=model,
        instruction=system_instruction or (
            "You are a precise assistant. Follow instructions exactly. "
            "Return only what is asked for."
        ),
    )
    result = await _run_agent_once(agent, [Part(text=prompt)])
    logger.debug("generate_text model=%s latency_ms=%.1f", model, (time.perf_counter() - start) * 1000)
    return result


async def generate_multimodal(
    prompt: str,
    image_bytes: bytes,
    model: str = DEFAULT_MODEL,
    system_instruction: str | None = None,
) -> str:
    """Generate text from prompt + image with automatic model fallback."""
    start = time.perf_counter()
    agent = LlmAgent(
        name="multimodal_analyzer",
        model=model,
        instruction=system_instruction or (
            "You are a precise visual analyst. Return only valid JSON when asked for JSON."
        ),
    )
    image_part = Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
    result = await _run_agent_once(agent, [Part(text=prompt), image_part])
    logger.debug("generate_multimodal model=%s latency_ms=%.1f", model, (time.perf_counter() - start) * 1000)
    return result


async def generate_multimodal_audio(
    prompt: str,
    audio_bytes: bytes,
    mime_type: str = "audio/webm",
    model: str = DEFAULT_MODEL,
) -> str:
    """Transcribe or reason over audio bytes via ADK LlmAgent with fallback."""
    start = time.perf_counter()
    agent = LlmAgent(
        name="audio_transcriber",
        model=model,
        instruction="You are an accurate audio transcription assistant.",
    )
    audio_part = Part.from_bytes(data=audio_bytes, mime_type=mime_type)
    result = await _run_agent_once(agent, [Part(text=prompt), audio_part])
    logger.debug("generate_multimodal_audio model=%s latency_ms=%.1f", model, (time.perf_counter() - start) * 1000)
    return result


async def embed_text(
    text: str,
    model: str = EMBED_MODEL,
) -> list[float]:
    """
    Embed text using google-genai directly (ADK does not wrap embedding models).
    Uses a singleton client to avoid creating a new HTTP connection per call.
    Model: gemini-embedding-001 → 3072 dimensions (matches Qdrant collection).
    """
    start = time.perf_counter()
    client = _get_embed_client()
    response = client.models.embed_content(model=model, contents=text)
    logger.debug("embed_text model=%s latency_ms=%.1f", model, (time.perf_counter() - start) * 1000)
    return response.embeddings[0].values


# ─────────────────────────────────────────────────────────────────────────────
# Factory: build a named ADK LlmAgent for injection into NammaCity agents
# ─────────────────────────────────────────────────────────────────────────────

def make_agent(
    name: str,
    instruction: str,
    model: str = DEFAULT_MODEL,
    tools: list[FunctionTool] | None = None,
) -> LlmAgent:
    """Build a named ADK LlmAgent. model defaults to the primary in the fallback chain."""
    return LlmAgent(
        name=name,
        model=model,
        instruction=instruction,
        tools=tools or [],
    )
