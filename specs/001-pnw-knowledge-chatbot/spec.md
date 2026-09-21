# Feature Specification: PNW Knowledge Chatbot

**Feature Branch**: `001-pnw-knowledge-chatbot`

**Created**: 2026-09-16

**Status**: Draft

**Input**: User description: "Build a knowledge-based chatbot for Purdue University Northwest (PNW) that provides accurate, source-linked answers to student questions using official PNW information."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find an answer to a university question (Priority: P1)

As a PNW student, I want to ask a question in plain language and receive a clear answer based on official PNW information so that I do not have to search across multiple university webpages.

**Why this priority**: Answering common university questions is the core student value and directly addresses the primary interview finding.

**Independent Test**: Ask representative questions about policies, deadlines, registration, academic standing, grade appeals, financial aid, course requirements, prerequisites, graduation, parking, programs, and student services; verify that each answer is clear, relevant, and linked to supporting official PNW sources.

**Acceptance Scenarios**:

1. **Given** the chatbot has access to relevant official PNW sources, **When** a student asks about a policy, deadline, procedure, course requirement, prerequisite, parking matter, program, or student service, **Then** it provides a concise answer and links to the official source or sources used.
2. **Given** a question requires information from related pages or documents, **When** the student asks the question, **Then** the chatbot combines the relevant information into one understandable response rather than returning only a search-results page.
3. **Given** the available PNW sources do not support a confident answer, **When** the student asks the question, **Then** the chatbot says it cannot confirm the answer and provides an appropriate official source or contact.

### User Story 2 - Get campus-aware information (Priority: P1)

As a PNW student, I want answers to account for Hammond and Westville campus differences so that I am not given guidance for the wrong campus.

**Why this priority**: Campus-dependent information can make an otherwise accurate answer wrong for the student.

**Independent Test**: Ask campus-dependent questions with and without a campus specified; verify that the chatbot answers for the stated campus and requests a campus choice when one is required but missing.

**Acceptance Scenarios**:

1. **Given** a student identifies Hammond or Westville, **When** the question depends on campus, **Then** the chatbot uses the identified campus context in its answer.
2. **Given** a question depends on campus and no campus is provided, **When** the student asks the question, **Then** the chatbot asks whether the student attends Hammond or Westville before giving a campus-specific answer.
3. **Given** a question is not campus-dependent, **When** the student asks it, **Then** the chatbot does not ask for unnecessary campus information.

### User Story 3 - Know when human help is needed (Priority: P1)

As a PNW student, I want the chatbot to distinguish general information from personalized decisions so that I know when to contact an advisor, department, or university office.

**Why this priority**: Incorrect or overconfident guidance about academic requirements, registration, deadlines, or graduation could negatively affect students.

**Independent Test**: Ask questions requiring a personal record, an official decision, an action, or information absent from the corpus; verify that the chatbot does not make the decision or claim certainty and instead gives an appropriate escalation path.

**Acceptance Scenarios**:

1. **Given** a student asks the chatbot to register for a course, change a schedule, submit a form, or make an academic decision, **When** the request is received, **Then** the chatbot explains that it cannot perform the action or make the decision and directs the student to the relevant official process or office.
2. **Given** a question requires personalized records or advice, **When** the student asks it, **Then** the chatbot states that general information cannot confirm the student's situation and directs the student to an advisor, department, or university office.
3. **Given** the chatbot lacks sufficient supporting information, **When** it responds, **Then** it does not invent, guess, or present unsupported information as fact.

### User Story 4 - Receive answers from varied official source formats (Priority: P2)

As a student, I want information from PNW PDFs, webpages, linked child pages, documents, and structured tables to be represented accurately so that important details are not lost during retrieval.

**Why this priority**: The reviewed corpus contains policies in PDFs, linked HTML content, complex academic schedule tables, and fragmented catalog content.

**Independent Test**: Test representative handbook and policy sections, parking child pages, academic schedule rows, and catalog prerequisite and campus information; verify that the answer preserves the source relationships and relevant qualifiers.

**Acceptance Scenarios**:

