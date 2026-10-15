# C6 / C7 evaluation

C6 (7 discriminative cases) and C7 (14 daily-work cases) report two results per trial.

## 1. Pass / fail (unchanged)

The source benchmark's own hidden tests run in the task container after the agent finishes. The
agent never sees them.

| Source | Cases | Hidden tests (copied verbatim, `dataset/<c6|c7>/envs/<ID>/`) |
|---|---|---|
| Terminal-Bench 2.0 | C6-01, C6-04, C6-06, C7-01..04 | `original_tests/` from laude-institute/terminal-bench-2 @ 69671fb |
| SWE-bench Verified | C6-05, C7-05..10 | `eval.sh` + FAIL_TO_PASS / PASS_TO_PASS, graded by swebench 4.1.0 |
| DeepSWE v1.1 | C6-02, C6-03, C7-11..14 | `tests/` from datacurve-ai/deep-swe @ 0b9fabb |
| FrontierSWE v2 | C6-07 | the published verifier image; continuous score, pass at ≥ 0.1 |

A trial passes if the verifier passes. Per case and model the result is the **pass rate** over
the trials (D1 in `evaluation/rubrics/c6_discriminative.json` / `c7_daily.json`).

## 2. Code quality (LLM judge)

One judge call per trial (Claude Opus 5.5) grades:

- **3 common items** for every case, defined in `evaluation/rubrics/coding_quality.json`. Their
  meanings come from C3 D3–D5, with C3's hard caps adapted:
  - **Readability 可读性**: naming, formatting consistent with the codebase, comments on
    non-obvious logic.
  - **Maintainability 可维护性**: separation of concerns, short functions, reuse of helpers, no
    copy-paste or dead code.
  - **Robustness 健壮性**: specific error handling, safe resources, input validation, no silently
    swallowed errors.
- **1–2 case-specific items** per case, defined in `evaluation/rubrics/tasks/<ID>.json`. These are
  task-specific questions the tests don't fully answer, e.g. C6-01 "obfuscated XSS vectors
  neutralised" or C7-08 "deprecated OPTIONS keys still supported".

Each item has a question and concrete **perfect / accept / bad** criteria. Scores: perfect = 1.0,
accept = 0.6, bad = 0. **Quality = 100 × mean item score.** The judge sees the task, the reference
solution (for comparison only), the agent's code change, a condensed action log, its final message
and the hidden-test outcome.

The case items for all 21 cases are listed in `guide/coding_rubric_items.md` (generated).

## Validity audit (not scored)

The grader also flags trials whose action log shows that the agent read, copied or ran the hidden
tests or the reference solution, downloaded the upstream fix, or tampered with tests. A confirmed
finding marks the trial **invalid** (`valid: false` in `quality.json`): its pass/fail is not
trustworthy, and it should be re-run. Ambiguous findings (only listing benchmark folders, changed
lines in existing tests, writes to `/tests`) are listed as provisional and don't invalidate the
trial.

Before 2026-10-14, host-side agents could browse the benchmark repo. 18 trials, almost all
gemini-3.8-flash, read hidden tests or solutions or fetched the upstream fix. Agents now run in
`bwrap` with the repo hidden.

## Commands

```bash
cd sources/xhs
# run (pass/fail). --quality: machine (default) = validity audit only, full = + LLM judge inline, off
python3 evaluation/run_benchmark.py --category c6 --all --agent agy --model gemini-3.8-flash-high --sandbox udocker --trials 3 --timeout 180
# (--timeout caps each case's own budget; the default 30 min would cut DeepSWE / FrontierSWE cases short)
# grade code quality (judge answers cached per trial in judge_v3_*.json)
python3 evaluation/quality_grader.py --all --jobs 4
# reports
python3 tools/detailed_report.py > results/README_c6_c7.md   # per-trial pass/fail
python3 tools/quality_report.py results                        # results/README_quality.md
python3 tools/quality_report.py rubric                         # guide/coding_rubric_items.md
```

`results/README_quality.md` lists a fixed 5% sample of judge answers for human spot-checks.
Human corrections go in `results/quality_overrides.json`:
`{"<run>/<trial>": {"<item id>": {"level": "...", "reviewer": "...", "note": "..."}}}`.

## Files

| File | Contents |
|---|---|
| `evaluation/rubrics/coding_quality.json` | Levels, the 3 common items, judge settings, aggregation |
| `evaluation/rubrics/tasks/<ID>.json` | The case's 1–2 items + project context for the judge |
| `evaluation/quality_grader.py` | Judge call, quality score, validity audit → `<trial>/quality.json` |
| `tools/build_rubric_v3.py` | How the case items were derived (from the earlier per-case drafts) |
