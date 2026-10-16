# C6 campaign report (runs ≥ 20261015_234242, < 20261015_234454)

42 trials, 2 setups, rubric v3.0. **D1** = pass rate on the source benchmark's hidden tests (cell tier snapped to 100/67/33/0). **D2** = code quality from the LLM judge (Claude Opus 5.5): Readability, Maintainability, Robustness + 1–2 case items, perfect 1 / accept 0.6 / bad 0, quality = 100 × mean. D1 and D2 are not combined. Trials with no code change cannot be judged (na) and are excluded from D2.

## Per case (passes/trials · D2 quality)

| Case | Former ID | Task | gemini-4-argon-low | gemini-4-argon-medium |
|---|---|---|---|---|
| C6-01 | C6-01 | Terminal-Bench 2.0 / filter-js-from-html | 0/3 · 53 | 0/3 · 56 ∅1 |
| C6-02 | C6-03 | DeepSWE v1.1 / pebble-durability-wait-apis | 3/3 · 58 | 2/3 · 45 ∅1 |
| C6-03 | C6-04 | Terminal-Bench 2.0 / video-processing | 2/3 · 56 | 1/3 · 47 |
| C6-04 | C6-06 | Terminal-Bench 2.0 / mteb-retrieve | 0/3 · 10 | 0/3 · 0 ∅1 |
| C6-05 | C7-01 | Terminal-Bench 2.0 / polyglot-c-py | 3/3 · 73 | 3/3 · 69 |
| C6-06 | C7-03 | Terminal-Bench 2.0 / cancel-async-tasks | 3/3 · 65 | 0/3 · — ∅3 |
| C6-07 | C7-12 | DeepSWE v1.1 / query-persist-restored-query-state | 2/3 · 52 | 3/3 · 56 |

∅n = n trials ended with no code change (all were agent timeouts); ⚠n = invalid (validity audit).

## Per model

| Model | Trials | Passes | Pass rate | D1 (mean case tier) | D2 quality (graded trials) | No-code trials | Timeouts | Invalid |
|---|---|---|---|---|---|---|---|---|
| gemini-4-argon-low | 21 | 13 | 62% | 62 | 53 (n=21) | 0 | 0 | 0 |
| gemini-4-argon-medium | 21 | 9 | 43% | 43 | 48 (n=15) | 6 | 7 | 0 |

## Run metrics per model (mean per trial)

Agent time = wall time of the agent run (capped by the budget). Tool calls are counted from the trajectory. Tokens = input + output as reported by the agent CLI; agy reports no usage when it hits its time budget, so for those trials the per-step usage in the saved trajectory is summed (marked * in the per-trial table; only available for runs after the partial-trajectory fix). Turns: Claude Code reports turns; agy always reports 1 per session, so use tool calls to compare.

| Model | Agent time (min) | Tool calls | Tokens (K) | Turns (Claude) | Cost USD (Claude, total) |
|---|---|---|---|---|---|
| gemini-4-argon-low | 18 | 75 | 538 | — | — |
| gemini-4-argon-medium | 39 | 77 | 783 | — | — |

## Run metrics per case (mean per trial: agent time min · tool calls · tokens K)

Same definitions as above, averaged over the trials of one case and model (— = no data, e.g. agy timeouts before the partial-trajectory fix).

| Case | Task | gemini-4-argon-low | gemini-4-argon-medium |
|---|---|---|---|
| C6-01 | Terminal-Bench 2.0 / filter-js-from-html | 8.1 · 29 · 122 | 29 · 39 · 330 |
| C6-02 | DeepSWE v1.1 / pebble-durability-wait-apis | 27 · 151 · 1201 | 59 · 136 · 1422 |
| C6-03 | Terminal-Bench 2.0 / video-processing | 10 · 38 · 205 | 10 · 32 · 150 |
| C6-04 | Terminal-Bench 2.0 / mteb-retrieve | 8.0 · 26 · 100 | 29 · 51 · 305 |
| C6-05 | Terminal-Bench 2.0 / polyglot-c-py | 1.5 · 9 · 40 | 2.0 · 8 · 40 |
| C6-06 | Terminal-Bench 2.0 / cancel-async-tasks | 9.4 · 33 · 154 | 15 · 28 · 199 |
| C6-07 | DeepSWE v1.1 / query-persist-restored-query-s | 59 · 237 · 1944 | 132 · 244 · 3035 |

