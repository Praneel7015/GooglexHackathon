from __future__ import annotations

import logging
import time
from uuid import uuid4

import tweepy

from .contracts import DeliveryResult, DeliveryStatus, SubmissionPayload

from config import settings

logger = logging.getLogger("nammacity.integrations.twitter")


class TwitterIntegration:
    """
    Twitter API v2 integration using OAuth 1.0a User Context (via tweepy).
    Reads credentials from config.settings.
    Falls back to STUB mode when credentials are missing.
    """

    channel = "twitter"

    def __init__(self) -> None:
        self._client: tweepy.Client | None = None

    def _get_client(self) -> tweepy.Client | None:
        """Create tweepy Client with OAuth 1.0a if all 4 keys are present."""
        if self._client is not None:
            return self._client

        api_key = settings.twitter_api_key
        api_secret = settings.twitter_api_secret
        access_token = settings.twitter_access_token
        access_secret = settings.twitter_access_token_secret

        if not all([api_key, api_secret, access_token, access_secret]):
            return None

        self._client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret,
        )
        return self._client

    async def send(self, payload: SubmissionPayload) -> DeliveryResult:
        started = time.perf_counter()
        tweet_text = self._build_tweet(payload)

        client = self._get_client()

        if client is None:
            logger.info("Twitter STUB mode: %s", tweet_text[:80])
            return DeliveryResult(
                channel=self.channel,
                status=DeliveryStatus.SUCCESS,
                attempts=1,
                elapsed_ms=self._elapsed_ms(started),
                provider_message_id=f"stub-tweet-{uuid4().hex[:10]}",
                external_ref=f"https://twitter.com/nammacity_blr/status/STUB_{uuid4().hex[:8]}",
                raw_response={"mode": "stub", "tweet_text": tweet_text},
            )

        try:
            response = client.create_tweet(text=tweet_text)
            tweet_id = response.data["id"]
            return DeliveryResult(
                channel=self.channel,
                status=DeliveryStatus.SUCCESS,
                attempts=1,
                elapsed_ms=self._elapsed_ms(started),
                provider_message_id=str(tweet_id),
                external_ref=f"https://twitter.com/nammacity_blr/status/{tweet_id}",
                raw_response={"tweet_id": tweet_id, "text": tweet_text},
            )
        except tweepy.TooManyRequests:
            return DeliveryResult(
                channel=self.channel,
                status=DeliveryStatus.FAILED,
                attempts=1,
                elapsed_ms=self._elapsed_ms(started),
                error="rate_limited",
            )
        except Exception as exc:
            return DeliveryResult(
                channel=self.channel,
                status=DeliveryStatus.FAILED,
                attempts=1,
                elapsed_ms=self._elapsed_ms(started),
                error=f"twitter_error:{exc}",
            )

    @staticmethod
    def _build_tweet(payload: SubmissionPayload) -> str:
        parts = [payload.subject.strip(), payload.body_text.strip()]
        if payload.twitter_handle:
            parts.append(f"cc {payload.twitter_handle.strip()}")
        tweet = " | ".join(part for part in parts if part)
        return tweet[:280]

    @staticmethod
    def _elapsed_ms(started: float) -> int:
        return int((time.perf_counter() - started) * 1000)
