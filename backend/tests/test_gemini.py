"""
Tests for the Gemini client.
Skipped if GEMINI_API_KEY is not set in .env.
"""

import pytest

from config import settings

# Skip all tests in this module if no API key
pytestmark = pytest.mark.skipif(
    not settings.gemini_api_key,
    reason="GEMINI_API_KEY not set — skipping Gemini tests",
)


@pytest.mark.asyncio
async def test_generate_text() -> None:
    from agents.gemini_client import generate_text

    result = await generate_text("Say hello in one word.")
    assert len(result) > 0
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_embed_text() -> None:
    from agents.gemini_client import embed_text

    vector = await embed_text("Hello world")
    assert isinstance(vector, list)
    assert len(vector) == 3072  # gemini-embedding-001 dimensions
    assert all(isinstance(v, float) for v in vector)
