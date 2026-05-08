"""
ADK-native Gemini client for NammaCity.
Replaces raw google-genai calls with Google ADK LlmAgent-backed inference.
Implements automatic model fallback chain on 429 rate limits.
"""

import asyncio
import logging
import os
import time

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
# gemini-2.5-flash: 20 req/day (free tier) — use as primary when quota allows
# gemini-2.0-flash: 1500 req/day (free tier) — primary workhorse
# gemini-2.0-flash-lite: 1500 req/day (free tier) — last resort
MODEL_FALLBACK_CHAIN = [
    "gemini-2.0-flash",        # primary — 1500/day free
    "gemini-2.0-flash-lite",   # fallback — 1500/day free, lower quality
    "gemini-2.5-flash",        # last resort — 20/day free, best quality
]
DEFAULT_MODEL = MODEL_FALLBACK_CHAIN[0]
EMBED_MODEL = "text-embedding-004"

# ── Session service singleton ─────────────────────────────────────────────────
_session_service = InMemorySessionService()
_session_counter = 0


def _next_session_id() -> str:
    global _session_counter
    _session_counter += 1
    return f"nammacity-inference-{_session_counter}"


def _is_rate_limit_error(exc: Exception) -> bool:
    """Return True if the exception is a 429 quota error."""
    msg = str(exc)
    return "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower()


def _parse_retry_delay(exc: Exception) -> float:
    """Extract retryDelay seconds from ADK error message, default 5s."""
    import re
    match = re.search(r"retryDelay.*?(\d+(?:\.\d+)?)\s*s", str(exc))
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
    """
    # Build the fallback list: requested model first, then the rest of the chain
    requested = agent.model or DEFAULT_MODEL
    chain = [requested] + [m for m in MODEL_FALLBACK_CHAIN if m != requested]

    last_exc: Exception | None = None

    for model in chain:
        try:
            # Rebuild agent with this model (LlmAgent is immutable after init)
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
                    # Brief pause before trying next model
                    await asyncio.sleep(min(delay, 2.0))
                    continue
                else:
                    logger.error("All models rate-limited. Last error: %s", exc)
                    raise
            else:
                raise  # Non-429 errors propagate immediately

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
    Embedding models have separate higher quotas.
    """
    from google import genai as _genai
    start = time.perf_counter()
    client = _genai.Client(api_key=_api_key or settings.gemini_api_key)
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
