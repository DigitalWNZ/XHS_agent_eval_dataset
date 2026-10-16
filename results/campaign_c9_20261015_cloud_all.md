# C9 campaign report (runs ≥ 20261015_183739, < 20261015_234455)

18 trials, 6 setups, rubric v3.0. **D1** = pass rate on the source benchmark's hidden tests (cell tier snapped to 100/67/33/0). **D2** = code quality from the LLM judge (Claude Opus 5.5): Readability, Maintainability, Robustness + 1–2 case items, perfect 1 / accept 0.6 / bad 0, quality = 100 × mean. D1 and D2 are not combined. Trials with no code change cannot be judged (na) and are excluded from D2.

## Per case (passes/trials · D2 quality)

| Case | Former ID | Task | claude-opus-5-5 | gemini-3.6-flash-high | gemini-3.8-flash-high | gemini-4-argon-high | gemini-4-argon-low | gemini-4-argon-medium |
|---|---|---|---|---|---|---|---|---|
| C9-01 | None | Customer-provided / 潮玩零售店工作台（单文件 HTML：商品、订单、售后） | 3/3 · 68 | 0/3 · 48 | 1/3 · 52 | 1/3 · 54 ∅1 | 3/3 · 63 | 0/3 · 48 ∅2 |

∅n = n trials ended with no code change (all were agent timeouts); ⚠n = invalid (validity audit).

## Per model

| Model | Trials | Passes | Pass rate | D1 (mean case tier) | D2 quality (graded trials) | No-code trials | Timeouts | Invalid |
|---|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 3 | 3 | 100% | 100 | 68 (n=3) | 0 | 0 | 0 |
| gemini-3.6-flash-high | 3 | 0 | 0% | 0 | 48 (n=3) | 0 | 0 | 0 |
| gemini-3.8-flash-high | 3 | 1 | 33% | 33 | 52 (n=3) | 0 | 0 | 0 |
| gemini-4-argon-high | 3 | 1 | 33% | 33 | 54 (n=2) | 1 | 1 | 0 |
| gemini-4-argon-low | 3 | 3 | 100% | 100 | 63 (n=3) | 0 | 0 | 0 |
| gemini-4-argon-medium | 3 | 0 | 0% | 0 | 48 (n=1) | 2 | 1 | 0 |

## Run metrics per model (mean per trial)

Agent time = wall time of the agent run (capped by the budget). Tool calls are counted from the trajectory. Tokens = input + output as reported by the agent CLI; agy reports no usage when it hits its time budget, so for those trials the per-step usage in the saved trajectory is summed (marked * in the per-trial table; only available for runs after the partial-trajectory fix). Turns: Claude Code reports turns; agy always reports 1 per session, so use tool calls to compare.

| Model | Agent time (min) | Tool calls | Tokens (K) | Turns (Claude) | Cost USD (Claude, total) |
|---|---|---|---|---|---|
| claude-opus-5-5 | 11 | 15 | 1270 | 16 | 6.92 |
| gemini-3.6-flash-high | 11 | 19 | 341 | — | — |
| gemini-3.8-flash-high | 12 | 25 | 322 | — | — |
| gemini-4-argon-high | 42 | 19 | 213 | — | — |
| gemini-4-argon-low | 10 | 6 | 141 | — | — |
| gemini-4-argon-medium | 47 | 9 | 151 | — | — |

## Run metrics per case (mean per trial: agent time min · tool calls · tokens K)

Same definitions as above, averaged over the trials of one case and model (— = no data, e.g. agy timeouts before the partial-trajectory fix).

| Case | Task | claude-opus-5-5 | gemini-3.6-flash-high | gemini-3.8-flash-high | gemini-4-argon-high | gemini-4-argon-low | gemini-4-argon-medium |
|---|---|---|---|---|---|---|---|
| C9-01 | Customer-provided / 潮玩零售店工作台（单文件 HTML：商品、订单、售 | 11 · 15 · 1270 | 11 · 19 · 341 | 12 · 25 · 322 | 42 · 19 · 213 | 9.8 · 6 · 141 | 47 · 9 · 151 |

## D2 item scores per model (mean over judged items, 0–100)

| Model | Readability | Maintainability | Robustness | Case-specific | Quality |
|---|---|---|---|---|---|
| claude-opus-5-5 | 60 | 40 | 40 | 100 | 68 |
| gemini-3.6-flash-high | 60 | 60 | 60 | 30 | 48 |
| gemini-3.8-flash-high | 60 | 60 | 60 | 40 | 52 |
| gemini-4-argon-high | 60 | 30 | 60 | 60 | 54 |
| gemini-4-argon-low | 73 | 60 | 60 | 60 | 63 |
| gemini-4-argon-medium | 60 | 0 | 60 | 60 | 48 |

