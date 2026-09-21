# Research: PNW Knowledge Chatbot

## Decision: source-grounded retrieval with explicit guardrails

The implementation will use a retrieval-first architecture that indexes official PNW sources, resolves campus qualifiers, and enforces a strict abstention policy whenever the answer is unsupported, personalized, or stale.

### Rationale

- The feature specification prioritizes accuracy and source traceability over completeness.
- The corpus is intentionally limited to official PNW pages, PDFs, catalogs, and linked pages, which reduces unsupported answer risk.
- Student questions often depend on campus, term, and policy context; those qualifiers must be kept in metadata and answer generation.
- Many questions involve generic information, but the chatbot must separate general guidance from human or transactional processes.

### Alternatives considered

1. Pure LLM-answer generation without retrieval
   - Rejected because it risks inventing or overgeneralizing answers and violates the no-guessing requirement.

2. Retrieval without source freshness tracking
   - Rejected because outdated or incomplete sources could produce wrong policy guidance.

3. Open-web retrieval or student forum content
   - Rejected because the spec requires official PNW sources only.

4. Personalized student-data access in the initial release
   - Rejected because the spec explicitly excludes authenticated or account-level student record access.

## Research Findings

### Source freshness and staleness

Decision: Missing or stale source dates should block a confident answer. If a document is older than the current policy cycle or no date is available, the system should say it cannot confirm the answer and cite the official source or contact.

Rationale: This matches the requirement to prioritize accuracy and decline unsupported claims.

### Student data access

Decision: The chatbot must use only general public PNW university information and must never access, infer, or use student records, personal history, or account data. Campus, term, and course context may be used only when supplied as context for a general-information question; it must not provide access to student records or account data.

Rationale: This keeps the chatbot informational and compliant with the scope constraints.

### Handling unanswered or uncertain questions

Decision: For unsupported, conflicting, or ambiguous questions, the chatbot must say it cannot confirm, explain what is missing, and direct the student to the appropriate official office or source.

Rationale: This aligns with both the user story around escalations and the acceptance requirements for uncertainty handling.

### Campus-aware behavior

Decision: When a campus-dependent question arrives without a campus, the chatbot must ask whether the student is at Hammond or Westville before giving a campus-specific answer.

Rationale: Campus-specific policy applications are treated as required context rather than optional context.

### Corpus scope

Decision: The initial knowledge corpus must include only authoritative PNW sources and linked official documents: student handbook, student conduct policy, information services policies, parking regulations, academic catalog, academic schedule, and relevant official support pages.

Rationale: The feature is designed as a trusted student information assistant, not a general web assistant.

## Design implications

- All source documents must have metadata for source URL, source type, document date, campus applicability, and coverage topic.
- Retrieval should rank campus and term-specific matches before generic matches.
- Responses must include explicit citation blocks and escalation guidance when the answer is uncertain.
- Response generation must include a final grounding check that rejects unsupported claims.
