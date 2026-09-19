# C5 Evaluation Guide: Test Generation (C5a) & Debugging (C5b)

## Overview

C5 contains two sub-categories that evaluate complementary engineering skills:

- **C5a (Test Generation)** — Can the agent write a comprehensive, high-quality test suite for an existing module?
- **C5b (Debugging)** — Can the agent diagnose a bug from a report + stack trace and produce a minimal, correct fix?

Both use **hybrid evaluation** (automated + LLM-as-Judge), and both give the agent **full repo access** (like C3). They differ in what the agent produces: C5a produces test code, C5b produces a bug fix.

| Sub-category | Composite Weight | Entries | Agent Receives | Agent Produces |
|-------------|-----------------|---------|---------------|---------------|
| C5a: Test Generation | 12% | 5 entries | Module description + implementation files | Test file (pytest) |
| C5b: Debugging | 8% | 3 entries | Bug report + stack trace + bugged file | Minimal code fix |

---

# Part 1: C5a — Test Generation

## 1.1 Data File Structure

Each C5a entry is a JSON file in `dataset/c5/`. There are 5 entries, one per service module.

```
dataset/c5/
├── C5a-01_campaign_service_tests.json     # Campaign Service (23 gold tests)
├── C5a-02_application_service_tests.json  # Application Service
├── C5a-03_content_service_tests.json      # Content Service
├── C5a-04_review_service_tests.json       # Review Service
└── C5a-05_user_service_tests.json         # User Service
```

### Top-Level Fields

| Field | Type | Purpose |
|-------|------|---------|
| `instance_id` | string | Unique identifier (e.g., `"C5a-01"`) |
| `category` | string | Always `"C5a"` |
| `category_name` | string | `"测试生成"` (Test Generation) |
| `maps_to_journey` | string | Which module is being tested |
| `base_commit` | string | Git commit hash for the worktree |
| `input` | object | **What the agent receives** — module description + file paths + test patterns |
| `gold_standard_tests` | object | **Expert-written test suite** — reference for evaluating completeness |
| `evaluation_config` | object | Scoring configuration (target files, required edge cases) |
| `evaluation_rubric` | string | Path to rubric (`evaluation/rubrics/c5a_testing.json`) |

### `input` Object

| Sub-field | Type | Purpose |
|-----------|------|---------|
| `module_under_test` | string | Natural-language description of what the module does — its responsibilities, business rules, and edge cases |
| `implementation_files` | array | Paths to the source files the agent should test (e.g., `["app/services/campaign_service.py", "app/models/campaign.py", ...]`) |
| `test_target_file` | string | Where the agent should write the test file (e.g., `"tests/api/test_campaigns.py"`) |
| `existing_test_patterns` | string | Description of existing test conventions — frameworks, fixtures, assertion styles, naming patterns |

**Example `input` (C5a-01):**
```json
{
  "module_under_test": "Campaign Service: Full CRUD lifecycle for marketing campaigns with a state-machine workflow. Supports creation (brand-only), update (draft/pending_review only, with auto-reset to draft), six status transitions (submit_for_review, approve, reject, pause, resume, cancel) guarded by role checks and business rules, listing with status filter, and soft-delete restricted to draft campaigns...",

  "implementation_files": [
    "app/services/campaign_service.py",
    "app/models/campaign.py",
    "app/repositories/campaign_repo.py",
    "app/schemas/campaign.py"
  ],

  "test_target_file": "tests/api/test_campaigns.py",

  "existing_test_patterns": "Tests use pytest-asyncio with an httpx AsyncClient hitting the FastAPI app. Fixtures create domain objects directly via SQLAlchemy (db_session.add + flush). A helper function _campaign_payload() builds valid JSON payloads with **overrides for negative cases..."
}
```

### `gold_standard_tests` Object

The expert-written test suite serves as a reference — not an answer key. The agent doesn't need to match it exactly.

```json
{
  "test_file_path": "tests/api/test_campaigns.py",
  "test_count": 23,
  "line_coverage": "estimated ~90%",
  "branch_coverage": "estimated ~80%",
  "edge_cases_covered": [
    "Missing required field (title) returns 422",
    "Budget less than min_fee returns 422",
    "Invalid deadline ordering (application >= content) returns 422",
    "Non-brand user cannot create campaign (403)",
    "Get non-existent campaign returns 404 with 'not found' message",
    "Update by non-owner returns 403",
    "Update active campaign returns 422 (only draft/pending_review editable)",
    "Editing pending_review campaign resets status to draft",
    "Approve requires admin role (403 for brand user)",
    "Reject requires rejection_reason (422 without it)",
    "Invalid state transition (pause from draft) returns 422",
    "Delete active campaign returns 422 (draft-only)",
    "Delete draft campaign returns 204 and subsequent GET returns 404"
  ]
}
```

