# C6 / C7 / C8 / C9 entry format (field reference)

C6, C7, C8 and C9 are the containerized categories. They share the harness (`evaluation/env_runner.py`)
and the entry layout; they differ in purpose (layout of 2026-10-15, chosen from the 2026-10-14 campaign:
claude-opus-5-5, gemini-3.6-flash-high, gemini-3.8-flash-high, gemini-4-argon-high, 3 trials each):

| Category | Name | Entries | Purpose | Rubric |
|---|---|---|---|---|
| C6 | 区分度任务 Discriminative | C6-01..07 | Pass rates differ across the setups but no single setup dominates (campaign: Claude 62%, gemini-3.8 57%, Argon 57%, gemini-3.6 29%). Use C6 to rank models. | `evaluation/rubrics/c6_discriminative.json` |
| C7 | 日常工作任务 Daily work | C7-01..11 | Routine engineering most setups solve (campaign pass rates 85–100%); code quality (D2) does most of the separating. | `evaluation/rubrics/c7_daily.json` |
| C8 | 高难任务 Hard | C8-01..03 | Only the strongest setup solved them reliably, or most setups ran out of time (campaign: Claude 8/9, gemini-3.6 3/9, Argon 1/9, gemini-3.8 0/9). | `evaluation/rubrics/c8_hard.json` |
| C9 | 客户提供任务 Customer-provided | C9-01 | Real requirements provided by the customer, kept verbatim plus an evaluation contract (deliverable path, test hook, deterministic business rules). | `evaluation/rubrics/c9_customer.json` |

All categories mix source types. An entry's fields depend on its source type, not on its category:

| Source type | Verifier `type` | C6 | C7 | C8 | Described in |
|---|---|---|---|---|---|
| Terminal-Bench 2.0 | `tb2_pytest` | C6-01, C6-03..06 | C7-02 | C8-03 | Part 1 |
| FrontierSWE v2 | `harbor_separate` (continuous score) | — | — | C8-02 | Part 1 |
| SWE-bench Verified | `swebench` | — | C7-03..08 | C8-01 | Part 2 |
| DeepSWE v1.1 | `deepswe` | C6-02, C6-07 | C7-01, C7-09..11 | — | Part 3 |

**Restructures, `former_id` and `id_history`.** Before 2026-10-14 the entries were split by source
(C6 = Terminal-Bench / FrontierSWE, C7 = SWE-bench, C8 = DeepSWE). `archive/migrations/restructure_c6_c7.py` regrouped
them into C6 (7) / C7 (14) on 2026-10-14, and `archive/migrations/restructure_v2.py` regrouped those into C6 (7) /
C7 (11) / C8 (3) on 2026-10-15. Each entry keeps the previous ID in `former_id` and every ID it had in
`id_history`. Raw run folders (`results/c{6,7,8}_runs/<recorded id>_...`) keep the ID used when they ran;
`results/id_mapping.json` has one epoch per restructure, and the report scripts and the quality grader map
recorded IDs through every later epoch (`tools/idmap.py`).

| Current | 2026-10-14 | 2026-10-13 | | Current | 2026-10-14 | 2026-10-13 |
|---|---|---|---|---|---|---|
| C6-01 | C6-01 | C6-06 | | C7-05 | C7-07 | C7-04 |
| C6-02 | C6-03 | C8-02 | | C7-06 | C7-08 | C7-05 |
| C6-03 | C6-04 | C6-04 | | C7-07 | C7-09 | C7-06 |
| C6-04 | C6-06 | C6-02 | | C7-08 | C7-10 | C7-07 |
| C6-05 | C7-01 | C6-01 | | C7-09 | C7-11 | C8-01 |
| C6-06 | C7-03 | C6-05 | | C7-10 | C7-13 | C8-05 |
| C6-07 | C7-12 | C8-04 | | C7-11 | C7-14 | C8-06 |
| C7-01 | C6-02 | C8-03 | | C8-01 | C6-05 | C7-01 |
| C7-02 | C7-04 | C6-07 | | C8-02 | C6-07 | C6-08 |
| C7-03 | C7-05 | C7-02 | | C8-03 | C7-02 | C6-03 |
| C7-04 | C7-06 | C7-03 | |  |  |  |

Each entry is one JSON file in `dataset/<c6|c7|c8>/` (e.g. `dataset/c6/C6-05_polyglot_c_py.json`).
Supporting files live in `dataset/<c6|c7|c8>/envs/<ID>/`. An entry describes one task:
- what the agent is asked to do
- the container it works in
- how the result is checked (hidden from the agent)
- where the task came from and why it was chosen

