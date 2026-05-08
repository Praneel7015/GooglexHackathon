# Submission Integrations (Portable Module)

This module is intentionally self-contained so it can be plugged into any FastAPI/service layer once the core app foundation is ready.

## Provided adapters

- `TwitterIntegration` (`twitter.py`)
- `GmailIntegration` (`gmail.py`)
- `WhatsAppIntegration` (`whatsapp.py`)

## Shared contracts

- `SubmissionPayload`
- `DeliveryResult`
- `DeliveryStatus`
- `RetryPolicy`
- `SubmissionIntegration` protocol

All contracts are defined in `contracts.py`.

## Usage with submission service

```python
from agents.submission import SubmissionService
from integrations.gmail import GmailConfig, GmailIntegration
from integrations.twitter import TwitterConfig, TwitterIntegration
from integrations.whatsapp import WhatsAppConfig, WhatsAppIntegration
from integrations.contracts import SubmissionPayload

service = SubmissionService(
    integrations=[
        TwitterIntegration(TwitterConfig(dry_run=True)),
        GmailIntegration(GmailConfig(dry_run=True)),
        WhatsAppIntegration(WhatsAppConfig(dry_run=True)),
    ]
)

payload = SubmissionPayload(
    complaint_id="cmp-001",
    correlation_id="corr-001",
    subject="Pothole near MSRIT gate",
    body_text="Large pothole causing traffic slowdown.",
    recipients=["ward.officer@example.com"],
    metadata={"whatsapp_contacts": ["+919999999999"]},
)

summary = await service.submit(payload)
```

## Portability choices

- Uses Python stdlib networking (`urllib`, `smtplib`) to avoid extra dependency coupling.
- Every adapter supports `dry_run=True` for local testing and demo mode.
- All integrations are async-friendly (`asyncio.to_thread` for blocking operations).
