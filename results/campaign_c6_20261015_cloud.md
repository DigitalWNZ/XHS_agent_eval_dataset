# C6 campaign report (runs ≥ 20261015_183739, < 20261015_184100)

84 trials, 4 setups, rubric v3.0. **D1** = pass rate on the source benchmark's hidden tests (cell tier snapped to 100/67/33/0). **D2** = code quality from the LLM judge (Claude Opus 5.5): Readability, Maintainability, Robustness + 1–2 case items, perfect 1 / accept 0.6 / bad 0, quality = 100 × mean. D1 and D2 are not combined. Trials with no code change cannot be judged (na) and are excluded from D2.

## Per case (passes/trials · D2 quality)

| Case | Former ID | Task | claude-opus-5-5 | gemini-3.6-flash-high | gemini-3.8-flash-high | gemini-4-argon-high |
|---|---|---|---|---|---|---|
| C6-01 | C6-01 | Terminal-Bench 2.0 / filter-js-from-html | 0/3 · 51 | 0/3 · 35 | 0/3 · 47 | 0/3 · 56 ∅1 |
| C6-02 | C6-03 | DeepSWE v1.1 / pebble-durability-wait-apis | 3/3 · 73 | 0/3 · 30 | 3/3 · 55 | 3/3 · 25 |
| C6-03 | C6-04 | Terminal-Bench 2.0 / video-processing | 0/3 · 45 | 1/3 · 47 | 0/3 · 35 | 1/3 · 35 |
| C6-04 | C6-06 | Terminal-Bench 2.0 / mteb-retrieve | 3/3 · 60 | 2/3 · 43 | 3/3 · 60 | 0/3 · 0 ∅2 |
| C6-05 | C7-01 | Terminal-Bench 2.0 / polyglot-c-py | 3/3 · 60 | 1/3 · 51 | 3/3 · 69 | 3/3 · 64 |
| C6-06 | C7-03 | Terminal-Bench 2.0 / cancel-async-tasks | 3/3 · 81 | 2/3 · 56 | 1/3 · 64 ∅2 | 0/3 · — ∅3 |
| C6-07 | C7-12 | DeepSWE v1.1 / query-persist-restored-query-state | 2/3 · 71 | 3/3 · 60 | 3/3 · 59 | 3/3 · 60 |

∅n = n trials ended with no code change (all were agent timeouts); ⚠n = invalid (validity audit).

## Per model

| Model | Trials | Passes | Pass rate | D1 (mean case tier) | D2 quality (graded trials) | No-code trials | Timeouts | Invalid |
|---|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 21 | 14 | 67% | 67 | 63 (n=21) | 0 | 0 | 0 |
| gemini-3.6-flash-high | 21 | 9 | 43% | 43 | 46 (n=21) | 0 | 2 | 0 |
| gemini-3.8-flash-high | 21 | 13 | 62% | 62 | 55 (n=19) | 2 | 2 | 0 |
| gemini-4-argon-high | 21 | 10 | 48% | 48 | 44 (n=15) | 6 | 7 | 0 |

## Run metrics per model (mean per trial)

Agent time = wall time of the agent run (capped by the budget). Tool calls are counted from the trajectory. Tokens = input + output as reported by the agent CLI; agy reports no usage when it hits its time budget, so for those trials the per-step usage in the saved trajectory is summed (marked * in the per-trial table; only available for runs after the partial-trajectory fix). Turns: Claude Code reports turns; agy always reports 1 per session, so use tool calls to compare.

| Model | Agent time (min) | Tool calls | Tokens (K) | Turns (Claude) | Cost USD (Claude, total) |
|---|---|---|---|---|---|
| claude-opus-5-5 | 4 | 11 | 456 | 12 | 10.77 |
| gemini-3.6-flash-high | 11 | 70 | 579 | — | — |
| gemini-3.8-flash-high | 24 | 125 | 978 | — | — |
| gemini-4-argon-high | 36 | 101 | 671 | — | — |

## Run metrics per case (mean per trial: agent time min · tool calls · tokens K)

Same definitions as above, averaged over the trials of one case and model (— = no data, e.g. agy timeouts before the partial-trajectory fix).

