# Backend Implementation Plan - NammaCity

## Verification Result (Backend Folder)

Current backend files exist as scaffolding, but all are empty:

- `backend/main.py`
- `backend/requirements.txt`
- `backend/agents/reporter.py`
- `backend/agents/geo.py`
- `backend/agents/routing.py`
- `backend/agents/crowd_validation.py`
- `backend/agents/drafting.py`
- `backend/agents/submission.py`
- `backend/agents/escalation.py`
- `backend/agents/prediction.py`
- `backend/integrations/twitter.py`
- `backend/integrations/gmail.py`
- `backend/integrations/whatsapp.py`
- `backend/db/schema.sql`
- `backend/db/seed_complaints.py`

## What Is Left Out

### 1) Core API and app setup
- FastAPI app bootstrap and router registration
- Health endpoint and readiness checks
- Config management (`.env` + settings model)
- Dependency injection for services and repositories
- Structured logging and request correlation IDs
- Error handling middleware and consistent API response models

### 2) Data layer
- PostgreSQL + PostGIS schema definition
- Async DB engine/session setup
- Repository layer for complaints, clusters, escalation events, submissions
- Migration workflow (Alembic or SQL migration strategy)
- Seed pipeline for synthetic historical complaints
- Geo and vector indexing strategy

### 3) Domain/services layer (business logic)
- Complaint intake and normalization service
- Orchestration service to run agent pipeline in sequence/parallel
- Escalation scheduler/state machine service
- Submission retry/idempotency service
- Prediction scoring service

### 4) Agent implementations
- Reporter agent (issue classification, severity, spam checks)
- Geo agent (GPS extraction, reverse geocode, ward mapping)
- Routing agent (issue type -> agency mapping)
- Crowd-validation agent (geo + semantic clustering + bundling rules)
- Drafting agent (multilingual content generation)
- Submission agent (channel dispatch and fallback)
- Escalation agent (day 7/14/21/30 action generation)
- Prediction agent (likelihood + ward trend scoring)

### 5) External integrations
- Twitter/X integration with auth + posting
- Gmail integration with SMTP/API and templates
- WhatsApp integration or demo-safe simulator
- Nominatim/geocoding client with retries and timeout controls
- Gemini/ADK wrappers for model calls with guardrails

### 6) Reliability and observability
- Structured logs for each pipeline stage
- Audit trail for every action (submission/escalation/cluster)
- Retries with backoff and circuit-breaker style fallbacks
- Idempotency keys for submissions/escalations
- Basic metrics and status endpoints for demo monitoring

### 7) Security and compliance basics
- Secrets handling with environment variables
- Input validation/sanitization
- File upload limits and MIME checks
- Abuse/spam throttling for complaint intake

### 8) Testing
- Unit tests for services and agents
- Integration tests for DB and pipeline flow
- Contract tests for integration adapters (mocked external APIs)
- End-to-end happy path test for demo-critical flow

---

## Execution Plan (Backend-Only)

## Phase 0 - Foundation (Must do first)
1. Create backend project structure following architecture boundaries:
   - `api/routes/`
   - `core/` (config, logging, exceptions)
   - `models/` (Pydantic schemas)
   - `repositories/`
   - `services/`
   - `agents/`
   - `integrations/`
   - `db/`
   - `tests/`
2. Fill `requirements.txt` with minimal runtime/test dependencies.
3. Implement `main.py` app bootstrap with health route and logging middleware.

Deliverable: backend starts cleanly and responds on `/health`.

## Phase 1 - Database and persistence
1. Implement `db/schema.sql` for:
   - complaints
   - clusters
   - submissions
   - escalations
   - audit_events
2. Add PostGIS indexes for radius queries.
3. Implement async DB session and base repository contracts.
4. Implement `db/seed_complaints.py` to generate/load synthetic data.

Deliverable: schema created, seeded data available for cluster/prediction demos.

## Phase 2 - Demo-critical pipeline (Priority 1)
1. Implement Reporter -> Geo -> Routing -> Crowd Validation services.
2. Expose API endpoint for complaint intake.
3. Persist complaint and cluster outputs.
4. Add deterministic fallback behavior when AI/geocoding fails.

Deliverable: intake request creates routed complaint and crowd bundle metadata.

## Phase 3 - Submission flow (Priority 1)
1. Implement Drafting agent outputs (at least English + Kannada draft fields).
2. Implement `integrations/twitter.py` as primary channel.
3. Implement `integrations/gmail.py` as secondary channel.
4. Implement `integrations/whatsapp.py` as simulator/fallback if API unavailable.
5. Implement Submission service with retry, idempotency, and per-channel status tracking.

Deliverable: one request triggers multi-channel submission with persisted status.

## Phase 4 - Escalation and prediction (Priority 2)
1. Implement Escalation state machine logic in `agents/escalation.py`.
2. Add scheduler/background worker for day-based escalation events.
3. Implement Prediction logic from ward-level historical seeded data.
4. Expose endpoints for escalation timeline and prediction response.

Deliverable: escalation actions can be simulated and queried.

## Phase 5 - Hardening and quality
1. Add structured logs across all services.
2. Add input validation and abuse checks.
3. Add tests:
   - Unit: routing/crowd bundle/escalation logic
   - Integration: complaint pipeline
   - Integration adapters: mocked Twitter/Gmail/WhatsApp
4. Add smoke script to verify demo-critical path quickly.

Deliverable: reliable backend with repeatable test checks.

---

## Suggested 31-Hour Backend Time Allocation

- Hours 0-3: Phase 0 + Phase 1 setup
- Hours 3-10: Phase 2 (Reporter/Geo/Routing/Crowd Validation)
- Hours 10-15: Phase 3 (Drafting + Submission integrations)
- Hours 15-20: Phase 4 (Escalation + Prediction)
- Hours 20-24: Phase 5 tests + hardening
- Hours 24+: bug fixes and demo safety improvements only

---

## Immediate Next 5 Tasks

1. Finalize `requirements.txt` and app skeleton in `main.py`.
2. Implement DB schema and async DB session/repository base.
3. Build complaint intake endpoint and core pipeline orchestration service.
4. Implement Twitter and Gmail adapters with mocked test mode.
5. Seed 200 synthetic complaints and validate crowd-clustering behavior.