## D2 item scores per model (mean over judged items, 0–100)

| Model | Readability | Maintainability | Robustness | Case-specific | Quality |
|---|---|---|---|---|---|
| gemini-4-argon-low | 59 | 28 | 57 | 68 | 53 |
| gemini-4-argon-medium | 60 | 43 | 46 | 60 | 48 |

## Quality among passing vs failing trials

| Model | D2 on passing trials | D2 on failing trials (with code) |
|---|---|---|
| gemini-4-argon-low | 62 | 37 |
| gemini-4-argon-medium | 57 | 35 |

## Validity findings

- results/c6_runs/C6-07_agy_gemini-4-argon-low_20261015_234257/trial_0: test_tampering (provisional) — existing test lines changed/removed (1): packages/svelte-query/tests/createQuery.svelte.test.ts; existing test lines changed/removed (1): packages/vue-query/src/__tests__/useQuery.test.ts
- results/c6_runs/C6-07_agy_gemini-4-argon-low_20261015_234258/trial_0: test_tampering (provisional) — existing test lines changed/removed (1): packages/query-core/src/__tests__/query.test.tsx; existing test lines changed/removed (1): packages/svelte-query/tests/createQuery.svelte.test.ts; existing tes
- results/c6_runs/C6-07_agy_gemini-4-argon-low_20261015_234259/trial_0: test_tampering (provisional) — existing test lines changed/removed (1): packages/query-core/src/__tests__/infiniteQueryObserver.test.tsx; existing test lines changed/removed (1): packages/react-query/src/__tests__/fine-grained-pers
- results/c6_runs/C6-07_agy_gemini-4-argon-medium_20261015_234254/trial_0: test_tampering (provisional) — existing test lines changed/removed (1): packages/query-core/src/__tests__/query.test.tsx; existing test lines changed/removed (1): packages/query-persist-client-core/src/__tests__/createPersister.tes
- results/c6_runs/C6-07_agy_gemini-4-argon-medium_20261015_234255/trial_0: test_tampering (provisional) — existing test lines changed/removed (1): packages/preact-query/src/__tests__/fine-grained-persister.test.tsx; existing test lines changed/removed (1): packages/query-core/src/__tests__/query.test.tsx;
- results/c6_runs/C6-07_agy_gemini-4-argon-medium_20261015_234256/trial_0: test_tampering (provisional) — existing test lines changed/removed (1): packages/preact-query/src/__tests__/fine-grained-persister.test.tsx; existing test lines changed/removed (1): packages/query-persist-client-core/src/__tests__/

## Per trial

Item levels: P = perfect (100), A = accept (60), B = bad (0), – = not applicable. Read / Maint / Robust = the 3 common items; Case = the case-specific item(s) in order.