| Case | Task | claude-opus-5-5 | gemini-3.6-flash-high | gemini-3.8-flash-high | gemini-4-argon-high |
|---|---|---|---|---|---|
| C6-01 | Terminal-Bench 2.0 / filter-js-from-html | 3.4 · 5 · 170 | 14 · 20 · 194 | 15 · 75 · 573 | 30 · 61 · 417 |
| C6-02 | DeepSWE v1.1 / pebble-durability-wait-apis | 11 · 26 · 1248 | 16 · 142 · 1272 | 47 · 266 · 2652 | 52 · 189 · 1443 |
| C6-03 | Terminal-Bench 2.0 / video-processing | 2.1 · 13 · 320 | 13 · 78 · 677 | 36 · 121 · 856 | 12 · 41 · 206 |
| C6-04 | Terminal-Bench 2.0 / mteb-retrieve | 1.1 · 4 · 82 | 9.2 · 52 · 345 | 13 · 63 · 357 | 25 · 69 · 368 |
| C6-05 | Terminal-Bench 2.0 / polyglot-c-py | 0.6 · 3 · 81 | 4.0 · 42 · 272 | 6.8 · 43 · 235 | 2.4 · 11 · 53 |
| C6-06 | Terminal-Bench 2.0 / cancel-async-tasks | 1.3 · 4 · 100 | 7.7 · 32 · 207 | 14 · 73 · 396 | 15 · 37 · 186 |
| C6-07 | DeepSWE v1.1 / query-persist-restored-query-s | 5.3 · 24 · 1189 | 15 · 124 · 1086 | 39 · 236 · 1775 | 114 · 301 · 2022 |

## D2 item scores per model (mean over judged items, 0–100)

| Model | Readability | Maintainability | Robustness | Case-specific | Quality |
|---|---|---|---|---|---|
| claude-opus-5-5 | 72 | 55 | 52 | 68 | 63 |
| gemini-3.6-flash-high | 61 | 35 | 34 | 54 | 46 |
| gemini-3.8-flash-high | 62 | 33 | 49 | 63 | 55 |
| gemini-4-argon-high | 60 | 26 | 43 | 55 | 44 |

## Quality among passing vs failing trials

| Model | D2 on passing trials | D2 on failing trials (with code) |
|---|---|---|
| claude-opus-5-5 | 69 | 51 |
| gemini-3.6-flash-high | 63 | 33 |
| gemini-3.8-flash-high | 61 | 41 |
| gemini-4-argon-high | 50 | 32 |

## Validity findings

- results/c6_runs/C6-07_agy_gemini-3.6-flash-high_20261015_183805/trial_0: test_tampering (provisional) — existing test lines changed/removed (1): packages/query-persist-client-core/src/__tests__/createPersister.test.ts
- results/c6_runs/C6-07_agy_gemini-3.8-flash-high_20261015_183757/trial_0: test_tampering (provisional) — existing test lines changed/removed (1): packages/react-query/src/__tests__/fine-grained-persister.test.tsx
- results/c6_runs/C6-07_agy_gemini-3.8-flash-high_20261015_183758/trial_0: test_tampering (provisional) — existing test lines changed/removed (2): packages/react-query/src/__tests__/fine-grained-persister.test.tsx
- results/c6_runs/C6-07_agy_gemini-4-argon-high_20261015_183800/trial_0: test_tampering (provisional) — existing test lines changed/removed (1): packages/preact-query/src/__tests__/fine-grained-persister.test.tsx; existing test lines changed/removed (1): packages/query-core/src/__tests__/query.test.tsx;
- results/c6_runs/C6-07_agy_gemini-4-argon-high_20261015_183801/trial_0: test_tampering (provisional) — existing test lines changed/removed (1): packages/preact-query/src/__tests__/fine-grained-persister.test.tsx; existing test lines changed/removed (1): packages/query-core/src/__tests__/query.test.tsx;
- results/c6_runs/C6-07_agy_gemini-4-argon-high_20261015_183802/trial_0: test_tampering (provisional) — existing test lines changed/removed (1): packages/preact-query/src/__tests__/fine-grained-persister.test.tsx; existing test lines changed/removed (1): packages/query-core/src/__tests__/query.test.tsx;

## Per trial

Item levels: P = perfect (100), A = accept (60), B = bad (0), – = not applicable. Read / Maint / Robust = the 3 common items; Case = the case-specific item(s) in order.

