# C2 Evaluation Guide: Technical Design

## Overview

C2 tests whether a coding agent can take a **structured requirements specification** (the output of C1) and produce a **production-ready technical design document**. It evaluates the agent's ability to think like a principal engineer — designing module boundaries, API contracts, data models, integration points, and making explicit trade-off decisions with justification.

C2 sits between C1 (requirements understanding) and C3 (code generation) in the evaluation pipeline. The input to C2 is much more specific than C1's vague business requirement — it includes user stories, state machines, and constraints. The expected output is not code, but a blueprint that could be handed to a developer for implementation.

---

## 1. Data File Structure

Each C2 entry is a JSON file in `dataset/c2/`. There are 5 entries, one per business journey.

```
dataset/c2/
├── C2-01_campaign_creation.json      # Journey 1: Brand Campaign Creation
├── C2-02_creator_application.json    # Journey 2: Creator Discovery & Application
├── C2-03_content_submission.json     # Journey 3: Content Submission & Revision
├── C2-04_review_workflow.json        # Journey 4: Review & Approval Workflow
└── C2-05_settlement_analytics.json   # Journey 5: Settlement & Analytics
```

### Top-Level Fields

| Field | Type | Purpose |
|-------|------|---------|
| `instance_id` | string | Unique identifier (e.g., `"C2-01"`) |
| `category` | string | Always `"C2"` |
| `category_name` | string | `"技术方案设计"` (Technical Design) |
| `maps_to_journey` | string | Which business journey this entry covers |
| `input` | object | **What the agent receives** — the requirements spec + system context + constraints |
| `gold_standard_output` | object | **Expert-written technical design** — calibration anchor for the judge |
| `evaluation_rubric` | string | Path to the rubric file (`evaluation/rubrics/c2_design.json`) |

### `input` Object

Unlike C1's vague PM request, C2's input is already a structured specification — detailed enough to design against.

| Sub-field | Type | Purpose |
|-----------|------|---------|
| `requirements_spec` | string | The structured requirements specification. Contains user stories (US-1.1...), state machines, edge cases, and key requirements. This is what a strong C1 output would look like. |
| `system_context` | string | Detailed existing system architecture: tech stack, frameworks, patterns, conventions, existing modules. The agent must design *within* this context, not in isolation. |
| `constraints` | string | Non-functional requirements: performance targets, security model, data integrity rules, auditability, currency, external service boundaries. |

**Example `input` (C2-01):**
```json
{
  "requirements_spec": "Enable brand users to create, manage, and publish campaign briefs to a creator marketplace. Core user stories: (US-1.1) Brand creates campaign with brief, budget, timeline, and creator eligibility criteria — saved as 'draft'. (US-1.2) Brand edits campaign with constraints — all fields editable in draft/pending_review, restricted edits in active... State machine: draft → pending_review → active → paused → completed → cancelled...",

  "system_context": "Existing FastAPI microservice 'xhs-campaign-service' (Python 3.11). Layered architecture: Model (SQLAlchemy 2.0 with Mapped[] annotations) → Repository (async, DB access only) → Service (business logic) → API (FastAPI routers under /api/v1/). PostgreSQL via asyncpg, Redis available, Celery for async tasks. Existing patterns from User module: UUID string PKs (generate_uuid()), TimestampMixin..., SoftDeleteMixin..., Pydantic v2 schemas..., custom exceptions..., auth via X-User-Id header → CurrentUser dependency...",

  "constraints": "Performance: campaign list p95 < 200ms for 10k campaigns. Security: ownership-based authorization — brands see only own campaigns; admin endpoints require admin role. Data integrity: atomic status transitions with optimistic locking. Auditability: log all status changes with actor, timestamp, from/to states..."
}
```

**Key difference from C1:** The agent is given an established architecture with specific patterns (layered arch, naming conventions, dependency wiring). A good C2 output must follow these patterns — not reinvent them.

### `gold_standard_output` Object

The expert-written design serves as a **calibration anchor** for the judge. It contains:

| Section | Content | Example |
|---------|---------|---------|
| `module_design` | `new_files` (path, responsibility, depends_on), `modified_files` (path, change), `dependency_graph` | 5 new files (model, schema, repo, service, router) + 2 modified files (__init__, router aggregator) |
| `api_design` | `base_path`, `endpoints[]` — each with method, path, description, auth, request_body, response, errors | 10 endpoints: CRUD + submit/approve/reject/pause/resume/cancel/delete |
| `data_model` | `tables[]` — each with columns (name, type, constraints), indexes, enums | 2 tables: `campaigns` (22 columns, 4 indexes, 1 enum) + `campaign_status_logs` (7 columns, 1 index) |
| `integration_points` | External/internal services, type (sync/async), interface contracts | User Service (direct repo call) + Notification Service (Celery fire-and-forget) |
| `technical_decisions` | Each with decision, justification, alternatives_considered (option + rejected_because), implementation | Optimistic locking, enum + audit table, Decimal for money |
| `data_flow` | Step-by-step for primary operations | create_campaign (8 steps), submit_for_review (detailed sub-steps), generic state transition |

**Example — a gold standard technical decision:**
```json
{
  "decision": "Use optimistic locking via integer version field",
  "justification": "Campaign edits are infrequent and conflicts are rare but possible. Optimistic locking avoids holding database locks during the user's edit session.",
  "alternatives_considered": [
    {
      "option": "Pessimistic locking (SELECT ... FOR UPDATE)",
      "rejected_because": "Holds row-level locks during the full edit-save cycle. In a web application this could be seconds to minutes — causes lock contention and deadlock risk."
    },
    {
      "option": "Last-write-wins (no locking)",
      "rejected_because": "Silent data loss when concurrent edits overwrite each other. Unacceptable for campaign budget and deadline fields."
    }
  ],
  "implementation": "Add 'version: int' column with default=1. On update, check version matches, increment, use WHERE version = :expected in UPDATE. If 0 rows updated, raise ConflictError."
}
```

This level of trade-off thinking is what distinguishes a senior design from a junior one.

---

## 2. Submission: How the Agent Prompt Is Built

The agent prompt is constructed by `build_prompt_c2()` in `evaluation/run_benchmark.py`:

```python
def build_prompt_c2(entry: dict) -> str:
    inp = entry["input"]
    return (
        f"You are a senior software architect designing a technical solution.\n\n"
        f"## Requirements Specification\n"
        f"{json.dumps(inp['requirements_spec'], indent=2, ensure_ascii=False)}\n\n"
        f"## System Context\n"
        f"{inp['system_context']}\n\n"
        f"## Constraints\n"
        f"{json.dumps(inp.get('constraints', {}), indent=2, ensure_ascii=False)}\n\n"
        f"## Task\n"
        f"Produce a technical design document that includes:\n"
        f"1. Module design (components, responsibilities, dependencies)\n"
        f"2. API design (endpoints with method, path, request/response schemas)\n"
        f"3. Data model (tables, fields, types, relationships, indexes)\n"
        f"4. Integration points with external services\n"
        f"5. Key technical decisions with rationale\n"
        f"6. Data flow for primary operations\n\n"
        f"Output as structured JSON."
    )
```

### Resulting Prompt (C2-01 example)

```
You are a senior software architect designing a technical solution.

## Requirements Specification
"Enable brand users to create, manage, and publish campaign briefs to a
creator marketplace. Core user stories: (US-1.1) Brand creates campaign
with brief, budget, timeline, and creator eligibility criteria — saved
as 'draft'. ..."

## System Context
Existing FastAPI microservice 'xhs-campaign-service' (Python 3.11).
Layered architecture: Model → Repository → Service → API. PostgreSQL
via asyncpg, Redis available, Celery for async tasks. Existing patterns
from User module: UUID string PKs, TimestampMixin, SoftDeleteMixin,
Pydantic v2 schemas, custom exceptions, auth via X-User-Id header...

## Constraints
"Performance: campaign list p95 < 200ms for 10k campaigns. Security:
ownership-based authorization. Data integrity: atomic status transitions
with optimistic locking. Auditability: log all status changes..."

## Task
Produce a technical design document that includes:
1. Module design (components, responsibilities, dependencies)
2. API design (endpoints with method, path, request/response schemas)
3. Data model (tables, fields, types, relationships, indexes)
4. Integration points with external services
5. Key technical decisions with rationale
6. Data flow for primary operations

Output as structured JSON.
```

### How It's Submitted

Identical to C1 — the prompt is piped to the agent CLI via stdin:

```bash
agy --input-format text \
    --model gemini-3.8-flash-high \
    --output-format stream-json \
    --dangerously-skip-permissions
```

Key points:
- **No tools, no repo access** — C2 is pure text-in, text-out (like C1)
- The agent designs from the spec and system context alone — no browsing existing code
- The agent's full response is saved to `results/outputs/C2-01_agy_gemini-3.8-flash-high.json`

### C1 vs C2 Execution Path

Both C1 and C2 use the same `run_c1_c2()` function in the harness. The only difference is which prompt builder is called:

```python
prompt = build_prompt_c1(entry) if category == "c1" else build_prompt_c2(entry)
```

The rest of the pipeline — agent invocation, output capture, judge scoring — is identical.

---

## 3. Evaluation: How the Judge Scores

### Step 1: Build the Judge Prompt

After the agent responds, the harness calls `build_judge_payload()` which fills the C2 `judge_prompt_template`. The template uses placeholder replacement (`.replace("{key}", value)`).

### Placeholders Filled

| Placeholder | Source | Content |
|-------------|--------|---------|
| `{requirements_spec}` | `json.dumps(entry["input"]["requirements_spec"])` | The requirements specification the agent was given |
| `{system_context}` | `entry["input"]["system_context"]` | The existing system architecture context |
| `{agent_output}` | Agent's response | The full technical design the agent produced |
| `{gold_standard_design}` | `json.dumps(entry["gold_standard_output"])` | Expert-written technical design |
| `{calibration_persona}` | `rubric["calibration_persona"]` | Grading instructions for the judge |
| `{hard_caps_text}` | Formatted from `rubric["hard_caps"]` | Rules that force score limits |
| `{dimensions_text}` | Formatted from `rubric["dimensions"]` | All 5 dimensions with tier definitions |

**Note:** C2's template has **different placeholders** than C1's. C1 uses `{input_requirement}` and `{gold_standard_spec}`. C2 uses `{requirements_spec}`, `{system_context}`, and `{gold_standard_design}`. The `build_judge_payload()` function pre-populates all possible keys so the same function works for both categories.

### Resulting Judge Prompt (simplified)

```
You are a principal engineer evaluating the quality of a technical design
document produced by an AI coding agent.

## Context
The agent was given:
1. This requirements specification:
<requirements>
{ ... user stories, state machine, edge cases ... }
</requirements>

2. This existing system architecture context:
<system_context>
Existing FastAPI microservice 'xhs-campaign-service' ...
</system_context>

The agent produced this technical design:
<output>
{ ... agent's module design, API design, data model ... }
</output>

## Reference Design (Gold Standard)
<reference>
{ ... expert-written design with module_design, api_design, data_model,
  integration_points, technical_decisions, data_flow ... }
</reference>

## Calibration
You are a principal engineer reviewing a technical design for a
high-traffic production system. Grade based on whether this design could
actually be built, deployed, and maintained...

## Hard Capping Rules
...

## Evaluation Task
Score the agent's output on each of the following 5 dimensions.
...

## Output Format
Respond in JSON: { dimension_1: {score, justification}, ... }
```

### Step 2–3: Submit and Parse

Identical to C1. The judge prompt goes to the same agent/model, returns structured JSON with per-dimension scores and justifications, and the harness extracts the total (max 100).

---

## 4. Rubric Design (`c2_design.json`) — Full Reference

The rubric file at `evaluation/rubrics/c2_design.json` is the single source of truth for C2 scoring.

### Top-Level Fields

```json
{
  "category": "C2",
  "category_name": "Technical Design",
  "category_name_zh": "技术方案设计",
  "evaluation_method": "llm_as_judge",
  "total_points": 100,
  "pass_threshold": 60,
  "dimensions": [ ... ],
  "hard_caps": [ ... ],
  "calibration_persona": "...",
  "judge_prompt_template": "..."
}
```

| Field | Type | Description |
|-------|------|-------------|
| `category` | string | Category identifier: `"C2"` |
| `category_name` | string | English name: `"Technical Design"` |
| `category_name_zh` | string | Chinese name: `"技术方案设计"` |
| `evaluation_method` | string | Always `"llm_as_judge"` for C2 |
| `total_points` | int | Maximum possible score: `100` |
| `pass_threshold` | int | Minimum score to be considered "passing": `60` |
| `dimensions` | array | The 5 scoring dimensions (see below) |
| `hard_caps` | array | Override rules that force score limits (see below) |
| `calibration_persona` | string | Instructions telling the judge WHO to be when grading |
| `judge_prompt_template` | string | The full prompt template with `{placeholders}` |

