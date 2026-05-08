# Submission Integrations

## Setup

### Twitter (@nammacity_blr)
1. Create a Twitter/X developer account at developer.twitter.com
2. Apply for free tier (500 tweets/month)
3. Create an app, get all 4 OAuth 1.0a keys
4. Add to `.env`:
   ```
   TWITTER_API_KEY=...
   TWITTER_API_SECRET=...
   TWITTER_ACCESS_TOKEN=...
   TWITTER_ACCESS_TOKEN_SECRET=...
   ```

### Gmail (complaints@nammacity.in)
1. Create a Google account for NammaCity
2. Enable 2-Factor Authentication
3. Generate an App Password at myaccount.google.com/apppasswords
4. Add to `.env`:
   ```
   GMAIL_USER=complaints@nammacity.in
   GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
   ```

### WhatsApp
Stubbed for hackathon. Meta Business API approval takes weeks.
No env vars needed — all calls return `mode: stub`.

## Email User-Attribution Model (CRITICAL)

NammaCity drives the send (zero user friction) but BBMP sees and
replies to the actual citizen:

```
From: NammaCity <complaints@nammacity.in>     ← always our address
To: ward95@bbmp.gov.in                        ← BBMP officer
Cc: citizen@gmail.com                         ← the citizen (optional)
Reply-To: citizen@gmail.com                   ← BBMP replies go here
Body: "Submitted by: Citizen Name <citizen@gmail.com>"
```

If citizen doesn't provide email: complaint sends from NammaCity only,
no Cc, no Reply-To override. Pipeline still works.

## API Reference

### TwitterIntegration
```python
twitter = TwitterIntegration()  # reads from config.settings
result = await twitter.send(payload)
# result: DeliveryResult { status, provider_message_id, external_ref, mode }
```
- STUB when credentials missing (returns fake URL)
- LIVE posts via tweepy OAuth 1.0a
- Auto-truncates to 280 chars
- Rate limit: 500 tweets/month (free tier)

### GmailIntegration
```python
gmail = GmailIntegration()  # reads from config.settings
result = await gmail.send(
    payload,
    cc="citizen@gmail.com",          # citizen's email
    reply_to="citizen@gmail.com",    # BBMP replies go to citizen
    bcc="records@nammacity.in",      # optional internal copy
)
# result: DeliveryResult { status, provider_message_id, mode }
```
- STUB when credentials missing
- LIVE sends via smtp.gmail.com:587 STARTTLS
- Supports HTML + plain text body
- Rate limit: 500 emails/day (free Gmail)

### WhatsAppIntegration
```python
wa = WhatsAppIntegration()
result = await wa.send(payload)
# Always returns mode='stub'
```

## For the Submission Agent (next phase)
- Call all three clients in parallel via asyncio.gather
- Each returns DeliveryResult with success/error/mode fields
- Pipeline must NOT crash if a client fails
- For email: pass citizen's email as `cc` AND `reply_to` when available
