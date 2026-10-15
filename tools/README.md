# tools/

Everything needed to **run** the containerized benchmark (C6 hill climb / C7 daily job / C8 hard / C9 customer-provided),
grade it and report it. Together with `evaluation/` this is the single home of the run code; the analysis workspace no
longer keeps copies. One-off migrations, historical orchestrators and dataset builders are in [`../archive/`](../archive/README.md).

## Run

| Script | Purpose |
|---|---|
| `run_all.sh` | Full C6 + C7 + C8 + C9 campaign on the current IDs, 3 trials per entry and model, LLM judge inline (`QUALITY=full`). `AGENT=agy\|claude`, `MODELS=...`; Claude via Vertex needs `CLAUDE_CODE_USE_VERTEX=1 CLOUD_ML_REGION=global ANTHROPIC_VERTEX_PROJECT_ID=...`. Runs from anywhere. |
| `run_queue.sh` | `run_queue.sh <K> <timeout_min> <rm\|keep> <cat:ENTRY>...` — run one agent on a queue of entries (all `MODELS` per entry, K entries in parallel, optional udocker base removal). Calls `evaluation/run_benchmark.py`. Env: `AGENT`, `MODELS`, `TRIALS` (3), `QUALITY` (`off\|machine\|full`), `RUNS_DIR` (default `<repo>/runs`, git-ignored), `LOG_DIR`. |

## Environment setup and validation

| Script | Purpose |
|---|---|
| `patch_udocker_r1.py` | **Required for `--sandbox udocker`.** Patches udocker's R1 (rootless runc) engine: private spec dir per run (concurrent runs of one container) and stdio pass-through. Without it the harness falls back to proot, where the Go toolchain segfaults intermittently. Re-run after reinstalling udocker. |
| `fetch_oci_digest.py` | Fetch a digest-pinned public image (`repo@sha256:...`, which udocker can't pull) into a docker-save tarball for `udocker load` (C8-02's FrontierSWE images). |
| `prepare_c7_bases.sh` | Pre-create the udocker base containers for the SWE-bench images, one at a time, with a disk guard. |
| `revalidate_r1.sh` | Validation chain: `revalidate_r1.sh "cat:ENTRY:gold,empty[:rm]" ...` — gold must pass, empty must fail. Logs to `$RUNS_DIR/validate_r1`. |

## Reports

| Script | Purpose |
|---|---|
| `campaign_report.py` | Per-campaign D1/D2 report under the current IDs: `--category c6\|c7\|c8\|c9 --since <YYYYMMDD_HHMM> [--until ...] --out results/<name>.md`. Includes item levels, time, tool calls, tokens, per-case run metrics. |
| `quality_report.py` | `results` → `results/README_quality.md`; `rubric` → `guide/coding_rubric_items.md`. Reads the `quality.json` files written by `evaluation/quality_grader.py`. |
| `summarize_agy.py`, `detailed_report.py` | Results matrix (used by `run_all.sh`) and the per-case report (`results/README_c6_c7.md`). |
| `idmap.py` | Shared helper: locates the repo and maps IDs recorded by older runs to the current IDs (`results/id_mapping.json`). |
| `sheets/` | Fill the Google Sheet "XHS Evalution DataSet": `fill_sheet.py` (`Coding_Detail`), `fill_summary_sheet.py` (`Coding_Summary_Internal`, with a group-average row per category); Chinese texts in `sheet_texts.py`. Needs a Sheets-scoped ADC in `~/.cache/sheets-gcloud` (`CLOUDSDK_CONFIG=~/.cache/sheets-gcloud gcloud auth application-default login --scopes=...spreadsheets,...cloud-platform`). |

## Setup on a fresh machine

This repo is self-contained: a clone of it alone runs the benchmark (verified 2026-10-15 from a standalone clone: gold
for C6-05 / C7-02 / C7-04 / C9-01 and a Claude Code + Opus run with the LLM judge). What the machine must provide:

| # | Prerequisite | How | Needed for |
|---|---|---|---|
| 1 | `git`, `bwrap` (bubblewrap), Python 3.10+ | OS packages (`apt install git bubblewrap python3`) | Everything (`bwrap` hides the repo from the agent; without it trials run unisolated) |
| 2 | `uv` / `uvx` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` (the harness also installs a copy under `~/.cache/xhs_c6/opt` if missing) | Graders (Terminal-Bench / C9 tests run via `uvx`) |
| 3 | `udocker` + R1 patch | `uv tool install udocker && python3 tools/patch_udocker_r1.py` (re-run the patch after reinstalling udocker) | All containerized cases (`--sandbox udocker`) |
| 4 | Agent CLIs | Antigravity CLI `agy` (Gemini models); Claude Code: `npm install -g @anthropic-ai/claude-code` | The agents under test |
| 5 | Agent / judge credentials | **agy:** an `authorized_user` ADC file at `~/.cache/xhs_c6/agy-adc/adc.json` (e.g. `gcloud auth application-default login`, then copy `~/.config/gcloud/application_default_credentials.json` there). **Claude Code + LLM judge (Claude Opus):** Vertex AI — `export CLAUDE_CODE_USE_VERTEX=1 CLOUD_ML_REGION=global ANTHROPIC_VERTEX_PROJECT_ID=<project>` with the default ADC allowed to call Claude on Vertex in that project | Agent runs, `QUALITY=full` |
| 6 | SWE-bench grader venv | `uv venv ~/.cache/xhs_c6/swebench-venv && VIRTUAL_ENV=~/.cache/xhs_c6/swebench-venv uv pip install swebench==4.1.0` | C7-03..C7-08, C8-01 |
| 7 | C8-02 images (digest-pinned; udocker can't pull them) | see below | C8-02 only |
| 8 | Disk / `/tmp` | ~60 GB free under `$HOME` (`~/.udocker` images + base containers; `tools/prepare_c7_bases.sh` pre-creates the SWE-bench bases with a disk guard); `/tmp` ≥ 16 GB (trial workspaces live there; DeepSWE repos are up to ~2.8 GB each) | Parallel runs |

All other images are pulled from public registries on first use. `XHS_C6_CACHE` overrides `~/.cache/xhs_c6`.

C8-02 images (once):

```bash
python3 tools/fetch_oci_digest.py us-west1-docker.pkg.dev/proximal-core-0/proximal-evals-public/ffmpeg-libswscale-optimization@sha256:29c425c53c9079c9adce1a9d63bf9d4f2b81a5316cf5e9e995280b14c8595f48 xhs/ffmpeg-swscale-env:fswe-da83f84 /tmp/env.tar
python3 tools/fetch_oci_digest.py us-west1-docker.pkg.dev/proximal-core-0/proximal-evals-public/ffmpeg-libswscale-optimization@sha256:494a93a2ae0a5e7b7e00741b23ad48550cbdb718966362eeaee753783c5f77c6 xhs/ffmpeg-swscale-verifier:fswe-da83f84 /tmp/verifier.tar
udocker load -i /tmp/env.tar xhs/ffmpeg-swscale-env && udocker load -i /tmp/verifier.tar xhs/ffmpeg-swscale-verifier && rm /tmp/env.tar /tmp/verifier.tar
```

Smoke test (no agent, ~1 min): the reference solution must pass and an empty workspace must fail.

```bash
AGENT=gold  MODELS=gemini-3.8-flash-high TRIALS=1 QUALITY=off bash tools/run_queue.sh 2 30 keep c9:C9-01 c6:C6-05   # expect 1
AGENT=empty MODELS=gemini-3.8-flash-high TRIALS=1 QUALITY=off bash tools/run_queue.sh 1 30 keep c9:C9-01           # expect 0
```

## Cloud runner (`tools/cloud/`, GCP Batch)

For many trials in parallel: `xhs_cloud.py` runs one Batch task per trial on worker VMs in a GCP project
(default `gcr-evaluation-hub`, region `us-central1`) and removes every resource afterwards. Workers use real
**Docker** (`--sandbox docker`: exact published images, C8-02's separate verifier supported) instead of udocker.
Like the udocker runs, the source benchmarks' cpus/memory limits are not enforced by default (`--env
XHS_DOCKER_LIMITS=1` enforces them; then C6-01's grader exceeds its 900 s timeout). Validated 2026-10-15 on
Docker: gold 21/22 pass (C8-02's FrontierSWE oracle scores 0 on udocker too), empty 0/22.

| File | Role |
|---|---|
| `cloud/xhs_cloud.py` | Controller: `bake`, `run`, `status`, `collect`, `down`, `gc` |
| `cloud/bake.sh` | Startup script of the temporary bake VM → image family `xhs-worker` (Docker, bwrap, uv, Claude Code, agy, SWE-bench venv, all task images pre-pulled) |
| `cloud/worker.py` | Runs one trial on a worker: code from GCS → `run_benchmark.py --sandbox docker --trials 1` → results + status to GCS |

```bash
export CLOUDSDK_CONFIG=~/.cache/sheets-gcloud      # a gcloud config whose ADC can manage the project
python3 tools/cloud/xhs_cloud.py bake               # once, ~40 min; re-bake when tools or task images change
python3 tools/cloud/xhs_cloud.py run --cases all --agent agy --models gemini-3.8-flash-high,gemini-4-argon-high --trials 3
python3 tools/cloud/xhs_cloud.py run --cases c9:C9-01 --agent claude --models claude-opus-5-5 --trials 3 --detach
python3 tools/cloud/xhs_cloud.py status <run-id> --watch     # from any shell
python3 tools/cloud/xhs_cloud.py down <run-id>               # collect + delete jobs/VMs/GCS prefix
python3 tools/cloud/xhs_cloud.py gc                          # clean up anything orphaned (label purpose=xhs-runner)
```

- **One-time project setup:** service account `xhs-runner` with `roles/aiplatform.user`, `logging.logWriter`,
  `batch.agentReporter`, `artifactregistry.reader`, `monitoring.metricWriter`, and `storage.objectAdmin` on the
  bucket `gs://gcr-evaluation-hub-xhs-runs`. Workers authenticate agy (`AGY_ADC_AUTH=true`) and Claude Code
  (Vertex) with this service account; no user credential is copied to the cloud.
