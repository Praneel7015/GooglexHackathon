# NammaCity — The Civic Operating System for Bangalore

**Master Build Document**
**Hackathon:** Google × DeepStation × MSRIT | May 8–9, 2026
**Duration:** 31 hours | **Theme:** Community Track

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Core Idea](#2-the-core-idea)
3. [Multi-Agent Architecture](#3-multi-agent-architecture)
4. [Tech Stack](#4-tech-stack)
5. [Data Sources & API Strategy](#5-data-sources--api-strategy)
6. [31-Hour Build Plan](#6-31-hour-build-plan)
7. [Risk Register & Mitigations](#7-risk-register--mitigations)
8. [Demo Script](#8-demo-script)
9. [Pre-Hackathon Checklist](#9-pre-hackathon-checklist)
10. [Quick Reference Tables](#10-quick-reference-tables)
11. [Post-Hackathon Vision](#11-post-hackathon-vision)

---

## 1. Executive Summary

### The Pitch (Memorize This)

> *"Bangalore citizens filed 1.2 lakh civic complaints last year. 60% never got resolved. Not because the city doesn't care — because one voice doesn't matter. Watch what happens when AI gives a single citizen the power of a thousand."*

### One-Line Description

A multi-agent AI civic operating system that lets any Bangalore citizen photograph any civic issue, get it auto-routed to the right authority across 30+ agencies, **bundled with similar nearby complaints**, escalated automatically through a 30-day enforcement ladder, and tracked on a public accountability dashboard.

### Why This Wins

- **Solves a pain every judge personally feels** (potholes, garbage, broken streetlights — Bangalore-specific)
- **Genuine multi-agent depth** (10 agents, not 3 dressed up as 10)
- **Uses Google ADK as intended** — orchestrating real parallel workflows
- **Has a moat:** crowd-validation clustering — no other team will think to build this
- **Has teeth:** automated escalation ladder converts AI from messenger to enforcer
- **Has a legacy:** public dashboard makes it useful beyond the hackathon
- **Demo theater is undeniable:** live photo → live tweet → live dashboard update

### Hackathon Acceptance Criteria

- ✅ Uses **Google ADK** (mandatory)
- ✅ Uses **Gemini API** (multimodal: photo + voice + text)
- ✅ Optionally uses Antigravity for code generation
- ✅ Multi-agent system (10 agents)
- ✅ Takes real action — not just chat
- ✅ Uses real APIs (Twitter, Gmail, OpenStreetMap, BBMP open data)
- ✅ End-to-end workflow
- ✅ Strong Indian/Bangalore context

---

## 2. The Core Idea

### Problem Statement

Bangalore's civic governance suffers from compounding failures:

1. **Fragmented authority** — 30+ agencies (BBMP, BESCOM, BWSSB, BMTC, Traffic Police, KSPCB, BMRCL, RERA…) and citizens don't know which handles what
2. **Single-voice powerlessness** — individual complaints get lost; only volume gets attention
3. **No follow-up mechanism** — file and forget
4. **Opaque resolution status** — citizens never know what happened
5. **No public accountability** — officials face no consequence for inaction
6. **Language exclusion** — most civic apps are English-only

### The Solution

NammaCity is a **PWA (Progressive Web App)** where a citizen takes one photo + one voice note in their language. Behind the scenes, a multi-agent system runs:

1. Issue identified via Gemini multimodal
2. Auto-routed to the correct agency
3. **Crowd-validated** — finds similar nearby complaints, bundles them
4. Drafted in proper format and language
5. Submitted across multiple channels (Twitter, email, portal, WhatsApp)
6. **Escalated automatically** through a 30-day enforcement ladder
7. Resolution likelihood predicted from ward history
8. Updated on a **public dashboard** anyone can view

### The Four Differentiators (The Moat)

These are the layers no other hackathon team will build. The basic civic-complaint app loses; this version wins because of these:

| # | Layer | Why It Matters |
|---|---|---|
| 1 | **Crowd Validation** | One pothole report gets ignored. 47 bundled reports get fixed. AI does political organizing automatically. |
| 2 | **Escalation Ladder** | Day 7 councillor tag → Day 14 RTI → Day 21 MLA + media → Day 30 PIL. Converts AI from messenger to enforcer. |
| 3 | **Public Dashboard** | Live Bangalore civic-health map with ward leaderboards. Officials change behavior when measured publicly. |
| 4 | **Multi-Agency Routing** | 30+ agencies pre-mapped. Most citizens file to wrong place; we don't. Practical depth that judges respect. |

---

## 3. Multi-Agent Architecture

**Orchestration:** Google ADK | **Reasoning:** Gemini 2.5 Pro (multimodal) | **Voice:** Gemini Live API

### Agent 1 — Reporter Agent
**Role:** Multimodal entry point.
- Accepts photo + voice in Kannada/Hindi/English/Tamil
- Classifies issue across ~30 types (pothole, garbage, streetlight, water leak, illegal construction, etc.)
- Assigns severity score (1–5)
- Detects spam/duplicates/AI-generated images
- Transcribes voice for context

### Agent 2 — Geo Agent
**Role:** Location intelligence.
- Extracts GPS from photo EXIF
- If GPS missing, uses Gemini vision to identify landmarks
- Reverse-geocodes via OpenStreetMap Nominatim
- Maps to BBMP ward, zone, MLA constituency, MP constituency, police jurisdiction

### Agent 3 — Routing Agent
**Role:** Pick the correct civic agency from 30+.
- Pre-built routing table covering BBMP, BESCOM, BWSSB, BMTC, Traffic Police, KSPCB, BMRCL, RERA, Forest Dept, etc.
- Most citizens file to the wrong agency — this agent fixes that

### Agent 4 — Crowd Validation Agent (THE MOAT)
**Role:** Bundle similar/nearby complaints to amplify pressure.

**The insight:** Government responds to political pressure, not individual requests. AI does the political organizing automatically.

**How it works:**
1. New complaint comes in → geocoded + embedded (Gemini text-embedding-004 on description)
2. Stored in PostgreSQL+PostGIS (geo) + ChromaDB (semantic)
3. For each new complaint, agent runs in parallel:
   - **Geo cluster:** complaints within 200–500m radius
   - **Semantic cluster:** description similarity > 0.85
   - **Time window:** last 30 days
4. If 3+ matches → auto-bundle as "neighborhood issue"
5. Notifies all original complainants: *"47 others reported the same issue. Joint complaint filed."*
6. Generates aggregated complaint with all signatories

### Agent 5 — Drafting Agent
**Role:** Generate complaint content in multiple formats simultaneously.
- Formal complaint letter (English + Kannada) with municipal code citations
- Tweet draft (≤280 chars) tagging right agency handles
- Email to ward officer (using pre-mapped officer database)
- WhatsApp message to councillor
- RTI application template (kept ready for escalation)

### Agent 6 — Submission Agent
**Role:** Multi-channel dispatch.
- **Twitter/X API** (PRIMARY — guaranteed to work, publicly verifiable)
- **Gmail SMTP/API** (email to ward officer)
- **BBMP Sahaaya portal** (pre-fill URL)
- **WhatsApp Business API** or simulation
- **Internal NammaCity dashboard registry**

If one channel fails during demo, others succeed.

### Agent 7 — Escalation Agent (THE TEETH)
**Role:** Ratchet up pressure if no response.

| Day | Action |
|---|---|
| 0 | Initial multi-channel submission |
| 7 | Auto-tweet tagging ward councillor by name |
| 14 | AI-drafted RTI application sent (legally binding 30-day response) |
| 21 | MLA tag + local media (@TimesofIndia_blr, @DeccanHerald) |
| 30 | PIL outline drafted; NGO partner notification |

### Agent 8 — Prediction Agent
**Role:** Set expectations and inform escalation strategy.
- Resolution likelihood: *"73% chance of resolution in 21 days based on Ward 95 history"*
- Ward comparison: *"Ward 174: 89% resolution. Ward 87: 34%."*
- Officer scorecards: *"Officer X: 73% complaints handled, avg 14 days"*
- **Data source:** seed ~200 synthetic historical complaints across wards for demo

### Agent 9 — Dashboard Agent (THE LEGACY LAYER)
**Role:** Render the public accountability dashboard.
- Bangalore heatmap of all open civic issues
- Ward-level resolution leaderboard
- Officer scorecards
- Aggregate stats
- Trending issues

This is what makes NammaCity a public good, not just an app. Officials change behavior when publicly measured.

### Agent 10 — Engagement Agent
**Role:** Retention and virality through gamification.
- Civic Karma points
- Badges: Pothole Hunter, Garbage Crusader, Streetlight Sentinel
- Leaderboards by ward, college (MSRIT vs RVCE vs BMSCE)
- Ward WhatsApp groups (auto-formed)

---

## 4. Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Frontend | **PWA** (React + Vite + Tailwind) | Universal access, looks like an app, judges scan QR → use on their phone |
| PWA enablers | manifest.json + service worker | Installable on home screen |
| Backend | **Python FastAPI** | Async-native, ADK Python integration, WebSocket support |
| Multi-agent | **Google ADK** | Mandatory + natural fit |
| LLM | **Gemini 2.5 Pro** | Multimodal: photo + voice + text |
| Voice | Gemini Live API | Multilingual real-time |
| Embeddings | Gemini text-embedding-004 | Duplicate detection + crowd clustering |
| Primary DB | **PostgreSQL + PostGIS** | Geo radius queries are essential |
| Vector DB | **ChromaDB** | Free, runs locally |
| Maps | **Leaflet.js + OpenStreetMap** | Free, no API key needed |
| Geocoding | Nominatim (OpenStreetMap) | Free reverse-geocoding |
| Twitter | Twitter API v2 | Publicly verifiable, reliable |
| Email | Gmail API / SMTP | Reliable |
| WhatsApp | WhatsApp Business API or simulated | Approval can take time — fallback to simulation |
| Voice escalation | Bland.ai or Vapi (optional) | Real outbound calls |
| Hosting | **Google Cloud Run** | Free hackathon credits |
| Static hosting | Firebase Hosting | Fast PWA deployment |
| Charts | Recharts or Chart.js | Standard, fast |
| Auth | Firebase Auth (Google Sign-in) | Optional, simple |

---

## 5. Data Sources & API Strategy

### Real Working Integrations (No Fakery)

| Source | Purpose | Reliability |
|---|---|---|
| Twitter API v2 | Public complaint submission | ⭐⭐⭐⭐⭐ |
| Gmail SMTP / API | Email to ward officers | ⭐⭐⭐⭐⭐ |
| OpenStreetMap Nominatim | Geocoding | ⭐⭐⭐⭐⭐ |
| BBMP open data (ward GeoJSON) | Ward boundary mapping | ⭐⭐⭐⭐ |
| Karnataka Election Commission | MLA/councillor contacts | ⭐⭐⭐ (scrape once) |

### Stubbed / Simulated (Be Honest)

| Source | Why Stubbed | Fallback |
|---|---|---|
| BBMP Sahaaya portal | No public submission API | Pre-fill URL with one-click submit |
| WhatsApp Business API | Approval takes weeks | Personal WhatsApp Web automation, or simulate |
| Direct BBMP database | Doesn't exist | Twitter as primary channel |

### Data Assets to Pre-Build BEFORE Hackathon

1. **Bangalore ward GeoJSON** — all 198 BBMP ward boundaries
2. **Ward officer contact list** — scrape from BBMP website
3. **Civic agency Twitter handles** — list of ~30 verified handles
4. **Synthetic historical complaints** — ~200 fake complaints across Bangalore (CRITICAL for crowd-validation demo)
5. **Municipal code reference** — Karnataka Municipal Corporations Act key sections
6. **MLA/Councillor contacts** — Karnataka Election Commission

---

## 6. 31-Hour Build Plan

### Hours 0–3: Foundation
- ADK scaffolding + Gemini API testing
- PostgreSQL + PostGIS setup
- ChromaDB setup
- PWA shell (manifest.json, service worker, basic React app)
- Pre-built data ingestion (ward GeoJSON, officer DB, agency table)
- Cloud Run deployment pipeline tested
- Twitter API auth working

### Hours 3–8: Frontend Pipeline (Reporter + Geo + Routing)
- Camera capture in PWA (HTML5 mediaDevices)
- Voice capture (Web Audio API)
- Reporter Agent live (issue classification working)
- Geo Agent live (GPS extraction + ward mapping)
- Routing Agent live (correct agency selection)
- End-to-end test: photo → issue classified → routed

### Hours 8–12: Submission Pipeline (Drafting + Submission)
- Drafting Agent generates English + Kannada
- Twitter API submission working with real test posts
- Email submission working with real test emails
- BBMP Sahaaya pre-fill URL working
- Multi-channel dispatch tested

### Hours 12–18: Crowd Validation (THE DIFFERENTIATOR)
- Seed database with 200 synthetic complaints
- Embed all in ChromaDB
- Geo + semantic clustering logic built
- Bundling logic working
- UI shows "X others reported this nearby"
- Dashboard map updates when bundle forms
- **This must work flawlessly — invest the time here**

### Hours 18–22: Escalation + Prediction
- Escalation timer logic (delayed task scheduling)
- Day-7/14/21/30 escalation actions defined
- Prediction Agent: ward-based historical analysis using seeded data
- UI shows "73% chance of resolution in 21 days"

### Hours 22–26: Public Dashboard (Demo Centerpiece)
- Bangalore-wide map with all complaints (Leaflet.js)
- Ward leaderboard
- Aggregate stats
- Real-time updates via WebSocket or polling
- **Make this beautiful — it's the visual everyone remembers**

### Hours 26–29: Demo Polish
- Dry runs (3 minimum)
- Deck/slides (5 slides max)
- Fix top 3 bugs
- Mobile QR code for judge demos
- Backup video in case of live failure

### Hours 29–31: Buffer
- Last-minute panic
- Final dry run
- Coffee, sleep, mental prep

---

## 7. Risk Register & Mitigations

### Technical Risks

| Risk | Severity | Mitigation |
|---|---|---|
| BBMP Sahaaya portal unreliable for live demo | High | Use Twitter API as primary submission channel — publicly verifiable, never down |
| Crowd validation needs density to look impressive | High | **Seed 200 synthetic complaints BEFORE the hackathon starts** |
| Real BBMP submission requires OTP/captcha | High | Don't promise direct submission. Pre-fill URL + Twitter is the demo |
| Live internet flakiness at venue | Medium | Cache key responses; have a backup video |
| Twitter API rate limits | Medium | Use one Twitter account with elevated access; pre-test rate limits |
| Gemini API throttling under load | Medium | In-memory cache for common queries; streaming responses |
| WhatsApp Business API approval takes weeks | High | Simulate WhatsApp in demo; don't promise real send |
| Voice escalation calls fragile | High | Make this stretch goal — only demo if reliable in dry runs |
| Multi-language voice doesn't recognize accents | Medium | Test Kannada/Hindi specifically with team voices before demo; English fallback |

### Demo Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Live photo capture fails on stage | High | Pre-load backup photo on device; teammate ready to swap |
| Live tweet doesn't appear due to API delay | High | Pre-tweet a similar one 30 sec before demo as proof |
| Crowd-validation cluster doesn't form | High | Verify clustering with seeded data BEFORE going on stage |
| Judge asks "is BBMP submission real?" | High | Honest framing: *"Twitter goes live and is public. BBMP Sahaaya is pre-filled — we don't auto-submit because that's how every responsible system works."* |
| Dashboard doesn't update in real time | Medium | Use polling instead of WebSockets if WS is flaky; 2-sec refresh feels live |
| Demo runs over time | Medium | Practice 3 dry runs; cut by 30 sec each time |

### Process / Team Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Team duplicates work | Medium | Each agent owned by ONE person; daily 10-min syncs |
| Scope creep (10 perfect agents) | High | **3 agents deeply working + 7 stubbed = winning. 10 perfect = 10 broken.** Stick to plan |
| Fatigue mistakes hour 24+ | High | Mandatory 4-hr sleep rotation per person; pair-program after hour 20 |
| Disagreement on priorities mid-build | Medium | Pre-agree: dashboard + crowd validation + Twitter submission are non-negotiable |
| Forgetting demo prep until last minute | High | Deck and demo script due by hour 26, not hour 30 |

### "Hard Question" Defense (Anticipate from Judges)

**Q: How does this differ from BBMP Sahaaya?**
A: Sahaaya only handles BBMP. We route across 30+ agencies. We bundle similar complaints — they don't. We escalate automatically — they don't. We make data public — they don't.

**Q: Is the BBMP submission real?**
A: Twitter submission is real and public. BBMP portal is pre-filled because direct API submission requires OTP we don't have access to — that's a partnership conversation, not a tech problem.

**Q: How do you prevent fake/spam complaints?**
A: Reporter Agent runs spam/AI-generated detection. Geo agent verifies location. Crowd validation requires multiple independent complaints — fake ones won't cluster.

**Q: How do you scale to all of India?**
A: Architecture is agency-agnostic. Add new agencies to routing table; ward GeoJSONs are publicly available for major Indian cities.

**Q: What's the business model?**
A: Free for citizens. SaaS for municipal corporations who want their dashboard. Civic-tech NGO partnerships. Smart City Mission integrations.

**Q: Privacy concerns?**
A: Complainant identity protected by default. Public dashboard shows aggregate data only. Officer scorecards based on public response data.

---

## 8. Demo Script (5 Minutes — Memorize This)

### Setup Before You Start

- One QR code on the big screen → links to namma.city
- Public dashboard already loaded on a second screen — Bangalore lit up with seeded issues
- Teammate stationed outside ready to photograph a real issue near MSRIT
- Backup video ready in case anything fails live
- Twitter and Gmail tabs pre-opened on a third laptop showing inbox/timeline

### Minute 1 — The Hook

Walk on stage. Hold up your phone.

> *"Bangalore citizens filed 1.2 lakh civic complaints last year. 60% never got resolved. Not because the city doesn't care — because one voice doesn't matter. Watch what happens when AI gives a single citizen the power of a thousand."*

Pull up the public dashboard. Bangalore lit up with seeded issues, color-coded by ward, severity, age. Judges immediately see scale.

### Minute 2 — The Live Capture

Teammate (outside, in real time) photographs a real pothole or garbage near MSRIT. Voice memo in Kannada:

> *"Idu MSRIT gate hattira. Ond varshadinda iddathe."* (This is near MSRIT gate. Has been here for a year.)

Show agents lighting up on a control-room style screen — Reporter, Geo, Routing — each surfacing its result in real time.

### Minute 3 — The Crowd Validation Moment (THE WIN)

Pause. Slow down here. This is your killer beat.

> *"But here's where it gets interesting…"*

Crowd Validation Agent fires. Map zooms to a 500m radius around MSRIT — **37 other reports light up** (from your seeded data). Animation: clusters merging into one bundled complaint.

Screen shows: *"Bundling 38 verified reports. Priority elevated. Joint complaint filed on behalf of 38 residents."*

This is where Google judges go *"oh, that's smart."* Let the moment land.

### Minute 4 — The Multi-Channel Submission

Multi-channel dispatch on screen:
- Tweet posted live to @BBMPCOMM (teammate's Twitter visible — show it appear)
- Email sent to Ward 95 officer (real Gmail, show the sent mail)
- BBMP Sahaaya complaint pre-filled (or simulated)
- Public dashboard updates with the new bundled issue

Show the actual tweet on screen with timestamp.

### Minute 5 — Escalation + Closer

> *"And we don't stop there. If BBMP doesn't respond in 7 days, NammaCity escalates automatically."*

Show escalation timeline: Day 7 councillor tag, Day 14 RTI, Day 21 MLA, Day 30 PIL.

Pull up the ward leaderboard.

> *"Officials know they're being measured. Citizens know what to expect. Issues get bundled, escalated, resolved. This isn't a complaint app — it's a civic operating system for Bangalore."*

Land the closer:

> *"There are 1.2 crore people in Bangalore. Today, only the loud ones get heard. Tomorrow, with NammaCity, every one of them does. We built this in 31 hours. We're not stopping until every ward officer in this city wakes up to a bundled complaint they can't ignore."*

Hands off the stage. Let it sit.

---

## 9. Pre-Hackathon Checklist

### TODAY (Before Hackathon Starts)

- [ ] Confirm team roles: who owns each agent
- [ ] Set up GitHub repo, share access
- [ ] Set up shared Notion/Google Doc for live coordination
- [ ] Get Google Cloud account ready (use hackathon credits)
- [ ] Apply for Twitter API access (has approval delay — do this NOW)
- [ ] Apply for Gemini API key
- [ ] Install Python 3.11+, Node.js 20+, Docker, PostgreSQL on every team laptop
- [ ] Buy/register a clean domain (namma.city or nammacity.app — costs ~₹500)
- [ ] Reach out to DeepStation organizers asking for any sponsor contacts

### Pre-Build Data Assets

- [ ] Download Bangalore ward GeoJSON (BBMP open data portal)
- [ ] Scrape ward officer contact list from BBMP website
- [ ] Compile civic agency Twitter handles (~30)
- [ ] Generate 200 synthetic historical complaints (Python script with random Bangalore coords + issue types)
- [ ] Save Karnataka Municipal Corporations Act key sections as a reference doc
- [ ] Compile MLA/councillor contact list

### Day 1 Morning (Hour 0)

- [ ] Arrive 30 minutes early — lock in good seats + wifi
- [ ] Eat breakfast (food NOT provided Day 1)
- [ ] Phones fully charged + power bank
- [ ] All laptops + chargers + extension cords + adapters
- [ ] Notebook + pens for whiteboarding
- [ ] Headphones for focus
- [ ] Personal hotspot in case venue wifi fails

### Throughout Hackathon

- [ ] Daily 10-minute syncs (every 6 hours)
- [ ] Commit code every hour to GitHub
- [ ] Update shared Notion doc with progress + blockers
- [ ] One person handles food/water for the team
- [ ] Mandatory 4-hour sleep per person sometime in hours 12–24

---

## 10. Quick Reference Tables

### Bangalore Civic Agencies & What They Handle

| Agency | Handles | Twitter | Email pattern |
|---|---|---|---|
| BBMP | Roads, garbage, parks, drainage, building violations, electrical, health | @BBMPCOMM | jc.[zone]@bbmp.gov.in |
| BESCOM | Electricity, broken poles, dangerous wires, outages | @bescomofficial | helpdesk@bescom.co.in |
| BWSSB | Water leaks, sewage overflow, broken pipes | @bwssb_official | comp@bwssb.gov.in |
| BMTC | Bus stops, missed buses, conductor issues | @BMTC_BENGALURU | mdbmtc@gmail.com |
| Bangalore Traffic Police | Signals, traffic violations | @blrcitytraffic | addlcptraffic-blr@ksp.gov.in |
| KSPCB | Air, water, noise pollution | — | mail@kspcb.gov.in |
| BMRCL | Metro issues | @OfficialBMRCL | info@bmrc.co.in |
| RERA Karnataka | Builder fraud, real-estate disputes | — | secy-rera@karnataka.gov.in |
| Karnataka Forest Dept | Tree fall, illegal cutting | @aranya_kfd | — |

### Issue Type → Agency Routing

| Issue | Primary Agency |
|---|---|
| Pothole, road damage | BBMP Roads |
| Garbage, sanitation | BBMP SWM |
| Streetlight not working | BBMP Electrical → BESCOM if pole issue |
| Broken footpath | BBMP Engineering |
| Open drain, sewage overflow | BWSSB |
| Water leak | BWSSB |
| Electrical wire hanging dangerously | BESCOM |
| Power outage | BESCOM |
| Bus stop damage | BMTC |
| Broken traffic signal | Bangalore Traffic Police |
| Open dump | BBMP Health + BBMP SWM |
| Tree fall | BBMP Forest Cell |
| Illegal construction | BBMP Town Planning |

### Common Municipal Code Citations

- **Karnataka Municipal Corporations Act, 1976** — primary statute
- **Section 256** — Maintenance of public streets
- **Section 297** — Removal of unauthorized encroachments
- **Section 320** — Sanitation provisions
- **Karnataka Right to Information Act** — for RTI applications

### Demo Day Twitter Handles to Tag

- @BBMPCOMM (BBMP Commissioner)
- @CMofKarnataka (Chief Minister)
- @bcpbengaluru (Bengaluru City Police)
- @ICCCBLR (Integrated Command Control Center)
- @TimesofIndia_blr (media)
- @DeccanHerald (media)
- @TheNewsMinute (media)

### Key URLs

- BBMP open data: opendata.bbmp.gov.in
- BBMP Sahaaya: sahaaya.bbmp.gov.in
- Karnataka eCourts: ecourts.gov.in
- Twitter API docs: developer.twitter.com
- Gemini API: ai.google.dev
- Google ADK: github.com/google/adk-python
- Cloud Run: cloud.google.com/run

---

## 11. Post-Hackathon Vision

### Why This Could Be a Real Startup

NammaCity isn't just a hackathon project — it's a wedge into a multi-billion-rupee civic-tech opportunity:

- **Free for citizens** (always)
- **SaaS for municipal corporations** wanting their own dashboard, insights, and complaint analytics
- **Partnerships with civic-tech NGOs** (Janaagraha, Citizen Matters)
- **Government dashboard licensing** — Smart Cities Mission, Ministry of Housing & Urban Affairs
- **Reward partnership revenue** — local businesses sponsoring civic-engagement rewards

### Roadmap Beyond the Hackathon

**Month 1–3:** Bangalore-only beta. 1,000 active users. Real BBMP partnership conversation.

**Month 4–6:** Add 5 more Indian cities (Mumbai, Delhi, Hyderabad, Pune, Chennai).

**Month 6–12:** SaaS B2G product for municipal corporations.

**Year 2:** National rollout. Integration with eFIR, RTI portals.

### What Makes This Defensible

- **Network effect from crowd validation** — more users = better clustering = more pressure = more results = more users
- **Public dashboard creates accountability** that no competitor can replicate without similar user base
- **Multi-agency routing knowledge** — months of work to build for one city, scales fast city-to-city

---

## Final Reminder

The thing that wins isn't the idea — it's the **demo**. Whatever happens during the build, the demo is what judges remember. Engineer the 5-minute demo first. Build everything backward from that.

**Three non-negotiables for demo day:**
1. Live photo → Reporter Agent classification works
2. Crowd validation cluster animates with seeded data
3. Twitter post appears live and is publicly verifiable

If those three work, you are in the top 3. If you also nail the dashboard visuals and multi-language voice, you win.

**Go build it.** 🚀

---

*Document version 1.0 | Compiled May 7, 2026 — eve of hackathon*
*Hackathon: Google × DeepStation × MSRIT*
