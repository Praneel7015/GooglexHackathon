<p align="center">
  <img src="frontend/public/icons/icon-192x192.png" alt="NammaCity Logo" width="120" />
</p>

<h1 align="center">NammaCity</h1>
<h3 align="center">The Civic Operating System for Bangalore</h3>

<p align="center">
  <a href="#-quick-start"><strong>Quick Start</strong></a> ·
  <a href="#-architecture"><strong>Architecture</strong></a> ·
  <a href="#-api-reference"><strong>API</strong></a> ·
  <a href="#-contributing"><strong>Contributing</strong></a> ·
  <a href="LICENSE"><strong>License</strong></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/hackathon-Google%20×%20DeepStation%20×%20MSRIT-4285F4?style=flat-square&logo=google" alt="Hackathon" />
  <img src="https://img.shields.io/badge/agents-10%20AI%20Agents-FF6F00?style=flat-square&logo=google-gemini" alt="Agents" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License" />
  <img src="https://img.shields.io/badge/frontend-React%20+%20Vite-61DAFB?style=flat-square&logo=react" alt="Frontend" />
  <img src="https://img.shields.io/badge/backend-FastAPI-009688?style=flat-square&logo=fastapi" alt="Backend" />
</p>

---

## 📌 Overview

> *"Bangalore citizens filed 1.2 lakh civic complaints last year. 60% never got resolved. Not because the city doesn't care — because one voice doesn't matter. NammaCity gives a single citizen the power of a thousand."*

**NammaCity** is a multi-agent AI civic operating system built at the **Google × DeepStation × MSRIT Hackathon (May 8–9, 2026)**. It lets any Bangalore citizen photograph a civic issue, get it auto-routed to the right authority across 30+ agencies, bundled with similar nearby complaints, escalated automatically through a 30-day enforcement ladder, and tracked on a public accountability dashboard.

### ✨ Key Features

| Feature | Description |
|---|---|
| 📸 **One-Tap Reporting** | Take a photo + voice note in Kannada/Hindi/English/Tamil — AI handles the rest |
| 🤖 **10-Agent AI Pipeline** | Reporter → Geo → Routing → Crowd Validation → Drafting → Submission → Escalation → Prediction → Dashboard → Engagement |
| 🗺️ **Crowd Validation** | Bundles similar nearby complaints (geo + semantic clustering) — 47 reports get fixed, 1 gets ignored |
| ⚡ **Auto-Escalation** | Day 7 councillor tag → Day 14 RTI → Day 21 MLA + media → Day 30 PIL outline |
| 📊 **Public Dashboard** | Live Bangalore heatmap, ward leaderboards, officer scorecards — officials change behavior when measured publicly |
| 📱 **PWA** | Installable on any device — scan a QR code and go |
| 🔐 **Firebase Auth** | Email + password authentication with user-scoped issue tracking |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (PWA)                           │
│  React 18 · Vite · Tailwind CSS · Leaflet.js · Zustand          │
│  Firebase Auth · QR Install · Service Worker                    │
└────────────────────────────┬────────────────────────────────────┘
                             │  REST API
┌────────────────────────────▼────────────────────────────────────┐
│                     BACKEND (FastAPI)                            │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ Reporter │→ │   Geo    │→ │ Routing  │→ │ Crowd Validation │ │
│  │  Agent   │  │  Agent   │  │  Agent   │  │     Agent        │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┬─────────┘ │
│                                                      │           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────▼─────────┐ │
│  │Prediction│← │Escalation│← │Submission│← │    Drafting      │ │
│  │  Agent   │  │  Agent   │  │  Agent   │  │     Agent        │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
│                                                                 │
│  Orchestration: Google ADK  ·  LLM: Gemini 2.5 Pro             │
└───────┬──────────────┬──────────────┬───────────────────────────┘
        │              │              │
   ┌────▼────┐   ┌─────▼─────┐  ┌────▼────┐
   │Supabase │   │  Qdrant   │  │ Twitter │
   │PostgreSQL│  │ Vector DB │  │ Gmail   │
   │+ PostGIS │  │           │  │WhatsApp │
   └──────────┘  └───────────┘  └─────────┘
