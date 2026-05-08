from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol


class DeliveryStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(slots=True)
class SubmissionPayload:
    complaint_id: str
    correlation_id: str
    subject: str
    body_text: str
    recipients: list[str] = field(default_factory=list)
    body_html: str | None = None
    twitter_handle: str | None = None
    media_urls: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DeliveryResult:
    channel: str
    status: DeliveryStatus
    attempts: int
    elapsed_ms: int
    provider_message_id: str | None = None
    external_ref: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None


@dataclass(slots=True)
class RetryPolicy:
    max_attempts: int = 3
    initial_delay_seconds: float = 0.5
    max_delay_seconds: float = 8.0
    backoff_multiplier: float = 2.0
    retry_on_exceptions: tuple[type[BaseException], ...] = (TimeoutError, ConnectionError)

    def next_delay(self, attempt_number: int) -> float:
        # attempt_number is 1-indexed.
        growth = self.initial_delay_seconds * (self.backoff_multiplier ** max(0, attempt_number - 1))
        return min(self.max_delay_seconds, growth)


class SubmissionIntegration(Protocol):
    channel: str

    async def send(self, payload: SubmissionPayload) -> DeliveryResult:
        ...