1. **Given** a relevant parking answer is on a linked child page or document, **When** a student asks about parking, **Then** the chatbot can cite the relevant linked source rather than relying only on the top-level parking page.
2. **Given** a deadline is represented in a schedule table with terms, dates, add/drop information, or refund percentages, **When** a student asks about it, **Then** the answer keeps the date associated with the correct term and event.
3. **Given** course information is distributed across catalog sections, expandable content, pop-ups, or campus-specific details, **When** a student asks about a course, **Then** the answer combines the relevant requirement, prerequisite, offering, and campus qualifiers when available.

### Edge Cases

- If a student asks about a campus-dependent topic without identifying Hammond or Westville, ask for the campus rather than assuming one.
- If sources conflict, are outdated, or do not identify the applicable term or campus, state that the answer cannot be confirmed and direct the student to the responsible official office.
- If a source is inaccessible, incomplete, or contains information behind an element that cannot be reliably read, do not infer the missing content.
- If a question combines general information with a personalized request, answer only the supported general portion and identify the part requiring human assistance.
- If a student asks for an action outside the chatbot's scope, provide the official process or contact instead of simulating completion.
- If no relevant official PNW source is available, clearly state that limitation and provide the closest appropriate official contact or source when known.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The chatbot MUST accept natural-language questions about PNW policies, procedures, deadlines, registration, academic standing, grade appeals, financial aid deadlines, course requirements, prerequisites, graduation procedures, parking, programs, and student services.
- **FR-002**: The chatbot MUST answer using information supported by the available official PNW knowledge sources and MUST NOT invent, guess, or silently fill gaps in policy, deadline, academic, course, or procedural information.
- **FR-003**: The chatbot MUST provide clear, direct answers rather than only returning search links.
- **FR-004**: Each substantive answer MUST provide links to the official PNW source or sources supporting the answer when such links are available.
- **FR-005**: The chatbot MUST identify when a question depends on campus and MUST ask the student to choose Hammond or Westville when campus information is required but missing.
- **FR-006**: The chatbot MUST use the student's stated campus when responding to campus-dependent questions.
- **FR-007**: The chatbot MUST preserve the association between academic schedule terms, events, dates, add/drop periods, and refund percentages when using schedule information.
- **FR-008**: The chatbot MUST follow relevant linked parking pages and documents and use linked official content when that content contains the answer.
- **FR-009**: The chatbot MUST combine related catalog information, including course requirements, prerequisites, offerings, and campus-specific details, when the available sources support those details.
- **FR-010**: The chatbot MUST identify when available information is insufficient, ambiguous, conflicting, inaccessible, or not applicable to the student's context, and MUST communicate that limitation.
- **FR-011**: When it cannot confidently answer, the chatbot MUST direct the student to an appropriate official PNW source, advisor, department, or university office when that destination is available.
- **FR-012**: The chatbot MUST provide general university information and MUST NOT register students for courses, change schedules, submit forms, or make academic decisions.
- **FR-013**: For requests requiring a student's personal record, individualized academic judgment, or official approval, the chatbot MUST direct the student to the appropriate advisor, department, or university office.
- **FR-014**: The chatbot MUST support knowledge sources in both PDF and HTML formats, including documents with headings, definitions, numbered sections, linked pages, and structured tables.
- **FR-015**: The chatbot MUST make the source and relevant qualifiers understandable to a student, including applicable campus, term, date, or procedural context when available.
- **FR-016**: The system MUST support updating or replacing official source content so that answers can reflect changes to PNW policies, deadlines, procedures, and course information.
- **FR-017**: The chatbot MUST show available source dates or freshness information and MUST flag or decline to confirm information when a source date is unavailable or indicates that the information may be stale.

### Non-Functional Requirements

