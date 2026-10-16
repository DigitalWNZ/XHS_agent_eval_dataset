# C8 campaign report (runs ≥ 20261015_183739, < 20261015_234455)

54 trials, 6 setups, rubric v3.0. **D1** = pass rate on the source benchmark's hidden tests (cell tier snapped to 100/67/33/0). **D2** = code quality from the LLM judge (Claude Opus 5.5): Readability, Maintainability, Robustness + 1–2 case items, perfect 1 / accept 0.6 / bad 0, quality = 100 × mean. D1 and D2 are not combined. Trials with no code change cannot be judged (na) and are excluded from D2.

## Per case (passes/trials · D2 quality)

| Case | Former ID | Task | claude-opus-5-5 | gemini-3.6-flash-high | gemini-3.8-flash-high | gemini-4-argon-high | gemini-4-argon-low | gemini-4-argon-medium |
|---|---|---|---|---|---|---|---|---|
| C8-01 | C6-05 | SWE-bench Verified / django__django-15957 | 3/3 · 97 | 0/3 · 20 | 0/3 · 47 | 0/3 · — ∅3 | 1/3 · 62 ∅1 | 0/3 · 80 ∅2 |
| C8-02 | C6-07 | FrontierSWE v2 / ffmpeg-swscale-rewrite | 2/3 · 48 | 0/3 · 24 | 0/3 · 24 | 1/3 · 45 | 0/3 · 45 | 0/3 · 36 |
| C8-03 | C7-02 | Terminal-Bench 2.0 / query-optimize | 1/3 · 77 | 3/3 · 80 | 2/3 · 70 ∅1 | 0/3 · — ∅3 | 2/3 · 52 ∅1 | 1/3 · 30 ∅2 |

∅n = n trials ended with no code change (all were agent timeouts); ⚠n = invalid (validity audit).

## Per model

| Model | Trials | Passes | Pass rate | D1 (mean case tier) | D2 quality (graded trials) | No-code trials | Timeouts | Invalid |
|---|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 9 | 6 | 67% | 67 | 74 (n=9) | 0 | 0 | 0 |
| gemini-3.6-flash-high | 9 | 3 | 33% | 33 | 41 (n=9) | 0 | 3 | 0 |
| gemini-3.8-flash-high | 9 | 2 | 22% | 22 | 44 (n=8) | 1 | 2 | 0 |
| gemini-4-argon-high | 9 | 1 | 11% | 11 | 45 (n=3) | 6 | 8 | 0 |
| gemini-4-argon-low | 9 | 3 | 33% | 33 | 52 (n=7) | 2 | 4 | 0 |
| gemini-4-argon-medium | 9 | 1 | 11% | 11 | 44 (n=5) | 4 | 8 | 0 |

## Run metrics per model (mean per trial)

Agent time = wall time of the agent run (capped by the budget). Tool calls are counted from the trajectory. Tokens = input + output as reported by the agent CLI; agy reports no usage when it hits its time budget, so for those trials the per-step usage in the saved trajectory is summed (marked * in the per-trial table; only available for runs after the partial-trajectory fix). Turns: Claude Code reports turns; agy always reports 1 per session, so use tool calls to compare.

| Model | Agent time (min) | Tool calls | Tokens (K) | Turns (Claude) | Cost USD (Claude, total) |
|---|---|---|---|---|---|
| claude-opus-5-5 | 25 | 76 | 11460 | 54 | 59.77 |
| gemini-3.6-flash-high | 45 | 303 | 3074 | — | — |
| gemini-3.8-flash-high | 48 | 330 | 2515 | — | — |
| gemini-4-argon-high | 52 | 146 | 942 | — | — |
| gemini-4-argon-low | 51 | 99 | 953 | — | — |
| gemini-4-argon-medium | 55 | 108 | 876 | — | — |

## Run metrics per case (mean per trial: agent time min · tool calls · tokens K)

Same definitions as above, averaged over the trials of one case and model (— = no data, e.g. agy timeouts before the partial-trajectory fix).

