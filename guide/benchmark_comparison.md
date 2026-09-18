# Benchmark Comparison: HumanEval, SWE-bench, AACR-Bench, XHS Agent Eval

End-to-end samples of three influential coding benchmarks, with comparison to our XHS Agent Eval design.

---

## 1. HumanEval — Function-Level Code Completion

**Source:** OpenAI, `github.com/openai/human-eval`. 164 hand-written Python problems.

### 1.1 Data Format

Each problem is a JSON object in `HumanEval.jsonl`:

```json
{
  "task_id": "HumanEval/0",
  "prompt": "from typing import List\n\ndef has_close_elements(numbers: List[float], threshold: float) -> bool:\n    \"\"\" Check if in given list of numbers, are any two numbers closer to each other than\n    given threshold.\n    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)\n    False\n    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)\n    True\n    \"\"\"\n",
  "entry_point": "has_close_elements",
  "canonical_solution": "    for idx, elem in enumerate(numbers):\n        for idx2, elem2 in enumerate(numbers):\n            if idx != idx2:\n                distance = abs(elem - elem2)\n                if distance < threshold:\n                    return True\n    return False\n",
  "test": "def check(candidate):\n    assert candidate([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.3) == True\n    assert candidate([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.05) == False\n    assert candidate([1.0, 2.0, 5.9, 4.0, 5.0], 0.95) == True\n    assert candidate([1.0, 2.0, 5.9, 4.0, 5.0], 0.8) == False\n    assert candidate([1.0, 2.0, 3.0, 4.0, 5.0, 2.0], 0.1) == True\n    assert candidate([1.1, 2.2, 3.1, 4.1, 5.1], 1.0) == True\n    assert candidate([1.1, 2.2, 3.1, 4.1, 5.1], 0.5) == False\n"
}
```

| Field | Purpose |
|-------|---------|
| `task_id` | Unique ID (`HumanEval/0` through `HumanEval/163`) |
| `prompt` | Function signature + docstring — **what the model sees** |
| `entry_point` | Function name, used to wire up tests |
| `canonical_solution` | Reference solution (never shown to model) |
| `test` | `check(candidate)` with assert statements (never shown to model) |

The model only sees `prompt`. It must generate the function body. The `test` and `canonical_solution` are hidden ground truth.

### 1.2 Evaluation Harness

The harness combines `prompt + completion + test` into a single executable program:

```python
# What the harness actually executes:
from typing import List

def has_close_elements(numbers: List[float], threshold: float) -> bool:
    """ Check if in given list of numbers, are any two numbers closer... """
    # ← MODEL'S COMPLETION IS INSERTED HERE
    for idx, elem in enumerate(numbers):
        for idx2, elem2 in enumerate(numbers):
            if idx != idx2:
                if abs(elem - elem2) < threshold:
                    return True
    return False

# ← HIDDEN TEST IS APPENDED HERE
def check(candidate):
    assert candidate([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.3) == True
    assert candidate([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.05) == False
    # ...

check(has_close_elements)
```

Core harness code:

```python
def check_correctness(problem, completion, timeout=3.0):
    """Run the completion against unit tests in a subprocess with timeout."""
    program = problem["prompt"] + completion + "\n" + problem["test"] + \
              f"\ncheck({problem['entry_point']})\n"
    result = unsafe_execute(program, timeout)
    return {"task_id": problem["task_id"], "passed": result == "passed"}


def unsafe_execute(program, timeout):
    """Execute program in a subprocess, return 'passed' or 'failed'."""
    try:
        exec_globals = {}
        with time_limit(timeout):
            exec(program, exec_globals)
        return "passed"
    except Exception:
        return "failed"
```

Key details:
- Each completion runs in an **isolated subprocess** with a timeout (default 3 seconds)
- Any exception (AssertionError, RuntimeError, timeout) = **failed**
- No partial credit — either all asserts pass or the whole thing fails

CLI commands:

```bash
# Generate samples (model-specific, each team writes their own)
# Evaluate the samples
evaluate_functional_correctness samples.jsonl
# Output: {'pass@1': 0.672, 'pass@10': 0.876, 'pass@100': 0.944}
```

### 1.3 Evaluation Criteria: pass@k

Given `n` total samples per problem, `c` of which are correct:

```
pass@k = 1 - C(n-c, k) / C(n, k)
```

In code:

```python
def estimate_pass_at_k(num_samples, num_correct, k):
    """Unbiased estimator for pass@k."""
    if num_samples - num_correct < k:
        return 1.0
    return 1.0 - np.prod(1.0 - k / np.arange(num_samples - num_correct + 1, num_samples + 1))
```

### Worked Example

Problem HumanEval/0, `n=10` samples generated, `c=7` passed:

```
pass@1  = 1 - C(3,1)/C(10,1) = 1 - 3/10  = 0.70
pass@5  = 1 - C(3,5)/C(10,5) = 1 - 0/252 = 1.00
pass@10 = 1 - C(3,10)/C(10,10) = 1 - 0/1  = 1.00
```

Final score = **mean pass@k across all 164 problems**. Modern models score >90% pass@1 — HumanEval is largely saturated.

### 1.4 Prompt & Tools

HumanEval was designed for **Codex** (a base completion model). The official `openai/human-eval` repo has **no system prompt, no instruction wrapper, no chat formatting**. The `prompt` field is passed directly as a completion prefix:

#### 1.4.1 Base/Completion Models (Original Design)

The model receives the raw `prompt` field and continues it:

```python
from typing import List

def has_close_elements(numbers: List[float], threshold: float) -> bool:
    """ Check if in given list of numbers, are any two numbers closer to each other than
    given threshold.
    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)
    False
    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
    True
    """
```

The model outputs raw Python code — the function body. The harness truncates at the first `\ndef ` or `\nclass ` boundary (stop sequences) to prevent the model from generating extra functions.

The official repo's generation function is a **stub** — users must implement it themselves:

```python
# From human_eval/generate_samples.py (placeholder)
def generate_one_completion(prompt: str) -> str:
    """Calls your model. Replace this with your actual generation code."""
    raise NotImplementedError
```

#### 1.4.2 Chat/Instruction Models (Modern Practice)

Modern models (GPT-4, Claude, etc.) are instruction-tuned, not completion models. Evaluation frameworks wrap the raw prompt in a chat template.

**EvalPlus** (`github.com/evalplus/evalplus`) — the most widely used HumanEval evaluator for chat models:

```python
# EvalPlus instruction prompt for chat models
HUMANEVAL_CHAT_INSTRUCTION = (
    "Complete the following Python function. "
    "Your response should only contain the code for the completed function."
)

# Assembled as chat messages:
messages = [
    {"role": "system", "content": HUMANEVAL_CHAT_INSTRUCTION},
    {"role": "user", "content": prompt}   # raw HumanEval prompt field
]
```

For base models, EvalPlus passes the raw `prompt` with no wrapper — identical to the original repo. Toggle with `--greedy --base` (completion) vs `--instruct` (chat).

**BigCodeBench** uses a more detailed instruction:

```
Complete the following Python function. Only output the function body
(the code that comes after the function signature). Do not include
the function signature, imports, or any explanation.
```

**Open LLM Leaderboard** (HuggingFace):

```
System: You are a helpful coding assistant.
User: Complete the following Python function:
{prompt}
```

#### 1.4.3 Summary

| Property | Base/Completion Model | Chat/Instruction Model |
|----------|----------------------|----------------------|
| System prompt | None | "Complete the following Python function" (framework-dependent) |
| Instance prompt | Raw `prompt` field (function signature + docstring) | Same raw `prompt` field, wrapped in user message |
| Tools | None | None |
| Output format | Raw Python code (function body) | Raw Python code, possibly with markdown fences to strip |
| Agent loop | No — single-pass completion | No — single-pass completion |
| Stop sequences | `\ndef `, `\nclass ` | Same, plus markdown fence stripping |

The key point: **HumanEval itself defines no prompt template** — it provides only the raw `prompt` field. The wrapping is done by evaluation frameworks (EvalPlus, BigCodeBench, etc.) and varies across implementations. This is a known limitation — results for the same model can differ depending on which framework and prompt wrapper was used.

---

## 2. SWE-bench — Repo-Level Issue Resolution

**Source:** Princeton NLP, `github.com/princeton-nlp/SWE-bench`. Real GitHub issues from 12 open-source Python repos. 300 (Lite) / 500 (Verified) / 2,294 (Full) instances.

### 2.1 Data Format

A real entry (`astropy__astropy-12907`):

