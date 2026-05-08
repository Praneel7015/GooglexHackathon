# NammaCity Backend — Run Guide

## Prerequisites

- Python 3.11+
- Supabase project (URL + anon key)
- Gemini API key
- Qdrant Cloud account (or use in-memory fallback)
- Twitter API v2 keys (optional — falls back to stub mode)
- Gmail App Password (optional — falls back to stub mode)

---

## 1. Environment Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate (Windows)
source .venv/Scripts/activate

# Activate (Mac/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 2. Configure Environment

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

Minimum required values:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
GEMINI_API_KEY=your-gemini-key
```

Optional (all fall back to stub/demo mode if blank):

```env
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-qdrant-key

TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_TOKEN_SECRET=

GMAIL_USER=you@gmail.com
GMAIL_APP_PASSWORD=your-16-char-app-password
```

---

## 3. Database Setup

Run this once in your **Supabase SQL Editor**:

```
backend/db/schema.sql
```

Paste the entire file contents and execute. This creates:
- `agencies`, `ward_officers`, `complaints`, `clusters`
- `submissions`, `escalations`
- PostGIS spatial indexes
- `get_complaints_in_radius` and `get_open_complaints_map` RPC functions

---

## 4. Seed Reference Data

```bash
# Activate venv first
source .venv/Scripts/activate

# Seed agencies and ward officers (run once)
python db/seed.py

# Seed 200 synthetic historical complaints + Qdrant embeddings
# Required for crowd validation clustering demo
python db/seed_complaints.py
```

`seed_complaints.py` will:
- Insert 200 synthetic complaints distributed across 10 Bangalore wards
- Embed each complaint description via Gemini and upsert into Qdrant
- Weight complaints heavily near MSRIT (Wards 95/96/97) for demo clustering effect

---

## 5. Run the Server

```bash
source .venv/Scripts/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API is now live at: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

---

## 6. Run Tests

```bash
source .venv/Scripts/activate
pytest -v
```

Tests that require live API keys are auto-skipped when keys are absent.

---

## API Reference

### Core Pipeline

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/report` | Submit complaint — runs full 9-step pipeline |
| `GET`  | `/health` | Health check |
| `GET`  | `/api/v1/info` | Version and agent list |

### Complaint Queries

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/complaints` | List complaints (filterable by status, ward, type) |
| `GET` | `/api/v1/complaints/{id}` | Single complaint with escalation timeline + prediction |

### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/dashboard/stats` | Aggregate totals, top issues, ward leaderboard |
| `GET` | `/api/v1/dashboard/map` | All geo-located complaints for Leaflet.js map |
| `GET` | `/api/v1/dashboard/clusters` | Active crowd-validation clusters for heatmap |

### Prediction

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/predict?ward_number=95&issue_type=pothole` | Resolution likelihood for a ward + issue |

---

## POST /api/v1/report — Request Format

`multipart/form-data`:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `photo` | file | Yes | JPEG/PNG civic issue photo |
| `voice_note` | file | No | Audio in any format (transcribed by Gemini) |
| `language` | string | No | `en` \| `kn` \| `hi` — default `en` |
| `fallback_lat` | float | No | GPS latitude if photo has no EXIF |
| `fallback_lng` | float | No | GPS longitude if photo has no EXIF |
| `user_name` | string | No | For email attribution |
| `user_email` | string | No | Added as CC on ward officer email |

### Response shape

```json
{
  "complaint_id": "uuid",
  "reporter": { "issue_type": "pothole", "severity": 4, "spam_score": 0.02 },
  "geo": { "lat": 12.98, "lng": 77.56, "ward_number": 95, "ward_name": "Malleshwaram" },
  "routing": { "primary_agency": { "name": "BBMP" }, "ward_officer": { "email": "..." } },
  "crowd_validation": { "is_bundled": true, "member_count": 38, "cluster_id": "uuid" },
  "drafting": { "email_subject": "...", "tweet_text": "...", "whatsapp_text": "..." },
  "submission": { "status": "sent", "submitted_channels": [...], "primary_reference": "..." },
  "escalation": { "scheduled": true, "timeline": [{ "day": 0 }, { "day": 7 }, ...] },
  "prediction": { "confidence_message": "72% chance of resolution in ~18 days", "resolution_rate": 0.72 },
  "pipeline_latency_ms": 3241.5
}
```

---

## Agent Pipeline

```
Photo + Voice
     │
     ▼
