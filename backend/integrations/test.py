import asyncio
import sys
from pathlib import Path

# Allow running this script directly from backend/integrations.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.agents.submission import SubmissionService
from backend.integrations.contracts import SubmissionPayload
from backend.integrations.twitter import TwitterConfig, TwitterIntegration
from backend.integrations.gmail import GmailConfig, GmailIntegration
from backend.integrations.whatsapp import WhatsAppConfig, WhatsAppIntegration
import os

from dotenv import load_dotenv
load_dotenv()
bearer_token = os.getenv("X_Bearer_token")




async def main() -> None:
    # Start with dry_run=True for all channels
    twitter = TwitterIntegration(
        TwitterConfig(
            dry_run=True,
            bearer_token=bearer_token,
        )
    )

    gmail = GmailIntegration(
        GmailConfig(
            dry_run=False,
            username="owaistab18@gmail.com",
            password="ekrd lqbw yqpl ctpl",
            from_email="owaistab18@gmail.com",
        )
    )

    whatsapp = WhatsAppIntegration(
        WhatsAppConfig(
            dry_run=False,
            endpoint_url="https://graph.facebook.com/v25.0/1129321136928938/messages",
            bearer_token="EAAyEOhTsZAzwBRe4vIOFiaZAAkv26xNIHMu1qNwT6RQXDPtJBCGzZApY9ztGIjTOpXqxvMy4X8ZBu2MvMjSpT9AZAecZBFK8Fk3xSDhkJqw0HX8fh91pLB5i9afCagViA8kL7Ti6US3CyKVDMRBCiK82PRtgwcGSd24uR8PSldP3MieWn2IfFIH0NDg9lJejmqn0UUZABL7bLSOwZCXjioYs75nZBVcSaLzenPwjTdytqZB7xung5ALw28t6WxmBZCiR2PvX1QLL2smz1Ky1gLtihBQAAQ5",
        )
    )

    service = SubmissionService([twitter, gmail, whatsapp])

    payload = SubmissionPayload(
        complaint_id="cmp-001",
        correlation_id="corr-001",
        subject="Pothole near MSRIT gate",
        body_text="Large pothole causing traffic hazard.",
        recipients=["recipient@example.com"],
        twitter_handle="@BBMPCOMM",
        metadata={"whatsapp_contacts": ["+917996515179"]},
    )

    summary = await service.submit(payload)
    print("OVERALL:", summary.overall_status.value)
    for channel, result in summary.per_channel.items():
        print(
            channel,
            result.status.value,
            "attempts=", result.attempts,
            "error=", result.error,
            "provider_id=", result.provider_message_id,
        )
        print(result.raw_response)


if __name__ == "__main__":
    asyncio.run(main())