```json
{
  "repo": "astropy/astropy",
  "instance_id": "astropy__astropy-12907",
  "base_commit": "d16bfe05a744909de4b27f5875fe0d4ed41ce607",
  "problem_statement": "Modeling's `separability_matrix` does not compute separability correctly for nested CompoundModels\n\nConsider the following model:\n\n```python\nfrom astropy.modeling import models as m\nfrom astropy.modeling.separable import separability_matrix\n\ncm = m.Linear1D(10) & m.Linear1D(5)\n```\n\nIt's separability matrix as you might expect is a diagonal:\n\n```python\n>>> separability_matrix(cm)\narray([[ True, False],\n       [False,  True]])\n```\n\nIf however, I nest these compound models:\n```python\n>>> separability_matrix(m.Pix2Sky_TAN() & cm)\narray([[ True,  True, False, False],\n       [ True,  True, False, False],\n       [False, False,  True,  True],\n       [False, False,  True,  True]])\n```\nSuddenly the inputs and outputs are no longer separable?\nThis feels like a bug to me, but I might be missing something?",
  "hints_text": "",
  "patch": "diff --git a/astropy/modeling/separable.py b/...\n-        cright[-right.shape[0]:, -right.shape[1]:] = 1\n+        cright[-right.shape[0]:, -right.shape[1]:] = right",
  "test_patch": "diff --git a/astropy/modeling/tests/test_separable.py b/...\n+    'cm8': (rot & (sh1 & sh2), cm_4d_expected),\n+    'cm9': (rot & sh1 & sh2, cm_4d_expected),\n+    'cm10': ((rot & sh1) & sh2, cm_4d_expected),\n+    'cm11': (rot & sh1 & (scl1 & scl2), ...),",
  "FAIL_TO_PASS": [
    "astropy/modeling/tests/test_separable.py::test_separable[compound_model6-result6]",
    "astropy/modeling/tests/test_separable.py::test_separable[compound_model9-result9]"
  ],
  "PASS_TO_PASS": [
    "astropy/modeling/tests/test_separable.py::test_coord_matrix",
    "astropy/modeling/tests/test_separable.py::test_cdot",
    "astropy/modeling/tests/test_separable.py::test_cstack",
    "astropy/modeling/tests/test_separable.py::test_arith_oper",
    "astropy/modeling/tests/test_separable.py::test_separable[compound_model0-result0]"
  ],
  "version": "4.3",
  "environment_setup_commit": "298ccb478e6bf092953bca67a3d29dc6c35f6752",
  "created_at": "2022-03-03T15:14:54Z",
  "difficulty": "15 min - 1 hour"
}
```

| Field | Purpose |
|-------|---------|
| `repo` | GitHub repo (e.g., `astropy/astropy`) |
| `instance_id` | `{owner}__{repo}-{issue_number}` |
| `base_commit` | Exact commit to checkout before the agent works |
| `problem_statement` | The GitHub issue text — **what the agent sees** |
| `hints_text` | Optional extra context (often empty) |
| `patch` | Gold solution — the expert-written fix (agent never sees this) |
| `test_patch` | Hidden tests — injected after agent finishes |
| `FAIL_TO_PASS` | Test names that must pass after the fix |
| `PASS_TO_PASS` | Test names that must not regress |
| `version` | Library version at the base commit |
| `environment_setup_commit` | Commit used to build the Docker environment |
| `difficulty` | Human-estimated fix time |

### 2.2 Evaluation Harness

Model prediction format (JSONL):

```json
{"instance_id": "astropy__astropy-12907", "model_name_or_path": "gpt-4", "model_patch": "diff --git a/astropy/modeling/separable.py b/..."}
```

End-to-end flow:

```
1. BUILD DOCKER IMAGE (3-layer cache)
   Base image (language/tooling)
     → Environment image (repo dependencies at version X)
       → Instance image (repo at base_commit with test_patch baked in)

2. CREATE CONTAINER
   docker create --name sweb.eval.{instance_id}.{run_id}
   Start with "tail -f /dev/null" to keep alive

3. APPLY MODEL PATCH (cascade fallback)
   Copy model_patch into container, then try in order:
     git apply --verbose
     git apply --verbose --3way
     git apply --verbose --reject
     patch --batch --forward --fuzz=5 -p1 -i
   Between failures: git checkout -- . ; git clean -fd
   Final fallback: git apply --check --reverse (already applied?)

4. APPLY TEST PATCH
   Baked into eval.sh during TestSpec generation
   The eval script resets test files, applies test_patch via git apply

5. RUN TESTS
   exec_run_with_timeout(container, "/bin/bash /eval.sh", timeout=1800s)
   Output captured between START_TEST_OUTPUT / END_TEST_OUTPUT markers
   Parsed by language-specific log parsers

6. GRADE
   get_eval_report() checks:
   - Did ALL FAIL_TO_PASS tests pass? (SKIPPED counts as failure)
   - Did ALL PASS_TO_PASS tests stay passing? (SKIPPED counts as pass)

7. REPORT
   Per-instance: report.json, test_output.txt, eval.sh, patch.diff
   Aggregate: results.json with counts and ID lists
```

Commands:

```bash
# Install
pip install swebench

# Run evaluation
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path predictions.jsonl \
    --max_workers 8 \
    --run_id my_eval

# Gold patch validation
swebench eval verified --gold -i sympy__sympy-20590 --run-id validate
```

### 2.3 Evaluation Criteria: % Resolved

Strictly binary — an instance is resolved if and only if 100% F2P pass AND 100% P2P pass:

```python
def get_resolution_status(report):
    f2p = compute_fail_to_pass(report)   # fraction of F2P tests now passing
    p2p = compute_pass_to_pass(report)   # fraction of P2P tests maintained

    if f2p == 1 and p2p == 1:
        return ResolvedStatus.FULL       # → resolved: True
    elif 0 < f2p < 1 and p2p == 1:
        return ResolvedStatus.PARTIAL    # → resolved: False (no partial credit)
    else:
        return ResolvedStatus.NO         # → resolved: False
```

Key nuances:
- `SKIPPED` tests count as **failure** for F2P
- `SKIPPED` tests count as **maintained** for P2P
- `XFAIL` (expected failure) counts the same as `PASSED`

### 2.4 Rubrics

**SWE-bench has no LLM-as-judge rubrics, no dimension scores, no quality tiers.** One metric:

```
% Resolved = resolved_count / total_instances
```

Aggregate report:

```json
{
  "total_instances": 500,
  "submitted_instances": 500,
  "completed_instances": 487,
  "resolved_instances": 245,
  "unresolved_instances": 242,
  "empty_patch_instances": 3,
  "error_instances": 10,
  "resolved_ids": ["astropy__astropy-12907", "..."],
  "unresolved_ids": ["..."]
}
```

Current best agents: ~50% on SWE-bench Verified.

### 2.5 Prompt & Tools

SWE-bench itself is **evaluation-only** — it doesn't prescribe how the agent should be prompted. Different agent frameworks provide different prompts and tools.

#### 2.5.1 Raw Baseline (No Tools)

The simplest approach — text-in, diff-out:

```
You will be provided with a partial code base and an issue statement
explaining a problem to resolve.

<issue>
{problem_statement}
</issue>

Please generate a patch file (in unified diff format) that resolves
the issue. The patch should be minimal and only modify the files
necessary to fix the issue.

<patch>
```

The model outputs a unified diff directly. No tools, no agent loop. This baseline achieves ~2-5% resolve rate with GPT-4/Claude.

#### 2.5.2 SWE-agent (Princeton NLP) — The Primary Agent Framework

SWE-agent (`github.com/princeton-nlp/SWE-agent`) wraps the model in a ReAct loop with a custom shell environment and 11 specialized commands.

**System prompt (from `config/default.yaml`):**

```
SETTING: You are an autonomous programmer, and you're working directly
in the command line with a special interface.

The special interface consists of a file viewer that shows you {WINDOW}
lines of a file at a time. In addition to typical bash commands, you can
use the following commands to help you navigate and edit files.

COMMANDS:
{command_docs}

Please note that THE EDIT COMMAND REQUIRES PROPER INDENTATION.

RESPONSE FORMAT:
Your shell prompt is formatted as follows:
(Open file: <path>) (Current directory: <cwd>)
bash-$

You need to format your output using two fields; discussion and command.
Your output should always include _one_ discussion and _one_ command field
EXACTLY as follows:

DISCUSSION
First I'll start by reproducing the issue...

```
command
```
```

**Instance prompt (per-task):**

```
We're currently solving the following issue within our repository.
Here's the issue text:
ISSUE:
{issue}

INSTRUCTIONS:
Now, you're going to solve this issue on your own. Your terminal
session has started and you're in the repository's root directory.
You can use any bash commands or the special commands listed above.
Edit all the files you need to and run any checks or tests that you
think are relevant. Remember, YOU CAN ONLY ENTER ONE COMMAND AT A TIME.
When you're satisfied with all of your changes, you can submit your
changes to the code base by simply running the submit command.
Note however that you cannot use any interactive session commands
(e.g. python, vim) in this environment, but you can write scripts
and run them. E.g. you can write a python script and then run it
with `python <script_name>.py`.

NOTE ABOUT THE EDIT COMMAND: Indentation is important and must be
consistent with the rest of the file.
```

**SWE-agent's 11 custom tools:**

| Command | Syntax | Description |
|---------|--------|-------------|
| `open` | `open <path> [<line>]` | Opens a file in the viewer at a given line. Shows {WINDOW} lines at a time. |
| `goto` | `goto <line>` | Moves the viewer window to the specified line. |
| `scroll_down` | `scroll_down` | Moves the viewer window down by {WINDOW} lines. |
| `scroll_up` | `scroll_up` | Moves the viewer window up by {WINDOW} lines. |
| `create` | `create <filename>` | Creates a new file and opens it in the editor. |
| `edit` | `edit <start>:<end>`<br>`<replacement>`<br>`end_of_edit` | Replaces lines start through end (inclusive) with the given text. Requires exact indentation. |
| `search_dir` | `search_dir <term> [<dir>]` | Searches for a term in all files in a directory. |
| `search_file` | `search_file <term> [<file>]` | Searches for a term in the currently open file. |
| `find_file` | `find_file <name> [<dir>]` | Finds files by name in a directory tree. |
| `submit` | `submit` | Submits current repo state as the solution. Generates git diff. |

