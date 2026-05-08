"""
Singleton Gemini client for NammaCity.
Wraps google-genai with auto-fallback to cheaper models on rate limits.
"""

import logging
import time

from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

from config import settings

logger = logging.getLogger("nammacity.gemini")

_client: genai.Client | None = None

DEFAULT_TIMEOUT = 30  # seconds

# Fallback chain: try primary, then cheaper models on 429
TEXT_FALLBACK_CHAIN = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

MULTIMODAL_FALLBACK_CHAIN = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]


def get_client() -> genai.Client:
    """Get or create the Gemini client singleton."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def _log_usage(model: str, latency_ms: float, response: object) -> None:
    """Log token usage from response metadata."""
    usage = getattr(response, "usage_metadata", None)
    info: dict = {
        "model": model,
        "latency_ms": round(latency_ms, 2),
    }
    if usage:
        info["prompt_tokens"] = getattr(usage, "prompt_token_count", 0)
        info["output_tokens"] = getattr(usage, "candidates_token_count", 0)
        info["total_tokens"] = getattr(usage, "total_token_count", 0)
    logger.info("gemini_usage: %s", info)


def _is_rate_limit(exc: Exception) -> bool:
    """Check if exception is a 429 rate limit error."""
    return isinstance(exc, ClientError) and "429" in str(exc)


async def generate_text(
    prompt: str,
    model: str | None = None,
) -> str:
    """Generate text with auto-fallback on rate limits."""
    chain = [model] if model else TEXT_FALLBACK_CHAIN
    client = get_client()
    last_error = None

    for m in chain:
        try:
            start = time.perf_counter()
            response = client.models.generate_content(
                model=m,
                contents=prompt,
                config=types.GenerateContentConfig(
                    http_options=types.HttpOptions(timeout=DEFAULT_TIMEOUT * 1000),
                ),
            )
            latency = (time.perf_counter() - start) * 1000
            _log_usage(m, latency, response)
            return response.text or ""
        except (ClientError, ServerError) as e:
            last_error = e
            if _is_rate_limit(e) and m != chain[-1]:
                logger.warning("Rate limited on %s, falling back to next model", m)
                continue
            raise

    raise last_error


async def generate_multimodal(
    prompt: str,
    image_bytes: bytes,
    model: str | None = None,
) -> str:
    """Generate text from prompt + image with auto-fallback on rate limits."""
    chain = [model] if model else MULTIMODAL_FALLBACK_CHAIN
    client = get_client()
    last_error = None
    image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")

    for m in chain:
        try:
            start = time.perf_counter()
            response = client.models.generate_content(
                model=m,
                contents=[prompt, image_part],
                config=types.GenerateContentConfig(
                    http_options=types.HttpOptions(timeout=DEFAULT_TIMEOUT * 1000),
                ),
            )
            latency = (time.perf_counter() - start) * 1000
            _log_usage(m, latency, response)
            return response.text or ""
        except (ClientError, ServerError) as e:
            last_error = e
            if _is_rate_limit(e) and m != chain[-1]:
                logger.warning("Rate limited on %s, falling back to next model", m)
                continue
            raise

    raise last_error


async def embed_text(
    text: str,
    model: str = "gemini-embedding-001",
) -> list[float]:
    """Embed text and return the vector. 3072 dimensions for gemini-embedding-001."""
    client = get_client()
    start = time.perf_counter()
    response = client.models.embed_content(
        model=model,
        contents=text,
    )
    latency = (time.perf_counter() - start) * 1000
    logger.info("embed_usage: model=%s latency_ms=%.2f", model, latency)
    return response.embeddings[0].values
