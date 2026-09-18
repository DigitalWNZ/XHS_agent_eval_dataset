# C1 Evaluation Guide: Requirements Understanding

## Overview

C1 tests whether a coding agent can take a **vague business requirement** and produce a **comprehensive, structured requirements specification**. It evaluates the agent's ability to think like a senior engineer — deriving implicit requirements, identifying edge cases, asking clarifying questions, and structuring the output for downstream consumption.

---

## 1. Data File Structure

Each C1 entry is a JSON file in `dataset/c1/`. There are 5 entries, one per business journey.

```
dataset/c1/
├── C1-01_campaign_creation.json      # Journey 1: Brand Campaign Creation
├── C1-02_creator_application.json    # Journey 2: Creator Discovery & Application
├── C1-03_content_submission.json     # Journey 3: Content Submission & Revision
├── C1-04_review_workflow.json        # Journey 4: Review & Approval Workflow
└── C1-05_settlement_analytics.json   # Journey 5: Settlement & Analytics
```

### Top-Level Fields

| Field | Type | Purpose |
|-------|------|---------|
| `instance_id` | string | Unique identifier (e.g., `"C1-01"`) |
| `category` | string | Always `"C1"` |
| `category_name` | string | `"需求理解与预评审"` (Requirements Understanding) |
| `maps_to_journey` | string | Which business journey this entry covers |
| `input` | object | **What the agent receives** — the vague business requirement |
| `gold_standard_output` | object | **Expert-written specification** — calibration anchor for the judge |
| `evaluation_rubric` | string | Path to the rubric file (`evaluation/rubrics/c1_requirements.json`) |

### `input` Object

The input simulates what a product manager might say in a kickoff meeting — deliberately vague and under-specified.

| Sub-field | Type | Purpose |
|-----------|------|---------|
| `role` | string | Who is making the request (e.g., `"Product Manager"`) |
| `requirement_description` | string | The vague, natural-language business ask. Deliberately under-specified so we can test if the agent derives implicit requirements. |
| `context` | string | Tech stack and system information (e.g., `"FastAPI microservice, PostgreSQL, Redis, Celery"`) |

**Example `input`:**
```json
{
  "role": "Product Manager",
  "requirement_description": "We need to let brands create campaigns on our platform. Brands should be able to post a brief describing what kind of content they want from creators, set a budget, and define who can apply. Once posted, creators can see the campaign in a marketplace. We already have a user system with brands and creators. This is the first version so don't overcomplicate things, but it should be production-ready. Target launch: 4 weeks.",
  "context": "The system is a FastAPI microservice called campaign-service. We have existing User and Content services. Tech stack: Python, PostgreSQL, Redis, Celery."
}
```

### `gold_standard_output` Object

The expert-written specification serves as a **calibration anchor** for the LLM judge — not as a hard answer key. It contains a `structured_spec` with the following sections:

| Section | Content | Example |
|---------|---------|---------|
| `overview` | One-paragraph summary of the feature | "Enable brand users to create, manage, and publish campaign briefs..." |
| `user_stories` | Numbered user stories (US-1.1, US-1.2...) with detailed acceptance criteria | Each story has `id`, `story`, and `acceptance_criteria` (list of strings) |
| `state_machine` | `states` (list) + `transitions` (list of `{from, to, trigger, guard}`) | 7 states, 9 transitions with guards like "rejection reason provided" |
| `edge_cases` | Numbered scenarios (EC-1.1...) with `scenario` + `handling` | "Brand sets max_fee < min_fee" → "Reject with validation error" |
| `clarifying_questions` | Questions the agent SHOULD ask, with `question`, `impact`, and `assumption_if_unanswered` | "Can multiple brand team members manage the same campaign?" |
| `non_functional_requirements` | Numbered NFRs with `category`, `requirement`, `rationale` | Performance: "Campaign list endpoint should respond within 200ms (p95)" |
| `priority_classification` | P0 (must have), P1 (should have), P2 (nice to have) | P0: Create, Submit, Approve. P2: Campaign templates, Draft auto-save |

**Why gold standard and not direct assertion?**
- The gold standard gives the judge a concrete reference for what "thorough" looks like
- The judge does NOT check "did the agent match the gold standard word-for-word"
- Instead it asks "does the agent demonstrate the same depth of thinking?"
- This prevents score drift across different judge runs
- Different agents can produce valid but different specifications and still score well

