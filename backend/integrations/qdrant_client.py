"""
Qdrant Cloud vector store for semantic similarity search.
Falls back to in-memory mode if no URL/key configured.
"""

import logging
from qdrant_client import QdrantClient, models

from config import settings

logger = logging.getLogger("nammacity.qdrant")

COLLECTION_NAME = "complaints"
VECTOR_SIZE = 3072  # gemini-embedding-001 dimensions
DISTANCE = models.Distance.COSINE

_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is not None:
        return _client

    if settings.qdrant_url and settings.qdrant_api_key:
        _client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key, timeout=15)
        logger.info("Connected to Qdrant Cloud: %s", settings.qdrant_url[:40])
    else:
        _client = QdrantClient(":memory:")
        logger.warning("Qdrant running in-memory mode (data lost on restart)")
    return _client


def ensure_collection() -> None:
    client = get_qdrant_client()
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=DISTANCE),
        )
    try:
        client.create_payload_index(collection_name=COLLECTION_NAME, field_name="issue_type", field_schema=models.PayloadSchemaType.KEYWORD)
        client.create_payload_index(collection_name=COLLECTION_NAME, field_name="complaint_id", field_schema=models.PayloadSchemaType.KEYWORD)
    except Exception:
        pass
    logger.info("Qdrant collection '%s' ready", COLLECTION_NAME)


async def upsert_complaint(complaint_id: str, embedding: list[float], metadata: dict) -> None:
    client = get_qdrant_client()
    client.upsert(collection_name=COLLECTION_NAME, points=[
        models.PointStruct(id=complaint_id, vector=embedding, payload=metadata)
    ])


async def search_similar(embedding: list[float], limit: int = 20, score_threshold: float = 0.85, issue_type: str | None = None, exclude_id: str | None = None) -> list[dict]:
    client = get_qdrant_client()
    conditions = []
    if issue_type:
        conditions.append(models.FieldCondition(key="issue_type", match=models.MatchValue(value=issue_type)))
    if exclude_id:
        conditions.append(models.FieldCondition(key="complaint_id", match=models.MatchExcept(**{"except": [exclude_id]})))
    query_filter = models.Filter(must=conditions) if conditions else None
    results = client.query_points(collection_name=COLLECTION_NAME, query=embedding, query_filter=query_filter, limit=limit, score_threshold=score_threshold)
    return [{"id": str(p.id), "score": p.score, "payload": p.payload} for p in results.points]


async def delete_complaint(complaint_id: str) -> None:
    client = get_qdrant_client()
    client.delete(collection_name=COLLECTION_NAME, points_selector=models.PointIdsList(points=[complaint_id]))