### `evaluation_config` Object

```json
{
  "target_module_files": [
    "app/services/campaign_service.py",
    "app/models/campaign.py"
  ],
  "min_acceptable_coverage": 60,
  "required_edge_cases": [
    "Budget validation: total_budget must be >= min_fee",
    "Deadline ordering: application_deadline < content_deadline < publish_deadline",
    "State machine: valid transition (draft -> pending_review)",
    "State machine: invalid transition returns error",
    "Ownership check: non-owner cannot update or delete",
    "Draft-only deletion: cannot delete non-draft campaigns",
    "Pending_review edit resets status to draft",
    "Reject requires rejection_reason",
    "Approve requires admin role"
  ]
}
```

---

## 1.2 Submission: How the Agent Is Invoked

C5a gives the agent **full repo access** — the agent can read implementation files, browse conftest, run tests, and iterate.

### Prompt Construction

```python
def build_prompt_c5a(entry, work_dir):
    inp = entry["input"]
    # Read actual implementation files from the worktree
    impl_content = ""
    for fpath in inp.get("implementation_files", []):
        full = work_dir / fpath
        if full.exists():
            impl_content += f"\n### {fpath}\n```python\n{full.read_text()}\n```\n"

    return (
        f"You are a senior QA engineer writing comprehensive tests.\n\n"
        f"## Module Under Test\n{inp['module_under_test']}\n\n"
        f"## Implementation Files\n{impl_content}\n"
        f"## Existing Test Patterns\n{inp['existing_test_patterns']}\n"
        f"## Task\n"
        f"Write a comprehensive pytest test suite for the module. "
        f"Target file: `{inp['test_target_file']}`\n\n"
        f"Requirements:\n"
        f"1. Cover all public methods/endpoints\n"
        f"2. Test success paths and error paths\n"
        f"3. Test edge cases and boundary conditions\n"
        f"4. Follow the existing test patterns (async, fixtures, httpx)\n"
        f"5. Each test should be independent and self-contained\n\n"
        f"Write the test file directly."
    )
```

**Key detail:** The prompt includes the **actual source code** of the implementation files, read from the worktree at runtime. The agent sees the exact code it needs to test.

### Agent Invocation

```bash
agy --input-format text \
    --model gemini-3.8-flash-high \
    --output-format stream-json \
    --dangerously-skip-permissions \
    --mode accept-edits \
    --add-dir /tmp/c5a-xxxxx/repo
```

The agent has full tool access — it can:
- Read implementation files and conftest.py
- Write the test file to the target path
- Run pytest to verify tests pass
- Iterate on failing tests

---

## 1.3 Evaluation: How C5a Is Scored

### Automated Phase

After the agent finishes, the harness runs the agent's test file:

```python
result = subprocess.run(
    ["python3", "-m", "pytest", str(test_file), "-v", "--tb=short"],
    cwd=work_dir, capture_output=True, text=True, timeout=120,
)
```

The harness counts how many tests pass vs fail/error. This feeds into the scoring.

### LLM Judge Phase

The agent's test code + execution results are sent to an LLM judge for D2-D5 scoring:

```python
judge_result = build_judge_payload("c5a", rubric, entry, test_code,
    extra_replacements={
        "module_under_test": entry["input"]["module_under_test"],
        "agent_test_code": test_code,
        "test_results_summary": f"{pass_count}/{test_count} tests passed",
    },
    judge_dims_only=True)
```

---

## 1.4 C5a Rubric (`c5a_testing.json`) — Full Reference

### Top-Level Fields

```json
{
  "category": "C5a",
  "category_name": "Test Generation",
  "category_name_zh": "测试生成",
  "evaluation_method": "automated_plus_llm",
  "total_points": 100,
  "pass_threshold": 60
}
```

### `dimensions` Array — All 5 Dimensions

#### D1: Coverage (测试覆盖率) — 50 points

| Score | Criteria |
|-------|----------|
| **50** | 100% pass rate AND test count >= gold_test_count. All agent-written tests pass and the suite is comprehensive. |
| **40** | 100% pass rate but test count < gold_test_count. All tests pass but coverage is incomplete. |
| **30** | Pass rate >= 80%. Most tests pass, a few failures. |
| **20** | Pass rate 50-79%. Significant test failures. |
| **10** | Pass rate < 50%, OR fewer than 5 tests written. |

- **Method:** `automated` (via `pytest`)
- **Tool:** pytest

