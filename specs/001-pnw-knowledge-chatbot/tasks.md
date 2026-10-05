---

description: "Implementation task list for the PNW Knowledge Chatbot"
---

# Tasks: PNW Knowledge Chatbot

**Input**: Design documents from `/specs/001-pnw-knowledge-chatbot/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/chatbot-api.yaml`, and `quickstart.md`

**Organization**: Tasks are grouped by user story so each increment can be implemented and validated independently.

## Path Conventions

- Backend application: `backend/app/`
- Backend scripts: `backend/scripts/`
- Backend tests: `backend/tests/`
- Frontend application: `frontend/`
- Infrastructure: `docker-compose.yml`, `backend/Dockerfile`, and `frontend/Dockerfile`
- Dependencies: `backend/requirements.txt` and `frontend/package.json`

## Phase 1: Setup

**Purpose**: Initialize the project structure and selected stack.

- [x] T001 Create the backend package structure in `backend/app/`, including `api/`, `models/`, `services/`, `corpus/`, `prompts/`, and `config/`.
- [x] T002 Create the backend test and evaluation directories in `backend/tests/contract/`, `backend/tests/integration/`, `backend/tests/unit/`, and `backend/tests/eval/`.
- [x] T003 [P] Create the FastAPI application entrypoint and minimal configuration files in `backend/app/main.py` and `backend/app/config/`.
- [x] T004 [P] Create the Python dependency manifest in `backend/requirements.txt` for FastAPI, Pydantic Settings, SQLAlchemy, Alembic, Psycopg, pgvector, HTTPX, and pytest.
- [x] T005 [P] Create corpus import and answer validation script entrypoints in `backend/scripts/import_corpus.py` and `backend/scripts/validate_answers.py`.
- [x] T006 [P] Create the React TypeScript/Vite application shell and dependency manifest in `frontend/package.json`, `frontend/tsconfig.json`, `frontend/vite.config.ts`, and `frontend/src/`.
- [x] T007 [P] Create the backend and frontend container definitions in `backend/Dockerfile` and `frontend/Dockerfile`.
- [x] T008 [P] Create the local Docker Compose stack for FastAPI, React, and PostgreSQL with pgvector in `docker-compose.yml` and `.env.example`.

---

## Phase 2: Foundational

