"""
NammaCity FastAPI application — entry point and route definitions.
Wires all 7 pipeline agents and exposes complaint, dashboard, and escalation APIs.
"""

import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, File, Form, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agents.base import AgentInput
from agents.crowd_validation import CrowdValidationAgent
from agents.drafting import DraftingAgent
from agents.escalation import EscalationAgent, get_escalation_timeline
from agents.geo import GeoAgent, load_ward_boundaries
from agents.prediction import PredictionAgent, get_ward_leaderboard
from agents.reporter import ReporterAgent
from agents.routing import RoutingAgent
from agents.submission import SubmissionAgent
from config import settings
from db.client import (
    get_active_clusters,
    get_all_complaints,
    get_client,
    get_complaint_by_id,
    get_dashboard_stats,
    get_map_complaints,
    get_ward_officer,
    insert_complaint,
)
from integrations.qdrant_client import ensure_collection

AGENTS = [
    "reporter", "geo", "routing", "crowd_validation", "drafting",
    "submission", "escalation", "prediction", "dashboard", "engagement",
]

VERSION = "0.1.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("nammacity")

# ─────────────────────────────────────────────────────────────────────────────
# Agent singletons (one instance shared across all requests)
# ─────────────────────────────────────────────────────────────────────────────

reporter_agent = ReporterAgent()
geo_agent = GeoAgent()
routing_agent = RoutingAgent()
crowd_validation_agent = CrowdValidationAgent()
drafting_agent = DraftingAgent()
submission_agent = SubmissionAgent()
escalation_agent = EscalationAgent()
prediction_agent = PredictionAgent()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("NammaCity backend starting (env=%s)", settings.environment)
    load_ward_boundaries()
    ensure_collection()
    yield
    logger.info("NammaCity backend shutting down")


app = FastAPI(
    title="NammaCity API",
    description="Civic Operating System for Bangalore",
    version=VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Health & meta
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "nammacity-backend"}