**How it works:** The harness runs `pytest <test_file> -v --tb=short`, counts PASSED vs FAILED/ERROR, and calls `_score_c5a_d1(pass_count, test_count, gold_test_count)` to compute the tier score. Tier scores are read from `c5a_testing.json` rubric via `_get_tiers("c5a", "D1")`. The `gold_test_count` is read from `gold_standard_tests.test_count` in the data file — if the agent writes significantly fewer tests than the gold standard, it scores 40 instead of 50 even with 100% pass rate.

**Single source of truth:** All tier scores (both automated and judge-scored) are defined in `evaluation/rubrics/c5a_testing.json`. The automated scoring function reads tier values via `_get_tiers()`. Judge-returned scores for D2–D5 are validated and snapped to the nearest valid rubric tier via `validate_judge_scores()`.

**What it measures:** Can the agent write tests that actually run? A test file full of import errors or assertion failures indicates the agent doesn't understand the code it's testing. Pass rate is the foundation — broken tests can't catch bugs.

#### D2: Assertion Quality (断言质量) — 18 points

| Score | Criteria |
|-------|----------|
| **18** | Every test has specific, meaningful assertions (exact value checks, not just "no exception"). Asserts cover return values, state changes, side effects, AND error conditions. Uses appropriate assertion methods. |
| **14** | Good assertions covering return values and error conditions. Minor gaps in side-effect verification. |
| **10** | Assertions present but some are weak (assert result is not None instead of checking actual value). Error conditions partially tested. |
| **7** | Many tests just check "no exception raised". Few meaningful value assertions. |
| **3** | Trivial assertions only (assert True, assert response.status_code == 200 without body checks). |

- **Method:** `llm_as_judge`

**What it measures:** Are the tests actually checking the right things? A test that calls the endpoint but only asserts `status_code == 200` without checking the response body has no teeth — it won't catch data corruption bugs. Good assertions check specific values: `assert body["status"] == "draft"`, `assert body["remaining_budget"] == "10000.00"`.

#### D3: Edge Case Coverage (边界场景覆盖) — 14 points

| Score | Criteria |
|-------|----------|
| **14** | Tests cover: empty inputs, boundary values (min/max), error conditions (invalid input, not found, permission denied), concurrent operations (if applicable), and at least 2 non-obvious edge cases specific to the business logic. |
| **11** | Tests cover most common edge cases (empty input, not found, permission). 1 non-obvious case. |
| **8** | Some edge cases covered but gaps in error conditions or boundary values. |
| **5** | Only happy path + 1-2 obvious error cases (e.g., 404). |
| **3** | Happy path only. No edge cases. |

- **Method:** `llm_as_judge`

**What it measures:** Does the agent think about what can go wrong? Testing `create_campaign_success` is easy. Testing `create_campaign_with_budget_less_than_min_fee` requires understanding the business rule. Testing `editing_pending_review_campaign_resets_status_to_draft` requires understanding the state machine's reset behavior — a non-obvious edge case.

#### D4: Test Independence & Structure (测试独立性与结构) — 11 points

| Score | Criteria |
|-------|----------|
| **11** | All tests pass individually and in any order. Proper setup/teardown. Each test tests one thing. Clear naming pattern. Tests use existing conftest.py fixtures. |
| **9** | Tests independent and structured. Minor issues. |
| **6** | Mostly independent but some shared mutable state or order dependencies. |
| **4** | Test isolation issues: shared state, order-dependent tests. |
| **2** | Tests tightly coupled, can't run individually, or fragile. |

- **Method:** `llm_as_judge`

**What it measures:** Can each test run in isolation? Order-dependent tests are the #1 cause of flaky CI. Each test should create its own data (via fixtures), assert its own expectations, and not depend on side effects from other tests.

#### D5: Convention Adherence (规范遵循) — 7 points

| Score | Criteria |
|-------|----------|
| **7** | Follows existing test patterns: uses pytest, uses conftest fixtures, follows file naming (test_<module>.py), uses existing test client and DB fixtures, consistent mock patterns. |
| **5** | Mostly follows conventions. 1 minor deviation. |
| **4** | Partially follows conventions. Uses pytest but doesn't leverage existing fixtures. |
| **2** | Uses different testing patterns (e.g., unittest.TestCase when repo uses pytest functions). |
| **1** | Completely different testing style. Ignores existing test infrastructure. |

- **Method:** `llm_as_judge`