| Case | Task | claude-opus-5-5 | gemini-3.6-flash-high | gemini-3.8-flash-high | gemini-4-argon-high | gemini-4-argon-low | gemini-4-argon-medium |
|---|---|---|---|---|---|---|---|
| C8-01 | SWE-bench Verified / django__django-15957 | 1.2 · 13 · 341 | 5.1 · 44 · 376 | 14 · 117 · 698 | 30 · 123 · 759 | 28 · 94 · 773 | 30 · 89 · 662 |
| C8-02 | FrontierSWE v2 / ffmpeg-swscale-rewrite | 64 · 208 · 33935 | 120 · 808 · 8332 | 117 · 800 · 6401 | 112 · 260 · 1845 | 112 · 171 · 1929 | 120 · 185 · 1742 |
| C8-03 | Terminal-Bench 2.0 / query-optimize | 11 · 6 · 105 | 9.6 · 57 · 513 | 14 · 75 · 444 | 15 · 55 · 223 | 13 · 33 · 156 | 15 · 50 · 223 |

## D2 item scores per model (mean over judged items, 0–100)

| Model | Readability | Maintainability | Robustness | Case-specific | Quality |
|---|---|---|---|---|---|
| claude-opus-5-5 | 73 | 62 | 76 | 75 | 74 |
| gemini-3.6-flash-high | 67 | 24 | 42 | 30 | 41 |
| gemini-3.8-flash-high | 70 | 30 | 48 | 27 | 44 |
| gemini-4-argon-high | 60 | 0 | 60 | 53 | 45 |
| gemini-4-argon-low | 66 | 43 | 51 | 48 | 52 |
| gemini-4-argon-medium | 68 | 24 | 36 | 42 | 44 |

## Quality among passing vs failing trials

| Model | D2 on passing trials | D2 on failing trials (with code) |
|---|---|---|
| claude-opus-5-5 | 83 | 55 |
| gemini-3.6-flash-high | 80 | 22 |
| gemini-3.8-flash-high | 70 | 35 |
| gemini-4-argon-high | 56 | 40 |
| gemini-4-argon-low | 58 | 48 |
| gemini-4-argon-medium | 30 | 47 |

## Validity findings

- results/c8_runs/C8-01_agy_gemini-3.6-flash-high_20261015_184010/trial_0: test_tampering (provisional) — existing test lines changed/removed (2): tests/prefetch_related/tests.py

## Per trial

Item levels: P = perfect (100), A = accept (60), B = bad (0), – = not applicable. Read / Maint / Robust = the 3 common items; Case = the case-specific item(s) in order.

