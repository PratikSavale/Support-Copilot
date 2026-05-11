"""Embedding engine using Gemini embeddings."""

from __future__ import annotations

import asyncio

from google import genai
from google.genai import types

from config.settings import get_settings

_emb_instance: "EmbeddingEngine | None" = None


class EmbeddingEngine:
    """Engine for generating text embeddings."""

    def __init__(self) -> None:
        settings = get_settings()
        self.model_name = settings.GEMINI_EMBEDDING_MODEL.removeprefix("models/")
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.config = types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=self.get_embedding_dimension(),
        )

    async def embed_query(self, text: str) -> list[float]:
        query_config = types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=self.get_embedding_dimension(),
        )
        return await asyncio.to_thread(self._embed_one, text, query_config)

    async def embed_documents(self, documents: list[str]) -> list[list[float]]:
        if not documents:
            return []
        return await asyncio.to_thread(self._embed_many, documents)

    def _embed_one(self, text: str, config: types.EmbedContentConfig) -> list[float]:
        result = self.client.models.embed_content(
            model=self.model_name,
            contents=text,
            config=config,
        )
        return list(result.embeddings[0].values)

    def _embed_many(self, documents: list[str]) -> list[list[float]]:
        result = self.client.models.embed_content(
            model=self.model_name,
            contents=documents,
            config=self.config,
        )
        return [list(embedding.values) for embedding in result.embeddings]

    def get_embedding_dimension(self) -> int:
        return 768


def get_embedding_engine() -> EmbeddingEngine:
    """Module-level singleton."""
    global _emb_instance
    if _emb_instance is None:
        _emb_instance = EmbeddingEngine()
    return _emb_instance
