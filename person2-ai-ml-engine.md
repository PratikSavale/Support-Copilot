# Person 2 — AI/ML Engine & RAG Pipeline

## Role: Backend Engineer (AI Core)

---

## Task Overview

Build the AI/ML core of the system including Google Gemini API integration, embedding generation, RAG (Retrieval-Augmented Generation) pipeline, text splitting, and ChromaDB vector database integration. This is the brain of the copilot that powers intelligent responses.

**Priority:** CRITICAL — Core AI functionality
**Start Time:** Hour 2 (after Person 1 provides database models)
**Primary Completion Target:** Hours 6-10

---

## Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| LLM | Google Gemini API (gemini-2.0-flash) | Latest |
| Embeddings | Gemini Embedding API (text-embedding-004) | Latest |
| RAG Framework | LangChain | 0.1.x |
| Vector Database | ChromaDB | 0.4.x |
| Text Splitting | LangChain Text Splitters | Included in langchain |
| HTTP Client | httpx | 0.26+ |

---

## Detailed Task Breakdown

### 2.1 Directory Structure

Create the following structure under `/backend/ai`:

```
backend/ai/
├── __init__.py
├── llm_engine.py          # Google Gemini LLM interface
├── embedding_engine.py    # Embedding generation
├── rag_pipeline.py        # RAG chain implementation
├── prompts.py             # System prompts
└── utils.py               # AI utilities
```

### 2.2 Google Gemini API Integration

**File:** `backend/ai/llm_engine.py`

```python
"""
Google Gemini LLM Engine
Handles all LLM inference through Gemini API.
"""
import os
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from config.settings import get_settings

class LLMEngine:
    """Engine for Google Gemini LLM inference."""
    
    def __init__(self):
        settings = get_settings()
        self.model = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.3,  # Low temperature for consistent responses
            max_tokens=1024,
        )
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            messages: List of {role, content} dicts
            system_prompt: Optional system prompt
            
        Returns:
            Generated response string
        """
        langchain_messages = []
        
        if system_prompt:
            langchain_messages.append(SystemMessage(content=system_prompt))
        
        for msg in messages:
            if msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_messages.append(AIMessage(content=msg["content"]))
            elif msg["role"] == "system":
                langchain_messages.append(SystemMessage(content=msg["content"]))
        
        response = await self.model.ainvoke(langchain_messages)
        return response.content
    
    async def generate_structured_response(
        self,
        prompt: str,
        response_format: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate a structured response using Gemini function calling.
        
        Args:
            prompt: The prompt to send
            response_format: Expected JSON schema
            
        Returns:
            Parsed JSON response
        """
        # Use Gemini's function calling capability
        # This is useful for ticket creation, confidence evaluation, etc.
        pass
    
    async def evaluate_relevance(
        self,
        query: str,
        context: str,
    ) -> float:
        """
        Evaluate how relevant the context is to the query.
        Returns a score between 0 and 1.
        
        Args:
            query: User's question
            context: Retrieved document chunk
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        prompt = f"""
        Evaluate how relevant the following context is to answering the user's query.
        
        Query: {query}
        Context: {context}
        
        Rate on a scale of 1-5:
        1 = Completely irrelevant
        2 = Slightly relevant
        3 = Moderately relevant
        4 = Highly relevant
        5 = Perfectly answers the query
        
        Return ONLY the number (1-5), nothing else.
        """
        response = await self.generate_response([{"role": "user", "content": prompt}])
        try:
            score = int(response.strip())
            return max(1, min(5, score)) / 5.0  # Normalize to 0-1
        except ValueError:
            return 0.5  # Default to neutral if parsing fails
```

### 2.3 Embedding Engine

**File:** `backend/ai/embedding_engine.py`

```python
"""
Embedding Engine
Handles text embedding generation using Gemini Embedding API.
"""
import os
from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config.settings import get_settings

class EmbeddingEngine:
    """Engine for generating text embeddings."""
    
    def __init__(self):
        settings = get_settings()
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.GEMINI_EMBEDDING_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
        )
    
    async def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a query string.
        
        Args:
            text: Query text
            
        Returns:
            Embedding vector (list of floats)
        """
        return await self.embeddings.aembed_query(text)
    
    async def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple documents.
        
        Args:
            documents: List of document texts
            
        Returns:
            List of embedding vectors
        """
        return await self.embeddings.aembed_documents(documents)
    
    def get_embedding_dimension(self) -> int:
        """
        Returns the dimension of the embedding vectors.
        For text-embedding-004, this is 768.
        """
        return 768
```

### 2.4 Text Splitter

**File:** `backend/utils/text_splitter.py`

