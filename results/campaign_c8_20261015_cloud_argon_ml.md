# C8 campaign report (runs ≥ 20261015_234242, < 20261015_234454)

18 trials, 2 setups, rubric v3.0. **D1** = pass rate on the source benchmark's hidden tests (cell tier snapped to 100/67/33/0). **D2** = code quality from the LLM judge (Claude Opus 5.5): Readability, Maintainability, Robustness + 1–2 case items, perfect 1 / accept 0.6 / bad 0, quality = 100 × mean. D1 and D2 are not combined. Trials with no code change cannot be judged (na) and are excluded from D2.

## Per case (passes/trials · D2 quality)

| Case | Former ID | Task | gemini-4-argon-low | gemini-4-argon-medium |
|---|---|---|---|---|
| C8-01 | C6-05 | SWE-bench Verified / django__django-15957 | 1/3 · 62 ∅1 | 0/3 · 80 ∅2 |
| C8-02 | C6-07 | FrontierSWE v2 / ffmpeg-swscale-rewrite | 0/3 · 45 | 0/3 · 36 |
| C8-03 | C7-02 | Terminal-Bench 2.0 / query-optimize | 2/3 · 52 ∅1 | 1/3 · 30 ∅2 |

∅n = n trials ended with no code change (all were agent timeouts); ⚠n = invalid (validity audit).

## Per model

| Model | Trials | Passes | Pass rate | D1 (mean case tier) | D2 quality (graded trials) | No-code trials | Timeouts | Invalid |
|---|---|---|---|---|---|---|---|---|
| gemini-4-argon-low | 9 | 3 | 33% | 33 | 52 (n=7) | 2 | 4 | 0 |
| gemini-4-argon-medium | 9 | 1 | 11% | 11 | 44 (n=5) | 4 | 8 | 0 |

## Run metrics per model (mean per trial)

Agent time = wall time of the agent run (capped by the budget). Tool calls are counted from the trajectory. Tokens = input + output as reported by the agent CLI; agy reports no usage when it hits its time budget, so for those trials the per-step usage in the saved trajectory is summed (marked * in the per-trial table; only available for runs after the partial-trajectory fix). Turns: Claude Code reports turns; agy always reports 1 per session, so use tool calls to compare.

| Model | Agent time (min) | Tool calls | Tokens (K) | Turns (Claude) | Cost USD (Claude, total) |
|---|---|---|---|---|---|
| gemini-4-argon-low | 51 | 99 | 953 | — | — |
| gemini-4-argon-medium | 55 | 108 | 876 | — | — |

## Run metrics per case (mean per trial: agent time min · tool calls · tokens K)

Same definitions as above, averaged over the trials of one case and model (— = no data, e.g. agy timeouts before the partial-trajectory fix).

| Case | Task | gemini-4-argon-low | gemini-4-argon-medium |
|---|---|---|---|
| C8-01 | SWE-bench Verified / django__django-15957 | 28 · 94 · 773 | 30 · 89 · 662 |
| C8-02 | FrontierSWE v2 / ffmpeg-swscale-rewrite | 112 · 171 · 1929 | 120 · 185 · 1742 |
| C8-03 | Terminal-Bench 2.0 / query-optimize | 13 · 33 · 156 | 15 · 50 · 223 |

## D2 item scores per model (mean over judged items, 0–100)

| Model | Readability | Maintainability | Robustness | Case-specific | Quality |
|---|---|---|---|---|---|
| gemini-4-argon-low | 66 | 43 | 51 | 48 | 52 |
| gemini-4-argon-medium | 68 | 24 | 36 | 42 | 44 |

## Quality among passing vs failing trials

| Model | D2 on passing trials | D2 on failing trials (with code) |
|---|---|---|
| gemini-4-argon-low | 58 | 48 |
| gemini-4-argon-medium | 30 | 47 |

## Validity findings

none

## Per trial

Item levels: P = perfect (100), A = accept (60), B = bad (0), – = not applicable. Read / Maint / Robust = the 3 common items; Case = the case-specific item(s) in order.