| Case | Model | Trial | Pass | Score | D2 | Read | Maint | Robust | Case | Time (min) | Tool calls | Tokens (K) | Notes | Verifier reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C6-01 | claude-opus-5-5 | 0 | ❌ | 0 | 48 | A | B | A | A,A | 3 | 3 | 116 |  | test_outputs.py::test_filter_blocks_xss: The test failed in the call phase due to an asser |
| C6-01 | claude-opus-5-5 | 0 | ❌ | 0 | 56 | A | B | A | P,A | 2 | 5 | 153 |  | test_outputs.py::test_clean_html_unchanged: The test failed in the call phase due to an as |
| C6-01 | claude-opus-5-5 | 0 | ❌ | 0 | 48 | A | B | A | A,A | 5 | 6 | 242 |  | test_outputs.py::test_filter_blocks_xss: The test failed in the call phase due to an asser |
| C6-01 | gemini-3.6-flash-high | 0 | ❌ | 0 | 36 | A | B | A | B,A | 4 | 26 | 213 |  | test_outputs.py::test_filter_blocks_xss: The test failed in the call phase due to an asser |
| C6-01 | gemini-3.6-flash-high | 0 | ❌ | 0 | 44 | A | B | B | A,P | 30 | 8 | 97* | timeout | grader rc=None: verifier timeout 900s |
| C6-01 | gemini-3.6-flash-high | 0 | ❌ | 0 | 24 | A | B | B | B,A | 9 | 25 | 271 |  | test_outputs.py::test_filter_blocks_xss: The test failed in the call phase due to an asser |
| C6-01 | gemini-3.8-flash-high | 0 | ❌ | 0 | 48 | A | B | A | A,A | 14 | 91 | 533 |  | test_outputs.py::test_filter_blocks_xss: The test failed in the call phase due to an asser |
| C6-01 | gemini-3.8-flash-high | 0 | ❌ | 0 | 44 | A | B | A | B,P | 13 | 69 | 412 |  | test_outputs.py::test_filter_blocks_xss: The test failed in the call phase due to an asser |
| C6-01 | gemini-3.8-flash-high | 0 | ❌ | 0 | 48 | A | B | A | A,A | 16 | 64 | 774 |  | test_outputs.py::test_clean_html_unchanged: The test failed in the call phase due to an as |
| C6-01 | gemini-4-argon-high | 0 | ❌ | 0 | 56 | A | B | A | P,A | 29 | 54 | 361 |  | test_outputs.py::test_clean_html_unchanged: The test failed in the call phase due to an as |
| C6-01 | gemini-4-argon-high | 0 | ❌ | 0 | 56 | A | B | A | P,A | 30 | 56 | 427* | timeout | test_outputs.py::test_clean_html_unchanged: The test failed in the call phase due to an as |
| C6-01 | gemini-4-argon-high | 0 | ❌ | 0 | — | – | – | – | –,– | 30 | 74 | 462* | timeout, no code | test_outputs.py::test_filter_blocks_xss: The test failed in the call phase due to an asser |
| C6-02 | claude-opus-5-5 | 0 | ✅ | 1 | 90 | A | P | P | P | 9 | 24 | 1184 |  | resolved (F2P 59/59, P2P 44/44) |
| C6-02 | claude-opus-5-5 | 0 | ✅ | 1 | 60 | A | A | A | A | 14 | 28 | 1387 |  | resolved (F2P 59/59, P2P 44/44) |
| C6-02 | claude-opus-5-5 | 0 | ✅ | 1 | 70 | A | A | A | P | 10 | 25 | 1173 |  | resolved (F2P 59/59, P2P 44/44) |
| C6-02 | gemini-3.6-flash-high | 0 | ❌ | 0 | 45 | A | A | B | A | 22 | 143 | 1576 |  | not resolved (F2P 58/59, P2P 44/44) |
| C6-02 | gemini-3.6-flash-high | 0 | ❌ | 0 | 30 | A | A | B | B | 12 | 109 | 870 |  | not resolved (F2P 57/59, P2P 44/44) |
| C6-02 | gemini-3.6-flash-high | 0 | ❌ | 0 | 15 | A | B | B | B | 15 | 173 | 1370 |  | not resolved (F2P 57/59, P2P 9/44) |
| C6-02 | gemini-3.8-flash-high | 0 | ✅ | 1 | 60 | A | A | A | A | 41 | 256 | 1365 |  | resolved (F2P 59/59, P2P 44/44) |
| C6-02 | gemini-3.8-flash-high | 0 | ✅ | 1 | 45 | A | B | A | A | 51 | 260 | 4000 |  | resolved (F2P 59/59, P2P 44/44) |
| C6-02 | gemini-3.8-flash-high | 0 | ✅ | 1 | 60 | A | A | A | A | 48 | 281 | 2590 |  | resolved (F2P 59/59, P2P 44/44) |
| C6-02 | gemini-4-argon-high | 0 | ✅ | 1 | 30 | A | B | A | B | 51 | 157 | 986 |  | resolved (F2P 59/59, P2P 44/44) |
| C6-02 | gemini-4-argon-high | 0 | ✅ | 1 | 30 | A | B | A | B | 58 | 211 | 1733 |  | resolved (F2P 59/59, P2P 44/44) |
| C6-02 | gemini-4-argon-high | 0 | ✅ | 1 | 15 | A | B | B | B | 48 | 198 | 1609 |  | resolved (F2P 59/59, P2P 44/44) |
| C6-03 | claude-opus-5-5 | 0 | ❌ | 0 | 44 | A | A | B | B,P | 2 | 13 | 331 |  | test_outputs.py::test_jump_analyzer_test_video: The test failed in the call phase due to a |
| C6-03 | claude-opus-5-5 | 0 | ❌ | 0 | 44 | A | A | B | B,P | 2 | 10 | 206 |  | test_outputs.py::test_jump_analyzer_test_video: The test failed in the call phase due to a |
| C6-03 | claude-opus-5-5 | 0 | ❌ | 0 | 48 | A | A | A | B,A | 3 | 15 | 424 |  | test_outputs.py::test_jump_analyzer_example_video: The test failed in the call phase due t |
| C6-03 | gemini-3.6-flash-high | 0 | ❌ | 0 | 56 | A | B | A | A,P | 20 | 99 | 1010 |  | test_outputs.py::test_jump_analyzer_test_video: The test failed in the call phase due to a |
| C6-03 | gemini-3.6-flash-high | 0 | ❌ | 0 | 48 | A | B | A | A,A | 14 | 70 | 475 |  | test_outputs.py::test_jump_analyzer_test_video: The test failed in the call phase due to a |
| C6-03 | gemini-3.6-flash-high | 0 | ✅ | 1 | 36 | A | B | A | B,A | 4 | 66 | 547 |  | all 5 tests passed |
| C6-03 | gemini-3.8-flash-high | 0 | ❌ | 0 | 24 | A | B | B | B,A | 25 | 130 | 715 |  | test_outputs.py::test_jump_analyzer_test_video: The test failed in the call phase due to a |
| C6-03 | gemini-3.8-flash-high | 0 | ❌ | 0 | 32 | A | B | B | B,P | 32 | 86 | 890 |  | test_outputs.py::test_jump_analyzer_test_video: The test failed in the call phase due to a |
| C6-03 | gemini-3.8-flash-high | 0 | ❌ | 0 | 48 | A | B | A | A,A | 52 | 146 | 964 |  | test_outputs.py::test_jump_analyzer_test_video: The test failed in the call phase due to a |
| C6-03 | gemini-4-argon-high | 0 | ❌ | 0 | 24 | A | B | B | B,A | 14 | 46 | 304 |  | test_outputs.py::test_jump_analyzer_test_video: The test failed in the call phase due to a |
| C6-03 | gemini-4-argon-high | 0 | ✅ | 1 | 56 | A | B | A | A,P | 11 | 39 | 161 |  | all 5 tests passed |
| C6-03 | gemini-4-argon-high | 0 | ❌ | 0 | 24 | A | B | B | B,A | 11 | 38 | 153 |  | test_outputs.py::test_jump_analyzer_test_video: The test failed in the call phase due to a |
| C6-04 | claude-opus-5-5 | 0 | ✅ | 1 | 60 | A | A | A | A | 1 | 3 | 69 |  | all 2 tests passed |
| C6-04 | claude-opus-5-5 | 0 | ✅ | 1 | 60 | A | A | A | A | 1 | 5 | 109 |  | all 2 tests passed |
| C6-04 | claude-opus-5-5 | 0 | ✅ | 1 | 60 | – | – | – | A | 1 | 3 | 70 |  | all 2 tests passed |
| C6-04 | gemini-3.6-flash-high | 0 | ✅ | 1 | 70 | P | A | A | A | 12 | 65 | 490 |  | all 2 tests passed |
| C6-04 | gemini-3.6-flash-high | 0 | ✅ | 1 | 60 | – | – | – | A | 9 | 42 | 236 |  | all 2 tests passed |
| C6-04 | gemini-3.6-flash-high | 0 | ❌ | 0 | 0 | – | – | – | B | 7 | 49 | 308 |  | test_outputs.py::test_data_matches: The test failed in the call phase due to an assertion  |
| C6-04 | gemini-3.8-flash-high | 0 | ✅ | 1 | 60 | A | A | A | A | 12 | 49 | 331 |  | all 2 tests passed |
| C6-04 | gemini-3.8-flash-high | 0 | ✅ | 1 | 60 | – | – | – | A | 11 | 43 | 293 |  | all 2 tests passed |
| C6-04 | gemini-3.8-flash-high | 0 | ✅ | 1 | 60 | – | – | – | A | 15 | 97 | 446 |  | all 2 tests passed |
| C6-04 | gemini-4-argon-high | 0 | ❌ | 0 | — | – | – | – | – | 30 | 83 | 456* | timeout, no code | test_outputs.py::test_result_exists: The test failed in the call phase due to an assertion |
| C6-04 | gemini-4-argon-high | 0 | ❌ | 0 | 0 | – | – | – | B | 15 | 56 | 237 |  | test_outputs.py::test_data_matches: The test failed in the call phase due to an assertion  |
| C6-04 | gemini-4-argon-high | 0 | ❌ | 0 | — | – | – | – | – | 30 | 68 | 411* | timeout, no code | test_outputs.py::test_result_exists: The test failed in the call phase due to an assertion |
| C6-05 | claude-opus-5-5 | 0 | ✅ | 1 | 56 | A | A | B | A,P | 0 | 3 | 72 |  | all 1 tests passed |
| C6-05 | claude-opus-5-5 | 0 | ✅ | 1 | 56 | A | A | B | A,P | 1 | 4 | 96 |  | all 1 tests passed |
| C6-05 | claude-opus-5-5 | 0 | ✅ | 1 | 68 | A | A | A | A,P | 1 | 3 | 76 |  | all 1 tests passed |
| C6-05 | gemini-3.6-flash-high | 0 | ❌ | 0 | 48 | A | A | B | A,A | 2 | 38 | 208 |  | test_outputs.py::test_fibonacci_polyglot: The test failed in the call phase due to an asse |
| C6-05 | gemini-3.6-flash-high | 0 | ✅ | 1 | 56 | A | A | B | A,P | 3 | 49 | 349 |  | all 1 tests passed |
| C6-05 | gemini-3.6-flash-high | 0 | ❌ | 0 | 48 | A | A | B | A,A | 7 | 40 | 260 |  | test_outputs.py::test_fibonacci_polyglot: The test failed in the call phase due to an asse |
| C6-05 | gemini-3.8-flash-high | 0 | ✅ | 1 | 64 | A | P | B | A,P | 7 | 48 | 257 |  | all 1 tests passed |
| C6-05 | gemini-3.8-flash-high | 0 | ✅ | 1 | 76 | A | P | A | A,P | 5 | 41 | 253 |  | all 1 tests passed |
| C6-05 | gemini-3.8-flash-high | 0 | ✅ | 1 | 68 | A | A | A | A,P | 8 | 40 | 195 |  | all 1 tests passed |
| C6-05 | gemini-4-argon-high | 0 | ✅ | 1 | 68 | A | A | A | A,P | 4 | 19 | 80 |  | all 1 tests passed |
| C6-05 | gemini-4-argon-high | 0 | ✅ | 1 | 68 | A | A | A | A,P | 2 | 8 | 50 |  | all 1 tests passed |
| C6-05 | gemini-4-argon-high | 0 | ✅ | 1 | 56 | A | A | B | A,P | 1 | 5 | 27 |  | all 1 tests passed |
| C6-06 | claude-opus-5-5 | 0 | ✅ | 1 | 92 | P | P | P | P,A | 1 | 4 | 95 |  | all 6 tests passed |
| C6-06 | claude-opus-5-5 | 0 | ✅ | 1 | 76 | P | A | A | A,P | 1 | 5 | 111 |  | all 6 tests passed |
| C6-06 | claude-opus-5-5 | 0 | ✅ | 1 | 76 | P | A | A | A,P | 1 | 4 | 93 |  | all 6 tests passed |
| C6-06 | gemini-3.6-flash-high | 0 | ✅ | 1 | 76 | A | A | A | P,P | 3 | 32 | 204 |  | all 6 tests passed |
| C6-06 | gemini-3.6-flash-high | 0 | ✅ | 1 | 92 | P | A | P | P,P | 5 | 42 | 252 |  | all 6 tests passed |
| C6-06 | gemini-3.6-flash-high | 0 | ❌ | 0 | 0 | B | B | B | B,B | 15 | 22 | 164* | timeout | test_outputs.py::test_run_py_file_exists: The test failed in the call phase due to an asse |
| C6-06 | gemini-3.8-flash-high | 0 | ❌ | 0 | — | – | – | – | –,– | 15 | 56 | 364* | timeout, no code | test_outputs.py::test_run_py_file_exists: The test failed in the call phase due to an asse |
| C6-06 | gemini-3.8-flash-high | 0 | ✅ | 1 | 64 | A | B | A | P,P | 12 | 76 | 383 |  | all 6 tests passed |
| C6-06 | gemini-3.8-flash-high | 0 | ❌ | 0 | — | – | – | – | –,– | 15 | 87 | 442* | timeout, no code | test_outputs.py::test_run_py_file_exists: The test failed in the call phase due to an asse |
| C6-06 | gemini-4-argon-high | 0 | ❌ | 0 | — | – | – | – | –,– | 15 | 35 | 190* | timeout, no code | test_outputs.py::test_run_py_file_exists: The test failed in the call phase due to an asse |
| C6-06 | gemini-4-argon-high | 0 | ❌ | 0 | — | – | – | – | –,– | 15 | 34 | 185* | timeout, no code | test_outputs.py::test_run_py_file_exists: The test failed in the call phase due to an asse |
| C6-06 | gemini-4-argon-high | 0 | ❌ | 0 | — | – | – | – | –,– | 15 | 41 | 184* | timeout, no code | test_outputs.py::test_run_py_file_exists: The test failed in the call phase due to an asse |
| C6-07 | claude-opus-5-5 | 0 | ✅ | 1 | 68 | P | A | A | A,A | 6 | 24 | 1227 |  | resolved (F2P 8/8, P2P 42/42) |
| C6-07 | claude-opus-5-5 | 0 | ❌ | 0 | 68 | P | A | A | A,A | 4 | 21 | 1019 |  | not resolved (F2P 7/8, P2P 42/42) |
| C6-07 | claude-opus-5-5 | 0 | ✅ | 1 | 76 | P | A | A | A,P | 6 | 27 | 1321 |  | resolved (F2P 8/8, P2P 42/42) |
| C6-07 | gemini-3.6-flash-high | 0 | ✅ | 1 | 60 | A | A | A | A,A | 15 | 96 | 981 |  | resolved (F2P 8/8, P2P 42/42) |
| C6-07 | gemini-3.6-flash-high | 0 | ✅ | 1 | 60 | A | A | A | A,A | 18 | 172 | 1609 |  | resolved (F2P 8/8, P2P 42/42) |
| C6-07 | gemini-3.6-flash-high | 0 | ✅ | 1 | 60 | A | A | A | A,A | 12 | 103 | 669 |  | resolved (F2P 8/8, P2P 42/42) |
| C6-07 | gemini-3.8-flash-high | 0 | ✅ | 1 | 60 | A | A | A | A,A | 45 | 259 | 1775 |  | resolved (F2P 8/8, P2P 42/42) |
| C6-07 | gemini-3.8-flash-high | 0 | ✅ | 1 | 60 | A | A | A | A,A | 40 | 260 | 2418 |  | resolved (F2P 8/8, P2P 42/42) |
| C6-07 | gemini-3.8-flash-high | 0 | ✅ | 1 | 56 | P | B | A | A,A | 33 | 190 | 1132 |  | resolved (F2P 8/8, P2P 42/42) |
| C6-07 | gemini-4-argon-high | 0 | ✅ | 1 | 60 | A | A | A | A,A | 132 | 362 | 2443 |  | resolved (F2P 8/8, P2P 42/42) |
| C6-07 | gemini-4-argon-high | 0 | ✅ | 1 | 60 | A | A | A | A,A | 97 | 248 | 1855 |  | resolved (F2P 8/8, P2P 42/42) |
| C6-07 | gemini-4-argon-high | 0 | ✅ | 1 | 60 | A | A | A | A,A | 113 | 293 | 1769 |  | resolved (F2P 8/8, P2P 42/42) |
