# Quickstart: PNW Knowledge Chatbot

## Prerequisites

- Docker and Docker Compose
- Git
- Python 3.11 with `backend/requirements.txt` installed for host-side corpus ingestion
- A curated set of official PNW HTML/PDF sources for ingestion

## Start the local stack

From the repository root:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
docker compose up --build
```

Expected services:

- React frontend at `http://localhost:5173`
- FastAPI backend at `http://localhost:8000`
- OpenAPI documentation at `http://localhost:8000/docs`
- PostgreSQL/pgvector at the Compose database service

Run database migrations and load the curated corpus. The import script expects at least three PDF/HTML files and their official PNW URLs in `manifest.json` (HTML documents may instead provide a canonical link).

```bash
cd backend
alembic -c alembic.ini upgrade head
cd ..
python backend/scripts/import_corpus.py ./corpus
```

Example `corpus/manifest.json`:

```json
{
  "policies/registration.html": {
    "source_url": "https://www.pnw.edu/registrar/registration/",
    "source_type": "policy",
    "campus_applicability": ["both"],
    "topic_tags": ["registration"]
  },
  "catalog/programs.pdf": {
    "source_url": "https://www.pnw.edu/academics/catalog/programs.pdf",
    "source_type": "pdf",
    "campus_applicability": ["unknown"],
    "topic_tags": ["catalog"]
  },
  "policies/financial-aid.html": {
    "source_url": "https://www.pnw.edu/financial-aid/policies/",
    "source_type": "policy",
    "campus_applicability": ["both"],
    "topic_tags": ["financial aid"]
  }
}
```

The CLI runs `sentence-transformers/all-MiniLM-L6-v2` locally on CPU and writes 384-dimensional vectors to pgvector; it does not require an embedding API key. Model weights are downloaded/cached by Sentence Transformers on first use. The command prints processed documents, chunks, model, dimensions, and database record counts.

## Contract validation

Validate `POST /api/chat/message` against [`contracts/chatbot-api.yaml`](contracts/chatbot-api.yaml).

Example request:

```bash
curl -sS http://localhost:8000/api/chat/message \
  -H 'content-type: application/json' \
  -d '{"question":"When is the registration deadline for fall semester?","term":"Fall 2026"}'
```

Expected outcome:

- A direct answer only when current official evidence supports it.
- `answer_type` is `direct_answer` with one or more citations.
- Each citation contains a stable source identity, official URL, excerpt, and freshness status.

## Required behavior scenarios

### Campus clarification

Ask: `Where is the parking office?`

Expected: If the applicable source is campus-specific, return `clarification_required` asking for Hammond or Westville. Do not assume a campus.

### Unsupported or personalized request

Ask: `Can you register me for a class?`

Expected: Return `escalation_required` or `insufficient_info`, state that the system cannot perform the action, and provide an official process or destination.

### Stale or missing source metadata

Use a source dated 2019 or with no date and ask whether the rule still applies.

Expected: Do not provide a confident direct answer. Return an explicit limitation and current official source or office when available.

### Multi-source catalog answer

Ask for prerequisites, offerings, and campus notes for a course or program.

Expected: Combine only related catalog evidence and preserve prerequisite, offering, term, and campus qualifiers in the answer and citations.

### Linked document and schedule-table preservation

Ask a parking question answered by a linked child page, then ask a term-specific deadline represented in a schedule table.

Expected: Cite the linked official page for parking and preserve the correct term/event/date/add-drop/refund relationship for the schedule answer.

## Automated validation

Run the backend unit and contract suites, PostgreSQL/pgvector integration suite, frontend tests, and the corpus evaluation script in CI. The required checks are:

- Direct claims have supporting official citations.
- Campus-dependent questions without campus context always clarify.
- Unsupported, conflicting, stale, and personalized requests never produce unsupported claims.
- Citation IDs resolve to stored source versions and excerpts.
- Vector dimensions/model identity match the configured embedding schema.
- Docker Compose health checks and API smoke tests pass.