Plus standard bash commands (`ls`, `cd`, `cat`, `python`, `grep`, `git`, etc.).

**Edit command example:**

```
edit 142:142
        end = start + per_page
end_of_edit
```

This replaces line 142. The `end_of_edit` sentinel marks the end of the replacement block.

**Agent loop:** ReAct-style. Each turn, the model outputs a DISCUSSION block (reasoning) and a single command. The harness executes the command, returns stdout/stderr (truncated to fit context), and loops until the agent calls `submit`.

#### 2.5.3 Other Agent Frameworks

**Aider** — Architect + Editor pattern:
- Architect model gets the issue + repo map (condensed file tree with function/class signatures)
- Editor model translates the plan into SEARCH/REPLACE edit blocks:
  ```
  <<<<<<< SEARCH
  old code exactly as it appears
  =======
  new replacement code
  >>>>>>> REPLACE
  ```
- Tools: repo map generation, file reading, SEARCH/REPLACE editing, git diff, test running

**OpenHands (formerly OpenDevin)** — Full sandbox:
- Tools: `CmdRunAction` (bash), `FileReadAction`, `FileWriteAction`, `BrowseURLAction`, `IPythonRunCellAction`
- Docker sandbox with full OS access — can install packages, run tests, browse docs

**Moatless Tools** — Code-search-first:
- Tools: `SearchCode` (semantic search), `ViewCode`, `FindClass`, `FindFunction`, `StringReplace` (edit), `CreateFile`
- Two-phase: localize the bug (search), then edit (fix). No bash access.

| Framework | Tools | Edit Mechanism | Agent Loop | Typical Resolve Rate |
|-----------|-------|---------------|------------|---------------------|
| Raw baseline | None | Direct diff output | No | 2-5% |
| SWE-agent | 11 custom + bash | `edit start:end` | ReAct | 12-25% |
| Aider | Repo map + SEARCH/REPLACE | SEARCH/REPLACE blocks | Architect → Editor | 20-30% |
| OpenHands | Bash + file ops + browser | File write | ReAct | 25-40% |
| Moatless | Semantic search + edit | StringReplace | Two-phase | 15-25% |
| Claude Code / agy | Full shell + file tools | Native file editing | Agentic loop | 40-55% |

---

## 3. AACR-Bench — AI Code Review Evaluation

**Source:** Alibaba, `github.com/alibaba/aacr-bench`, Apache 2.0. 200 real PRs, 50 projects, 10 languages, 2,145 review comments annotated by 80+ senior engineers.

### What AACR-Bench Measures

The AI reviewer **generates review comments from scratch** given a real PR diff. The harness then **matches** those generated comments against expert-validated ground truth to compute precision and recall. The benchmark answers: "Can the AI find the same issues that expert reviewers find?"

### How the Ground Truth Was Built (Hybrid Annotation)

The reference comments are NOT purely human-written. They come from a 3-step hybrid process:

1. **Human reviewers** (80+ senior engineers) write review comments on real GitHub PRs
2. **LLMs** (multiple models like Gemini, Claude, etc.) also generate comments on the same PRs
3. **Expert annotators** do 3 rounds of cross-validation on ALL comments (both human and AI-generated), marking each as `label=1` (valid finding) or `label=0` (rejected)

Only `label=1` comments serve as ground truth during evaluation. The `is_ai_comment` and `source_model` fields indicate where each reference comment originated — not how it will be used.

### 3.1 Data Format

Each instance is a row in JSONL (HuggingFace: `Alibaba-Aone/aacr-bench`):

```json
{
  "project_main_language": "C++",
  "pr_url": "https://github.com/FreeCAD/FreeCAD/pull/19411",
  "pr_source_commit": "0c65673a6fd2421be8fbe613116077120adea068",
  "pr_target_commit": "a050e422e23ce3eaee960b75ceff236b34f369b9",
  "pr_change_line_count": 862,
  "pr_category": "Code Refactoring / Architectural Improvement",
  "is_ai_comment": true,
  "note": "Optimization suggestion: getDirsFromFront(t) is currently called for every view in the loop. If multiple views share the same ProjDirection t, this results in redundant calculations. Consider checking if t is already in saveVals before calling getDirsFromFront.",
  "path": "src/Mod/TechDraw/App/DrawProjGroup.cpp",
  "side": "right",
  "source_model": "Gemini-3-Pro",
  "from_line": 1123,
  "to_line": 1126,
  "category": "Performance",
  "context": "File Level",
  "label": 1
}
```

