# XHS Agent Eval Benchmark — Deployment Guide

This guide walks a new user through deploying the full XHS Coding Agent Evaluation Benchmark from scratch in a clean environment.

---

## Architecture Overview

The benchmark consists of **two separate git repositories** and **two CLI tools**:

```
┌─────────────────────────────────────────────────────────────┐
│  xhs_agent_eval/                (Repo 1: benchmark itself)  │
│  ├── dataset/                   34 JSON evaluation entries  │
│  │   ├── c1/  (5 entries)                                   │
│  │   ├── c2/  (5 entries)                                   │
│  │   ├── c3/  (8 entries)                                   │
│  │   ├── c4/  (8 entries)                                   │
│  │   └── c5/  (5 C5a + 3 C5b entries)                      │
│  ├── evaluation/                                            │
│  │   ├── run_benchmark.py       Main runner (all categories)│
│  │   ├── harness.py             Standalone evaluator        │
│  │   └── rubrics/               6 scoring rubric JSONs      │
│  ├── guide/                     Evaluation guides (C1-C5)   │
│  ├── deck/                      Presentation decks (C1-C5)  │
│  ├── results/                   Output directory (gitignored)│
│  └── xhs-campaign-service/     ← Repo 2 (nested, separate) │
│      ├── app/                   FastAPI application code     │
│      ├── tests/                 Existing test suite          │
│      ├── requirements.txt       Python dependencies          │
│      └── pyproject.toml         Project config               │
└─────────────────────────────────────────────────────────────┘
```

**Repo 1** (`XHS_agent_eval_dataset`) contains the benchmark dataset, evaluation harness, rubrics, and documentation.

**Repo 2** (`xhs-campaign-service`) is a realistic FastAPI codebase that the benchmark evaluates agents against. Categories C3, C5a, and C5b create git worktrees from this repo for the agent to work in.

---

## Prerequisites

### System Requirements

| Requirement | Minimum | Notes |
|-------------|---------|-------|
| OS | Linux (tested on Debian 13) | macOS should work but is untested |
| Python | 3.11+ (tested on 3.13) | Required by xhs-campaign-service |
| Git | 2.20+ | Needs `git worktree` support |
| Disk | 5 GB free | Worktrees + results accumulate |
| Memory | 4 GB | Agent invocations may use more |

### Required CLI Tools

You need at least one of these coding agent CLIs installed:

**Option A: Antigravity CLI (`agy`)** — default agent

```bash
# Install Antigravity CLI (check internal docs for latest instructions)
# After installation, verify:
which agy
agy --version
```

**Option B: Claude Code CLI (`claude`)**

```bash
# Install Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Verify:
which claude
claude --version
```

### Authentication

**For Antigravity (`agy`):**
The harness sets `AGY_ADC_AUTH=true` automatically, which uses Google Application Default Credentials. Set up ADC before running:

```bash
gcloud auth application-default login
```

Or if running in a GCP environment (Cloud Shell, Compute Engine, etc.), ADC is typically pre-configured.

**For Claude Code (`claude`):**
Authenticate via the CLI's built-in auth flow:

```bash
claude auth login
```

---

## Step 1: Clone the Benchmark Repo

```bash
git clone https://github.com/DigitalWNZ/XHS_agent_eval_dataset.git xhs_agent_eval
cd xhs_agent_eval
```

---

## Step 2: Clone the Campaign Service Repo

The campaign service is a **separate repository** that must be cloned inside the benchmark directory. The harness expects it at `xhs_agent_eval/xhs-campaign-service/`.

```bash
# From inside xhs_agent_eval/
git clone https://github.com/DigitalWNZ/xhs-campaign-service.git
```

After cloning, verify the required base commits exist:

```bash
cd xhs-campaign-service
git log --oneline
```

You should see (at minimum) these two commits that the C3/C5 entries reference:

```
88d9911 feat: initial project scaffold with user service
07968bf feat: implement two-level review workflow (brand + compliance)
```

If either is missing, the harness will fail when setting up worktrees.

```bash
cd ..  # back to xhs_agent_eval/
```

---

## Step 3: Install Python Dependencies

