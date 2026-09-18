# C3 Evaluation Guide: Code Understanding & Generation

## Overview

C3 tests whether a coding agent can take a **technical specification** and produce **working, production-quality code** within an existing codebase. It is the most heavily weighted category in the benchmark (30% of the composite score) and uses a **hybrid evaluation**: automated test execution (D1–D2) + LLM-as-Judge code quality review (D3–D7).

C3 follows the **SWE-bench** evaluation pattern:
1. Set up a clean worktree at a known commit
2. Give the agent the problem statement and full repo access
3. Capture the agent's code changes as a patch
4. Inject hidden test files (test_patch) that the agent never saw
5. Run the tests to verify correctness (FAIL_TO_PASS) and regression safety (PASS_TO_PASS)
6. Send the patch to an LLM judge for code quality scoring (D3–D7)

The agent has **full tool access** — it can read files, write code, run commands, execute tests — unlike C1/C2 which are pure text-in/text-out.

---

## 1. Data File Structure

Each C3 entry is a JSON file in `dataset/c3/`. There are 8 entries covering both new feature implementation and amendment tasks.

```
dataset/c3/
├── C3-01_campaign_crud.json          # New feature: Campaign CRUD (23 F2P tests)
├── C3-02_creator_application.json    # New feature: Creator Application flow (13 F2P)
├── C3-03_content_submission.json     # New feature: Content Submission (13 F2P)
├── C3-04_review_workflow.json        # New feature: Review & Approval (12 F2P)
├── C3-05_settlement_analytics.json   # New feature: Settlement & Analytics (14 F2P)
├── C3-06_campaign_search.json        # Amendment: Add search to campaigns (10 F2P)
├── C3-07_application_ranking.json    # Amendment: Add ranking to applications (8 F2P)
└── C3-08_rate_limiting.json          # Amendment: Add rate limiting middleware (8 F2P)
```

### Top-Level Fields

| Field | Type | Purpose |
|-------|------|---------|
| `instance_id` | string | Unique identifier (e.g., `"C3-01"`) |
| `category` | string | Always `"C3"` |
| `category_name` | string | `"代码理解与生成"` (Code Understanding & Generation) |
| `task_type` | string | `"new_feature"` or `"amendment"` — determines the scope of changes expected |
| `maps_to_journey` | string | Which business journey this entry covers |
| `base_commit` | string | Git commit hash to check out before the agent starts (e.g., `"88d9911"`) |
| `problem_statement` | string | **What the agent receives** — the full task description with technical spec |
| `gold_patch` | string | **Expert-written solution** — a git diff showing the ideal implementation |
| `test_patch` | string | **Hidden test files** — a git diff that injects test files AFTER the agent finishes |
| `FAIL_TO_PASS` | array | Test names that MUST pass after the agent's changes (the feature verification) |
| `PASS_TO_PASS` | array | Test names that MUST still pass (regression safety — existing tests) |
| `evaluation_rubric` | string | Path to rubric file (`evaluation/rubrics/c3_codegen.json`) |

### `task_type` — New Feature vs Amendment

| Type | Description | Typical Scope | Example |
|------|-------------|---------------|---------|
| `new_feature` | Build a complete module from scratch following existing patterns | 5+ new files, 200-500 lines of code | C3-01: Full Campaign CRUD (model, schema, repo, service, router) |
| `amendment` | Add a feature to an already-built module | 1-3 files modified/added, 50-200 lines | C3-08: Add rate limiting middleware to existing content endpoint |

New feature entries have **more FAIL_TO_PASS tests** (10-23) because they verify an entire module. Amendment entries have **more PASS_TO_PASS tests** (82) because the existing module's tests must not break.

### `problem_statement` — What the Agent Sees

The problem statement is a detailed technical specification. It includes:

1. **Context** — what the service is and what already exists
2. **Task** — what to implement
3. **Technical Specification** — data model, state machine, repository pattern, service layer, API endpoints, schemas
4. **Required API Contract** — exact names, paths, field names, method signatures that the hidden tests will verify

**Example — Required API Contract section (C3-08):**
```
## Required API Contract
The tests verify the following interfaces — use these exact names and paths:

### Rate Limiter: `app/utils/rate_limiter.py`
- `RateLimiter` class with constructor `RateLimiter(max_requests: int, window_seconds: int)`
- Methods: `is_allowed(key: str) -> tuple[bool, dict]` where dict has `limit`, `remaining`, `retry_after`
- Method: `reset(key: str) -> None` — clears rate limit for a specific key
- Method: `reset_all()` — clears all tracked state
- Attribute: `max_requests` — readable and writable

### Dependencies: `app/api/deps.py`
- Module-level instance: `_rate_limiter = RateLimiter(...)` (underscore-prefixed, importable)
```