---

### `dimensions` Array — All 5 Dimensions with Complete Tier Definitions

Each dimension object has this structure:

```json
{
  "id": "D1",
  "name": "Architecture Soundness",
  "name_zh": "架构合理性",
  "max_score": 25,
  "tiers": [
    {"score": 25, "criteria": "..."},
    {"score": 20, "criteria": "..."},
    {"score": 15, "criteria": "..."},
    {"score": 10, "criteria": "..."},
    {"score": 5,  "criteria": "..."}
  ]
}
```

#### D1: Architecture Soundness (架构合理性) — 25 points

| Score | Criteria |
|-------|----------|
| **25** | Clean separation of concerns with clear module boundaries. Appropriate design patterns applied (not forced). Layer dependencies are unidirectional. Service boundaries align with business domains. Considers horizontal scalability. No circular dependencies. Consistent with existing system architecture style. |
| **20** | Good separation of concerns. Mostly appropriate patterns. Minor architectural smells. Compatible with existing architecture. |
| **15** | Reasonable structure but some design issues: 2-3 unclear module boundaries, or a pattern choice that doesn't fit well. Would require some rework for production. |
| **10** | Significant structural issues: tight coupling between modules, inappropriate patterns, or design that ignores the existing system architecture. |
| **5** | Fundamentally flawed: monolithic design for a microservice context, or fragmented into too many services with excessive inter-service calls. |

**What the judge looks for:** Does the agent follow the existing layered architecture (Model → Repository → Service → API) with unidirectional dependencies? Does it reuse existing patterns (TimestampMixin, SoftDeleteMixin, generate_uuid()) instead of reinventing them? A top-tier design extends the system naturally — someone familiar with the User module would immediately understand the Campaign module.

#### D2: API Design Quality (API 设计质量) — 20 points

| Score | Criteria |
|-------|----------|
| **20** | RESTful conventions followed consistently. All endpoints have clear request/response schemas with types. Proper HTTP methods and status codes. Pagination for list endpoints. Idempotency for mutations. Versioning strategy stated. Error response format standardized. Authentication/authorization specified per endpoint. |
| **16** | Good API design with minor gaps: missing pagination on a list endpoint, or inconsistent error format. Most endpoints well-defined. |
| **12** | APIs defined but with notable issues: missing response schemas, inconsistent naming conventions, or missing error handling specification. |
| **8** | Minimal API definition. Only endpoint paths listed without detailed schemas. Major design issues. |
| **4** | No meaningful API design, or APIs that contradict RESTful principles throughout. |

**What the judge looks for:** Concrete details per endpoint: method, path, auth requirement, request body schema (with field types and constraints), response schema, and error conditions (with HTTP status codes and conditions). Vague endpoints like "POST /campaigns — creates a campaign" score low. Specific endpoints like "POST /api/v1/campaigns — CampaignCreate body, 201 response, 403 if not brand role, 422 on validation failure" score high.

#### D3: Data Model Completeness (数据模型完整性) — 20 points

| Score | Criteria |
|-------|----------|
| **20** | All entities identified with complete field definitions (name, type, constraints). Relationships properly modeled (FK, junction tables for M:N). Appropriate indexes for query patterns. Soft delete where appropriate. Audit fields (created_at, updated_at). Enum types for status fields. |
| **16** | Good schema covering all main entities. Relationships correct. Minor gaps: missing an index, or incomplete field constraints. |
| **12** | Main entities present but some incomplete: missing fields, or relationships not properly modeled. |
| **8** | Incomplete schema: missing 1-2 important entities, or fundamental relationship errors. |
| **4** | Minimal or incorrect schema that would not support the required functionality. |

**What the judge looks for:** Column-level detail — not just "campaigns table with relevant fields" but the exact column name, SQL type, nullable/not-null, default value, and why. Index design should match query patterns mentioned in the requirements (e.g., compound index on `owner_id + status` for the "list my campaigns filtered by status" query). Audit tables should be append-only with immutable timestamps.