The campaign service needs its dependencies installed for worktree-based categories (C3, C5a, C5b):

```bash
pip install -r xhs-campaign-service/requirements.txt
```

This installs:
- `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `pydantic-settings` — application framework
- `httpx`, `redis`, `celery`, `asyncpg`, `alembic` — integrations
- `pytest`, `pytest-asyncio`, `pytest-cov` — test execution (used by harness)
- `ruff`, `mypy` — linting (not required by harness, but part of the project)

The harness also runs `pip install -e .` in each worktree it creates (via `setup_worktree()`), so the campaign service's `pyproject.toml` must be valid.

**No additional dependencies are needed for the benchmark harness itself** — `run_benchmark.py` uses only the Python standard library plus `pytest` (already in the requirements above).

---

## Step 4: Verify the Directory Structure

Run this check to confirm everything is in place:

```bash
# From xhs_agent_eval/
echo "=== Benchmark repo ==="
ls dataset/c1 dataset/c2 dataset/c3 dataset/c4 dataset/c5
ls evaluation/run_benchmark.py evaluation/rubrics/*.json
ls dataset/manifest.json

echo "=== Campaign service repo ==="
ls xhs-campaign-service/pyproject.toml
ls xhs-campaign-service/requirements.txt
ls xhs-campaign-service/app/
git -C xhs-campaign-service log --oneline | head -5

echo "=== Agent CLIs ==="
which agy 2>/dev/null && echo "agy: OK" || echo "agy: NOT FOUND"
which claude 2>/dev/null && echo "claude: OK" || echo "claude: NOT FOUND"
```

Expected output: all files listed, both commits visible, at least one agent CLI found.

---

## Step 5: Run a Dry Run

Before spending agent tokens, do a dry run to verify the harness loads data correctly:

```bash
# C1 dry run (text-in/text-out, no worktree needed)
python evaluation/run_benchmark.py --category c1 --entry C1-01 --dry-run

# C3 dry run (verify it can load the problem_statement)
python evaluation/run_benchmark.py --category c3 --entry C3-01 --dry-run
```

The dry run prints the first 500 characters of the prompt without invoking the agent.

---

## Step 6: Run Individual Entries

### C1/C2 (LLM-as-Judge, no repo access needed)

```bash
# Run a single C1 entry
python evaluation/run_benchmark.py --category c1 --entry C1-01 --agent agy --model gemini-3.8-flash-high

# Run a single C2 entry
python evaluation/run_benchmark.py --category c2 --entry C2-01 --agent agy --model gemini-3.8-flash-high
```

These are the simplest categories — text in, text out, scored by LLM judge. No git worktree involved.

### C3 (Code Generation, requires worktree)

```bash
python evaluation/run_benchmark.py --category c3 --entry C3-08 --agent agy --model gemini-3.8-flash-high --timeout 30
```

This will:
1. Create a git worktree at `/tmp/c3-c3-08-.../repo` from commit `07968bf`
2. Run `pip install -e .` in the worktree
3. Send the `problem_statement` to the agent with full file-write access
4. Capture the agent's code changes as a patch
5. Apply the hidden `test_patch`
6. Run FAIL_TO_PASS and PASS_TO_PASS tests
7. Send the patch to the LLM judge for D3-D7 scoring
8. Clean up the worktree

### C4 (Code Review, no repo access)

```bash
python evaluation/run_benchmark.py --category c4 --entry C4-01 --agent agy --model gemini-3.8-flash-high
```

### C5a (Test Generation, requires worktree)

```bash
python evaluation/run_benchmark.py --category c5a --entry C5a-01 --agent agy --model gemini-3.8-flash-high
```

### C5b (Debugging, requires worktree + bug injection)

```bash
python evaluation/run_benchmark.py --category c5b --entry C5b-01 --agent agy --model gemini-3.8-flash-high
```

---

## Step 7: Run All Entries in a Category

```bash
# Run all 8 C3 entries
python evaluation/run_benchmark.py --category c3 --all --agent agy --model gemini-3.8-flash-high --timeout 30

# Run all 5 C1 entries
python evaluation/run_benchmark.py --category c1 --all --agent agy --model gemini-3.8-flash-high
```

---

## Step 8: Run the Full Benchmark

Run all categories sequentially. Estimated time: 3-5 hours with `gemini-3.8-flash-high`, depending on agent speed.

```bash
for cat in c1 c2 c3 c4 c5a c5b; do
    echo "========== Running $cat =========="
    python evaluation/run_benchmark.py --category $cat --all --agent agy --model gemini-3.8-flash-high --timeout 30
done
```

---

## Output and Results

### Results Directory

All results are saved to `results/`:

```
results/
├── c1_agy_gemini-3.8-flash-high_20260916_160843.json    ← Category report
├── c3_agy_gemini-3.8-flash-high_20260916_141138.json
├── trajectories/                                         ← Agent conversation logs
│   ├── C3-01_agy_gemini-3.8-flash-high.jsonl
│   └── ...
├── outputs/                                              ← Raw agent text responses
│   ├── C1-01_agy_gemini-3.8-flash-high.json
│   └── ...
└── patches/                                              ← Agent code patches (C3/C5b)
    ├── C3-01_agy_gemini-3.8-flash-high.patch
    └── ...
```

### Result JSON Structure

Each category report contains:

```json
{
  "benchmark": "xhs-agent-eval",
  "category": "C3",
  "agent": "agy",
  "model": "gemini-3.8-flash-high",
  "timestamp": "2026-09-16T14:11:38+00:00",
  "entries": [
    {
      "instance_id": "C3-01",
      "agent_elapsed_seconds": 142.3,
      "usage": {"input_tokens": 12000, "output_tokens": 8500, "total_tokens": 20500},
      "num_turns": 15,
      "test_results": {"f2p_passed": 20, "f2p_total": 23, "p2p_passed": 13, "p2p_total": 13},
      "scores": {
        "resolved": false,
        "D1_functional_correctness": 0.87,
        "D2_regression_safety": 1.0
      }
    }
  ]
}
```

### Console Summary

The harness prints a summary table after each category run:

```
============================================================
SUMMARY — C3
============================================================
Entry          F2P      P2P  Resolved    Time   Tokens  Turns
------------------------------------------------------------
C3-01        20/   23  13/   13       NO   142.3s   20.5K     15
C3-08         8/    8  82/   82      YES    98.7s   15.2K     12
```

---

## Switching Agents

To evaluate a different agent or model, change `--agent` and `--model`:

```bash
# Evaluate with Claude Code instead of Antigravity
python evaluation/run_benchmark.py --category c3 --entry C3-01 --agent claude --model claude-sonnet-5

# Evaluate with a different Gemini model
python evaluation/run_benchmark.py --category c3 --entry C3-01 --agent agy --model gemini-3.8-pro
```

Results files include the agent and model in the filename, so different evaluations don't overwrite each other.

---

## Composite Score Calculation

After running all categories, compute the composite score using these weights:

| Category | Weight | Entries |
|----------|--------|---------|
| C1 (Requirements) | 15% | 5 |
| C2 (Design) | 15% | 5 |
| C3 (Code Gen) | 30% | 8 |
| C4 (Code Review) | 20% | 8 |
| C5a (Test Gen) | 12% | 5 |
| C5b (Debug) | 8% | 3 |

```
Composite = 0.15×C1_avg + 0.15×C2_avg + 0.30×C3_avg + 0.20×C4_avg + 0.12×C5a_avg + 0.08×C5b_avg
```

Grade mapping:
- **S (90-100):** Expert level — production-ready
- **A (80-89):** Strong — reliable for most tasks
- **B (70-79):** Competent — usable with oversight
- **C (60-69):** Marginal — significant gaps
- **D (<60):** Insufficient

---

## Troubleshooting

### `git worktree add` fails

```
fatal: '88d9911' is not a commit
```

The campaign service repo doesn't have the required commits. Make sure you cloned the full repo (not a shallow clone):

```bash
cd xhs-campaign-service
git fetch --unshallow   # if it was a shallow clone
git log --oneline       # verify 88d9911 and 07968bf exist
```

### Worktree cleanup after crashes

If the harness crashes mid-run, worktrees may be left behind in `/tmp/`:

```bash
# List orphaned worktrees
git -C xhs-campaign-service worktree list

# Remove orphaned worktrees
git -C xhs-campaign-service worktree prune

# Clean up temp directories
rm -rf /tmp/c3-* /tmp/c5a-* /tmp/c5b-*
```

### `pip install -e .` fails in worktree

The worktree runs `pip install -e .` to make imports work. If this fails:

```bash
# Check that pyproject.toml is valid
cat xhs-campaign-service/pyproject.toml

# Try installing manually
cd /tmp/c3-c3-01-.../repo
pip install -e . --break-system-packages
```

Common fix: ensure `pip` is recent enough (`pip install --upgrade pip`).

### `test_patch` fails to apply

```
Test patch failed to apply: error: patch does not apply
```

This usually means the agent created a file at a path that conflicts with the test_patch. The harness deletes conflicting files before applying (lines 906-911 of `run_benchmark.py`), but if the agent modified a file the test_patch also modifies, the apply can fail. This is expected behavior — the entry scores 0 on D1/D2.

### Agent timeout

```
TIMEOUT after 30 minutes
```

Increase the timeout for complex entries:

```bash
python evaluation/run_benchmark.py --category c3 --entry C3-01 --timeout 60
```

C3 new-feature entries (C3-01 through C3-05) typically take 2-5 minutes. Amendment entries (C3-06 through C3-08) are faster.

### `AGY_ADC_AUTH` / authentication errors

```
Error: Could not authenticate
```

For `agy`: Run `gcloud auth application-default login` and verify credentials.

For `claude`: Run `claude auth login` and follow the prompts.

### Judge scoring fails to parse

```
Judge response could not be parsed as JSON
```

The LLM judge sometimes returns malformed JSON. The harness has regex fallback patterns (line 433 of `run_benchmark.py`) that try to extract scores from markdown fences or partial JSON. If all parsing fails, the judge dimensions will show `"note": "Judge response could not be parsed as JSON"` in the results — the automated dimensions (D1/D2 for C3, recall/precision for C4) are still valid.

---

## File Reference

| File | Purpose |
|------|---------|
| `evaluation/run_benchmark.py` | Main benchmark runner — handles all 6 categories |
| `evaluation/harness.py` | Standalone evaluator for pre-captured agent output |
| `evaluation/run_c3.py` | Legacy C3-only runner (superseded by run_benchmark.py) |
| `evaluation/rubrics/c1_requirements.json` | C1 scoring rubric with judge prompt template |
| `evaluation/rubrics/c2_design.json` | C2 scoring rubric |
| `evaluation/rubrics/c3_codegen.json` | C3 scoring rubric (7 dimensions) |
| `evaluation/rubrics/c4_review.json` | C4 scoring rubric with matching logic |
| `evaluation/rubrics/c5a_testing.json` | C5a scoring rubric |
| `evaluation/rubrics/c5b_debug.json` | C5b scoring rubric |
| `dataset/manifest.json` | Full dataset manifest with all entries and metadata |
| `guide/c1_evaluation_guide.md` | Detailed C1 evaluation guide |
| `guide/c2_evaluation_guide.md` | Detailed C2 evaluation guide |
| `guide/c3_evaluation_guide.md` | Detailed C3 evaluation guide |
| `guide/c4_evaluation_guide.md` | Detailed C4 evaluation guide |
| `guide/c5_evaluation_guide.md` | Detailed C5a + C5b evaluation guide |

---

## Quick Start Checklist

```
[ ] 1. Clone benchmark repo (XHS_agent_eval_dataset)
[ ] 2. Clone campaign service repo inside benchmark dir
[ ] 3. Verify commits 88d9911 and 07968bf exist in campaign service
[ ] 4. pip install -r xhs-campaign-service/requirements.txt
[ ] 5. Install agy or claude CLI
[ ] 6. Set up authentication (gcloud ADC or claude auth)
[ ] 7. Dry run: python evaluation/run_benchmark.py --category c1 --entry C1-01 --dry-run
[ ] 8. Real run: python evaluation/run_benchmark.py --category c1 --entry C1-01
[ ] 9. Check results/ for output
```
