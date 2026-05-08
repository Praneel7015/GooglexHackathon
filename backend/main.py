import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings

AGENTS = [
    "reporter",
    "geo",
    "routing",
    "crowd_validation",
    "drafting",
    "submission",
    "escalation",
    "prediction",
    "dashboard",
    "engagement",
]

VERSION = "0.1.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("nammacity")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("NammaCity backend starting (env=%s)", settings.environment)
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