| Field | Purpose |
|-------|---------|
| `pr_url` | GitHub PR URL (serves as instance identifier) |
| `pr_source_commit` / `pr_target_commit` | Base/head commits defining the diff |
| `pr_change_line_count` | Size of the PR |
| `note` | The review comment text (ground truth) |
| `path` | File the comment targets |
| `from_line` / `to_line` | Line range (closed interval) |
| `side` | `"left"` (old code) or `"right"` (new code) |
| `category` | Security / Defect / Performance / Maintainability |
| `context` | Scope: Diff Level / File Level / Repo Level |
| `label` | 1 = expert-confirmed valid finding (used as ground truth), 0 = rejected by experts (filtered out during eval) |
| `source_model` | Empty for human-written comments, model name for AI-generated ones. Indicates origin, not quality — all are expert-validated. |

### 3.2 Evaluation Harness: 4-Stage Matching Pipeline

```
For each reference comment × each generated comment:

  ┌─────────────────────────────────────────────────┐
  │ Stage 1: PATH MATCH                             │
  │   normalize("\" → "/")                          │
  │   ref_path == gen_path?                         │
  │   (skip check if either is empty)               │
  │   NO → skip to next generated comment           │
  └─────────────────────────────────────────────────┘
                    ↓ pass
  ┌─────────────────────────────────────────────────┐
  │ Stage 2: SIDE MATCH                             │
  │   ref_side == gen_side?                         │
  │   (skip check if either is None)                │
  │   NO → skip                                     │
  └─────────────────────────────────────────────────┘
                    ↓ pass
  ┌─────────────────────────────────────────────────┐
  │ Stage 3: LINE MATCH (k-tolerance)               │
  │   Do ranges [ref_from, ref_to] and              │
  │   [gen_from, gen_to] overlap?                   │
  │   OR is minimum endpoint distance ≤ k?          │
  │   (default k=1, configurable via --line-k)      │
  │   NO → skip                                     │
  └─────────────────────────────────────────────────┘
                    ↓ pass → record line_match
  ┌─────────────────────────────────────────────────┐
  │ Stage 4: SEMANTIC MATCH (LLM judge)             │
  │   "Do these two comments express the same       │
  │   concern or suggestion?"                       │
  │   YES → record semantic_match, stop searching   │
  │   NO → skip                                     │
  └─────────────────────────────────────────────────┘
```

Line distance function:

```python
def diff_location_is_same(from_line1, from_line2, to_line1, to_line2, k=1):
    has_overlap = not (from_line1 > to_line2 or from_line2 < to_line1)
    if has_overlap:
        min_distance = 0
    else:
        min_distance = min(abs(from_line1 - to_line2), abs(from_line2 - to_line1))
    return min_distance <= k
```

Deduplication: Each generated comment can contribute at most one line match and one semantic match across all reference comments.

### 3.3 Semantic Match — LLM Judge Prompt

```
-Role-
You are an expert code reviewer assistant specialized in analyzing
and comparing code review comments.

-Task-
Determine whether two given review comments express the same concern
or suggestion. Ignore differences in wording, tone, or formatting —
focus solely on semantic equivalence of the underlying issue.
If the core intent and technical substance are identical,
answer "yes"; otherwise, answer "no".

Review Comment 1:
{reference_note}

Review Comment 2:
{generated_note}

Your answer:
```

Response parsing: checks for "yes"/"similar"/"same"/"identical"/"equivalent" keywords, with a guard that "no" before "yes" negates the match.

Mock fallback (when no judge API key): `SequenceMatcher ratio >= 0.4` OR `Jaccard word overlap >= 0.3`.

### 3.4 Evaluation Metrics

```python
def compute_cr_statistics(comments, generated_count):
    line_match_rate     = line_match_count / generated_count      # precision
    semantic_match_rate = semantic_match_count / generated_count   # precision

    line_recall_rate     = line_match_count / total_expected       # recall
    semantic_recall_rate = semantic_match_count / total_expected   # recall
```

| Metric | Formula | Measures |
|--------|---------|----------|
| **Semantic Precision** | semantic_matches / total_generated | How many of the agent's findings are real issues |
| **Semantic Recall** | semantic_matches / total_expected | How many real issues the agent found |
| **Line Precision** | line_matches / total_generated | How precisely the agent locates issues |
| **Line Recall** | line_matches / total_expected | What fraction of issues are correctly located |
| **Noise Rate** | 1 - semantic_precision | Fraction of invalid/incorrect generated comments |

### 3.5 Prompt & Tools

AACR-Bench supports three reviewer backends, each with different prompting:

#### 3.5.1 OCR (OpenCodeReview) — CLI Tool

OCR is invoked as a CLI binary — the prompt is built internally:

```bash
ocr review --from {base_commit} --to {head_commit} --format json
```

The user doesn't control the prompt. OCR computes the diff internally and outputs a JSON array of findings.

#### 3.5.2 Claude Code / Codex — Structured Review Prompt

