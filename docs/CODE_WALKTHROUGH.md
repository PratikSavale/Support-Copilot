# EscalateAI — Code Walkthrough

> A component-by-component walkthrough of every file in the codebase, explaining what it does and how the pieces connect.

---

## Table of Contents

- [1. Project Root](#1-project-root)
- [2. Backend — Entry & Configuration](#2-backend--entry--configuration)
- [3. Backend — Data Models](#3-backend--data-models)
- [4. Backend — API Layer](#4-backend--api-layer)
- [5. Backend — Services (Business Logic)](#5-backend--services-business-logic)
- [6. Backend — AI Engine](#6-backend--ai-engine)
- [7. Backend — Utilities](#7-backend--utilities)
- [8. Backend — Middleware](#8-backend--middleware)
- [9. Frontend — App Shell & Routing](#9-frontend--app-shell--routing)
- [10. Frontend — State Management](#10-frontend--state-management)
- [11. Frontend — Pages](#11-frontend--pages)
- [12. Frontend — Components](#12-frontend--components)
- [13. Frontend — Hooks](#13-frontend--hooks)
- [14. Infrastructure & Deployment](#14-infrastructure--deployment)

---

## 1. Project Root

| File | Purpose |
|---|---|
| [docker-compose.yml](file:///home/shrey/Development/Support-Copilot/docker-compose.yml) | Orchestrates 5 services: PostgreSQL (pgvector), Redis, ChromaDB, Backend, Frontend. Each service has health checks, and the backend waits for all dependencies to be healthy before starting. |
| [Requirements.md](file:///home/shrey/Development/Support-Copilot/Requirements.md) | Original requirements document. Defines the architecture, modules, database schema, API endpoints, and configuration variables. |
| [GEMINI.md](file:///home/shrey/Development/Support-Copilot/GEMINI.md) | Development guidelines: coding standards for Python/FastAPI, React/TypeScript, AI/RAG patterns, testing, and workflow conventions. |
| [scripts/local_test_no_devops.sh](file:///home/shrey/Development/Support-Copilot/scripts/local_test_no_devops.sh) | Shell script that provisions a local pgvector container, initializes the DB schema, creates a Python venv, installs requirements, and starts the FastAPI server — all in one command. |

---

## 2. Backend — Entry & Configuration

### [main.py](file:///home/shrey/Development/Support-Copilot/backend/main.py)
**The application entrypoint.** Creates the FastAPI app, wires middleware, and mounts all routers.

- **Lifespan hook**: Seeds an admin user on startup (`seed_admin()`), disposes the DB engine on shutdown.
- **CORS**: Configured from `CORS_ORIGINS` env var (comma-separated).
- **Routers**: All API routes under `/api/v1`, WebSocket under `/api/v1/chat/ws`.
- **Health check**: `GET /health` returns version and status.

### [config/settings.py](file:///home/shrey/Development/Support-Copilot/backend/config/settings.py)
**Centralized configuration using Pydantic Settings.** Reads from `backend/.env` with fallback defaults.

Key settings groups:
- **Database**: `DATABASE_URL`, pool size, overflow, pre-ping.
- **AI**: `GEMINI_API_KEY`, `GEMINI_MODEL` (gemini-2.0-flash).
- **Jira**: URL, email, API token, project key, default issue type.
- **ChromaDB**: Host, port, collection name, batch size.
- **Auth**: `SECRET_KEY`, JWT algorithm (HS256), token expiry (24h).
- **CORS**: Origins parsed from comma-separated string via `cors_origins_list()`.

Uses `@lru_cache` so the settings singleton is computed once.

### [config/database.py](file:///home/shrey/Development/Support-Copilot/backend/config/database.py)
**Async SQLAlchemy engine and session factory.**

- Creates a connection pool with configurable size (default 10, overflow 20).
- `get_db()` is a dependency that yields a request-scoped session, commits on success, rolls back on exception.
- `expire_on_commit=False` prevents lazy-loading issues after flush.

### [seed_admin.py](file:///home/shrey/Development/Support-Copilot/backend/seed_admin.py)
**Creates a default admin user on first startup** (email: `admin@escalateai.com`, password: `admin123`). Only runs if the user doesn't already exist.

---

## 3. Backend — Data Models

All models use SQLAlchemy 2.0's modern `Mapped` / `mapped_column` syntax with UUID primary keys and auto-timestamps.

### [models/base.py](file:///home/shrey/Development/Support-Copilot/backend/models/base.py)
Two abstract base classes:
- **`TimestampedModel`**: Provides `id` (UUID), `created_at`, `updated_at` (with `onupdate`).
- **`UUIDCreatedModel`**: Provides `id` (UUID), `created_at` only.

### [models/enums.py](file:///home/shrey/Development/Support-Copilot/backend/models/enums.py)
All enums used across the schema:
- `UserRole`: agent, manager, admin
- `SessionStatus`: active, resolved, escalated
- `MessageRole`: user, assistant, system
- `TicketSeverity`: low, medium, high, critical
- `TicketStatus`: open, in_progress, resolved, closed
- `KnowledgeSourceType`: web_page, pdf, docx, markdown
- `KnowledgeSourceStatus`: pending, processing, indexed, error
- `MetricType`: query_count, resolution_count, escalation_count, avg_confidence, avg_response_time

### [models/user.py](file:///home/shrey/Development/Support-Copilot/backend/models/user.py)
The `users` table: `id`, `username`, `email`, `password_hash`, `role`. Has a `sessions` relationship.

### [models/session.py](file:///home/shrey/Development/Support-Copilot/backend/models/session.py)
The `sessions` table: `id`, `user_id` (FK), `title`, `status`. Has `messages` and `tickets` relationships. The session title auto-updates from the first user message.

### [models/message.py](file:///home/shrey/Development/Support-Copilot/backend/models/message.py)
The `messages` table: `id`, `session_id` (FK), `role`, `content`, `confidence_score`, `sources` (JSONB array of source citations), `action` (resolve/clarification/escalated/failed).

### [models/ticket.py](file:///home/shrey/Development/Support-Copilot/backend/models/ticket.py)
The `tickets` table — the richest model:
- Core: `summary`, `description`, `severity`, `status`.
- Jira sync: `jira_issue_key`, `jira_issue_id`, `jira_comments` (JSONB), `assignee`, `jira_synced`.
- Diagnostic: `product_module`, `environment`, `error_messages`, `steps_to_reproduce`, `troubleshooting_attempted`.
- References: `doc_references` (JSONB), `conversation_summary`.

### [models/knowledge_source.py](file:///home/shrey/Development/Support-Copilot/backend/models/knowledge_source.py)
The `knowledge_sources` table: `url`, `title`, `source_type`, `status` (pending → processing → indexed/error), `chunk_count`, `pages_crawled`, `max_pages`, `last_indexed_at`.

### [models/knowledge_chunk.py](file:///home/shrey/Development/Support-Copilot/backend/models/knowledge_chunk.py)
The `knowledge_chunks` table: `source_id` (FK), `chunk_index`, `content`, `embedding_vector` (pgvector VECTOR 768), `chunk_metadata` (JSONB).

### [models/metric.py](file:///home/shrey/Development/Support-Copilot/backend/models/metric.py)
The `metrics` table: `metric_type`, `date`, `value`, `metadata` (JSONB). Used for time-series analytics.

---

## 4. Backend — API Layer

### [api/router.py](file:///home/shrey/Development/Support-Copilot/backend/api/router.py)
**Central router aggregator.** Mounts all v1 routers with prefixes:
- `/auth` → authentication
- `/chat` → chat sessions and messages
- `/knowledge` → knowledge base management
- `/tickets` → ticket CRUD and Jira operations
- `/analytics` → dashboard metrics

### [api/dependencies.py](file:///home/shrey/Development/Support-Copilot/backend/api/dependencies.py)
**Shared FastAPI dependencies:**
- `DbSession`: Type alias for `Annotated[AsyncSession, Depends(get_db)]`.
- `get_current_user()`: Validates JWT from `Authorization: Bearer` header, looks up the user in DB.
- `CurrentUser`: Type alias for the authenticated user dependency.

### [api/v1/auth.py](file:///home/shrey/Development/Support-Copilot/backend/api/v1/auth.py)
- `POST /auth/login`: Accepts `OAuth2PasswordRequestForm`, validates credentials via `AuthService`, returns JWT.
- `POST /auth/register`: Creates a new user with hashed password.

### [api/v1/chat.py](file:///home/shrey/Development/Support-Copilot/backend/api/v1/chat.py)
- `POST /chat/sessions`: Creates a new chat session tied to the authenticated user.
- `GET /chat/sessions`: Lists all sessions for the current user.
- `GET /chat/sessions/{id}`: Returns session with full message history (eager-loaded).
- `POST /chat/sessions/{id}/messages`: Synchronous message processing (REST fallback for non-WebSocket clients).
- `POST /chat/sessions/{id}/feedback`: Submit thumbs-up/down feedback on an assistant message.

### [api/v1/knowledge.py](file:///home/shrey/Development/Support-Copilot/backend/api/v1/knowledge.py)
- `POST /knowledge/sources`: Add a URL to ingest. Creates the source record (status=pending), then kicks off `ingest_source()` as a `BackgroundTask`.
- `GET /knowledge/sources`: List all sources with status and chunk counts.
- `DELETE /knowledge/sources/{id}`: Delete source + its ChromaDB chunks + semantic cache entries.
- `POST /knowledge/sources/{id}/reindex`: Wipe existing chunks and re-ingest from scratch.

### [api/v1/tickets.py](file:///home/shrey/Development/Support-Copilot/backend/api/v1/tickets.py)
- `GET /tickets`: List tickets with optional `status` and `severity` filters.
- `GET /tickets/{id}`: Get a single ticket, optionally refreshing from Jira.
- `POST /tickets/escalate`: Manual admin escalation — creates a Jira ticket from a session.
- `PUT /tickets/{id}`: Update ticket fields (status, severity, etc.) and sync to Jira.
- `POST /tickets/{id}/comment`: Add a comment to a ticket (synced to Jira).
- `GET /tickets/jira/issue-types`: Fetch available Jira issue types.

### [api/v1/analytics.py](file:///home/shrey/Development/Support-Copilot/backend/api/v1/analytics.py)
- `GET /analytics/overview`: Dashboard metrics (total queries, resolution rate, escalation rate, avg confidence, total tickets, total sessions).
- `GET /analytics/trends`: Time-series data for charting (query_count, resolution_count, escalation_count).
- `GET /analytics/issues`: Top common issues grouped by product_module and severity.

### [api/v1/ws/websocket.py](file:///home/shrey/Development/Support-Copilot/backend/api/v1/ws/websocket.py)
**WebSocket endpoint for real-time streaming chat.**

Connection flow:
1. Client connects with `?token=JWT`.
2. Server validates JWT via `_get_user_from_token()` **before** calling `accept()`.
3. On invalid/missing token → closes with code `4001 Unauthorized`.
4. On valid token → accepts, enters message loop.

Message processing:
1. Receives `{"type": "message", "content": "...", "knowledge_sources": [...], "attachments": [...]}`.
2. Opens a fresh DB session scoped to message processing.
3. Verifies session ownership (user_id matches authenticated user).
4. Calls `chat_service.stream_message()`, iterating over yielded events.
5. Serializes events safely (handles Pydantic models, enums, datetimes) and sends via WebSocket.
6. Commits DB on success, rolls back on error.

---

## 5. Backend — Services (Business Logic)

### [services/service_factory.py](file:///home/shrey/Development/Support-Copilot/backend/services/service_factory.py)
**Dependency injection factory.** Uses `@lru_cache(maxsize=1)` for singleton services:
- `get_jira_client()` → `JiraClient`
- `get_confidence_service()` → `ConfidenceService(llm_engine)`
- `get_ticket_service()` → `TicketService(jira_client, llm_engine)`
- `get_knowledge_service()` → `KnowledgeService(rag_engine)`
- `get_chat_service()` → `ChatService(rag_engine, confidence_service, ticket_service)`
- `get_analytics_service()` → `AnalyticsService()`

This avoids module-level instantiation that would fail if external services aren't ready at import time.

### [services/chat_service.py](file:///home/shrey/Development/Support-Copilot/backend/services/chat_service.py)
**The central orchestrator** — the largest service (~770 lines).

**`process_message()`** (synchronous REST path):
1. Ensures session exists (auto-creates if not found).
2. Stores user message in DB.
3. Checks semantic cache (two-stage: semantic + diagnostic signature).
4. If cache hit → return instantly.
5. Calculates initial confidence (heuristic).
6. If LOW → return clarifying questions (LLM-generated).
7. If MEDIUM/HIGH → run hybrid RAG search with source filters.
8. If no results → escalate to Jira.
9. Calculate post-retrieval confidence (weighted formula).
10. If HIGH → generate response via agentic RAG, return with sources.
11. If LOW/MEDIUM or `INSUFFICIENT_DOCUMENTATION` → escalate to Jira.

**`stream_message()`** (WebSocket path):
Same pipeline as above, but yields events (`start`, `chunk`, `final`) for streaming. Additionally includes:
- **ReAct Query Understanding**: Uses LLM to refine the search query from conversation context.
- **Multi-hop Architecture**: After initial retrieval, asks the LLM if context is sufficient. If not, performs an additional search.

**`submit_message_feedback()`**:
- On 👍: Stores the Q&A pair in semantic cache (primary + diagnostic signature entries).
- On 👎: Marks the message as `failed`, so its sources are excluded from future searches in the same session (DRY Search).

### [services/confidence_service.py](file:///home/shrey/Development/Support-Copilot/backend/services/confidence_service.py)
**Two-phase confidence scoring:**

**Phase 1 — Initial (pre-retrieval):**
- Base score: 0.40 (default, enough to trigger RAG search).
- Short queries (< 3 words) → 0.15 (triggers clarification).
- Boost if user already answered clarifications (+0.10).
- Boost if conversation history exists (+0.10).

**Phase 2 — Post-retrieval:**
```
confidence = (0.40 × retrieval) + (0.35 × relevance) + (0.25 × completeness)
```
- **Retrieval**: Average cosine similarity of retrieved chunks.
- **Relevance**: LLM evaluates relevance of top document (1-5 integer → normalized to 0-1).
- **Completeness**: Heuristic from `ai/utils.py` — measures prose density and sentence structure.

**Thresholds:**
- ≤ 0.20 → `clarification` (ask questions)
- 0.20–0.60 → `searching` (proceed with RAG)
- ≥ 0.60 → `resolve` (generate answer)

### [services/ticket_service.py](file:///home/shrey/Development/Support-Copilot/backend/services/ticket_service.py)
**Ticket creation and management.**

**`create_ticket_from_chat()`**:
1. Takes the last 20 messages of conversation history.
2. Sends to LLM with `TICKET_CREATION_PROMPT` to extract structured fields (summary, severity, product_module, environment, error_messages, steps_to_reproduce, troubleshooting_attempted).
3. Creates a `Ticket` ORM record.
4. Calls `jira_client.create_ticket()` (best-effort — never blocks on failure).
5. Marks the session as `escalated`.

**`create_manual_ticket()`**: Allows admins to manually escalate any session. Retrieves actual messages from DB if not provided.

Also handles: CRUD operations, Jira status sync, and comment management.

### [services/jira_client.py](file:///home/shrey/Development/Support-Copilot/backend/services/jira_client.py)
**Async Jira Cloud REST API v3 wrapper** (~870 lines).

**Mock fallback**: If `JIRA_API_TOKEN` is empty, all methods return sensible mock data. This lets the entire pipeline work in demo/dev without Jira credentials.

**Key operations:**
- `create_ticket()`: Maps ticket fields to Jira v3 ADF format. Auto-detects available issue types and falls back to Task/Story if Bug is unavailable.
- `get_ticket()`: Fetches full issue details.
- `add_comment()`: Adds ADF-formatted comments.
- `update_ticket()`: Handles status transitions via the transitions API, field updates via PUT.
- `sync_status()`: Full bi-directional sync (status, priority, assignee, comments) from Jira → local DB.
- `search_issues()`: JQL-based search.
- `get_issue_types()`, `get_priorities()`, `get_custom_fields()`: Metadata fetchers.

All HTTP methods use `tenacity` retry with exponential backoff (3 attempts, 2-10s wait).

### [services/knowledge_service.py](file:///home/shrey/Development/Support-Copilot/backend/services/knowledge_service.py)
**Knowledge base ingestion pipeline.**

**`ingest_source()`** (runs as BackgroundTask with its own DB session):
1. Marks source as `processing`.
2. Calls `WebScraper.crawl_website()` (concurrent, up to 200 pages, 20 workers).
3. Cleans and deduplicates pages via `clean_and_filter_pages()`.
4. Splits into parent-child chunks via `TextSplitter.split_parent_child()`.
5. Embeds and upserts into ChromaDB via `RAGEngine.add_documents()`.
6. Updates source record (status=indexed, chunk_count, last_indexed_at).
7. On error: rolls back, marks source as `error`.

**`delete_source()`**: Removes from ChromaDB, invalidates semantic cache, deletes DB record.

**`reindex_source()`**: Deletes existing ChromaDB data + cache, then re-ingests.

### [services/cache_service.py](file:///home/shrey/Development/Support-Copilot/backend/services/cache_service.py)
**Semantic query cache using a dedicated ChromaDB collection (`semantic_cache`).**

- **`check_cache()`**: Embeds the query, searches the cache collection. Returns a hit only if similarity ≥ 0.95. Supports filtering by `knowledge_source_ids` to prevent cross-source leakage. Increments hit count on match.
- **`store_cache()`**: Stores a verified Q&A pair. Uses MD5 hash of the normalized query as the ChromaDB document ID.
- **`invalidate_cache()`**: Deletes all cache entries matching a `source_id` (called when a source is deleted or re-indexed).

### [services/auth_service.py](file:///home/shrey/Development/Support-Copilot/backend/services/auth_service.py)
**JWT authentication:**
- `verify_password()`: bcrypt comparison.
- `get_password_hash()`: bcrypt with salt.
- `create_access_token()`: JWT encoding with configurable expiry.
- `get_user_by_email()`: DB lookup.
- `create_user()`: Creates user with hashed password.

### [services/analytics_service.py](file:///home/shrey/Development/Support-Copilot/backend/services/analytics_service.py)
**Dashboard metrics aggregation using raw SQL (via SQLAlchemy).**

- **`get_overview()`**: Counts total queries (user messages), resolved messages (assistant messages with sources), total tickets, calculates resolution/escalation rates, average confidence score, and total sessions — all within a configurable lookback window.
- **`get_trends()`**: Groups data by date for time-series charts (query_count, resolution_count, escalation_count).
- **`get_common_issues()`**: Groups tickets by `product_module` × `severity`, returns the top N most frequent.

---

## 6. Backend — AI Engine

### [ai/prompts.py](file:///home/shrey/Development/Support-Copilot/backend/ai/prompts.py)
**All LLM prompts in one file** (no hardcoded strings in logic):

- `CHAT_SYSTEM_PROMPT`: Base system identity — professional, cite sources, don't fabricate.
- `CONFIDENCE_EVALUATION_PROMPT`: Template for confidence scoring (0-1 decimal).
- `TICKET_CREATION_PROMPT`: Extracts 8 structured fields from conversation for Jira tickets.
- `CLARIFICATION_PROMPT`: Generates 2-3 questions about affected module, error text, environment, user action.
- `AGENTIC_RAG_PROMPT`: The core agentic prompt — instructs the LLM to either `answer`, `search` (re-query), or report `insufficient`. Includes critical domain-scoping rules to prevent hallucination.
- `AGENTIC_RAG_SCHEMA`: Expected JSON output format.

### [ai/llm_engine.py](file:///home/shrey/Development/Support-Copilot/backend/ai/llm_engine.py)
**Google Gemini wrapper via LangChain.**

- `generate_response()`: Standard text generation. Handles LangChain's list-of-content-blocks format. Returns mock on API error.
- `generate_response_stream()`: Async streaming via `model.astream()`.
- `generate_structured_response()`: Appends `"Respond with valid JSON ONLY"` instruction, parses JSON from response (strips markdown fences).
- `generate_multimodal_response()`: Handles images and non-image files via base64 inline content. Supports structured output schemas.
- `evaluate_relevance()`: Asks LLM to rate query-context relevance on a 1-5 scale.

All methods use `tenacity` retry (3 attempts, exponential backoff). Temperature set to 0.3 for consistency.

### [ai/embedding_engine.py](file:///home/shrey/Development/Support-Copilot/backend/ai/embedding_engine.py)
**On-device embedding using FastEmbed (BAAI/bge-small-en-v1.5, 384 dimensions).**

- `embed_query()`: Embeds a single query string. Runs in a thread pool via `asyncio.to_thread()`.
- `embed_documents()`: Batch-embeds a list of document chunks. Also threaded.
- Runs entirely on ONNX Runtime — no API keys, no rate limits, no cost.
- Module-level singleton via `get_embedding_engine()`.

### [ai/rag_pipeline.py](file:///home/shrey/Development/Support-Copilot/backend/ai/rag_pipeline.py)
**The core RAG engine** — retrieval + grounded generation.

**`add_documents()`**:
1. Cleans chunks inline (strips Jina metadata, markdown links, HTML).
2. Rejects chunks < 50 chars.
3. Generates embeddings via FastEmbed.
4. Assigns content-hash-based IDs for deduplication.
5. Upserts to ChromaDB in configurable batch sizes.

**`search()`** — Hybrid retrieval with RRF:
1. **Dense**: Queries ChromaDB with embedding (top-k × 3 candidates).
2. **Sparse**: Builds a BM25 ranker over the corpus (filtered subset or dense candidates).
3. **RRF**: Merges rankings using `score += 1/(60 + rank)`, sorts by fused score, returns top-k.

**`generate_response()`** — Agentic multi-hop:
1. Builds context from retrieved docs using **parent-child strategy** (uses `parent_content` from metadata if available).
2. Sends the `AGENTIC_RAG_PROMPT` with context and query.
3. Parses the structured JSON response (`action`: answer/search/insufficient).
4. If `search` → executes a new search with the LLM's suggested query, merges results, loops (up to 3 hops).
5. If `answer` → returns the grounded response with deduplicated source list.
6. If `insufficient` → returns `INSUFFICIENT_DOCUMENTATION`.

### [ai/chroma_utils.py](file:///home/shrey/Development/Support-Copilot/backend/ai/chroma_utils.py)
Helper to get/create ChromaDB client and collections. Uses `cosine` distance for similarity.

### [ai/utils.py](file:///home/shrey/Development/Support-Copilot/backend/ai/utils.py)
- `truncate_excerpt()`: Truncates chunk text to 300 chars for source citations.
- `compute_completeness_score()`: Heuristic that measures average line count and length of chunks — proxy for how "complete" the retrieved content is.

---

## 7. Backend — Utilities

### [utils/web_scraper.py](file:///home/shrey/Development/Support-Copilot/backend/utils/web_scraper.py)
**Concurrent website crawler with adaptive fetching.**

- **`fetch_content()`**: Single-page fetch via Jina AI Reader (`https://r.jina.ai/{url}`).
- **`crawl_website()`**: Full site crawler:
  - Uses `asyncio.Queue` + worker pool (up to 20 concurrent).
  - Restricts crawl to the starting URL's path prefix.
  - For each page: tries local HTML parsing first (BeautifulSoup), falls back to Jina Reader if content quality is low.
  - **Storybook SPA heuristic**: Detects `?path=/docs/` URLs and fetches iframe content.
  - Extracts links from both HTML `<a>/<frame>/<iframe>` tags and markdown `[text](url)` syntax.
  - **Quality filter**: Rejects frameset boilerplate, pure class-listing pages, and pages with insufficient prose density.
  - **Progress callback**: Updates `pages_crawled` in DB for real-time admin feedback.
  - Polite crawling: 0.1s delay between requests.

### [utils/content_cleaner.py](file:///home/shrey/Development/Support-Copilot/backend/utils/content_cleaner.py)
**Cleaning pipeline between scraper and splitter.**

`clean_page()` transforms:
1. Strips Jina metadata (Title:, URL Source:, Published Time:, etc.).
2. Converts markdown links `[text](url)` → plain text.
3. Removes markdown images.
4. Removes bare URL lines.
5. Removes navigation boilerplate (Prev/Next/All Classes/Skip to content/Copyright).
6. Strips leftover HTML tags.
7. Collapses excessive whitespace.

`deduplicate_pages()`: Fingerprints pages using `MD5(head[:200] + tail[-200:] + len_bucket)` and removes duplicates.

`clean_and_filter_pages()`: Full pipeline — clean each page → filter by length (≥ 100 chars) → deduplicate.

### [utils/text_splitter.py](file:///home/shrey/Development/Support-Copilot/backend/utils/text_splitter.py)
**Text chunking with quality filtering and parent-child strategy.**

`TextSplitter` maintains two `RecursiveCharacterTextSplitter` instances:
- **Child splitter**: 500 chars, 100 overlap (for precise retrieval).
- **Parent splitter**: 2000 chars, 200 overlap (for rich LLM context).

`split_parent_child()`: Splits text into large parents, then each parent into small children. Returns `[{child_content, parent_content}]` pairs. Children are embedded; parents are stored in metadata.

`_is_quality_chunk()`: Rejects chunks that are:
- Too short (< 60 chars).
- Mostly dotted identifiers (> 50%, e.g., Java package listings).
- Mostly single words (> 60% with < 2 sentence endings).
- Mostly markdown links (> 70%).
- Almost no prose (< 20% sentence-like lines with < 2 punctuation marks).

### [utils/bm25.py](file:///home/shrey/Development/Support-Copilot/backend/utils/bm25.py)
**Self-contained BM25 sparse ranker** (no external dependencies).

- Tokenizes with regex, preserving dotted identifiers (e.g., `com.test.Class`).
- Standard BM25 formula with smoothed IDF: `log(1 + (N - df + 0.5) / (df + 0.5))`.
- Parameters: `k1=1.5`, `b=0.75`.

### [utils/log_parser.py](file:///home/shrey/Development/Support-Copilot/backend/utils/log_parser.py)
**Extracts deterministic diagnostic signatures from stack traces.**

Recognizes three stack trace formats:
- **Java**: `at com.example.Service.method(Service.java:73)` → `NullPointerException in Service.method line 73`
- **Python**: `File "app.py", line 42, in method` → `ValueError in app.py.method line 42`
- **Node.js**: `at Object.method (/app/index.js:58:21)` → `TypeError in index.js.method line 58`

Used by the semantic cache for deterministic cache lookups on log-heavy queries.

### [utils/attachment_parser.py](file:///home/shrey/Development/Support-Copilot/backend/utils/attachment_parser.py)
**Parses user-uploaded evidence files into structured issue descriptions.**

Flow by type:
- **Images/Videos**: Sent to Gemini via `generate_multimodal_response()` with structured output schema (`AttachmentSummarySchema`). Extracts errors, screen names, steps, and evidence.
- **Logs/Text**: Regex heuristics extract error lines, URLs, and steps. Then LLM refines the summary.
- **PDFs**: Text extracted via `pypdf`, then processed like logs.

Output: `ParsedAttachment` dataclass with `issue_summary`, `detected_error`, `screen_or_area`, `visible_steps`, `important_evidence`, and `confidence` score.

### [utils/formatters.py](file:///home/shrey/Development/Support-Copilot/backend/utils/formatters.py)
Simple formatting helpers for API responses.

### [utils/validators.py](file:///home/shrey/Development/Support-Copilot/backend/utils/validators.py)
Input validation utilities (URL format, string length, etc.).

### [utils/logging_config.py](file:///home/shrey/Development/Support-Copilot/backend/utils/logging_config.py)
Sets up structured logging with configurable levels.

---

## 8. Backend — Middleware

### [middleware/error_handler.py](file:///home/shrey/Development/Support-Copilot/backend/middleware/error_handler.py)
**Centralized exception handlers** registered on the FastAPI app:

| Exception | HTTP Code | Response Type |
|---|---|---|
| `HTTPException` | Varies | `http_error` |
| `RequestValidationError` | 422 | `validation_error` with field details |
| `ValidationError` (Pydantic) | 422 | `validation_error` |
| `SQLAlchemyError` | 500 | `database_error` |
| `Exception` (catch-all) | 500 | `internal_error` |

All errors return a consistent `{"error": {"code", "message", "type"}}` envelope.

### [middleware/rate_limiter.py](file:///home/shrey/Development/Support-Copilot/backend/middleware/rate_limiter.py)
**Rate limiting via slowapi.** Uses client IP as the key function. Returns 429 with a consistent error envelope on exceeding limits.

---

## 9. Frontend — App Shell & Routing

### [src/App.tsx](file:///home/shrey/Development/Support-Copilot/frontend/src/App.tsx)
**Root component with React Router.**

Two route guard components:
- `ProtectedRoute`: Redirects to `/login` if not authenticated.
- `AdminRoute`: Redirects to `/login` if not authenticated, to `/` if not admin role.

Route structure:
- `/login` → `LoginPage`
- `/`, `/tickets` → `TicketsLandingPage` (wrapped in `UserLayout`)
- `/chat/:sessionId` → `ChatPage` (wrapped in `UserLayout`)
- `/admin` → `AdminDashboard` (wrapped in `AdminLayout`)
- `/admin/knowledge` → `KnowledgePage` (wrapped in `AdminLayout`)
- `/admin/tickets` → `TicketsPage` (wrapped in `AdminLayout`)

### [src/layouts/UserLayout.tsx](file:///home/shrey/Development/Support-Copilot/frontend/src/layouts/UserLayout.tsx)
Minimal layout wrapper for the user view — renders `Header` + children.

### [src/layouts/AdminLayout.tsx](file:///home/shrey/Development/Support-Copilot/frontend/src/layouts/AdminLayout.tsx)
Admin layout with sidebar navigation (Dashboard, Knowledge, Tickets) and a responsive header.

### [src/config/api.ts](file:///home/shrey/Development/Support-Copilot/frontend/src/config/api.ts)
**Axios instance + WebSocket URL configuration.**

- `API_BASE_URL`: From `VITE_API_BASE_URL` env var or `http://localhost:8000/api/v1`.
- `WS_BASE_URL`: From `VITE_WS_URL` env var or `ws://localhost:8000/api/v1/chat/ws`.
- **Request interceptor**: Reads JWT from Zustand's persisted localStorage and attaches as `Authorization: Bearer` header on every request.

---

## 10. Frontend — State Management

### [src/store/authStore.ts](file:///home/shrey/Development/Support-Copilot/frontend/src/store/authStore.ts)
**Authentication state** (persisted to localStorage via Zustand middleware):
- `token`, `user`, `isAuthenticated`
- `login()`: Calls `/auth/login`, stores token and user.
- `logout()`: Clears token and user.

### [src/store/userStore.ts](file:///home/shrey/Development/Support-Copilot/frontend/src/store/userStore.ts)
**User view state:**
- `sessions`, `messages`, `isStreaming`, `isConnected`, `isHistoryLoading`
- `availableSources`, `selectedSources` (for knowledge source filtering in chat)
- `fetchSessions()`: GET `/chat/sessions`
- `fetchSessionHistory()`: GET `/chat/sessions/{id}` — maps server messages, handles 404 gracefully.
- `fetchAvailableSources()`: GET `/knowledge/sources`
- `toggleSourceSelection()`: Toggle a source for scoped search.
- Message management: `addMessage`, `updateLastMessage`, `setMessages`, `clearMessages`.

### [src/store/adminStore.ts](file:///home/shrey/Development/Support-Copilot/frontend/src/store/adminStore.ts)
**Admin view state:**
- **Knowledge**: `loadKnowledgeSources`, `addKnowledgeSource`, `deleteKnowledgeSource`, `reindexSource`.
- **Tickets**: `loadTickets` (with filter support), `syncTicket`, `addTicketComment`, `openTicketDetail`, `closeTicketDetail`.
- **Analytics**: `loadMetrics`.
- **Jira**: `loadIssueTypes`.
- All actions handle errors and set `error` state for UI display.

---

## 11. Frontend — Pages

### [src/pages/LoginPage.tsx](file:///home/shrey/Development/Support-Copilot/frontend/src/pages/LoginPage.tsx)
Login form with email/password. On success, navigates to `/` (user) or `/admin` (admin role).

### [src/pages/TicketsLandingPage.tsx](file:///home/shrey/Development/Support-Copilot/frontend/src/pages/TicketsLandingPage.tsx)
**User's landing page.** Shows existing sessions and a "New Conversation" button. Each session card shows title, status, and creation date. Clicking navigates to `/chat/:sessionId`.

### [src/pages/ChatPage.tsx](file:///home/shrey/Development/Support-Copilot/frontend/src/pages/ChatPage.tsx)
**The main chat interface.**
- Uses the `useWebSocket` hook for real-time communication.
- Renders message list with `MessageBubble` components.
- Includes `MessageInput` for text + file attachments.
- Shows `KnowledgeSourceSelector` for scoping RAG search.
- Loads session history on mount.

### [src/pages/AdminPages.tsx](file:///home/shrey/Development/Support-Copilot/frontend/src/pages/AdminPages.tsx)
**Three admin pages in one file:**

- **`AdminDashboard`**: Displays `StatCard` components for key metrics (total queries, resolution rate, escalation rate, avg confidence, total tickets, total sessions). Loads data via `loadMetrics()`.

- **`KnowledgePage`**: Add URL form → source list (with status badges: pending/processing/indexed/error, chunk count, pages crawled progress). Actions: delete, re-index. Uses polling to update status during ingestion.

- **`TicketsPage`**: Ticket list with severity/status filters and color-coded badges. Click to open `TicketDetail` modal with full ticket info, Jira sync, and comment thread.

---

## 12. Frontend — Components

### [src/components/MessageBubble.tsx](file:///home/shrey/Development/Support-Copilot/frontend/src/components/MessageBubble.tsx)
Renders a single chat message with:
- Different styling for user vs. assistant messages.
- Markdown rendering for assistant content.
- Source citations panel (expandable).
- Ticket info card when escalated.
- Thumbs up/down feedback buttons on assistant messages.
- Clarification suggestion chips.

### [src/components/MessageInput.tsx](file:///home/shrey/Development/Support-Copilot/frontend/src/components/MessageInput.tsx)
Rich input component supporting:
- Text input with Enter-to-send.
- File attachment (drag-and-drop + file picker).
- Attachment preview with type detection.
- Upload progress indication.

### [src/components/SourceChipPanel.tsx](file:///home/shrey/Development/Support-Copilot/frontend/src/components/SourceChipPanel.tsx)
Expandable panel showing the documentation sources that were used to generate an answer. Each chip shows the source title and a chunk excerpt.

### [src/components/Header.tsx](file:///home/shrey/Development/Support-Copilot/frontend/src/components/Header.tsx)
App header with branding, navigation, user info, and logout button. Shows admin link for admin users.

### [src/components/KnowledgeSourceSelector.tsx](file:///home/shrey/Development/Support-Copilot/frontend/src/components/KnowledgeSourceSelector.tsx)
Dropdown/chip selector that lets users scope their chat queries to specific knowledge sources.

### [src/components/TicketDetail.tsx](file:///home/shrey/Development/Support-Copilot/frontend/src/components/TicketDetail.tsx)
Modal showing full ticket details: summary, description, severity, status, product module, error messages, steps to reproduce, Jira link, comment thread, and sync button.

### [src/components/ClarificationChips.tsx](file:///home/shrey/Development/Support-Copilot/frontend/src/components/ClarificationChips.tsx)
Clickable suggestion chips shown when the AI asks clarifying questions. Clicking a chip sends it as the user's response.

### [src/components/StatCard.tsx](file:///home/shrey/Development/Support-Copilot/frontend/src/components/StatCard.tsx)
Reusable card for dashboard metrics — title, value, icon, and optional trend indicator.

### [src/components/StatusBadge.tsx](file:///home/shrey/Development/Support-Copilot/frontend/src/components/StatusBadge.tsx)
Color-coded badge for ticket/source status (open=blue, in_progress=yellow, resolved=green, error=red).

### [src/components/KnowledgeGraph.tsx](file:///home/shrey/Development/Support-Copilot/frontend/src/components/KnowledgeGraph.tsx) & [RagGraphModal.tsx](file:///home/shrey/Development/Support-Copilot/frontend/src/components/RagGraphModal.tsx)
Visualization components for the RAG retrieval graph — shows how documents connect to the query.

---

## 13. Frontend — Hooks

### [src/hooks/useWebSocket.ts](file:///home/shrey/Development/Support-Copilot/frontend/src/hooks/useWebSocket.ts)
**Singleton WebSocket manager** — the most critical frontend hook.

Design decisions:
- Uses **global variables** (`globalSocket`, `globalSessionId`) instead of React state to survive StrictMode double-renders and component re-mounts.
- **Ref-based store access** (`storeRef`) to avoid stale closures in WebSocket callbacks.
- **Auto-reconnect**: Exponential backoff (1s → 2s → 4s → 8s → 10s), max 5 attempts.
- **Buffered send**: If socket is in `CONNECTING` state, waits 1s then retries.

`sendMessage()`:
1. Adds user message to UI immediately (optimistic update).
2. Sends `{type: "message", content, knowledge_sources, attachments}` via WebSocket.
3. Selected knowledge sources are read from the store at send time.

`stopQuery()`: Closes the WebSocket to abort a streaming response.

### [src/hooks/useKnowledgePolling.ts](file:///home/shrey/Development/Support-Copilot/frontend/src/hooks/useKnowledgePolling.ts)
Polls `GET /knowledge/sources` every 3 seconds while any source is in `processing` status, to update the admin UI with crawl progress.

---

## 14. Infrastructure & Deployment

### [docker-compose.yml](file:///home/shrey/Development/Support-Copilot/docker-compose.yml)
Five-service stack:

| Service | Image | Port | Health Check |
|---|---|---|---|
| `db` | pgvector/pgvector:pg16 | 5432 (internal) | `pg_isready` |
| `redis` | redis:7-alpine | 6379 (internal) | `redis-cli ping` |
| `chroma` | chromadb/chroma:latest | 8000 (internal) | TCP probe |
| `backend` | Custom (Dockerfile) | 8000 → 8000 | `curl /health` |
| `frontend` | Custom (Dockerfile + Nginx) | 8080 → 80 | N/A |

Dependency chain: `frontend → backend → (db + redis + chroma)`

### [backend/Dockerfile](file:///home/shrey/Development/Support-Copilot/backend/Dockerfile)
Python 3.11 slim image. Installs requirements, copies source, runs `uvicorn main:app --host 0.0.0.0 --port 8000`.

### [frontend/Dockerfile](file:///home/shrey/Development/Support-Copilot/frontend/Dockerfile)
Two-stage build: Node 18 for `npm run build`, then Nginx Alpine to serve the static bundle.

### [frontend/nginx.conf](file:///home/shrey/Development/Support-Copilot/frontend/nginx.conf)
Nginx config that:
- Serves the Vite build output.
- Proxies `/api/` requests to the backend.
- Handles SPA fallback (all routes → `index.html`).
- Proxies WebSocket upgrade headers.

---

## Schemas Reference

### [schemas/chat.py](file:///home/shrey/Development/Support-Copilot/backend/schemas/chat.py)
Pydantic models: `ChatRequest`, `ChatResponse`, `SourceInfo`, `TicketInfo`, `Action` enum, `SessionResponse`, `MessageResponse`.

### [schemas/ticket.py](file:///home/shrey/Development/Support-Copilot/backend/schemas/ticket.py)
Pydantic models: `TicketCreate`, `TicketUpdate`, `TicketResponse`, `EscalateRequest`.

### [schemas/knowledge.py](file:///home/shrey/Development/Support-Copilot/backend/schemas/knowledge.py)
Pydantic models: `KnowledgeSourceCreate`, `KnowledgeSourceResponse`.

### [schemas/analytics.py](file:///home/shrey/Development/Support-Copilot/backend/schemas/analytics.py)
Pydantic models: `MetricOverview`, `TrendPoint`, `CommonIssue`, `AnalyticsOverviewResponse`.

### [schemas/auth.py](file:///home/shrey/Development/Support-Copilot/backend/schemas/auth.py)
Pydantic models: `LoginRequest`, `RegisterRequest`, `TokenResponse`.

---

## File Count Summary

| Layer | Files | Total Lines |
|---|---|---|
| Backend — Config | 3 | ~160 |
| Backend — Models | 10 | ~430 |
| Backend — Schemas | 7 | ~290 |
| Backend — API Routes | 8 | ~460 |
| Backend — Services | 10 | ~2,600 |
| Backend — AI Engine | 7 | ~870 |
| Backend — Utils | 10 | ~1,120 |
| Backend — Middleware | 3 | ~120 |
| Frontend — Pages | 4 | ~1,500 |
| Frontend — Components | 11 | ~3,400 |
| Frontend — Stores | 3 | ~670 |
| Frontend — Hooks | 2 | ~360 |
| Frontend — Config | 1 | ~30 |
| **Total** | **~79 source files** | **~12,000 lines** |
