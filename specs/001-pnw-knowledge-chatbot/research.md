# Research: PNW Knowledge Chatbot

## Decision: separate React and FastAPI applications

**Rationale:** The backend owns retrieval, citations, freshness, refusal, and escalation logic; the React client owns chat state and presentation. A typed OpenAPI boundary prevents the UI from depending on persistence or retrieval internals.

**Alternatives considered:** A single application serving a bundled frontend is simpler for a prototype, but separate containers provide clearer boundaries and independent deployment without changing the public API.

## Decision: FastAPI with typed schemas and layered persistence

**Rationale:** FastAPI response models validate and document the public contract. Pydantic Settings provides typed environment configuration. SQLAlchemy 2, Alembic, and Psycopg 3 provide explicit database sessions and migrations. Routers call services, services call repositories, and database models remain separate from API schemas.

**Alternatives considered:** A synchronous database stack is viable, but the plan selects explicit async-compatible boundaries so request handling and integration tests do not block on database work. A module-global settings singleton is avoided because test overrides and environment validation are clearer with a cached settings dependency.

## Decision: PostgreSQL with pgvector and hybrid retrieval

**Rationale:** PostgreSQL stores source metadata, immutable versions, full-text indexes, and embeddings in one system. Exact/full-text retrieval is important for course codes, dates, terms, and policy names; pgvector adds semantic matching. Hard metadata filters apply official-domain, current-version, campus, and term constraints before generation.

**Alternatives considered:** Vector-only retrieval is rejected because it can miss exact dates and qualifiers. A separate vector database is unnecessary for the initial small-to-medium corpus and would duplicate source metadata and transaction handling.

## Decision: structure-preserving document ingestion

**Rationale:** Parse PDFs and HTML into a lossless intermediate representation before chunking. Preserve heading paths, page/anchor references, links, table headers and rows, campus scope, term scope, course codes, parser version, and source version on chunks. Schedule rows must retain their term/event/date/refund relationships; catalog chunks must retain prerequisite/offering/campus relationships.

**Alternatives considered:** Flattened text-only ingestion and PyMuPDF-only extraction are faster to start but are insufficient for complex tables, linked content, reading order, and precise citations. A structure-aware parser with a fallback is preferred.

## Decision: immutable source versions and explicit freshness

**Rationale:** A canonical URL/document identity receives immutable versions keyed by content hash. Changed content is parsed and validated before a transaction marks the new version current; prior versions remain available for reproducible citations. Missing or stale dates produce `unknown` or `stale` status rather than silently becoming current.

**Alternatives considered:** In-place replacement is simpler but loses historical evidence and makes citation reproducibility difficult. Deleting inaccessible sources is rejected; they should be marked unavailable.

## Decision: deterministic grounding and refusal gates

**Rationale:** Classify campus dependence, term dependence, personal/transactional requests, and unsupported topics before retrieval. Require relevant official evidence, detect conflicts, validate claim-to-citation mappings, and reject unknown citation IDs or stale/ambiguous evidence. Return a limitation plus an official escalation destination when a direct answer is not safe.

**Alternatives considered:** Post-hoc citation insertion or unconstrained LLM output may produce plausible but unsupported claims and is incompatible with the accuracy requirements.

## Decision: Docker Compose locally and separate production images

**Rationale:** Compose provides reproducible local orchestration for React, FastAPI, and PostgreSQL/pgvector. Separate frontend and backend images keep runtime configuration and scaling boundaries explicit; secrets remain environment-managed and never enter images.

**Alternatives considered:** Native frontend development with only a containerized backend is faster for some teams, but a fully containerized local stack better matches deployment and integration testing.

## Decision: contract and integration validation

**Rationale:** Test `POST /api/chat/message` against the OpenAPI schema, use HTTPX for API tests, and run PostgreSQL/pgvector integration tests rather than substituting SQLite. Add React tests for request/response rendering and a Docker Compose smoke test.

**Alternatives considered:** Frontend-only mocks and SQLite are useful for isolated unit tests but cannot validate the pgvector extension, vector operators, transaction behavior, or end-to-end citation contract.