Fields common to all source types:

| Field | Meaning |
|---|---|
| `instance_id` | Current entry ID. Used with `--category c6\|c7 --entry <ID>` and in result directory names (`results/<c6\|c7>_runs/<ID>_<agent>_<model>_<ts>`). |
| `former_id` | The ID before the latest restructure (see above). |
| `id_history` | Every ID the entry has had, by restructure date (see above). |
| `category` / `category_name` | `C6` / 区分度任务（容器化，模型区分）, or `C7` / 日常工作任务（容器化，贴近日常）. The harness uses `category` to pick the rubric and the results directory. |
| `evaluation_rubric` | `evaluation/rubrics/c6_discriminative.json` or `c7_daily.json`: D1 = pass rate over trials (`--trials`, CLI default 5; our runs use 3), D2 = code quality (LLM judge; see `guide/coding_rubric.md`). Reported side by side, not combined. |
| `task_rubric` | Path to the case's code-quality rubric, `evaluation/rubrics/tasks/<ID>.json` (1–2 case-specific LLM-judge items; see `guide/coding_rubric.md`). |
| `discrimination.observed_xhs_runs` | Pass counts per agent/model from our own runs. Per-trial detail is in `results/README_c6_c7.md`. |

# Part 1: Terminal-Bench 2.0 and FrontierSWE v2 entries

The Terminal-Bench entries (C6-01, C6-03..06, C7-02, C8-03) are graded by their original pytest
suites. C6-05 (originally C6-01) was built first and originally used a custom verifier; it now uses
the original suite like the others. C8-02 (originally C6-08) is a FrontierSWE v2 task with a separate
verifier container and a continuous score. Fields that apply only to some entries are marked.

## Top-level fields

| Field | Meaning |
|---|---|
| `task_type` | `terminal_task`: the agent works in a shell inside a container, not in the xhs-campaign-service worktree used by C3/C5. |
| `maps_to_journey` | Provenance label, e.g. `External: Terminal-Bench 2.0 / polyglot-c-py`. |
| `rednote_relevance` | Why the task fits Rednote's business or routine work (all except C6-05). |
| `problem_statement` | The task prompt sent to the agent, copied verbatim from the source benchmark. For host CLI agents (agy/claude), the harness adds an "Environment notes" footer explaining the container and the `task-exec` helper. |

## `environment`: the container the agent works in

| Field | Meaning |
|---|---|
| `type` | `docker`: the task runs in its own image. |
| `dockerfile` | The original Dockerfile and build context (`envs/<ID>/...`), kept for provenance and rebuilds. |
| `prebuilt_image` | The image actually run: the source benchmark's published image, so the environment matches the source exactly. C8-02 pins it by digest. |
| `workdir` | Task directory (`/app`). For agy/claude it is backed by a host directory, so the agent can edit files directly. |
| `cpus` / `memory` | Resource limits from the source task. Enforced under `--sandbox docker`, not under udocker. |
| `network` | Whether the task needs network access. |
| `agent_timeout_sec` | The agent's time budget (900 s = Terminal-Bench's default). The harness uses `min(--timeout minutes, agent_timeout_sec)`. |
| `initial_state` | What the agent starts with, e.g. an empty `/app`. |
| `udocker_image` | *(C8-02)* Local alias for the digest-pinned image. udocker cannot pull `repo@sha256:...`, so the image is loaded with `tools/fetch_oci_digest.py`. |
| `udocker_execmode` | *(C8-02)* udocker engine for this entry (`P1` = proot). The default R1 engine maps only uid 0, which breaks the task's `runuser`. |
| `per_trial_paths` | *(C8-02)* Extra fresh, empty directories mounted per trial. For example, `/root` hides root-only verifier assets, because the agent runs as fake root under udocker. |
| `container_env` | *(C8-02)* Environment variables set in the container, e.g. `TASK_BUDGET_SECS` for the agent-visible `sandbox-timer`. |
| `init_cmd` | *(C8-02)* Command run once at the start of each trial, e.g. `sandbox-timer start`. |

## `verification`: how pass/fail is decided

The tests are never shown to the agent. They run in the container only after the agent stops.

