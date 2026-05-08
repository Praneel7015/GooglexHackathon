"""
Crowd Validation Agent — THE MOAT.
Bundles similar nearby complaints to amplify political pressure.
Uses ADK adk_client for embeddings and aggregation text generation.
"""

import asyncio
import logging
import time
import uuid
from collections import OrderedDict

from agents.adk_client import embed_text, generate_text
from agents.base import AgentInput, AgentOutput, BaseAgent
from db.client import get_client as get_supabase, get_complaints_in_radius
from integrations.qdrant_client import upsert_complaint, search_similar

logger = logging.getLogger("nammacity.agents.crowd_validation")

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

RADIUS_CONFIG: dict[str, float] = {
    "pothole": 200.0,
    "road_damage": 200.0,
    "garbage_pile": 300.0,
    "streetlight_out": 300.0,
    "illegal_construction": 1000.0,
    "flooding": 500.0,
    "sewage_overflow": 400.0,
    "open_drain": 300.0,
}
DEFAULT_RADIUS = 500.0
BUNDLE_THRESHOLD = 3
MAX_BUNDLED_IDS = 50
_EMBED_CACHE_TTL = 300.0   # seconds
_EMBED_CACHE_MAX = 512     # max entries — evict LRU when full

_AGGREGATION_INSTRUCTION = (
    "You are a civic advocacy writer. "
    "When given multiple similar complaints from residents, "
    "produce a single elevated joint complaint in 2-3 formal sentences. "
    "Return only the aggregated complaint text, nothing else."
)

# ─────────────────────────────────────────────────────────────────────────────
# Bounded LRU embedding cache
# ─────────────────────────────────────────────────────────────────────────────

_embed_cache: OrderedDict[str, tuple[list[float], float]] = OrderedDict()


async def _get_embedding(description: str) -> list[float]:
    """Return cached embedding or compute a fresh one. Evicts LRU when full."""
    now = time.time()
    if description in _embed_cache:
        vec, ts = _embed_cache[description]
        if (now - ts) < _EMBED_CACHE_TTL:
            _embed_cache.move_to_end(description)  # mark recently used
            return vec
        del _embed_cache[description]

    embedding = await embed_text(description)

    # Evict oldest entry if at capacity
    if len(_embed_cache) >= _EMBED_CACHE_MAX:
        _embed_cache.popitem(last=False)

    _embed_cache[description] = (embedding, now)
    return embedding


# ─────────────────────────────────────────────────────────────────────────────
# CrowdValidationAgent
# ─────────────────────────────────────────────────────────────────────────────

