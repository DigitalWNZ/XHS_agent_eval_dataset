# archive/

Code that is **not needed to run the benchmark**, kept for provenance. Nothing in `tools/` or `evaluation/` imports it.

| Folder | Contents |
|---|---|
| `dataset_build/` | Entry builders that created the cases from the public sources (Terminal-Bench 2.0, FrontierSWE v2, SWE-bench Verified, DeepSWE v1.1). They write the **pre-restructure** IDs and read source checkouts from the analysis workspace (`sources/tb2`, `sources/deepswe`, `deliverables/cases/...`); run `migrations/restructure_c6_c7.py` and then `migrations/restructure_v2.py` afterwards to reach the current layout. |
| `migrations/` | One-off migrations: `restructure_c6_c7.py` (2026-10-14 regroup into C6/C7), `restructure_v2.py` (2026-10-15 regroup into C6/C7/C8; writes the epochs in `results/id_mapping.json`), `build_rubric_v3.py` (wrote rubric v3 from per-case drafts not in the repo). Already applied — do not re-run. |
| `historical_runs/` | Orchestrators of the October 2026 runs on the **old IDs**: `run_all_agy.sh`, `run_all_claude.sh`, and `run_agy_queue.sh` (superseded by `tools/run_queue.sh` with `AGENT=agy`). Paths assume the analysis-workspace layout. |
| `deprecated/` | `harness_deprecated.py` (standalone evaluator for pre-captured output) and `run_c3_deprecated.py` (legacy C3-only runner), both superseded by `evaluation/run_benchmark.py`. |