- **NFR-001**: Accuracy MUST be prioritized over completeness; when confidence is insufficient, the chatbot MUST decline to confirm rather than provide an unsupported answer.
- **NFR-002**: Responses MUST be understandable to students without requiring them to interpret source navigation or specialized retrieval terminology.
- **NFR-003**: Source links MUST identify official PNW destinations and be usable by students to verify or continue the process.
- **NFR-004**: The chatbot MUST preserve enough source context to support review of answers involving policies, deadlines, requirements, prerequisites, registration, or graduation.
- **NFR-005**: The system MUST handle the reviewed PDF and HTML source structures without mixing unrelated table cells, sections, terms, campuses, or linked documents.
- **NFR-006**: Response-time, availability, accessibility, privacy, and usage-volume targets are deferred to a later requirements review and MUST be defined before implementation planning is complete.

### Constraints

- The initial knowledge corpus is limited to official PNW sources, including the Student Handbook, Classroom Behavior Policy, Information Services Policies, parking regulations, academic catalog, and academic schedule, plus their relevant linked pages and documents.
- The chatbot is informational and does not execute student transactions or make decisions on behalf of students.
- Hammond and Westville are the supported campus contexts identified for this specification.
- Answers about policies, deadlines, academic requirements, prerequisites, registration, or graduation must remain traceable to official PNW information.
- The feature must account for content represented in PDFs, HTML pages, linked documents, complex tables, expandable sections, pop-ups, buttons, images, and text boxes where those elements contain relevant information.

### Key Entities

- **Student Question**: A natural-language request, including any stated topic, campus, term, course, or personal-context clues.
- **Chatbot Answer**: A clear response that distinguishes supported information, limitations, applicable qualifiers, source links, and escalation guidance.
- **Official PNW Source**: A PNW webpage, PDF, linked document, catalog entry, policy, regulation, schedule, or designated university contact used to support an answer.
- **Campus**: The PNW location context, currently Hammond or Westville, which may affect availability, procedures, or course information.
- **Academic Schedule Entry**: A term-specific schedule item connecting an event, date, add/drop period, or refund percentage.
- **Course Information**: Related catalog details such as course requirements, prerequisites, offerings, and campus applicability.
- **Escalation Destination**: An advisor, department, university office, or official source that can resolve a question the chatbot cannot confidently answer.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In evaluation using representative questions across the supported topic areas, at least 95% of answers that claim a policy, deadline, requirement, prerequisite, registration, or graduation fact cite an official PNW source containing the supporting information.
- **SC-002**: In evaluation using campus-dependent questions, 100% of cases without a required campus context ask the student to choose Hammond or Westville before giving a campus-specific answer.
- **SC-003**: In evaluation using unsupported, conflicting, incomplete, or personalized questions, 100% of responses avoid unsupported claims and provide a limitation plus an appropriate official escalation destination when one is available.
- **SC-004**: At least 90% of student evaluators can identify the answer, supporting source, and next step from a response without navigating more than one additional official source page.
- **SC-005**: At least 80% of representative information-seeking tasks covering the interview topics are completed without the student needing to search multiple unrelated PNW pages independently.
- **SC-006**: Evaluation of academic schedule questions preserves the correct relationship between term, event, date, add/drop information, and refund percentage in at least 98% of tested cases.
- **SC-007**: Evaluation of catalog questions preserves applicable prerequisite, offering, and campus qualifiers in at least 95% of tested cases where those details exist in the source corpus.
- **SC-008**: Student evaluation shows that at least 85% of participants rate the chatbot's answers as clear enough to act on or escalate appropriately.

## Assumptions

- Students use the chatbot primarily for general university information and can open official source links.
- Official PNW source links and contact destinations are available to the knowledge corpus or can be identified during corpus preparation.
- The initial release does not require the chatbot to authenticate students or access individual student records.
- Students may provide general context, such as campus or term, but the initial release does not use authenticated student records for personalized answers.
- The initial release supports Hammond and Westville; other campus contexts are outside this specification unless added later.
- The measures in the success criteria will be evaluated using a maintained set of representative questions derived from the interview topics and reviewed corpus.
- Response language is English unless a later requirement adds language support.
- Personalized advising, official approvals, and transaction completion remain the responsibility of PNW staff and existing university processes.
- Operational response-time, availability, accessibility, privacy, and usage-volume targets remain deferred until a later requirements review; source freshness is represented through available source dates and stale-information handling.
