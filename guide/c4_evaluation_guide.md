# C4 Evaluation Guide: Code Review

## Overview

C4 tests whether a coding agent can perform a **thorough, accurate code review** — detecting planted defects in a pull request diff, classifying them correctly, localizing them precisely, and explaining the root cause with actionable fix suggestions.

Unlike C1–C3 which ask the agent to *produce* artifacts (specs, designs, code), C4 asks the agent to *critique* someone else's code. This evaluates a fundamentally different skill: the ability to read code skeptically, reason about what could go wrong, and communicate findings clearly.

C4 uses a **hybrid evaluation**: automated matching of findings against planted defects (D1–D2) + LLM-as-Judge for localization, classification, and explanation (D3–D5). The matching logic is inspired by [AACR-Bench](https://arxiv.org/abs/2401.05649) (Automated Assessment of Code Reviews) and uses **LLM semantic matching** to determine if a finding addresses the same issue as a planted defect.

---

## 1. Data File Structure

Each C4 entry is a JSON file in `dataset/c4/`. There are 8 entries, one per code module.

```
dataset/c4/
├── C4-01_campaign_crud.json         # Campaign CRUD (3 planted defects)
├── C4-02_application_flow.json      # Application flow
├── C4-03_content_submission.json    # Content submission
├── C4-04_review_workflow.json       # Review workflow
├── C4-05_settlement.json           # Settlement
├── C4-06_campaign_search.json       # Campaign search
├── C4-07_application_ranking.json   # Application ranking
└── C4-08_rate_limiting.json         # Rate limiting
```

### Top-Level Fields

| Field | Type | Purpose |
|-------|------|---------|
| `instance_id` | string | Unique identifier (e.g., `"C4-01"`) |
| `category` | string | Always `"C4"` |
| `category_name` | string | `"代码评审"` (Code Review) |
| `maps_to_journey` | string | Which business journey this entry covers |
| `base_commit` | string | Git commit (for context, not used for worktree in C4) |
| `input` | object | **What the agent receives** — the PR diff with bugs planted in it |
| `planted_defects` | array | **Ground truth** — the deliberately injected bugs with full metadata |
| `evaluation_config` | object | Summary stats: total defects, by category, by severity |
| `evaluation_rubric` | string | Path to rubric file (`evaluation/rubrics/c4_review.json`) |

### `input` Object — The PR Being Reviewed

| Sub-field | Type | Purpose |
|-----------|------|---------|
| `pr_title` | string | The pull request title (e.g., `"feat: implement campaign CRUD with state machine"`) |
| `pr_description` | string | PR description written as if by a real developer — explains what was implemented, what patterns were followed |
| `bugged_diff` | string | A **complete git diff** of the "PR" — this is code that LOOKS correct but has **deliberate bugs planted** in it |

**Example `input` (C4-01):**
```json
{
  "pr_title": "feat: implement campaign CRUD with state machine",
  "pr_description": "Implements full campaign lifecycle management...\n\n## Changes\n- New Campaign model with 7-state machine...\n- CampaignRepository with CRUD + filtering...\n- CampaignService with business logic...\n\n## Follows existing patterns\n- Repository pattern (UserRepository reference)...",
  "bugged_diff": "diff --git a/app/api/v1/campaigns.py b/app/api/v1/campaigns.py\n..."
}
```

**Key design principle:** The `bugged_diff` looks like a real, competent PR. The bugs are subtle — not syntax errors or obvious typos, but logic errors, security oversights, and missing guards. This tests whether the agent can find *real-world* code review issues, not just linting violations.

### `planted_defects` Array — The Ground Truth

Each planted defect is a deliberately injected bug with full metadata for automated scoring:

```json
{
  "id": "D-C4-01-1",
  "file": "app/services/campaign_service.py",
  "line_range_in_diff": "delete_campaign method",
  "category": "Security",
  "severity": "Critical",
  "title": "Missing ownership authorization check on campaign deletion",
  "description": "The delete_campaign method checks if the campaign exists and if it's in draft status, but does NOT verify that the requesting user is the owner. Any authenticated user can delete any draft campaign by providing its ID. This is a broken access control vulnerability (OWASP A01:2021).",
  "root_cause": "The ownership check `if campaign.brand_id != brand_user.id: raise ForbiddenError(...)` is missing from the delete_campaign method, while it IS present in update_campaign and transition_status.",
  "expected_location": {
    "file": "app/services/campaign_service.py",
    "function": "delete_campaign",
    "line_hint": "Between the NotFoundError check and the status check"
  },
  "suggested_fix": "Add `if campaign.brand_id != brand_user.id: raise ForbiddenError('You do not own this campaign')` after the None check, before the status check."
}
```

| Field | Type | Purpose |
|-------|------|---------|
| `id` | string | Unique defect identifier (e.g., `"D-C4-01-1"`) — used in matching results |
| `file` | string | File path where the defect is located |
| `line_range_in_diff` | string | Human-readable location hint (not used for automated scoring) |
| `category` | string | Defect category: `Security`, `Defect`, `Performance`, or `Maintainability` |
| `severity` | string | Severity level: `Critical`, `Major`, `Minor`, or `Suggestion` |
| `title` | string | Short summary of the defect |
| `description` | string | Detailed explanation of why this is a problem, with impact |
| `root_cause` | string | The technical root cause — what specific code is wrong and why |
| `expected_location` | object | Where the fix should go: `file`, `function`, `line_hint` |
| `suggested_fix` | string | How to fix the defect |

### Categories of Planted Defects

| Category | What It Covers | Example |
|----------|---------------|---------|
| **Security** | Access control, authorization bypass, input injection, data exposure | Missing ownership check → any user can delete any campaign |
| **Defect** | Logic errors, incorrect state transitions, missing validation | DRAFT can transition directly to COMPLETED (skipping review) |
| **Performance** | Missing bounds, unbounded queries, N+1 queries, missing indexes | `page_size` has no upper limit → client can request 1M rows |
| **Maintainability** | Code structure, tight coupling, missing abstractions | (Not common for Critical/Major — typically Minor or Suggestion) |

### `evaluation_config` — Quick Stats

```json
{
  "total_planted_defects": 3,
  "defect_categories": {
    "Security": 1,
    "Defect": 1,
    "Performance": 1
  },
  "defect_severities": {
    "Critical": 1,
    "Major": 2
  }
}
```

---

## 2. Submission: How the Agent Prompt Is Built

The agent prompt is constructed by `build_prompt_c4()`:

```python
def build_prompt_c4(entry: dict) -> str:
    inp = entry["input"]
    return (
        f"You are a senior software engineer performing a code review.\n\n"
        f"## Pull Request\n"
        f"**Title:** {inp['pr_title']}\n"
        f"**Description:** {inp['pr_description']}\n\n"
        f"## Diff\n"
        f"```diff\n{inp['bugged_diff']}\n```\n\n"
        f"## Task\n"
        f"Review this pull request for bugs, security issues, performance problems, "
        f"and design concerns. For each finding, provide:\n"
        f"1. file: the file path\n"
        f"2. line: approximate line number in the diff\n"
        f"3. severity: critical/major/minor\n"
        f"4. category: Security/Defect/Performance/Design/Maintainability\n"
        f"5. title: short summary\n"
        f"6. description: detailed explanation of the issue\n"
        f"7. suggestion: how to fix it\n\n"
        f"Output as JSON array of findings. Focus on real bugs — avoid nitpicks."
    )
```

### Resulting Prompt (C4-01 example)

```
You are a senior software engineer performing a code review.

## Pull Request
**Title:** feat: implement campaign CRUD with state machine
**Description:** Implements full campaign lifecycle management...

## Diff
```diff
diff --git a/app/api/v1/campaigns.py b/app/api/v1/campaigns.py
new file mode 100644
...
(full diff with ~500 lines of code across 6 files)
```

## Task
Review this pull request for bugs, security issues, performance problems,
and design concerns. For each finding, provide:
1. file: the file path
2. line: approximate line number in the diff
3. severity: critical/major/minor
4. category: Security/Defect/Performance/Design/Maintainability
5. title: short summary
6. description: detailed explanation of the issue
7. suggestion: how to fix it

Output as JSON array of findings. Focus on real bugs — avoid nitpicks.
```

### How It's Submitted

Like C1/C2, C4 is **pure text-in/text-out** — the agent doesn't get repo access:

```bash
agy --input-format text \
    --model gemini-3.8-flash-high \
    --output-format stream-json \
    --dangerously-skip-permissions
```

The agent reviews the diff from the prompt alone. It cannot browse the actual repo. This is intentional — real code reviewers often review PRs from the diff view.

### Expected Agent Output

The agent returns a JSON array of findings:

```json
[
  {
    "file": "app/services/campaign_service.py",
    "line": 165,
    "severity": "critical",
    "category": "Security",
    "title": "Missing ownership check on delete",
    "description": "The delete_campaign method does not verify that the requesting user owns the campaign...",
    "suggestion": "Add brand_id ownership check before the status check"
  },
  {
    "file": "app/models/campaign.py",
    "line": 32,
    "severity": "major",
    "category": "Defect",
    "title": "Invalid state transition from DRAFT to COMPLETED",
    "description": "VALID_TRANSITIONS allows draft → completed, bypassing the review lifecycle...",
    "suggestion": "Remove COMPLETED from the DRAFT transitions set"
  }
]
```

---

## 3. Evaluation: Automated Matching + LLM-as-Judge

C4 evaluation has two phases:

1. **Automated matching** (D1–D2): Map agent findings to planted defects using file match + LLM semantic matching (with keyword overlap fallback)
2. **LLM-as-Judge** (D3–D5): Evaluate localization accuracy, category/severity accuracy, and explanation quality

### Phase 1: Finding–Defect Matching

The `score_c4()` function implements AACR-Bench-inspired matching with two tiers:

1. **LLM semantic matching** (primary) — calls the rubric's `semantic_match_prompt` to determine if a finding and a planted defect describe the same issue
2. **Keyword overlap** (fallback) — used when LLM matching is unavailable or returns no match

```python
def score_c4(planted, findings, rubric=None, agent=None, model=None):
    # If rubric has semantic_match_prompt and agent/model are provided,
    # use LLM semantic matching (primary path)
    use_llm = bool(rubric and rubric.get("semantic_match_prompt") and agent and model)

    for finding in findings:
        # Step 1: File path match (filter candidates)
        file_matched_candidates = [i for i, d in enumerate(planted)
                                   if i not in matched and _file_match(finding["file"], d["file"])]

        # Step 2: LLM semantic match (if available)
        if use_llm and file_matched_candidates:
            for i in file_matched_candidates:
                result = _semantic_match_llm(finding, planted[i], semantic_prompt, agent, model)
                if result["is_same_issue"]:
                    # Pick highest confidence match
                    ...

        # Step 3: Keyword overlap fallback
        if no LLM match found:
            best by _keyword_overlap() ≥ 0.25
```

#### Step 1: File Path Match

```python
def _file_match(a, b):
    return (os.path.basename(a) == os.path.basename(b)
            or a.endswith(b) or b.endswith(a))
```

Tolerant matching — `campaign_service.py` matches `app/services/campaign_service.py`. This handles agents that report partial paths.

#### Step 2: LLM Semantic Match

For each file-matched candidate, calls `_semantic_match_llm()` which fills the rubric's `semantic_match_prompt` template and sends it to the LLM. The LLM returns `{"is_same_issue": true/false, "confidence": "high|medium|low"}`. Among positive matches, the one with the highest confidence is selected.

This handles cases where an agent describes the same bug using different terminology — e.g., "missing authorization check" vs "IDOR vulnerability" — which would fail keyword matching but are semantically the same issue.

#### Step 3: Keyword Overlap Fallback

```python
def _keyword_overlap(text_a, text_b):
    stop = {"the", "a", "an", "is", "in", "of", ...}
    words_b = set(text_b.lower().split()) - stop
    return sum(1 for w in words_b if w in text_a.lower()) / len(words_b)
```

If LLM semantic matching is unavailable (no rubric/agent/model) or returns no match, falls back to keyword overlap. A score of 0.25+ means at least 25% of the defect's key terms appear in the agent's description.

#### Match Priority

Each finding matches to AT MOST one planted defect. Each planted defect can only be matched once. LLM semantic matches take priority over keyword overlap. The result records which method was used (`match_method: "semantic_llm"` or `"keyword_overlap"`).

#### Matching Outcomes

| Outcome | Definition | Impact |
|---------|-----------|--------|
| **True Positive** | Finding matches a planted defect (file match + LLM semantic match or keyword overlap ≥ 0.25) | Increases recall and precision |
| **False Positive** | Finding doesn't match any planted defect | Decreases precision |
| **Undetected** | Planted defect with no matching finding | Decreases recall |

### Scoring Formulas

```python
recall = detected / total_planted           # raw ratio
precision = true_positives / total_findings  # raw ratio

# D1 tier scoring — _score_c4_d1(recall)
# Tier scores are read from c4_review.json rubric via _get_tiers("c4", "D1")
# Thresholds: ≥90% → tier[0], ≥70% → tier[1], ≥50% → tier[2], ≥30% → tier[3], <30% → tier[4]

# D2 tier scoring — _score_c4_d2(precision)
# Tier scores are read from c4_review.json rubric via _get_tiers("c4", "D2")
# Thresholds: ≥80% → tier[0], ≥60% → tier[1], ≥40% → tier[2], ≥20% → tier[3], <20% → tier[4]
```

**Single source of truth:** All tier scores (both automated and judge-scored) are defined in `evaluation/rubrics/c4_review.json`. Automated scoring functions read tier values via `_get_tiers()`. Judge-returned scores are validated and snapped to the nearest valid rubric tier via `validate_judge_scores()`.

**Example — C4-01 with 3 planted defects:**

| Scenario | Findings | TP | FP | Detected | Recall | Precision |
|----------|----------|----|----|----------|--------|-----------|
| Perfect | 3 | 3 | 0 | 3 | 100% | 100% |
| Good + some noise | 5 | 3 | 2 | 3 | 100% | 60% |
| Missed one | 2 | 2 | 0 | 2 | 66.7% | 100% |
| Missed one + noise | 4 | 2 | 2 | 2 | 66.7% | 50% |
| All noise | 3 | 0 | 3 | 0 | 0% | 0% |

### Phase 2: LLM Judge for D3, D4, D5

After automated scoring, the harness sends the agent's findings + planted defects + the diff to an LLM judge for D3 (Localization Accuracy), D4 (Category & Severity Accuracy), and D5 (Explanation & Fix Quality) scoring:

```python
judge_result = build_judge_payload("c4", rubric, entry, agent_response,
    extra_replacements={
        "code_diff": entry["input"]["bugged_diff"],
        "agent_findings": json.dumps(findings, indent=2),
        "planted_defects": json.dumps(planted, indent=2),
    },
    judge_dims_only=True)
```

The judge evaluates D3 (Localization Accuracy), D4 (Category & Severity Accuracy), and D5 (Explanation & Fix Quality). D1 and D2 are tier-scored automatically by `_score_c4_d1()` and `_score_c4_d2()` inside `score_c4()`.

---

## 4. The AACR-Bench Matching Pipeline

The rubric defines a 3-step matching pipeline inspired by AACR-Bench. Steps 1 and 3 are implemented; Step 2 (line proximity) is skipped because planted defects use text-based location descriptions rather than numeric line ranges:

```json
{
  "matching_logic": {
    "description": "AACR-Bench inspired 3-step matching",
    "steps": [
      {"step": 1, "name": "Path match",
       "description": "File path must match a planted defect's file"},
      {"step": 2, "name": "Line proximity",
       "description": "Line range overlaps or within ±5 lines of planted defect"},
      {"step": 3, "name": "Semantic match",
       "description": "LLM-as-judge determines if finding addresses the same concern"}
    ],
    "outcomes": {
      "all_pass": "TRUE POSITIVE (matched to specific planted defect)",
      "step1_2_pass_step3_fail": "Check if it's a VALID NON-PLANTED finding (LLM-as-judge)",
      "otherwise": "FALSE POSITIVE"
    }
  }
}
```

The `semantic_match_prompt` is used by `_semantic_match_llm()` for Step 3. It is called once per file-matched finding-defect pair:

```
You are an expert code reviewer. Determine whether two code review
comments address the same underlying issue.

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

This semantic match avoids penalizing agents that describe the same bug differently (e.g., "missing authorization check" vs "IDOR vulnerability" — same issue, different terminology).

---

## 5. Rubric Design (`c4_review.json`) — Full Reference

### Top-Level Fields

```json
{
  "category": "C4",
  "category_name": "Code Review",
  "category_name_zh": "代码评审",
  "evaluation_method": "automated_plus_llm",
  "total_points": 100,
  "pass_threshold": 60,
  "dimensions": [ ... 5 dimensions ... ],
  "matching_logic": { ... },
  "semantic_match_prompt": "...",
  "agent_prompt_template": "...",
  "judge_prompt_template": "..."
}
```

| Field | Type | Description |
|-------|------|-------------|
| `category` | string | `"C4"` |
| `category_name` | string | `"Code Review"` |
| `evaluation_method` | string | `"automated_plus_llm"` — automated matching (D1, D2) + LLM judge (D3, D4, D5) |
| `total_points` | int | `100` |
| `pass_threshold` | int | `60` |
| `dimensions` | array | 5 dimensions (D1–D5): 2 automated (D1, D2) + 3 LLM-judged (D3, D4, D5) |
| `matching_logic` | object | AACR-Bench inspired 3-step matching pipeline |
| `semantic_match_prompt` | string | LLM prompt for determining if two findings address the same issue |
| `agent_prompt_template` | string | Template for constructing the agent's review prompt |
| `judge_prompt_template` | string | Template for the explanation quality judge |

---

### `dimensions` Array — All 5 Dimensions

#### D1: Detection Recall (缺陷召回率) — 25 points

| Score | Criteria |
|-------|----------|
| **25** | Detects 90-100% of planted defects. |
| **20** | Detects 70-89% of planted defects. |
| **15** | Detects 50-69% of planted defects. |
| **10** | Detects 30-49% of planted defects. |
| **5** | Detects < 30% of planted defects. |

- **Method:** `automated`
- **Scoring function:** `_score_c4_d1(recall)` — maps recall ratio to tier score
- **Scoring formula:** `recall = detected_count / total_planted_count` → tier mapping

**What it measures:** Can the agent find the bugs? This is the most important dimension — a code review that misses real bugs is useless regardless of how well-written the found issues are. Recall is measured against the planted defects, not against all possible issues.

#### D2: Detection Precision (检测精确率) — 25 points

| Score | Criteria |
|-------|----------|
| **25** | Precision >= 80%. Very few false positives. |
| **20** | Precision 60-79%. Some false positives but mostly accurate. |
| **15** | Precision 40-59%. Roughly equal true and false positives. |
| **10** | Precision 20-39%. Many false positives. |
| **5** | Precision < 20%. Almost all findings are noise. |

- **Method:** `automated`
- **Scoring function:** `_score_c4_d2(precision)` — maps precision ratio to tier score
- **Scoring formula:** `precision = true_positive_count / total_findings_count` → tier mapping

**What it measures:** Is the agent signal or noise? An agent that reports 50 findings, only 3 of which are real bugs, wastes the reviewer's time. High precision means the developer can trust the review — if the agent flags something, it's probably real. Precision is equal-weighted with recall (both 25 pts) because both matter in practice.

#### D3: Localization Accuracy (定位准确性) — 20 points

| Score | Criteria |
|-------|----------|
| **20** | 90%+ of true-positive findings point to correct file AND correct line range (within ±3 lines). |
| **16** | 70-89% correct localization. |
| **12** | 50-69% correct localization. |
| **8** | 30-49% correct localization. |
| **4** | < 30% correct localization. |

- **Method:** `llm_as_judge`
- **Tolerance:** `±3 lines` — the agent's line number can be off by up to 3 lines and still count as correct

**What it measures:** Does the agent point to the RIGHT PLACE? Saying "there's a security issue in campaign_service.py" is less helpful than saying "line 165: delete_campaign is missing an ownership check." The LLM judge evaluates localization accuracy by comparing agent findings against planted defects, both of which are provided in the judge prompt.

#### D4: Category & Severity Accuracy (分类与严重性准确率) — 15 points

| Score | Criteria |
|-------|----------|
| **15** | 80%+ of true-positive findings have correct category AND severity within one level of ground truth. |
| **12** | 60-79% correct classification. |
| **9** | 40-59% correct classification. |
| **6** | 20-39% correct classification. |
| **3** | < 20% correct classification, or no category/severity provided. |

- **Method:** `llm_as_judge`
- **Severity tolerance:** `1 level` — calling a Critical issue "Major" is acceptable; calling it "Minor" is not

**What it measures:** Does the agent correctly categorize bugs? Calling a broken access control vulnerability "Maintainability" is misleading. Calling a Critical security bug "Minor" is dangerous — it might get deprioritized.

**Severity levels and tolerance:**
```
Critical ←→ Major (1 level apart — acceptable)
Major ←→ Minor (1 level apart — acceptable)
Critical ←→ Minor (2 levels apart — NOT acceptable)
```

#### D5: Explanation & Fix Quality (解释与修复建议质量) — 15 points

| Score | Criteria |
|-------|----------|
| **15** | Root cause is clearly explained, suggested fix is correct and actionable, explanation demonstrates understanding of why it's a problem (attack vectors for security, race condition sequences for concurrency). |
| **12** | Root cause mostly clear. Fix suggestion is correct but may need refinement. Good but not complete explanation of impact. |
| **9** | Issue identified but explanation is shallow. Fix suggestion is vague ("add validation"). |
| **6** | Issue described but root cause not identified. Fix suggestion is incorrect or missing. |
| **3** | Finding is just a label with no explanation. |

- **Method:** `llm_as_judge`

**What it measures:** Can the agent explain WHY something is wrong and HOW to fix it? Saying "missing authorization check" is 9/15. Saying "delete_campaign doesn't verify brand_id == user.id, so any authenticated user can delete any draft campaign via IDOR (OWASP A01:2021). Fix: add `if campaign.brand_id != brand_user.id: raise ForbiddenError(...)` between the None check and status check" is 15/15.

---

### `agent_prompt_template` — Full Template

The rubric includes a more detailed agent prompt template than the one used in the harness code. The rubric version provides richer context:

```
You are an experienced code reviewer. Review the following pull request
for a FastAPI-based campaign collaboration platform.

## PR Information
Title: {pr_title}
Description: {pr_description}

## Code Changes (Diff)
```diff
{bugged_diff}
```

## Repository Context
You have access to the full repository at /repo. The codebase follows
these conventions:
- Repository pattern for data access
- Service layer for business logic
- Pydantic schemas for validation
- Custom exception hierarchy (AppError → NotFoundError, ConflictError,
  ForbiddenError, ValidationError)
- Soft delete with is_deleted flag
- Decimal for monetary values

## Instructions
Review this PR thoroughly. For each issue you find, provide:
1. **File** and **line range** in the diff
2. **Category**: Security, Defect, Performance, or Maintainability
3. **Severity**: Critical, Major, Minor, or Suggestion
4. **Description**: What the issue is and why it matters
5. **Suggested fix**: How to resolve it

Focus on substantive issues. Do not flag style preferences or nitpicks.

Output as JSON array:
[
  {
    "file": "<path>",
    "line_range": "<start-end>",
    "category": "<Security|Defect|Performance|Maintainability>",
    "severity": "<Critical|Major|Minor|Suggestion>",
    "description": "<detailed description>",
    "suggested_fix": "<actionable fix>"
  }
]
```

### `judge_prompt_template` — The Complete Template

```
You are a senior software engineer evaluating the quality of code review
findings produced by an AI coding agent.

## Code Under Review (Diff)
<diff>
{code_diff}
</diff>

## Agent's Review Findings
<findings>
{agent_findings}
</findings>

## Ground Truth Defects
For reference, the planted defects in this code are:
<planted>
{planted_defects}
</planted>

## Calibration
{calibration_persona}

## Evaluation Task
D1 (Recall) and D2 (Precision) are scored automatically.
Evaluate the following dimensions:

{dimensions_text}

## Output Format
Respond in JSON:
{
  "D3": {"score": 0, "justification": ""},
  "D4": {"score": 0, "justification": ""},
  "D5": {"score": 0, "justification": ""},
  "total_score": 0,
  "overall_assessment": ""
}
```

#### Placeholder Reference

| Placeholder | Filled By | Content |
|-------------|-----------|---------|
| `{code_diff}` | `entry["input"]["bugged_diff"]` | The full PR diff the agent reviewed |
| `{agent_findings}` | `json.dumps(findings)` | The agent's review findings (parsed JSON array) |
| `{planted_defects}` | `json.dumps(planted)` | The ground truth defects with full metadata |
| `{calibration_persona}` | `rubric["calibration_persona"]` | Senior software engineer grading persona — avoid leniency for vague findings, avoid paranoia for minor localization imprecision |
| `{dimensions_text}` | Formatted from D3, D4, D5 (`judge_dims_only=True` filters out D1, D2 which have `method="automated"`) | Tier tables for the 3 LLM-judged dimensions |

---

## 6. End-to-End Flow Summary

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. LOAD: Read C4-01_campaign_crud.json                          │
│    Extract input.bugged_diff (the PR with planted bugs)         │
│    Extract planted_defects (ground truth)                       │
│                                                                 │
│ 2. PROMPT: build_prompt_c4(entry)                               │
│    "You are a senior software engineer performing code review"  │
│    + PR title, description                                      │
│    + full bugged diff                                           │
│    + "For each finding, provide file, line, severity..."        │
│                                                                 │
│ 3. SUBMIT: Pipe prompt to agent CLI via stdin                   │
│    Agent reviews diff, returns JSON array of findings           │
│    No repo access — pure text-in, text-out                      │
│                                                                 │
│ 4. PARSE: parse_findings(agent_response)                        │
│    Extract JSON array from agent's response                     │
│    Handles: raw JSON array, {findings: [...]}, regex fallback   │
│                                                                 │
│ 5. MATCH: score_c4(planted_defects, agent_findings, rubric,     │
│           agent, model)                                         │
│    For each finding:                                            │
│      a. File path match against planted defects                 │
│      b. LLM semantic match (via semantic_match_prompt)          │
│      c. Keyword overlap fallback (≥ 0.25 threshold)             │
│    Result: true_positives, false_positives, undetected           │
│    Compute: recall, precision                                   │
│                                                                 │
│ 6. TIER SCORES: _score_c4_d1(recall), _score_c4_d2(precision)   │
│                                                                 │
│ 7. LLM JUDGE: Send findings + defects + diff to judge           │
│    Judge scores D3 (Localization), D4 (Category/Severity),      │
│    and D5 (Explanation & Fix Quality)                            │
│                                                                 │
│ 8. COMBINE: D1 + D2 (automated) + D3 + D4 + D5 (judge)         │
│    Sum for total (max 100)                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. How Planted Defects Are Designed

Each C4 entry is constructed by:

1. **Starting from a correct implementation** — the gold_patch from C3 (or a human-written version)
2. **Deliberately introducing bugs** — each bug is:
   - **Subtle** — not a syntax error or obvious typo, but a logic flaw that could slip past a human reviewer
   - **Realistic** — the kind of bug that actually happens in production (missing auth check, wrong state transition, unbounded query)
   - **Well-documented** — full metadata for automated scoring (file, line, category, severity, root cause, fix)
3. **Creating the bugged_diff** — the diff with bugs looks like a normal, competent PR

### Example: 3 Planted Defects in C4-01

| # | Category | Severity | Title | Subtlety |
|---|----------|----------|-------|----------|
| 1 | Security | Critical | Missing ownership check on delete | All other methods (update, transition) have the check — only delete is missing. Easy to miss because the pattern is established elsewhere. |
| 2 | Defect | Major | DRAFT → COMPLETED is allowed | One extra value in a set literal inside a large dict. Requires understanding the state machine to notice. |
| 3 | Performance | Major | No upper bound on page_size | One endpoint has `le=100`, the other doesn't. Requires comparing two similar parameter definitions. |

The defects span multiple categories (Security, Defect, Performance) and are spread across multiple files (service, model, router), testing the agent's ability to review comprehensively.

---

## 8. Key Design Decisions

### Why planted defects (not real bugs)?
Real bugs have subjective severity, unclear boundaries, and no ground truth. Planted defects provide a controlled evaluation where recall and precision can be computed exactly.

### Why recall AND precision (not just recall)?
An agent that flags everything has perfect recall but is useless in practice. Developers will stop reading reviews if 90% of findings are false positives. Equal weighting (25 pts each) reflects that both matter.

### Why LLM semantic matching + keyword overlap fallback?
LLM semantic matching handles cases where agents describe the same bug using different terminology (e.g., "IDOR vulnerability" vs "missing ownership authorization check"). Keyword overlap is retained as a fallback for when LLM calls are unavailable. The cost is manageable because file path matching (Step 1) narrows the candidate pairs significantly — typically 1–3 LLM calls per finding rather than N×M.

### Why is C4 text-in/text-out (no repo access)?
Real code reviewers often review from the diff view. Giving repo access would let agents grep for patterns, run tests, and use tools that make the task easier — but wouldn't test the *review* skill. C4 specifically tests: can you read a diff and spot bugs?

### Why 20% composite weight?
Code review is a high-value skill for coding agents — catching bugs before they ship is often more valuable than writing new code. The 20% weight (second-highest after C3's 30%) reflects this importance. A good coding agent should be both a good writer AND a good reviewer.

### Why do D3, D4, D5 use LLM-as-Judge?
D1 (recall) and D2 (precision) can be computed from matching counts. But localization accuracy (D3), category/severity correctness (D4), and explanation quality (D5) require judgment — e.g., is "near the delete method" close enough to the planted defect's location? Is "IDOR vulnerability" the right category for a missing ownership check? LLM-as-Judge is the right tool for these qualitative assessments.