---

## 2. Submission: How the Agent Prompt Is Built

The agent prompt is constructed by `build_prompt_c1()` in `evaluation/run_benchmark.py`:

```python
def build_prompt_c1(entry: dict) -> str:
    inp = entry["input"]
    return (
        f"You are a senior software engineer performing requirements analysis.\n\n"
        f"## Context\n"
        f"Role: {inp['role']}\n"
        f"System Context: {inp['context']}\n\n"
        f"## Business Requirement\n"
        f"{inp['requirement_description']}\n\n"
        f"## Task\n"
        f"Produce a structured requirements specification that includes:\n"
        f"1. User stories with detailed acceptance criteria\n"
        f"2. State machine definition (states, transitions, guards)\n"
        f"3. Edge cases with handling strategies\n"
        f"4. Clarifying questions with assumptions if unanswered\n"
        f"5. Non-functional requirements (performance, security, data integrity)\n"
        f"6. Priority classification (P0/P1/P2)\n\n"
        f"Output as structured JSON."
    )
```

### Resulting Prompt (C1-01 example)

```
You are a senior software engineer performing requirements analysis.

## Context
Role: Product Manager
System Context: The system is a FastAPI microservice called campaign-service.
We have existing User and Content services. Tech stack: Python, PostgreSQL,
Redis, Celery.

## Business Requirement
We need to let brands create campaigns on our platform. Brands should be able
to post a brief describing what kind of content they want from creators, set
a budget, and define who can apply. Once posted, creators can see the campaign
in a marketplace. We already have a user system with brands and creators.
This is the first version so don't overcomplicate things, but it should be
production-ready. Target launch: 4 weeks.

## Task
Produce a structured requirements specification that includes:
1. User stories with detailed acceptance criteria
2. State machine definition (states, transitions, guards)
3. Edge cases with handling strategies
4. Clarifying questions with assumptions if unanswered
5. Non-functional requirements (performance, security, data integrity)
6. Priority classification (P0/P1/P2)

Output as structured JSON.
```

### How It's Submitted

The prompt is piped to the agent CLI via stdin. For Antigravity (agy):

```bash
agy --input-format text \
    --model gemini-3.8-flash-high \
    --output-format stream-json \
    --dangerously-skip-permissions
```

Key points:
- **No tools, no repo access** — C1 is pure text-in, text-out
- The agent just thinks and writes (no code execution, no file browsing)
- The agent's full text response is captured and saved to `results/outputs/C1-01_agy_gemini-3.8-flash-high.json`

---

## 3. Evaluation: How the Judge Scores

### Step 1: Build the Judge Prompt

After the agent responds, the harness calls `build_judge_payload()` which fills the `judge_prompt_template` from the rubric file. The template uses placeholder replacement (`.replace("{key}", value)` — not `.format()`, because JSON braces would conflict).

### Placeholders Filled

| Placeholder | Source | Content |
|-------------|--------|---------|
| `{input_requirement}` | `entry["input"]` | The original vague business requirement |
| `{agent_output}` | Agent's response | The full specification the agent produced |
| `{gold_standard_spec}` | `entry["gold_standard_output"]` | Expert-written specification |
| `{calibration_persona}` | `rubric["calibration_persona"]` | Grading instructions for the judge |
| `{hard_caps_text}` | `rubric["hard_caps"]` + per-dimension hard caps | Rules that force score limits |
| `{dimensions_text}` | `rubric["dimensions"]` | All 5 dimensions with tier definitions |

### Resulting Judge Prompt (simplified)