| Case | Model | Trial | Pass | Score | D2 | Read | Maint | Robust | Case | Time (min) | Tool calls | Tokens (K) | Notes | Verifier reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C8-01 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P | 1 | 10 | 240 |  | resolved (F2P 4/4, P2P 89/89) |
| C8-01 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P | 2 | 18 | 503 |  | resolved (F2P 4/4, P2P 89/89) |
| C8-01 | claude-opus-5-5 | 0 | ✅ | 1 | 90 | P | P | P | A | 1 | 11 | 278 |  | resolved (F2P 4/4, P2P 89/89) |
| C8-01 | gemini-3.6-flash-high | 0 | ❌ | 0 | 15 | A | B | B | B | 7 | 37 | 352 |  | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_relate |
| C8-01 | gemini-3.6-flash-high | 0 | ❌ | 0 | 30 | A | B | A | B | 5 | 50 | 433 |  | not resolved (F2P 0/4, P2P 87/89); first failure: test_foreignkey_reverse (prefetch_relate |
| C8-01 | gemini-3.6-flash-high | 0 | ❌ | 0 | 15 | A | B | B | B | 3 | 44 | 344 |  | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_relate |
| C8-01 | gemini-3.8-flash-high | 0 | ❌ | 0 | 55 | P | A | A | B | 11 | 106 | 870 |  | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_relate |
| C8-01 | gemini-3.8-flash-high | 0 | ❌ | 0 | 55 | P | A | A | B | 13 | 121 | 613 |  | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_relate |
| C8-01 | gemini-3.8-flash-high | 0 | ❌ | 0 | 30 | A | B | A | B | 17 | 123 | 612 |  | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_relate |
| C8-01 | gemini-4-argon-high | 0 | ❌ | 0 | — | – | – | – | – | 30 | 127 | 1169* | timeout, no code | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_relate |
| C8-01 | gemini-4-argon-high | 0 | ❌ | 0 | — | – | – | – | – | 30 | 132 | 575* | timeout, no code | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_relate |
| C8-01 | gemini-4-argon-high | 0 | ❌ | 0 | — | – | – | – | – | 30 | 109 | 534* | timeout, no code | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_relate |
| C8-01 | gemini-4-argon-low | 0 | ❌ | 0 | 55 | P | A | A | B | 30 | 82 | 685* | timeout | not resolved (F2P 1/4, P2P 89/89); first failure: test_m2m_forward (prefetch_related.tests |
| C8-01 | gemini-4-argon-low | 0 | ✅ | 1 | 70 | A | A | A | P | 23 | 108 | 689 |  | resolved (F2P 4/4, P2P 89/89) |
| C8-01 | gemini-4-argon-low | 0 | ❌ | 0 | — | – | – | – | – | 30 | 92 | 946* | timeout, no code | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_relate |
| C8-01 | gemini-4-argon-medium | 0 | ❌ | 0 | — | – | – | – | – | 30 | 68 | 767* | timeout, no code | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_relate |
| C8-01 | gemini-4-argon-medium | 0 | ❌ | 0 | — | – | – | – | – | 30 | 113 | 495* | timeout, no code | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_relate |
| C8-01 | gemini-4-argon-medium | 0 | ❌ | 0 | 80 | P | A | A | P | 30 | 85 | 725* | timeout | not resolved (F2P 4/4, P2P 86/89); first failure: test_using_is_honored_custom_qs (prefetc |
| C8-02 | claude-opus-5-5 | 0 | ✅ | 0.117 | 64 | A | B | A | P,P | 63 | 150 | 37702 |  | score=0.1175; reward 0.117492 |
| C8-02 | claude-opus-5-5 | 0 | ❌ | 0 | 24 | A | B | B | B,A | 54 | 213 | 35607 |  | score=0.0000; output does not meet the accuracy bars |
| C8-02 | claude-opus-5-5 | 0 | ✅ | 0.174 | 56 | A | B | A | A,P | 75 | 260 | 28496 |  | score=0.1742; reward 0.174208 |
| C8-02 | gemini-3.6-flash-high | 0 | ❌ | 0 | 12 | B | B | B | B,A | 120 | 962 | 10115* | timeout | score=0.0000; output does not meet the accuracy bars |
| C8-02 | gemini-3.6-flash-high | 0 | ❌ | 0 | 24 | A | B | B | B,A | 120 | 984 | 10669* | timeout | score=0.0000; output does not meet the accuracy bars |
| C8-02 | gemini-3.6-flash-high | 0 | ❌ | 0 | 36 | A | B | A | B,A | 120 | 478 | 4211* | timeout | score=0.0000; output does not meet the accuracy bars |
| C8-02 | gemini-3.8-flash-high | 0 | ❌ | 0 | 24 | A | B | B | B,A | 116 | 773 | 7468 |  | score=0.0000; output does not meet the accuracy bars |
| C8-02 | gemini-3.8-flash-high | 0 | ❌ | 0 | 24 | A | B | B | B,A | 120 | 865 | 6088* | timeout | score=0.0000; output does not meet the accuracy bars |
| C8-02 | gemini-3.8-flash-high | 0 | ❌ | 0 | 24 | A | B | B | B,A | 117 | 761 | 5648 |  | score=0.0000; reward 0.0 |
| C8-02 | gemini-4-argon-high | 0 | ✅ | 0.127 | 56 | A | B | A | A,P | 97 | 238 | 1636 |  | score=0.1269; model says 4.274x less work but native runtime is 0.874x - review |
| C8-02 | gemini-4-argon-high | 0 | ❌ | 0 | 36 | A | B | A | B,A | 120 | 274 | 2130* | timeout | score=0.0000; output does not meet the accuracy bars |
| C8-02 | gemini-4-argon-high | 0 | ❌ | 0 | 44 | A | B | A | B,P | 120 | 269 | 1768* | timeout | score=0.0000; output does not meet the accuracy bars |
| C8-02 | gemini-4-argon-low | 0 | ❌ | 0.0542 | 68 | A | A | A | A,P | 116 | 215 | 2566 |  | score=0.0542; reward 0.054179 |
| C8-02 | gemini-4-argon-low | 0 | ❌ | 0 | 24 | A | B | B | B,A | 120 | 121 | 2206* | timeout | score=0.0000; output does not meet the accuracy bars |
| C8-02 | gemini-4-argon-low | 0 | ❌ | 0 | 44 | A | B | A | B,P | 99 | 176 | 1015 |  | score=0.0000; output does not meet the accuracy bars |
| C8-02 | gemini-4-argon-medium | 0 | ❌ | 0 | 12 | A | B | B | B,B | 120 | 152 | 1172* | timeout | score=0.0000; the submission did not build |
| C8-02 | gemini-4-argon-medium | 0 | ❌ | 0.0763 | 48 | A | B | A | A,A | 120 | 231 | 1739* | timeout | score=0.0763; model says 3.016x less work but native runtime is 0.938x - review |
| C8-02 | gemini-4-argon-medium | 0 | ❌ | 0 | 48 | A | B | A | A,A | 120 | 173 | 2315* | timeout | score=0.0000; output does not meet the accuracy bars |
| C8-03 | claude-opus-5-5 | 0 | ✅ | 1 | 90 | A | P | P | P | 7 | 4 | 102 |  | all 6 tests passed |
| C8-03 | claude-opus-5-5 | 0 | ❌ | 0 | 60 | A | A | A | A | 14 | 7 | 164 |  | test_outputs.py::test_compare_golden_vs_solution_runtime: The test failed in the call phas |
| C8-03 | claude-opus-5-5 | 0 | ❌ | 0 | 80 | A | P | P | A | 12 | 7 | 48 |  | test_outputs.py::test_compare_golden_vs_solution_runtime: The test failed in the call phas |
| C8-03 | gemini-3.6-flash-high | 0 | ✅ | 1 | 90 | P | P | P | A | 5 | 35 | 217 |  | all 6 tests passed |
| C8-03 | gemini-3.6-flash-high | 0 | ✅ | 1 | 70 | P | A | A | A | 10 | 83 | 982 |  | all 6 tests passed |
| C8-03 | gemini-3.6-flash-high | 0 | ✅ | 1 | 80 | P | A | P | A | 14 | 52 | 339 |  | all 6 tests passed |
| C8-03 | gemini-3.8-flash-high | 0 | ✅ | 1 | 70 | A | A | P | A | 14 | 80 | 578 |  | all 6 tests passed |
| C8-03 | gemini-3.8-flash-high | 0 | ❌ | 0 | — | – | – | – | – | 15 | 58 | 333* | timeout, no code | test_outputs.py::test_compare_golden_vs_solution_runtime: The test failed in the call phas |
| C8-03 | gemini-3.8-flash-high | 0 | ✅ | 1 | 70 | A | A | P | A | 12 | 87 | 422 |  | all 6 tests passed |
| C8-03 | gemini-4-argon-high | 0 | ❌ | 0 | — | – | – | – | – | 15 | 55 | 207* | timeout, no code | test_outputs.py::test_compare_golden_vs_solution_runtime: The test failed in the call phas |
| C8-03 | gemini-4-argon-high | 0 | ❌ | 0 | — | – | – | – | – | 15 | 57 | 220* | timeout, no code | test_outputs.py::test_compare_golden_vs_solution_runtime: The test failed in the call phas |
| C8-03 | gemini-4-argon-high | 0 | ❌ | 0 | — | – | – | – | – | 15 | 53 | 243* | timeout, no code | test_outputs.py::test_compare_golden_vs_solution_runtime: The test failed in the call phas |
| C8-03 | gemini-4-argon-low | 0 | ✅ | 1 | 60 | A | A | A | A | 13 | 35 | 200 |  | all 6 tests passed |
| C8-03 | gemini-4-argon-low | 0 | ❌ | 0 | — | – | – | – | – | 15 | 25 | 106* | timeout, no code | test_outputs.py::test_compare_golden_vs_solution_runtime: The test failed in the call phas |
| C8-03 | gemini-4-argon-low | 0 | ✅ | 1 | 45 | A | A | A | B | 11 | 39 | 164 |  | all 6 tests passed |
| C8-03 | gemini-4-argon-medium | 0 | ❌ | 0 | — | – | – | – | – | 15 | 46 | 234* | timeout, no code | test_outputs.py::test_compare_golden_vs_solution_runtime: The test failed in the call phas |
| C8-03 | gemini-4-argon-medium | 0 | ❌ | 0 | — | – | – | – | – | 15 | 51 | 248* | timeout, no code | test_outputs.py::test_compare_golden_vs_solution_runtime: The test failed in the call phas |
| C8-03 | gemini-4-argon-medium | 0 | ✅ | 1 | 30 | A | A | B | B | 15 | 53 | 185 |  | all 6 tests passed |
