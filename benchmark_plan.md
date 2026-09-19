# XHS Coding Agent Evaluation Benchmark — Baseline Plan

## 1. Business Scenario: Creator Campaign Collaboration Platform (创作者品牌合作平台)

### Overview

A platform feature within Xiaohongshu that connects **brands** with **content creators** for sponsored content collaborations. Brands publish campaign briefs, creators apply and produce content, the platform manages the workflow from discovery to settlement.

This scenario is chosen because it:
- Reflects XHS's core business (content + commerce)
- Involves multiple user roles (brand, creator, platform operator, end user)
- Requires complex technical patterns (async workflows, payment, search/ranking, content moderation, analytics)
- Maps naturally to 5 distinct user journeys

### System Context

The platform operates as a microservice within XHS's existing ecosystem:
- **User Service** (existing): user profiles, authentication, follower data
- **Content Service** (existing): note/post CRUD, media storage
- **Campaign Service** (new — this is what we're building): campaign management, matching, workflow
- **Payment Service** (existing): wallet, transactions, settlement
- **Notification Service** (existing): push notifications, in-app messages
- **Analytics Service** (existing): metrics collection, report generation

Tech stack: Python (FastAPI), PostgreSQL, Redis, Celery, Elasticsearch

---

### 5 User Journeys

#### Journey 1: Brand Campaign Creation (品牌发布合作活动)

**Actor:** Brand marketing manager

**Flow:**
1. Brand creates a campaign with brief: title, description, content requirements (note type, word count, image count), target audience tags, budget (total + per-creator fee range), timeline (application deadline, content deadline, publish deadline)
2. Brand sets creator eligibility criteria: min follower count, min engagement rate, required content categories, region restrictions
3. System validates campaign (budget >= min per-creator × min creators), estimates potential reach
4. Campaign enters platform review queue → approved → published to creator marketplace
5. Brand can edit campaign (before any applications), pause, or cancel

**Key complexity:** Budget validation rules, campaign state machine (draft → pending_review → active → paused → completed → cancelled), partial editing constraints

#### Journey 2: Creator Discovery & Application (创作者发现与申请)

**Actor:** Content creator

**Flow:**
1. Creator browses campaign marketplace with filters: category, budget range, deadline, brand
2. System ranks campaigns by relevance (creator's content category match, historical performance, engagement rate fit)
3. Creator views campaign detail, sees eligibility check result (eligible / ineligible with reason)
4. Creator submits application with: proposed content outline, estimated delivery date, requested fee (within campaign's range)
5. Brand receives applications, system auto-ranks by "fit score" (creator metrics vs. campaign criteria)
6. Brand accepts/rejects applications. Accepted creators get notified and campaign budget is reserved

**Key complexity:** Eligibility engine with multiple rules, ranking algorithm, concurrent application handling (budget exhaustion race condition), application state machine

#### Journey 3: Content Submission & Revision (内容提交与修改)

**Actor:** Content creator (accepted)

**Flow:**
1. Creator submits content draft: title, body text, image URLs, video URL (optional), hashtags
2. System runs automated checks: text length within campaign requirements, image count within range, sensitive word detection, image quality score (via external API stub)
3. If auto-check fails → rejected with reasons, creator can resubmit
4. If auto-check passes → enters brand review queue
5. Creator can view submission history with version tracking (v1, v2, v3...)

**Key complexity:** Multi-version tracking, automated content validation pipeline, file/media reference handling, deadline enforcement (reject if past content deadline)

#### Journey 4: Review & Approval Workflow (审核与确认流程)

**Actor:** Brand marketing manager + Platform compliance reviewer

**Flow:**
1. Brand reviews submitted content, can: approve, reject with comments, request revision with inline feedback
2. If revision requested → creator gets notification with feedback, submits new version (back to Journey 3)
3. If brand approves → content enters platform compliance review
4. Platform reviewer checks: no policy violations, brand safety, disclosure requirements met
5. If compliance passes → content is marked "ready to publish", creator gets publish instruction
6. If compliance fails → rejected with reason, loops back to creator

**Key complexity:** Two-level approval chain, revision loop (max 3 revisions), state transitions with audit trail, concurrent reviews (brand + compliance can't both be reviewing same content)

#### Journey 5: Settlement & Analytics (结算与数据分析)

**Actor:** Brand marketing manager + Content creator

**Flow:**
1. After content is published (creator confirms publish, provides post URL), system starts tracking performance
2. Performance tracking window: 7 days from publish date, collecting metrics (views, likes, comments, shares, clicks) via periodic sync
3. After tracking window closes, system calculates final payment: base_fee + performance_bonus (if metrics exceed thresholds defined in campaign)
4. Payment record created, enters settlement queue → processed in next settlement batch (weekly)
5. Brand can view campaign analytics dashboard: total reach, engagement rate, ROI, per-creator breakdown
6. Creator can view earnings detail: base fee, bonus breakdown, payment status

**Key complexity:** Async performance data collection, bonus calculation formula, settlement batch processing, idempotent payment creation, analytics aggregation

---

## 2. C1 — Requirements Understanding & Pre-review (需求理解与预评审)

### Task Definition

**Input:** A vague, incomplete business requirement description (simulating what a PM would write in a real ticket/PRD)

**Expected Output:** Structured requirements specification including:
- Functional requirements (organized by user story)
- Non-functional requirements (performance, security, scalability)
- Edge cases and boundary conditions
- Clarifying questions for ambiguous points
- Acceptance criteria
- Abnormal/exception scenario handling
- Requirement priority classification

### Evaluation Method: LLM-as-Judge

**Calibration guidance:** You are adopting the persona of a senior staff
engineer who has reviewed hundreds of PRDs and spec documents. Grade based on
the severity, frequency, and systemic nature of gaps. Avoid leniency bias
(being too generous or impressed by well-formatted but shallow specs) AND
paranoia (being overly punitive for isolated minor omissions in an otherwise
thorough spec). An isolated gap in an otherwise comprehensive spec should not
drop a dimension score by more than one tier.

### Evaluation Dimensions (5 dimensions, 100 points total)

### Hard Capping Rules (C1)

1. If the spec **misunderstands the core business intent** (e.g., treats a
   marketplace feature as a simple CRUD form), the overall score MUST be ≤ 40.
2. If the spec produces **zero clarifying questions** despite the input
   containing obvious ambiguities, Dimension 3 MUST be ≤ 8.
3. If the spec contains **no edge cases or exception handling at all**,
   Dimension 2 MUST be ≤ 5.
4. If the spec is a **wall of unstructured text** with no requirement
   numbering, user stories, or acceptance criteria, Dimension 4 MUST be ≤ 6.
5. **Systemic vs. isolated:** A single missed edge case in an otherwise
   thorough spec should score 20/25 on Dimension 2, not 10/25. Reserve ≤ 10
   for specs that show no systematic thinking about failure modes.

#### Dimension 1: Functional Completeness (功能完整性) — 25 points

Does the spec cover all necessary functional requirements derivable from the input?

| Score | Criteria |
|-------|----------|
| 25 | Identifies all explicit requirements AND proactively derives implicit requirements (e.g., "campaign creation" implies "campaign editing/deletion"). Covers all CRUD operations, state transitions, and user-facing feedback. No functional gaps. |
| 20 | Identifies all explicit requirements and most implicit ones. Minor gaps in secondary flows (e.g., missing cancel/undo operations). |
| 15 | Covers the main happy path but misses 2-3 important secondary flows or implicit requirements. |
| 10 | Only addresses the most obvious requirements. Misses multiple important flows. Feels like a surface-level reading of the input. |
| 5  | Fundamentally incomplete. Misses core functional requirements or misunderstands the business intent. |

#### Dimension 2: Edge Case & Exception Handling (边界与异常场景) — 25 points

Does the spec identify boundary conditions, error scenarios, and edge cases?

| Score | Criteria |
|-------|----------|
| 25 | Identifies 8+ valid edge cases including: concurrency issues (race conditions), boundary values (min/max), temporal edge cases (deadline expiry during action), data integrity issues (partial failures), and permission boundaries. Each edge case has a defined handling strategy. |
| 20 | Identifies 5-7 valid edge cases covering multiple categories (concurrency, boundary, temporal). Most have handling strategies. |
| 15 | Identifies 3-4 valid edge cases but concentrated in one category (e.g., only input validation). Some handling strategies missing. |
| 10 | Identifies 1-2 obvious edge cases (e.g., empty input). No systematic thinking about failure modes. |
| 5  | No meaningful edge cases identified, or identified "edge cases" are actually normal flows. |

#### Dimension 3: Ambiguity Identification & Clarification (歧义识别与澄清) — 20 points

Does the spec identify ambiguous/underspecified aspects and ask meaningful clarifying questions?

| Score | Criteria |
|-------|----------|
| 20 | Identifies 5+ genuine ambiguities in the input (e.g., "what happens if budget is exhausted mid-application?", "is fee negotiable or fixed?"). Questions are specific, non-obvious, and answering them would materially change the implementation. Clearly states assumptions when questions can't be answered. |
| 16 | Identifies 3-4 genuine ambiguities. Questions are specific and relevant. Assumptions are stated. |
| 12 | Identifies 1-2 ambiguities but questions are somewhat generic (e.g., "what is the expected user volume?"). Some assumptions unstated. |
| 8  | Asks questions but they're trivial or answerable from the input itself. Or makes significant unstated assumptions. |
| 4  | No ambiguities identified. Proceeds with silent assumptions, or asks irrelevant questions. |

#### Dimension 4: Structure & Specification Quality (结构与规范质量) — 15 points

Is the output well-organized, professional, and following industry-standard formats?

| Score | Criteria |
|-------|----------|
| 15 | Follows a clear spec structure (user stories / use cases with preconditions, postconditions, alternate flows). Uses consistent formatting. Includes priority/MoSCoW classification. Requirements are atomic, testable, and uniquely identifiable (numbered). |
| 12 | Good structure with clear sections. Requirements are mostly atomic and testable. Minor formatting inconsistencies. |
| 9  | Organized but informal. Requirements are described in paragraphs rather than structured formats. Some ambiguous requirements that aren't testable. |
| 6  | Poorly organized. Mixed concerns within sections. Hard to trace individual requirements. |
| 3  | Unstructured dump of text. No clear organization or requirement identification. |

#### Dimension 5: Non-functional & Feasibility Awareness (非功能性与可行性) — 15 points

Does the spec address non-functional requirements and technical feasibility concerns?

| Score | Criteria |
|-------|----------|
| 15 | Identifies relevant NFRs: performance expectations (response time, throughput), security requirements (authorization, data privacy), data consistency requirements, and scalability considerations. Flags potential technical risks or constraints. |
| 12 | Identifies 3-4 NFRs covering at least 2 categories (performance + security, or security + consistency). Some risk awareness. |
| 9  | Mentions NFRs but generically (e.g., "should be fast" without specific expectations). Limited risk identification. |
| 6  | Brief mention of 1 NFR category. No feasibility assessment. |
| 3  | No NFRs mentioned. No awareness of technical constraints. |

### LLM-as-Judge Prompt Template (C1)

```
You are a senior software architect evaluating the quality of a requirements
specification produced by an AI coding agent.

## Context
The agent was given this input (a vague business requirement):
<input>
{input_requirement}
</input>

The agent produced this requirements specification:
<output>
{agent_output}
</output>

## Reference Specification (Gold Standard)
For comparison, here is an expert-written specification for the same input:
<reference>
{gold_standard_spec}
</reference>

## Evaluation Task
Score the agent's output on each of the following 5 dimensions. For each
dimension, provide:
1. A score (using the exact point values from the rubric)
2. A brief justification (2-3 sentences) citing specific examples from
   the output

### Dimension 1: Functional Completeness (0-25 points)
[Rubric description...]

### Dimension 2: Edge Case & Exception Handling (0-25 points)
[Rubric description...]

### Dimension 3: Ambiguity Identification & Clarification (0-20 points)
[Rubric description...]

### Dimension 4: Structure & Specification Quality (0-15 points)
[Rubric description...]

### Dimension 5: Non-functional & Feasibility Awareness (0-15 points)
[Rubric description...]

## Output Format
Respond in JSON:
{
  "dimension_1": {"score": <int>, "justification": "<string>"},
  "dimension_2": {"score": <int>, "justification": "<string>"},
  "dimension_3": {"score": <int>, "justification": "<string>"},
  "dimension_4": {"score": <int>, "justification": "<string>"},
  "dimension_5": {"score": <int>, "justification": "<string>"},
  "total_score": <int>,
  "overall_assessment": "<1-2 sentence summary>"
}
```

---

## 3. C2 — Technical Design (技术方案设计)

### Task Definition

**Input:**
- Structured requirements specification (gold standard from C1)
- Existing system architecture context (description of existing services, tech stack, conventions)
- System constraints (performance SLAs, data privacy rules, deployment environment)

**Expected Output:** Technical design document including:
- Module decomposition & dependency graph
- API contract definitions (endpoints, request/response schemas)
- Database schema design (tables, relationships, indexes)
- Key technical decisions with justification
- Data flow for critical paths
- Integration points with existing services

### Evaluation Method: LLM-as-Judge

**Calibration guidance:** You are adopting the persona of a principal engineer
reviewing a technical design for a high-traffic production system. Grade based
on whether this design could actually be built, deployed, and maintained — not
on whether it reads well as a document. Avoid leniency bias (being impressed
by comprehensive diagrams while missing fundamental architectural flaws) AND
paranoia (penalizing reasonable simplifications in a first-iteration design).

### Hard Capping Rules (C2)

1. If the design **introduces circular dependencies** between modules, or
   creates a distributed monolith (excessive inter-service calls for simple
   operations), Architecture Soundness MUST be ≤ 10.
2. If the design **provides no API contracts** (just endpoint names without
   request/response schemas), API Design MUST be ≤ 8.
3. If the design **has no database schema** or only lists table names without
   fields/types/relationships, Data Model MUST be ≤ 8.
4. If the design **completely ignores the existing system context** (designs
   from scratch without acknowledging existing services), Constraint Adherence
   MUST be ≤ 8.
5. **Systemic vs. isolated:** A missing index on one table in an otherwise
   thoughtful schema is a 16/20, not an 8/20. Reserve low scores for designs
   that show no awareness of query patterns or data relationships.

### Evaluation Dimensions (5 dimensions, 100 points total)

#### Dimension 1: Architecture Soundness (架构合理性) — 25 points

Is the proposed architecture well-structured, maintainable, and appropriate for the requirements?

| Score | Criteria |
|-------|----------|
| 25 | Clean separation of concerns with clear module boundaries. Appropriate design patterns applied (not forced). Layer dependencies are unidirectional. Service boundaries align with business domains. Considers horizontal scalability. No circular dependencies. Consistent with existing system architecture style. |
| 20 | Good separation of concerns. Mostly appropriate patterns. Minor architectural smells (e.g., one module doing slightly too much). Compatible with existing architecture. |
| 15 | Reasonable structure but some design issues: 2-3 unclear module boundaries, or a pattern choice that doesn't fit well. Would require some rework for production. |
| 10 | Significant structural issues: tight coupling between modules, inappropriate patterns, or design that ignores the existing system architecture. |
| 5  | Fundamentally flawed: monolithic design for a microservice context, or fragmented into too many services with excessive inter-service calls. |

#### Dimension 2: API Design Quality (API 设计质量) — 20 points

Are the API contracts well-designed, complete, and following best practices?

| Score | Criteria |
|-------|----------|
| 20 | RESTful conventions followed consistently. All endpoints have clear request/response schemas with types. Proper HTTP methods and status codes. Pagination for list endpoints. Idempotency for mutations. Versioning strategy stated. Error response format standardized. Authentication/authorization specified per endpoint. |
| 16 | Good API design with minor gaps: missing pagination on a list endpoint, or inconsistent error format. Most endpoints well-defined. |
| 12 | APIs defined but with notable issues: missing response schemas for some endpoints, inconsistent naming conventions, or missing error handling specification. |
| 8  | Minimal API definition. Only endpoint paths listed without detailed schemas. Major design issues (e.g., using GET for mutations). |
| 4  | No meaningful API design, or APIs that contradict RESTful principles throughout. |

#### Dimension 3: Data Model Completeness (数据模型完整性) — 20 points

Is the database schema well-designed and complete for the requirements?

| Score | Criteria |
|-------|----------|
| 20 | All entities identified with complete field definitions (name, type, constraints). Relationships properly modeled (FK, junction tables for M:N). Appropriate indexes for query patterns identified in the requirements. Soft delete where appropriate. Audit fields (created_at, updated_at). Enum types for status fields. Migration strategy considered. |
| 16 | Good schema covering all main entities. Relationships correct. Minor gaps: missing an index, or incomplete field constraints. |
| 12 | Main entities present but some incomplete: missing fields, or relationships not properly modeled (e.g., M:N represented as 1:N). |
| 8  | Incomplete schema: missing 1-2 important entities, or fundamental relationship errors. |
| 4  | Minimal or incorrect schema that would not support the required functionality. |

#### Dimension 4: System Constraint Adherence (系统约束遵循) — 20 points

Does the design respect existing system constraints and integrate properly with existing services?

| Score | Criteria |
|-------|----------|
| 20 | All integration points with existing services clearly identified with interface contracts. Respects existing authentication/authorization patterns. Uses existing infrastructure (cache, queue, storage) appropriately. Backward compatibility considered. Data ownership boundaries clear. Failure handling at integration points specified (timeouts, retries, circuit breakers). |
| 16 | Integration points identified. Uses existing infrastructure. Minor gaps in failure handling or boundary specification. |
| 12 | Acknowledges existing services but integration details are vague. Some assumptions about existing service capabilities unverified. |
| 8  | Ignores some existing system constraints. Proposes redundant infrastructure that already exists. Integration approach unclear. |
| 4  | Designs in isolation, ignoring the existing system context entirely. |

#### Dimension 5: Trade-off Analysis & Risk Awareness (权衡分析与风险意识) — 15 points

Does the design discuss trade-offs, alternatives considered, and technical risks?

| Score | Criteria |
|-------|----------|
| 15 | Key technical decisions have explicit justification with alternatives considered (e.g., "chose PostgreSQL over MongoDB because of relational data patterns; MongoDB would offer easier schema evolution but we need transaction support for payment flows"). Performance implications discussed. At least 2 technical risks identified with mitigation strategies. |
| 12 | Some decisions justified with alternatives mentioned. 1-2 risks identified. Trade-off thinking is present but not thorough. |
| 9  | Decisions made without justification. One risk mentioned in passing. Little evidence of alternative evaluation. |
| 6  | No trade-off analysis. Design presented as the only option. No risk awareness. |
| 3  | Design choices contradict the stated constraints without acknowledgment. |

### LLM-as-Judge Prompt Template (C2)

```
You are a principal engineer evaluating the quality of a technical design
document produced by an AI coding agent.

## Context
The agent was given:
1. This requirements specification:
<requirements>
{requirements_spec}
</requirements>

2. This existing system architecture context:
<system_context>
{system_context}
</system_context>

The agent produced this technical design:
<output>
{agent_output}
</output>

## Reference Design (Gold Standard)
For comparison, here is an expert-written design for the same requirements:
<reference>
{gold_standard_design}
</reference>

## Evaluation Task
Score the agent's output on each of the following 5 dimensions.
For each dimension, provide:
1. A score (using the exact point values from the rubric)
2. A brief justification (2-3 sentences) citing specific examples

### Dimension 1: Architecture Soundness (0-25 points)
[Rubric description...]

### Dimension 2: API Design Quality (0-20 points)
[Rubric description...]

### Dimension 3: Data Model Completeness (0-20 points)
[Rubric description...]

### Dimension 4: System Constraint Adherence (0-20 points)
[Rubric description...]

### Dimension 5: Trade-off Analysis & Risk Awareness (0-15 points)
[Rubric description...]

## Output Format
Respond in JSON:
{
  "dimension_1": {"score": <int>, "justification": "<string>"},
  "dimension_2": {"score": <int>, "justification": "<string>"},
  "dimension_3": {"score": <int>, "justification": "<string>"},
  "dimension_4": {"score": <int>, "justification": "<string>"},
  "dimension_5": {"score": <int>, "justification": "<string>"},
  "total_score": <int>,
  "overall_assessment": "<1-2 sentence summary>"
}
```

---

## 4. C3 — Code Understanding & Generation (代码理解与生成)

### Task Definition

**Input (what the agent sees):**
- Technical specification (gold standard from C2)
- Existing mock repository (Python/FastAPI project with established conventions)
- Specific task instruction (implement feature X, or amend existing function Y)

**Expected Output:**
- Code changes as a git diff / patch

**Hidden from agent (used by evaluation harness only):**
- `test_patch` — new test file(s) that validate the feature (agent never sees these)
- `gold_patch` — reference implementation (for comparison, not for pass/fail)
- `FAIL_TO_PASS` — test names from `test_patch` that must pass after the agent's patch
- `PASS_TO_PASS` — existing 13 user tests that must still pass (regression)

### Evaluation Flow (SWE-bench aligned)

```
1. Harness checks out repo at base_commit
2. Agent receives: repo access + task prompt (problem_statement)
3. Agent explores repo, implements changes, submits patch (git diff)
4. Harness applies: agent's patch to the base repo
5. Harness applies: test_patch (new tests the agent never saw)
6. Harness runs FAIL_TO_PASS tests → must now PASS (feature works)
7. Harness runs PASS_TO_PASS tests → must still PASS (no regressions)
8. Harness runs static analysis (AST, linting, convention checks)
9. Score computed across all dimensions
```

### Dataset Entry Schema (per entry)

```json
{
  "instance_id": "C3-01",
  "category": "new_feature",
  "base_commit": "<sha of initial repo commit>",
  "problem_statement": "<task description + tech spec>",
  "gold_patch": "<reference implementation diff>",
  "test_patch": "<new test file diff, applied by harness>",
  "FAIL_TO_PASS": ["tests/api/test_campaigns.py::test_create_campaign_success", "..."],
  "PASS_TO_PASS": ["tests/api/test_users.py::test_create_user_success", "... all 13 user tests"],
  "hints_text": ""
}
```

### Mock Repository Design

A Python FastAPI project: `xhs-campaign-service`

**Pre-existing structure:**
```
xhs-campaign-service/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app initialization
│   ├── config.py                # Settings & configuration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py              # SQLAlchemy base, common mixins
│   │   └── user.py              # User model (existing, reference)
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── user.py              # Pydantic schemas (reference)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py              # Dependency injection (DB session, auth)
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── users.py         # User endpoints (reference)
│   ├── services/
│   │   ├── __init__.py
│   │   └── user_service.py      # User business logic (reference)
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── user_repo.py         # User data access (reference)
│   └── utils/
│       ├── __init__.py
│       ├── exceptions.py        # Custom exception classes
│       └── pagination.py        # Pagination helpers
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Fixtures (test DB, test client)
│   └── test_users.py            # User tests (reference)
├── alembic/                     # DB migrations
├── requirements.txt
├── pyproject.toml
└── .flake8                      # Linting config
```

The repo has established conventions visible from the existing code:
- Repository pattern for data access
- Service layer for business logic
- Pydantic schemas for request/response validation
- Consistent error handling via custom exceptions
- Test fixtures in conftest.py

### 8 Evaluation Entries

#### New Feature Entries (5, mapping to user journeys):

| Entry | Task | Maps to Journey |
|-------|------|-----------------|
| C3-01 | Implement Campaign CRUD (model, schema, API, service, repo) | Journey 1 |
| C3-02 | Implement Creator Application flow (apply, list, accept/reject) | Journey 2 |
| C3-03 | Implement Content Submission with auto-validation pipeline | Journey 3 |
| C3-04 | Implement two-level Review & Approval workflow | Journey 4 |
| C3-05 | Implement Settlement calculation and campaign analytics | Journey 5 |

#### Code Amendment Entries (3):

| Entry | Task | Description |
|-------|------|-------------|
| C3-06 | Add campaign search with Elasticsearch integration | Add full-text search + filter to existing campaign list endpoint |
| C3-07 | Enhance application ranking with weighted scoring | Modify existing application listing to support multi-factor ranking |
| C3-08 | Add rate limiting to content submission endpoint | Add Redis-based rate limiting middleware to prevent spam submissions |

### Evaluation Criteria (7 dimensions, 100 points total)

**Calibration guidance for evaluators/judges:** Grade based on the severity,
frequency, and systemic nature of issues. Avoid leniency bias (being too
generous or easily impressed by boilerplate scaffolding) AND paranoia (being
overly punitive for isolated minor issues). An isolated infraction in an
otherwise strong codebase should not drop a dimension score by more than one
tier — reserve the lowest scores for widespread, systemic anti-patterns.

#### Dimension 1: Functional Correctness — FAIL_TO_PASS (新功能正确性) — 50 points

**Method:** Automated test execution — new feature tests the agent never saw

| Score | Criteria |
|-------|----------|
| 50 | 100% of FAIL_TO_PASS tests pass. All new feature tests green. |
| 40 | 80-99% of FAIL_TO_PASS tests pass. Core feature works, minor edge cases missed. |
| 30 | 60-79% of FAIL_TO_PASS tests pass. Main flow works but significant gaps. |
| 20 | 30-59% of FAIL_TO_PASS tests pass. Partial implementation. |
| 0  | < 30% of FAIL_TO_PASS tests pass, or code doesn't parse. |

#### Dimension 2: Regression Safety — PASS_TO_PASS (回归安全性) — 20 points

**Method:** Automated test execution — existing 13 user tests must still pass

| Score | Criteria |
|-------|----------|
| 20 | 100% of PASS_TO_PASS tests still pass. Zero regressions. |
| 14 | 90-99% of PASS_TO_PASS tests pass. 1-2 minor regressions. |
| 6  | 70-89% of PASS_TO_PASS tests pass. Several regressions. |
| 0  | < 70% of PASS_TO_PASS tests pass. Agent broke existing functionality. |

#### Dimension 3: Readability (可读性) — 7 points

**Method:** LLM-as-judge

| Score | Criteria |
|-------|----------|
| 7  | Intent-revealing naming that reads like natural language. Consistent formatting matching the existing codebase. Docstrings on all public interfaces. Complex logic has inline explanatory comments. |
| 5  | Highly readable, consistent formatting, clear naming. Minor gaps in documentation of non-obvious logic. |
| 4  | Mostly readable, but some cryptic names (`temp`, `data1`, `v`), or complex algorithms/regex lack inline comments. |
| 2  | Inconsistent naming/casing, large undocumented blocks, confusing layout. |
| 1  | Completely cryptic naming throughout, no comments, messy indentation. |

**Hard cap:** If the agent uses single-letter variable names in business logic (not loop counters), readability MUST be ≤ 4.

#### Dimension 4: Maintainability (可维护性) — 7 points

**Method:** Automated (AST complexity analysis) + LLM-as-judge

| Score | Criteria |
|-------|----------|
| 7  | Flawless separation of concerns. Single-responsibility functions (mostly < 20 lines). Clean dependency injection. Loose coupling. Zero copy-pasted logic (DRY compliance). |
| 5  | Strong modularity, clear layer boundaries, short functions (mostly < 30 lines), mockable dependencies. |
| 4  | Standard structure but some implementation details leak across layers; a few functions are monolithic or contain duplicate logic blocks. |
| 2  | Monolithic functions (> 80 lines), high cyclomatic complexity (> 15), deep nesting (4+), or systemic copy-pasted code across modules. |
| 1  | Extreme debt: gigantic functions (> 150 lines), God Classes, global mutable state, tight coupling. |

**Hard caps:**
- If any single new file exceeds 500 lines, maintainability MUST be ≤ 4.
- If a single function exceeds 100 lines, maintainability MUST be ≤ 2.
- If business logic is placed directly in API route handlers (bypassing service layer), maintainability MUST be ≤ 4.

#### Dimension 5: Robustness (健壮性) — 7 points

**Method:** Automated (pattern detection) + LLM-as-judge

| Score | Criteria |
|-------|----------|
| 7  | Defensive programming throughout. Specific exceptions handled and propagated (not bare `except:`). Safe resource management (context managers, async cleanup). No magic constants. Input validation at boundaries. Concurrent safety where applicable. |
| 5  | Strong defensive coding. Specific exceptions handled. Clean resource lifetimes. Minor magic constants (< 2). |
| 4  | Errors handled but generic catch-all blocks common. Some magic constants. Missing validation on 1-2 edge cases. |
| 2  | Silent error swallowing (logging but not propagating). Manual resource management with leak risks. Bare `except: pass` in business logic. |
| 1  | Silently swallowed exceptions in critical paths (payment, data mutation). No input validation. Hardcoded credentials or secrets. |

**Hard caps:**
- If the agent uses bare `except:` or `except Exception: pass` in business logic, robustness MUST be ≤ 4.
- If errors in payment/settlement/data-mutation paths are silently swallowed, robustness MUST be ≤ 2.
- If hardcoded secrets/credentials are introduced, robustness MUST be ≤ 1.

#### Dimension 6: Convention Adherence (规范遵循) — 5 points

**Method:** Automated pattern matching + LLM-as-judge

| Score | Criteria |
|-------|----------|
| 5  | Follows all established repo patterns: repository pattern for data access, service layer for logic, Pydantic schemas for validation, consistent naming (snake_case), proper file placement, imports organized per existing style. New code is indistinguishable from existing code in style. |
| 4  | Follows most patterns. 1-2 minor deviations (e.g., slightly different import style). |
| 3  | Follows general structure but with notable deviations: putting business logic in API layer, or skipping the repository pattern. |
| 2  | Partially follows conventions. Mix of patterns used inconsistently. |
| 1  | Ignores repo conventions entirely. Code works but doesn't fit the codebase. |

**Hard cap:** If the agent skips the repository pattern entirely (direct DB queries in service or API layer), convention MUST be ≤ 3.

#### Dimension 7: Change Minimality (变更最小化) — 4 points

**Method:** Automated diff analysis

| Score | Criteria |
|-------|----------|
| 4  | Changes are minimal and focused. Only touches files necessary for the task. No unnecessary refactoring, no unrelated changes, no dead code introduced. |
| 3  | Mostly minimal. 1-2 minor unnecessary changes (e.g., reformatting an unrelated line). |
| 2  | Some unnecessary changes: touching files that didn't need modification, or adding unused imports/utilities. |
| 1  | Significant unnecessary changes: refactoring unrelated code, adding helper functions never called. |
| 0  | Massive unnecessary changes that obscure the actual feature implementation. |

### Overall Score Synthesis (C3)

The C3 overall score is **NOT a simple sum** of dimension scores. It is synthesized
following these rules:

1. **Functional correctness is the gatekeeper:** If D1 (FAIL_TO_PASS) scores 0,
   the overall score is capped at 20 regardless of other dimensions — code that
   doesn't work cannot score well.
2. **Regressions are disqualifying:** If D2 (PASS_TO_PASS) scores 0 (broke
   existing functionality), overall is capped at 30.
3. **Otherwise:** Overall = sum of all 7 dimension scores (max 100), with the
   understanding that D1+D2 (functional) anchor the score while D3-D7 (quality)
   differentiate within the functional tier.

### Agent Prompt Template (C3)

```
<uploaded_files>
/repo
</uploaded_files>

I've uploaded a Python code repository in /repo. This is a FastAPI-based
microservice for a campaign collaboration platform.

## Task
{task_description}

## Technical Specification
<tech_spec>
{technical_spec_from_c2}
</tech_spec>

## Instructions
1. Explore the existing codebase to understand the project structure,
   conventions, and patterns used
2. Implement the required changes following the existing codebase conventions
3. Ensure your implementation matches the technical specification
4. Run existing tests to make sure nothing is broken
5. Your changes should be minimal — only modify what's necessary

Do NOT modify any existing test files. New test files will be added
separately to verify your implementation.
```

---

## 5. C4 — Code Review (代码评审)

### Task Definition

**Input:**
- Git diff (PR) from C3 — with intentionally planted defects
- Repository context (full repo access for cross-file analysis)
- PR description (what the change is supposed to do)

**Expected Output:** List of review findings, each with:
- File path and line range
- Issue category (Defect / Security / Performance / Maintainability)
- Severity (Critical / Major / Minor / Suggestion)
- Description of the issue
- Suggested fix

### Planted Defect Design

Each of the 8 PRs from C3 will have a "bugged variant" with 2-3 intentionally planted defects.

| PR | Planted Defects |
|----|----------------|
| C3-01 Campaign CRUD | (1) Missing authorization check on delete endpoint [Security/Critical]. (2) Campaign status allows invalid transition draft→completed [Defect/Major]. (3) No pagination on list endpoint returns unbounded results [Performance/Major]. |
| C3-02 Application Flow | (1) Race condition: budget check and reservation not atomic [Defect/Critical]. (2) SQL injection via unsanitized filter parameter [Security/Critical]. (3) Missing index on `campaign_id` foreign key [Performance/Minor]. |
| C3-03 Content Submission | (1) Deadline check uses server local time instead of UTC [Defect/Major]. (2) File path traversal in image URL validation [Security/Critical]. (3) Synchronous call to external image quality API blocks event loop [Performance/Major]. |
| C3-04 Review Workflow | (1) Concurrent approval: brand and compliance can both approve simultaneously creating duplicate records [Defect/Major]. (2) Revision count not enforced (exceeds max 3) [Defect/Minor]. (3) Audit log missing for status transitions [Maintainability/Major]. |
| C3-05 Settlement | (1) Floating-point arithmetic for payment calculation instead of Decimal [Defect/Critical]. (2) Settlement job not idempotent — duplicate payments on retry [Defect/Critical]. (3) Creator payment data exposed in brand analytics endpoint [Security/Major]. |
| C3-06 Search | (1) Elasticsearch query allows wildcard injection in user input [Security/Major]. (2) Missing error handling when ES cluster is unavailable [Defect/Major]. |
| C3-07 Ranking | (1) Division by zero when creator has zero followers [Defect/Critical]. (2) Hardcoded ranking weights should be configurable [Maintainability/Minor]. |
| C3-08 Rate Limiting | (1) Rate limit key doesn't include endpoint path — all endpoints share one counter [Defect/Major]. (2) Redis connection failure crashes the request instead of graceful degradation [Defect/Major]. |

**Total: 21 planted defects** across 8 PRs

### Evaluation Criteria (5 dimensions, 100 points total)

#### Dimension 1: Detection Recall (缺陷召回率) — 25 points

**Method:** Automated matching against planted defect list

| Score | Criteria |
|-------|----------|
| 25 | Detects 90-100% of planted defects (19-21 / 21). |
| 20 | Detects 70-89% of planted defects (15-18 / 21). |
| 15 | Detects 50-69% of planted defects (11-14 / 21). |
| 10 | Detects 30-49% of planted defects (7-10 / 21). |
| 5  | Detects < 30% of planted defects (< 7 / 21). |

#### Dimension 2: Detection Precision (检测精确率) — 25 points

**Method:** Automated + LLM-as-judge for non-planted findings

| Score | Criteria |
|-------|----------|
| 25 | Precision >= 80%. Very few false positives. Every reported issue is a genuine concern. |
| 20 | Precision 60-79%. Some false positives but mostly accurate. |
| 15 | Precision 40-59%. Roughly equal true and false positives. Signal-to-noise ratio is marginal. |
| 10 | Precision 20-39%. Many false positives. Reviewer would spend more time dismissing noise than reading real issues. |
| 5  | Precision < 20%. Almost all findings are noise (nitpicks, style preferences, non-issues). |

#### Dimension 3: Localization Accuracy (定位准确性) — 20 points

**Method:** Automated line range matching (tolerance: ±3 lines)

| Score | Criteria |
|-------|----------|
| 20 | 90%+ of true-positive findings point to the correct file AND correct line range (within ±3 lines). |
| 16 | 70-89% correct localization. |
| 12 | 50-69% correct localization. Some findings point to the right file but wrong location. |
| 8  | 30-49% correct localization. Findings are vaguely associated with the right area. |
| 4  | < 30% correct localization. Findings can't be mapped to specific code locations. |

#### Dimension 4: Category & Severity Accuracy (分类与严重性准确率) — 15 points

**Method:** Automated matching against planted defect metadata

| Score | Criteria |
|-------|----------|
| 15 | 80%+ of true-positive findings have correct category (Defect/Security/Performance/Maintainability) AND severity within one level of ground truth. |
| 12 | 60-79% correct classification. |
| 9  | 40-59% correct classification. Frequent miscategorization (e.g., security issue labeled as maintainability). |
| 6  | 20-39% correct classification. |
| 3  | < 20% correct classification, or no category/severity provided. |

#### Dimension 5: Explanation & Fix Quality (解释与修复建议质量) — 15 points

**Method:** LLM-as-judge

| Score | Criteria |
|-------|----------|
| 15 | For true-positive findings: root cause is clearly explained (not just "this looks wrong"), the suggested fix is correct and actionable (a developer could implement it directly), and the explanation demonstrates understanding of why it's a problem (e.g., explains the attack vector for security issues, the race condition sequence for concurrency bugs). |
| 12 | Root cause mostly clear. Fix suggestion is correct but may need refinement. Good but not complete explanation of impact. |
| 9  | Issue identified but explanation is shallow ("this might cause problems"). Fix suggestion is vague ("add validation"). |
| 6  | Issue described but root cause not identified. Fix suggestion is incorrect or missing. |
| 3  | Finding is just a label with no explanation (e.g., "security issue" with no detail). |

### Matching Logic (AACR-Bench inspired)

```
For each generated finding:
  Step 1: Path match     → file path must match a planted defect's file
  Step 2: Line proximity → line range overlaps or within ±5 lines of planted defect
  Step 3: Semantic match → LLM-as-judge determines if the finding addresses
                           the same concern as the planted defect
  → If all 3 pass: TRUE POSITIVE (matched to specific planted defect)
  → If Step 1-2 pass but Step 3 fails: check if it's a VALID NON-PLANTED
    finding (LLM-as-judge decides if it's a real issue not in our planted list)
  → Otherwise: FALSE POSITIVE
```

### LLM-as-Judge Prompt Template (C4 — Semantic Matching)

```
You are an expert code reviewer. Determine whether two code review comments
address the same underlying issue.

## Planted Defect (Ground Truth)
File: {planted_file}
Lines: {planted_lines}
Category: {planted_category}
Description: {planted_description}

## Agent's Finding
File: {agent_file}
Lines: {agent_lines}
Category: {agent_category}
Description: {agent_description}

## Task
Do these two findings describe the same underlying code issue?
Ignore differences in wording, severity assessment, or suggested fix.
Focus on whether they identify the same root cause in the same code location.

Respond in JSON:
{
  "is_same_issue": true/false,
  "confidence": "high" | "medium" | "low",
  "reasoning": "<1-2 sentences>"
}
```

---

## 6. C5 — Testing & Debug (测试和 Debug)

### C5a: Test Generation (5 entries)

#### Task Definition

**Input:**
- Implemented code from C3 (gold standard, correct implementation)
- Module specification (what the code is supposed to do)
- Existing test patterns in the repo (conftest.py fixtures, test style)

**Expected Output:**
- Unit tests and/or integration tests for the implemented module
- Tests should follow existing patterns in the repo

#### Evaluation Criteria (5 dimensions, 100 points total)

##### Dimension 1: Coverage (测试覆盖率) — 50 points

**Method:** Automated (pytest pass rate)

| Score | Criteria |
|-------|----------|
| 50 | 100% pass rate AND test count >= gold_test_count. All agent-written tests pass and the suite is comprehensive. |
| 40 | 100% pass rate but test count < gold_test_count. All tests pass but coverage is incomplete. |
| 30 | Pass rate >= 80%. Most tests pass, a few failures. |
| 20 | Pass rate 50-79%. Significant test failures. |
| 10 | Pass rate < 50%, OR fewer than 5 tests written. |

##### Dimension 2: Assertion Quality (断言质量) — 18 points

**Method:** AST analysis + LLM-as-judge

| Score | Criteria |
|-------|----------|
| 18 | Every test has specific, meaningful assertions (exact value checks, not just "no exception"). Asserts cover return values, state changes, side effects, AND error conditions. Uses appropriate assertion methods. |
| 14 | Good assertions covering return values and error conditions. Minor gaps in side-effect verification. |
| 10 | Assertions present but some are weak (e.g., `assert result is not None` instead of checking the actual value). Error conditions partially tested. |
| 7  | Many tests just check "no exception raised". Few meaningful value assertions. |
| 3  | Trivial assertions only (e.g., `assert True`, `assert response.status_code == 200` without body checks). |

##### Dimension 3: Edge Case Coverage (边界场景覆盖) — 14 points

**Method:** LLM-as-judge against gold-standard edge case list

| Score | Criteria |
|-------|----------|
| 14 | Tests cover: empty inputs, boundary values (min/max), error conditions (invalid input, resource not found, permission denied), concurrent operations (if applicable), and at least 2 non-obvious edge cases specific to the business logic. |
| 11 | Tests cover most common edge cases (empty input, not found, permission). 1 non-obvious case. |
| 8  | Some edge cases covered but gaps in error conditions or boundary values. |
| 5  | Only happy path + 1-2 obvious error cases (e.g., 404). |
| 3  | Happy path only. No edge cases. |

##### Dimension 4: Test Independence & Structure (测试独立性与结构) — 11 points

**Method:** Automated (pytest execution analysis) + AST analysis

| Score | Criteria |
|-------|----------|
| 11 | All tests pass when run individually and in any order. Proper setup/teardown (fixtures, not shared mutable state). Each test tests one thing (single assertion concern). Clear test names following `test_<action>_<condition>_<expected>` pattern. Tests use existing conftest.py fixtures. |
| 9  | Tests independent and structured. Minor issues (e.g., 1 test name unclear, or slightly redundant setup). |
| 6  | Mostly independent but some tests share mutable state or have order dependencies. Test names could be clearer. |
| 4  | Test isolation issues: shared state, order-dependent tests, or setup logic mixed into test functions. |
| 2  | Tests tightly coupled, can't run individually, or fragile (break when unrelated code changes). |

##### Dimension 5: Convention Adherence (规范遵循) — 7 points

**Method:** Automated (AST pattern matching)

| Score | Criteria |
|-------|----------|
| 7  | Follows existing test patterns in the repo: uses pytest (not unittest), uses fixtures from conftest.py, follows existing file naming (test_<module>.py), uses existing test client and DB fixtures, mock patterns consistent with existing tests. |
| 5  | Mostly follows conventions. 1 minor deviation. |
| 4  | Partially follows conventions. Uses pytest but doesn't leverage existing fixtures. |
| 2  | Uses different testing patterns (e.g., unittest.TestCase when repo uses pytest functions). |
| 1  | Completely different testing style. Ignores existing test infrastructure. |

---

### C5b: Debug (3 entries)

#### Task Definition

**Input:**
- Code with an intentionally planted bug
- Error stack trace or failing test output
- Bug report description (what was expected vs. what happened)

**Expected Output:**
- Diagnosis of root cause
- Code fix (minimal patch)
- Explanation of why the fix resolves the issue

#### 3 Debug Entries

| Entry | Bug Type | Scenario |
|-------|----------|----------|
| C5b-01 | Logic Error | Settlement bonus calculation uses `>` instead of `>=` for threshold comparison, causing creators who exactly meet the threshold to miss their bonus. Stack trace: test_settlement_bonus_at_threshold fails with `AssertionError: 0 != 500`. |
| C5b-02 | Concurrency Bug | Campaign application endpoint has a TOCTOU race condition — checks budget availability then reserves, but two concurrent requests can both pass the check. Bug manifests under load testing as `IntegrityError: budget_remaining below zero`. |
| C5b-03 | Integration Error | Content submission fails when image quality API returns a timeout. The async task crashes with `ConnectionTimeout` instead of gracefully handling the failure and marking quality check as "pending_retry". Stack trace provided. |

#### Evaluation Criteria (4 dimensions, 100 points total)

##### Dimension 1: Root Cause Identification (根因定位) — 20 points

**Method:** LLM-as-judge against ground-truth root cause

| Score | Criteria |
|-------|----------|
| 20 | Correctly identifies the exact root cause: the specific line(s) of code, the nature of the bug (off-by-one, race condition, missing error handling), and why it produces the observed symptom. |
| 16 | Identifies the correct area and type of bug but slightly imprecise about the exact mechanism (e.g., "there's a race condition in the application flow" without specifying the TOCTOU pattern). |
| 12 | Identifies the correct file/function but mischaracterizes the bug type, or identifies the symptom but not the underlying cause. |
| 8  | Partially correct: right area but wrong diagnosis. Would lead to a fix that might mask the bug but not truly resolve it. |
| 4  | Incorrect root cause identification. Points to the wrong code or wrong type of issue. |

##### Dimension 2: Fix Correctness (修复正确性) — 50 points

**Method:** Automated test execution (SWE-bench style)

| Score | Criteria |
|-------|----------|
| 50 | All FAIL_TO_PASS tests pass AND all PASS_TO_PASS tests pass. The fix resolves the reported issue completely. |
| 40 | FAIL_TO_PASS tests pass but 1 PASS_TO_PASS test regressed (fix has minor side effect). |
| 30 | Most FAIL_TO_PASS tests pass (70%+). The core issue is resolved but edge cases may remain. |
| 20 | Partial fix: the immediate symptom is addressed but the underlying issue can still trigger under different conditions. |
| 10 | Fix doesn't resolve the issue. Tests still fail, or new failures introduced. |

##### Dimension 3: Fix Minimality (修复最小化) — 20 points

**Method:** Automated diff analysis

| Score | Criteria |
|-------|----------|
| 20 | Fix is surgical: changes only the lines necessary to resolve the bug. No refactoring, no unrelated changes, no "while I'm here" improvements. Diff is clean and focused. |
| 16 | Fix is focused but includes 1-2 minor unnecessary changes (e.g., formatting a nearby line). |
| 12 | Fix is correct but includes some unnecessary refactoring or defensive coding beyond what's needed. |
| 8  | Significant unnecessary changes that obscure the actual fix. |
| 4  | Major rewrite instead of targeted fix. |

##### Dimension 4: Explanation Quality (诊断解释质量) — 10 points

**Method:** LLM-as-judge

| Score | Criteria |
|-------|----------|
| 10 | Explanation clearly describes: (1) what the bug is, (2) why the current code produces the wrong behavior (step-by-step reasoning), (3) why the fix resolves it, and (4) whether similar patterns exist elsewhere that might need the same fix. Demonstrates deep understanding. |
| 8  | Clear explanation of the bug and fix. Missing either the step-by-step reasoning or the similar-pattern analysis. |
| 6  | Explains what was changed but not deeply why the original code was wrong. Surface-level understanding. |
| 4  | Minimal explanation. "Changed X to Y" without reasoning. |
| 2  | No explanation or incorrect explanation that contradicts the actual fix. |

---

## Appendix: Scoring Summary

### Per-Category Score Ranges

| Category | Max Score | Evaluation Method | Pass Threshold |
|----------|-----------|-------------------|----------------|
| C1 Requirements | 100 | LLM-as-Judge (5 dimensions) | 60 |
| C2 Tech Design | 100 | LLM-as-Judge (5 dimensions) | 60 |
| C3 Code Gen | 100 | Automated + LLM-as-Judge (7 dimensions: FAIL_TO_PASS + PASS_TO_PASS + readability + maintainability + robustness + convention + minimality) | 70 |
| C4 Code Review | 100 | Automated + LLM-as-Judge (5 dimensions) | 60 |
| C5a Testing | 100 | Automated + LLM-as-Judge (5 dimensions) | 60 |
| C5b Debug | 100 | Automated + LLM-as-Judge (4 dimensions) | 60 |

### Composite Score

```
Overall Score = (C1 + C2 + C3 + C4 + C5a + C5b) / 6

Equal-weight average across all 6 categories.
```

### Grade Mapping

| Grade | Score Range | Interpretation |
|-------|------------|----------------|
| S | 90-100 | Expert level — ready for production-critical tasks |
| A | 80-89 | Strong — reliable for most development tasks |
| B | 70-79 | Competent — usable with oversight |
| C | 60-69 | Marginal — significant gaps, needs human review |
| D | < 60 | Insufficient — not ready for the evaluated task type |
