from __future__ import annotations

import asyncio
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from uuid import uuid4

from .contracts import DeliveryResult, DeliveryStatus, SubmissionPayload


@dataclass(slots=True)
class TwitterConfig:
    bearer_token: str | None = None
    api_base_url: str = "https://api.twitter.com"
    timeout_seconds: float = 8.0
    dry_run: bool = True


class TwitterIntegration:
    channel = "twitter"

    def __init__(self, config: TwitterConfig) -> None:
        self.config = config

    async def send(self, payload: SubmissionPayload) -> DeliveryResult:
        started = time.perf_counter()
        tweet_text = self._build_tweet(payload)

        if self.config.dry_run or not self.config.bearer_token:
            return DeliveryResult(
                channel=self.channel,
                status=DeliveryStatus.SUCCESS,
                attempts=1,
                elapsed_ms=self._elapsed_ms(started),
                provider_message_id=f"dryrun-tweet-{uuid4().hex[:10]}",
                raw_response={"mode": "dry_run", "tweet_text": tweet_text},
            )

        try:
            response_body = await asyncio.to_thread(self._post_tweet, tweet_text)
            return DeliveryResult(
                channel=self.channel,
                status=DeliveryStatus.SUCCESS,
                attempts=1,
                elapsed_ms=self._elapsed_ms(started),
                provider_message_id=response_body.get("data", {}).get("id"),
                raw_response=response_body,
            )
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            return DeliveryResult(
                channel=self.channel,
                status=DeliveryStatus.FAILED,
                attempts=1,
                elapsed_ms=self._elapsed_ms(started),
                error=f"http_error:{exc.code}",
                raw_response={"detail": error_body},
            )
        except Exception as exc:  # noqa: BLE001
            return DeliveryResult(
                channel=self.channel,
                status=DeliveryStatus.FAILED,
                attempts=1,
                elapsed_ms=self._elapsed_ms(started),
                error=f"unexpected_error:{exc}",
            )

    def _post_tweet(self, tweet_text: str) -> dict:
        body = json.dumps({"text": tweet_text}).encode("utf-8")
        url = f"{self.config.api_base_url.rstrip('/')}/2/tweets"
        request = urllib.request.Request(  # noqa: S310
            url=url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.config.bearer_token}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:  # noqa: S310
            raw = response.read().decode("utf-8")
            return json.loads(raw)

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