| Case | Model | Trial | Pass | Score | D2 | Read | Maint | Robust | Case | Time (min) | Tool calls | Tokens (K) | Notes | Verifier reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C6-01 | gemini-4-argon-low | 0 | ❌ | 0 | 56 | A | B | A | P,A | 6 | 31 | 107 |  | test_outputs.py::test_clean_html_unchanged: The test failed in the call phase due to an as |
| C6-01 | gemini-4-argon-low | 0 | ❌ | 0 | 48 | A | B | A | A,A | 11 | 26 | 159 |  | test_outputs.py::test_filter_blocks_xss: The test failed in the call phase due to an asser |
| C6-01 | gemini-4-argon-low | 0 | ❌ | 0 | 56 | A | B | A | P,A | 7 | 29 | 99 |  | test_outputs.py::test_clean_html_unchanged: The test failed in the call phase due to an as |
| C6-01 | gemini-4-argon-medium | 0 | ❌ | 0 | 56 | A | B | A | P,A | 27 | 44 | 271 |  | test_outputs.py::test_clean_html_unchanged: The test failed in the call phase due to an as |
| C6-01 | gemini-4-argon-medium | 0 | ❌ | 0 | 56 | A | B | A | P,A | 30 | 29 | 455* | timeout | test_outputs.py::test_clean_html_unchanged: The test failed in the call phase due to an as |
| C6-01 | gemini-4-argon-medium | 0 | ❌ | 0 | — | – | – | – | –,– | 30 | 44 | 265* | timeout, no code | test_outputs.py::test_filter_blocks_xss: The test failed in the call phase due to an asser |
| C6-02 | gemini-4-argon-low | 0 | ✅ | 1 | 45 | A | A | A | B | 25 | 155 | 998 |  | resolved (F2P 59/59, P2P 44/44) |
| C6-02 | gemini-4-argon-low | 0 | ✅ | 1 | 70 | P | A | A | A | 31 | 147 | 1070 |  | resolved (F2P 59/59, P2P 44/44) |
| C6-02 | gemini-4-argon-low | 0 | ✅ | 1 | 60 | A | A | A | A | 26 | 151 | 1534 |  | resolved (F2P 59/59, P2P 44/44) |
| C6-02 | gemini-4-argon-medium | 0 | ✅ | 1 | 45 | A | A | B | A | 80 | 186 | 2352 |  | resolved (F2P 59/59, P2P 44/44) |
| C6-02 | gemini-4-argon-medium | 0 | ✅ | 1 | 45 | A | A | A | B | 74 | 158 | 1416 |  | resolved (F2P 59/59, P2P 44/44) |
| C6-02 | gemini-4-argon-medium | 0 | ❌ | 0 | — | – | – | – | – | 22 | 63 | 498 | no code | no committed changes (empty model.patch); F2P 0/59, P2P 44/44 |
| C6-03 | gemini-4-argon-low | 0 | ❌ | 0 | 56 | A | B | A | A,P | 13 | 35 | 179 |  | test_outputs.py::test_jump_analyzer_test_video: The test failed in the call phase due to a |
| C6-03 | gemini-4-argon-low | 0 | ✅ | 1 | 56 | A | B | A | A,P | 11 | 45 | 264 |  | all 5 tests passed |
| C6-03 | gemini-4-argon-low | 0 | ✅ | 1 | 56 | A | B | A | A,P | 7 | 34 | 171 |  | all 5 tests passed |
| C6-03 | gemini-4-argon-medium | 0 | ❌ | 0 | 48 | A | B | A | A,A | 10 | 34 | 182 |  | test_outputs.py::test_jump_analyzer_test_video: The test failed in the call phase due to a |
| C6-03 | gemini-4-argon-medium | 0 | ✅ | 1 | 44 | A | B | B | A,P | 10 | 34 | 157 |  | all 5 tests passed |
| C6-03 | gemini-4-argon-medium | 0 | ❌ | 0 | 48 | A | B | A | A,A | 11 | 27 | 109 |  | test_outputs.py::test_jump_analyzer_test_video: The test failed in the call phase due to a |
| C6-04 | gemini-4-argon-low | 0 | ❌ | 0 | 0 | B | B | B | B | 3 | 21 | 76 |  | test_outputs.py::test_data_matches: The test failed in the call phase due to an assertion  |
| C6-04 | gemini-4-argon-low | 0 | ❌ | 0 | 30 | A | B | A | B | 10 | 30 | 120 |  | test_outputs.py::test_data_matches: The test failed in the call phase due to an assertion  |
| C6-04 | gemini-4-argon-low | 0 | ❌ | 0 | 0 | – | – | – | B | 10 | 28 | 104 |  | test_outputs.py::test_data_matches: The test failed in the call phase due to an assertion  |
| C6-04 | gemini-4-argon-medium | 0 | ❌ | 0 | 0 | – | – | – | B | 26 | 59 | 377 |  | test_outputs.py::test_data_matches: The test failed in the call phase due to an assertion  |
| C6-04 | gemini-4-argon-medium | 0 | ❌ | 0 | — | – | – | – | – | 30 | 31 | 232* | timeout, no code | test_outputs.py::test_result_exists: The test failed in the call phase due to an assertion |
| C6-04 | gemini-4-argon-medium | 0 | ❌ | 0 | 0 | – | – | – | B | 30 | 62 | 306* | timeout | test_outputs.py::test_result_exists: The test failed in the call phase due to an assertion |
| C6-05 | gemini-4-argon-low | 0 | ✅ | 1 | 68 | A | A | A | A,P | 2 | 10 | 45 |  | all 1 tests passed |
| C6-05 | gemini-4-argon-low | 0 | ✅ | 1 | 76 | A | P | A | A,P | 1 | 10 | 37 |  | all 1 tests passed |
| C6-05 | gemini-4-argon-low | 0 | ✅ | 1 | 76 | A | P | A | A,P | 1 | 8 | 37 |  | all 1 tests passed |
| C6-05 | gemini-4-argon-medium | 0 | ✅ | 1 | 76 | A | P | A | A,P | 1 | 6 | 29 |  | all 1 tests passed |
| C6-05 | gemini-4-argon-medium | 0 | ✅ | 1 | 68 | A | A | A | A,P | 2 | 8 | 34 |  | all 1 tests passed |
| C6-05 | gemini-4-argon-medium | 0 | ✅ | 1 | 64 | A | P | B | A,P | 3 | 10 | 57 |  | all 1 tests passed |
| C6-06 | gemini-4-argon-low | 0 | ✅ | 1 | 64 | A | B | A | P,P | 7 | 34 | 126 |  | all 6 tests passed |
| C6-06 | gemini-4-argon-low | 0 | ✅ | 1 | 56 | A | B | A | A,P | 11 | 32 | 221 |  | all 6 tests passed |
| C6-06 | gemini-4-argon-low | 0 | ✅ | 1 | 76 | A | A | A | P,P | 10 | 33 | 115 |  | all 6 tests passed |
| C6-06 | gemini-4-argon-medium | 0 | ❌ | 0 | — | – | – | – | –,– | 15 | 27 | 181* | timeout, no code | test_outputs.py::test_run_py_file_exists: The test failed in the call phase due to an asse |
| C6-06 | gemini-4-argon-medium | 0 | ❌ | 0 | — | – | – | – | –,– | 15 | 26 | 231* | timeout, no code | test_outputs.py::test_run_py_file_exists: The test failed in the call phase due to an asse |
| C6-06 | gemini-4-argon-medium | 0 | ❌ | 0 | — | – | – | – | –,– | 15 | 31 | 186* | timeout, no code | test_outputs.py::test_run_py_file_exists: The test failed in the call phase due to an asse |
| C6-07 | gemini-4-argon-low | 0 | ✅ | 1 | 60 | A | A | A | A,A | 58 | 295 | 2213 |  | resolved (F2P 8/8, P2P 42/42) |
| C6-07 | gemini-4-argon-low | 0 | ✅ | 1 | 48 | A | B | A | A,A | 69 | 234 | 2060 |  | resolved (F2P 8/8, P2P 42/42) |
| C6-07 | gemini-4-argon-low | 0 | ❌ | 0 | 48 | A | B | A | A,A | 49 | 182 | 1559 |  | not resolved (F2P 7/8, P2P 42/42) |
| C6-07 | gemini-4-argon-medium | 0 | ✅ | 1 | 48 | A | A | A | A,B | 143 | 234 | 3792 |  | resolved (F2P 8/8, P2P 42/42) |
| C6-07 | gemini-4-argon-medium | 0 | ✅ | 1 | 60 | A | A | A | A,A | 108 | 179 | 2144 |  | resolved (F2P 8/8, P2P 42/42) |
| C6-07 | gemini-4-argon-medium | 0 | ✅ | 1 | 60 | A | A | A | A,A | 144 | 319 | 3168 |  | resolved (F2P 8/8, P2P 42/42) |