**Why the API Contract is critical:** The agent never sees the test files. The tests import specific classes, call specific methods, and assert specific response structures. If the agent names a method `check_rate` instead of `is_allowed`, or puts the rate limiter instance in `app/utils/` instead of `app/api/deps.py`, every test that imports it will fail — even if the logic is correct. The Required API Contract section bridges this gap.

### `gold_patch` — Expert Solution

A complete git diff showing the ideal implementation. Used for:
- Reference during development (not shown to the agent)
- Validating that the test_patch tests are correct (the tests must pass against this patch)
- Not used directly in scoring — the agent is scored on test results and code quality, not on matching the gold patch

### `base_commit` — Starting Point

The git commit hash where the worktree is created. Different entries have different base commits because later entries build on earlier ones:

| Entry | Base Commit | Existing Modules |
|-------|-------------|-----------------|
| C3-01 | `88d9911` | Users only |
| C3-02 | `88d9911` | Users only (Campaign model exists but no app/service/routes) |
| C3-06 | `07968bf` | Users + Campaigns + Applications + Content + Reviews |
| C3-08 | `07968bf` | Users + Campaigns + Applications + Content + Reviews |

Amendment entries (C3-06/07/08) start from a later commit with more modules already built, so the agent must add to an existing codebase without breaking anything.

---

## 2. The test_patch Mechanism — Deep Dive

The test_patch is the heart of C3's automated evaluation. It is a **git diff** that injects test files into the worktree **after** the agent finishes and **before** tests are run.

### Why test_patch Exists

The agent must NEVER see the test files. If it could see them, it would:
- Reverse-engineer the expected interface from the tests
- Write code that passes specific tests rather than implementing the spec correctly
- Game the evaluation by matching test assertions exactly

By hiding the tests until after the agent is done, we ensure the agent implements from the specification, not from the tests. This is the same approach used by SWE-bench.

### test_patch Format

A test_patch is a standard git unified diff. Here's an annotated example (C3-08, abbreviated):

```diff
diff --git a/tests/api/test_rate_limiting.py b/tests/api/test_rate_limiting.py
new file mode 100644                          ← creating a new file
index 0000000..07c048a
--- /dev/null                                 ← new file (no previous version)
+++ b/tests/api/test_rate_limiting.py         ← target path in the repo
@@ -0,0 +1,349 @@                             ← hunk header: adds lines 1-349
+from datetime import datetime, timedelta, timezone
+                                              ← every line starts with +
+import pytest                                 (it's all new content)
+from httpx import AsyncClient
+
+from app.api.deps import _rate_limiter        ← imports agent's code!
+from app.models.application import Application, ApplicationStatus
+...
+
+@pytest.fixture(autouse=True)
+def configure_rate_limiter():
+    """Reset the rate limiter and set a low limit for testing."""
+    original_max = _rate_limiter.max_requests  ← accesses agent's attribute
+    _rate_limiter.reset_all()                  ← calls agent's method
+    _rate_limiter.max_requests = RATE_LIMIT
+    yield
+    _rate_limiter.reset_all()
+    _rate_limiter.max_requests = original_max
+
+...
+
+@pytest.mark.asyncio
+async def test_rate_limit_blocks_after_limit(...):
+    ...
+    resp = await client.post(                  ← calls agent's endpoint
+        f"/api/v1/applications/{apps[RATE_LIMIT].id}/content",
+        json={"title": "Content Over Limit", "body": BODY_TEXT},
+        headers={"X-User-Id": creator_user.id},
+    )
+    assert resp.status_code == 429             ← asserts agent's behavior
+    assert "Rate limit exceeded" in resp.json()["error"]
```

### Hunk Header Anatomy

```
@@ -0,0 +1,349 @@
 ^  ^ ^  ^ ^
 |  | |  | └── number of lines being added (349)
 |  | |  └──── starting line in the new file (1)
 |  | └─────── lines removed from old file (0 — it's a new file)
 |  └───────── starting line in old file (0 — no old file)
 └──────────── hunk marker
```

**Critical rule:** The line count in the hunk header MUST match the actual number of `+` lines in the diff. If the header says `+1,349` but there are only 348 `+` lines, `git apply` will fail with `error: corrupt patch at line NNN`.

This was the source of several bugs we fixed during dataset development:
- C3-02: Removed 1 assertion line but forgot to update `+1,311` → `+1,310`
- C3-04: Added 1 assertion line but forgot to update the count

