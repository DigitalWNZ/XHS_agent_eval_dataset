# tools/

Helper scripts for the containerized categories (C6 discriminative / C7 daily work). They were developed in the
analysis workspace and copied here so the harness setup is reproducible from this repo.

| Script | Purpose |
|---|---|
| `patch_udocker_r1.py` | **Required for `--sandbox udocker`.** Patches udocker's R1 (rootless runc) engine: private spec dir per run (concurrent runs of one container) and stdio pass-through (multi-byte output crashed the pty relay). The harness uses R1 only when this patch is applied; otherwise it falls back to proot, where the Go toolchain segfaults intermittently. Re-run after reinstalling udocker. |
| `fetch_oci_digest.py` | Fetch a digest-pinned public image (`repo@sha256:...`, which udocker can't pull) into a docker-save tarball for `udocker load` (used for C6-07's FrontierSWE images; former C6-08). |
| `run_agy_queue.sh` | Run Antigravity on a queue of entries: both models per entry, K entries at a time, optional base removal afterwards (disk). Paths assume the analysis-workspace layout (`<root>/sources/xhs`); adjust `ROOT`/`XHS` if run from elsewhere. |
| `revalidate_r1.sh`, `prepare_c7_bases.sh` | Validation chains (gold must pass, empty must fail) and C7 base pre-creation with a disk guard. Same path assumption. |
| `run_all.sh` | Full C6 + C7 run on the current IDs (`AGENT=agy\|claude`, `MODELS=...`). |
| `run_queue.sh`, `run_all_agy.sh`, `run_all_claude.sh` | Agent-agnostic queue (`AGENT=agy|claude`, `MODELS=...`) and the historical orchestrators (pre-restructure IDs) used for the Gemini and Claude Code + Opus 5.5 runs (Claude via Vertex: `CLAUDE_CODE_USE_VERTEX=1 CLOUD_ML_REGION=global ANTHROPIC_VERTEX_PROJECT_ID=...`). |
| `restructure_c6_c7.py` | One-off migration (2026-10-14) from the source-based C6/C7/C8 layout to C6 = discriminative (7) / C7 = daily work (14). Renumbers entries (keeping `former_id`), moves `envs/`, rewrites paths, updates the manifest and writes `results/id_mapping.json`. |
| `summarize_agy.py`, `detailed_report.py`, `idmap.py` | Results matrix and the per-case report (`results/README_c6_c7.md`). `idmap.py` maps the former IDs of runs recorded before the restructure to the current IDs. |
| `build/` | Entry builders (provenance). They write the **pre-restructure** layout and IDs (C6 = Terminal-Bench 2.0 + FrontierSWE v2, C7 = SWE-bench Verified (needs swebench==4.1.0), C8 = DeepSWE v1.1); run `restructure_c6_c7.py` afterwards to get the current layout. They read source checkouts from the analysis workspace (`sources/tb2`, `sources/deepswe`, `deliverables/cases/...`). |

Setup on a fresh machine (udocker backend):

```bash
uv tool install udocker
python3 tools/patch_udocker_r1.py
uv venv ~/.cache/xhs_c6/swebench-venv && VIRTUAL_ENV=~/.cache/xhs_c6/swebench-venv uv pip install swebench==4.1.0   # C7 grading
```
