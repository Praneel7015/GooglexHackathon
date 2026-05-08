import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agents.base import AgentInput
from agents.crowd_validation import CrowdValidationAgent
from agents.drafting import DraftingAgent
from agents.geo import GeoAgent, load_ward_boundaries
from agents.reporter import ReporterAgent
from agents.routing import RoutingAgent
from agents.submission import SubmissionAgent
from config import settings
from db.client import insert_complaint
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

# Agent singletons
reporter_agent = ReporterAgent()
geo_agent = GeoAgent()
routing_agent = RoutingAgent()
crowd_validation_agent = CrowdValidationAgent()
drafting_agent = DraftingAgent()
submission_agent = SubmissionAgent()


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
    Reporter -> Geo -> Routing -> DB -> CrowdValidation -> Drafting -> Submission
    """
    photo_bytes = await photo.read()
    voice_bytes = await voice_note.read() if voice_note else None

    # --- Step 1: Reporter Agent ---
    reporter_result = await reporter_agent.execute(
        AgentInput(data={
            "photo_bytes": photo_bytes,
            "voice_note_bytes": voice_bytes,
            "language": language,
        })
    )
    if not reporter_result.success:
        return JSONResponse(status_code=500, content={
            "error": "reporter_failed", "message": reporter_result.error,
        })

    if reporter_result.data.get("spam_score", 0) > 0.95:
        return JSONResponse(status_code=422, content={
            "error": "likely_spam",
            "message": "This image was flagged as likely spam or AI-generated.",
            "spam_score": reporter_result.data["spam_score"],
        })

    # --- Step 2: Geo Agent ---
    geo_result = await geo_agent.execute(
        AgentInput(data={
            "photo_bytes": photo_bytes,
            "fallback_lat": fallback_lat,
            "fallback_lng": fallback_lng,
        })
    )

    # --- Step 3: Routing Agent ---
    routing_result = await routing_agent.execute(
        AgentInput(data={
            "issue_type": reporter_result.data["issue_type"],
            "ward_number": geo_result.data.get("ward_number") if geo_result.success else None,
        })
    )

    # --- Step 4: Insert complaint into Supabase ---
    complaint = {}
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

    # --- Step 5: Crowd Validation Agent ---
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

    # --- Step 6: Drafting Agent ---
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

    # --- Step 7: Submission Agent ---
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

    total_latency = (
        reporter_result.latency_ms
        + geo_result.latency_ms
        + routing_result.latency_ms
        + (crowd_result.latency_ms if crowd_result else 0)
        + drafting_result.latency_ms
        + (submission_result.latency_ms if submission_result else 0)
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
        "pipeline_latency_ms": round(total_latency, 2),
    }