### How test_patch Is Applied — Step by Step

The `run_c3()` function in `evaluation/run_benchmark.py` follows this sequence:

```
1. WORKTREE SETUP
   ┌──────────────────────────────────────────────────┐
   │ git worktree add /tmp/c3-01-xxxxx {base_commit}  │
   │ pip install -e .                                  │
   │ State: clean repo at base_commit                  │
   └──────────────────────────────────────────────────┘
                         ↓
2. AGENT RUNS
   ┌──────────────────────────────────────────────────┐
   │ Agent receives problem_statement via stdin         │
   │ Agent has full repo access (--add-dir work_dir)   │
   │ Agent reads existing code, writes new files,      │
   │   runs tests, iterates until done                 │
   │ State: repo has agent's changes                   │
   └──────────────────────────────────────────────────┘
                         ↓
3. CAPTURE AGENT PATCH
   ┌──────────────────────────────────────────────────┐
   │ git diff HEAD          → tracked file changes     │
   │ git ls-files --others  → new untracked files      │
   │ Combine into agent_patch (saved for judge review) │
   │ State: agent's changes captured as a diff         │
   └──────────────────────────────────────────────────┘
                         ↓
4. CLEAN CONFLICTING TEST FILES
   ┌──────────────────────────────────────────────────┐
   │ For each file in test_patch (+++ b/path):         │
   │   If agent created a test file at same path,      │
   │   DELETE it (agent's tests are discarded)         │
   │ Why: test_patch creates new files — if agent also │
   │   created tests/api/test_campaigns.py, git apply  │
   │   would fail because the file already exists      │
   └──────────────────────────────────────────────────┘
                         ↓
5. APPLY test_patch
   ┌──────────────────────────────────────────────────┐
   │ git apply --allow-empty <<< test_patch            │
   │ This creates the test files the agent never saw   │
   │ If apply fails → entry scored as UNRESOLVED       │
   │ State: repo has agent's code + hidden test files  │
   └──────────────────────────────────────────────────┘
                         ↓
6. RUN TESTS
   ┌──────────────────────────────────────────────────┐
   │ pytest -v {FAIL_TO_PASS tests}                    │
   │   → Must ALL pass (agent's new code works)        │
   │ pytest -v {PASS_TO_PASS tests}                    │
   │   → Must ALL pass (agent didn't break anything)   │
   │ Counts: f2p_passed/f2p_total, p2p_passed/p2p_total│
   │ resolved = (f2p == 100%) AND (p2p == 100%)        │
   └──────────────────────────────────────────────────┘
                         ↓
7. LLM JUDGE (code quality)
   ┌──────────────────────────────────────────────────┐
   │ Send agent_patch to LLM judge for D3-D7 scoring   │
   │ Judge reviews: readability, maintainability,      │
   │   robustness, convention adherence, minimality    │
   └──────────────────────────────────────────────────┘
```

### Code from the Harness

```python
def run_c3(entry, agent, model, timeout):
    # 1. Setup worktree at base_commit
    setup_worktree(base_commit, work_dir)

    # 2. Agent runs with full tool access
    agent_result = invoke_agent(
        agent, model,
        entry["problem_statement"],  # prompt is the problem_statement
        work_dir, timeout,
        need_file_writes=True,       # enables --add-dir for repo access
    )

    # 3. Capture agent's changes
    agent_patch = capture_agent_patch(work_dir)

    # 4. Remove conflicting test files the agent may have created
    test_patch = entry["test_patch"]
    for line in test_patch.splitlines():
        if line.startswith("+++ b/"):
            conflict_file = work_dir / line[6:]
            if conflict_file.exists():
                conflict_file.unlink()  # delete agent's test file

    # 5. Apply test_patch (hidden tests)
    result = subprocess.run(
        ["git", "apply", "--allow-empty"],
        input=test_patch, text=True, cwd=work_dir,
    )
    if result.returncode != 0:
        return {"error": "test_patch conflict", "resolved": False}

    # 6. Run tests
    f2p = run_tests(work_dir, entry["FAIL_TO_PASS"])
    p2p = run_tests(work_dir, entry["PASS_TO_PASS"])
```

### What Makes test_patch Tricky

**1. Interface coupling:** Tests import from the agent's code. If the agent uses a different module path, class name, or method signature, imports fail and every test in the file errors.

```python
# test_patch imports:
from app.api.deps import _rate_limiter        # expects this exact name
from app.utils.rate_limiter import RateLimiter # expects this exact path

# If agent puts it in app/middleware/rate_limiter.py → ImportError → 0/8 F2P
```

**2. Assertion specificity:** Tests assert specific field names, status codes, and error messages.

