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
class WhatsAppConfig:
    endpoint_url: str | None = None
    bearer_token: str | None = None
    timeout_seconds: float = 8.0
    dry_run: bool = True


class WhatsAppIntegration:
    channel = "whatsapp"

    def __init__(self, config: WhatsAppConfig) -> None:
        self.config = config

    async def send(self, payload: SubmissionPayload) -> DeliveryResult:
        started = time.perf_counter()
        contacts = payload.metadata.get("whatsapp_contacts", [])
        if not isinstance(contacts, list) or not contacts:
            return DeliveryResult(
                channel=self.channel,
                status=DeliveryStatus.SKIPPED,
                attempts=1,
                elapsed_ms=self._elapsed_ms(started),
                error="no_whatsapp_contacts",
            )

        if self.config.dry_run or not self.config.endpoint_url:
            return DeliveryResult(
                channel=self.channel,
                status=DeliveryStatus.SUCCESS,
                attempts=1,
                elapsed_ms=self._elapsed_ms(started),
                provider_message_id=f"dryrun-wa-{uuid4().hex[:10]}",
                raw_response={"mode": "dry_run", "contacts": contacts},
            )

        try:
            response_body = await asyncio.to_thread(self._post_message, payload, contacts)
            return DeliveryResult(
                channel=self.channel,
                status=DeliveryStatus.SUCCESS,
                attempts=1,
                elapsed_ms=self._elapsed_ms(started),
                provider_message_id=response_body.get("message_id"),
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

    def _post_message(self, payload: SubmissionPayload, contacts: list[str]) -> dict:
        # Meta Cloud API accepts one recipient per request for text messages.
        if self._is_meta_cloud_api():
            results: list[dict] = []
            for contact in contacts:
                normalized_contact = self._normalize_phone(contact)
                meta_body = {
                    "messaging_product": "whatsapp",
                    "to": normalized_contact,
                    "type": "text",
                    "text": {
                        "preview_url": False,
                        "body": self._build_message_text(payload),
                    },
                }
                response_payload = self._post_json(meta_body)
                results.append({"to": normalized_contact, "response": response_payload})

            first_message_id = None
            if results:
                message_entries = results[0].get("response", {}).get("messages", [])
                if message_entries:
                    first_message_id = message_entries[0].get("id")
            return {
                "message_id": first_message_id,
                "results": results,
            }

        body = {
            "recipients": contacts,
            "message": {
                "subject": payload.subject,
                "body_text": payload.body_text,
                "correlation_id": payload.correlation_id,
            },
        }
        return self._post_json(body)

    def _post_json(self, body: dict) -> dict:
        encoded = json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.config.bearer_token:
            headers["Authorization"] = f"Bearer {self.config.bearer_token}"
        request = urllib.request.Request(  # noqa: S310
            url=self.config.endpoint_url or "",
            data=encoded,
            method="POST",
            headers=headers,
        )
        with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:  # noqa: S310
            raw = response.read().decode("utf-8")
            return json.loads(raw)

    def _is_meta_cloud_api(self) -> bool:
        endpoint = self.config.endpoint_url or ""
        return "graph.facebook.com" in endpoint and endpoint.endswith("/messages")

    @staticmethod
    def _normalize_phone(contact: str) -> str:
        # Meta API usually expects E.164 digits without '+' in request body.
        return contact.replace("+", "").replace(" ", "").replace("-", "")

    @staticmethod
    def _build_message_text(payload: SubmissionPayload) -> str:
        return (
            f"{payload.subject}\n\n"
            f"{payload.body_text}\n\n"
            f"Complaint ID: {payload.complaint_id}\n"
            f"Ref: {payload.correlation_id}"
        )

    @staticmethod
    def _elapsed_ms(started: float) -> int:
        return int((time.perf_counter() - started) * 1000)
