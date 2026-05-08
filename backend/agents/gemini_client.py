"""
Singleton Gemini client for NammaCity.
Wraps google-genai with retry, timeout, and usage logging.
"""

import logging
import time

from google import genai
from google.genai import types
from google.genai.errors import ServerError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from config import settings

logger = logging.getLogger("nammacity.gemini")

_client: genai.Client | None = None

DEFAULT_TIMEOUT = 30  # seconds


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


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(ServerError),
    reraise=True,
)
async def generate_text(
    prompt: str,
    model: str = "gemini-2.5-flash",
) -> str:
    """Generate text from a prompt. Retries on rate limits."""
    client = get_client()
    start = time.perf_counter()
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            http_options=types.HttpOptions(timeout=DEFAULT_TIMEOUT * 1000),
        ),
    )
    latency = (time.perf_counter() - start) * 1000
    _log_usage(model, latency, response)
    return response.text or ""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(ServerError),
    reraise=True,
)
async def generate_multimodal(
    prompt: str,
    image_bytes: bytes,
    model: str = "gemini-2.5-flash",
) -> str:
    """Generate text from prompt + image. Retries on rate limits."""
    client = get_client()
    start = time.perf_counter()

    image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")

    response = client.models.generate_content(
        model=model,
        contents=[prompt, image_part],
        config=types.GenerateContentConfig(
            http_options=types.HttpOptions(timeout=DEFAULT_TIMEOUT * 1000),
        ),
    )
    latency = (time.perf_counter() - start) * 1000
    _log_usage(model, latency, response)
    return response.text or ""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(ServerError),
    reraise=True,
)
async def embed_text(
    text: str,
    model: str = "gemini-embedding-001",
) -> list[float]:
    """Embed text and return the vector. 768 dimensions for gemini-embedding-001."""
    client = get_client()
    start = time.perf_counter()
    response = client.models.embed_content(
        model=model,
        contents=text,
    )
    latency = (time.perf_counter() - start) * 1000
    logger.info("embed_usage: model=%s latency_ms=%.2f", model, latency)
    return response.embeddings[0].values