```python
assert resp.status_code == 429
assert "Rate limit exceeded" in resp.json()["error"]
assert "retry-after" in resp.headers
```

If the agent returns `{"message": "Too many requests"}` instead of `{"error": "Rate limit exceeded"}`, the test fails.

**3. Fixture dependency:** Test fixtures create database objects that must match the agent's model schema.

```python
campaign = Campaign(
    brand_id=brand_user.id,
    remaining_budget=10000,  # test expects this field name
    min_fee=500,             # test expects this field name (not min_fee_per_creator)
    ...
)
```

If the agent names the field `budget_remaining` instead of `remaining_budget`, the fixture throws a TypeError on instantiation.

**4. Hunk header accuracy:** The `@@ -0,0 +1,N @@` header must exactly match the number of `+` lines. Any mismatch causes `git apply` to fail with `corrupt patch`, and the entire entry is scored as unresolved.

### FAIL_TO_PASS vs PASS_TO_PASS

| List | Purpose | Contains | Scoring |
|------|---------|----------|---------|
| `FAIL_TO_PASS` | Does the agent's code implement the feature correctly? | Tests from the test_patch (tests that don't exist before the agent runs) | D1: 25 × (passed / total) |
| `PASS_TO_PASS` | Did the agent break any existing functionality? | Tests that already exist in the repo at base_commit | D2: 10 × (passed / total) |

**Resolved = ALL FAIL_TO_PASS pass AND ALL PASS_TO_PASS pass.** Missing even 1 test means the entry is NOT resolved.

**Example — C3-01 (Campaign CRUD):**
- FAIL_TO_PASS: 23 tests (test_create_campaign_success, test_get_campaign_not_found, test_submit_for_review_success, test_pause_campaign_success, ... )
- PASS_TO_PASS: 13 tests (test_create_user_success, test_get_user_not_found, test_list_users_pagination, ... )
- Resolved = 23/23 F2P AND 13/13 P2P → YES

**Example — C3-08 (Rate Limiting):**
- FAIL_TO_PASS: 8 tests (test_rate_limit_allows_normal_usage, test_rate_limit_blocks_after_limit, ... )
- PASS_TO_PASS: 82 tests (all existing campaign, application, content, review, and user tests)
- Resolved = 8/8 F2P AND 82/82 P2P → YES

Amendment entries have many more PASS_TO_PASS tests because the existing codebase is larger.

---

## 3. Submission: How the Agent Is Invoked

Unlike C1/C2 (text-in/text-out), C3 gives the agent **full repo access** and tool capabilities.

### Agent Invocation

```python
agent_result = invoke_agent(
    agent, model,
    entry["problem_statement"],  # the prompt
    work_dir, timeout,
    need_file_writes=True,       # enables file system access
    trajectory_file=traj_file,   # saves full agent trajectory
)
```

For Antigravity (agy), this translates to:

```bash
agy --input-format text \
    --model gemini-3.8-flash-high \
    --output-format stream-json \
    --dangerously-skip-permissions \
    --print-timeout 30m \
    --mode accept-edits \          # auto-approve file writes
    --add-dir /tmp/c3-01-xxxxx/repo  # give agent access to the repo
```

Key differences from C1/C2:
- `--mode accept-edits` — agent can create and modify files without confirmation
- `--add-dir` — agent can browse and edit the repo directory
- `--print-timeout 30m` — long timeout (agents typically take 7-25 minutes per C3 entry)
- The agent runs in the worktree directory, so it sees the full codebase

### What the Agent Can Do

The agent has full coding capabilities:
- **Read** existing files (models, services, schemas, tests)
- **Write** new files (model, repo, service, router, schema)
- **Run** commands (pytest, pip install, python scripts)
- **Iterate** — if tests fail, the agent can fix and re-run
- **Explore** — the agent can grep, find, and understand the codebase

The agent prompt (`problem_statement`) ends with explicit instructions:

```
## Instructions
1. Explore the existing codebase to understand the project structure,
   conventions, and patterns used
2. Implement the required changes following the existing codebase conventions
3. Ensure your implementation matches the technical specification
4. Run existing tests to make sure nothing is broken
5. Your changes should be minimal — only modify what's necessary

Do NOT modify any existing test files.
```

### Agent Patch Capture

After the agent finishes, the harness captures all changes:

```python
def capture_agent_patch(work_dir):
    # 1. Get changes to tracked files
    tracked_diff = git diff HEAD

    # 2. Get list of new (untracked) files
    new_files = git ls-files --others --exclude-standard

    # 3. For each new file, generate a diff
    for f in new_files:
        content = read_file(f)
        # Format as: diff --git a/{f} b/{f}
        #            new file mode 100644
        #            --- /dev/null
        #            +++ b/{f}
        #            @@ -0,0 +1,{line_count} @@
        #            +line1
        #            +line2
        #            ...

    return tracked_diff + untracked_diff
```

The combined patch is saved to `results/patches/C3-01_agy_gemini-3.8-flash-high.patch` and also sent to the LLM judge for code quality review.

---

## 4. Evaluation: Hybrid Automated + LLM-as-Judge

C3 is unique in using **both** automated testing and LLM judging:

| Dimensions | Method | What It Measures |
|-----------|--------|-----------------|
| D1 (Functional Correctness) | Automated — pytest | Does the code work? (FAIL_TO_PASS) |
| D2 (Regression Safety) | Automated — pytest | Did the agent break anything? (PASS_TO_PASS) |
| D3 (Readability) | LLM-as-Judge | Is the code readable and well-named? |
| D4 (Maintainability) | LLM-as-Judge | Is the code modular and well-structured? |
| D5 (Robustness) | LLM-as-Judge | Does the code handle errors and edge cases? |
| D6 (Convention Adherence) | LLM-as-Judge | Does the code follow existing repo patterns? |
| D7 (Change Minimality) | LLM-as-Judge | Are the changes focused and minimal? |

### Automated Scoring (D1–D2)

```python
# D1: Functional Correctness (25 pts) — _score_c3_d1()
rate = f2p_passed / f2p_total
# 100% → 25, ≥80% → 20, ≥60% → 15, ≥30% → 10, <30% → 0

# D2: Regression Safety (10 pts) — _score_c3_d2()
rate = p2p_passed / p2p_total
# 100% → 10, ≥90% → 7, ≥70% → 3, <70% → 0
```

### Gatekeeper Rules

The rubric defines gatekeeper rules for score capping:

| Condition | Effect |
|-----------|--------|
| D1 scores 0 (zero F2P tests pass) | Overall capped at 20 regardless of other dimensions |
| D2 scores 0 (zero P2P tests pass) | Overall capped at 30 |

> **Note:** These gatekeeper rules are defined in the rubric (`score_synthesis.gatekeeper_rules`) but are **not yet enforced** in the current `run_c3()` code. The harness stores D1/D2 tier scores and judge scores independently; capping must be applied during score aggregation.

### LLM Judge Scoring (D3–D7)

The LLM judge receives the **agent's patch** (the diff), not the full files. This is important — the judge evaluates the *changes*, not the entire codebase.

The judge prompt template explicitly tells the judge that D1 and D2 are scored automatically:

```
## Evaluation Task
D1 (Functional Correctness) and D2 (Regression Safety) are scored
automatically via test suites. Evaluate the following code quality
dimensions only:
```

---

## 5. Rubric Design (`c3_codegen.json`) — Full Reference

### Top-Level Fields

```json
{
  "category": "C3",
  "category_name": "Code Understanding & Generation",
  "category_name_zh": "代码理解与生成",
  "evaluation_method": "automated_plus_llm",
  "total_points": 100,
  "pass_threshold": 70,
  "dimensions": [ ... 7 dimensions ... ],
  "score_synthesis": { ... },
  "calibration_persona": "...",
  "agent_prompt_template": "...",
  "judge_prompt_template": "..."
}
```

| Field | Type | Description |
|-------|------|-------------|
| `category` | string | `"C3"` |
| `category_name` | string | `"Code Understanding & Generation"` |
| `evaluation_method` | string | `"automated_plus_llm"` — hybrid of test execution + judge scoring |
| `total_points` | int | `100` |
| `pass_threshold` | int | `70` — higher than C1/C2's 60 because code either works or doesn't |
| `dimensions` | array | 7 dimensions (D1–D7) — 2 automated (D1, D2) + 5 LLM-judged (D3–D7) |
| `score_synthesis` | object | Gatekeeper rules for overall score capping |
| `calibration_persona` | string | Grading instructions for the LLM judge |
| `agent_prompt_template` | string | Template used to construct the agent's prompt (contains `{task_description}` and `{technical_spec_from_c2}` placeholders) |
| `judge_prompt_template` | string | Template for the code quality judge |

**Note:** C3 has TWO templates — `agent_prompt_template` (for the agent) and `judge_prompt_template` (for the judge). C1/C2 only have `judge_prompt_template` because their agent prompts are built in Python code.

---

### `dimensions` Array — All 7 Dimensions

#### D1: Functional Correctness / FAIL_TO_PASS (新功能正确性) — 25 points

