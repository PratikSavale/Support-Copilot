"""ChromaDB integration utilities."""

from functools import lru_cache

import chromadb

from config.settings import get_settings


@lru_cache(maxsize=1)
def get_chroma_client() -> chromadb.HttpClient:
    """Return Chroma HttpClient configured from settings."""
    settings = get_settings()
    return chromadb.HttpClient(
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT,
    )


def get_collection(client: chromadb.HttpClient, name: str = "knowledge_chunks"):
    """Get or create Chroma collection."""
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def reset_collection(client: chromadb.HttpClient, name: str = "knowledge_chunks"):
    """Delete and recreate collection."""
    try:
        client.delete_collection(name)
    except Exception:
        pass
    return get_collection(client, name=name)


def get_collection_stats(collection) -> dict[str, int | str]:
    """Return basic collection stats."""
    return {"name": collection.name, "count": collection.count()}
