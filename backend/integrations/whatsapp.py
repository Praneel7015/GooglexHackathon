from __future__ import annotations

import logging
import time
from uuid import uuid4

from .contracts import DeliveryResult, DeliveryStatus, SubmissionPayload

logger = logging.getLogger("nammacity.integrations.whatsapp")


class WhatsAppIntegration:
    """
    WhatsApp integration — STUB ONLY for hackathon.
    Meta Business API approval takes weeks. Logs the message, returns success.
    """

    channel = "whatsapp"

    async def send(self, payload: SubmissionPayload) -> DeliveryResult:
        started = time.perf_counter()
        contacts = payload.metadata.get("whatsapp_contacts", [])

        message_preview = (
            f"{payload.subject}: {payload.body_text}"[:100]
        )

        logger.info(
            "WhatsApp STUB: would send to %s — %s",
            contacts or "no contacts",
            message_preview,
        )

        return DeliveryResult(
            channel=self.channel,
            status=DeliveryStatus.SUCCESS,
            attempts=1,
            elapsed_ms=self._elapsed_ms(started),
            provider_message_id=f"stub-wa-{uuid4().hex[:10]}",
            raw_response={
                "mode": "stub",
                "contacts": contacts,
                "message_preview": message_preview,
                "note": "Pending Meta Business API verification",
            },
        )

    @staticmethod
    def _elapsed_ms(started: float) -> int:
        return int((time.perf_counter() - started) * 1000)