## Quality among passing vs failing trials

| Model | D2 on passing trials | D2 on failing trials (with code) |
|---|---|---|
| claude-opus-5-5 | 68 | — |
| gemini-3.6-flash-high | — | 48 |
| gemini-3.8-flash-high | 48 | 54 |
| gemini-4-argon-high | 48 | 60 |
| gemini-4-argon-low | 63 | — |
| gemini-4-argon-medium | — | 48 |

## Validity findings

none

## Per trial

Item levels: P = perfect (100), A = accept (60), B = bad (0), – = not applicable. Read / Maint / Robust = the 3 common items; Case = the case-specific item(s) in order.

| Case | Model | Trial | Pass | Score | D2 | Read | Maint | Robust | Case | Time (min) | Tool calls | Tokens (K) | Notes | Verifier reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C9-01 | claude-opus-5-5 | 0 | ✅ | 1 | 52 | A | B | B | P,P | 11 | 13 | 1028 |  | all 25 tests passed |
| C9-01 | claude-opus-5-5 | 0 | ✅ | 1 | 76 | A | A | A | P,P | 11 | 15 | 1117 |  | all 25 tests passed |
| C9-01 | claude-opus-5-5 | 0 | ✅ | 1 | 76 | A | A | A | P,P | 12 | 18 | 1664 |  | all 25 tests passed |
| C9-01 | gemini-3.6-flash-high | 0 | ❌ | 0 | 48 | A | A | A | B,A | 12 | 19 | 295 |  | test_outputs.py::test_single_self_contained_file: failed |
| C9-01 | gemini-3.6-flash-high | 0 | ❌ | 0 | 48 | A | A | A | B,A | 13 | 21 | 463 |  | test_outputs.py::test_seed_products_and_orders: The test failed in the call phase due to a |
| C9-01 | gemini-3.6-flash-high | 0 | ❌ | 0 | 48 | A | A | A | B,A | 9 | 16 | 265 |  | test_outputs.py::test_seed_products_and_orders: The test failed in the call phase due to a |
| C9-01 | gemini-3.8-flash-high | 0 | ❌ | 0 | 60 | A | A | A | A,A | 10 | 20 | 264 |  | test_outputs.py::test_seed_products_and_orders: The test failed in the call phase due to a |
| C9-01 | gemini-3.8-flash-high | 0 | ✅ | 1 | 48 | A | A | A | B,A | 19 | 27 | 416 |  | all 25 tests passed |
| C9-01 | gemini-3.8-flash-high | 0 | ❌ | 0 | 48 | A | A | A | B,A | 8 | 29 | 287 |  | test_outputs.py::test_cart_rejects_illegal_quantity: The test failed in the call phase due |
| C9-01 | gemini-4-argon-high | 0 | ✅ | 1 | 48 | A | B | A | A,A | 44 | 21 | 292 |  | all 25 tests passed |
| C9-01 | gemini-4-argon-high | 0 | ❌ | 0 | — | – | – | – | –,– | 60 | 2 | 32* | timeout, no code | test_outputs.py::test_single_self_contained_file: failed |
| C9-01 | gemini-4-argon-high | 0 | ❌ | 0 | 60 | A | A | A | A,A | 21 | 34 | 314 |  | test_outputs.py::test_seed_products_and_orders: The test failed in the call phase due to a |
| C9-01 | gemini-4-argon-low | 0 | ✅ | 1 | 60 | A | A | A | A,A | 11 | 7 | 206 |  | all 25 tests passed |
| C9-01 | gemini-4-argon-low | 0 | ✅ | 1 | 60 | A | A | A | A,A | 9 | 6 | 88 |  | all 25 tests passed |
| C9-01 | gemini-4-argon-low | 0 | ✅ | 1 | 68 | P | A | A | A,A | 9 | 6 | 130 |  | all 25 tests passed |
| C9-01 | gemini-4-argon-medium | 0 | ❌ | 0 | — | – | – | – | –,– | 60 | 2 | 25* | timeout, no code | test_outputs.py::test_single_self_contained_file: failed |
| C9-01 | gemini-4-argon-medium | 0 | ❌ | 0 | 48 | A | B | A | A,A | 25 | 24 | 401 |  | test_outputs.py::test_seed_products_and_orders: The test failed in the call phase due to a |
| C9-01 | gemini-4-argon-medium | 0 | ❌ | 0 | — | – | – | – | –,– | 57 | 2 | 27 | no code | test_outputs.py::test_single_self_contained_file: failed |
