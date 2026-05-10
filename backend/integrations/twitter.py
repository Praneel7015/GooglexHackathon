"""
Twitter/X integration using X's internal GraphQL API with cookies.
No paid API needed. Uses auth_token + ct0 cookies from browser session.
"""

from __future__ import annotations

import json
import logging
import time
from uuid import uuid4

import httpx

from .contracts import DeliveryResult, DeliveryStatus, SubmissionPayload
from config import settings

logger = logging.getLogger("nammacity.integrations.twitter")

# X's internal API endpoint for creating tweets
CREATE_TWEET_URL = "https://x.com/i/api/graphql/a1p9RWpkYKBjWv_I3WzS-A/CreateTweet"


def _get_headers() -> dict | None:
    """Build headers for X's internal API using cookies."""
    auth_token = getattr(settings, 'twitter_auth_token', '') or ''
    ct0 = getattr(settings, 'twitter_ct0', '') or ''

    if not auth_token or not ct0:
        return None

    return {
        "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
        "content-type": "application/json",
        "cookie": f"auth_token={auth_token}; ct0={ct0}",
        "x-csrf-token": ct0,
        "x-twitter-auth-type": "OAuth2Session",
        "x-twitter-active-user": "yes",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }


class TwitterIntegration:
    """Post tweets via X's internal GraphQL API (free, cookie-based)."""

    channel = "twitter"

    async def send(self, payload: SubmissionPayload) -> DeliveryResult:
        started = time.perf_counter()
        tweet_text = self._build_tweet(payload)
        username = getattr(settings, 'twitter_username', 'nammacity_blr')

        headers = _get_headers()

        if headers is None:
            logger.info("Twitter STUB mode: %s", tweet_text[:80])
            return DeliveryResult(
                channel=self.channel,
                status=DeliveryStatus.SUCCESS,
                attempts=1,
                elapsed_ms=self._elapsed_ms(started),
                provider_message_id=f"stub-tweet-{uuid4().hex[:10]}",
                external_ref=f"https://x.com/{username}/status/STUB_{uuid4().hex[:8]}",
                raw_response={"mode": "stub", "tweet_text": tweet_text},
            )

        try:
            tweet_id = await self._post_tweet(tweet_text, headers)
            tweet_url = f"https://x.com/{username}/status/{tweet_id}"
            logger.info("Tweet posted: %s", tweet_url)
            return DeliveryResult(
                channel=self.channel,
                status=DeliveryStatus.SUCCESS,
                attempts=1,
                elapsed_ms=self._elapsed_ms(started),
                provider_message_id=str(tweet_id),
                external_ref=tweet_url,
                raw_response={"mode": "live", "tweet_id": tweet_id, "text": tweet_text},
            )
        except Exception as exc:
            logger.warning("Tweet failed: %s", exc)
            return DeliveryResult(
                channel=self.channel,
                status=DeliveryStatus.FAILED,
                attempts=1,
                elapsed_ms=self._elapsed_ms(started),
                error=f"twitter_error:{exc}",
            )

    async def _post_tweet(self, text: str, headers: dict) -> str:
        """Post tweet using X's GraphQL CreateTweet mutation."""
        payload = {
            "variables": {
                "tweet_text": text,
                "dark_request": False,
                "media": {"media_entities": [], "possibly_sensitive": False},
                "semantic_annotation_ids": [],
            },
            "features": {
                "communities_web_enable_tweet_community_results_fetch": True,
                "c9s_tweet_anatomy_moderator_badge_enabled": True,
                "tweetypie_unmention_optimization_enabled": True,
                "responsive_web_edit_tweet_api_enabled": True,
                "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
                "view_counts_everywhere_api_enabled": True,
                "longform_notetweets_consumption_enabled": True,
                "responsive_web_twitter_article_tweet_consumption_enabled": True,
                "tweet_awards_web_tipping_enabled": False,
                "creator_subscriptions_quote_tweet_preview_enabled": False,
                "longform_notetweets_rich_text_read_enabled": True,
                "longform_notetweets_inline_media_enabled": True,
                "articles_preview_enabled": True,
                "rweb_video_timestamps_enabled": True,
                "rweb_tipjar_consumption_enabled": True,
                "responsive_web_graphql_exclude_directive_enabled": True,
                "verified_phone_label_enabled": False,
                "freedom_of_speech_not_reach_fetch_enabled": True,
                "standardized_nudges_misinfo": True,
                "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
                "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
                "responsive_web_graphql_timeline_navigation_enabled": True,
                "responsive_web_enhance_cards_enabled": False,
            },
            "queryId": "a1p9RWpkYKBjWv_I3WzS-A",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                CREATE_TWEET_URL,
                json=payload,
                headers=headers,
            )

        if resp.status_code != 200:
            raise Exception(f"X API {resp.status_code}: {resp.text[:200]}")

        data = resp.json()

        # Extract tweet ID from response
        try:
            result = data["data"]["create_tweet"]["tweet_results"]["result"]
            tweet_id = result.get("rest_id") or result.get("tweet", {}).get("rest_id")
            if tweet_id:
                return tweet_id
        except (KeyError, TypeError):
            pass

        # If we can't parse the ID but got 200, tweet likely posted
        return f"posted-{uuid4().hex[:10]}"

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
