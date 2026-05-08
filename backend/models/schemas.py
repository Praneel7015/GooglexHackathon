from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ComplaintStatus(str, Enum):
    RECEIVED = "received"
    CLASSIFIED = "classified"
    ROUTED = "routed"
    SUBMITTED = "submitted"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class Location(BaseModel):
    lat: float
    lng: float
    ward_number: int | None = None
    zone: str | None = None
    mla_constituency: str | None = None


class Agency(BaseModel):
    id: str
    name: str
    twitter_handle: str | None = None
    email_pattern: str | None = None
    jurisdiction: str | None = None


class Complaint(BaseModel):
    id: str = Field(default="")
    description: str
    photo_url: str | None = None
    location: Location | None = None
    ward_id: int | None = None
    agency_id: str | None = None
    severity: int = Field(default=1, ge=1, le=5)
    status: ComplaintStatus = ComplaintStatus.RECEIVED
    created_at: datetime = Field(default_factory=lambda: datetime.now())


class ClusterResult(BaseModel):
    cluster_id: str
    member_count: int
    signatories: list[str] = Field(default_factory=list)
    aggregated_description: str = ""