[1] ReporterAgent    — Gemini multimodal → issue_type, severity, spam_score
     │
     ▼
[2] GeoAgent         — EXIF GPS → Nominatim → BBMP ward mapping
     │
     ▼
[3] RoutingAgent     — issue_type → agency + ward officer lookup
     │
     ▼
[4] DB Insert        — Supabase PostGIS complaint row
     │
     ▼
[5] CrowdValidationAgent  — Geo radius + Qdrant semantic cluster → bundle
     │
     ▼
[6] DraftingAgent    — 5 parallel Gemini calls → EN email, KN email, tweet, WhatsApp, RTI
     │
     ▼
[7] SubmissionAgent  — Twitter + Gmail + WhatsApp parallel dispatch (milestone suppression)
     │
     ▼
[8] EscalationAgent  — Schedules day 0/7/14/21/30 enforcement ladder in DB
     │
     ▼
[9] PredictionAgent  — Ward history → resolution likelihood stat
```

---

## Features

### Reporter Agent
- Gemini 2.5 Flash multimodal classification across 30 civic issue types
- Severity scoring 1–5
- Spam/AI-generated image detection
- Voice note transcription (Kannada, Hindi, English, Tamil)

### Geo Agent
- Extracts GPS from photo EXIF metadata
- Falls back to browser-provided coordinates
- Reverse-geocodes via OpenStreetMap Nominatim
- Maps to BBMP ward, zone, MLA constituency

### Routing Agent
- Pre-mapped routing table for 30+ civic issue types
- Routes across BBMP, BESCOM, BWSSB, BMTC, Traffic Police, KSPCB, BMRCL, RERA, Forest Dept
- Fetches ward officer contact (email, phone) from DB

### Crowd Validation Agent (THE MOAT)
- Dual clustering: geo radius (200–500m) + Qdrant semantic similarity (>0.85)
- Auto-bundles when 3+ independent complaints match
- Generates aggregated complaint description via Gemini
- Milestone suppression: only re-notifies at 1, 3, 5, 10, 25, 50 member milestones

### Drafting Agent
- 5 parallel Gemini calls per complaint
- English formal complaint email with Karnataka Municipal Corporations Act citations
- Kannada translation
- 280-char tweet with correct agency handle
- Bilingual WhatsApp message
- RTI application template

### Submission Agent
- Simultaneous Twitter, Gmail, WhatsApp dispatch
- Stub fallback on all channels when credentials absent (safe for demo)
- Per-channel status tracking persisted to `submissions` table
- CC citizen's email on ward officer email

### Escalation Agent
- Schedules full 30-day enforcement ladder at complaint creation
- Day 0: initial submission
- Day 7: ward councillor Twitter tag
- Day 14: RTI application drafted
- Day 21: MLA + local media (@TimesofIndia_blr, @DeccanHerald) tagged
- Day 30: PIL outline drafted
- Idempotency keys prevent double-scheduling

### Prediction Agent
- Queries historical seeded complaints per ward
- Computes resolution rate, average days to resolve
- Issue-type multipliers (tree_fall resolves faster than pothole)
- Ward leaderboard for dashboard

### Public Dashboard APIs
- Map endpoint: all geo-located complaints for Leaflet.js
- Cluster endpoint: active crowd-validation bundles
- Stats endpoint: totals, top issues, hotspot wards, ward leaderboard
- Complaint detail: full escalation timeline + inline prediction
