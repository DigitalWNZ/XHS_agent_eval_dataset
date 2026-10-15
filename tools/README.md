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

## Setup on a fresh machine (udocker backend)

```bash
uv tool install udocker
python3 tools/patch_udocker_r1.py
uv venv ~/.cache/xhs_c6/swebench-venv && VIRTUAL_ENV=~/.cache/xhs_c6/swebench-venv uv pip install swebench==4.1.0   # C7 grading
```

## Typical use

```bash
# full campaign, Gemini via Antigravity CLI (detached)
AGENT=agy MODELS="gemini-3.8-flash-high gemini-4-argon-high" setsid nohup bash tools/run_all.sh > /tmp/run_all.log 2>&1 < /dev/null &
# one case, Claude Code + Opus, 3 trials
AGENT=claude MODELS=claude-opus-5-5 QUALITY=full bash tools/run_queue.sh 1 60 keep c9:C9-01
# report
python3 tools/campaign_report.py --category c9 --since 20261015_0946 --out results/campaign_c9_20261015.md
```
