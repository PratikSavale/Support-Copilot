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
        self.batch_size = settings.CHROMA_BATCH_SIZE

    async def add_documents(
        self, source_id: str, source_title: str, chunks: list[str], source_url: str = ""
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
        for meta in metadatas:
            if source_url:
                meta["source_url"] = source_url

        # ChromaDB has a maximum batch size (often 5461). 
        # We split the upload into smaller batches to avoid ValueError.
        for i in range(0, len(chunks), self.batch_size):
            batch_chunks = chunks[i : i + self.batch_size]
            batch_embeddings = embeddings[i : i + self.batch_size]
            batch_metadatas = metadatas[i : i + self.batch_size]
            batch_ids = ids[i : i + self.batch_size]

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
                    "You are an expert, context-aware L2 Support AI. Analyze the provided documentation to interpret and deduce the answer to the user's question. "
                    "You may apply the concepts from the documentation to troubleshoot specific errors (like Java stack traces), but you MUST base your reasoning on the provided text. "
                    "Do not hallucinate outside facts. If the documentation does not contain enough relevant information to deduce a helpful answer, "
                    "you MUST reply EXACTLY with the phrase 'INSUFFICIENT_DOCUMENTATION'.\n\n"
                    f"Documentation:\n{context}\n\n"
                    f"User Question: {query}"
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
        accumulated_docs = {doc.get("id"): doc for doc in context_docs}
        search_history = [query]
        
        max_hops = 3
        for hop in range(max_hops):
            context = "\n\n".join(doc.get("content", "") for doc in accumulated_docs.values())
            prompt = (
                "You are an expert, context-aware L2 Support AI equipped with Graph Traversal reasoning.\n"
                "You must analyze the user's question and the retrieved documentation.\n"
                f"Documentation:\n{context}\n\n"
                f"User Question: {query}\n\n"
                "If the documentation provides enough context to deduce the answer, reply with action 'answer' and the content.\n"
                "If the documentation is missing pieces (e.g. you see a concept but need to know its configuration), you can trigger another search by replying with action 'search' and the new query content.\n"
                "If you cannot deduce the answer and cannot think of anything else to search, reply with action 'insufficient'.\n"
                "Do NOT use outside knowledge.\n"
            )
            schema_hint = '{"action": "answer" | "search" | "insufficient", "content": "your response or your next search query"}'
            
            import logging
            logger = logging.getLogger(__name__)
            
            structured_resp = await self.llm_engine.generate_structured_response(prompt, schema_hint)
            
            action = structured_resp.get("action")
            content = structured_resp.get("content", "")
            
            if action == "answer" and content:
                logger.info(f"🟢 [Agentic RAG] Deduced answer on hop {hop+1}")
                # Deduplicate and return
                sources = [
                    {
                        "source_id": str(doc.get("metadata", {}).get("source_id", "")),
                        "title": str(doc.get("metadata", {}).get("source_title", "")),
                        "url": str(doc.get("metadata", {}).get("source_url", "")),
                        "chunk_excerpt": truncate_excerpt(doc.get("content", "")),
                    }
                    for doc in accumulated_docs.values()
                ]
                return content, sources
                
            elif action == "search" and content and content not in search_history:
                logger.info(f"🔍 [Agentic RAG] Hop {hop+1}: Missing context. Triggering graph search for -> '{content}'")
                # Execute the hop!
                new_docs = await self.search(content, top_k=3)
                for nd in new_docs:
                    accumulated_docs[nd.get("id")] = nd
                search_history.append(content)
                continue # Next hop
                
            else:
                logger.warning(f"🔴 [Agentic RAG] Hop {hop+1}: Reached dead end or insufficient context. Falling back.")
                # Either insufficient, or empty/malformed due to API error
                break
                
        # If we exhausted hops or hit insufficient/error
        sources = [
            {
                "source_id": str(doc.get("metadata", {}).get("source_id", "")),
                "title": str(doc.get("metadata", {}).get("source_title", "")),
                "url": str(doc.get("metadata", {}).get("source_url", "")),
                "chunk_excerpt": truncate_excerpt(doc.get("content", "")),
            }
            for doc in accumulated_docs.values()
        ]
        return "INSUFFICIENT_DOCUMENTATION", sources

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