| Score | Criteria |
|-------|----------|
| **25** | 100% of FAIL_TO_PASS tests pass. |
| **20** | 80-99% of FAIL_TO_PASS tests pass. Core feature works, minor edge cases missed. |
| **15** | 60-79% of FAIL_TO_PASS tests pass. Main flow works but significant gaps. |
| **10** | 30-59% of FAIL_TO_PASS tests pass. Partial implementation. |
| **0** | < 30% of FAIL_TO_PASS tests pass, or code doesn't parse. |

- **Method:** `automated`
- **Scoring function:** `_score_c3_d1(f2p_passed, f2p_total)` — maps pass rate to tier score

D1 is the primary gating dimension. The rubric defines a gatekeeper rule: D1=0 → overall capped at 20 (not yet enforced in code).

#### D2: Regression Safety / PASS_TO_PASS (回归安全性) — 10 points

| Score | Criteria |
|-------|----------|
| **10** | 100% of PASS_TO_PASS tests still pass. Zero regressions. |
| **7** | 90-99% of PASS_TO_PASS tests pass. 1-2 minor regressions. |
| **3** | 70-89% of PASS_TO_PASS tests pass. Several regressions. |
| **0** | < 70% of PASS_TO_PASS tests pass. Agent broke existing functionality. |

- **Method:** `automated`
- **Scoring function:** `_score_c3_d2(p2p_passed, p2p_total)` — maps pass rate to tier score

D2 catches agents that implement the new feature by accidentally breaking existing modules — e.g., modifying a shared base class, breaking imports, or altering database schema in ways that break existing queries.

#### D3: Readability (可读性) — 15 points

| Score | Criteria |
|-------|----------|
| **15** | Intent-revealing naming that reads like natural language. Consistent formatting matching existing codebase. Docstrings on all public interfaces. Complex logic has inline comments. |
| **12** | Highly readable, consistent formatting, clear naming. Minor gaps in documentation of non-obvious logic. |
| **9** | Mostly readable but some cryptic names (temp, data1, v), or complex algorithms lack inline comments. |
| **6** | Inconsistent naming/casing, large undocumented blocks, confusing layout. |
| **3** | Completely cryptic naming throughout, no comments, messy indentation. |

- **Method:** `llm_as_judge`
- **Hard cap:** Agent uses single-letter variable names in business logic (not loop counters) → `D3 <= 9`

#### D4: Maintainability (可维护性) — 15 points

| Score | Criteria |
|-------|----------|
| **15** | Flawless separation of concerns. Single-responsibility functions (mostly < 20 lines). Clean dependency injection. Loose coupling. Zero copy-pasted logic. |
| **12** | Strong modularity, clear layer boundaries, short functions (mostly < 30 lines), mockable dependencies. |
| **9** | Standard structure but some implementation details leak across layers; a few functions are monolithic or contain duplicate logic blocks. |
| **6** | Monolithic functions (> 80 lines), high cyclomatic complexity (> 15), deep nesting (4+), or systemic copy-pasted code. |
| **3** | Extreme debt: gigantic functions (> 150 lines), God Classes, global mutable state, tight coupling. |

- **Method:** `llm_as_judge`
- **Hard caps:**
  - Any single new file exceeds 500 lines → `D4 <= 9`
  - A single function exceeds 100 lines → `D4 <= 6`
  - Business logic placed directly in API route handlers (bypassing service layer) → `D4 <= 9`

#### D5: Robustness (健壮性) — 15 points

| Score | Criteria |
|-------|----------|
| **15** | Defensive programming throughout. Specific exceptions handled. Safe resource management. No magic constants. Input validation at boundaries. Concurrent safety where applicable. |
| **12** | Strong defensive coding. Specific exceptions handled. Clean resource lifetimes. Minor magic constants (< 2). |
| **9** | Errors handled but generic catch-all blocks common. Some magic constants. Missing validation on 1-2 edge cases. |
| **6** | Silent error swallowing. Manual resource management with leak risks. Bare except: pass in business logic. |
| **3** | Silently swallowed exceptions in critical paths. No input validation. Hardcoded credentials. |

- **Method:** `llm_as_judge`
- **Hard caps:**
  - Bare `except:` or `except Exception: pass` in business logic → `D5 <= 9`
  - Errors in payment/settlement/data-mutation paths silently swallowed → `D5 <= 6`
  - Hardcoded secrets/credentials introduced → `D5 <= 3`

#### D6: Convention Adherence (规范遵循) — 10 points

