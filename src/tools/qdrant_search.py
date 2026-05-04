"""Qdrant vector database client for similar project retrieval."""

from __future__ import annotations

from typing import Any

import structlog
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.prompts.llm_config import get_settings

logger = structlog.get_logger(__name__)

COLLECTION_NAME = "historical_projects"


def _get_qdrant_client() -> QdrantClient:
    settings = get_settings()
    return QdrantClient(url=settings.qdrant_url)


def ensure_collection() -> None:
    client = _get_qdrant_client()
    collections = [
        col.name for col in client.get_collections().collections  # type: ignore[union-attr]
    ]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )
        logger.info("qdrant_collection_created", collection=COLLECTION_NAME)


def seed_projects(projects: list[dict[str, Any]]) -> int:
    """Seed Qdrant with initial historical project data.

    Each project dict should contain:
        - id: int
        - description: str
        - metadata: dict (optional)
    """
    ensure_collection()
    client = _get_qdrant_client()

    points: list[PointStruct] = []
    for i, proj in enumerate(projects):
        # In production, use an embedding model to get real vectors.
        # Here we use a simple hash-based pseudo-vector for demo purposes.
        vector = _pseudo_embed(proj.get("description", ""), 1536)
        points.append(
            PointStruct(
                id=proj.get("id", i),
                vector=vector,
                payload={
                    "description": proj.get("description", ""),
                    "metadata": proj.get("metadata", {}),
                },
            )
        )

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    logger.info("qdrant_seed_complete", count=len(points))
    return len(points)


def search_similar_projects(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Search for similar historical projects using vector similarity."""
    try:
        client = _get_qdrant_client()
        vector = _pseudo_embed(query, 1536)
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=limit,
        )
        return [
            {
                "id": hit.id,
                "score": hit.score,
                "description": hit.payload.get("description", "") if hit.payload else "",
                "metadata": hit.payload.get("metadata", {}) if hit.payload else {},
            }
            for hit in results
        ]
    except Exception:
        logger.warning("qdrant_search_fallback", query=query[:100])
        return []


def get_project_count() -> int:
    try:
        client = _get_qdrant_client()
        info = client.count(collection_name=COLLECTION_NAME)
        return info.count
    except Exception:
        return 0


def _pseudo_embed(text: str, dim: int) -> list[float]:
    """Generate a pseudo-embedding vector from text hash for demo.

    In production, replace with a real embedding model (e.g., text-embedding-3-small).
    """
    import hashlib
    import math

    seed = int(hashlib.md5(text.encode()).hexdigest(), 16)
    result: list[float] = []
    for i in range(dim):
        angle = (seed * (i + 1) * 2654435761) % (2**32)
        result.append(float(math.sin(angle)))
    return result
