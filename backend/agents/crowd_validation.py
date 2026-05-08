"""
Crowd Validation Agent — THE MOAT.
Bundles similar nearby complaints to amplify political pressure.
"""

import asyncio
import logging
import time
import uuid

from agents.base import AgentInput, AgentOutput, BaseAgent
from agents.gemini_client import embed_text, generate_text
from db.client import get_client as get_supabase, get_complaints_in_radius
from integrations.qdrant_client import upsert_complaint, search_similar

logger = logging.getLogger("nammacity.agents.crowd_validation")

_embed_cache: dict[str, tuple[list[float], float]] = {}
_CACHE_TTL = 300.0

RADIUS_CONFIG: dict[str, float] = {
    "pothole": 200.0, "road_damage": 200.0, "garbage_pile": 300.0,
    "streetlight_out": 300.0, "illegal_construction": 1000.0, "flooding": 500.0,
}
DEFAULT_RADIUS = 500.0
BUNDLE_THRESHOLD = 3


async def _get_embedding(description: str) -> list[float]:
    now = time.time()
    cached = _embed_cache.get(description)
    if cached and (now - cached[1]) < _CACHE_TTL:
        return cached[0]
    embedding = await embed_text(description)
    _embed_cache[description] = (embedding, now)
    return embedding


class CrowdValidationAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name="CrowdValidationAgent", description="Bundles similar nearby complaints")

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        complaint_id = agent_input.data.get("complaint_id", "")
        description = agent_input.data.get("description", "")
        lat = agent_input.data.get("lat", 0.0)
        lng = agent_input.data.get("lng", 0.0)
        ward_number = agent_input.data.get("ward_number")
        issue_type = agent_input.data.get("issue_type", "other")

        if not description or not complaint_id:
            return AgentOutput(agent_name=self.name, success=True, data={"is_bundled": False, "member_count": 1, "cluster_id": None})

        radius = RADIUS_CONFIG.get(issue_type, DEFAULT_RADIUS)

        embedding_task = _get_embedding(description)
        geo_task = get_complaints_in_radius(lat=lat, lng=lng, radius_meters=radius, issue_type=issue_type)
        embedding, geo_results = await asyncio.gather(embedding_task, geo_task)

        semantic_results = await search_similar(embedding=embedding, limit=20, score_threshold=0.85, issue_type=issue_type, exclude_id=complaint_id)

        await upsert_complaint(complaint_id=complaint_id, embedding=embedding, metadata={"complaint_id": complaint_id, "issue_type": issue_type, "ward_number": ward_number, "lat": lat, "lng": lng})

        geo_ids = {c["id"] for c in geo_results if c.get("id") != complaint_id}
        semantic_ids = {r["id"] for r in semantic_results}
        candidate_ids = geo_ids if len(geo_ids) >= BUNDLE_THRESHOLD else (geo_ids & semantic_ids)

        if len(candidate_ids) >= BUNDLE_THRESHOLD:
            bundled_ids = list(candidate_ids)[:50]
            bundled_ids.append(complaint_id)
            aggregated = await self._generate_aggregated_description(description, geo_results[:5], len(bundled_ids))
            cluster_id = await self._create_cluster(lat, lng, issue_type, len(bundled_ids), aggregated)
            await self._assign_cluster(bundled_ids, cluster_id)

            return AgentOutput(agent_name=self.name, success=True, data={
                "is_bundled": True, "cluster_id": cluster_id, "member_count": len(bundled_ids),
                "bundled_complaint_ids": bundled_ids, "aggregated_description": aggregated,
                "nearest_complaints": [{"id": c["id"], "description": c.get("description", "")[:100]} for c in geo_results[:5]],
            })

        return AgentOutput(agent_name=self.name, success=True, data={
            "is_bundled": False, "cluster_id": None, "member_count": 1,
            "bundled_complaint_ids": [complaint_id], "aggregated_description": None,
            "nearest_complaints": [{"id": c["id"], "description": c.get("description", "")[:100]} for c in geo_results[:3]],
        })

    async def _generate_aggregated_description(self, current, nearby, count):
        try:
            descriptions = [current] + [c.get("description", "")[:200] for c in nearby if c.get("description")]
            prompt = f"You are drafting a joint civic complaint on behalf of {count} residents. Summarize these reports into ONE elevated complaint (2-3 sentences, formal):\n\n" + "\n".join(f"- {d}" for d in descriptions[:8])
            return await generate_text(prompt)
        except Exception as e:
            logger.warning("Aggregation failed: %s", e)
            return f"Joint complaint filed by {count} residents regarding {current[:100]}"

    async def _create_cluster(self, lat, lng, issue_type, member_count, description):
        client = get_supabase()
        cluster_id = str(uuid.uuid4())
        try:
            client.table("clusters").insert({"id": cluster_id, "centroid_location": f"SRID=4326;POINT({lng} {lat})", "member_count": member_count, "issue_type": issue_type, "status": "active"}).execute()
        except Exception as e:
            logger.warning("Cluster insert failed: %s", e)
        return cluster_id

    async def _assign_cluster(self, complaint_ids, cluster_id):
        client = get_supabase()
        try:
            for cid in complaint_ids:
                client.table("complaints").update({"cluster_id": cluster_id}).eq("id", cid).execute()
        except Exception as e:
            logger.warning("Cluster assignment failed: %s", e)
