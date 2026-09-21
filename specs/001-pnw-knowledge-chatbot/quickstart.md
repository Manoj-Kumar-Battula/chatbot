# Quickstart: PNW Knowledge Chatbot

## Purpose

This guide validates the end-to-end behavior of a source-grounded PNW chatbot before implementation and during evaluation.

## Validation setup

- Use the curated official PNW corpus, including official webpages, PDFs,
  linked documents, catalog content, schedules, and student-service pages.
- Confirm that each source exposes its official URL and available date or
  freshness information.
- Use the chatbot interface or service selected for implementation to run the
  scenarios below.

No particular programming language, database, hosting platform, or runtime
command is required by this validation guide.

## Validation scenarios

### 1. General university information

Ask: "When is the registration deadline for fall semester?"

Expected outcome:
- Answer includes a direct statement.
- At least one official PNW citation is attached.
- No unsupported claim is made.

### 2. Campus-required topic without campus

Ask: "Where is the parking office?"

Expected outcome:
- System asks for Hammond or Westville if campus-specific policy is required.
- It does not guess a campus before clarification.

### 3. Unsupported or personalized request

Ask: "Can you register me for a class?"

Expected outcome:
- System refuses to perform the action.
- It explains the limitation and provides the proper contact or process.

### 4. Stale or missing source metadata

Ask: "Does this rule still apply if the source is dated 2019?"

Expected outcome:
- System checks freshness metadata.
- If the source is stale or date is missing, it declines to answer confidently and points to a more current official source or office.

### 5. Multi-source answer aggregation

Ask: "What are the course prerequisites and campus notes for a specific program?"

Expected outcome:
- The answer combines relevant catalog and campus-specific qualifiers.
- Citations are included for each supporting source.

## Success checks

- All direct answers include official citations.
- Campus-dependent questions ask for clarification when campus is missing.
- Unsupported actions are routed to escalation or guidance.
- Stale or missing source dates are handled as insufficient evidence.