```python
"""
Text Splitter Utility
Handles document chunking for RAG pipeline.
"""
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List

class TextSplitter:
    """Utility for splitting text into chunks for embedding."""
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
    ):
        """
        Initialize text splitter.
        
        Args:
            chunk_size: Maximum tokens per chunk
            chunk_overlap: Number of overlapping tokens between chunks
        """
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks.
        
        Args:
            text: Input text to split
            
        Returns:
            List of text chunks
        """
        return self.splitter.split_text(text)
    
    def create_chunks_with_metadata(
        self,
        text: str,
        source_id: str,
        source_title: str = "",
    ) -> List[dict]:
        """
        Split text and attach metadata to each chunk.
        
        Args:
            text: Input text
            source_id: ID of the knowledge source
            source_title: Title of the knowledge source
            
        Returns:
            List of dicts with 'content' and 'metadata' keys
        """
        chunks = self.split_text(text)
        result = []
        for i, chunk in enumerate(chunks):
            result.append({
                "content": chunk,
                "metadata": {
                    "source_id": source_id,
                    "source_title": source_title,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                },
            })
        return result
```

### 2.5 System Prompts

**File:** `backend/ai/prompts.py`

```python
"""
System Prompts
Defines all system prompts used throughout the application.
"""

CHAT_SYSTEM_PROMPT = """
You are an AI-powered L2 Support Copilot. Your job is to help end users resolve 
their technical issues by searching through known documentation and providing 
accurate, helpful responses.

Guidelines:
1. Always be professional and helpful
2. If you find relevant information in the knowledge base, provide a clear, 
   step-by-step solution
3. Cite your sources when providing answers
4. If you cannot find a definitive answer, acknowledge this and explain what 
   you found that was partially relevant
5. If the user's question is vague, ask clarifying questions
6. Do not make up information — only provide answers based on retrieved knowledge
7. Keep responses concise but complete
"""

CONFIDENCE_EVALUATION_PROMPT = """
Evaluate the confidence level of the following response to a user query.

User Query: {query}
Retrieved Context: {context}
Generated Response: {response}

Provide a confidence score between 0 and 1, where:
- 0.0-0.39: Low confidence (need more information or clarification)
- 0.40-0.74: Medium confidence (partial match found)
- 0.75-1.0: High confidence (strong match found)

Return ONLY the score as a decimal number, nothing else.
"""

TICKET_CREATION_PROMPT = """
Extract the following information from the conversation to create a support ticket:

1. Summary: A concise one-line summary of the issue
2. Severity: low, medium, high, or critical
3. Product Module: The component/module affected
4. Environment: Where the issue occurs (if mentioned)
5. Error Messages: Any specific error codes or messages
6. Steps to Reproduce: What the user was doing when the issue occurred
7. Troubleshooting Attempted: Any steps the user already tried
8. Conversation Summary: A brief summary of the entire conversation

Return as a JSON object with these keys.
"""

CLARIFICATION_PROMPT = """
The user's question is too vague to provide an accurate answer. 
Ask 2-3 specific clarifying questions that will help narrow down the issue.

Focus on:
- Which product/module is affected
- What the exact error message is
- What environment they are in
- What they were trying to do when the issue occurred

Keep questions concise and specific.
"""
```

### 2.6 RAG Pipeline

**File:** `backend/ai/rag_pipeline.py`

```python
"""
RAG (Retrieval-Augmented Generation) Pipeline
Orchestrates retrieval from ChromaDB and generation with Gemini.
"""
import os
from typing import List, Dict, Any, Optional, Tuple
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema.document import Document

from ai.embedding_engine import EmbeddingEngine
from ai.llm_engine import LLMEngine
from ai.prompts import CHAT_SYSTEM_PROMPT
from utils.text_splitter import TextSplitter
import chromadb

class RAGEngine:
    """
    RAG Pipeline Engine.
    Combines retrieval from ChromaDB with generation from Gemini.
    """
    
    def __init__(
        self,
        collection_name: str = "knowledge_chunks",
        top_k: int = 5,
    ):
        self.embedding_engine = EmbeddingEngine()
        self.llm_engine = LLMEngine()
        self.text_splitter = TextSplitter()
        self.top_k = top_k
        self.collection_name = collection_name
        
        # Initialize ChromaDB client
        settings = get_settings()
        self.chroma_client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
    
    async def add_documents(
        self,
        source_id: str,
        source_title: str,
        chunks: List[str],
    ) -> int:
        """
        Add document chunks to ChromaDB.
        
        Args:
            source_id: Knowledge source ID
            source_title: Title of the source
            chunks: List of text chunks
            
        Returns:
            Number of chunks added
        """
        if not chunks:
            return 0
        
        # Generate embeddings
        embeddings = await self.embedding_engine.embed_documents(chunks)
        
        # Prepare metadata
        metadatas = [
            {
                "source_id": source_id,
                "source_title": source_title,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            for i in range(len(chunks))
        ]
        
        # Add to ChromaDB
        ids = [f"{source_id}_chunk_{i}" for i in range(len(chunks))]
        self.collection.add(
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )
        
        return len(chunks)
    
    async def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[dict] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search the knowledge base for relevant documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of matching documents with scores
        """
        k = top_k or self.top_k
        
        # Generate query embedding
        query_embedding = await self.embedding_engine.embed_query(query)
        
        # Search ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filters,
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results["ids"][0])):
            formatted_results.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
                "similarity": 1 - results["distances"][0][i],  # Convert to similarity
            })
        
        return formatted_results
    
    async def generate_response(
        self,
        query: str,
        context_docs: List[Dict[str, Any]],
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Generate a response using retrieved context.
        
        Args:
            query: User's question
            context_docs: Retrieved documents from ChromaDB
            
        Returns:
            Tuple of (response, sources)
        """
        # Build context from retrieved documents
        context = "\n\n".join([doc["content"] for doc in context_docs])
        
        # Build messages for LLM
        messages = [
            {"role": "system", "content": CHAT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""
                Based on the following documentation, answer the user's question.
                
                Documentation:
                {context}
                
                User Question: {query}
                
                Provide a clear, helpful answer. If the documentation doesn't contain 
                enough information to fully answer the question, say so and provide 
                whatever partial information you can.
                """
            },
        ]
        
        # Generate response
        response = await self.llm_engine.generate_response(messages)
        
        # Format sources
        sources = []
        for doc in context_docs:
            sources.append({
                "source_id": doc["metadata"].get("source_id", ""),
                "title": doc["metadata"].get("source_title", ""),
                "chunk_excerpt": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
            })
        
        return response, sources
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Full RAG pipeline: search + generate.
        
        Args:
            query: User's question
            
        Returns:
            Dict with response, sources, and metadata
        """
        # Step 1: Search knowledge base
        context_docs = await self.search(query)
        
        if not context_docs:
            return {
                "response": "I couldn't find any relevant information in the knowledge base. I'll create a support ticket for your issue.",
                "sources": [],
                "action": "escalated",
                "confidence": 0.0,
            }
        
        # Step 2: Generate response
        response, sources = await self.generate_response(query, context_docs)
        
        # Calculate average similarity as confidence proxy
        avg_similarity = sum(doc["similarity"] for doc in context_docs) / len(context_docs)
        
        return {
            "response": response,
            "sources": sources,
            "action": "resolve",
            "confidence": avg_similarity,
        }
```

