# C6 / C7 entry format (field reference)

Part 1 covers C6 (environment tasks). Part 2 covers C7 (daily backend bug fixes), which shares the
layout but differs in several fields.

# Part 1: C6 entries

Each C6 entry is one JSON file in `dataset/c6/` (e.g. `C6-01_polyglot_c_py.json`). It describes
one task:
- what the agent is asked to do
- the container it works in
- how the result is checked (hidden from the agent)
- where the task came from and why it was chosen

Supporting files live in `dataset/c6/envs/C6-XX/`.

C6-01 was built first and uses a custom verifier. C6-02..07 are Terminal-Bench 2.0 tasks graded by
their original pytest suites. C6-08 is a FrontierSWE v2 task with a separate verifier container
and a continuous score. Fields that apply only to some entries are marked.

## Top-level fields

| Field | Meaning |
|---|---|
| `instance_id` | Entry ID (`C6-01`). Used with `--entry` and in result directory names. |
| `category` / `category_name` | `C6` / 环境任务（容器化终端）. The harness uses `category` to pick the rubric (`evaluation/rubrics/c6_env.json`). |
| `task_type` | `terminal_task`: the agent works in a shell inside a container, not in the xhs-campaign-service worktree used by C3/C5. |
| `maps_to_journey` | Provenance label, e.g. `External: Terminal-Bench 2.0 / polyglot-c-py`. |
| `rednote_relevance` | Why the task fits Rednote's business or routine work (C6-02 and later). |
| `problem_statement` | The task prompt sent to the agent, copied verbatim from the source benchmark. For host CLI agents (agy/claude), the harness adds an "Environment notes" footer explaining the container and the `task-exec` helper. |

## `environment`: the container the agent works in

| Field | Meaning |
|---|---|
| `type` | `docker`: the task runs in its own image. |
| `dockerfile` | The original Dockerfile and build context (`envs/C6-XX/...`), kept for provenance and rebuilds. |
| `prebuilt_image` | The image actually run: the source benchmark's published image, so the environment matches the source exactly. C6-08 pins it by digest. |
| `workdir` | Task directory (`/app`). For agy/claude it is backed by a host directory, so the agent can edit files directly. |
| `cpus` / `memory` | Resource limits from the source task. Enforced under `--sandbox docker`, not under udocker. |
| `network` | Whether the task needs network access. |
| `agent_timeout_sec` | The agent's time budget (900 s = Terminal-Bench's default). The harness uses `min(--timeout minutes, agent_timeout_sec)`. |
| `initial_state` | What the agent starts with, e.g. an empty `/app`. |
| `udocker_image` | *(C6-08)* Local alias for the digest-pinned image. udocker cannot pull `repo@sha256:...`, so the image is loaded with `scripts/fetch_oci_digest.py`. |
| `per_trial_paths` | *(C6-08)* Extra fresh, empty directories mounted per trial. For example, `/root` hides root-only verifier assets, because the agent runs as fake root under udocker. |
| `container_env` | *(C6-08)* Environment variables set in the container, e.g. `TASK_BUDGET_SECS` for the agent-visible `sandbox-timer`. |
| `init_cmd` | *(C6-08)* Command run once at the start of each trial, e.g. `sandbox-timer start`. |

## `verification`: how pass/fail is decided

The tests are never shown to the agent. They run in the container only after the agent stops.