| Field | Meaning |
|---|---|
| `type` | Grader kind:<br>• `tb2_pytest`: the original Terminal-Bench pytest suite (C6-01, C6-03..06, C7-02, C8-03)<br>• `harbor_separate`: FrontierSWE's verifier in its own container (C8-02)<br>• `script`: custom verifier (still supported by the harness; no current entry uses it) |
| `script`, `container_path`, `command` | *(script)* The verifier is copied to `container_path` (e.g. `/tmp/verify.py`) and run with `command` (e.g. `--root /app`). Its last stdout line is a JSON verdict: `{"reward": 0 or 1, "reason": ..., "checks": [...]}`. |
| `checks_in_order` | *(C6-05)* What the tests check, in order:<br>• only `main.py.c` is left in `/app/polyglot`<br>• gcc compiles it<br>• both the Python and C programs print the right Fibonacci numbers for n = 42, 10, 0 |
| `tests_dir`, `command` | *(tb2_pytest)* The original tests are copied to `/tests` and `bash /tests/grader.sh` is run. |
| `grader_derivation` | *(tb2_pytest)* `grader.sh` is the original `tests/test.sh` with exactly four setup lines removed: `apt-get update`, `apt-get install -y curl`, the uv installer and `source $HOME/.local/bin/env`. The harness provides uv/uvx at `/opt/xhs`. |
| `reward` | Plain-language scoring rule. For tb2_pytest, the trial passes iff the original script writes `1` to `/logs/verifier/reward.txt`. Per-test results come from the CTRF report. |
| `hidden_from_agent` | `true`: the tests are copied into the container only at grading time. |
| `tests` | *(tb2_pytest)* Names of the hidden tests, for reference. |
| `timeout_sec` | Time limit for the grader. |
| `verifier_image`, `udocker_verifier_image` | *(C8-02)* The separate verifier image (digest-pinned) and its local udocker alias. |
| `artifact_excludes` | *(C8-02)* Files left out when copying `/app` into the verifier container (build caches, built `.so` files). Taken from the task's `[[artifacts]]`. |
| `pass_threshold` | *(C8-02)* The score is continuous (0–1); a trial counts as passed at ≥ this value (0.1). D1 is the pass rate; the mean raw score over trials is also recorded (`scores.mean_score`). Binary graders default to 1.0. |

## `gold_solution`: the reference solution

| Field | Meaning |
|---|---|
| `script` | The source benchmark's own `solve.sh`. |
| `run_in` | Directory it runs in (`/app`). |
| `dir`, `timeout_sec` | *(C8-02)* The solution ships as a directory (script plus sources). It is copied to `/solution` and run with `HARBOR_ORACLE_FLAG` set, as in Harbor's oracle stage. |
| `expected_reward`, `note` | *(C8-02)* FrontierSWE ships a placeholder oracle that scores 0.0 by design. Validation checks the verifier's evidence fields (build, provenance, correctness, measurement) instead of the score. |

The gold solution is used only to validate the task: `--agent gold` should pass and
`--agent empty` should fail.

## `evaluation_rubric`

