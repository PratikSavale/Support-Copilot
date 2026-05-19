"""RAG pipeline: retrieve from Chroma and generate with Gemini.

Design principles:
  - Search ChromaDB for top-k chunks relevant to the query.
  - Clean the retrieved chunks (strip Jina markdown noise) before feeding to LLM.
  - Ask the LLM to answer STRICTLY from the provided context.
  - If the context is insufficient, return INSUFFICIENT_DOCUMENTATION.
  - Never save generated answers back into ChromaDB (that causes self-pollution).
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, AsyncIterator

from ai.chroma_utils import get_chroma_client, get_collection
from ai.embedding_engine import get_embedding_engine
from ai.llm_engine import get_llm_engine
from ai.prompts import (
    CHAT_SYSTEM_PROMPT,
    AGENTIC_RAG_PROMPT,
    AGENTIC_RAG_SCHEMA
)
from ai.utils import truncate_excerpt
from config.settings import get_settings

logger = logging.getLogger(__name__)

_rag_instance: "RAGEngine | None" = None

# ── Inline content cleaner (fast, no import cycle) ────────────────────────
_MD_LINK    = re.compile(r'\[([^\]]*)\]\([^)]+\)')
_MD_IMAGE   = re.compile(r'!\[[^\]]*\]\([^)]+\)')
_BARE_URL   = re.compile(r'^https?://\S+\s*$', re.MULTILINE)
_HTML_TAG   = re.compile(r'<[^>]+>')
_MULTI_NL   = re.compile(r'\n{3,}')


def _clean_chunk(text: str) -> str:
    """Strip Jina reader noise from a single chunk so the LLM sees clean prose."""
    # 1. Strip Jina metadata lines
    meta_prefixes = (
        "Title:", "URL Source:", "Published Time:", 
        "Markdown Content:", "Description:", "Image "
    )
    lines = text.splitlines()
    clean_lines = []
    for line in lines:
        if line.startswith(meta_prefixes) and ":" in line:
            # Check if it's really an Image N: prefix
            if line.startswith("Image ") and not re.match(r'^Image \d+:', line):
                clean_lines.append(line)
            continue
        clean_lines.append(line)
    
    text = "\n".join(clean_lines)

    # 2. Strip other markdown elements and clean up
    text = _MD_IMAGE.sub('', text)
    text = _MD_LINK.sub(r'\1', text)
    text = _BARE_URL.sub('', text)
    text = _HTML_TAG.sub('', text)
    text = _MULTI_NL.sub('\n\n', text)
    return text.strip()


# ── RAGEngine ─────────────────────────────────────────────────────────────

class RAGEngine:
    """Retrieval + grounded generation engine."""

    def __init__(self, top_k: int = 5) -> None:
        settings = get_settings()
        self.top_k = top_k
        self.max_hops = 3
        self.embedding_engine = get_embedding_engine()
        self.llm_engine = get_llm_engine()
        client = get_chroma_client()
        self.collection = get_collection(client, settings.CHROMA_COLLECTION)
        self.batch_size = settings.CHROMA_BATCH_SIZE

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    async def add_documents(
        self,
        source_id: str,
        source_title: str,
        chunks: list[str | dict[str, str]],
        source_url: str = "",
    ) -> int:
        """Embed and upsert chunks into ChromaDB.

        NOTE: Never call this with auto-generated fallback text. Only call it
        with real documentation content from the ingestion pipeline.
        """
        if not chunks:
            return 0

        # Normalize chunks to objects
        chunk_data = []
        for c in chunks:
            if isinstance(c, str):
                chunk_data.append({"content": c, "url": source_url, "parent_content": c})
            else:
                chunk_data.append({
                    "content": c.get("content", ""),
                    "url": c.get("url", source_url),
                    "parent_content": c.get("parent_content", c.get("content", ""))
                })

        # Clean chunks inline before embedding
        clean_chunks = []
        clean_metadatas = []
        import hashlib
        for i, item in enumerate(chunk_data):
            cleaned = _clean_chunk(item["content"])
            cleaned_parent = _clean_chunk(item["parent_content"])
            if len(cleaned) >= 50:
                clean_chunks.append(cleaned)
                clean_metadatas.append({
                    "source_id": source_id,
                    "source_title": source_title,
                    "source_url": item["url"],
                    "parent_content": cleaned_parent,
                    "chunk_index": i,
                })

        if not clean_chunks:
            logger.warning("add_documents: all chunks became empty after cleaning for %s", source_id)
            return 0
            
        embeddings = await self.embedding_engine.embed_documents(clean_chunks)
        ids = [f"{source_id}_chunk_{hashlib.md5(c.encode()).hexdigest()[:12]}" for c in clean_chunks]

        # Deduplicate within this batch to prevent ChromaDB DuplicateIDError.
        # Although we use .upsert, ChromaDB prohibits duplicate IDs within a single list.
        seen_ids = set()
        final_chunks = []
        final_metadatas = []
        final_embeddings = []
        final_ids = []
        
        for i in range(len(ids)):
            cid = ids[i]
            if cid not in seen_ids:
                seen_ids.add(cid)
                final_chunks.append(clean_chunks[i])
                final_metadatas.append(clean_metadatas[i])
                final_embeddings.append(embeddings[i])
                final_ids.append(cid)

        # Upsert in batches.
        for i in range(0, len(final_ids), self.batch_size):
            end = i + self.batch_size
            self.collection.upsert(
                documents=final_chunks[i:end],
                embeddings=final_embeddings[i:end],
                metadatas=final_metadatas[i:end],
                ids=final_ids[i:end],
            )
        logger.info("Indexed %d unique chunks (dropped %d duplicates) for source '%s'", 
                    len(final_ids), len(ids) - len(final_ids), source_title)
        return len(final_ids)

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict | None = None,
    ) -> list[dict[str, Any]]:
        """Hybrid search combining Dense Vector Similarity and Sparse BM25 Keywords via RRF."""
        k = top_k or self.top_k
        
        # 1. Fetch Dense Vector candidates
        query_embedding = await self.embedding_engine.embed_query(query)
        dense_k = max(k * 3, 20)
        query_kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": dense_k,
        }
        if filters:
            query_kwargs["where"] = filters

        result = await asyncio.to_thread(self.collection.query, **query_kwargs)

        dense_ids       = result.get("ids",       [[]])[0]
        dense_docs      = result.get("documents", [[]])[0]
        dense_metadatas = result.get("metadatas", [[]])[0]
        dense_distances = result.get("distances", [[]])[0]

        dense_rows = []
        for i in range(len(dense_ids)):
            dist = dense_distances[i] if i < len(dense_distances) else 1.0
            dense_rows.append({
                "id":         dense_ids[i],
                "content":    _clean_chunk(dense_docs[i]),
                "metadata":   dense_metadatas[i] or {},
                "distance":   dist,
                "similarity": round(1.0 - float(dist), 4),
            })

        # 2. Fetch/Build Sparse BM25 Ranker
        corpus_ids = []
        corpus_docs = []
        corpus_metadatas = []
        
        # Only load the whole active subset if filtered and small enough to avoid scanning massive DBs
        if filters:
            try:
                corp = await asyncio.to_thread(
                    self.collection.get,
                    where=filters,
                    include=["documents", "metadatas"]
                )
                corpus_ids = corp.get("ids", [])
                corpus_docs = corp.get("documents", [])
                corpus_metadatas = corp.get("metadatas", [])
            except Exception as e:
                logger.warning("Failed to fetch full sparse corpus from ChromaDB: %s", e)

        # Fallback to dense candidates if no filters are applied, or collection.get is empty/large
        if not corpus_ids or len(corpus_ids) > 1000:
            corpus_ids = [d["id"] for d in dense_rows]
            corpus_docs = [d["content"] for d in dense_rows]
            corpus_metadatas = [d["metadata"] for d in dense_rows]

        # Calculate BM25 scores
        from utils.bm25 import BM25Ranker
        sparse_rows = []
        if corpus_docs:
            try:
                bm25 = BM25Ranker(corpus_docs)
                bm25_scores = bm25.score(query)
                
                # Pair and sort by BM25 score
                sparse_candidates = []
                for idx in range(len(corpus_ids)):
                    if bm25_scores[idx] > 0.0:
                        sparse_candidates.append({
                            "id": corpus_ids[idx],
                            "content": _clean_chunk(corpus_docs[idx]),
                            "metadata": corpus_metadatas[idx] or {},
                            "bm25_score": bm25_scores[idx],
                            "distance": 0.5,
                            "similarity": 0.5
                        })
                sparse_candidates.sort(key=lambda x: x["bm25_score"], reverse=True)
                sparse_rows = sparse_candidates[:dense_k]
            except Exception as e:
                logger.error("Failed executing sparse BM25 search: %s", e)

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: dict[str, float] = {}
        doc_registry: dict[str, dict[str, Any]] = {}

        # Register dense candidates
        for rank, row in enumerate(dense_rows, 1):
            doc_id = row["id"]
            doc_registry[doc_id] = row
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (60.0 + rank))

        # Register sparse candidates
        for rank, row in enumerate(sparse_rows, 1):
            doc_id = row["id"]
            if doc_id not in doc_registry:
                doc_registry[doc_id] = row
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (60.0 + rank))

        # Sort all registered documents by RRF score descending
        fused_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        
        final_rows = []
        for doc_id in fused_ids[:k]:
            final_rows.append(doc_registry[doc_id])

        return final_rows

    async def _generate_hypothetical_doc(self, query: str) -> str:
        """Use LLM to generate a hypothetical ideal answer to the query (HyDE)."""
        prompt = (
            f"Please write a technical documentation excerpt that would perfectly answer this query: \"{query}\". "
            f"Focus on technical details, API names, and specific configuration steps. "
            f"Reply ONLY with the text of the documentation excerpt."
        )
        try:
            hypothetical_doc = await self.llm_engine.generate_response([{"role": "user", "content": prompt}])
            return hypothetical_doc.strip()
        except Exception as e:
            logger.warning("Failed to generate hypothetical doc for HyDE: %s", e)
            return query


    # ------------------------------------------------------------------
    # Generation — streaming (for the UI)
    # ------------------------------------------------------------------

    async def generate_response_stream(
        self, query: str, context_docs: list[dict[str, Any]], filters: dict | None = None
    ) -> AsyncIterator[str]:
        context = self._build_context(context_docs)
        messages = [{"role": "user", "content": self._build_answer_prompt(query, context)}]
        async for chunk in self.llm_engine.generate_response_stream(
            messages, system_prompt=CHAT_SYSTEM_PROMPT
        ):
            yield chunk

    # ------------------------------------------------------------------
    # Generation — non-streaming (used by process_message / stream_message)
    # ------------------------------------------------------------------

    async def generate_response(
        self, query: str, context_docs: list[dict[str, Any]], filters: dict | None = None
    ) -> tuple[str, list[dict[str, Any]]]:
        """Answer the query strictly from context_docs with agentic re-searching.

        Returns:
            (answer_text, source_list)
            answer_text is 'INSUFFICIENT_DOCUMENTATION' when docs don't help.
        """
        all_docs = list(context_docs)
        seen_queries = {query.lower().strip()}

        for hop in range(self.max_hops):
            context_text = self._build_context(all_docs)
            prompt = AGENTIC_RAG_PROMPT.format(context=context_text, query=query)
            
            result = await self.llm_engine.generate_structured_response(
                prompt, schema_hint=AGENTIC_RAG_SCHEMA
            )
            
            action = result.get("action", "insufficient")
            content = result.get("content", "")

            if action == "answer":
                logger.info("✅ [RAG] Answered on hop %d", hop)
                return content, self._build_source_list(all_docs)
            
            if action == "search":
                new_query = content.strip().lower()
                if new_query in seen_queries or not new_query:
                    logger.info("Stopping agentic RAG: duplicate or empty search query")
                    break
                
                seen_queries.add(new_query)
                logger.info("🔍 [RAG] Hop %d: re-searching for '%s'", hop, new_query)
                
                new_docs = await self.search(content, top_k=3, filters=filters)
                
                # Merge and deduplicate by ID
                seen_ids = {d["id"] for d in all_docs}
                added_count = 0
                for d in new_docs:
                    if d["id"] not in seen_ids:
                        all_docs.append(d)
                        seen_ids.add(d["id"])
                        added_count += 1
                
                if added_count == 0:
                    logger.info("Stopping agentic RAG: no new documentation found")
                    break
                
                # Sort by similarity and keep top 8
                all_docs.sort(key=lambda x: x.get("similarity", 0), reverse=True)
                all_docs = all_docs[:8]
                continue
            
            if action == "insufficient":
                break
        
        logger.warning("⚠️  [RAG] Could not answer from documentation for: %s", query[:80])
        return "INSUFFICIENT_DOCUMENTATION", self._build_source_list(all_docs)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_context(self, docs: list[dict[str, Any]]) -> str:
        """Concatenate doc contents for the LLM context window using Parent-Child strategy."""
        parts = []
        for i, doc in enumerate(docs, 1):
            title = doc.get("metadata", {}).get("source_title", "Document")
            # Retrieve parent chunk if available (Parent-Child Strategy), else fallback to child chunk
            content = doc.get("metadata", {}).get("parent_content", doc.get("content", ""))
            parts.append(f"[Source {i}: {title}]\n{content}")
        return "\n\n---\n\n".join(parts)

    def _build_answer_prompt(self, query: str, context: str) -> str:
        return (
            "You are an expert L2 Support AI. You must answer the user's question.\n"
            "CRITICAL INSTRUCTION: You MUST base your answer STRICTLY on the documentation excerpts provided below.\n"
            "Do NOT use your own general knowledge. Even if the documentation only provides partial steps or clues, "
            "synthesize them to the best of your ability. Do not state that the documentation is lacking unless it is completely irrelevant.\n\n"
            "Rules:\n"
            "- Answer clearly and concisely.\n"
            "- If the provided documentation is completely irrelevant to the question, reply EXACTLY with 'I_DONT_KNOW'.\n\n"
            f"Documentation:\n{context}\n\n"
            f"Question: {query}"
        )

    def _build_source_list(
        self, docs: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Convert retrieved docs to the source info format expected by chat_service."""
        seen: set[str] = set()
        sources: list[dict[str, Any]] = []
        for doc in docs:
            meta = doc.get("metadata", {})
            # Deduplicate by URL to show individual pages as sources
            url = str(meta.get("source_url", ""))
            if url in seen:
                continue
            seen.add(url)
            
            sources.append(
                {
                    "source_id":     str(meta.get("source_id", "")),
                    "title":         str(meta.get("source_title", "Unknown")),
                    "url":           url,
                    "chunk_excerpt": truncate_excerpt(doc.get("content", "")),
                }
            )
        return sources

    async def process_query(self, query: str) -> dict[str, Any]:
        """Convenience method for standalone testing."""
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
            "action": "resolve" if response != "INSUFFICIENT_DOCUMENTATION" else "escalated",
            "retrieval_score": round(avg_similarity, 4),
            "retrieved_chunks": context_docs,
        }


def get_rag_engine() -> RAGEngine:
    """Module-level singleton."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGEngine()
    return _rag_instance
