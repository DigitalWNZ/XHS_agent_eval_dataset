# C7 campaign report (runs ≥ 20261015_0845, < 20261015_0946)

11 trials, 1 setups, rubric v3.0. **D1** = pass rate on the source benchmark's hidden tests (cell tier snapped to 100/67/33/0). **D2** = code quality from the LLM judge (Claude Opus 5.5): Readability, Maintainability, Robustness + 1–2 case items, perfect 1 / accept 0.6 / bad 0, quality = 100 × mean. D1 and D2 are not combined. Trials with no code change cannot be judged (na) and are excluded from D2.

## Per case (passes/trials · D2 quality)

| Case | Former ID | Task | claude-opus-5-5 |
|---|---|---|---|
| C7-01 | C6-02 | DeepSWE v1.1 / drizzle-orm-window-function-builders | 1/1 · 100 |
| C7-02 | C7-04 | Terminal-Bench 2.0 / db-wal-recovery | 1/1 · 76 |
| C7-03 | C7-05 | SWE-bench Verified / django__django-15280 | 1/1 · 100 |
| C7-04 | C7-06 | SWE-bench Verified / django__django-12965 | 1/1 · 100 |
| C7-05 | C7-07 | SWE-bench Verified / django__django-15503 | 1/1 · 100 |
| C7-06 | C7-08 | SWE-bench Verified / django__django-14376 | 1/1 · 100 |
| C7-07 | C7-09 | SWE-bench Verified / django__django-11532 | 1/1 · 90 |
| C7-08 | C7-10 | SWE-bench Verified / psf__requests-6028 | 1/1 · 90 |
| C7-09 | C7-11 | DeepSWE v1.1 / kgateway-consistent-hash-policy | 1/1 · 92 |
| C7-10 | C7-13 | DeepSWE v1.1 / onedump-dump-encryption-pipeline | 1/1 · 90 |
| C7-11 | C7-14 | DeepSWE v1.1 / geo-shapeindex-serialization | 1/1 · 80 |

∅n = n trials ended with no code change (all were agent timeouts); ⚠n = invalid (validity audit).

## Per model

| Model | Trials | Passes | Pass rate | D1 (mean case tier) | D2 quality (graded trials) | No-code trials | Timeouts | Invalid |
|---|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 11 | 11 | 100% | 100 | 93 (n=11) | 0 | 0 | 0 |

## Run metrics per model (mean per trial)

Agent time = wall time of the agent run (capped by the budget). Tool calls are counted from the trajectory. Tokens = input + output as reported by the agent CLI; agy reports no usage when it hits its time budget, so for those trials the per-step usage in the saved trajectory is summed (marked * in the per-trial table; only available for runs after the partial-trajectory fix). Turns: Claude Code reports turns; agy always reports 1 per session, so use tool calls to compare.

| Model | Agent time (min) | Tool calls | Tokens (K) | Turns (Claude) | Cost USD (Claude, total) |
|---|---|---|---|---|---|
| claude-opus-5-5 | 4 | 13 | 509 | 14 | 5.33 |

## Run metrics per case (mean per trial: agent time min · tool calls · tokens K)

Same definitions as above, averaged over the trials of one case and model (— = no data, e.g. agy timeouts before the partial-trajectory fix).

| Case | Task | claude-opus-5-5 |
|---|---|---|
| C7-01 | DeepSWE v1.1 / drizzle-orm-window-function-bu | 6.6 · 18 · 675 |
| C7-02 | Terminal-Bench 2.0 / db-wal-recovery | 0.6 · 6 · 129 |
| C7-03 | SWE-bench Verified / django__django-15280 | 2.0 · 17 · 458 |
| C7-04 | SWE-bench Verified / django__django-12965 | 0.7 · 3 · 74 |
| C7-05 | SWE-bench Verified / django__django-15503 | 1.1 · 7 · 170 |
| C7-06 | SWE-bench Verified / django__django-14376 | 0.6 · 6 · 127 |
| C7-07 | SWE-bench Verified / django__django-11532 | 0.9 · 10 · 227 |
| C7-08 | SWE-bench Verified / psf__requests-6028 | 0.5 · 5 · 91 |
| C7-09 | DeepSWE v1.1 / kgateway-consistent-hash-polic | 12 · 32 · 1990 |
| C7-10 | DeepSWE v1.1 / onedump-dump-encryption-pipeli | 17 · 17 · 765 |
| C7-11 | DeepSWE v1.1 / geo-shapeindex-serialization | 5.7 · 18 · 901 |

## D2 item scores per model (mean over judged items, 0–100)

| Model | Readability | Maintainability | Robustness | Case-specific | Quality |
|---|---|---|---|---|---|
| claude-opus-5-5 | 93 | 85 | 93 | 97 | 93 |

## Quality among passing vs failing trials

| Model | D2 on passing trials | D2 on failing trials (with code) |
|---|---|---|
| claude-opus-5-5 | 93 | — |

## Validity findings

- results/c7_runs/C7-10_claude_claude-opus-5-5_20261015_090036/trial_0: test_tampering (provisional) — existing test lines changed/removed (4): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go

## Per trial

Item levels: P = perfect (100), A = accept (60), B = bad (0), – = not applicable. Read / Maint / Robust = the 3 common items; Case = the case-specific item(s) in order.

| Case | Model | Trial | Pass | Score | D2 | Read | Maint | Robust | Case | Time (min) | Tool calls | Tokens (K) | Notes | Verifier reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C7-01 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P | 7 | 18 | 675 |  | resolved (F2P 130/130, P2P 566/566) |
| C7-02 | claude-opus-5-5 | 0 | ✅ | 1 | 76 | A | A | A | P,P | 1 | 6 | 129 |  | all 7 tests passed |
| C7-03 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P | 2 | 17 | 458 |  | resolved (F2P 1/1, P2P 85/85) |
| C7-04 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P | 1 | 3 | 74 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-05 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P | 1 | 7 | 170 |  | resolved (F2P 2/2, P2P 78/78) |
| C7-06 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P,P | 1 | 6 | 127 |  | resolved (F2P 3/3, P2P 6/6) |
| C7-07 | claude-opus-5-5 | 0 | ✅ | 1 | 90 | P | A | P | P | 1 | 10 | 227 |  | resolved (F2P 1/1, P2P 148/148) |
| C7-08 | claude-opus-5-5 | 0 | ✅ | 1 | 90 | P | A | P | P | 0 | 5 | 91 |  | resolved (F2P 2/2, P2P 185/185) |
| C7-09 | claude-opus-5-5 | 0 | ✅ | 1 | 92 | P | P | A | P,P | 12 | 32 | 1990 |  | resolved (F2P 2/2, P2P 214/214) |
| C7-10 | claude-opus-5-5 | 0 | ✅ | 1 | 90 | P | P | P | A | 17 | 17 | 765 |  | resolved (F2P 82/82, P2P 6/6) |
| C7-11 | claude-opus-5-5 | 0 | ✅ | 1 | 80 | A | A | P | P | 6 | 18 | 901 |  | resolved (F2P 24/24, P2P 599/599) |