| Score | Criteria |
|-------|----------|
| **10** | Follows all established repo patterns: repository pattern, service layer, Pydantic schemas, consistent naming (snake_case), proper file placement, imports organized per existing style. New code is indistinguishable from existing code. |
| **8** | Follows most patterns. 1-2 minor deviations. |
| **6** | Follows general structure but notable deviations: putting business logic in API layer, or skipping repository pattern. |
| **4** | Partially follows conventions. Mix of patterns used inconsistently. |
| **2** | Ignores repo conventions entirely. Code works but doesn't fit the codebase. |

- **Method:** `llm_as_judge`
- **Hard cap:** Agent skips the repository pattern entirely (direct DB queries in service or API layer) → `D6 <= 6`

#### D7: Change Minimality (变更最小化) — 10 points

| Score | Criteria |
|-------|----------|
| **10** | Changes are minimal and focused. Only touches files necessary for the task. No unnecessary refactoring, no unrelated changes, no dead code introduced. |
| **8** | Mostly minimal. 1-2 minor unnecessary changes. |
| **6** | Some unnecessary changes: touching files that didn't need modification, or adding unused imports/utilities. |
| **4** | Significant unnecessary changes: refactoring unrelated code, adding helper functions never called. |
| **2** | Massive unnecessary changes that obscure the actual feature implementation. |

- **Method:** `llm_as_judge`

---

### `score_synthesis` — Gatekeeper Rules

```json
{
  "gatekeeper_rules": [
    {
      "condition": "D1 (FAIL_TO_PASS) scores 0",
      "effect": "Overall capped at 20 regardless of other dimensions"
    },
    {
      "condition": "D2 (PASS_TO_PASS) scores 0",
      "effect": "Overall capped at 30"
    }
  ],
  "formula": "Sum of all 7 dimension scores (max 100). D1+D2 anchor the score while D3-D7 differentiate within the functional tier."
}
```

The gatekeeper rules define the intended priority: **correctness first, quality second**. These rules are defined in the rubric for score aggregation but are not yet enforced in `run_c3()` — they should be applied when computing the final composite score.

---

### `calibration_persona`

```
"Grade based on the severity, frequency, and systemic nature of issues.
Avoid leniency bias (being too generous or easily impressed by boilerplate
scaffolding) AND paranoia (being overly punitive for isolated minor issues).
An isolated infraction in an otherwise strong codebase should not drop a
dimension score by more than one tier."
```

**Key difference from C1/C2:** The C3 calibration persona is shorter and more focused. It doesn't adopt a specific role ("senior staff engineer") — it just gives grading instructions. This is because C3 is primarily scored by automated tests; the judge only handles D3-D7 (code quality), which is a narrower evaluation.

---

### `judge_prompt_template` — The Complete Template

```
You are a senior software engineer evaluating the code quality of changes
produced by an AI coding agent for a FastAPI-based campaign collaboration
platform.

## Task Description
The agent was asked to implement the following:
<task>
{task_description}
</task>

## Agent's Code Changes (Diff)
<patch>
{agent_patch}
</patch>

## Calibration
{calibration_persona}

## Hard Capping Rules
Before scoring, check for these conditions that FORCE score limits:
{hard_caps_text}

## Evaluation Task
D1 (Functional Correctness) and D2 (Regression Safety) are scored
automatically via test suites. Evaluate the following code quality
dimensions only:

{dimensions_text}

## Output Format
Respond in JSON:
{
  "hard_cap_triggered": [{"rule": "...", "triggered": true/false}],
  "D3": {"score": 0, "justification": ""},
  "D4": {"score": 0, "justification": ""},
  "D5": {"score": 0, "justification": ""},
  "D6": {"score": 0, "justification": ""},
  "D7": {"score": 0, "justification": ""},
  "total_score": 0,
  "overall_assessment": ""
}
```

#### Placeholder Reference

| Placeholder | Filled By | Content |
|-------------|-----------|---------|
| `{task_description}` | `entry["problem_statement"]` | The full problem statement the agent was given |
| `{agent_patch}` | `capture_agent_patch(work_dir)` | The complete git diff of the agent's changes |
| `{calibration_persona}` | `rubric["calibration_persona"]` | Grading instructions |
| `{hard_caps_text}` | Formatted from hard caps across D3-D7 | All per-dimension hard cap rules |
| `{dimensions_text}` | Formatted from D3-D7 dimensions only (`judge_dims_only=True` filters out D1, D2 which have `method="automated"`) | Tier tables for D3-D7 (all non-automated dimensions) |

**Note:** `judge_dims_only=True` filters out D1 and D2 from the dimensions text sent to the judge, since those are scored automatically.

#### Judge Output Schema

