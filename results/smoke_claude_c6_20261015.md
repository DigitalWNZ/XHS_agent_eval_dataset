# C6 campaign report (runs ≥ 20261015_0845, < 20261015_0946)

7 trials, 1 setups, rubric v3.0. **D1** = pass rate on the source benchmark's hidden tests (cell tier snapped to 100/67/33/0). **D2** = code quality from the LLM judge (Claude Opus 5.5): Readability, Maintainability, Robustness + 1–2 case items, perfect 1 / accept 0.6 / bad 0, quality = 100 × mean. D1 and D2 are not combined. Trials with no code change cannot be judged (na) and are excluded from D2.

## Per case (passes/trials · D2 quality)

| Case | Former ID | Task | claude-opus-5-5 |
|---|---|---|---|
| C6-01 | C6-01 | Terminal-Bench 2.0 / filter-js-from-html | 0/1 · — ∅1 |
| C6-02 | C6-03 | DeepSWE v1.1 / pebble-durability-wait-apis | 1/1 · 90 |
| C6-03 | C6-04 | Terminal-Bench 2.0 / video-processing | 1/1 · 56 |
| C6-04 | C6-06 | Terminal-Bench 2.0 / mteb-retrieve | 1/1 · 60 |
| C6-05 | C7-01 | Terminal-Bench 2.0 / polyglot-c-py | 0/1 · 48 |
| C6-06 | C7-03 | Terminal-Bench 2.0 / cancel-async-tasks | 1/1 · 76 |
| C6-07 | C7-12 | DeepSWE v1.1 / query-persist-restored-query-state | 1/1 · 68 |

∅n = n trials ended with no code change (all were agent timeouts); ⚠n = invalid (validity audit).

## Per model

| Model | Trials | Passes | Pass rate | D1 (mean case tier) | D2 quality (graded trials) | No-code trials | Timeouts | Invalid |
|---|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 7 | 5 | 71% | 71 | 66 (n=6) | 1 | 0 | 0 |

## Run metrics per model (mean per trial)

Agent time = wall time of the agent run (capped by the budget). Tool calls are counted from the trajectory. Tokens = input + output as reported by the agent CLI; agy reports no usage when it hits its time budget, so for those trials the per-step usage in the saved trajectory is summed (marked * in the per-trial table; only available for runs after the partial-trajectory fix). Turns: Claude Code reports turns; agy always reports 1 per session, so use tool calls to compare.

| Model | Agent time (min) | Tool calls | Tokens (K) | Turns (Claude) | Cost USD (Claude, total) |
|---|---|---|---|---|---|
| claude-opus-5-5 | 5 | 10 | 440 | 11 | 3.84 |

## Run metrics per case (mean per trial: agent time min · tool calls · tokens K)

Same definitions as above, averaged over the trials of one case and model (— = no data, e.g. agy timeouts before the partial-trajectory fix).

| Case | Task | claude-opus-5-5 |
|---|---|---|
| C6-01 | Terminal-Bench 2.0 / filter-js-from-html | 2.7 · 1 · 64 |
| C6-02 | DeepSWE v1.1 / pebble-durability-wait-apis | 11 · 22 · 1148 |
| C6-03 | Terminal-Bench 2.0 / video-processing | 2.5 · 13 · 265 |
| C6-04 | Terminal-Bench 2.0 / mteb-retrieve | 4.5 · 4 · 90 |
| C6-05 | Terminal-Bench 2.0 / polyglot-c-py | 0.5 · 2 · 53 |
| C6-06 | Terminal-Bench 2.0 / cancel-async-tasks | 1.4 · 4 · 92 |
| C6-07 | DeepSWE v1.1 / query-persist-restored-query-s | 13 · 25 · 1371 |

## D2 item scores per model (mean over judged items, 0–100)

| Model | Readability | Maintainability | Robustness | Case-specific | Quality |
|---|---|---|---|---|---|
| claude-opus-5-5 | 80 | 60 | 57 | 66 | 66 |

## Quality among passing vs failing trials

| Model | D2 on passing trials | D2 on failing trials (with code) |
|---|---|---|
| claude-opus-5-5 | 70 | 48 |

## Validity findings

- results/c6_runs/C6-07_claude_claude-opus-5-5_20261015_084558/trial_0: test_tampering (provisional) — existing test lines changed/removed (1): packages/query-core/src/__tests__/query.test.tsx; existing test lines changed/removed (2): packages/query-persist-client-core/src/__tests__/createPersister.tes

## Per trial

Item levels: P = perfect (100), A = accept (60), B = bad (0), – = not applicable. Read / Maint / Robust = the 3 common items; Case = the case-specific item(s) in order.

| Case | Model | Trial | Pass | Score | D2 | Read | Maint | Robust | Case | Time (min) | Tool calls | Tokens (K) | Notes | Verifier reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C6-01 | claude-opus-5-5 | 0 | ❌ | 0 | — | – | – | – | –,– | 3 | 1 | 64 | no code | test_outputs.py::test_filter_blocks_xss: The test failed in the call phase due to an asser |
| C6-02 | claude-opus-5-5 | 0 | ✅ | 1 | 90 | P | A | P | P | 11 | 22 | 1148 |  | resolved (F2P 59/59, P2P 44/44) |
| C6-03 | claude-opus-5-5 | 0 | ✅ | 1 | 56 | A | A | A | B,P | 2 | 13 | 265 |  | all 5 tests passed |
| C6-04 | claude-opus-5-5 | 0 | ✅ | 1 | 60 | A | A | A | A | 5 | 4 | 90 |  | all 2 tests passed |
| C6-05 | claude-opus-5-5 | 0 | ❌ | 0 | 48 | A | A | B | A,A | 0 | 2 | 53 |  | test_outputs.py::test_fibonacci_polyglot: The test failed in the call phase due to an asse |
| C6-06 | claude-opus-5-5 | 0 | ✅ | 1 | 76 | P | A | A | A,P | 1 | 4 | 92 |  | all 6 tests passed |
| C6-07 | claude-opus-5-5 | 0 | ✅ | 1 | 68 | P | A | A | A,A | 13 | 25 | 1371 |  | resolved (F2P 8/8, P2P 42/42) |
