# Implementation Plan: PNW Knowledge Chatbot

**Branch**: `001-pnw-knowledge-chatbot` | **Date**: 2026-09-23 | **Spec**: `/specs/001-pnw-knowledge-chatbot/spec.md`

**Input**: Feature specification plus the requested stack: FastAPI, React, PostgreSQL with pgvector, and Docker.

## Summary

Build a source-grounded chatbot that answers student questions using only official Purdue University Northwest (PNW) sources, asks for campus context when required, and refuses unsupported or personalized answers while directing users to official offices or sources. The system uses a React client, a FastAPI service, PostgreSQL/pgvector retrieval, structure-preserving document ingestion, and deterministic grounding/refusal checks.

## Technical Context

**Language/Version**: Python 3.11 backend; TypeScript/React frontend.

**Primary Dependencies**: FastAPI, Pydantic Settings, SQLAlchemy 2, Alembic, Psycopg 3, pgvector, HTTPX/pytest, React, TypeScript, Vite, and PDF/HTML document parsing libraries. Any LLM/RAG orchestration layer is behind structured retrieval and grounding interfaces.

**Storage**: PostgreSQL with pgvector for source metadata, immutable source versions, full-text search, and embeddings; optional object storage or file cache for PDF/HTML snapshots. Source freshness, parser metadata, and citation evidence are retained per document version and chunk.

**Testing**: pytest with FastAPI/HTTPX contract tests, PostgreSQL/pgvector integration tests, React component tests, and representative evaluation questions with golden-source assertions.

**Target Platform**: Dockerized Linux deployment with separate FastAPI and React containers plus PostgreSQL/pgvector. Docker Compose is used for local development. No authenticated student-account integration is included.

**Project Type**: Web service / knowledge application.

**Performance Goals**: Operational response-time targets remain deferred as specified; retrieval correctness and source traceability take priority.

**Constraints**: Informational only; no authenticated student-record access; Hammond/Westville clarification when required; no unsupported claims; substantive answers cite official sources; freshness and staleness are explicit.

**Scale/Scope**: Small-to-medium corpus of official PNW resources, linked child pages, catalog entries, schedules, policies, and designated student service pages.

## Constitution Check

The constitution file is a template without binding project-specific governance rules. The design remains compliant with the feature requirements: informational-only behavior, source traceability, no student records, campus-aware disambiguation, and abstention when evidence is insufficient. No gate failures or exceptions are required.

## Project Structure

### Documentation

```text
specs/001-pnw-knowledge-chatbot/
├── plan.md
├── research.md
├── data-model.md
├── contracts/
│   └── chatbot-api.yaml
├── quickstart.md
├── spec.md
└── tasks.md
```

### Source Code

```text
backend/
├── app/
│   ├── api/
│   │   ├── deps.py
│   │   ├── routes/
│   │   └── schemas/
│   ├── core/
│   ├── db/
│   │   ├── base.py
│   │   ├── migrations/
│   │   └── session.py
│   ├── models/
│   ├── services/
│   │   ├── answer_grounding/
│   │   ├── escalation/
│   │   ├── retrieval/
│   │   └── source_freshness/
│   ├── corpus/
│   │   ├── indexes/
│   │   └── loaders/
│   ├── prompts/
│   ├── config/
│   └── main.py
├── tests/
│   ├── contract/
│   ├── eval/
│   ├── integration/
│   └── unit/
├── scripts/
└── requirements.txt

frontend/
├── src/
│   ├── api/
│   ├── components/
│   ├── hooks/
│   └── types/
├── package.json
└── vite.config.ts

docker-compose.yml
backend/Dockerfile
frontend/Dockerfile
```

**Structure Decision**: Use a separate React client and FastAPI service with a typed OpenAPI boundary. Backend domain logic follows routers → services → repositories → database; the frontend owns presentation and chat state only. PostgreSQL/pgvector is the system of record for indexed corpus metadata and embeddings. Docker Compose supports local orchestration, and production uses separate frontend and backend images. No separate Campus entity or authenticated student-data integration is introduced.

## Retrieval and Grounding Decisions

- Parse sources into a lossless intermediate representation before chunking.
- Preserve heading paths, page/anchor references, links, table headers/rows, campus scope, term scope, course codes, source version, and freshness metadata on every retrieval chunk.
- Use hybrid PostgreSQL full-text and pgvector retrieval with hard filters for official-domain, current-version, campus, and term applicability.
- Require claim-to-citation evidence validation before returning a direct answer; otherwise return clarification, insufficient information, or escalation.
- Replace source content atomically by canonical source identity and content hash while retaining prior versions for traceability.

## Phase 0 Research Summary

Research resolved the stack and integration choices. FastAPI with typed Pydantic schemas, SQLAlchemy 2/Alembic, Psycopg 3, and a repository abstraction are selected for the backend. React with TypeScript/Vite is selected for the browser client, with API types derived from the OpenAPI contract. PostgreSQL full-text search combined with pgvector is selected over vector-only retrieval. Docker Compose is selected for local orchestration with separate production images.

Document ingestion uses a structure-preserving PDF/HTML pipeline, retaining immutable source versions and parser metadata before generating citation-aware chunks. Direct answers require official current evidence and validated citations; stale, conflicting, missing, or insufficient evidence produces a limitation and escalation path.

## Phase 1 Design Summary

The public interface is `POST /api/chat/message`; its response includes answer type, citations, source freshness, campus used, and escalation information. The data model adds immutable source versions and retrieval chunks while retaining the student-facing entities in the specification. The quickstart validates the Dockerized stack, API contract, campus clarification, refusal behavior, source freshness, and multi-source citation preservation.

## Post-Design Constitution Check

PASS. The design preserves the feature boundaries: no student records, no transactions, no official decisions, official PNW sources only, explicit source traceability, and abstention on unsupported claims. React, Docker, PostgreSQL, and pgvector add deployment and persistence structure without introducing a constitution exception.

## Complexity Tracking

No constitution violations detected. Complexity tracking is not required.