```json
{
  "hard_cap_triggered": [
    {"rule": "Any single new file exceeds 500 lines", "triggered": false},
    {"rule": "A single function exceeds 100 lines", "triggered": false},
    {"rule": "Business logic placed directly in API route handlers", "triggered": false},
    {"rule": "Agent uses bare except: or except Exception: pass", "triggered": false},
    {"rule": "Errors in payment paths silently swallowed", "triggered": false},
    {"rule": "Hardcoded secrets/credentials", "triggered": false},
    {"rule": "Agent skips repository pattern entirely", "triggered": false},
    {"rule": "Single-letter variable names in business logic", "triggered": false}
  ],
  "D3": {"score": 12, "justification": "Clear naming throughout. CampaignService methods are self-documenting. Missing docstrings on repository methods."},
  "D4": {"score": 15, "justification": "Clean separation: Model → Repo → Service → Router. All functions under 30 lines. No copy-pasted logic."},
  "D5": {"score": 12, "justification": "Custom exceptions used consistently (NotFoundError, ForbiddenError, ValidationError). Minor: no validation for empty rejection_reason string."},
  "D6": {"score": 10, "justification": "Follows User module patterns exactly: same file structure, naming, dependency wiring, Pydantic schema style."},
  "D7": {"score": 8, "justification": "Mostly minimal. Added an unused marketplace endpoint not in the spec."},
  "total_score": 57,
  "overall_assessment": "Strong code quality with clean architecture matching existing patterns. Minor gaps in documentation and an unnecessary marketplace endpoint."
}
```

The harness adds D1 + D2 (from test results) to the judge's D3-D7 total for the final score.

---

## 6. C1 → C2 → C3 Pipeline

C3 sits at the end of a three-stage evaluation pipeline:

```
C1: Requirements Understanding
  PM says "we need campaigns"
    → Agent produces structured spec (user stories, edge cases, questions)
    → Scored by LLM judge (100 pts)

C2: Technical Design
  Agent receives structured spec + system context
    → Agent produces technical design (modules, APIs, data model, decisions)
    → Scored by LLM judge (100 pts)

C3: Code Generation
  Agent receives technical spec + full repo access
    → Agent writes working code
    → Scored by automated tests (D1-D2) + LLM judge (D3-D7) = 100 pts
```

Each stage's output becomes the next stage's input. The C3 `problem_statement` is derived from C2's gold standard design. This means if C2's design is wrong, C3's tests would still pass — C3 tests against its OWN spec, not C2's output.

---

## 7. Key Design Decisions

### Why SWE-bench style (not HumanEval)?
HumanEval tests isolated function generation (write `is_palindrome`). Real engineering requires reading existing code, following patterns, and integrating into a system. SWE-bench's worktree + hidden test approach evaluates this end-to-end.

### Why 7 dimensions instead of just "tests pass/fail"?
Two agents can both pass all tests with very different code quality. One writes clean, maintainable code following patterns. Another writes a 300-line god function with bare except blocks. D3-D7 differentiate between them.

### Why is D1 (Functional Correctness) only 25/100?
Because "does it work" is a binary gate, not a spectrum. Either the agent passes the tests or it doesn't. The rubric defines gatekeeper rules (D1=0 → overall ≤ 20) to enforce this priority (not yet applied in current code — intended for score aggregation). The remaining 75 points measure HOW it works — code quality is the differentiator between agents that all pass the tests.

### Why test_patch and not pre-existing tests?
If tests existed in the repo, the agent could read them. SWE-bench's insight: hidden tests force the agent to implement from the SPEC, not reverse-engineer from tests. This measures specification comprehension, not test-driven development.

### Why delete agent-created test files before applying test_patch?
Agents often create their own test files during implementation (good practice!). But if the agent creates `tests/api/test_campaigns.py` and the test_patch also creates `tests/api/test_campaigns.py`, `git apply` fails because the file already exists. The harness deletes agent-created test files at conflicting paths before applying the test_patch. The agent's tests are captured in the agent_patch for reference but not used for scoring.

### Why is pass_threshold 70 for C3 (higher than C1/C2's 60)?
Code either works or it doesn't. A spec that's 60% complete might still be useful. Code that passes 60% of tests is broken. The higher threshold reflects that code has a higher bar for "acceptable."

### Why does C3 have the highest composite weight (30%)?
Code generation is the primary task of a coding agent. Requirements understanding (C1: 15%) and design (C2: 15%) are important but secondary. Code review (C4: 20%) and testing/debugging (C5a: 12%, C5b: 8%) are also important but less central. The 30% weight reflects that C3 is the closest proxy for "can this agent actually write production code?"
