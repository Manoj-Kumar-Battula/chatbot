# Data Model: PNW Knowledge Chatbot

## Core entities

### StudentQuestion

Represents the user input and the context needed to answer it safely.

Fields:
- id: string
- text: string
- campus_context: enum | null (Hammond, Westville, unknown)
- term_context: string | null
- course_context: string | null
- created_at: datetime

Validation rules:
- text must be non-empty.
- when a question depends on campus, campus_context must be set to Hammond or Westville or the system must ask for clarification before giving a campus-specific answer.

### OfficialSource

Represents an official PNW source page or document used to support a response.

Fields:
- id: string
- title: string
- source_type: enum (webpage, pdf, catalog_entry, policy, schedule, linked_document, office_page)
- url: string
- document_date: date | null
- campus_applicability: list[enum] (Hammond, Westville, both, unknown)
- topic_tags: list[string]
- freshness_status: enum (current, stale, unknown)

Validation rules:
- url must be an official PNW destination or a linked official PNW document.
- source_type must match the actual source material being stored (for example, policy, catalog, schedule, or webpage).
- if document_date is missing or outdated, freshness_status should be unknown or stale and the system should avoid claiming certainty.

### Citation

A specific excerpt used to support a response.

Fields:
- id: string
- source_id: string
- excerpt_text: string
- section_ref: string | null
- page_or_anchor: string | null

Validation rules:
- excerpt_text must be traceable to a specific OfficialSource.
- citation cannot reference unsupported or invented information.

### ChatbotAnswer

The final response delivered to the student.

Fields:
- id: string
- question_id: string
- answer_text: string
- answer_type: enum (direct_answer, clarification_required, insufficient_info, escalation_required)
- citations: list[Citation]
- campus_used: enum | null
- escalation_destination: string | null
- created_at: datetime

Validation rules:
- direct answers require at least one valid Citation.
- answers that cannot be confirmed must include a limitation statement and an official escalation destination when available.
- answer_text cannot contain unsupported facts or undocumented policy assertions.

### EscalationDestination

An official PNW office, advisor, or source page that can help when the chatbot cannot answer confidently.

Fields:
- id: string
- name: string
- office_type: enum (advisor, department, office, policy_page)
- url: string | null

Validation rules:
- the destination must be an official PNW page, office, or advisor contact path already present in the source corpus.
- phone numbers and internal notes are excluded from the initial release because they are not required by the specification and are not guaranteed to be available in the official corpus.

## Relationships

- StudentQuestion may lead to one or more OfficialSource records through retrieval.
- OfficialSource may be associated with many Citation records.
- ChatbotAnswer belongs to one StudentQuestion and includes many Citation records.
- ChatbotAnswer may include zero or one EscalationDestination.

## State transitions

### Source freshness state

- discovered -> indexed -> reviewed -> current
- reviewed -> stale
- reviewed -> unknown
- stale -> insufficient_for_confident_answer

### Answer state

- received -> analyzed -> direct_answer
- received -> analyzed -> clarification_required
- received -> analyzed -> insufficient_info
- received -> analyzed -> escalation_required

### Query resolution

- campus_missing -> ask_for_campus
- campus_known -> retrieve
- unsupported_or_uncertain -> decline_and_guide