| Field | Meaning |
|---|---|
| `type` | Grader kind:<br>• `script`: custom verifier (C6-01)<br>• `tb2_pytest`: the original Terminal-Bench pytest suite (C6-02..07)<br>• `harbor_separate`: FrontierSWE's verifier in its own container (C6-08) |
| `script`, `container_path`, `command` | *(script)* The verifier is copied to `container_path` (e.g. `/tmp/verify.py`) and run with `command` (e.g. `--root /app`). Its last stdout line is a JSON verdict: `{"reward": 0 or 1, "reason": ..., "checks": [...]}`. |
| `checks_in_order` | *(C6-01)* What the verifier checks, in order:<br>• only `main.py.c` is left in `/app/polyglot`<br>• gcc compiles it<br>• both the Python and C programs print the right Fibonacci numbers for n = 42, 10, 0 |
| `equivalent_to`, `original_tests` | *(C6-01)* The custom verifier runs the same checks, in the same order, as the original `test_fibonacci_polyglot`. The original tests are kept for reference. |
| `tests_dir`, `command` | *(tb2_pytest)* The original tests are copied to `/tests` and `bash /tests/grader.sh` is run. |
| `grader_derivation` | *(tb2_pytest)* `grader.sh` is the original `tests/test.sh` with exactly four setup lines removed: `apt-get update`, `apt-get install -y curl`, the uv installer and `source $HOME/.local/bin/env`. The harness provides uv/uvx at `/opt/xhs`. |
| `reward` | Plain-language scoring rule. For tb2_pytest, the trial passes iff the original script writes `1` to `/logs/verifier/reward.txt`. Per-test results come from the CTRF report. |
| `hidden_from_agent` | `true`: the tests are copied into the container only at grading time. |
| `tests` | *(tb2_pytest)* Names of the hidden tests, for reference. |
| `timeout_sec` | Time limit for the grader. |
| `verifier_image`, `udocker_verifier_image` | *(C6-08)* The separate verifier image (digest-pinned) and its local udocker alias. |
| `artifact_excludes` | *(C6-08)* Files left out when copying `/app` into the verifier container (build caches, built `.so` files). Taken from the task's `[[artifacts]]`. |
| `pass_threshold` | *(C6-08)* The score is continuous (0–1); a trial counts as passed at ≥ this value (0.1). The mean score over trials is the primary metric. Binary graders default to 1.0. |

## `gold_solution`: the reference solution

| Field | Meaning |
|---|---|
| `script` | The source benchmark's own `solve.sh`. |
| `run_in` | Directory it runs in (`/app`). |
| `dir`, `timeout_sec` | *(C6-08)* The solution ships as a directory (script plus sources). It is copied to `/solution` and run with `HARBOR_ORACLE_FLAG` set, as in Harbor's oracle stage. |
| `expected_reward`, `note` | *(C6-08)* FrontierSWE ships a placeholder oracle that scores 0.0 by design. Validation checks the verifier's evidence fields (build, provenance, correctness, measurement) instead of the score. |

The gold solution is used only to validate the task: `--agent gold` should pass and
`--agent empty` should fail.

## `evaluation_rubric`

Path to the rubric (`evaluation/rubrics/c6_env.json`). It has one dimension, D1: the pass rate over
trials, snapped to the tiers 100/80/60/40/20/0.

## `source`: where the task came from

| Field | Meaning |
|---|---|
| `benchmark`, `repo`, `commit`, `path` | Exact origin, e.g. the Terminal-Bench 2.0 repo at commit `69671fb`, task directory `polyglot-c-py`. |
| `author`, `difficulty`, `category`, `expert_time_estimate_min` | Metadata from the source task's `task.toml`. |
| `task_page` | *(C6-08)* Public task page. |
| `original_scoring` | How the source benchmark scores the task. |
| `conversion_changes` | Every change made when converting the task to this format. Examples: "copied verbatim"; "grader drops only the curl/uv install lines"; *(C6-08)* "2 h agent budget instead of 20 h". |

## `discrimination`: why the task was chosen

These values are computed from public per-model leaderboard results. See
`deliverables/REPORT.md` in the analysis workspace.