| Case | Model | Trial | Pass | Score | D2 | Read | Maint | Robust | Case | Time (min) | Tool calls | Tokens (K) | Notes | Verifier reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C8-01 | gemini-4-argon-low | 0 | ❌ | 0 | 55 | P | A | A | B | 30 | 82 | 685* | timeout | not resolved (F2P 1/4, P2P 89/89); first failure: test_m2m_forward (prefetch_related.tests |
| C8-01 | gemini-4-argon-low | 0 | ✅ | 1 | 70 | A | A | A | P | 23 | 108 | 689 |  | resolved (F2P 4/4, P2P 89/89) |
| C8-01 | gemini-4-argon-low | 0 | ❌ | 0 | — | – | – | – | – | 30 | 92 | 946* | timeout, no code | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_relate |
| C8-01 | gemini-4-argon-medium | 0 | ❌ | 0 | — | – | – | – | – | 30 | 68 | 767* | timeout, no code | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_relate |
| C8-01 | gemini-4-argon-medium | 0 | ❌ | 0 | — | – | – | – | – | 30 | 113 | 495* | timeout, no code | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_relate |
| C8-01 | gemini-4-argon-medium | 0 | ❌ | 0 | 80 | P | A | A | P | 30 | 85 | 725* | timeout | not resolved (F2P 4/4, P2P 86/89); first failure: test_using_is_honored_custom_qs (prefetc |
| C8-02 | gemini-4-argon-low | 0 | ❌ | 0.0542 | 68 | A | A | A | A,P | 116 | 215 | 2566 |  | score=0.0542; reward 0.054179 |
| C8-02 | gemini-4-argon-low | 0 | ❌ | 0 | 24 | A | B | B | B,A | 120 | 121 | 2206* | timeout | score=0.0000; output does not meet the accuracy bars |
| C8-02 | gemini-4-argon-low | 0 | ❌ | 0 | 44 | A | B | A | B,P | 99 | 176 | 1015 |  | score=0.0000; output does not meet the accuracy bars |
| C8-02 | gemini-4-argon-medium | 0 | ❌ | 0 | 12 | A | B | B | B,B | 120 | 152 | 1172* | timeout | score=0.0000; the submission did not build |
| C8-02 | gemini-4-argon-medium | 0 | ❌ | 0.0763 | 48 | A | B | A | A,A | 120 | 231 | 1739* | timeout | score=0.0763; model says 3.016x less work but native runtime is 0.938x - review |
| C8-02 | gemini-4-argon-medium | 0 | ❌ | 0 | 48 | A | B | A | A,A | 120 | 173 | 2315* | timeout | score=0.0000; output does not meet the accuracy bars |
| C8-03 | gemini-4-argon-low | 0 | ✅ | 1 | 60 | A | A | A | A | 13 | 35 | 200 |  | all 6 tests passed |
| C8-03 | gemini-4-argon-low | 0 | ❌ | 0 | — | – | – | – | – | 15 | 25 | 106* | timeout, no code | test_outputs.py::test_compare_golden_vs_solution_runtime: The test failed in the call phas |
| C8-03 | gemini-4-argon-low | 0 | ✅ | 1 | 45 | A | A | A | B | 11 | 39 | 164 |  | all 6 tests passed |
| C8-03 | gemini-4-argon-medium | 0 | ❌ | 0 | — | – | – | – | – | 15 | 46 | 234* | timeout, no code | test_outputs.py::test_compare_golden_vs_solution_runtime: The test failed in the call phas |
| C8-03 | gemini-4-argon-medium | 0 | ❌ | 0 | — | – | – | – | – | 15 | 51 | 248* | timeout, no code | test_outputs.py::test_compare_golden_vs_solution_runtime: The test failed in the call phas |
| C8-03 | gemini-4-argon-medium | 0 | ✅ | 1 | 30 | A | A | B | B | 15 | 53 | 185 |  | all 6 tests passed |