**Purpose**: Establish shared API, persistence, source, retrieval, and deployment foundations before user-story work.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T009 Configure typed environment settings, CORS, structured logging, and shared error handling in `backend/app/config/settings.py`, `backend/app/main.py`, and `backend/app/api/deps.py`.
- [ ] T010 Define shared `QuestionRequest`, `AnswerResponse`, and `Citation` schemas in `backend/app/api/schemas/chatbot.py` matching `specs/001-pnw-knowledge-chatbot/contracts/chatbot-api.yaml`, including non-empty question validation, answer types, source status, limitations, and citation provenance.
- [ ] T011 [P] Define the `StudentQuestion` model in `backend/app/models/student_question.py` with non-empty text, nullable Hammond/Westville/unknown campus context, nullable term/course context, and `created_at`.
- [x] T012 [P] Define the `OfficialSource` model in `backend/app/models/official_source.py` with official URL validation, source types `webpage`, `pdf`, `catalog_entry`, `policy`, `schedule`, `linked_document`, and `office_page`, campus applicability, topic tags, and freshness status `current`, `stale`, or `unknown`.
- [x] T013 [P] Define `OfficialSourceVersion` and `RetrievalChunk` models in `backend/app/models/official_source_version.py` and `backend/app/models/retrieval_chunk.py`, preserving immutable content hashes, parser metadata, heading paths, page/anchor references, links, table relationships, campus scope, term scope, course codes, and pgvector metadata.
- [ ] T014 [P] Define the `Citation`, `ChatbotAnswer`, and `EscalationDestination` models in `backend/app/models/citation.py`, `backend/app/models/chatbot_answer.py`, and `backend/app/models/escalation_destination.py`, enforcing traceable excerpts, valid answer types, official destinations, and direct-answer citation requirements.
- [x] T015 Configure SQLAlchemy 2 database sessions, declarative metadata, and repository dependencies in `backend/app/db/session.py`, `backend/app/db/base.py`, and `backend/app/api/deps.py`.
- [x] T016 Configure Alembic and create the initial PostgreSQL schema migration, including the pgvector extension, source/version/chunk tables, full-text fields, indexes, and vector dimension metadata in `backend/alembic.ini`, `backend/alembic/env.py`, and `backend/app/db/migrations/`.
- [ ] T017 Implement source freshness classification and response-facing statuses `current`, `stale`, `unknown`, and `missing` in `backend/app/services/source_freshness/`.
- [x] T018 Implement official PDF and HTML loading into a structure-preserving intermediate representation in `backend/app/corpus/loaders/`, retaining source URL, source type, dates, parser status, headings, links, tables, campus applicability, topic tags, and freshness metadata.
- [x] T019 Implement source identity, immutable version replacement, and current-version selection in `backend/app/corpus/` and `backend/app/services/retrieval/`, using canonical source identity and content hashes while retaining superseded versions.
- [x] T020 Implement the shared PostgreSQL/pgvector repository interface and hybrid full-text/vector retrieval in `backend/app/services/retrieval/`, including embedding-model/dimension validation and official-domain, current-version, campus, and term filters.
- [x] T020A [P] Implement the offline RAG ingestion pipeline required by the demo assignment in `backend/app/corpus/`, `backend/app/services/retrieval/`, and `backend/scripts/import_corpus.py`, reusing the existing PDF/HTML loaders from T018. Parse PDF/HTML sources into structured documents, create meaningful text chunks while preserving source/version/chunk metadata, generate local embeddings with the `sentence-transformers` `all-MiniLM-L6-v2` model (384 dimensions), and store documents, source versions, chunks, metadata, and embeddings in PostgreSQL with pgvector. Update the `RetrievalChunk.embedding` schema and the initial migration from `Vector(1536)` to `Vector(384)` to match the selected model. The CLI must accept an input corpus directory, ingest at least 3 documents, and print a useful ingestion summary showing documents, chunks, embedding model, dimensions, and stored records. This task is strictly for the offline ingestion pipeline and does not include the React chatbot or answer-generation features.
- [ ] T021 Configure Docker Compose health checks, migration startup ordering, backend CORS environment, frontend API base URL, and PostgreSQL/pgvector connectivity in `docker-compose.yml`, `backend/app/config/`, and `frontend/src/api/`.

**Checkpoint**: Foundation ready; user story implementation can begin.

---

## Phase 3: User Story 1 - Find an answer to a university question (Priority: P1) 🎯 MVP

**Goal**: Answer supported general PNW questions with concise, source-linked responses or an explicit limitation and escalation path.

**Independent Test**: Ask representative policy, deadline, registration, academic standing, grade appeal, financial aid, course, graduation, parking, program, and student-service questions; verify supported answers cite official PNW evidence and unsupported answers do not guess.

### Implementation

- [ ] T022 [US1] Implement general-question classification and retrieval selection in `backend/app/services/retrieval/`, limited to current official PNW sources and preserving source qualifiers.
- [ ] T023 [US1] Implement citation construction and evidence lookup in `backend/app/services/answer_grounding/`, requiring stable source/version/chunk IDs, exact excerpts, official URLs, and section/page/anchor metadata.
- [ ] T024 [US1] Implement grounded answer generation in `backend/app/services/answer_grounding/`, mapping each substantive claim to retrieved evidence and returning a limitation when evidence is insufficient, stale, conflicting, or missing.
- [ ] T025 [US1] Implement official escalation destination selection in `backend/app/services/escalation/` using only corpus-backed PNW advisors, departments, offices, and policy pages.
- [ ] T026 [US1] Implement `POST /api/chat/message` in `backend/app/api/routes/chat.py` using the contract schemas from `backend/app/api/schemas/chatbot.py`.
- [ ] T027 [US1] Wire the FastAPI chat route through classification, hybrid retrieval, freshness checks, grounding, citations, and escalation in `backend/app/api/routes/chat.py` and `backend/app/services/`.
- [ ] T028 [US1] Add React chat submission, loading, error, answer, citation, limitation, and escalation rendering in `frontend/src/api/chat.ts`, `frontend/src/hooks/useChat.ts`, and `frontend/src/components/`.
- [ ] T029 [US1] Reject unsupported claims and action requests such as registration, schedule changes, form submission, or academic decisions in `backend/app/services/answer_grounding/`, returning `insufficient_info` or `escalation_required`.

**Checkpoint**: The FastAPI API and React client provide an independently usable general-information MVP with citations and safe refusal.

---

## Phase 4: User Story 2 - Get campus-aware information (Priority: P1)

