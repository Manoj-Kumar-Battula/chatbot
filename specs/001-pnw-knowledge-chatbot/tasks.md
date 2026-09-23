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
- Dependencies: `backend/requirements.txt`

## Phase 1: Setup

**Purpose**: Initialize the technology-neutral project structure described by the plan without adding capabilities outside the initial release.

- [x] T001 Create the backend package structure in `backend/app/`, including `api/`, `models/`, `services/`, `corpus/`, `prompts/`, and `config/`.
- [x] T002 Create the backend test and evaluation directories in `backend/tests/contract/`, `backend/tests/integration/`, `backend/tests/unit/`, and `backend/tests/eval/`.
- [x] T003 [P] Create the application entrypoint and minimal configuration files in `backend/app/main.py` and `backend/app/config/`.
- [x] T004 [P] Create the dependency manifest in `backend/requirements.txt` for the selected Python 3.11 service dependencies documented in `plan.md`.
- [x] T005 [P] Create corpus import and answer validation script entrypoints in `backend/scripts/import_corpus.py` and `backend/scripts/validate_answers.py`.

---

## Phase 2: Foundational

**Purpose**: Establish shared source, response, and API foundations before implementing individual user stories.

**Checkpoint**: Foundation ready; user story implementation can begin.

- [ ] T006 Define shared request and response schemas for `QuestionRequest`, `AnswerResponse`, and `Citation` in `backend/app/api/schemas/chatbot.py` according to `contracts/chatbot-api.yaml`.
- [ ] T007 [P] Define the `StudentQuestion` model in `backend/app/models/student_question.py` with non-empty `text`, nullable Hammond/Westville/unknown `campus_context`, nullable `term_context`, nullable `course_context`, and `created_at`.
- [ ] T008 [P] Define the `OfficialSource` model in `backend/app/models/official_source.py` with `source_type` values `webpage`, `pdf`, `catalog_entry`, `policy`, `schedule`, `linked_document`, and `office_page`; official URL validation; campus applicability; document date; topic tags; and `freshness_status` values `current`, `stale`, and `unknown`.
- [ ] T009 [P] Define the `Citation` model in `backend/app/models/citation.py` with a traceable `source_id`, non-invented `excerpt_text`, optional `section_ref`, and optional `page_or_anchor`.
- [ ] T010 [P] Define the `ChatbotAnswer` model in `backend/app/models/chatbot_answer.py` with `answer_type` values `direct_answer`, `clarification_required`, `insufficient_info`, and `escalation_required`, citations, optional campus used, optional escalation destination, and `created_at`.
- [ ] T011 [P] Define the `EscalationDestination` model in `backend/app/models/escalation_destination.py` with official PNW `name`, `office_type` values `advisor`, `department`, `office`, and `policy_page`, and optional official `url`.
- [ ] T012 Configure shared error handling and structured application logging in `backend/app/main.py` and `backend/app/config/` without adding authentication or student-record access.
- [ ] T013 Implement official-source corpus loading for PDF and HTML documents in `backend/app/corpus/loaders/`, preserving source URL, source type, document date, campus applicability, topic tags, and freshness status.
- [ ] T014 Implement the shared retrieval interface in `backend/app/services/retrieval/` for official sources, retaining section, page, table, term, campus, and linked-document relationships needed for citations.
- [ ] T015 Implement source freshness classification and stale/missing-source refusal inputs in `backend/app/services/source_freshness/`, including `current`, `stale`, `unknown`, and `missing` response-facing statuses.

---

## Phase 3: User Story 1 - Find an answer to a university question (Priority: P1) 🎯 MVP

**Goal**: Answer supported general PNW questions with clear, source-linked responses or an explicit limitation and escalation path.

**Independent Test**: Ask representative questions about policies, deadlines, registration, academic standing, grade appeals, financial aid, course requirements, prerequisites, graduation, parking, programs, and student services; verify that supported answers are clear and cite official PNW sources, while unsupported answers do not guess.

### Implementation