```
You are a senior software architect evaluating the quality of a
requirements specification produced by an AI coding agent.

## Context
The agent was given this input (a vague business requirement):
<input>
{
  "role": "Product Manager",
  "requirement_description": "We need to let brands create campaigns...",
  "context": "FastAPI microservice..."
}
</input>

The agent produced this requirements specification:
<output>
{ ... agent's full response ... }
</output>

## Reference Specification (Gold Standard)
For comparison, here is an expert-written specification:
<reference>
{ ... gold standard spec with user stories, state machine, edge cases ... }
</reference>

## Calibration
You are a senior staff engineer who has reviewed hundreds of PRDs and
spec documents. Grade based on the severity, frequency, and systemic
nature of gaps. Avoid leniency bias (being too generous or impressed by
well-formatted but shallow specs) AND paranoia (being overly punitive
for isolated minor omissions in an otherwise thorough spec).

## Hard Capping Rules
Before scoring, check for these conditions that FORCE score limits:
- Spec misunderstands core business intent: overall_score <= 40
- Zero clarifying questions despite obvious ambiguities: D3 <= 8
- Spec contains no edge cases or exception handling at all: D2 <= 5
- Spec is unstructured text with no requirement numbering: D4 <= 6

## Evaluation Task
Score the agent's output on each of 5 dimensions:

### D1: Functional Completeness (25 points)
- 25 pts: Identifies all explicit requirements AND proactively derives
  implicit requirements. Covers all CRUD operations, state transitions.
- 20 pts: Identifies all explicit and most implicit ones. Minor gaps.
- 15 pts: Covers main happy path but misses 2-3 important flows.
- 10 pts: Only addresses the most obvious requirements. Surface-level.
- 5 pts: Fundamentally incomplete. Misses core functional requirements.

### D2: Edge Case & Exception Handling (25 points)
- 25 pts: Identifies 8+ valid edge cases including concurrency,
  boundary values, temporal edge cases. Each has handling strategy.
- 20 pts: Identifies 5-7 valid edge cases covering multiple categories.
...

### D3: Ambiguity Identification & Clarification (20 points)
...
### D4: Structure & Specification Quality (15 points)
...
### D5: Non-functional & Feasibility Awareness (15 points)
...

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

### Step 2: Submit Judge Prompt

The judge prompt is sent to the **same agent/model** via another CLI invocation:

```bash
agy --input-format text \
    --model gemini-3.8-flash-high \
    --output-format json \
    --dangerously-skip-permissions \
    --print-timeout 5m
