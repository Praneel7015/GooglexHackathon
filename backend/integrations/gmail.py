from __future__ import annotations

import asyncio
import smtplib
import time
from dataclasses import dataclass
from email.message import EmailMessage
from uuid import uuid4

from .contracts import DeliveryResult, DeliveryStatus, SubmissionPayload


@dataclass(slots=True)
class GmailConfig:
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    username: str | None = None
    password: str | None = None
    from_email: str | None = None
    use_starttls: bool = True
    timeout_seconds: float = 10.0
    dry_run: bool = True


class GmailIntegration:
    channel = "gmail"

    def __init__(self, config: GmailConfig) -> None:
        self.config = config

    async def send(self, payload: SubmissionPayload) -> DeliveryResult:
        started = time.perf_counter()

        if not payload.recipients:
            return DeliveryResult(
                channel=self.channel,
                status=DeliveryStatus.SKIPPED,
                attempts=1,
                elapsed_ms=self._elapsed_ms(started),
                error="no_recipients",
            )

        if self.config.dry_run or not self.config.username or not self.config.password:
            return DeliveryResult(
                channel=self.channel,
                status=DeliveryStatus.SUCCESS,
                attempts=1,
                elapsed_ms=self._elapsed_ms(started),
                provider_message_id=f"dryrun-mail-{uuid4().hex[:10]}",
                raw_response={"mode": "dry_run", "recipients": payload.recipients},
            )

        try:
            message_id = await asyncio.to_thread(self._send_smtp, payload)
            return DeliveryResult(
                channel=self.channel,
                status=DeliveryStatus.SUCCESS,
                attempts=1,
                elapsed_ms=self._elapsed_ms(started),
                provider_message_id=message_id,
                raw_response={"recipients": payload.recipients},
            )
        except smtplib.SMTPException as exc:
            return DeliveryResult(
                channel=self.channel,
                status=DeliveryStatus.FAILED,
                attempts=1,
                elapsed_ms=self._elapsed_ms(started),
                error=f"smtp_error:{exc}",
            )
        except Exception as exc:  # noqa: BLE001
            return DeliveryResult(
                channel=self.channel,
                status=DeliveryStatus.FAILED,
                attempts=1,
                elapsed_ms=self._elapsed_ms(started),
                error=f"unexpected_error:{exc}",
            )

    def _send_smtp(self, payload: SubmissionPayload) -> str:
        message = EmailMessage()
        message["Subject"] = payload.subject
        message["From"] = self.config.from_email or self.config.username
        message["To"] = ", ".join(payload.recipients)
        message["X-Correlation-ID"] = payload.correlation_id
        message.set_content(payload.body_text)
        if payload.body_html:
            message.add_alternative(payload.body_html, subtype="html")

        with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=self.config.timeout_seconds) as smtp:
            smtp.ehlo()
            if self.config.use_starttls:
                smtp.starttls()
                smtp.ehlo()
            smtp.login(self.config.username, self.config.password)
            smtp.send_message(message)
        return message["Message-ID"] or f"smtp-{uuid4().hex[:12]}"

    @staticmethod
    def _elapsed_ms(started: float) -> int:
        return int((time.perf_counter() - started) * 1000)