- [ ] T016 [US1] Implement general-question retrieval and source selection in `backend/app/services/retrieval/`, limited to the curated official PNW corpus.
- [ ] T017 [US1] Implement citation construction in `backend/app/services/answer_grounding/` so every substantive answer links to traceable official excerpts when links are available.
- [ ] T018 [US1] Implement grounded answer generation in `backend/app/services/answer_grounding/` that provides a concise direct answer only when the retrieved sources support it and otherwise states the limitation.
- [ ] T019 [US1] Implement escalation destination selection in `backend/app/services/escalation/` using only official PNW offices, advisors, departments, policy pages, and contacts represented in the corpus.
- [ ] T020 [US1] Implement `POST /api/chat/message` in `backend/app/api/routes/chat.py` using the `QuestionRequest` and `AnswerResponse` schemas from `backend/app/api/schemas/chatbot.py`.
- [ ] T021 [US1] Wire the chat route through retrieval, freshness checks, answer grounding, citations, and escalation in `backend/app/api/routes/chat.py` and `backend/app/services/`.
- [ ] T022 [US1] Reject unsupported claims and action requests such as registration, schedule changes, form submission, or academic decisions in `backend/app/services/answer_grounding/` and return `insufficient_info` or `escalation_required`.

**Checkpoint**: User Story 1 is independently usable for general PNW information questions and unsupported-question escalation.

---

## Phase 4: User Story 2 - Get campus-aware information (Priority: P1)

**Goal**: Use Hammond or Westville context when required and request it before giving a campus-specific answer.

**Independent Test**: Ask campus-dependent questions with Hammond, Westville, and no campus; verify that the stated campus is used, missing campus context triggers clarification, and campus-independent questions do not request unnecessary context.

### Implementation

- [ ] T023 [P] [US2] Implement campus-context extraction and validation for Hammond and Westville in `backend/app/services/retrieval/`.
- [ ] T024 [US2] Implement campus applicability filtering for `OfficialSource` records in `backend/app/services/retrieval/`, keeping campus context on the question and source rather than creating a separate Campus entity.
- [ ] T025 [US2] Implement `clarification_required` responses for campus-dependent questions without campus context in `backend/app/services/answer_grounding/`.
- [ ] T026 [US2] Update `POST /api/chat/message` handling in `backend/app/api/routes/chat.py` to return `campus_used` and to avoid requesting campus context for campus-independent questions.
- [ ] T027 [US2] Preserve campus qualifiers in citations and answer text in `backend/app/services/answer_grounding/` so the student can understand which campus the guidance applies to.

**Checkpoint**: User Stories 1 and 2 work independently; campus-specific answers never assume Hammond or Westville.

---

## Phase 5: User Story 3 - Know when human help is needed (Priority: P1)

**Goal**: Keep the chatbot informational, never access student records, and direct personalized, transactional, official-decision, or unsupported requests to appropriate human help.

**Independent Test**: Ask for registration, schedule changes, form submission, academic decisions, personal-record advice, and unsupported information; verify that the chatbot does not perform or decide, does not access or infer student data, and provides an official limitation and escalation path.

### Implementation

- [ ] T028 [P] [US3] Implement request classification for transactional, personalized, official-decision, and unsupported questions in `backend/app/services/answer_grounding/`.
- [ ] T029 [P] [US3] Enforce the general-public-information-only boundary in `backend/app/services/answer_grounding/` and `backend/app/api/routes/chat.py`; never read, infer, or use student records, personal history, or account data.
- [ ] T030 [US3] Implement limitation messages and `escalation_required` responses in `backend/app/services/escalation/` using only known official PNW destinations.
- [ ] T031 [US3] Ensure supplied campus, term, and course values are treated only as context for a general-information question in `backend/app/api/schemas/chatbot.py` and `backend/app/services/`.
- [ ] T032 [US3] Add mixed-request handling in `backend/app/services/answer_grounding/` so supported general information is answered while personalized or transactional portions are escalated.

**Checkpoint**: User Stories 1–3 work independently without authenticated student access or simulated university actions.

---

## Phase 6: User Story 4 - Receive answers from varied official source formats (Priority: P2)

**Goal**: Preserve relationships and qualifiers across official PDFs, HTML pages, linked documents, structured tables, catalogs, schedules, and fragmented content.

**Independent Test**: Ask parking, academic schedule, and catalog questions against representative corpus content; verify that linked sources, term/date relationships, prerequisites, offerings, and campus qualifiers remain accurate and cited.