#### D4: System Constraint Adherence (系统约束遵循) — 20 points

| Score | Criteria |
|-------|----------|
| **20** | All integration points with existing services clearly identified with interface contracts. Respects existing auth patterns. Uses existing infrastructure appropriately. Backward compatibility considered. Failure handling at integration points specified. |
| **16** | Integration points identified. Uses existing infrastructure. Minor gaps in failure handling or boundary specification. |
| **12** | Acknowledges existing services but integration details are vague. Some unverified assumptions. |
| **8** | Ignores some existing system constraints. Proposes redundant infrastructure. |
| **4** | Designs in isolation, ignoring the existing system context entirely. |

**What the judge looks for:** Does the agent use what's already there? The system_context says "auth via X-User-Id header → CurrentUser dependency, role enforcement via require_role()" — a good design uses these exact patterns, not a custom JWT middleware. Does it identify integration boundaries? "Notification is fire-and-forget via Celery task" means the design should not make status transitions depend on notification success. Does it handle failure at service boundaries?

#### D5: Trade-off Analysis & Risk Awareness (权衡分析与风险意识) — 15 points

| Score | Criteria |
|-------|----------|
| **15** | Key technical decisions have explicit justification with alternatives considered. Performance implications discussed. At least 2 technical risks identified with mitigation strategies. |
| **12** | Some decisions justified with alternatives mentioned. 1-2 risks identified. Trade-off thinking is present but not thorough. |
| **9** | Decisions made without justification. One risk mentioned in passing. Little evidence of alternative evaluation. |
| **6** | No trade-off analysis. Design presented as the only option. No risk awareness. |
| **3** | Design choices contradict the stated constraints without acknowledgment. |

**What the judge looks for:** Explicit reasoning. "Use optimistic locking" alone is 9/15. "Use optimistic locking because conflicts are rare but data loss is unacceptable; pessimistic locking would hold locks during user edit sessions (seconds to minutes), risking deadlocks; last-write-wins causes silent data loss on budget fields" is 15/15. The alternatives_considered + rejected_because pattern is what separates a design review from a design dump.

---

### `hard_caps` Array — Override Rules

Hard caps are checked **before** scoring. If a condition is true, the judge MUST enforce the score limit.

```json
[
  {
    "condition": "Design introduces circular dependencies or creates a distributed monolith",
    "effect": "D1 <= 10"
  },
  {
    "condition": "Design provides no API contracts (just endpoint names without request/response schemas)",
    "effect": "D2 <= 8"
  },
  {
    "condition": "Design has no database schema or only lists table names without fields/types/relationships",
    "effect": "D3 <= 8"
  },
  {
    "condition": "Design completely ignores the existing system context",
    "effect": "D4 <= 8"
  },
  {
    "condition": "Systemic vs isolated: missing index on one table in otherwise thoughtful schema is 16/20, not 8/20",
    "effect": "calibration_guidance"
  }
]
```

| # | Condition | Effect | Purpose |
|---|-----------|--------|---------|
| 1 | Circular dependencies or distributed monolith | `D1 <= 10` | Architecture that looks decoupled but requires every module to call every other module is worse than a monolith — it has the complexity of both without the benefits of either. |
| 2 | No API contracts (just endpoint names) | `D2 <= 8` | An API design without request/response schemas is not a design — it's a placeholder. "POST /campaigns" without field definitions tells a developer nothing. |
| 3 | No database schema or only table names | `D3 <= 8` | Same principle: "campaigns table" without columns, types, and indexes is not a data model. |
| 4 | Ignores existing system context | `D4 <= 8` | The entire point of C2 is designing *within* an existing system. A greenfield design that ignores the provided patterns, conventions, and infrastructure fails the fundamental constraint. |
| 5 | Systemic vs isolated (calibration guidance) | `calibration_guidance` | Missing one index in a well-thought-out schema is an isolated gap (16/20), not a systemic failure (8/20). Prevents over-penalizing single omissions. |

---

### `calibration_persona` — Grading Identity

```
"You are a principal engineer reviewing a technical design for a high-traffic
production system. Grade based on whether this design could actually be built,
deployed, and maintained — not on whether it reads well as a document. Avoid
leniency bias (being impressed by comprehensive diagrams while missing
fundamental architectural flaws) AND paranoia (penalizing reasonable
simplifications in a first-iteration design)."
```