**What it measures:** Does the agent write tests that fit the existing codebase? The repo uses pytest-asyncio with httpx AsyncClient and SQLAlchemy fixtures. An agent that writes unittest.TestCase with requests.Session is technically functional but doesn't fit. The LLM judge evaluates convention adherence by comparing the agent's test code against the repo's established patterns (naming, fixtures, class structure, import style).

---

### `judge_prompt_template` (C5a)

```
You are a senior QA engineer evaluating the quality of a test suite
produced by an AI coding agent for a FastAPI-based campaign collaboration
platform.

## Module Under Test
{module_under_test}

## Agent's Test Code
<test_code>
{agent_test_code}
</test_code>

## Test Execution Results
{test_results_summary}

## Calibration
{calibration_persona}

## Evaluation Task
D1 (Coverage) is scored automatically.
Evaluate the following test quality dimensions only:

{dimensions_text}

## Output Format
Respond in JSON:
{
  "D2": {"score": 0, "justification": ""},
  "D3": {"score": 0, "justification": ""},
  "D4": {"score": 0, "justification": ""},
  "D5": {"score": 0, "justification": ""},
  "total_score": 0,
  "overall_assessment": ""
}
```

| Placeholder | Filled By | Content |
|-------------|-----------|---------|
| `{module_under_test}` | `entry["input"]["module_under_test"]` | What the module does (business rules, responsibilities) |
| `{agent_test_code}` | `test_file.read_text()` | The agent's full test file content |
| `{test_results_summary}` | `f"{pass_count}/{test_count} tests passed"` | Execution results |
| `{calibration_persona}` | `rubric["calibration_persona"]` | Senior QA engineer grading persona — avoid leniency for shallow assertions, avoid paranoia for minor style deviations |
| `{dimensions_text}` | D2-D5 tier tables (judge_dims_only=True) | Only the LLM-judged dimensions |

---

