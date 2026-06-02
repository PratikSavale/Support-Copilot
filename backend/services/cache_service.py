import json
import logging
import hashlib
from datetime import datetime, timezone
from typing import Any, Optional

from ai.chroma_utils import get_chroma_client, get_collection
from ai.embedding_engine import get_embedding_engine

logger = logging.getLogger(__name__)

class SemanticCacheService:
    """Manages high-fidelity semantic query caching using ChromaDB."""

    def __init__(self) -> None:
        self.embedding_engine = get_embedding_engine()
        client = get_chroma_client()
        self.collection = get_collection(client, "semantic_cache")

    async def check_cache(
        self, query: str, knowledge_source_ids: Optional[list[str]] = None
    ) -> Optional[dict[str, Any]]:
        """Query semantic_cache for a highly similar previously resolved answer."""
        try:
            query_embedding = await self.embedding_engine.embed_query(query)
            
            query_kwargs: dict[str, Any] = {
                "query_embeddings": [query_embedding],
                "n_results": 1,
            }

            # Restrict lookup to active knowledge sources to prevent leakage
            if knowledge_source_ids:
                if len(knowledge_source_ids) == 1:
                    query_kwargs["where"] = {"source_id": knowledge_source_ids[0]}
                else:
                    query_kwargs["where"] = {"source_id": {"$in": knowledge_source_ids}}

            # Run query in a thread pool since Chroma is synchronous
            import asyncio
            result = await asyncio.to_thread(self.collection.query, **query_kwargs)

            ids = result.get("ids", [[]])[0]
            metadatas = result.get("metadatas", [[]])[0]
            distances = result.get("distances", [[]])[0]

            if ids and metadatas:
                dist = distances[0] if distances else 1.0
                similarity = round(1.0 - float(dist), 4)

                # Strict semantic match threshold (similarity >= 0.95 / distance <= 0.05)
                if similarity >= 0.95:
                    meta = metadatas[0]
                    logger.info("⚡ [Cache] Semantic cache HIT for query '%s' (similarity: %f)", query[:60], similarity)
                    
                    # Safely load JSON sources list
                    sources = []
                    if meta.get("sources"):
                        try:
                            sources = json.loads(str(meta.get("sources")))
                        except Exception:
                            pass

                    # Increment hit count in background
                    try:
                        self.collection.update(
                            ids=[ids[0]],
                            metadatas=[{**meta, "hit_count": int(meta.get("hit_count", 0)) + 1}]
                        )
                    except Exception as e:
                        logger.warning("Failed to update cache hit count: %s", e)

                    return {
                        "response": str(meta.get("cached_response")),
                        "sources": sources,
                    }
                    
            logger.info("❄️ [Cache] Semantic cache MISS for query '%s'", query[:60])
            return None
        except Exception as e:
            logger.error("Error during semantic cache lookup: %s", e, exc_info=True)
            return None

    async def store_cache(
        self, query: str, response: str, sources: list[dict], knowledge_source_ids: Optional[list[str]] = None
    ) -> None:
        """Embed and store a verified resolved Q&A pair in the semantic cache."""
        try:
            # We only cache non-empty, non-trivial responses
            if not response or response == "INSUFFICIENT_DOCUMENTATION":
                return

            query_norm = query.strip()
            query_hash = hashlib.md5(query_norm.encode("utf-8")).hexdigest()
            query_embedding = await self.embedding_engine.embed_query(query_norm)

            primary_source = ""
            if knowledge_source_ids:
                primary_source = knowledge_source_ids[0]
            # Fallback to source of the first cited document if primary is missing
            elif sources:
                primary_source = str(sources[0].get("source_id", ""))

            metadata = {
                "cached_response": response,
                "sources": json.dumps(sources),
                "source_id": primary_source,
                "knowledge_source_ids": json.dumps(knowledge_source_ids or []),
                "hit_count": 0,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            self.collection.upsert(
                ids=[query_hash],
                documents=[query_norm],
                embeddings=[query_embedding],
                metadatas=[metadata],
            )
            logger.info("💾 [Cache] Successfully stored verified answer in semantic cache for: '%s'", query_norm[:60])
        except Exception as e:
            logger.error("Failed to store verified response in semantic cache: %s", e, exc_info=True)

    def invalidate_cache(self, source_id: str) -> None:
        """Evict all cached entries that depend on the modified knowledge source."""
        try:
            self.collection.delete(where={"source_id": source_id})
            logger.info("🗑️ [Cache] Invalidated and cleared cache entries matching source_id '%s'", source_id)
        except Exception as e:
            logger.error("Failed to invalidate cache for source_id %s: %s", source_id, e)

_cache_service_instance = None

def get_cache_service() -> SemanticCacheService:
    global _cache_service_instance
    if _cache_service_instance is None:
        _cache_service_instance = SemanticCacheService()
    return _cache_service_instance