### 2.7 ChromaDB Integration Utilities

**File:** `backend/ai/chroma_utils.py`

```python
"""
ChromaDB Integration Utilities
Helper functions for ChromaDB operations.
"""
import chromadb
from config.settings import get_settings

def get_chroma_client() -> chromadb.HttpClient:
    """Get ChromaDB HTTP client."""
    settings = get_settings()
    return chromadb.HttpClient(
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT,
    )

def get_collection(client: chromadb.HttpClient, name: str = "knowledge_chunks"):
    """Get or create a ChromaDB collection."""
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )

def reset_collection(client: chromadb.HttpClient, name: str = "knowledge_chunks"):
    """Reset (delete and recreate) a ChromaDB collection."""
    client.delete_collection(name)
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )

def get_collection_stats(collection) -> dict:
    """Get statistics about a ChromaDB collection."""
    count = collection.count()
    return {
        "name": collection.name,
        "count": count,
    }
```

### 2.8 Requirements Update

Add these to `backend/requirements.txt` if not already present:

```
langchain==0.1.9
langchain-google-genai==0.0.6
langchain-community==0.0.21
google-generativeai==0.5.2
chromadb==0.4.24
```

---

## Acceptance Criteria

- [ ] `LLMEngine` can generate responses via Gemini API
- [ ] `EmbeddingEngine` can generate embeddings for text
- [ ] `TextSplitter` correctly splits documents into chunks (500 tokens, 100 overlap)
- [ ] `RAGEngine` can add documents to ChromaDB
- [ ] `RAGEngine` can search ChromaDB and return relevant results
- [ ] `RAGEngine.process_query()` returns formatted response with sources
- [ ] System prompts are defined and produce appropriate outputs
- [ ] ChromaDB connection works with Docker Compose
- [ ] All async functions properly use `await`
- [ ] Error handling for API failures (rate limits, network issues)

---

## Error Handling Requirements

Implement retry logic with exponential backoff for Gemini API calls:

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
)
async def call_gemini_api(prompt):
    # API call here
    pass
```

---

## Dependencies

| Dependency | Owner | Status |
|------------|-------|--------|
| Database models | Person 1 | Required for metadata storage |
| Settings | Person 1 | Required for API keys |
| ChromaDB | Person 8 | Required for vector storage |

## Deliverables To

| Recipient | What They Get |
|-----------|--------------|
| Person 3 | RAG engine, confidence scoring integration points |
| Person 4 | Embedding engine for analytics |
| Person 7 | Testable AI components |

---

## Tips for AI-Assisted Implementation

1. Start with `llm_engine.py` — test Gemini API connectivity first
2. Then build `embedding_engine.py` — verify embeddings are 768-dimensional
3. Build `text_splitter.py` — test with sample documents
4. Integrate with ChromaDB last — ensure it's running via Docker
5. Use LangChain's built-in abstractions to reduce boilerplate
6. Test with real documentation URLs from the demo scenario
7. Handle API key errors gracefully — they are the most common failure point