class CrowdValidationAgent(BaseAgent):
    """Bundle similar nearby complaints using ADK-backed embedding + generation."""

    def __init__(self) -> None:
        super().__init__(
            name="CrowdValidationAgent",
            description="Bundles similar nearby complaints via ADK LlmAgent",
        )

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        complaint_id: str = agent_input.data.get("complaint_id", "")
        description: str  = agent_input.data.get("description", "")
        lat: float | None = agent_input.data.get("lat")
        lng: float | None = agent_input.data.get("lng")
        ward_number: int | None = agent_input.data.get("ward_number")
        issue_type: str = agent_input.data.get("issue_type", "other")

        # Guard: need both a description and valid non-zero coordinates
        if not description or not complaint_id:
            logger.info("CrowdValidation skipped — missing description or complaint_id")
            return self._no_bundle(complaint_id)

        if lat is None or lng is None or (lat == 0.0 and lng == 0.0):
            logger.info("CrowdValidation skipped — no valid coordinates for %s", complaint_id)
            return self._no_bundle(complaint_id)

        radius = RADIUS_CONFIG.get(issue_type, DEFAULT_RADIUS)

        # Embed + geo-search in parallel
        try:
            embedding, geo_results = await asyncio.gather(
                _get_embedding(description),
                get_complaints_in_radius(
                    lat=lat, lng=lng, radius_meters=radius, issue_type=issue_type
                ),
            )
        except Exception as e:
            logger.error("CrowdValidation parallel fetch failed: %s", e)
            return self._no_bundle(complaint_id)

        # Semantic search via Qdrant
        try:
            semantic_results = await search_similar(
                embedding=embedding,
                limit=20,
                score_threshold=0.85,
                issue_type=issue_type,
                exclude_id=complaint_id,
            )
        except Exception as e:
            logger.warning("Qdrant semantic search failed, falling back to geo-only: %s", e)
            semantic_results = []

        # Persist this complaint's vector — use deterministic UUID from complaint_id
        try:
            await upsert_complaint(
                complaint_id=complaint_id,
                embedding=embedding,
                metadata={
                    "complaint_id": complaint_id,
                    "issue_type": issue_type,
                    "ward_number": ward_number,
                    "lat": lat,
                    "lng": lng,
                },
            )
        except Exception as e:
            logger.warning("Qdrant upsert failed (non-fatal): %s", e)

        # Candidate selection: geo-only if enough, else geo ∩ semantic
        geo_ids = {c["id"] for c in geo_results if c.get("id") and c["id"] != complaint_id}
        semantic_ids = {r["id"] for r in semantic_results}
        candidate_ids = (
            geo_ids if len(geo_ids) >= BUNDLE_THRESHOLD
            else (geo_ids & semantic_ids)
        )

        if len(candidate_ids) >= BUNDLE_THRESHOLD:
            bundled_ids = list(candidate_ids)[:MAX_BUNDLED_IDS]
            bundled_ids.append(complaint_id)

            # Check for existing active cluster on this complaint to avoid duplicates
            existing_cluster = await self._get_existing_cluster(complaint_id)
            if existing_cluster:
                logger.info(
                    "Complaint %s already in cluster %s, skipping new cluster creation",
                    complaint_id, existing_cluster,
                )
                return AgentOutput(
                    agent_name=self.name,
                    success=True,
                    data={
                        "is_bundled": True,
                        "cluster_id": existing_cluster,
                        "member_count": len(bundled_ids),
                        "bundled_complaint_ids": bundled_ids,
                        "aggregated_description": description,
                        "nearest_complaints": _format_nearby(geo_results[:5]),
                    },
                )

            aggregated = await self._generate_aggregated_description(
                description, geo_results[:5], len(bundled_ids)
            )
            cluster_id = await self._create_cluster(lat, lng, issue_type, len(bundled_ids))
            await self._assign_cluster_batch(bundled_ids, cluster_id)

            logger.info(
                "Bundled %d complaints into cluster %s (issue=%s ward=%s)",
                len(bundled_ids), cluster_id, issue_type, ward_number,
            )
            return AgentOutput(
                agent_name=self.name,
                success=True,
                data={
                    "is_bundled": True,
                    "cluster_id": cluster_id,
                    "member_count": len(bundled_ids),
                    "bundled_complaint_ids": bundled_ids,
                    "aggregated_description": aggregated,
                    "nearest_complaints": _format_nearby(geo_results[:5]),
                },
            )

        return AgentOutput(
            agent_name=self.name,
            success=True,
            data={
                "is_bundled": False,
                "cluster_id": None,
                "member_count": 1,
                "bundled_complaint_ids": [complaint_id],
                "aggregated_description": None,
                "nearest_complaints": _format_nearby(geo_results[:3]),
            },
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _no_bundle(self, complaint_id: str) -> AgentOutput:
        """Return a standard not-bundled result."""
        return AgentOutput(
            agent_name=self.name,
            success=True,
            data={
                "is_bundled": False,
                "cluster_id": None,
                "member_count": 1,
                "bundled_complaint_ids": [complaint_id] if complaint_id else [],
                "aggregated_description": None,
                "nearest_complaints": [],
            },
        )

    async def _get_existing_cluster(self, complaint_id: str) -> str | None:
        """Return cluster_id if this complaint is already clustered, else None."""
        try:
            db = get_supabase()
            result = (
                db.table("complaints")
                .select("cluster_id")
                .eq("id", complaint_id)
                .limit(1)
                .execute()
            )
            if result.data:
                return result.data[0].get("cluster_id")
        except Exception as e:
            logger.warning("Cluster dedup check failed: %s", e)
        return None

    async def _generate_aggregated_description(
        self, current: str, nearby: list[dict], count: int
    ) -> str:
        """Use ADK generate_text to produce a joint complaint description."""
        try:
            descriptions = [current] + [
                c.get("description", "")[:200]
                for c in nearby
                if c.get("description")
            ]
            prompt = (
                f"Draft a joint civic complaint on behalf of {count} residents. "
                f"Summarize these reports into ONE elevated complaint (2-3 sentences, formal):\n\n"
                + "\n".join(f"- {d}" for d in descriptions[:8])
            )
            return await generate_text(prompt, system_instruction=_AGGREGATION_INSTRUCTION)
        except Exception as e:
            logger.warning("Aggregation LLM call failed: %s", e)
            return f"Joint complaint filed by {count} residents regarding {current[:100]}"

    async def _create_cluster(
        self, lat: float, lng: float, issue_type: str, member_count: int
    ) -> str:
        """Insert a new cluster row and return its ID."""
        db = get_supabase()
        cluster_id = str(uuid.uuid4())
        try:
            db.table("clusters").insert({
                "id": cluster_id,
                "centroid_location": f"SRID=4326;POINT({lng} {lat})",
                "member_count": member_count,
                "issue_type": issue_type,
                "status": "active",
            }).execute()
        except Exception as e:
            logger.error("Cluster insert failed: %s", e)
        return cluster_id

    async def _assign_cluster_batch(
        self, complaint_ids: list[str], cluster_id: str
    ) -> None:
        """
        Bulk-assign complaints to a cluster.
        Uses individual updates (Supabase JS client doesn't support IN-clause updates
        via the Python SDK natively); wrapped in a single try block.
        """
        db = get_supabase()
        failed = 0
        for cid in complaint_ids:
            try:
                db.table("complaints").update({"cluster_id": cluster_id}).eq("id", cid).execute()
            except Exception as e:
                failed += 1
                logger.warning("Cluster assign failed for %s: %s", cid, e)
        if failed:
            logger.warning(
                "Cluster %s: %d/%d assignments failed",
                cluster_id, failed, len(complaint_ids),
            )


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _format_nearby(complaints: list[dict]) -> list[dict]:
    """Safely format nearby complaint previews."""
    return [
        {
            "id": c.get("id", ""),
            "description": (c.get("description") or "")[:100],
        }
        for c in complaints
        if c.get("id")
    ]