```

The judge returns structured JSON with per-dimension scores and justifications.

### Step 3: Parse Scores

The harness parses the JSON response, extracts scores for D1-D5, sums them for the total (max 100), and stores everything in the results file.

---

## 4. Rubric Design (`c1_requirements.json`) — Full Reference

The rubric file at `evaluation/rubrics/c1_requirements.json` is the single source of truth for C1 scoring. Below is a field-by-field breakdown of the entire JSON.

### Top-Level Fields

```json
{
  "category": "C1",
  "category_name": "Requirements Understanding",
  "category_name_zh": "需求理解与预评审",
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
| `category` | string | Category identifier: `"C1"` |
| `category_name` | string | English name: `"Requirements Understanding"` |
| `category_name_zh` | string | Chinese name: `"需求理解与预评审"` |
| `evaluation_method` | string | Always `"llm_as_judge"` for C1 — meaning an LLM grades the output using this rubric, rather than automated tests |
| `total_points` | int | Maximum possible score: `100` |
| `pass_threshold` | int | Minimum score to be considered "passing": `60` |
| `dimensions` | array | The 5 scoring dimensions (see below) |
| `hard_caps` | array | Override rules that force score limits (see below) |
| `calibration_persona` | string | Instructions telling the judge WHO to be when grading |
| `judge_prompt_template` | string | The full prompt template with `{placeholders}` that gets filled at evaluation time |

---

### `dimensions` Array — All 5 Dimensions with Complete Tier Definitions

Each dimension object has this structure:

```json
{
  "id": "D1",
  "name": "Functional Completeness",
  "name_zh": "功能完整性",
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

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Dimension identifier (D1–D5) |
| `name` | string | English name |
| `name_zh` | string | Chinese name |
| `max_score` | int | Maximum points for this dimension |
| `tiers` | array | Exactly 5 scoring tiers, descending from max to min. Each has `score` (int) and `criteria` (string) |

#### D1: Functional Completeness (功能完整性) — 25 points

| Score | Criteria |
|-------|----------|
| **25** | Identifies all explicit requirements AND proactively derives implicit requirements (e.g., "campaign creation" implies "campaign editing/deletion"). Covers all CRUD operations, state transitions, and user-facing feedback. No functional gaps. |
| **20** | Identifies all explicit requirements and most implicit ones. Minor gaps in secondary flows (e.g., missing cancel/undo operations). |
| **15** | Covers the main happy path but misses 2-3 important secondary flows or implicit requirements. |
| **10** | Only addresses the most obvious requirements. Misses multiple important flows. Feels like a surface-level reading of the input. |
| **5** | Fundamentally incomplete. Misses core functional requirements or misunderstands the business intent. |

**What the judge looks for:** Does the agent go beyond the literal words of the PM's request? A PM says "create campaigns" — a good spec also covers edit, delete, list, archive, clone. The top tier requires the agent to *derive* unstated requirements.

#### D2: Edge Case & Exception Handling (边界与异常场景) — 25 points

| Score | Criteria |
|-------|----------|
| **25** | Identifies 8+ valid edge cases including: concurrency issues, boundary values, temporal edge cases, data integrity issues, and permission boundaries. Each has a defined handling strategy. |
| **20** | Identifies 5-7 valid edge cases covering multiple categories. Most have handling strategies. |
| **15** | Identifies 3-4 valid edge cases but concentrated in one category. Some handling strategies missing. |
| **10** | Identifies 1-2 obvious edge cases. No systematic thinking about failure modes. |
| **5** | No meaningful edge cases identified, or identified "edge cases" are actually normal flows. |

**What the judge looks for:** Quantity AND diversity of edge cases. 8 edge cases that are all "invalid input" variants would score lower than 6 edge cases spanning concurrency, time zones, permission escalation, and data races. Each edge case must have a *handling strategy*, not just be listed.

#### D3: Ambiguity Identification & Clarification (歧义识别与澄清) — 20 points

| Score | Criteria |
|-------|----------|
| **20** | Identifies 5+ genuine ambiguities. Questions are specific, non-obvious, and answering them would materially change the implementation. Clearly states assumptions when questions can't be answered. |
| **16** | Identifies 3-4 genuine ambiguities. Questions are specific and relevant. Assumptions are stated. |
| **12** | Identifies 1-2 ambiguities but questions are somewhat generic. Some assumptions unstated. |
| **8** | Asks questions but they're trivial or answerable from the input itself. Or makes significant unstated assumptions. |
| **4** | No ambiguities identified. Proceeds with silent assumptions, or asks irrelevant questions. |

**What the judge looks for:** The quality of questions matters more than quantity. "What database should we use?" is trivial (already stated in context). "Can multiple brand team members manage the same campaign, and if so, how are conflicting edits handled?" is specific, non-obvious, and implementation-altering.

**Note:** The tier scores for D3 are `20/16/12/8/4` (multiples of 4), not the `25/20/15/10/5` pattern used by D1/D2. This is because D3's max is 20, and the designers chose to space tiers evenly within that range.

#### D4: Structure & Specification Quality (结构与规范质量) — 15 points

| Score | Criteria |
|-------|----------|
| **15** | Follows a clear spec structure (user stories / use cases with preconditions, postconditions, alternate flows). Uses consistent formatting. Includes priority/MoSCoW classification. Requirements are atomic, testable, and uniquely identifiable (numbered). |
| **12** | Good structure with clear sections. Requirements are mostly atomic and testable. Minor formatting inconsistencies. |
| **9** | Organized but informal. Requirements described in paragraphs rather than structured formats. Some ambiguous requirements that aren't testable. |
| **6** | Poorly organized. Mixed concerns within sections. Hard to trace individual requirements. |
| **3** | Unstructured dump of text. No clear organization or requirement identification. |

**What the judge looks for:** Can a developer pick up this spec and start implementing without asking "what does this mean?" Key signals: numbered requirements (US-1.1, EC-2.3), acceptance criteria per story, preconditions/postconditions, priority labels (P0/P1/P2 or MoSCoW).

#### D5: Non-functional & Feasibility Awareness (非功能性与可行性) — 15 points

| Score | Criteria |
|-------|----------|
| **15** | Identifies relevant NFRs: performance expectations, security requirements, data consistency requirements, and scalability considerations. Flags potential technical risks or constraints. |
| **12** | Identifies 3-4 NFRs covering at least 2 categories. Some risk awareness. |
| **9** | Mentions NFRs but generically ("should be fast" without specific expectations). Limited risk identification. |
| **6** | Brief mention of 1 NFR category. No feasibility assessment. |
| **3** | No NFRs mentioned. No awareness of technical constraints. |

**What the judge looks for:** Specificity. "The API should be fast" scores low. "Campaign list endpoint should respond within 200ms (p95) for up to 10,000 active campaigns" scores high. Also looks for security awareness (authz on campaign ownership), data integrity (concurrent budget deductions), and realistic constraints (4-week timeline → what can we cut?).

---

### `hard_caps` Array — Override Rules

Hard caps are checked **before** scoring. If a condition is true, the judge MUST enforce the score limit regardless of other quality.

```json
[
  {
    "condition": "Spec misunderstands the core business intent",
    "effect": "overall_score <= 40"
  },
  {
    "condition": "Spec produces zero clarifying questions despite obvious ambiguities",
    "effect": "D3 <= 8"
  },
  {
    "condition": "Spec contains no edge cases or exception handling at all",
    "effect": "D2 <= 5"
  },
  {
    "condition": "Spec is unstructured text with no requirement numbering, user stories, or acceptance criteria",
    "effect": "D4 <= 6"
  },
  {
    "condition": "Systemic vs isolated: single missed edge case in otherwise thorough spec should score 20/25, not 10/25",
    "effect": "calibration_guidance"
  }
]
```

| # | Condition | Effect | Purpose |
|---|-----------|--------|---------|
| 1 | Spec misunderstands the core business intent | `overall_score <= 40` | Prevents a well-formatted but wrong spec from passing. If the agent thinks "campaign creation" means "ad bidding", nothing else matters. |
| 2 | Zero clarifying questions despite obvious ambiguities | `D3 <= 8` | Forces D3 to the second-lowest tier. The input is *deliberately* vague — an agent that asks no questions is either overconfident or not thinking. |
| 3 | No edge cases or exception handling at all | `D2 <= 5` | Forces D2 to the lowest tier. A production-ready spec without edge cases is incomplete by definition. |
| 4 | Unstructured text with no numbering, user stories, or acceptance criteria | `D4 <= 6` | Forces D4 to the second-lowest tier. Raw prose is not a usable specification. |
| 5 | Systemic vs isolated (calibration guidance) | `calibration_guidance` | Not a hard cap — it's a grading instruction. Tells the judge: one missed edge case in an otherwise thorough spec = 20/25, not 10/25. Prevents over-penalizing isolated gaps. |

The judge reports which hard caps triggered in its JSON output:
```json
"hard_cap_triggered": [
  {"rule": "Spec misunderstands the core business intent", "triggered": false},
  {"rule": "Zero clarifying questions despite obvious ambiguities", "triggered": false},
  ...
]
```

---

### `calibration_persona` — Grading Identity

```
"You are a senior staff engineer who has reviewed hundreds of PRDs and spec
documents. Grade based on the severity, frequency, and systemic nature of gaps.
Avoid leniency bias (being too generous or impressed by well-formatted but
shallow specs) AND paranoia (being overly punitive for isolated minor omissions
in an otherwise thorough spec)."
```

The persona serves three purposes:
1. **Anchors expertise level** — grade like someone who knows what a good spec looks like, not a junior engineer easily impressed by bullet points
2. **Guards against leniency** — explicitly calls out the trap of being "impressed by well-formatted but shallow specs"
3. **Guards against harshness** — explicitly warns against "being overly punitive for isolated minor omissions"

---

### `judge_prompt_template` — The Complete Template

This is the exact template string stored in the rubric. At evaluation time, the harness replaces each `{placeholder}` with actual content.

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

## Calibration
{calibration_persona}

## Hard Capping Rules
Before scoring, check for these conditions that FORCE score limits:
{hard_caps_text}

## Evaluation Task
Score the agent's output on each of the following 5 dimensions. For each
dimension, provide:
1. A score (using the exact point values from the rubric)
2. A brief justification (2-3 sentences) citing specific examples from the output

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
| `{input_requirement}` | `json.dumps(entry["input"])` | The full input object (role, requirement_description, context) serialized as JSON |
| `{agent_output}` | Agent's captured response | The entire text/JSON the agent produced when given the C1 prompt |
| `{gold_standard_spec}` | `json.dumps(entry["gold_standard_output"])` | The expert-written specification from the dataset entry |
| `{calibration_persona}` | `rubric["calibration_persona"]` | The grading identity string (see above) |
| `{hard_caps_text}` | Formatted from `rubric["hard_caps"]` | All hard cap rules formatted as a bullet list |
| `{dimensions_text}` | Formatted from `rubric["dimensions"]` | All 5 dimensions with their tier tables, formatted for the judge to use as a rubric |

**Why `.replace()` instead of `.format()`?**
The template contains JSON braces (`{`, `}`) in the output format section. Python's `.format()` would interpret those as format placeholders and throw a `KeyError`. Using `.replace("{key}", value)` only replaces the specific named placeholders and leaves literal braces alone.

#### Judge Output Schema

The judge returns a JSON object with these fields:

```json
{
  "hard_cap_triggered": [
    {"rule": "Spec misunderstands the core business intent", "triggered": false},
    {"rule": "Zero clarifying questions despite obvious ambiguities", "triggered": false},
    {"rule": "Spec contains no edge cases or exception handling at all", "triggered": false},
    {"rule": "Spec is unstructured text with no requirement numbering...", "triggered": false}
  ],
  "dimension_1": {
    "score": 25,
    "justification": "Agent derived 6 user stories including implicit edit/delete/archive flows beyond what the PM explicitly requested. All CRUD operations covered with preconditions."
  },
  "dimension_2": {
    "score": 20,
    "justification": "Identified 6 edge cases across concurrency, validation, and permissions. Missing temporal edge cases (timezone handling, campaign expiry race conditions)."
  },
  "dimension_3": {
    "score": 16,
    "justification": "Asked 4 relevant clarifying questions about multi-tenant access, budget currency, and creator eligibility. Stated assumptions clearly."
  },
  "dimension_4": {
    "score": 15,
    "justification": "Well-structured with numbered user stories, acceptance criteria, state machine definition, and P0/P1/P2 priority classification."
  },
  "dimension_5": {
    "score": 12,
    "justification": "Covered performance (p95 latency), security (authz), and data integrity (budget atomicity). Missing scalability analysis for marketplace listing."
  },
  "total_score": 88,
  "overall_assessment": "Strong specification that demonstrates senior-level requirements thinking. Minor gaps in temporal edge cases and scalability NFRs."
}
```

The harness extracts `total_score` as the final C1 score for this entry (0–100).

---

## 5. End-to-End Flow Summary

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. LOAD: Read C1-01_campaign_creation.json                      │
│    Extract input.requirement_description                        │
│                                                                 │
│ 2. PROMPT: build_prompt_c1(entry)                               │
│    "You are a senior software engineer..."                      │
│    + vague business requirement                                 │
│    + "Produce a structured requirements specification..."       │
│                                                                 │
│ 3. SUBMIT: Pipe prompt to agent CLI via stdin                   │
│    agy --input-format text --model gemini-3.8-flash-high ...    │
│    Agent responds with structured specification (pure text)     │
│                                                                 │
│ 4. SAVE: Agent response → results/outputs/C1-01_*.json          │
│                                                                 │
│ 5. JUDGE PROMPT: build_judge_payload()                          │
│    Fill judge_prompt_template with:                             │
│    - Original input (vague requirement)                         │
│    - Agent's output (the spec it wrote)                         │
│    - Gold standard (expert spec for calibration)                │
│    - Rubric dimensions (5 dims with tier definitions)           │
│    - Hard caps (critical failure rules)                         │
│    - Calibration persona (grading instructions)                 │
│                                                                 │
│ 6. JUDGE: Send judge prompt to same agent/model                 │
│    Judge returns JSON: {D1: {score, justification}, ...}        │
│                                                                 │
│ 7. SCORE: Parse JSON, extract D1-D5 scores, sum total           │
│    Store in results file with metadata                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Key Design Decisions

### Why LLM-as-Judge (not automated tests)?
Requirements specifications can't be verified by running code. There's no "test suite" for a PRD. LLM-as-Judge with structured rubrics is the standard approach (used by LMSYS Chatbot Arena, MT-Bench, AlpacaEval).

### Why Gold Standard as calibration, not answer key?
Two valid specifications can look completely different. The gold standard prevents the judge from drifting — it knows what "thorough" looks like — without penalizing creative or alternative approaches.

### Why 5 dimensions instead of 1 score?
A single score hides WHERE the agent is weak. An agent might produce beautifully structured specs (high D4) but miss all edge cases (low D2). Multi-dimensional scoring reveals the capability profile.

### Why hard caps?
Without hard caps, a fundamentally flawed spec could score 70+ by being well-formatted (high D4, D5) despite missing the core business intent. Hard caps prevent this gaming.

### Why specific tier criteria with numbers?
Vague criteria ("good edge case coverage") lead to inconsistent judging. Specific criteria ("identifies 8+ valid edge cases") force the judge to count and evaluate systematically.
