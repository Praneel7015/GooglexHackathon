"""
Tests for the ADK-native Gemini client (adk_client).
Skipped if GEMINI_API_KEY is not set in .env.
"""

import pytest

from config import settings

pytestmark = pytest.mark.skipif(
    not settings.gemini_api_key,
    reason="GEMINI_API_KEY not set — skipping ADK client tests",
)


@pytest.mark.asyncio
async def test_generate_text() -> None:
    from agents.adk_client import generate_text

    result = await generate_text("Say hello in one word.")
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_embed_text() -> None:
    from agents.adk_client import embed_text

    vector = await embed_text("Hello world")
    assert isinstance(vector, list)
    assert len(vector) > 0
    assert all(isinstance(v, float) for v in vector)