Path to the category rubric: `evaluation/rubrics/c6_discriminative.json` (C6) or `c7_daily.json` (C7).
D1 = pass rate over trials (snapped to the rubric's tiers); D2 = code quality from the LLM judge
(`guide/coding_rubric.md`).

## `source`: where the task came from

| Field | Meaning |
|---|---|
| `benchmark`, `repo`, `commit`, `path` | Exact origin, e.g. the Terminal-Bench 2.0 repo at commit `69671fb`, task directory `polyglot-c-py`. |
| `author`, `difficulty`, `category`, `expert_time_estimate_min` | Metadata from the source task's `task.toml`. |
| `task_page` | *(C8-02)* Public task page. |
| `original_scoring` | How the source benchmark scores the task. |
| `conversion_changes` | Every change made when converting the task to this format. Examples: "copied verbatim"; "grader drops only the curl/uv install lines"; *(C8-02)* "2 h agent budget instead of 20 h". |

## `discrimination`: why the task was chosen

Except for `observed_xhs_runs`, these values are computed from public per-model leaderboard results. See
`deliverables/REPORT.md` in the analysis workspace.

| Field | Meaning |
|---|---|
| `what_it_measures` | The skill the task actually tests. C6-05, for example, mostly tests workspace hygiene: 79% of leaderboard failures were leftover files such as `cmain`, not wrong code. |
| `n_models` | Number of leaderboard systems with results on this task. |
| `mean_pass_rate` / `mean_score` | Average result across those systems (difficulty). |
| `std` | Spread of results across systems. |
| `disc_r` | Item-rest correlation: Pearson r between a system's result on this task and its mean on all other tasks. High means the task consistently separates strong systems from weak ones. |
| `frontier_std`, `frontier_disc_r`, `frontier_mean` | The same metrics computed on the top half of systems only, i.e. whether the task separates strong systems *from each other*. |
| `tier` | `frontier (separates top models)` or `broad (strong vs weak)`, per the selection thresholds:<br>• broad: std ≥ 0.30, disc_r ≥ 0.50, 0.15 ≤ mean ≤ 0.85<br>• frontier: frontier_std ≥ 0.25, frontier_disc_r ≥ 0.30, 0.1 ≤ frontier_mean ≤ 0.9 |
| `leaderboard_failure_modes` | *(C6-05)* Leaderboard trials grouped by failure cause. |
| `caveat` | *(C8-02)* Why the reference scores are not directly comparable (20 h budget vs 2 h here). |

## `reference_scores`

The published per-system results for this task, used to compare your own runs against the
leaderboard. Each row has:
- `submission`, `agent`, `model`
- `pass_rate` (binary tasks) or `score` (continuous tasks)
- `n_runs`
- for FrontierSWE also `mean_hours` and `mean_cost_usd`

# Part 2: SWE-bench Verified entries

These entries (C7-03..08, C8-01; originally C7-01..07) each wrap one SWE-bench Verified issue (e.g.
`dataset/c8/C8-01_django__django-15957.json`): the agent fixes a real bug in a real repository,
and hidden tests decide whether it is resolved. They were selected for closeness to Rednote backend
daily work (Django ORM, MySQL, JSONField, i18n, HTTP proxies). C8-01 is in C8 because only Claude solved it
in the 2026-10-14 campaign.

Supporting files live in `dataset/<c6|c7|c8>/envs/<ID>/`:

| File | Meaning |
|---|---|
| `eval.sh` | The official SWE-bench eval script, generated by `make_test_spec` in swebench 4.1.0. It:<br>1. resets the files touched by the hidden test patch to `base_commit`<br>2. applies the test patch<br>3. runs the instance's test command between the `>>>>> Start/End Test Output` markers<br>4. resets the test files again |
| `instance.json` | The full SWE-bench Verified row. The grader feeds it to swebench's official grading code. It contains the gold patch and the test patch, so it is never shown to the agent. |
| `gold.patch` | The upstream fix from SWE-bench, kept for reference. |
| `gold.sh` | Applies `gold.patch` in `/testbed`. Used only for validation (`--agent gold`). |

The build script is `archive/dataset_build/build_xhs_c7_entries.py` (it writes the pre-restructure IDs; run `archive/migrations/restructure_c6_c7.py` afterwards). It must run with
the grader venv (`~/.cache/xhs_c6/swebench-venv`, swebench==4.1.0).

## Top-level fields

| Field | Meaning |
|---|---|
| `task_type` | `repo_bugfix`: edit an existing repository to fix an issue. |
| `maps_to_journey` | Provenance label, e.g. `External: SWE-bench Verified / django__django-15957`. |
| `rednote_relevance` | The Rednote scenario the issue represents, e.g. feed/comment pagination with top-N prefetch. |
| `daily_work_scenario` | The concrete routine task behind it, e.g. "latest 3 comments for each note in a feed page". |
| `problem_statement` | The prompt sent to the agent: the GitHub issue text verbatim, inside `<issue>` tags. It is wrapped in a short instruction giving the repo, the checkout path (`/testbed`) and the base commit, and saying not to modify existing tests because hidden tests run afterwards. As in Part 1, agy/claude also get the "Environment notes" footer. |

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
| `script` | `envs/<ID>/gold.sh`, which applies the upstream fix (`git apply`). |
| `run_in` | `/testbed`. |

The gold patch should resolve the issue and an untouched repo (`--agent empty`) should not.

## `evaluation_rubric`

As for all entries: `c6_discriminative.json` or `c7_daily.json` (D1 = resolve rate over trials;
D2 = code quality from the LLM judge).

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
| `disc_r` | Item-rest correlation, as in Part 1. Informational only. |

## `reference_scores`

Results for this instance from recent SWE-bench submissions whose names mention Gemini, Claude or
GPT (up to 30 rows). Each row has:
- `submission`: the leaderboard system, e.g. `20251120_livesweagent_gemini-3-pro-preview`
- `resolved`: 0 or 1, from a single run

# Part 3: DeepSWE v1.1 entries

These entries (C6-02, C6-07, C7-01, C7-09..11; originally C8-01..06) are DeepSWE v1.1 (Datacurve) feature
requests: the agent implements a feature in a real repository (TypeScript, Go, Python ...), and a
hidden test patch decides the result. Supporting files in `dataset/<c6|c7|c8>/envs/<ID>/`:

| Path | Meaning |
|---|---|
| `environment/Dockerfile` | The task image's Dockerfile (provenance; the published image is used). |
| `tests/` | The DeepSWE verifier: `test.patch`, `test.sh`, `grader.py`, `config.json` (FAIL_TO_PASS / PASS_TO_PASS lists), plus the source's `Dockerfile` (provenance; the harness does not build it, it copies `tests/` into a fresh sandbox of the task image). Never shown to the agent. |
| `solution/` | `solution.patch` + `solve.sh` (gold, validation only). |

Fields that differ from Parts 1–2:

| Field | Meaning |
|---|---|
| `task_type` | `repo_feature`. |
| `title`, `problem_statement` | The DeepSWE task title and instruction, verbatim. |
| `environment.prebuilt_image` | The published DeepSWE task image (`public.ecr.aws/...:<ext_id>-v1.1`); the repo is at `/app` at `base_commit` with future history removed. |
| `environment.agent_timeout_sec` | 10800 s (3 h). |
| `environment.udocker_rmi_after_create` | Remove the pulled image after the container is created (disk). |
| `verification.type` | `deepswe`. The harness mirrors Harbor's separate-environment flow: it collects `git diff --binary <base_commit> HEAD` (only **committed** work counts), applies it in a fresh sandbox of the task image, then runs `bash /tests/test.sh`, which applies `test.patch` and runs `grader.py`. `verdict.json` records `reward_json` (F2P/P2P counts), per-test `checks` (`FAIL_TO_PASS::<id>` / `PASS_TO_PASS::<id>`, runs since 2026-10-14) and `model_patch` (up to 400 KB). |
| `verification.collect_command`, `command`, `timeout_sec` | The diff collection command, the grader command and its time limit. |
| `verification.reward` | 1 iff every FAIL_TO_PASS test passes and no PASS_TO_PASS test fails (`/logs/verifier/reward.json`). |
| `verification.fail_to_pass_count`, `pass_to_pass_count`, `report_format` | Test counts and the report converter (e.g. `vitest-junit-to-ctrf`). |
| `source` | Benchmark repo/commit/path, `task_id`, `ext_id`, upstream repo and `base_commit`, language, category, `original_scoring`, `conversion_changes`. |
| `discrimination` | `selected_for`, the externally reported observation that motivated the pick, and `observed_xhs_runs`. |

The build script is `archive/dataset_build/build_xhs_c8_deepswe_entries.py` (it writes the original C8
IDs; run `archive/migrations/restructure_c6_c7.py`, then `archive/migrations/restructure_v2.py` afterwards).

# Part 4: Customer-provided entries (C9)

C9-01 (`dataset/c9/C9-01_toy_store_workbench.json`) is a customer requirement: a toy-shop clerk
workbench delivered as one self-contained HTML file (products and cart, coupons and member discount,
checkout, order status flow, partial refunds and returns, stock linkage, query and stats, persistence and
backup). The customer brief is kept verbatim in `customer_brief`; `problem_statement` appends a
**交付与验收约定** section so the result can be graded automatically:

- the deliverable is `/app/index.html`, opened via `file://` in Chromium with the network blocked;
- the page exposes `window.shopTestAPI` (synchronous methods, money in yuan) that must call the same
  business logic as the UI;
- business rules the tests depend on are fixed: status names, pro-rata refund allocation, the definition
  of sales / refunds / net / units sold, and the `products` / `orders` keys in the export.

Supporting files in `dataset/c9/envs/C9-01/`:

| Path | Purpose |
|---|---|
| `prompt.md` | The full prompt (brief + contract + environment hint) |
| `Dockerfile` | Documentation only: `mcr.microsoft.com/playwright/python:v1.55.0-noble` (Chromium in `/ms-playwright`) |
| `tests/test_outputs.py`, `tests/grader.sh` | Hidden pytest + Playwright tests (33), run as `tb2_pytest` (reward 1 iff all pass; per-test CTRF results) |
| `solution/index.html`, `solution/solve.sh` | Reference implementation (passes all tests) and the gold script that copies it to `/app` |

D2 uses the 3 common items plus two case items in `evaluation/rubrics/tasks/C9-01.json` (clerk usability:
amount breakdown, status hints, dangerous-action confirmation; and business logic shared by UI and test
API with exact money arithmetic).