@app.get("/api/v1/info")
async def info() -> dict:
    return {
        "version": VERSION,
        "environment": settings.environment,
        "agents": AGENTS,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Core complaint pipeline
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/v1/report")
async def report(
    photo: UploadFile = File(...),
    voice_note: UploadFile | None = File(None),
    language: str = Form("en"),
    fallback_lat: float | None = Form(None),
    fallback_lng: float | None = Form(None),
    user_name: str | None = Form(None),
    user_email: str | None = Form(None),
) -> dict:
    """
    Full complaint pipeline:
    Reporter -> Geo -> Routing -> DB -> CrowdValidation -> Drafting -> Submission -> Escalation
    """
    photo_bytes = await photo.read()
    voice_bytes = await voice_note.read() if voice_note else None

    # ── Step 1: Reporter Agent ────────────────────────────────────────────────
    reporter_result = await reporter_agent.execute(
        AgentInput(data={
            "photo_bytes": photo_bytes,
            "voice_note_bytes": voice_bytes,
            "language": language,
        })
    )
    if not reporter_result.success:
        err = reporter_result.error or ""
        is_quota = "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower()
        if is_quota:
            # LLM quota exhausted — continue pipeline with safe defaults
            logger.warning("ReporterAgent quota-exhausted; continuing with fallback classification")
            reporter_result.success = True
            reporter_result.data = {
                "issue_type": "other",
                "severity": 3,
                "spam_score": 0.0,
                "raw_description": "Civic issue reported via NammaCity (LLM quota exhausted — auto-classified)",
                "transcribed_text": "",
            }
        else:
            return JSONResponse(status_code=500, content={
                "error": "reporter_failed", "message": reporter_result.error,
            })

    if reporter_result.data.get("spam_score", 0) > 0.95:
        return JSONResponse(status_code=422, content={
            "error": "likely_spam",
            "message": "This image was flagged as likely spam or AI-generated.",
            "spam_score": reporter_result.data["spam_score"],
        })

    # ── Step 2: Geo Agent ─────────────────────────────────────────────────────
    geo_result = await geo_agent.execute(
        AgentInput(data={
            "photo_bytes": photo_bytes,
            "fallback_lat": fallback_lat,
            "fallback_lng": fallback_lng,
        })
    )

    # ── Step 3: Routing Agent ─────────────────────────────────────────────────
    routing_result = await routing_agent.execute(
        AgentInput(data={
            "issue_type": reporter_result.data["issue_type"],
            "ward_number": geo_result.data.get("ward_number") if geo_result.success else None,
        })
    )

    # ── Step 4: Insert complaint into Supabase ────────────────────────────────
    complaint: dict = {}
    if geo_result.success and settings.supabase_url:
        try:
            primary_agency_id = None
            if routing_result.success:
                primary_agency_id = routing_result.data.get("primary_agency", {}).get("id")
            complaint = await insert_complaint(
                description=reporter_result.data.get("raw_description", ""),
                lat=geo_result.data["lat"],
                lng=geo_result.data["lng"],
                ward_number=geo_result.data.get("ward_number"),
                zone=geo_result.data.get("zone"),
                agency_id=primary_agency_id,
                issue_type=reporter_result.data["issue_type"],
                severity=reporter_result.data["severity"],
            )
        except Exception as e:
            logger.warning("DB insert failed (non-fatal): %s", e)

    # ── Step 5: Crowd Validation Agent ────────────────────────────────────────
    crowd_result = None
    if complaint.get("id") and geo_result.success:
        crowd_result = await crowd_validation_agent.execute(
            AgentInput(data={
                "complaint_id": complaint["id"],
                "description": reporter_result.data.get("raw_description", ""),
                "lat": geo_result.data["lat"],
                "lng": geo_result.data["lng"],
                "ward_number": geo_result.data.get("ward_number"),
                "issue_type": reporter_result.data["issue_type"],
            })
        )

    crowd_data = crowd_result.data if crowd_result and crowd_result.success else {}

    # ── Step 6: Drafting Agent ────────────────────────────────────────────────
    drafting_result = await drafting_agent.execute(
        AgentInput(data={
            "complaint_id": complaint.get("id", ""),
            "issue_type": reporter_result.data["issue_type"],
            "severity": reporter_result.data["severity"],
            "description": reporter_result.data.get("raw_description", ""),
            "location": geo_result.data if geo_result.success else {},
            "routing": routing_result.data if routing_result.success else {},
            "crowd_validation": crowd_data,
            "user_name": user_name,
            "user_email": user_email,
        })
    )

    # ── Step 7: Submission Agent ──────────────────────────────────────────────
    submission_result = None
    if drafting_result.success:
        submission_result = await submission_agent.execute(
            AgentInput(data={
                "complaint_id": complaint.get("id", ""),
                "drafting": drafting_result.data,
                "routing": routing_result.data if routing_result.success else {},
                "crowd_validation": crowd_data,
                "user_email": user_email,
            })
        )

    # ── Step 8: Escalation (computed from complaint age, no Gemini calls) ──────
    escalation_result = None
    # Escalation timeline is computed in GET /api/v1/complaints/{id} based on age
    # No need to run the full EscalationAgent here — saves 35s of Gemini calls

    # ── Step 9: Prediction ────────────────────────────────────────────────────
    prediction_result = None
    if geo_result.success:
        prediction_result = await prediction_agent.execute(
            AgentInput(data={
                "ward_number": geo_result.data.get("ward_number"),
                "issue_type": reporter_result.data["issue_type"],
                "agency_id": complaint.get("agency_id"),
            })
        )

    total_latency = round(
        reporter_result.latency_ms
        + geo_result.latency_ms
        + routing_result.latency_ms
        + (crowd_result.latency_ms if crowd_result else 0)
        + drafting_result.latency_ms
        + (submission_result.latency_ms if submission_result else 0),
        2,
    )

    return {
        "complaint_id": complaint.get("id"),
        "reporter": reporter_result.data,
        "geo": geo_result.data if geo_result.success else {"error": geo_result.error},
        "routing": routing_result.data if routing_result.success else {"error": routing_result.error},
        "crowd_validation": crowd_data or None,
        "drafting": {
            "email_subject": drafting_result.data.get("email_subject"),
            "tweet_text": drafting_result.data.get("tweet_text"),
            "whatsapp_text": drafting_result.data.get("whatsapp_text"),
        } if drafting_result.success else {"error": drafting_result.error},
        "submission": submission_result.data if submission_result and submission_result.success else None,
        "escalation": {
            "scheduled": True,
            "timeline": [
                {"stage": "submitted", "action": "Initial multi-channel submission", "completed": True},
                {"stage": "councillor_tagged", "action": "Ward councillor tagged (Day 7)", "completed": False},
                {"stage": "rti_filed", "action": "RTI application filed (Day 14)", "completed": False},
                {"stage": "mla_tagged", "action": "MLA + media notified (Day 21)", "completed": False},
                {"stage": "pil_drafted", "action": "PIL outline drafted (Day 30)", "completed": False},
            ],
        },
        "prediction": prediction_result.data if prediction_result and prediction_result.success else None,
        "pipeline_latency_ms": total_latency,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Complaint queries
# ─────────────────────────────────────────────────────────────────────────────

WARD_NAMES: dict[int, str] = {
    95: "Malleshwaram", 96: "Rajajinagar", 97: "Subramanyanagar",
    110: "Yeshwanthpur", 44: "Hebbal", 87: "Koramangala",
    150: "HSR Layout", 151: "BTM Layout", 174: "Whitefield", 126: "Jayanagar",
}


@app.get("/api/v1/complaints")
async def list_complaints(
    status: str | None = Query(None),
    ward_number: int | None = Query(None),
    issue_type: str | None = Query(None),
    user_email: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    """Paginated complaint list for Track page."""
    complaints = await get_all_complaints(
        status=status, ward_number=ward_number, issue_type=issue_type, limit=limit + 1
    )

    # Apply offset manually (Supabase client doesn't chain .range easily)
    sliced = complaints[offset : offset + limit + 1]
    has_more = len(sliced) > limit
    items = sliced[:limit]

    shaped = []
    for c in items:
        desc = c.get("description", "") or ""
        shaped.append({
            "id": c.get("id"),
            "issue_type": c.get("issue_type"),
            "severity": c.get("severity"),
            "status": c.get("status"),
            "description": desc[:200],
            "ward_number": c.get("ward_number"),
            "ward_name": WARD_NAMES.get(c.get("ward_number", 0), ""),
            "created_at": c.get("created_at"),
            "updated_at": c.get("updated_at"),
            "cluster_id": c.get("cluster_id"),
            "bundle_size": 1,
            "submission_count": 0,
        })

    return {
        "complaints": shaped,
        "total": len(complaints),
        "limit": limit,
        "offset": offset,
        "has_more": has_more,
    }


@app.get("/api/v1/complaints/{complaint_id}")
async def get_complaint(complaint_id: str) -> dict:
    """Single complaint detail with escalation timeline."""
    complaint = await get_complaint_by_id(complaint_id)
    if not complaint:
        return JSONResponse(status_code=404, content={"error": "complaint_not_found"})

    # Ward officer + agency
    ward_num = complaint.get("ward_number")
    officer = await get_ward_officer(ward_num) if ward_num else None
    agency = None
    if complaint.get("agency_id"):
        try:
            client = get_client()
            a_result = client.table("agencies").select("*").eq("id", complaint["agency_id"]).limit(1).execute()
            agency = a_result.data[0] if a_result.data else None
        except Exception:
            pass

    # Cluster info
    cluster_info = None
    if complaint.get("cluster_id"):
        try:
            client = get_client()
            cl = client.table("clusters").select("*").eq("id", complaint["cluster_id"]).limit(1).execute()
            if cl.data:
                cluster_info = {
                    "id": cl.data[0].get("id"),
                    "member_count": cl.data[0].get("member_count", 1),
                    "aggregated_description": cl.data[0].get("aggregated_description", ""),
                    "other_complaint_ids": [],
                }
        except Exception:
            pass

    # Submissions
    submissions = []
    try:
        client = get_client()
        sub = client.table("submissions").select("*").eq("complaint_id", complaint_id).execute()
        submissions = [
            {
                "channel": s.get("channel"),
                "status": s.get("status"),
                "reference_id": s.get("reference_id"),
                "mode": s.get("mode"),
                "submitted_at": s.get("submitted_at"),
                "error": s.get("error_message"),
            }
            for s in (sub.data or [])
        ]
    except Exception:
        pass

    # Escalation timeline (computed from age)
    created = complaint.get("created_at", "")
    days_old = 0
    if created:
        try:
            from datetime import datetime, timezone
            ct = datetime.fromisoformat(created.replace("Z", "+00:00"))
            days_old = (datetime.now(timezone.utc) - ct).days
        except Exception:
            pass

    stages = [
        {"stage": "submitted", "day": 0, "action": "Initial multi-channel submission"},
        {"stage": "councillor_tagged", "day": 7, "action": "Ward councillor tagged on Twitter"},
        {"stage": "rti_filed", "day": 14, "action": "RTI application filed"},
        {"stage": "mla_tagged", "day": 21, "action": "MLA tagged + media notified"},
        {"stage": "pil_drafted", "day": 30, "action": "PIL outline drafted"},
    ]
    timeline = []
    current_stage = "submitted"
    for s in stages:
        completed = days_old >= s["day"]
        if completed:
            current_stage = s["stage"]
        timeline.append({
            "stage": s["stage"],
            "date": "",
            "action": s["action"],
            "completed": completed,
        })

    next_idx = next((i for i, t in enumerate(timeline) if not t["completed"]), None)

    # Location from complaint geometry
    loc = complaint.get("location", {})
    lat = loc.get("coordinates", [0, 0])[1] if isinstance(loc, dict) and "coordinates" in loc else None
    lng = loc.get("coordinates", [0, 0])[0] if isinstance(loc, dict) and "coordinates" in loc else None

    return {
        "id": complaint.get("id"),
        "description": complaint.get("description"),
        "issue_type": complaint.get("issue_type"),
        "severity": complaint.get("severity"),
        "status": complaint.get("status"),
        "created_at": complaint.get("created_at"),
        "updated_at": complaint.get("updated_at"),
        "location": {
            "lat": lat,
            "lng": lng,
            "ward_number": complaint.get("ward_number"),
            "ward_name": WARD_NAMES.get(complaint.get("ward_number", 0), ""),
            "zone": complaint.get("zone"),
            "address": None,
            "mla_constituency": None,
        },
        "routing": {
            "primary_agency": {
                "id": agency.get("id") if agency else None,
                "name": agency.get("name") if agency else None,
                "twitter_handle": agency.get("twitter_handle") if agency else None,
                "email_pattern": agency.get("email_pattern") if agency else None,
            } if agency else None,
            "ward_officer": {
                "name": officer.get("officer_name") if officer else None,
                "email": officer.get("email") if officer else None,
                "phone": officer.get("phone") if officer else None,
            } if officer else None,
        },
        "cluster": cluster_info,
        "submissions": submissions,
        "escalation": {
            "current_stage": current_stage,
            "days_since_submission": days_old,
            "next_action_at": None,
            "next_action": timeline[next_idx]["action"] if next_idx is not None else None,
            "timeline": timeline,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard APIs
# ─────────────────────────────────────────────────────────────────────────────

import time as _time

_stats_cache: dict = {}
_stats_cache_ts: float = 0.0
_STATS_CACHE_TTL = 30.0


@app.get("/api/v1/dashboard/stats")
async def dashboard_stats() -> dict:
    """Aggregate stats + ward leaderboard for the dashboard hero strip."""
    global _stats_cache, _stats_cache_ts
    now = _time.time()
    if _stats_cache and (now - _stats_cache_ts) < _STATS_CACHE_TTL:
        return _stats_cache

    raw = await get_dashboard_stats()
    leaderboard = get_ward_leaderboard()

    wards = []
    for i, w in enumerate(leaderboard):
        wards.append({
            "ward_number": w.get("ward_number"),
            "ward_name": WARD_NAMES.get(w.get("ward_number", 0), f"Ward {w.get('ward_number')}"),
            "total_complaints": w.get("total", 0),
            "resolved": w.get("resolved", 0),
            "open": w.get("open", w.get("total", 0) - w.get("resolved", 0)),
            "resolution_rate": w.get("resolution_rate", 0.0),
            "avg_response_days": w.get("avg_days"),
            "rank": i + 1,
        })

    clusters_count = 0
    try:
        cls = await get_active_clusters()
        clusters_count = len(cls)
    except Exception:
        pass

    result = {
        "totals": {
            "total_complaints": raw.get("total_complaints", 0),
            "total_resolved": raw.get("resolved", 0),
            "total_open": raw.get("open", 0),
            "total_escalated": 0,
            "total_clusters": clusters_count,
            "avg_resolution_days": None,
            "complaints_today": 0,
            "bundled_today": 0,
        },
        "wards": wards,
    }

    _stats_cache = result
    _stats_cache_ts = now
    return result


@app.get("/api/v1/dashboard/map")
async def dashboard_map(
    ward_number: int | None = Query(None),
    issue_type: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(500, le=2000),
) -> dict:
    """All complaints + cluster centroids for the Leaflet map."""
    all_complaints = await get_all_complaints(
        status=status, ward_number=ward_number, issue_type=issue_type, limit=limit
    )

    complaints_shaped = []
    for c in all_complaints:
        loc = c.get("location", {})
        lat = loc.get("coordinates", [0, 0])[1] if isinstance(loc, dict) and "coordinates" in loc else None
        lng = loc.get("coordinates", [0, 0])[0] if isinstance(loc, dict) and "coordinates" in loc else None
        if lat is None or lng is None:
            continue
        complaints_shaped.append({
            "id": c.get("id"),
            "lat": lat,
            "lng": lng,
            "issue_type": c.get("issue_type"),
            "severity": c.get("severity"),
            "status": c.get("status"),
            "ward_number": c.get("ward_number"),
            "ward_name": WARD_NAMES.get(c.get("ward_number", 0), ""),
            "created_at": c.get("created_at"),
            "cluster_id": c.get("cluster_id"),
            "bundle_size": 1,
        })

    clusters_shaped = []
    try:
        raw_clusters = await get_active_clusters()
        for cl in raw_clusters:
            cent = cl.get("centroid_location", {})
            clat = cent.get("coordinates", [0, 0])[1] if isinstance(cent, dict) and "coordinates" in cent else None
            clng = cent.get("coordinates", [0, 0])[0] if isinstance(cent, dict) and "coordinates" in cent else None
            clusters_shaped.append({
                "id": cl.get("id"),
                "centroid_lat": clat,
                "centroid_lng": clng,
                "issue_type": cl.get("issue_type"),
                "member_count": cl.get("member_count", 0),
                "status": cl.get("status"),
            })
    except Exception:
        pass

    return {
        "complaints": complaints_shaped,
        "clusters": clusters_shaped,
        "total": len(complaints_shaped),
    }


@app.get("/api/v1/dashboard/clusters")
async def dashboard_clusters() -> dict:
    """Active crowd-validation clusters for the heatmap animation."""
    clusters = await get_active_clusters()
    return {"count": len(clusters), "clusters": clusters}


# ─────────────────────────────────────────────────────────────────────────────
# Prediction endpoint (standalone, for frontend ward picker)
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/v1/predict")
async def predict(
    ward_number: int | None = Query(None),
    issue_type: str | None = Query(None),
) -> dict:
    result = await prediction_agent.execute(
        AgentInput(data={
            "ward_number": ward_number,
            "issue_type": issue_type,
            "include_leaderboard": False,
        })
    )
    if not result.success:
        return JSONResponse(status_code=500, content={"error": result.error})
    return result.data

