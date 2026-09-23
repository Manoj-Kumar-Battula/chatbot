# Data Model: PNW Knowledge Chatbot

## Student-facing entities

### StudentQuestion

Represents the natural-language request and optional context.

Fields:
- `id`: UUID/string
- `text`: non-empty string
- `campus_context`: `Hammond | Westville | unknown | null`
- `term_context`: string/null
- `course_context`: string/null
- `created_at`: datetime

Validation:
- Reject blank questions.
- Campus values are context only and never grant access to student records.
- Campus-dependent questions without Hammond or Westville require clarification.

### ChatbotAnswer

Represents the response returned by the API.

Fields:
- `id`: UUID/string
- `question_id`: identifier
- `answer_text`: string
- `answer_type`: `direct_answer | clarification_required | insufficient_info | escalation_required`
- `citations`: list of `Citation`
- `campus_used`: `Hammond | Westville | null`
- `escalation_destination`: `EscalationDestination | null`
- `created_at`: datetime

Validation:
- A direct answer requires at least one valid citation.
- Unsupported, stale, conflicting, or personalized requests must include a limitation.
- No answer may claim an action was performed or an academic decision was made.

## Corpus and retrieval entities

### OfficialSource

Stable identity for an official PNW page or document.

Fields:
- `id`: UUID/string
- `canonical_url`: official PNW URL
- `title`: string
- `source_type`: `webpage | pdf | catalog_entry | policy | schedule | linked_document | office_page`
- `campus_applicability`: list of `Hammond | Westville | both | unknown`
- `topic_tags`: list of strings
- `current_version_id`: source version/null
- `availability_status`: `available | unavailable`

Validation:
- URLs must resolve to official PNW destinations or linked official PNW documents.
- A source identity is unique by canonical URL/document identity.

### OfficialSourceVersion

Immutable fetched and parsed representation of an OfficialSource.

Fields:
- `id`: UUID/string
- `source_id`: OfficialSource identifier
- `content_sha256`: string
- `document_date`: date/null
- `fetched_at`: datetime
- `effective_from`: date/null
- `effective_to`: date/null
- `etag`: string/null
- `last_modified`: string/null
- `parser_name`: string
- `parser_version`: string
- `extraction_status`: `complete | partial | failed`
- `freshness_status`: `current | stale | unknown | missing`
- `is_current`: boolean
- `supersedes_version_id`: identifier/null
- `raw_object_uri`: string/null

State transitions:
- `discovered -> indexed -> reviewed -> current`
- `reviewed -> stale | unknown`
- `stale | unknown -> unavailable` when the source cannot be verified

### RetrievalChunk

Citation-aware searchable unit derived from an OfficialSourceVersion.

Fields:
- `id`: UUID/string
- `version_id`: source version identifier
- `ordinal`: integer
- `text`: string
- `heading_path`: list of strings
- `section_ref`: string/null
- `page_start`, `page_end`: integer/null
- `html_anchor`: string/null
- `link_targets`: list of URLs
- `campus_scope`: list of campus values
- `term_scope`: list of strings
- `course_code`: string/null
- `event_type`: string/null
- `table_id`: string/null
- `table_row_key`: string/null
- `table_column_headers`: list of strings
- `embedding_model`: string/null
- `embedding_dimensions`: integer/null
- `embedding`: pgvector value/null
- `search_text`: PostgreSQL full-text value

Validation:
- Chunk boundaries preserve headings, paragraphs, list items, and complete table rows.
- Schedule rows retain term, event, date, add/drop, and refund relationships.
- Catalog chunks retain course, prerequisite, offering, and campus relationships.
- Only chunks from current, usable official versions can support a direct answer.

## Citation and escalation entities

### Citation

Traceable evidence attached to an answer.

Fields:
- `id`: UUID/string
- `source_id`: OfficialSource identifier
- `version_id`: source version identifier
- `chunk_id`: retrieval chunk identifier
- `title`: string
- `url`: official URL
- `excerpt_text`: exact stored excerpt
- `section_ref`: string/null
- `page_or_anchor`: string/null
- `source_date`: date/null
- `freshness_status`: `current | stale | unknown | missing`

Validation:
- Excerpt and location must exist in the referenced stored version.
- Citation IDs in generated answers must resolve to retrieved evidence.

### EscalationDestination

Official PNW destination for questions requiring human assistance.

Fields:
- `id`: UUID/string
- `name`: string
- `office_type`: `advisor | department | office | policy_page`
- `url`: official URL/null

Validation:
- Destination must be represented by an official PNW source in the corpus.

## Relationships

- StudentQuestion retrieves zero or more RetrievalChunks.
- RetrievalChunk belongs to one OfficialSourceVersion, which belongs to one OfficialSource.
- OfficialSource has many immutable OfficialSourceVersions and one current version at a time.
- ChatbotAnswer belongs to one StudentQuestion and contains many Citations.
- Citation references exactly one OfficialSourceVersion and RetrievalChunk.
- ChatbotAnswer may contain zero or one EscalationDestination.

## Grounding states

- `received -> classified -> retrieve`
- `campus_missing -> clarification_required`
- `unsupported_or_personalized -> escalation_required`
- `insufficient_or_stale_evidence -> insufficient_info`
- `supported_claims_with_valid_citations -> direct_answer`
