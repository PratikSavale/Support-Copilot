"""Embedding engine using Gemini embeddings."""

from __future__ import annotations

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from config.settings import get_settings

_emb_instance: "EmbeddingEngine | None" = None


class EmbeddingEngine:
    """Engine for generating text embeddings."""

    def __init__(self) -> None:
        settings = get_settings()
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.GEMINI_EMBEDDING_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
        )

    async def embed_query(self, text: str) -> list[float]:
        return await self.embeddings.aembed_query(text)

    async def embed_documents(self, documents: list[str]) -> list[list[float]]:
        return await self.embeddings.aembed_documents(documents)

    def get_embedding_dimension(self) -> int:
        return 768


def get_embedding_engine() -> EmbeddingEngine:
    """Module-level singleton."""
    global _emb_instance
    if _emb_instance is None:
        _emb_instance = EmbeddingEngine()
    return _emb_instance