**Goal**: Use Hammond or Westville context when required and request it before giving a campus-specific answer.

**Independent Test**: Ask campus-dependent questions with Hammond, Westville, and no campus; verify the stated campus is used, missing context triggers clarification, and campus-independent questions do not request unnecessary context.

### Implementation

- [ ] T030 [P] [US2] Implement campus-context extraction and validation for Hammond and Westville in `backend/app/services/retrieval/campus_context.py`.
- [ ] T031 [US2] Implement campus applicability filtering for `OfficialSource` and `RetrievalChunk` records in `backend/app/services/retrieval/filters.py`, retaining campus context on questions and sources without introducing a separate Campus entity.
- [ ] T032 [US2] Implement `clarification_required` responses for campus-dependent questions without campus context in `backend/app/services/answer_grounding/campus_clarification.py`.
- [ ] T033 [US2] Update `POST /api/chat/message` in `backend/app/api/routes/chat.py` to return `campus_used` and avoid requesting campus context for campus-independent questions.
- [ ] T034 [US2] Preserve campus qualifiers in answer text, citation metadata, and React rendering in `backend/app/services/answer_grounding/` and `frontend/src/components/CitationList.tsx`.

**Checkpoint**: Campus-specific answers never assume Hammond or Westville, and both campuses remain independently testable through the API and UI.

---

## Phase 5: User Story 3 - Know when human help is needed (Priority: P1)

**Goal**: Keep the chatbot informational and direct personalized, transactional, official-decision, or unsupported requests to appropriate human help.

**Independent Test**: Ask for registration, schedule changes, form submission, academic decisions, personal-record advice, and unsupported information; verify no action or decision is simulated and an official limitation/escalation path is provided.

### Implementation

- [ ] T035 [P] [US3] Implement classification for transactional, personalized, official-decision, unsupported, and mixed requests in `backend/app/services/answer_grounding/request_classification.py`.
- [ ] T036 [P] [US3] Enforce the general-public-information-only boundary in `backend/app/services/answer_grounding/` and `backend/app/api/routes/chat.py`; never read, infer, or use student records, personal history, or account data.
- [ ] T037 [US3] Implement limitation messages and `escalation_required` responses in `backend/app/services/escalation/` using only known official PNW destinations and contract-supported fields.
- [ ] T038 [US3] Ensure supplied campus, term, and course values are used only as context for general-information retrieval in `backend/app/api/schemas/chatbot.py` and `backend/app/services/`.
- [ ] T039 [US3] Add mixed-request handling so supported general information is answered while personalized or transactional portions are escalated in `backend/app/services/answer_grounding/mixed_requests.py`.
- [ ] T040 [US3] Render refusal, limitation, and escalation states clearly in `frontend/src/components/AnswerPanel.tsx` without presenting unavailable actions as completed.

**Checkpoint**: User Stories 1–3 work without authentication, student records, simulated university actions, or unsupported claims.

---

## Phase 6: User Story 4 - Receive answers from varied official source formats (Priority: P2)

**Goal**: Preserve relationships and qualifiers across official PDFs, HTML pages, linked documents, structured tables, catalogs, schedules, and fragmented content.

**Independent Test**: Ask parking, academic schedule, and catalog questions against representative corpus content; verify linked sources, term/date relationships, prerequisites, offerings, and campus qualifiers remain accurate and cited.

### Implementation

- [ ] T041 [P] [US4] Implement PDF and HTML extraction for headings, definitions, numbered sections, links, expandable content, and structured tables in `backend/app/corpus/loaders/`.
- [ ] T042 [P] [US4] Implement linked-page and linked-document traversal for official PNW parking and policy content in `backend/app/corpus/loaders/link_traversal.py`.
- [ ] T043 [P] [US4] Preserve academic schedule relationships among term, event, date, add/drop period, and refund percentage in `backend/app/corpus/loaders/schedule.py` and `backend/app/services/retrieval/relationships.py`.
- [ ] T044 [P] [US4] Preserve catalog relationships among course requirements, prerequisites, offerings, campus applicability, expandable content, and related sections in `backend/app/corpus/loaders/catalog.py` and `backend/app/services/retrieval/relationships.py`.
- [ ] T045 [US4] Update answer grounding to combine related official citations without mixing unrelated sections, table cells, terms, campuses, or linked documents in `backend/app/services/answer_grounding/related_evidence.py`.
- [ ] T046 [US4] Update corpus replacement handling so revised official source content supersedes outdated content while retaining freshness status and traceable citations in `backend/app/corpus/versioning.py`.

