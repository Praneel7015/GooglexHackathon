"""
Smoke tests for Twitter, Gmail, and WhatsApp integrations.
STUB tests always run. LIVE tests skip if credentials not set.
"""

import pytest

from config import settings
from integrations.contracts import DeliveryStatus, SubmissionPayload
from integrations.twitter import TwitterIntegration
from integrations.gmail import GmailIntegration
from integrations.whatsapp import WhatsAppIntegration


def _make_payload(**overrides) -> SubmissionPayload:
    defaults = {
        "complaint_id": "test-001",
        "correlation_id": "corr-001",
        "subject": "Test pothole near MSRIT",
        "body_text": "Large pothole causing traffic hazard.",
        "recipients": ["test@example.com"],
        "twitter_handle": "@BBMPCOMM",
        "metadata": {"whatsapp_contacts": ["+919999999999"]},
    }
    defaults.update(overrides)
    return SubmissionPayload(**defaults)


# --- Twitter Tests ---

@pytest.mark.asyncio
async def test_twitter_stub_mode() -> None:
    """Twitter returns success in STUB mode when no credentials set."""
    # Clear any cached client
    twitter = TwitterIntegration()
    twitter._client = None

    # Temporarily blank out credentials to force stub
    original = (
        settings.twitter_api_key,
        settings.twitter_api_secret,
        settings.twitter_access_token,
        settings.twitter_access_token_secret,
    )
    settings.twitter_api_key = ""
    settings.twitter_api_secret = ""
    settings.twitter_access_token = ""
    settings.twitter_access_token_secret = ""

    try:
        result = await twitter.send(_make_payload())
        assert result.status == DeliveryStatus.SUCCESS
        assert result.raw_response["mode"] == "stub"
        assert result.provider_message_id.startswith("stub-tweet-")
        assert "STUB_" in result.external_ref
    finally:
        (
            settings.twitter_api_key,
            settings.twitter_api_secret,
            settings.twitter_access_token,
            settings.twitter_access_token_secret,
        ) = original


@pytest.mark.asyncio
async def test_twitter_truncates_to_280() -> None:
    """Tweet text is truncated to 280 characters."""
    twitter = TwitterIntegration()
    long_text = "A" * 500
    payload = _make_payload(body_text=long_text)
    tweet = twitter._build_tweet(payload)
    assert len(tweet) <= 280


# --- Gmail Tests ---

@pytest.mark.asyncio
async def test_gmail_stub_mode() -> None:
    """Gmail returns success in STUB mode when no credentials set."""
    gmail = GmailIntegration()

    original_user = settings.gmail_user
    original_pass = settings.gmail_app_password
    settings.gmail_user = ""
    settings.gmail_app_password = ""

    try:
        result = await gmail.send(
            _make_payload(),
            cc="citizen@gmail.com",
            reply_to="citizen@gmail.com",
        )
        assert result.status == DeliveryStatus.SUCCESS
        assert result.raw_response["mode"] == "stub"
        assert result.raw_response["cc"] == "citizen@gmail.com"
        assert result.raw_response["reply_to"] == "citizen@gmail.com"
    finally:
        settings.gmail_user = original_user
        settings.gmail_app_password = original_pass


@pytest.mark.asyncio
async def test_gmail_skips_no_recipients() -> None:
    """Gmail returns SKIPPED when no recipients provided."""
    gmail = GmailIntegration()
    result = await gmail.send(_make_payload(recipients=[]))
    assert result.status == DeliveryStatus.SKIPPED
    assert result.error == "no_recipients"


@pytest.mark.asyncio
async def test_gmail_stub_preserves_cc_reply_to() -> None:
    """STUB mode response includes cc and reply_to for verification."""
    gmail = GmailIntegration()

    original_user = settings.gmail_user
    original_pass = settings.gmail_app_password
    settings.gmail_user = ""
    settings.gmail_app_password = ""

    try:
        result = await gmail.send(
            _make_payload(recipients=["ward95@bbmp.gov.in"]),
            cc=["user1@gmail.com", "user2@gmail.com"],
            reply_to="user1@gmail.com",
            bcc="admin@nammacity.in",
        )
        assert result.status == DeliveryStatus.SUCCESS
        assert result.raw_response["cc"] == ["user1@gmail.com", "user2@gmail.com"]
        assert result.raw_response["reply_to"] == "user1@gmail.com"
    finally:
        settings.gmail_user = original_user
        settings.gmail_app_password = original_pass


# --- WhatsApp Tests ---

@pytest.mark.asyncio
async def test_whatsapp_stub() -> None:
    """WhatsApp always runs in stub mode."""
    wa = WhatsAppIntegration()
    result = await wa.send(_make_payload())

    assert result.status == DeliveryStatus.SUCCESS
    assert result.raw_response["mode"] == "stub"
    assert "Pending Meta Business API" in result.raw_response["note"]
    assert result.raw_response["contacts"] == ["+919999999999"]


@pytest.mark.asyncio
async def test_whatsapp_stub_no_contacts() -> None:
    """WhatsApp stub still succeeds even without contacts."""
    wa = WhatsAppIntegration()
    result = await wa.send(_make_payload(metadata={}))

    assert result.status == DeliveryStatus.SUCCESS
    assert result.raw_response["mode"] == "stub"
