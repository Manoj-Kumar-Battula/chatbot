# Implementation Plan: PNW Knowledge Chatbot

**Branch**: `001-pnw-knowledge-chatbot` | **Date**: 2026-09-20 | **Spec**: `/specs/001-pnw-knowledge-chatbot/spec.md`

**Input**: Feature specification from `/specs/001-pnw-knowledge-chatbot/spec.md`

## Summary

Build a source-grounded chatbot that answers student questions using only official Purdue University Northwest (PNW) sources, asks for campus context when required, and refuses unsupported or personalized answers while directing users to official offices or sources. The implementation will use a retrieval-first architecture that combines document ingestion, campus-aware citation, and strict refusal logic before generating a response.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: FastAPI, Pydantic, SQLAlchemy, pgvector-compatible PostgreSQL, a document parser/loader stack for PDFs and HTML, and an LLM/RAG orchestration layer that preserves source citations.

**Storage**: PostgreSQL for metadata, source records, and retrieval indexes; optional object storage or file cache for PDFs and HTML snapshots; source freshness metadata retained per document and citation.

**Testing**: pytest for unit/integration tests; contract tests for API behavior; evaluation suite with representative PNW questions and golden-source assertions.

**Target Platform**: Linux-based web service with browser UI or API client; no authenticated student-account integration in initial release.

**Project Type**: web-service / knowledge application

**Performance Goals**: Operational response-time targets are deferred pending the later requirements review, consistent with the specification.

**Constraints**: Must remain informational only; no authenticated student-record access; must ask for Hammond or Westville when required; no unsupported claims; all substantive answers must cite official sources; source freshness and staleness must be explicitly tracked.

**Scale/Scope**: Initial corpus limited to official PNW resources, linked child pages, catalog entries, schedules, policies, and designated student service pages; small-to-medium corpus with frequent updates and campus-specific qualifiers.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The current constitution file is a template without binding project-specific governance rules. The implementation remains compliant with the feature's explicit requirements: informational-only behavior, source-traceable answers, no student record access, and campus-aware disambiguation. No gate failures identified; no exceptions or waivers are required.

## Project Structure

### Documentation (this feature)

```text
specs/001-pnw-knowledge-chatbot/
├── plan.md              # This file
├── research.md          # Research findings and decisions
├── data-model.md        # Entity and relationship model
├── quickstart.md        # Validation and run guide
├── contracts/           # Public API contracts
├── spec.md              # Feature specification
└── tasks.md             # Future task planning output
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   └── schemas/
│   ├── models/
│   │   ├── student_question.py
│   │   ├── official_source.py
│   │   ├── citation.py
│   │   ├── chatbot_answer.py
│   │   └── escalation_destination.py
│   ├── services/
│   │   ├── retrieval/
│   │   ├── source_freshness/
│   │   ├── answer_grounding/
│   │   └── escalation/
│   ├── corpus/
│   │   ├── loaders/
│   │   └── indexes/
│   ├── prompts/
│   ├── config/
│   └── main.py
├── tests/
│   ├── contract/
│   ├── integration/
│   ├── unit/
│   └── eval/
├── scripts/
│   ├── import_corpus.py
│   └── validate_answers.py
└── requirements.txt
```

**Structure Decision**: A single backend service with a retrieval layer, source freshness checks, answer grounding, and escalation handling is sufficient for the initial release. The design intentionally avoids a separate Campus entity and avoids any authenticated student-data or account integration because the specification does not require those capabilities.

## Complexity Tracking

> No constitution violations detected. Complexity tracking is not required.
