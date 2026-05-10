"""
Email integration using Resend HTTP API (works on Railway/Docker).
Falls back to SMTP if Resend key not set but Gmail creds are available.
"""

from __future__ import annotations

import asyncio
import logging
import time
from uuid import uuid4

import httpx

from .contracts import DeliveryResult, DeliveryStatus, SubmissionPayload
from config import settings

logger = logging.getLogger("nammacity.integrations.email")

RESEND_API_URL = "https://api.resend.com/emails"


class GmailIntegration:
    """
    Email integration with user-attribution support.
    Primary: Resend HTTP API (works everywhere including Railway).
    Fallback: STUB mode if no credentials.
    """

    channel = "email"

    async def send(
        self,
        payload: SubmissionPayload,
        cc: str | list[str] | None = None,
        bcc: str | list[str] | None = None,
        reply_to: str | None = None,
    ) -> DeliveryResult:
        started = time.perf_counter()

        if not payload.recipients:
            return DeliveryResult(
                channel=self.channel,
                status=DeliveryStatus.SKIPPED,
                attempts=1,
                elapsed_ms=self._elapsed_ms(started),
                error="no_recipients",
            )

        resend_key = getattr(settings, 'resend_api_key', '') or ''
        gmail_user = settings.gmail_user or ''
        gmail_pass = settings.gmail_app_password or ''
        from_email = gmail_user or "NammaCity <onboarding@resend.dev>"

        if not resend_key and not (gmail_user and gmail_pass):
            # STUB mode — no credentials at all
            return DeliveryResult(
                channel=self.channel,
                status=DeliveryStatus.SUCCESS,
                attempts=1,
                elapsed_ms=self._elapsed_ms(started),
                provider_message_id=f"stub-mail-{uuid4().hex[:10]}",
                raw_response={"mode": "stub", "recipients": payload.recipients, "cc": cc, "reply_to": reply_to},
            )

        # Try Gmail SMTP if credentials are available (works on GCP, not Railway)
        if not resend_key and gmail_user and gmail_pass:
            try:
                import smtplib
                from email.message import EmailMessage
                message_id = await asyncio.to_thread(
                    self._send_smtp, payload, gmail_user, gmail_pass, cc, bcc, reply_to
                )
                return DeliveryResult(
                    channel=self.channel,
                    status=DeliveryStatus.SUCCESS,
                    attempts=1,
                    elapsed_ms=self._elapsed_ms(started),
                    provider_message_id=message_id,
                    raw_response={"mode": "live", "method": "smtp", "recipients": payload.recipients, "cc": cc, "reply_to": reply_to},
                )
            except Exception as exc:
                logger.warning("SMTP failed: %s", exc)
                return DeliveryResult(
                    channel=self.channel,
                    status=DeliveryStatus.FAILED,
                    attempts=1,
                    elapsed_ms=self._elapsed_ms(started),
                    error=f"smtp_error:{exc}",
                )

        try:
            message_id = await self._send_resend(
                payload, from_email, resend_key, cc, bcc, reply_to
            )
            return DeliveryResult(
                channel=self.channel,
                status=DeliveryStatus.SUCCESS,
                attempts=1,
                elapsed_ms=self._elapsed_ms(started),
                provider_message_id=message_id,
                raw_response={"mode": "live", "recipients": payload.recipients, "cc": cc, "reply_to": reply_to},
            )
        except Exception as exc:
            logger.warning("Email send failed: %s", exc)
            return DeliveryResult(
                channel=self.channel,
                status=DeliveryStatus.FAILED,
                attempts=1,
                elapsed_ms=self._elapsed_ms(started),
                error=f"email_error:{exc}",
            )

    async def _send_resend(
        self,
        payload: SubmissionPayload,
        from_email: str,
        api_key: str,
        cc: str | list[str] | None,
        bcc: str | list[str] | None,
        reply_to: str | None,
    ) -> str:
        """Send email via Resend HTTP API."""
        cc_list = [cc] if isinstance(cc, str) else (cc or [])
        bcc_list = [bcc] if isinstance(bcc, str) else (bcc or [])

        body = {
            "from": from_email,
            "to": payload.recipients,
            "subject": payload.subject,
            "text": payload.body_text,
        }
        if payload.body_html:
            body["html"] = payload.body_html
        if cc_list:
            body["cc"] = cc_list
        if bcc_list:
            body["bcc"] = bcc_list
        if reply_to:
            body["reply_to"] = reply_to

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                RESEND_API_URL,
                json=body,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )

        if resp.status_code >= 400:
            raise Exception(f"Resend API error {resp.status_code}: {resp.text}")

        data = resp.json()
        return data.get("id", f"resend-{uuid4().hex[:10]}")

    def _send_smtp(self, payload, username, password, cc, bcc, reply_to) -> str:
        """Send via Gmail SMTP_SSL (port 465)."""
        import smtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["Subject"] = payload.subject
        msg["From"] = username
        msg["To"] = ", ".join(payload.recipients)

        if cc:
            cc_list = [cc] if isinstance(cc, str) else cc
            msg["Cc"] = ", ".join(cc_list)
        if reply_to:
            msg["Reply-To"] = reply_to
        if bcc:
            bcc_list = [bcc] if isinstance(bcc, str) else bcc
            msg["Bcc"] = ", ".join(bcc_list)

        msg.set_content(payload.body_text)
        if payload.body_html:
            msg.add_alternative(payload.body_html, subtype="html")

        all_recipients = list(payload.recipients)
        if cc:
            all_recipients.extend([cc] if isinstance(cc, str) else cc)
        if bcc:
            all_recipients.extend([bcc] if isinstance(bcc, str) else bcc)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as smtp:
            smtp.login(username, password)
            smtp.sendmail(username, all_recipients, msg.as_string())

        return msg["Message-ID"] or f"smtp-{uuid4().hex[:12]}"

    @staticmethod
    def _elapsed_ms(started: float) -> int:
        return int((time.perf_counter() - started) * 1000)
