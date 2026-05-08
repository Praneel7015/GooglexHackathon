from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Iterable

from backend.integrations.contracts import (
    DeliveryResult,
    DeliveryStatus,
    RetryPolicy,
    SubmissionIntegration,
    SubmissionPayload,
)


@dataclass(slots=True)
class SubmissionSummary:
    complaint_id: str
    correlation_id: str
    started_at_epoch_ms: int
    completed_at_epoch_ms: int
    overall_status: DeliveryStatus
    per_channel: dict[str, DeliveryResult] = field(default_factory=dict)


class SubmissionService:
    """
    Portable submission orchestrator:
    - accepts integration adapters through dependency injection
    - retries failures safely with exponential backoff
    - protects against duplicate submissions with idempotency keys
    """

    def __init__(
        self,
        integrations: Iterable[SubmissionIntegration],
        retry_policy: RetryPolicy | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.integrations = {integration.channel: integration for integration in integrations}
        self.retry_policy = retry_policy or RetryPolicy()
        self.logger = logger or logging.getLogger(__name__)
        self._idempotency_keys: set[str] = set()
        self._idempotency_lock = asyncio.Lock()

    async def submit(
        self,
        payload: SubmissionPayload,
        selected_channels: list[str] | None = None,
    ) -> SubmissionSummary:
        started_ms = self._epoch_ms()
        idempotency_key = self._build_idempotency_key(payload)
        is_first_submission = await self._register_idempotency_key(idempotency_key)

        if not is_first_submission:
            self.logger.info(
                "submission_duplicate_skipped",
                extra={
                    "complaint_id": payload.complaint_id,
                    "correlation_id": payload.correlation_id,
                    "idempotency_key": idempotency_key,
                },
            )
            return SubmissionSummary(
                complaint_id=payload.complaint_id,
                correlation_id=payload.correlation_id,
                started_at_epoch_ms=started_ms,
                completed_at_epoch_ms=self._epoch_ms(),
                overall_status=DeliveryStatus.SKIPPED,
                per_channel={},
            )

        channels = selected_channels or list(self.integrations.keys())
        tasks = [self._send_via_channel(channel, payload) for channel in channels]
        results = await asyncio.gather(*tasks)
        per_channel = {result.channel: result for result in results}
        overall_status = self._resolve_overall_status(per_channel.values())

        summary = SubmissionSummary(
            complaint_id=payload.complaint_id,
            correlation_id=payload.correlation_id,
            started_at_epoch_ms=started_ms,
            completed_at_epoch_ms=self._epoch_ms(),
            overall_status=overall_status,
            per_channel=per_channel,
        )

        self.logger.info(
            "submission_completed",
            extra={
                "complaint_id": payload.complaint_id,
                "correlation_id": payload.correlation_id,
                "overall_status": summary.overall_status.value,
                "channels": list(summary.per_channel.keys()),
            },
        )
        return summary

    async def _send_via_channel(self, channel: str, payload: SubmissionPayload) -> DeliveryResult:
        integration = self.integrations.get(channel)
        started = time.perf_counter()
        if integration is None:
            return DeliveryResult(
                channel=channel,
                status=DeliveryStatus.SKIPPED,
                attempts=1,
                elapsed_ms=self._elapsed_ms(started),
                error="channel_not_configured",
            )

        attempt = 0
        while attempt < self.retry_policy.max_attempts:
            attempt += 1
            try:
                result = await integration.send(payload)
                result.attempts = attempt
                if result.status != DeliveryStatus.FAILED:
                    return result

                self.logger.warning(
                    "submission_channel_failed",
                    extra={
                        "channel": channel,
                        "attempt": attempt,
                        "complaint_id": payload.complaint_id,
                        "correlation_id": payload.correlation_id,
                        "error": result.error,
                    },
                )
            except self.retry_policy.retry_on_exceptions as exc:
                self.logger.warning(
                    "submission_channel_retryable_exception",
                    extra={
                        "channel": channel,
                        "attempt": attempt,
                        "complaint_id": payload.complaint_id,
                        "correlation_id": payload.correlation_id,
                        "error": str(exc),
                    },
                )
                result = DeliveryResult(
                    channel=channel,
                    status=DeliveryStatus.FAILED,
                    attempts=attempt,
                    elapsed_ms=self._elapsed_ms(started),
                    error=str(exc),
                )
            except Exception as exc:  # noqa: BLE001
                self.logger.exception(
                    "submission_channel_unexpected_exception",
                    extra={
                        "channel": channel,
                        "attempt": attempt,
                        "complaint_id": payload.complaint_id,
                        "correlation_id": payload.correlation_id,
                    },
                )
                return DeliveryResult(
                    channel=channel,
                    status=DeliveryStatus.FAILED,
                    attempts=attempt,
                    elapsed_ms=self._elapsed_ms(started),
                    error=f"unexpected_error:{exc}",
                )

            if attempt < self.retry_policy.max_attempts:
                await asyncio.sleep(self.retry_policy.next_delay(attempt))

        result.elapsed_ms = self._elapsed_ms(started)
        return result

    async def _register_idempotency_key(self, key: str) -> bool:
        async with self._idempotency_lock:
            if key in self._idempotency_keys:
                return False
            self._idempotency_keys.add(key)
            return True

    @staticmethod
    def _build_idempotency_key(payload: SubmissionPayload) -> str:
        return f"{payload.complaint_id}:{payload.correlation_id}"

    @staticmethod
    def _resolve_overall_status(results: Iterable[DeliveryResult]) -> DeliveryStatus:
        statuses = [result.status for result in results]
        if not statuses:
            return DeliveryStatus.SKIPPED
        if all(status == DeliveryStatus.SUCCESS for status in statuses):
            return DeliveryStatus.SUCCESS
        if any(status == DeliveryStatus.SUCCESS for status in statuses):
            return DeliveryStatus.SUCCESS
        if all(status == DeliveryStatus.SKIPPED for status in statuses):
            return DeliveryStatus.SKIPPED
        return DeliveryStatus.FAILED

    @staticmethod
    def _elapsed_ms(started: float) -> int:
        return int((time.perf_counter() - started) * 1000)

    @staticmethod
    def _epoch_ms() -> int:
        return int(time.time() * 1000)