## 1.5 C5a End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. WORKTREE: git worktree add at base_commit                    │
│    Agent gets full repo with all implementation code             │
│                                                                 │
│ 2. PROMPT: build_prompt_c5a(entry, work_dir)                    │
│    Includes actual source code of implementation files           │
│    + module description + existing test patterns                 │
│                                                                 │
│ 3. AGENT: Runs with full tool access                             │
│    Reads conftest.py, existing tests, implementation files       │
│    Writes test file to test_target_file path                     │
│    Runs pytest to verify tests pass, iterates if needed          │
│                                                                 │
│ 4. RUN TESTS: pytest test_file -v --tb=short                    │
│    Count passed/failed → _score_c5a_d1(pass, total, gold) → D1  │
│                                                                 │
│ 5. LLM JUDGE: Evaluate D2 (assertions), D3 (edge cases),        │
│    D4 (independence), D5 (conventions) from test code + results  │
│                                                                 │
│ 6. SCORE: D1 (automated) + D2-D5 (judge) = /100                │
└─────────────────────────────────────────────────────────────────┘
```

---

# Part 2: C5b — Debugging

## 2.1 Data File Structure

Each C5b entry is a JSON file in `dataset/c5/`. There are 3 entries, each with a different bug type.

```
dataset/c5/
├── C5b-01_off_by_one_deadline.json        # Off-by-one: < vs <= in deadline comparison
├── C5b-02_toctou_duplicate_application.json  # TOCTOU: race condition in duplicate check
└── C5b-03_null_check_revision.json        # Null check: missing None guard on revision
```

### Top-Level Fields

| Field | Type | Purpose |
|-------|------|---------|
| `instance_id` | string | Unique identifier (e.g., `"C5b-01"`) |
| `category` | string | Always `"C5b"` |
| `category_name` | string | `"调试"` (Debug) |
| `base_commit` | string | Git commit hash for the worktree |
| `input` | object | **What the agent receives** — bug report, stack trace, bugged file |
| `gold_standard` | object | **Expert diagnosis and fix** — root cause, fix diff, explanation, test lists |
| `test_patch` | string | **Hidden test** — git diff injected after agent fixes the bug |
| `evaluation_rubric` | string | Path to rubric (`evaluation/rubrics/c5b_debug.json`) |

### `input` Object

| Sub-field | Type | Purpose |
|-----------|------|---------|
| `bug_report` | string | Natural-language description of the bug — what was expected, what happened, reproduction scenario |
| `stack_trace` | string | The failing test output with assertion error, line numbers, and response details |
| `bugged_file` | string | Path to the file containing the bug (e.g., `"app/services/campaign_service.py"`) |
| `bugged_code` | string | The full source code of the bugged file — injected into the worktree before the agent starts |

**Example `input` (C5b-01, Off-by-One Bug):**
```json
{
  "bug_report": "Campaign with expired deadline (exactly at current time) was successfully resumed. A brand user paused their campaign, and the application_deadline is now exactly equal to the current UTC time. When the brand tries to resume the campaign, the system should reject the request because the deadline has passed (or is at the boundary). Instead, the campaign was successfully transitioned back to 'active' status.",

  "stack_trace": "FAILED tests/api/test_campaigns.py::test_resume_campaign_expired_deadline_boundary\n\n    >   assert response.status_code == 422\n    E   assert 200 == 422\n    ...",

  "bugged_file": "app/services/campaign_service.py",

  "bugged_code": "...if campaign.application_deadline < now:..."
}
```

The bug is subtle: `<` (strict less-than) instead of `<=` (less-than-or-equal). When the deadline is *exactly* equal to `now`, `<` returns False, and the resume is allowed.

### `gold_standard` Object

The expert diagnosis serves as the reference for scoring:

```json
{
  "root_cause": "Off-by-one error in the resume deadline comparison. The condition uses strict less-than (<) instead of less-than-or-equal (<=). When campaign.application_deadline is exactly equal to now, the strict < evaluates to False, allowing the campaign to be resumed.",

  "fix_diff": "--- a/app/services/campaign_service.py\n+++ b/app/services/campaign_service.py\n@@ -154,7 +154,7 @@\n-            if campaign.application_deadline < now:\n+            if campaign.application_deadline <= now:",

  "fix_explanation": "Change the comparison operator from < to <= so that campaigns whose application_deadline is exactly equal to the current time are also prevented from being resumed.",

  "FAIL_TO_PASS": [
    "tests/api/test_campaigns.py::test_resume_campaign_expired_deadline_boundary"
  ],

  "PASS_TO_PASS": [
    "tests/api/test_campaigns.py::test_create_campaign_success",
    "tests/api/test_campaigns.py::test_submit_for_review_success",
    "tests/api/test_campaigns.py::test_approve_campaign_success",
    "tests/api/test_campaigns.py::test_pause_campaign_success",
    "tests/api/test_campaigns.py::test_cancel_campaign_success",
    "tests/api/test_campaigns.py::test_invalid_status_transition",
    "tests/api/test_campaigns.py::test_delete_campaign_success"
  ]
}
```

| Field | Type | Purpose |
|-------|------|---------|
| `root_cause` | string | The technical root cause — exact line, bug type, and mechanism |
| `fix_diff` | string | The minimal fix as a unified diff (often just 1-2 lines changed) |
| `fix_explanation` | string | Why the fix resolves the issue |
| `FAIL_TO_PASS` | array | Test(s) that reproduce the bug — must pass after the fix |
| `PASS_TO_PASS` | array | Existing tests that must still pass (no regressions) |

### `test_patch` — Hidden Test Injection

Like C3, C5b uses a test_patch to inject the failing test **after** the agent fixes the bug. This ensures the agent fixes the actual bug, not just makes a test disappear.

```diff
diff --git a/tests/api/test_campaigns.py b/tests/api/test_campaigns.py
index bd80512..014c9dd 100644
--- a/tests/api/test_campaigns.py
+++ b/tests/api/test_campaigns.py
@@ -401,3 +401,38 @@ async def test_delete_campaign_success(
...
+@pytest.mark.asyncio
+async def test_resume_campaign_expired_deadline_boundary(
+    client, db_session, sample_brand
+):
+    frozen_now = datetime(2030, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
+    campaign = Campaign(
+        ...
+        application_deadline=frozen_now,
+        status=CampaignStatus.PAUSED,
+    )
+    ...
+    mock_dt = MagicMock(wraps=datetime)
+    mock_dt.now.return_value = frozen_now
+    with patch("app.services.campaign_service.datetime", mock_dt):
+        resp = await client.post(...)
+    assert resp.status_code == 422
```

Note how this test uses `unittest.mock.patch` to freeze `datetime.now()` to the exact deadline value, creating the boundary condition that triggers the off-by-one bug.

### Bug Types Across C5b Entries

| Entry | Bug Type | Subtlety | Fix Size |
|-------|---------|----------|----------|
| C5b-01 | Off-by-one (`<` vs `<=`) | Boundary condition on datetime comparison | 1 character |
| C5b-02 | TOCTOU race condition | Check-then-act on duplicate application without atomicity | ~5 lines |
| C5b-03 | Missing null check | Accessing `.revision_count` on a potentially None object | 2-3 lines |

The bugs are deliberately chosen to represent common real-world debugging scenarios — not exotic corner cases.

---

## 2.2 Submission: How the Agent Is Invoked

### Worktree Setup with Bug Injection

C5b has a unique setup step: the bugged code is **injected** into the worktree:

```python
setup_worktree(base_commit, work_dir)

# Inject the bugged code into the worktree
bugged_file = work_dir / entry["input"]["bugged_file"]
bugged_file.parent.mkdir(parents=True, exist_ok=True)
bugged_file.write_text(entry["input"]["bugged_code"])
```

This replaces the correct version of the file with the bugged version. The agent sees the repo with the bug already present.

### Prompt Construction

```python
def build_prompt_c5b(entry):
    inp = entry["input"]
    return (
        f"You are a senior software engineer debugging a production issue.\n\n"
        f"## Bug Report\n{inp['bug_report']}\n\n"
        f"## Stack Trace\n```\n{inp.get('stack_trace', 'N/A')}\n```\n\n"
        f"## Bugged File\n"
        f"The bug is in `{inp['bugged_file']}` in this codebase.\n\n"
        f"## Task\n"
        f"1. Read the file `{inp['bugged_file']}` in the current workspace\n"
        f"2. Identify the root cause of the bug\n"
        f"3. Fix the bug by editing the file directly\n"
        f"4. Make minimal changes — fix only the bug, do not refactor\n"
    )
```

The agent receives:
- A bug report describing the symptom
- A stack trace showing the failing test
- A hint about which file contains the bug
- Instructions to fix minimally

The agent then has full repo access to read the bugged file, understand the code, make the fix, and run tests to verify.

---

## 2.3 Evaluation: How C5b Is Scored

### Step-by-Step

```
1. WORKTREE SETUP + BUG INJECTION
   ┌──────────────────────────────────────────────────────────┐
   │ git worktree add at base_commit                          │
   │ Overwrite bugged_file with bugged_code                   │
   │ State: repo has the bug                                  │
   └──────────────────────────────────────────────────────────┘
                         ↓
2. AGENT RUNS
   ┌──────────────────────────────────────────────────────────┐
   │ Agent reads bug report, stack trace                      │
   │ Agent reads the bugged file                              │
   │ Agent diagnoses root cause                               │
   │ Agent edits the file to fix the bug                      │
   │ Agent runs tests to verify fix                           │
   └──────────────────────────────────────────────────────────┘
                         ↓
3. CAPTURE AGENT PATCH
   ┌──────────────────────────────────────────────────────────┐
   │ git diff HEAD → agent's fix as a patch                   │
   └──────────────────────────────────────────────────────────┘
                         ↓
4. APPLY test_patch (inject hidden boundary test)
   ┌──────────────────────────────────────────────────────────┐
   │ git apply test_patch                                     │
   │ Adds the FAIL_TO_PASS test to the test file              │
   └──────────────────────────────────────────────────────────┘
                         ↓
5. RUN TESTS + AUTOMATED SCORING
   ┌──────────────────────────────────────────────────────────┐
   │ FAIL_TO_PASS: Does the fix resolve the bug?              │
   │ PASS_TO_PASS: Did the fix break anything else?           │
   │ resolved = all F2P pass AND all P2P pass                 │
   │ D2 score = _score_c5b_d2(f2p, p2p) → /50                │
   │ D3 score = _score_c5b_d3(agent_patch, gold_fix) → /20   │
   └──────────────────────────────────────────────────────────┘
                         ↓
6. LLM JUDGE (D1 root cause, D4 explanation)
   ┌──────────────────────────────────────────────────────────┐
   │ Judge reviews: agent's response + patch + gold standard   │
   │ Scores D1 (Root Cause) and D4 (Explanation Quality)       │
   └──────────────────────────────────────────────────────────┘
```

---

## 2.4 C5b Rubric (`c5b_debug.json`) — Full Reference

### Top-Level Fields

```json
{
  "category": "C5b",
  "category_name": "Debug",
  "category_name_zh": "调试",
  "evaluation_method": "automated_plus_llm",
  "total_points": 100,
  "pass_threshold": 60
}
```

### `dimensions` Array — All 4 Dimensions

#### D1: Root Cause Identification (根因定位) — 20 points

| Score | Criteria |
|-------|----------|
| **20** | Correctly identifies the exact root cause: the specific line(s) of code, the nature of the bug (off-by-one, race condition, missing error handling), and why it produces the observed symptom. |
| **16** | Identifies the correct area and type of bug but slightly imprecise about the exact mechanism. |
| **12** | Identifies the correct file/function but mischaracterizes the bug type, or identifies the symptom but not the underlying cause. |
| **8** | Partially correct: right area but wrong diagnosis. Would lead to a fix that might mask the bug but not truly resolve it. |
| **4** | Incorrect root cause identification. Points to the wrong code or wrong type of issue. |

- **Method:** `llm_as_judge`

**What it measures:** Can the agent think like a debugger? Saying "the resume check is wrong" is 12/20. Saying "line 154: the comparison `campaign.application_deadline < now` uses strict less-than, which allows resume when deadline == now; this is an off-by-one boundary error that should use `<=`" is 20/20. The diagnosis must explain the mechanism, not just point to the area.

#### D2: Fix Correctness (修复正确性) — 50 points

| Score | Criteria |
|-------|----------|
| **50** | All FAIL_TO_PASS tests pass AND all PASS_TO_PASS tests pass. Fix resolves the issue completely. |
| **40** | FAIL_TO_PASS tests pass but 1 PASS_TO_PASS test regressed (minor side effect). |
| **30** | Most FAIL_TO_PASS tests pass (70%+). Core issue resolved but edge cases may remain. |
| **20** | Partial fix: immediate symptom addressed but underlying issue can still trigger under different conditions. |
| **10** | Fix doesn't resolve the issue. Tests still fail, or new failures introduced. |

- **Method:** `automated`
- **Scoring:** The harness computes D2 tier score from F2P/P2P test results using `_score_c5b_d2()`:
  - 50 pts: All F2P pass AND all P2P pass
  - 40 pts: All F2P pass, at most 1 P2P regression
  - 30 pts: ≥70% F2P pass
  - 20 pts: At least 1 F2P pass
  - 10 pts: No F2P pass or no tests

**The highest-weighted dimension (50 pts).** In debugging, the fix either works or it doesn't. A beautiful diagnosis with a wrong fix is less valuable than a terse diagnosis with a correct fix. The 50-point weight reflects this priority.

#### D3: Fix Minimality (修复最小化) — 20 points

| Score | Criteria |
|-------|----------|
| **20** | Fix is surgical: changes only the lines necessary. No refactoring, no unrelated changes, no "while I'm here" improvements. |
| **16** | Fix is focused but includes 1-2 minor unnecessary changes. |
| **12** | Fix is correct but includes some unnecessary refactoring or defensive coding beyond what's needed. |
| **8** | Significant unnecessary changes that obscure the actual fix. |
| **4** | Major rewrite instead of targeted fix. |

- **Method:** `automated`
- **Scoring:** The harness computes D3 tier score from patch size ratio using `_score_c5b_d3()`. It compares the number of changed lines in the agent's patch vs the gold fix diff:
  - 20 pts: ratio ≤ 2× gold fix (surgical)
  - 16 pts: ratio ≤ 4× (focused with minor extras)
  - 12 pts: ratio ≤ 8× (some unnecessary changes)
  - 8 pts: ratio ≤ 15× (significant extras)
  - 4 pts: ratio > 15× (major rewrite)

**What it measures:** Did the agent fix the bug, or did it rewrite the function? The ideal fix for C5b-01 is changing one character: `<` → `<=`. An agent that refactors the entire `transition_status` method to fix a one-character bug is over-engineering.

**Single source of truth:** All tier scores (both automated and judge-scored) are defined in `evaluation/rubrics/c5b_debug.json`. Automated scoring functions read tier values via `_get_tiers()`. Judge-returned scores for D1 and D4 are validated and snapped to the nearest valid rubric tier via `validate_judge_scores()`.

#### D4: Explanation Quality (诊断解释质量) — 10 points

| Score | Criteria |
|-------|----------|
| **10** | Explanation clearly describes: (1) what the bug is, (2) why the current code produces the wrong behavior (step-by-step reasoning), (3) why the fix resolves it, and (4) whether similar patterns exist elsewhere. Demonstrates deep understanding. |
| **8** | Clear explanation of the bug and fix. Missing either the step-by-step reasoning or the similar-pattern analysis. |
| **6** | Explains what was changed but not deeply why the original code was wrong. Surface-level understanding. |
| **4** | Minimal explanation. "Changed X to Y" without reasoning. |
| **2** | No explanation or incorrect explanation that contradicts the actual fix. |

- **Method:** `llm_as_judge`

**What it measures:** Can the agent communicate its diagnosis? The 10-point weight rewards agents that not only fix the bug but explain it clearly enough that a human reviewer can verify the fix is correct. The highest tier (10 pts) specifically looks for "whether similar patterns exist elsewhere" — demonstrating that the agent thinks beyond the immediate fix.

---

### `judge_prompt_template` (C5b)

```
You are a senior software engineer evaluating an AI coding agent's
debugging performance on a FastAPI-based campaign collaboration platform.

## Bug Report
<bug_report>
{bug_report}
</bug_report>

## Bugged Code (Original)
<bugged_code>
{bugged_code}
</bugged_code>

## Agent's Response
<agent_response>
{agent_response}
</agent_response>

## Agent's Fix (Diff)
<patch>
{agent_patch}
</patch>

## Reference Fix (Gold Standard)
<reference>
{gold_fix}
</reference>

## Calibration
{calibration_persona}

## Evaluation Task
D2 (Fix Correctness) and D3 (Fix Minimality) are scored automatically
via test suites. Evaluate the following dimensions only:

{dimensions_text}

## Output Format
Respond in JSON:
{
  "D1": {"score": 0, "justification": ""},
  "D4": {"score": 0, "justification": ""},
  "total_score": 0,
  "overall_assessment": ""
}
```

| Placeholder | Filled By | Content |
|-------------|-----------|---------|
| `{bug_report}` | `entry["input"]["bug_report"]` | The bug report the agent received |
| `{bugged_code}` | `entry["input"]["bugged_code"]` | The full source of the bugged file |
| `{agent_response}` | Agent's captured text response | The agent's diagnosis and explanation |
| `{agent_patch}` | `capture_agent_patch(work_dir)` | The diff of the agent's fix |
| `{gold_fix}` | `json.dumps(gold_standard)` | Expert root cause + fix diff + explanation |
| `{calibration_persona}` | `rubric["calibration_persona"]` | Senior engineer grading persona — avoid leniency for shallow explanations, avoid paranoia for imprecise root cause descriptions |
| `{dimensions_text}` | D1 + D4 tier tables (judge_dims_only=True) | Only the LLM-judged dimensions |

---

# Part 3: C5a vs C5b Comparison

| Aspect | C5a (Test Generation) | C5b (Debugging) |
|--------|----------------------|-----------------|
| **Skill tested** | Writing comprehensive tests | Diagnosing and fixing bugs |
| **Input** | Module description + implementation files | Bug report + stack trace + bugged file |
| **Output** | Complete test file | Minimal code fix + diagnosis |
| **Dimensions** | 5 (Coverage, Assertions, Edge Cases, Independence, Conventions) | 4 (Root Cause, Fix Correctness, Minimality, Explanation) |
| **Automated scoring** | D1 (coverage) | D2 (test pass/fail), D3 (patch size) |
| **LLM-judged** | D2 (assertions), D3 (edge cases), D4 (structure), D5 (conventions) | D1 (root cause), D4 (explanation) |
| **Highest-weighted dim** | D1: Coverage (50 pts) | D2: Fix Correctness (50 pts) |
| **test_patch used?** | No — agent writes the tests | Yes — injects the failing test after agent fixes |
| **Entries** | 5 (one per service module) | 3 (one per bug type) |
| **Composite weight** | 12% | 8% |
| **Combined C5 weight** | 20% total | |

---

# Part 4: Key Design Decisions

### Why separate Test Generation and Debugging?
They test fundamentally different skills. Test generation is *anticipatory* — thinking about what could go wrong. Debugging is *reactive* — given a symptom, finding the cause. A good coding agent needs both.

### Why does C5a give the agent the implementation code in the prompt?
The agent needs to know what the code does to test it. Unlike C3 where the agent writes the code and therefore knows it, C5a asks the agent to test someone else's code. Including the source in the prompt ensures the agent has the information needed to write meaningful assertions, not just generic smoke tests.

### Why only 3 C5b entries?
Each C5b entry takes the agent 5-25 minutes to solve. More importantly, each entry tests a distinct debugging archetype (boundary condition, race condition, null reference) — adding more entries of the same type wouldn't add evaluation value. Three well-designed bugs cover the core debugging skill space.

### Why is Fix Correctness (D2) the highest-weighted C5b dimension at 50 points?
In debugging, the fix either works or it doesn't. A brilliantly articulated root cause analysis (D1) combined with a fix that doesn't actually resolve the bug is useless. The 50-point weight ensures that agents which produce correct fixes always outscore agents that produce beautiful explanations with wrong fixes.

### Why does C5b use test_patch like C3?
The agent might "fix" the bug by deleting the test or modifying the test assertion. By injecting the test after the agent finishes (via test_patch), we ensure the fix is verified against a test the agent never saw and couldn't tamper with.

### Why 12% + 8% = 20% combined weight for C5?
Testing and debugging are essential engineering skills but less central than code generation (C3: 30%) and code review (C4: 20%). The 20% combined weight reflects their importance while keeping the composite score anchored on the primary tasks. C5a gets 12% (higher) because test generation is a more common agent use case than debugging.
