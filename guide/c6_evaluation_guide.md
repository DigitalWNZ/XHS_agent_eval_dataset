> [!NOTE]
> This guide was written for the first containerized entry, `polyglot-c-py`, when it was
> C6-01. It became C7-01 on 2026-10-14 and **C6-05** (discriminative) on 2026-10-15. Read "C6-01"
> below as today's C6-05 (`--category c6 --entry C6-05`).
> It now uses the original Terminal-Bench pytest suite (`tb2_pytest`) instead of the custom
> verifier described in section 2. Section 3's scoring is also outdated: D1 is now snapped to the
> tiers in `c6_discriminative.json` / `c7_daily.json` / `c8_hard.json`, and D2 (LLM-judge code quality) was added; see
> [coding_rubric.md](coding_rubric.md). For the current layout, IDs and field reference, see
> [c6_entry_format.md](c6_entry_format.md).

# C6 — Environment Tasks (Containerized Terminal) Evaluation Guide

C6 adds **externally sourced, model-discriminative tasks** to the XHS benchmark. Unlike C3/C5, a C6 task doesn't run in the `xhs-campaign-service` git worktree. Each entry brings **its own environment (a Docker image)**, and a **verifier script** grades it inside that environment after the agent finishes.

The first entry, `C6-01`, is Terminal-Bench 2.0's `polyglot-c-py`. Across 75 leaderboard agent+model submissions, it is one of the tasks whose scores vary most between models, and that variation tracks overall model strength.

---

## 1. Entry format (`dataset/c6/C6-XX_*.json`)

| Field | Type | Meaning |
|---|---|---|
| `instance_id` | string | `C6-01`, … |
| `category`, `category_name`, `task_type` | string | `C6`, `环境任务（容器化终端）`, `terminal_task` |
| `maps_to_journey` | string | Provenance label (e.g. `External: Terminal-Bench 2.0 / polyglot-c-py`) |
| `problem_statement` | string | **Exact** text given to the agent (verbatim from the source benchmark) |
| `environment` | object | `type: docker`, `dockerfile` (path in this repo), `prebuilt_image` (fallback), `workdir` (usually `/app`), `cpus`, `memory`, `network`, `agent_timeout_sec`, `initial_state` |
| `verification` | object | `type: script`, `script` (path in this repo), `container_path`, `command`, `timeout_sec`, `checks_in_order` (readable criteria), `equivalent_to`, `original_tests` |
| `gold_solution` | object | `script` (shell, run in `run_in`); used to validate the task and verifier |
| `evaluation_rubric` | string | `evaluation/rubrics/c6_discriminative.json` (C6) or `c7_daily.json` (C7) |
| `source` | object | Original benchmark, repo, commit, path, author, original scoring, and what changed in conversion |
| `discrimination` | object | Why the task separates models: leaderboard `n_models`, mean pass rate, std, `disc_r` (item–rest correlation), frontier-tier metrics, failure-mode breakdown |
| `reference_scores` | array | Per-submission leaderboard pass rates (`agent`, `model`, `pass_rate`, `n_runs`) to compare your runs against |

Each entry's environment assets live in `dataset/c6/envs/C6-XX/`:
`Dockerfile`, `verify.py`, `solve.sh`, and `original_tests/` (the source benchmark's tests, kept for traceability).

## 2. Verifier contract

The verifier runs **in the same container the agent used, after the agent stops**, so it grades the final state of the workspace. The agent never sees the verifier or its result.

- The last non-empty stdout line is JSON: `{"reward": 0|1, "reason": "...", "checks": [...]}`
- The exit code is 0 when reward is 1. It's informational only; the score comes from the JSON.

**C6-01 checks, in order (all must pass):**
1. `/app/polyglot` contains **exactly** `main.py.c`. A leftover `cmain` or scratch file fails the task.
2. `gcc /app/polyglot/main.py.c -o /app/polyglot/cmain` exits 0 (warnings are fine).
3. For n = 42, 10, 0: `python3 main.py.c n` and `./cmain n` both exit 0 and print `267914296`, `55`, `0`.

## 3. Scoring (`evaluation/rubrics/c6_discriminative.json` / `c7_daily.json`)

- Each trial gets a binary reward from the verifier.
- **D1 Task Success (100 pts):** pass rate over N trials (default 5), snapped to tiers 100/80/60/40/20/0. `total_score = D1`. Pass threshold: 60.
- Also reported: `pass_rate`, `pass_at_k` (unbiased estimator), and per-trial `reason`.
- Infrastructure failures are recorded as `infra_error` and count as 0. Rerun if you see them.
- C6 is **not in the composite score**; the manifest weights are unchanged.

## 4. Running

```bash
# Validate the task and verifier (should score 100 and 0)
python evaluation/run_benchmark.py --category c6 --entry C6-01 --agent gold  --model none --trials 2
python evaluation/run_benchmark.py --category c6 --entry C6-01 --agent empty --model none --trials 2

# Evaluate a model with the built-in agent (commands run INSIDE the container)
export GEMINI_API_KEY=...
python evaluation/run_benchmark.py --category c6 --entry C6-01 --agent loop --model gemini-3.5-flash --trials 5

# Evaluate with the repo's CLI agents (agy / claude)
python evaluation/run_benchmark.py --category c6 --entry C6-01 --agent agy --model gemini-3.8-flash-high --trials 5

# No Docker available: bubblewrap fallback (host toolchain, no network, home hidden)
... --sandbox bwrap
```

| `--agent` | How it acts | Fidelity |
|---|---|---|
| `loop` | Built-in loop: the model replies with JSON `{analysis, commands, task_complete}`, and each command runs via `docker exec` inside the task container. Stops at `task_complete` or `agent_timeout_sec` (900 s for C6-01). | Highest |
| `agy`, `claude` | The usual `invoke_agent()` CLI run, on the host in a temp workspace **bind-mounted to `/app`** in the container. The prompt gets an "Environment notes" footer with a `task-exec '<cmd>'` helper for running commands inside the container. | Good. The agent's own tools run on the host, so it should test with `task-exec`. |
| `gold` | Runs `gold_solution.script` inside the container | Validation |
| `empty` | Does nothing | Validation (must fail) |

**Outputs:**
- `results/c6_<agent>_<model>_<ts>.json`: the standard report (`benchmark`, `category`, `agent`, `model`, `entries`).
- `results/c6_runs/<entry>_<agent>_<model>_<ts>/trial_N/{transcript.json, verdict.json}`: per-trial details.

## 5. What C6-01 actually measures

The leaderboard's verifier logs (368 trials) show that **79% of failures are leftover files** in `/app/polyglot`. Usually it's the `cmain` binary that the prompt itself tells the agent to build, and wrong output almost never happens. So C6-01 mainly measures **workspace hygiene and implicit-requirement inference**, and the **agent harness matters**: Claude Opus 4.6 scores 0/5 under five different agents and 5/5 under one.

To measure polyglot or coding skill alone, the task would need one of these changes:
- add "Leave only main.py.c in /app/polyglot" to `problem_statement`, or
- make verifier check 1 ignore extra files.

Either change is expected to push pass rates up and reduce discrimination.