**Key differences from C1's persona:**

| Aspect | C1 Persona | C2 Persona |
|--------|-----------|-----------|
| **Role** | "Senior staff engineer who has reviewed hundreds of PRDs" | "Principal engineer reviewing for a high-traffic production system" |
| **Focus** | Completeness of *thinking* | Whether the design could actually be *built and maintained* |
| **Leniency trap** | "Impressed by well-formatted but shallow specs" | "Impressed by comprehensive diagrams while missing architectural flaws" |
| **Harshness trap** | "Punitive for isolated minor omissions" | "Penalizing reasonable simplifications in a first-iteration design" |

The C2 persona is deliberately more engineering-focused — it's not about whether the document reads well, but whether you could hand this to a team and have them start building.

---

### `judge_prompt_template` — The Complete Template

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
<reference>
{gold_standard_design}
</reference>

## Calibration
{calibration_persona}

## Hard Capping Rules
{hard_caps_text}

## Evaluation Task
Score the agent's output on each of the following 5 dimensions.

{dimensions_text}

## Output Format
Respond in JSON:
{
  "hard_cap_triggered": [{"rule": "...", "triggered": true/false}],
  "dimension_1": {"score": <int>, "justification": "<string>"},
  "dimension_2": {"score": <int>, "justification": "<string>"},
  "dimension_3": {"score": <int>, "justification": "<string>"},
  "dimension_4": {"score": <int>, "justification": "<string>"},
  "dimension_5": {"score": <int>, "justification": "<string>"},
  "total_score": <int>,
  "overall_assessment": "<1-2 sentence summary>"
}
```

#### Placeholder Reference

| Placeholder | Filled By | Content |
|-------------|-----------|---------|
| `{requirements_spec}` | `json.dumps(entry["input"]["requirements_spec"])` | The user stories, state machine, edge cases — the structured spec the agent was given |
| `{system_context}` | `entry["input"]["system_context"]` | Existing architecture description — FastAPI, SQLAlchemy patterns, auth conventions |
| `{agent_output}` | Agent's captured response | The complete technical design the agent produced |
| `{gold_standard_design}` | `json.dumps(entry["gold_standard_output"])` | Expert-written design (module_design, api_design, data_model, etc.) |
| `{calibration_persona}` | `rubric["calibration_persona"]` | Principal engineer grading identity |
| `{hard_caps_text}` | Formatted from `rubric["hard_caps"]` | All hard cap rules as bullet list |
| `{dimensions_text}` | Formatted from `rubric["dimensions"]` | All 5 dimensions with tier tables |

#### Judge Output Schema

The judge returns the same JSON structure as C1:

```json
{
  "hard_cap_triggered": [
    {"rule": "Design introduces circular dependencies or creates a distributed monolith", "triggered": false},
    {"rule": "Design provides no API contracts", "triggered": false},
    {"rule": "Design has no database schema or only lists table names", "triggered": false},
    {"rule": "Design completely ignores the existing system context", "triggered": false}
  ],
  "dimension_1": {
    "score": 25,
    "justification": "Clean layered architecture following existing Model → Repo → Service → API pattern. Correct dependency direction. Reuses TimestampMixin, SoftDeleteMixin, generate_uuid(). No circular dependencies."
  },
  "dimension_2": {
    "score": 16,
    "justification": "10 well-defined endpoints with method, path, auth, request/response schemas. Proper HTTP status codes. Missing idempotency discussion for mutation endpoints and versioning strategy."
  },
  "dimension_3": {
    "score": 20,
    "justification": "Complete schema for campaigns (22 columns) and status_logs (7 columns). All column types, constraints, and defaults specified. 4 indexes aligned with query patterns. CampaignStatus enum properly defined."
  },
  "dimension_4": {
    "score": 16,
    "justification": "Correctly identifies User Service (same DB, direct repo call) and Notification Service (Celery fire-and-forget). Auth pattern matches existing CurrentUser + require_role(). Minor gap: no explicit failure handling for Celery enqueue."
  },
  "dimension_5": {
    "score": 12,
    "justification": "Optimistic locking decision well-justified with alternatives. Decimal for money explained. Missing risk analysis for deadline enforcement and timezone handling."
  },
  "total_score": 89,
  "overall_assessment": "Strong technical design that demonstrates understanding of the existing system and produces a buildable blueprint. Minor gaps in API idempotency and risk analysis."
}
```

---

## 5. C1 vs C2 Comparison

| Aspect | C1 (Requirements) | C2 (Technical Design) |
|--------|-------------------|----------------------|
| **Input** | Vague business requirement from a PM | Structured requirements spec + system context |
| **Output** | Requirements specification (user stories, edge cases, clarifying questions) | Technical design (modules, APIs, data model, decisions) |
| **Agent role** | "Senior software engineer performing requirements analysis" | "Senior software architect designing a technical solution" |
| **Judge role** | "Senior staff engineer who has reviewed hundreds of PRDs" | "Principal engineer reviewing for a high-traffic production system" |
| **Gold standard purpose** | Shows what thorough *thinking* looks like | Shows what a *buildable* design looks like |
| **Top dimension** | D1: Functional Completeness (25 pts) — did you find all the requirements? | D1: Architecture Soundness (25 pts) — is the structure clean and consistent? |
| **Most distinctive dimension** | D3: Ambiguity Identification (20 pts) — did you ask the right questions? | D5: Trade-off Analysis (15 pts) — did you justify your decisions? |
| **Pass threshold** | 60/100 | 60/100 |
| **Composite weight** | 15% of overall score | 15% of overall score |

---

## 6. End-to-End Flow Summary

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. LOAD: Read C2-01_campaign_creation.json                      │
│    Extract input.requirements_spec, system_context, constraints  │
│                                                                 │
│ 2. PROMPT: build_prompt_c2(entry)                               │
│    "You are a senior software architect..."                     │
│    + structured requirements spec                               │
│    + existing system architecture context                       │
│    + performance/security/integrity constraints                 │
│    + "Produce a technical design document..."                   │
│                                                                 │
│ 3. SUBMIT: Pipe prompt to agent CLI via stdin                   │
│    agy --input-format text --model gemini-3.8-flash-high ...    │
│    Agent responds with technical design (pure text)             │
│                                                                 │
│ 4. SAVE: Agent response → results/outputs/C2-01_*.json          │
│                                                                 │
│ 5. JUDGE PROMPT: build_judge_payload()                          │
│    Fill judge_prompt_template with:                             │
│    - Requirements spec (what the agent was given)               │
│    - System context (architecture to design within)             │
│    - Agent's output (the design it produced)                    │
│    - Gold standard (expert design for calibration)              │
│    - Rubric dimensions (5 dims with tier definitions)           │
│    - Hard caps (critical failure rules)                         │
│    - Calibration persona (principal engineer identity)          │
│                                                                 │
│ 6. JUDGE: Send judge prompt to same agent/model                 │
│    Judge returns JSON: {D1: {score, justification}, ...}        │
│                                                                 │
│ 7. SCORE: Parse JSON, extract D1-D5 scores, sum total           │
│    Store in results file with metadata                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Key Design Decisions

### Why give the agent a structured spec (not a vague requirement)?
C2 measures *design* ability, not requirements extraction. Giving a vague requirement would conflate C1 and C2 scores. The structured spec isolates the design skill.

### Why include system_context?
Real-world technical design always happens within an existing system. Designing in a vacuum is a different (and less useful) skill. The system_context forces the agent to demonstrate *integration* thinking — reusing patterns, following conventions, respecting boundaries.

### Why separate D4 (System Constraints) from D1 (Architecture)?
An agent can produce a clean architecture that completely ignores the existing system. D4 specifically measures whether the design *fits* — does it use the auth patterns? Does it follow the naming conventions? Does it reuse infrastructure (Redis, Celery) instead of proposing new dependencies?

### Why is D5 (Trade-offs) only 15 points?
Trade-off analysis is important but secondary to the design itself. A design with perfect architecture, APIs, and data model but no explicit trade-off discussion is still buildable. A design with beautiful trade-off analysis but broken architecture is not. The weight reflects this priority.

### Why does the calibration persona say "not on whether it reads well as a document"?
This guards against a common failure mode: designs that are comprehensive documents but architecturally unsound. A well-formatted design with clean diagrams that introduces circular dependencies is worse than a terse design with correct module boundaries. The persona tells the judge to evaluate *engineering quality*, not *document quality*.