| Field | Meaning |
|---|---|
| `what_it_measures` | The skill the task actually tests. C6-01, for example, mostly tests workspace hygiene: 79% of leaderboard failures were leftover files such as `cmain`, not wrong code. |
| `n_models` | Number of leaderboard systems with results on this task. |
| `mean_pass_rate` / `mean_score` | Average result across those systems (difficulty). |
| `std` | Spread of results across systems. |
| `disc_r` | Item-rest correlation: Pearson r between a system's result on this task and its mean on all other tasks. High means the task consistently separates strong systems from weak ones. |
| `frontier_std`, `frontier_disc_r`, `frontier_mean` | The same metrics computed on the top half of systems only, i.e. whether the task separates strong systems *from each other*. |
| `tier` | `frontier (separates top models)` or `broad (strong vs weak)`, per the selection thresholds:<br>• broad: std ≥ 0.30, disc_r ≥ 0.50, 0.15 ≤ mean ≤ 0.85<br>• frontier: frontier_std ≥ 0.25, frontier_disc_r ≥ 0.30, 0.1 ≤ frontier_mean ≤ 0.9 |
| `leaderboard_failure_modes` | *(C6-01)* Leaderboard trials grouped by failure cause. |
| `caveat` | *(C6-08)* Why the reference scores are not directly comparable (20 h budget vs 2 h here). |

## `reference_scores`

The published per-system results for this task, used to compare your own runs against the
leaderboard. Each row has:
- `submission`, `agent`, `model`
- `pass_rate` (binary tasks) or `score` (continuous tasks)
- `n_runs`
- for FrontierSWE also `mean_hours` and `mean_cost_usd`

# Part 2: C7 entries

Each C7 entry is one JSON file in `dataset/c7/` (e.g. `C7-01_django__django-15957.json`). It wraps
one SWE-bench Verified issue: the agent fixes a real bug in a real repository, and hidden tests
decide whether it is resolved. C7 entries are selected for closeness to Rednote backend daily work
(Django ORM, MySQL, JSONField, i18n, HTTP proxies), not for model discrimination.

Supporting files live in `dataset/c7/envs/C7-XX/`:

| File | Meaning |
|---|---|
| `eval.sh` | The official SWE-bench eval script, generated by `make_test_spec` in swebench 4.1.0. It:<br>1. resets the files touched by the hidden test patch to `base_commit`<br>2. applies the test patch<br>3. runs the instance's test command between the `>>>>> Start/End Test Output` markers<br>4. resets the test files again |
| `instance.json` | The full SWE-bench Verified row. The grader feeds it to swebench's official grading code. It contains the gold patch and the test patch, so it is never shown to the agent. |
| `gold.patch` | The upstream fix from SWE-bench, kept for reference. |
| `gold.sh` | Applies `gold.patch` in `/testbed`. Used only for validation (`--agent gold`). |

The build script is `scripts/build_xhs_c7_entries.py` in the analysis workspace. It must run with
the grader venv (`~/.cache/xhs_c6/swebench-venv`, swebench==4.1.0).

## Top-level fields

| Field | Meaning |
|---|---|
| `instance_id` | Entry ID (`C7-01`). Used with `--category c7 --entry C7-01` and in result directory names (`results/c7_runs/...`). |
| `category` / `category_name` | `C7` / 日常后端缺陷修复（容器化仓库）. Selects the rubric `evaluation/rubrics/c7_swe.json`. |
| `task_type` | `repo_bugfix`: edit an existing repository to fix an issue. |
| `maps_to_journey` | Provenance label, e.g. `External: SWE-bench Verified / django__django-15957`. |
| `rednote_relevance` | The Rednote scenario the issue represents, e.g. feed/comment pagination with top-N prefetch. |
| `daily_work_scenario` | The concrete routine task behind it, e.g. "latest 3 comments for each note in a feed page". |
| `problem_statement` | The prompt sent to the agent: the GitHub issue text verbatim, inside `<issue>` tags. It is wrapped in a short instruction giving the repo, the checkout path (`/testbed`) and the base commit, and saying not to modify existing tests because hidden tests run afterwards. As in C6, agy/claude also get the "Environment notes" footer. |

## `environment`

