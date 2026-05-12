"""RAG pipeline: retrieve from Chroma and generate with Gemini."""

from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator

from ai.chroma_utils import get_chroma_client, get_collection
from ai.embedding_engine import get_embedding_engine
from ai.llm_engine import get_llm_engine
from ai.prompts import CHAT_SYSTEM_PROMPT
from ai.utils import truncate_excerpt
from config.settings import get_settings

_rag_instance: "RAGEngine | None" = None


class RAGEngine:
    """Retrieval + generation engine."""

    def __init__(self, top_k: int = 5) -> None:
        settings = get_settings()
        self.top_k = top_k
        self.embedding_engine = get_embedding_engine()
        self.llm_engine = get_llm_engine()
        client = get_chroma_client()
        self.collection = get_collection(client, settings.CHROMA_COLLECTION)

    async def add_documents(
        self, source_id: str, source_title: str, chunks: list[str]
    ) -> int:
        if not chunks:
            return 0

        embeddings = await self.embedding_engine.embed_documents(chunks)
        ids = [f"{source_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "source_id": source_id,
                "source_title": source_title,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            for i in range(len(chunks))
        ]

        # ChromaDB has a maximum batch size (often 5461). 
        # We split the upload into smaller batches to avoid ValueError.
        MAX_BATCH_SIZE = 5000
        for i in range(0, len(chunks), MAX_BATCH_SIZE):
            batch_chunks = chunks[i : i + MAX_BATCH_SIZE]
            batch_embeddings = embeddings[i : i + MAX_BATCH_SIZE]
            batch_metadatas = metadatas[i : i + MAX_BATCH_SIZE]
            batch_ids = ids[i : i + MAX_BATCH_SIZE]

            self.collection.upsert(
                documents=batch_chunks,
                embeddings=batch_embeddings,
                metadatas=batch_metadatas,
                ids=batch_ids,
            )
        
        return len(chunks)

    async def search(
        self, query: str, top_k: int | None = None, filters: dict | None = None
    ) -> list[dict[str, Any]]:
        k = top_k or self.top_k
        query_embedding = await self.embedding_engine.embed_query(query)
        query_kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": k,
        }
        if filters:
            query_kwargs["where"] = filters
        result = await asyncio.to_thread(self.collection.query, **query_kwargs)

        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        rows: list[dict[str, Any]] = []
        for i in range(len(ids)):
            distance = distances[i] if i < len(distances) else 1.0
            rows.append(
                {
                    "id": ids[i],
                    "content": docs[i],
                    "metadata": metadatas[i] or {},
                    "distance": distance,
                    "similarity": 1 - float(distance),
                }
            )
        return rows

    async def generate_response_stream(
        self, query: str, context_docs: list[dict[str, Any]]
    ) -> AsyncIterator[str]:
        context = "\n\n".join(doc.get("content", "") for doc in context_docs)
        messages = [
            {
                "role": "user",
                "content": (
                    "Based on the documentation below, answer the user question.\n\n"
                    f"Documentation:\n{context}\n\n"
                    f"User Question: {query}\n\n"
                    "If documentation is insufficient, explicitly say so."
                ),
            }
        ]
        async for chunk in self.llm_engine.generate_response_stream(
            messages, system_prompt=CHAT_SYSTEM_PROMPT
        ):
            yield chunk

    async def generate_response(
        self, query: str, context_docs: list[dict[str, Any]]
    ) -> tuple[str, list[dict[str, Any]]]:
        context = "\n\n".join(doc.get("content", "") for doc in context_docs)
        messages = [
            {
                "role": "user",
                "content": (
                    "Based on the documentation below, answer the user question.\n\n"
                    f"Documentation:\n{context}\n\n"
                    f"User Question: {query}\n\n"
                    "If documentation is insufficient, explicitly say so."
                ),
            }
        ]
        response = await self.llm_engine.generate_response(
            messages, system_prompt=CHAT_SYSTEM_PROMPT
        )
        sources = [
            {
                "source_id": str(doc.get("metadata", {}).get("source_id", "")),
                "title": str(doc.get("metadata", {}).get("source_title", "")),
                "chunk_excerpt": truncate_excerpt(doc.get("content", "")),
            }
            for doc in context_docs
        ]
        return response, sources

    async def process_query(self, query: str) -> dict[str, Any]:
        context_docs = await self.search(query)
        if not context_docs:
            return {
                "response": "I couldn't find relevant information in the knowledge base.",
                "sources": [],
                "action": "escalated",
                "retrieval_score": 0.0,
                "retrieved_chunks": [],
            }

        avg_similarity = sum(d["similarity"] for d in context_docs) / len(context_docs)
        response, sources = await self.generate_response(query, context_docs)
        return {
            "response": response,
            "sources": sources,
            "action": "resolve",
            "retrieval_score": round(avg_similarity, 4),
            "retrieved_chunks": [d["content"] for d in context_docs],
        }


def get_rag_engine() -> RAGEngine:
    """Module-level singleton."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGEngine()
    return _rag_instance