- **Scheduling:** one Batch job per model and provisioning class; `--parallelism` = max concurrent trials per
  model, `--per-vm` trials per VM (default 2 on `n2-standard-16`). VMs are **on-demand by default** (no
  preemption); `--spot auto|all` opts into Spot. Infrastructure failures (worker exit 75) are retried up to
  twice; agent failures are results. If a machine type is out of capacity in the region (stockout), the job
  waits in SCHEDULED and `status` shows the Batch event; pick another `--machine-type` (e.g. `e2-standard-16`,
  `n2d-standard-16`).
- **Results:** each task gets a unique run timestamp (`XHS_RUN_TS`), so run folders from all workers merge into
  `results/c*_runs/` exactly like local runs; `run`/`collect` then write `results/cloud_<run-id>_<cat>.md` with
  `campaign_report.py`. Logs and per-task status go to `$RUNS_DIR/cloud/<run-id>/`.
- **Teardown:** `run` deletes its Batch jobs (Batch deletes the VMs), any leftover VM labelled `xhs-run=<id>`
  and the run's GCS prefix when it finishes, on error and on Ctrl-C (after collecting what finished).
  `--detach` leaves the run going; finish it with `status --watch` + `down`.
- **Isolation on workers:** agents run in bwrap with `/work` (all trials' repo copies) and the repo hidden, and
  `/tmp` private. The worker service account can read the run bucket, so the validity audit flags any agent
  access to it (`quality_grader.LEAK_URL`).

## Typical use

```bash
# full campaign, Gemini via Antigravity CLI (detached)
AGENT=agy MODELS="gemini-3.8-flash-high gemini-4-argon-high" setsid nohup bash tools/run_all.sh > /tmp/run_all.log 2>&1 < /dev/null &
# one case, Claude Code + Opus, 3 trials
AGENT=claude MODELS=claude-opus-5-5 QUALITY=full bash tools/run_queue.sh 1 60 keep c9:C9-01
# report
python3 tools/campaign_report.py --category c9 --since 20261015_0946 --out results/campaign_c9_20261015.md
```