### Implementation

- [ ] T033 [P] [US4] Implement PDF and HTML document extraction for headings, definitions, numbered sections, links, and structured tables in `backend/app/corpus/loaders/`.
- [ ] T034 [P] [US4] Implement linked-page and linked-document traversal for official PNW parking and policy content in `backend/app/corpus/loaders/`.
- [ ] T035 [P] [US4] Preserve academic schedule relationships among term, event, date, add/drop period, and refund percentage in `backend/app/corpus/loaders/` and `backend/app/services/retrieval/`.
- [ ] T036 [P] [US4] Preserve catalog relationships among course requirements, prerequisites, offerings, campus applicability, expandable content, and related sections in `backend/app/corpus/loaders/` and `backend/app/services/retrieval/`.
- [ ] T037 [US4] Update answer grounding in `backend/app/services/answer_grounding/` to combine related official citations without mixing unrelated sections, table cells, terms, campuses, or linked documents.
- [ ] T038 [US4] Update corpus replacement handling in `backend/app/corpus/` so revised official source content supersedes outdated content while retaining freshness status and traceable citations.

**Checkpoint**: All four user stories are independently testable against the reviewed official source formats.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Complete documentation alignment and validate the initial release without introducing deferred operational targets or new capabilities.

- [ ] T039 [P] Document the implemented validation flow and expected outcomes in `specs/001-pnw-knowledge-chatbot/quickstart.md`.
- [ ] T040 [P] Verify the API implementation matches `specs/001-pnw-knowledge-chatbot/contracts/chatbot-api.yaml` without adding endpoints, authentication, student records, or infrastructure assumptions.
- [ ] T041 Run the scenarios in `specs/001-pnw-knowledge-chatbot/quickstart.md` against the curated official PNW corpus and record any requirement gaps in `backend/scripts/validate_answers.py`.
- [ ] T042 Review all answer paths in `backend/app/services/` for unsupported claims, missing citations, stale-source handling, campus ambiguity, and escalation coverage.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; creates the project skeleton.
- **Foundational (Phase 2)**: Depends on Setup and blocks all user story work.
- **User Stories (Phases 3–6)**: Depend on Foundational completion.
- **Polish (Phase 7)**: Depends on the desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2; no dependency on other user stories and is the MVP.
- **US2 (P1)**: Starts after Phase 2; integrates with US1's chat flow but can be validated independently.
- **US3 (P1)**: Starts after Phase 2; integrates with the shared answer flow but can be validated independently.
- **US4 (P2)**: Starts after Phase 2; improves corpus handling used by US1–US3 and can be validated independently against source-format scenarios.

### Within Each User Story

- Shared models and services precede route integration.
- Retrieval and freshness decisions precede grounded response generation.
- Story work should be validated at its checkpoint before moving to the next priority.

---

## Parallel Execution Examples

### Foundational phase

```text
T007 StudentQuestion model
T008 OfficialSource model
T009 Citation model
T010 ChatbotAnswer model
T011 EscalationDestination model
T013 PDF/HTML corpus loaders
T015 Source freshness classification
```

### User Story 2

```text
T023 Campus context extraction
T024 Campus applicability filtering
T025 Missing-campus clarification behavior
```

### User Story 4

```text
T033 PDF/HTML extraction
T034 Linked-page traversal
T035 Academic schedule relationship preservation
T036 Catalog relationship preservation
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate general answers, official citations, refusal behavior, freshness handling, and escalation.
5. Stop for MVP review before adding campus-specific and varied-format enhancements.

### Incremental Delivery

1. Add User Story 2 for Hammond and Westville clarification.
2. Add User Story 3 for strict human-escalation and data-boundary handling.
3. Add User Story 4 for PDF, HTML, linked-page, schedule-table, and catalog relationships.
4. Complete cross-cutting contract and quickstart validation.

### Scope Guardrails

- Use only general public PNW university information.
- Never access, infer, or use student records, personal history, or account data.
- Treat supplied campus, term, and course values only as context for general-information questions.
- Do not add authentication, transactions, personalized advising, health checks, corpus versioning, or operational performance targets.
