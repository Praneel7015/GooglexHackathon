# NammaCity — Project Context for Claude Code

## What we're building

A multi-agent civic operating system PWA for Bangalore. Citizens photograph
civic issues; AI routes to right agency, bundles similar nearby complaints,
files via Twitter/email/portal, and escalates over 30 days if ignored.

## Hackathon context

- Google × DeepStation × MSRIT, May 8-9, 2026
- 31 hours total
- Must use Google ADK + Gemini API
- Multi-agent system is mandatory

## Stack (LOCKED — do not deviate)

- Frontend: React + Vite + Tailwind (PWA)
- Backend: Python FastAPI
- Agents: Google ADK
- LLM: Gemini 2.5 Pro (multimodal)
- DB: Supabase (PostgreSQL + PostGIS)
- Vector DB: Qdrant Cloud
- Maps: Leaflet.js + OpenStreetMap
- Hosting: Cloud Run (backend), Firebase Hosting (frontend)

## Reference doc

See @master-build-doc.md for full architecture, agent specs, demo script,
and risk register. Always reference this before making architectural decisions.

## Code style

- Python: type hints required, async/await for all I/O
- TypeScript: strict mode on, no `any`
- Commit per feature, not per session
- One file = one responsibility

## Current sprint

[Update this section as you progress through the build plan]

- Hour 0-3: Foundation
- Currently working on: [agent/feature]
- Owner: [team member name]

## Non-negotiables for demo

1. Live photo → Reporter Agent classification works
2. Crowd validation cluster animates with seeded data
3. Twitter post appears live and is publicly verifiable

## What NOT to do

- Don't add localStorage/sessionStorage (use React state)
- Don't try to integrate BBMP Sahaaya direct submission (use Twitter as primary)
- Don't build features outside the 10-agent architecture
- Don't refactor working code mid-hackathon
