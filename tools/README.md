# tools/

Helper scripts for the containerized categories (C6 / C7 / C8). They were developed in the
analysis workspace and copied here so the harness setup is reproducible from this repo.

| Script | Purpose |
|---|---|
| `patch_udocker_r1.py` | **Required for `--sandbox udocker`.** Patches udocker's R1 (rootless runc) engine: private spec dir per run (concurrent runs of one container) and stdio pass-through (multi-byte output crashed the pty relay). The harness uses R1 only when this patch is applied; otherwise it falls back to proot, where the Go toolchain segfaults intermittently. Re-run after reinstalling udocker. |
| `fetch_oci_digest.py` | Fetch a digest-pinned public image (`repo@sha256:...`, which udocker can't pull) into a docker-save tarball for `udocker load` (used for C6-08's FrontierSWE images). |
| `run_agy_queue.sh` | Run Antigravity on a queue of entries: both models per entry, K entries at a time, optional base removal afterwards (disk). Paths assume the analysis-workspace layout (`<root>/sources/xhs`); adjust `ROOT`/`XHS` if run from elsewhere. |
| `revalidate_r1.sh`, `prepare_c7_bases.sh` | Validation chains (gold must pass, empty must fail) and C7 base pre-creation with a disk guard. Same path assumption. |
| `build/` | Entry builders (provenance): C6-01, C6-02..07 (Terminal-Bench 2.0), C6-08 (FrontierSWE v2), C7 (SWE-bench Verified, needs swebench==4.1.0), C8 (DeepSWE v1.1). They read source checkouts from the analysis workspace (`sources/tb2`, `sources/deepswe`, `deliverables/cases/...`). |

Setup on a fresh machine (udocker backend):

```bash
uv tool install udocker
python3 tools/patch_udocker_r1.py
uv venv ~/.cache/xhs_c6/swebench-venv && VIRTUAL_ENV=~/.cache/xhs_c6/swebench-venv uv pip install swebench==4.1.0   # C7 grading
```