For LLM-based reviewers, AACR-Bench builds a review prompt:

```
You are a senior software engineer performing a thorough code review.

## Pull Request
Repository: {repo_url}
Base: {base_commit}
Head: {head_commit}

## Changed Files
{diff_content}

## Task
Review the code changes for:
- Security vulnerabilities
- Bugs and defects
- Performance issues
- Maintainability concerns

For each issue found, report:
- file_path: the affected file
- from_line: start line number
- to_line: end line number
- side: "left" (removed code) or "right" (added code)
- category: Security | Defect | Performance | Maintainability
- comment: detailed explanation of the issue and suggested fix

Output as a JSON array of findings.
```

Claude Code is invoked with **two channels**:
1. **MCP findings server** — structured tool-based output
2. **stdout parsing** — fallback, parses JSON from text output

The harness picks whichever channel produces more findings.

#### 3.5.3 Expected Output Format

All reviewers must produce findings matching this schema:

```json
[
  {
    "file_path": "src/Mod/TechDraw/App/DrawProjGroup.cpp",
    "from_line": 1123,
    "to_line": 1126,
    "side": "right",
    "category": "Performance",
    "comment": "getDirsFromFront(t) is called redundantly in the loop..."
  }
]
```

| Property | Value |
|----------|-------|
| System prompt | "You are a senior software engineer performing a thorough code review." |
| Instance prompt | PR metadata + full diff + structured review instructions |
| Tools | MCP findings server (primary) + stdout JSON (fallback) |
| Output format | JSON array of `{file_path, from_line, to_line, side, category, comment}` |
| Agent loop | No — single-pass review |

---

## 4. Side-by-Side Comparison

| | HumanEval | SWE-bench | AACR-Bench | XHS Agent Eval |
|-|-----------|-----------|------------|----------------|
| **What it tests** | Write a function | Fix a repo-level issue | Review a PR for bugs | 6 skills (requirements → debugging) |
| **Scope** | Single function | Full repository | PR diff | Full repo or text-only (varies by category) |
| **Input to model** | Function signature + docstring | GitHub issue text | PR diff | Category-dependent (spec, problem_statement, diff, bug report) |
| **Model output** | Function body (5-30 lines) | Git patch (50-500 lines) | JSON array of findings | Varies: structured text, code patch, findings |
| **Ground truth** | Hidden assert tests | Hidden test_patch (F2P/P2P) | Expert-validated comments (hybrid: human + AI, all label=1) | Gold standard + test_patch + planted defects |
| **Matching** | N/A (exec pass/fail) | N/A (test pass/fail) | Path → Side → Line → LLM semantic | Path → keyword overlap ≥ 0.25 (C4) |
| **Metric** | pass@k | % resolved (binary) | Semantic P/R, Line P/R | 5-7 dimensions per category, /100 |
| **Partial credit** | No | No | Yes (P/R are continuous) | Yes (tier-based dimension scores) |
| **LLM judge** | No | No | Yes (semantic match only) | Yes (multi-dimension quality scoring) |
| **Dataset size** | 164 problems | 300-2,294 instances | 200 PRs, 2,145 comments | 34 entries across 6 categories |
| **Languages** | Python only | Python (12 repos) | 10 languages | Python only |
| **Saturation** | Yes (>90% pass@1) | No (~50%) | No | N/A (new benchmark) |
| **Setup complexity** | `pip install` | Docker per repo | Git clone + API keys | Git worktree + agent CLI |
| **Data source** | Hand-written | Real GitHub issues | Real GitHub PRs + hybrid annotations (human + AI, expert-validated) | Hand-crafted (synthetic) |

### Design Lineage: What XHS Agent Eval Borrows

| From | Pattern Borrowed | Used In |
|------|-----------------|---------|
| **SWE-bench** | Worktree checkout → agent runs → capture patch → apply test_patch → F2P/P2P binary testing | C3, C5b |
| **AACR-Bench** | Finding-to-defect matching via file path + semantic similarity | C4 |
| **HumanEval** | Self-contained text-in/text-out evaluation (no repo access needed) | C1, C2 |
| **Beyond all three** | Multi-dimensional LLM-as-Judge scoring with calibration personas, tier tables, and hard caps | All categories |

### Where XHS Agent Eval Goes Further

1. **Multi-dimensional scoring** — SWE-bench and HumanEval are binary (pass/fail). XHS uses 5-7 scored dimensions per category with explicit tier tables, giving actionable feedback on where an agent is weak.

2. **Calibration personas** — The LLM judge prompt includes a persona (e.g., "You are a senior software engineer at a mid-to-large tech company...") to anchor scoring consistency. Not present in any of the three reference benchmarks.

3. **Hard caps** — Category-specific rules that override dimension scores (e.g., "If no user stories → D1 capped at 5"). Not present in reference benchmarks.