```

### Agent Pipeline

| # | Agent | Role |
|---|---|---|
| 1 | **Reporter** | Multimodal entry — classifies issue type, severity, spam detection via Gemini |
| 2 | **Geo** | Extracts GPS from EXIF or Gemini vision, reverse-geocodes, maps to BBMP ward/zone |
| 3 | **Routing** | Routes to the correct civic agency from 30+ (BBMP, BESCOM, BWSSB, BMTC, etc.) |
| 4 | **Crowd Validation** | Geo + semantic clustering — bundles similar complaints within 500m radius |
| 5 | **Drafting** | Generates formal letter, tweet, email, WhatsApp message, RTI template |
| 6 | **Submission** | Multi-channel dispatch — Twitter API, Gmail SMTP, BBMP portal pre-fill |
| 7 | **Escalation** | 30-day enforcement ladder with automatic pressure escalation |
| 8 | **Prediction** | Resolution likelihood and ward-level historical analysis |
| 9 | **Dashboard** | Public accountability dashboard with heatmaps and leaderboards |
| 10 | **Engagement** | Civic Karma points, badges, and ward leaderboards |

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React 18, Vite, Tailwind CSS | PWA with installable app experience |
| **State** | Zustand | Lightweight global state management |
| **Maps** | Leaflet.js + OpenStreetMap | Free, interactive civic issue mapping |
| **Backend** | Python FastAPI + Uvicorn | Async API server with WebSocket support |
| **AI Orchestration** | Google ADK | Multi-agent coordination |
| **LLM** | Gemini 2.5 Pro | Multimodal — photo + voice + text analysis |
| **Embeddings** | Gemini text-embedding-004 | Semantic duplicate detection & clustering |
| **Database** | Supabase (PostgreSQL + PostGIS) | Geospatial queries, complaint storage |
| **Vector DB** | Qdrant Cloud | Semantic similarity search for crowd validation |
| **Auth** | Firebase Auth | Email/password authentication |
| **Hosting** | Firebase Hosting (frontend), Cloud Run (backend) | Serverless deployment |
| **Twitter** | Twitter API v2 (Tweepy) | Public complaint submission |
| **Email** | Gmail SMTP | Ward officer notifications |
| **CI/CD** | GitHub Actions | Automated Firebase Hosting deploys |

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** ≥ 20.x
- **Python** ≥ 3.11
- **Git**

### 1. Clone the Repository

```bash
git clone https://github.com/Praneel7015/GooglexHackathon.git
cd GooglexHackathon
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys (see Environment Variables section below)

# Run the development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env — set VITE_API_BASE_URL to your backend URL

# Run the dev server
npm run dev
```

The app will be available at `http://localhost:5173`.

### 4. Database Setup