| Field | Meaning |
|---|---|
| `type` | `docker`. |
| `prebuilt_image` | The official SWE-bench instance image, `swebench/sweb.eval.x86_64.<owner>_1776_<repo>-<n>:latest`. The repo is at `/testbed` with the instance's conda env `testbed` already set up. |
| `workdir` | `/testbed`. For agy/claude this is a host copy of the image's `/testbed`, bind-mounted back into the container. |
| `network` | `true` (some eval scripts reinstall the package, e.g. `pip install .` for requests). |
| `agent_timeout_sec` | Agent budget: 1800 s (30 min). The harness uses `min(--timeout, agent_timeout_sec)`. |
| `initial_state` | Repo at `base_commit` with the instance's conda env. |

## `verification`

| Field | Meaning |
|---|---|
| `type` | `swebench`. The grading flow:<br>1. record `git diff <base_commit>` in `/testbed` as the model patch (informational)<br>2. run `eval.sh` in the container, with stdout and stderr merged as in the official harness<br>3. grade the log on the host with swebench's own log parser and `get_eval_report` (`evaluation/swebench_grade.py`) |
| `eval_script` | Path to `eval.sh`. |
| `instance` | Path to `instance.json` (the SWE-bench row used by the grader). |
| `timeout_sec` | Time limit for `eval.sh` (1800 s). |
| `reward` | 1 iff **resolved**: every FAIL_TO_PASS test now passes (the fix works) and every PASS_TO_PASS test still passes (nothing regressed). This is the SWE-bench rule. |
| `hidden_from_agent` | `true`: the test patch and test lists are applied only at grading time. |
| `fail_to_pass` | Names of the tests that fail before the fix and must pass after it. |
| `pass_to_pass_count` | Number of tests that already pass and must keep passing (the full list is in `instance.json`). |

Each trial's `verdict.json` holds:
- `reward` and `reason` (e.g. `resolved (F2P 2/2, P2P 185/185)`)
- `checks`: per-test pass/fail for FAIL_TO_PASS and PASS_TO_PASS
- `swebench_report`: swebench's raw report
- `model_patch`: the agent's diff
- `eval_log_tail`

## `gold_solution`

| Field | Meaning |
|---|---|
| `script` | `envs/C7-XX/gold.sh`, which applies the upstream fix (`git apply`). |
| `run_in` | `/testbed`. |

The gold patch should resolve the issue and an untouched repo (`--agent empty`) should not.

## `evaluation_rubric`

`evaluation/rubrics/c7_swe.json`. It has one dimension, D1: the resolve rate over trials, snapped
to the tiers 100/80/60/40/20/0. This mirrors C6.

## `source`

| Field | Meaning |
|---|---|
| `benchmark`, `dataset` | `SWE-bench Verified`, `princeton-nlp/SWE-bench_Verified`. |
| `instance_id`, `repo`, `version` | The SWE-bench instance (e.g. `django__django-15957`), the GitHub repo, and the repo version (which determines the environment). |
| `base_commit` | The commit the agent starts from. |
| `created_at` | When the issue/PR was created. |
| `difficulty` | SWE-bench Verified's human estimate (e.g. `15 min - 1 hour`, `1-4 hours`). |
| `swebench_harness_version` | The swebench package version used to generate `eval.sh` and to grade (4.1.0). |
| `conversion_changes` | What differs from the official harness:<br>• the issue is wrapped in a short instruction<br>• `eval.sh` runs on the agent's edited `/testbed`, not on a diff applied to a fresh container |
| `contamination_note` | SWE-bench Verified has been public since 2024 and the gold fix is in upstream history, so models may have seen it. |

## `discrimination`

| Field | Meaning |
|---|---|
| `selected_for` | `daily-work relevance (not discrimination)`. |
| `n_systems` | Number of recent SWE-bench leaderboard submissions with results on this instance. |
| `mean_resolve_rate` | Fraction of those submissions that resolved it (difficulty). |
| `disc_r` | Item-rest correlation, as in C6. Informational only. |

## `reference_scores`

Results for this instance from recent SWE-bench submissions whose names mention Gemini, Claude or
GPT (up to 30 rows). Each row has:
- `submission`: the leaderboard system, e.g. `20251120_livesweagent_gemini-3-pro-preview`
- `resolved`: 0 or 1, from a single run