**Checkpoint**: All four user stories are independently testable against the reviewed official source formats.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Align documentation, validate the complete stack, and verify measurable requirements without adding deferred capabilities.

- [ ] T047 [P] Document the implemented Docker Compose setup, API/UI validation flow, and expected outcomes in `specs/001-pnw-knowledge-chatbot/quickstart.md`.
- [ ] T048 [P] Verify the FastAPI response and React client types match `specs/001-pnw-knowledge-chatbot/contracts/chatbot-api.yaml` in `backend/tests/contract/` and `frontend/src/types/`.
- [ ] T049 [P] Add PostgreSQL/pgvector integration validation for extension availability, vector round trips, embedding dimension mismatch, hybrid retrieval ordering, metadata filters, and transaction rollback in `backend/tests/integration/`.
- [ ] T050 [P] Add Docker Compose smoke validation for backend health, frontend reachability, database readiness, migrations, and `POST /api/chat/message` in `backend/tests/integration/` and `docker-compose.yml`.
- [ ] T051 Run the scenarios in `specs/001-pnw-knowledge-chatbot/quickstart.md` against the curated official PNW corpus and record requirement gaps in `backend/scripts/validate_answers.py`.
- [ ] T052 Review all answer paths in `backend/app/services/` and `frontend/src/` for unsupported claims, missing citations, stale-source handling, campus ambiguity, escalation coverage, and accidental student-data access.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001–T005 are complete; T006–T008 establish the React, container, and Compose foundations.
- **Foundational (Phase 2)**: Depends on Setup and blocks all user-story work.
- **User Stories (Phases 3–6)**: Depend on Foundational completion.
- **Polish (Phase 7)**: Depends on the desired user stories and the Dockerized stack being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Phase 2; MVP API and React chat flow.
- **User Story 2 (P1)**: Starts after Phase 2 and integrates with US1 retrieval/route behavior; campus handling remains independently testable.
- **User Story 3 (P1)**: Starts after Phase 2 and integrates with the shared answer flow; refusal behavior remains independently testable.
- **User Story 4 (P2)**: Starts after Phase 2; improves corpus handling used by US1–US3 and is independently testable with representative source fixtures.

### Within Each User Story

- Shared models and infrastructure precede story services.
- Retrieval and freshness decisions precede grounded response generation.
- Backend contract behavior precedes corresponding UI rendering.
- Complete and validate each story checkpoint before moving to the next priority.

## Parallel Execution Examples

### Foundational phase

```text
T011 StudentQuestion model
T012 OfficialSource model
T013 OfficialSourceVersion and RetrievalChunk models
T014 Citation, ChatbotAnswer, and EscalationDestination models
T017 Source freshness classification
T018 PDF/HTML loaders
T020 PostgreSQL/pgvector retrieval interface
```

### User Story 1

```text
T022 General retrieval selection
T023 Citation construction
T025 Escalation destination selection
T028 React chat rendering
```

### User Story 2

```text
T030 Campus extraction and validation
T031 Campus applicability filters
```

### User Story 4

```text
T041 PDF/HTML extraction
T042 Linked-page traversal
T043 Academic schedule relationships
T044 Catalog relationships
```

## Implementation Strategy

### MVP First

1. Retain and verify completed Phase 1 setup tasks.
2. Complete Phase 2 foundational API, PostgreSQL/pgvector, source, retrieval, React shell, and Docker tasks.
3. Complete Phase 3 User Story 1.
4. Validate general answers, official citations, refusal behavior, freshness handling, React rendering, and Docker Compose integration.
5. Stop for MVP review before adding campus-specific and varied-format enhancements.

### Incremental Delivery

1. Add User Story 2 for Hammond and Westville clarification.
2. Add User Story 3 for strict human escalation and data-boundary handling.
3. Add User Story 4 for PDF, HTML, linked-page, schedule-table, and catalog relationships.
4. Complete cross-cutting contract, database, Docker, and quickstart validation.

### Scope Guardrails

- Use only general public PNW university information.
- Never access, infer, or use student records, personal history, or account data.
- Treat supplied campus, term, and course values only as context for general-information questions.
- Do not add authentication, transactions, personalized advising, health checks beyond service readiness, or operational performance targets.