1. Create a [Supabase](https://supabase.com) project
2. Run the schema in the SQL editor:
   ```
   backend/db/schema.sql
   ```
3. (Optional) Seed synthetic complaints for demo:
   ```bash
   python backend/db/seed_complaints.py
   ```

---

## 🔑 Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Required |
|---|---|---|
| `SUPABASE_URL` | Supabase project URL | ✅ |
| `SUPABASE_KEY` | Supabase anon/service key | ✅ |
| `GEMINI_API_KEY` | Google Gemini API key | ✅ |
| `QDRANT_URL` | Qdrant Cloud cluster URL | ✅ |
| `QDRANT_API_KEY` | Qdrant API key | ✅ |
| `TWITTER_API_KEY` | Twitter API consumer key | Optional |
| `TWITTER_API_SECRET` | Twitter API consumer secret | Optional |
| `TWITTER_ACCESS_TOKEN` | Twitter access token | Optional |
| `TWITTER_ACCESS_TOKEN_SECRET` | Twitter access token secret | Optional |
| `GMAIL_USER` | Gmail address for sending emails | Optional |
| `GMAIL_APP_PASSWORD` | Gmail app password (requires 2FA) | Optional |
| `ENVIRONMENT` | `dev` or `production` | Optional |

### Frontend (`frontend/.env`)

| Variable | Description | Default |
|---|---|---|
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000` |

---

## 📡 API Reference

### Health & Info

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health check |
| `GET` | `/api/v1/info` | Version, environment, active agents |

### Core Pipeline

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/report` | Submit a civic complaint (photo + optional voice note) |

**`POST /api/v1/report`** — Multipart form data:
- `photo` (file, required) — Photo of the civic issue
- `voice_note` (file, optional) — Voice memo in any language
- `language` (string) — `en`, `kn`, `hi`, `ta`
- `fallback_lat`, `fallback_lng` (float) — GPS coordinates if not in EXIF
- `user_name`, `user_email` (string) — Reporter info

### Complaints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/complaints` | List complaints (filterable by status, ward, issue type) |
| `GET` | `/api/v1/complaints/{id}` | Detailed complaint view with escalation timeline |

### Dashboard

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/dashboard/stats` | Aggregate stats + ward leaderboard |
| `GET` | `/api/v1/dashboard/map` | All complaints + cluster centroids for Leaflet map |
| `GET` | `/api/v1/dashboard/clusters` | Active crowd-validation clusters |

### Prediction

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/predict` | Resolution likelihood by ward and issue type |

### Admin

| Method | Endpoint | Description |
|---|---|---|
| `PATCH` | `/api/v1/admin/complaints/{id}/status` | Update complaint status (requires `X-Admin-Token` header) |

---

## 📂 Project Structure

```
GooglexHackathon/
├── backend/
│   ├── agents/                 # 10 AI agent modules
│   │   ├── base.py             # Agent base class & I/O contracts
│   │   ├── reporter.py         # Multimodal issue classification
│   │   ├── geo.py              # GPS extraction & ward mapping
│   │   ├── routing.py          # Agency routing (30+ agencies)
│   │   ├── crowd_validation.py # Geo + semantic clustering
│   │   ├── drafting.py         # Multi-format complaint drafting
│   │   ├── submission.py       # Multi-channel dispatch
│   │   ├── escalation.py       # 30-day enforcement ladder
│   │   ├── prediction.py       # Resolution likelihood
│   │   ├── adk_agent.py        # Google ADK integration
│   │   └── gemini_client.py    # Gemini API wrapper
│   ├── db/
│   │   ├── schema.sql          # PostgreSQL + PostGIS schema
│   │   ├── client.py           # Supabase client & queries
│   │   ├── seed.py             # Reference data seeder
│   │   └── seed_complaints.py  # Synthetic complaint generator
│   ├── integrations/
│   │   ├── twitter.py          # Twitter API v2 (Tweepy)
│   │   ├── gmail.py            # Gmail SMTP integration
│   │   ├── whatsapp.py         # WhatsApp (stubbed)
│   │   └── qdrant_client.py    # Qdrant vector DB client
│   ├── models/
│   │   └── schemas.py          # Pydantic request/response models
│   ├── main.py                 # FastAPI entry point & routes
│   ├── config.py               # Settings via pydantic-settings
│   ├── Dockerfile              # Multi-stage Docker build
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── public/                 # PWA assets, icons, manifest
│   ├── src/
│   │   ├── components/
│   │   │   ├── AppShell.jsx    # Authenticated app layout
│   │   │   ├── PublicShell.jsx # Public landing layout
│   │   │   └── BangaloreMap.jsx# Leaflet map component
│   │   ├── pages/
│   │   │   ├── Landing.jsx     # Public landing page
│   │   │   ├── Auth.jsx        # Login / signup
│   │   │   ├── Dashboard.jsx   # Civic health dashboard
│   │   │   ├── Track.jsx       # Complaint tracking
│   │   │   ├── Leaderboard.jsx # Ward leaderboard
│   │   │   ├── Admin.jsx       # Admin complaint management
│   │   │   ├── Settings.jsx    # User settings
│   │   │   └── capture/        # Photo/voice capture flow
│   │   ├── lib/
│   │   │   ├── store.js        # Zustand global state
│   │   │   ├── api.js          # API client helpers
│   │   │   └── firebase.js     # Firebase Auth config
│   │   ├── App.jsx             # React Router definitions
│   │   └── main.jsx            # App entry point
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── firebase.json           # Firebase Hosting config
├── scripts/
│   ├── deploy.sh               # Deployment helper
│   ├── generate_synthetic_complaints.py
│   └── scrape_ward_officers.py
├── docs/                       # Documentation (expandable)
├── .github/workflows/          # CI/CD — Firebase Hosting deploys
├── NammaCity-Master-Build-Doc.md
├── LICENSE
└── README.md
```

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch:
   ```bash
   git checkout -b feat/your-feature
   ```
3. **Commit** your changes with clear messages:
   ```bash
   git commit -m "feat: add ward boundary visualization"
   ```
4. **Push** to your fork:
   ```bash
   git push origin feat/your-feature
   ```
5. **Open a Pull Request** against `main`

### Development Guidelines

- Follow existing code style and folder structure
- Add docstrings for new backend functions
- Test the full pipeline locally before submitting
- Keep commits atomic and messages descriptive

---

## 👥 Team

Built in 31 hours at the **Google × DeepStation × MSRIT Hackathon** (May 8–9, 2026) by:

| Name | GitHub |
|---|---|
| **Praneel S** | [@Praneel7015](https://github.com/Praneel7015) |
| **Ojasvi Poonia** | [@Ojasvi-Poonia](https://github.com/Ojasvi-Poonia) |
| **Owais Saud Tanveer** | [@Owais-cmd](https://github.com/Owais-cmd) |
| **Deepika Thota** | [@ThotaDeepika](https://github.com/thotaDeepika)|

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Google ADK** — Multi-agent orchestration framework
- **Gemini 2.5 Pro** — Multimodal AI powering all 10 agents
- **Supabase** — PostgreSQL + PostGIS backend
- **Qdrant** — Vector similarity search for crowd validation
- **OpenStreetMap & Nominatim** — Free geocoding and map tiles
- **Firebase** — Authentication and frontend hosting
- **BBMP Open Data** — Ward boundaries and civic reference data

---

<p align="center">
  <strong>NammaCity</strong> — Every voice heard. Every ward accountable. Every issue resolved. 🇮🇳
</p>