4. **Coverage breadth** — Tests 6 distinct skills (requirements, design, code gen, code review, test gen, debugging) in one benchmark. SWE-bench tests only code generation, HumanEval only function completion, AACR-Bench only code review.

5. **Composite scoring** — Weighted aggregation across categories with grade mapping (S/A/B/C/D). Produces a single comparable score while preserving per-dimension detail.

---

## 5. Prompt & Tools Comparison

### 5.1 Summary Table

| | HumanEval | SWE-bench (SWE-agent) | AACR-Bench | XHS Agent Eval |
|-|-----------|----------------------|------------|----------------|
| **System prompt** | None | "You are an autonomous programmer working in a special interface..." | "You are a senior software engineer performing a code review..." | Category-specific role (e.g., "senior software engineer performing requirements analysis") |
| **Instance prompt** | Function signature + docstring | GitHub issue text wrapped in "We're solving this issue..." | PR diff + structured review instructions | Category-specific: problem_statement (C3), structured input fields (C1/C2), bugged_diff (C4), bug_report + stack_trace (C5b) |
| **Tools** | None (pure completion) | 11 custom commands (open, edit, search_dir, search_file, find_file, goto, scroll, create, submit) + bash | CLI-based (OCR) or MCP + stdout (Claude/Codex) | `--mode accept-edits --add-dir` for repo access (C3/C5), none for text-only (C1/C2/C4) |
| **Edit mechanism** | N/A | `edit <start>:<end>` + `end_of_edit` sentinel | N/A (reviewer, not editor) | Native agent file editing (agy/claude) |
| **Search mechanism** | N/A | `search_dir`, `search_file`, `find_file` + grep/find | N/A | Native agent tools (agy/claude) |
| **Agent loop** | Single-pass completion | ReAct (discuss → command → observe → repeat) | Single-pass review | Agentic loop with full tool access (C3/C5), single-pass (C1/C2/C4) |
| **Output format** | Raw Python code | Git unified diff (via `submit`) | JSON array of findings | Structured JSON (C1/C2), code files (C3/C5a), git diff (C5b), JSON findings (C4) |
| **Submission** | Stop at `\ndef` boundary | `submit` command | JSON array | Captured via `git diff HEAD` + `git ls-files --others` |

### 5.2 Tool Access Comparison — What the Agent Can Do

```
HumanEval:     [no tools — pure text completion]
                └─ Model sees function signature, outputs function body

SWE-agent:     [custom shell with restricted commands]
                ├─ open / goto / scroll — windowed file viewer
                ├─ edit — line-range replacement with end_of_edit
                ├─ search_dir / search_file / find_file — code search
                ├─ create — new file creation
                ├─ submit — generate diff and terminate
                └─ bash commands (ls, cat, python, grep, git, etc.)
                    BUT no interactive commands (python REPL, vim)

AACR-Bench:    [reviewer — no code editing]
                ├─ OCR: CLI tool, prompt is internal
                └─ Claude/Codex: receives diff, outputs findings JSON
                    No repo access, no file editing, no bash

XHS C1/C2/C4:  [text-in, text-out — no repo access]
                └─ Agent receives structured input, outputs text/JSON
                    Same as AACR-Bench pattern

XHS C3/C5:     [full repo access via agy/claude agent CLI]
                ├─ --mode accept-edits — agent can create/edit any file
                ├─ --add-dir <worktree> — agent has full repo tree
                ├─ bash, python, pytest — any command
                ├─ git — full git access
                └─ No custom commands — uses native agent capabilities
                    More permissive than SWE-agent (no restricted shell)
```

### 5.3 Key Differences in Prompt Design

**HumanEval** gives the model everything it needs in the prompt — the function signature, docstring with examples, and type hints. The task is unambiguous. There is nothing to search for and no context to gather.

**SWE-bench / SWE-agent** gives the model a natural-language issue description (often ambiguous, sometimes with reproduction steps) and drops it into a repo. The model must **explore** — locating relevant files, understanding the codebase, and figuring out what to change. The custom tools (especially the windowed file viewer) are designed to keep context usage manageable.

**AACR-Bench** gives the model the full PR diff inline. The model must **analyze** — finding bugs in someone else's code without being able to run it. No exploration needed, but the diff can be very large (800+ changed lines).

**XHS Agent Eval** varies by category:
- **C1/C2** are closest to HumanEval — structured input, produce structured output, no tools needed
- **C3** is closest to SWE-bench — problem_statement + full repo access + hidden test verification
- **C4** is closest to AACR-Bench — bugged diff + produce findings JSON, no repo access
- **C5a/C5b** are unique — C5a asks the agent to write tests (not fix code), C5b injects a bug before the agent starts (not present in any reference benchmark)
