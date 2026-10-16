# C7 campaign report (runs ≥ 20261015_234242, < 20261015_234454)

66 trials, 2 setups, rubric v3.0. **D1** = pass rate on the source benchmark's hidden tests (cell tier snapped to 100/67/33/0). **D2** = code quality from the LLM judge (Claude Opus 5.5): Readability, Maintainability, Robustness + 1–2 case items, perfect 1 / accept 0.6 / bad 0, quality = 100 × mean. D1 and D2 are not combined. Trials with no code change cannot be judged (na) and are excluded from D2.

## Per case (passes/trials · D2 quality)

| Case | Former ID | Task | gemini-4-argon-low | gemini-4-argon-medium |
|---|---|---|---|---|
| C7-01 | C6-02 | DeepSWE v1.1 / drizzle-orm-window-function-builders | 3/3 · 87 | 3/3 · 83 |
| C7-02 | C7-04 | Terminal-Bench 2.0 / db-wal-recovery | 3/3 · 63 | 3/3 · 73 |
| C7-03 | C7-05 | SWE-bench Verified / django__django-15280 | 3/3 · 73 | 3/3 · 82 |
| C7-04 | C7-06 | SWE-bench Verified / django__django-12965 | 3/3 · 87 | 3/3 · 100 |
| C7-05 | C7-07 | SWE-bench Verified / django__django-15503 | 3/3 · 97 | 3/3 · 100 |
| C7-06 | C7-08 | SWE-bench Verified / django__django-14376 | 3/3 · 100 | 3/3 · 100 |
| C7-07 | C7-09 | SWE-bench Verified / django__django-11532 | 3/3 · 97 | 2/3 · 90 ∅1 |
| C7-08 | C7-10 | SWE-bench Verified / psf__requests-6028 | 3/3 · 100 | 3/3 · 100 |
| C7-09 | C7-11 | DeepSWE v1.1 / kgateway-consistent-hash-policy | 3/3 · 87 | 3/3 · 89 |
| C7-10 | C7-13 | DeepSWE v1.1 / onedump-dump-encryption-pipeline | 3/3 · 67 | 3/3 · 70 |
| C7-11 | C7-14 | DeepSWE v1.1 / geo-shapeindex-serialization | 3/3 · 60 | 3/3 · 57 |

∅n = n trials ended with no code change (all were agent timeouts); ⚠n = invalid (validity audit).

## Per model

| Model | Trials | Passes | Pass rate | D1 (mean case tier) | D2 quality (graded trials) | No-code trials | Timeouts | Invalid |
|---|---|---|---|---|---|---|---|---|
| gemini-4-argon-low | 33 | 33 | 100% | 100 | 83 (n=33) | 0 | 1 | 0 |
| gemini-4-argon-medium | 33 | 32 | 97% | 97 | 86 (n=32) | 1 | 2 | 0 |

## Run metrics per model (mean per trial)

Agent time = wall time of the agent run (capped by the budget). Tool calls are counted from the trajectory. Tokens = input + output as reported by the agent CLI; agy reports no usage when it hits its time budget, so for those trials the per-step usage in the saved trajectory is summed (marked * in the per-trial table; only available for runs after the partial-trajectory fix). Turns: Claude Code reports turns; agy always reports 1 per session, so use tool calls to compare.

| Model | Agent time (min) | Tool calls | Tokens (K) | Turns (Claude) | Cost USD (Claude, total) |
|---|---|---|---|---|---|
| gemini-4-argon-low | 15 | 59 | 398 | — | — |
| gemini-4-argon-medium | 22 | 67 | 503 | — | — |

## Run metrics per case (mean per trial: agent time min · tool calls · tokens K)

Same definitions as above, averaged over the trials of one case and model (— = no data, e.g. agy timeouts before the partial-trajectory fix).

| Case | Task | gemini-4-argon-low | gemini-4-argon-medium |
|---|---|---|---|
| C7-01 | DeepSWE v1.1 / drizzle-orm-window-function-bu | 25 · 113 · 697 | 42 · 121 · 1128 |
| C7-02 | Terminal-Bench 2.0 / db-wal-recovery | 1.3 · 8 · 34 | 3.6 · 9 · 54 |
| C7-03 | SWE-bench Verified / django__django-15280 | 21 · 57 · 599 | 22 · 54 · 480 |
| C7-04 | SWE-bench Verified / django__django-12965 | 8.9 · 32 · 119 | 10.0 · 37 · 151 |
| C7-05 | SWE-bench Verified / django__django-15503 | 14 · 31 · 148 | 15 · 31 · 313 |
| C7-06 | SWE-bench Verified / django__django-14376 | 2.2 · 20 · 58 | 6.7 · 24 · 91 |
| C7-07 | SWE-bench Verified / django__django-11532 | 11 · 53 · 262 | 21 · 47 · 420 |
| C7-08 | SWE-bench Verified / psf__requests-6028 | 6.0 · 25 · 96 | 8.9 · 26 · 133 |
| C7-09 | DeepSWE v1.1 / kgateway-consistent-hash-polic | 33 · 168 · 1304 | 66 · 258 · 1729 |
| C7-10 | DeepSWE v1.1 / onedump-dump-encryption-pipeli | 13 · 38 · 160 | 21 · 37 · 353 |
| C7-11 | DeepSWE v1.1 / geo-shapeindex-serialization | 34 · 101 · 909 | 29 · 91 · 677 |

## D2 item scores per model (mean over judged items, 0–100)

| Model | Readability | Maintainability | Robustness | Case-specific | Quality |
|---|---|---|---|---|---|
| gemini-4-argon-low | 87 | 75 | 86 | 85 | 83 |
| gemini-4-argon-medium | 86 | 76 | 90 | 90 | 86 |

## Quality among passing vs failing trials

| Model | D2 on passing trials | D2 on failing trials (with code) |
|---|---|---|
| gemini-4-argon-low | 83 | — |
| gemini-4-argon-medium | 86 | — |

## Validity findings

- results/c7_runs/C7-10_agy_gemini-4-argon-low_20261015_234315/trial_0: test_tampering (provisional) — existing test lines changed/removed (4): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go
- results/c7_runs/C7-10_agy_gemini-4-argon-low_20261015_234316/trial_0: test_tampering (provisional) — existing test lines changed/removed (4): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go
- results/c7_runs/C7-10_agy_gemini-4-argon-low_20261015_234317/trial_0: test_tampering (provisional) — existing test lines changed/removed (4): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go
- results/c7_runs/C7-10_agy_gemini-4-argon-medium_20261015_234312/trial_0: test_tampering (provisional) — existing test lines changed/removed (4): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go
- results/c7_runs/C7-10_agy_gemini-4-argon-medium_20261015_234313/trial_0: test_tampering (provisional) — existing test lines changed/removed (4): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go
- results/c7_runs/C7-10_agy_gemini-4-argon-medium_20261015_234314/trial_0: test_tampering (provisional) — existing test lines changed/removed (4): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go
- results/c7_runs/C7-11_agy_gemini-4-argon-low_20261015_234321/trial_0: test_tampering (provisional) — existing test lines changed/removed (2): s2/shapeutil_edge_iterator_test.go
- results/c7_runs/C7-11_agy_gemini-4-argon-low_20261015_234322/trial_0: test_tampering (provisional) — existing test lines changed/removed (2): s2/shapeutil_edge_iterator_test.go
- results/c7_runs/C7-11_agy_gemini-4-argon-low_20261015_234323/trial_0: test_tampering (provisional) — existing test lines changed/removed (2): s2/shapeutil_edge_iterator_test.go
- results/c7_runs/C7-11_agy_gemini-4-argon-medium_20261015_234319/trial_0: test_tampering (provisional) — existing test lines changed/removed (2): s2/shapeutil_edge_iterator_test.go

## Per trial

Item levels: P = perfect (100), A = accept (60), B = bad (0), – = not applicable. Read / Maint / Robust = the 3 common items; Case = the case-specific item(s) in order.

| Case | Model | Trial | Pass | Score | D2 | Read | Maint | Robust | Case | Time (min) | Tool calls | Tokens (K) | Notes | Verifier reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C7-01 | gemini-4-argon-low | 0 | ✅ | 1 | 90 | P | A | P | P | 17 | 115 | 343 |  | resolved (F2P 130/130, P2P 566/566) |
| C7-01 | gemini-4-argon-low | 0 | ✅ | 1 | 80 | P | A | P | A | 39 | 119 | 1195 |  | resolved (F2P 130/130, P2P 566/566) |
| C7-01 | gemini-4-argon-low | 0 | ✅ | 1 | 90 | P | A | P | P | 18 | 106 | 553 |  | resolved (F2P 130/130, P2P 566/566) |
| C7-01 | gemini-4-argon-medium | 0 | ✅ | 1 | 80 | A | A | P | P | 42 | 111 | 1729 |  | resolved (F2P 130/130, P2P 566/566) |
| C7-01 | gemini-4-argon-medium | 0 | ✅ | 1 | 90 | P | A | P | P | 37 | 122 | 596 |  | resolved (F2P 130/130, P2P 566/566) |
| C7-01 | gemini-4-argon-medium | 0 | ✅ | 1 | 80 | A | A | P | P | 46 | 131 | 1057 |  | resolved (F2P 130/130, P2P 566/566) |
| C7-02 | gemini-4-argon-low | 0 | ✅ | 1 | 56 | A | A | A | P,B | 1 | 6 | 28 |  | all 7 tests passed |
| C7-02 | gemini-4-argon-low | 0 | ✅ | 1 | 76 | A | A | A | P,P | 1 | 8 | 32 |  | all 7 tests passed |
| C7-02 | gemini-4-argon-low | 0 | ✅ | 1 | 56 | A | A | A | P,B | 2 | 11 | 41 |  | all 7 tests passed |
| C7-02 | gemini-4-argon-medium | 0 | ✅ | 1 | 76 | A | A | A | P,P | 3 | 8 | 35 |  | all 7 tests passed |
| C7-02 | gemini-4-argon-medium | 0 | ✅ | 1 | 68 | A | A | A | P,A | 5 | 11 | 82 |  | all 7 tests passed |
| C7-02 | gemini-4-argon-medium | 0 | ✅ | 1 | 76 | A | A | A | P,P | 2 | 7 | 43 |  | all 7 tests passed |
| C7-03 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P | 19 | 42 | 452 |  | resolved (F2P 1/1, P2P 85/85) |
| C7-03 | gemini-4-argon-low | 0 | ✅ | 1 | 90 | P | P | P | A | 30 | 79 | 746* | timeout | resolved (F2P 1/1, P2P 85/85) |
| C7-03 | gemini-4-argon-low | 0 | ✅ | 1 | 30 | A | A | B | B | 15 | 50 | 598 |  | resolved (F2P 1/1, P2P 85/85) |
| C7-03 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P | 23 | 47 | 514 |  | resolved (F2P 1/1, P2P 85/85) |
| C7-03 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P | 30 | 39 | 464* | timeout | resolved (F2P 1/1, P2P 85/85) |
| C7-03 | gemini-4-argon-medium | 0 | ✅ | 1 | 45 | A | A | A | B | 14 | 76 | 460 |  | resolved (F2P 1/1, P2P 85/85) |
| C7-04 | gemini-4-argon-low | 0 | ✅ | 1 | 60 | A | A | A | A | 15 | 42 | 190 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-04 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P | 3 | 28 | 80 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-04 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P | 9 | 26 | 86 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-04 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P | 8 | 36 | 123 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-04 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P | 12 | 44 | 161 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-04 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P | 10 | 32 | 168 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-05 | gemini-4-argon-low | 0 | ✅ | 1 | 90 | P | P | A | P | 11 | 35 | 143 |  | resolved (F2P 2/2, P2P 78/78) |
| C7-05 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P | 26 | 32 | 190 |  | resolved (F2P 2/2, P2P 78/78) |
| C7-05 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P | 6 | 27 | 110 |  | resolved (F2P 2/2, P2P 78/78) |
| C7-05 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P | 12 | 31 | 159 |  | resolved (F2P 2/2, P2P 78/78) |
| C7-05 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P | 21 | 32 | 335 |  | resolved (F2P 2/2, P2P 78/78) |
| C7-05 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P | 12 | 31 | 445 |  | resolved (F2P 2/2, P2P 78/78) |
| C7-06 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P,P | 3 | 18 | 59 |  | resolved (F2P 3/3, P2P 6/6) |
| C7-06 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P,P | 2 | 19 | 61 |  | resolved (F2P 3/3, P2P 6/6) |
| C7-06 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P,P | 2 | 22 | 53 |  | resolved (F2P 3/3, P2P 6/6) |
| C7-06 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P,P | 7 | 26 | 96 |  | resolved (F2P 3/3, P2P 6/6) |
| C7-06 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P,P | 5 | 21 | 106 |  | resolved (F2P 3/3, P2P 6/6) |
| C7-06 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P,P | 7 | 26 | 70 |  | resolved (F2P 3/3, P2P 6/6) |
| C7-07 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P | 11 | 52 | 295 |  | resolved (F2P 1/1, P2P 148/148) |
| C7-07 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P | 10 | 47 | 134 |  | resolved (F2P 1/1, P2P 148/148) |
| C7-07 | gemini-4-argon-low | 0 | ✅ | 1 | 90 | P | A | P | P | 13 | 60 | 357 |  | resolved (F2P 1/1, P2P 148/148) |
| C7-07 | gemini-4-argon-medium | 0 | ✅ | 1 | 90 | P | P | P | A | 10 | 51 | 514 |  | resolved (F2P 1/1, P2P 148/148) |
| C7-07 | gemini-4-argon-medium | 0 | ✅ | 1 | 90 | P | A | P | P | 23 | 58 | 522 |  | resolved (F2P 1/1, P2P 148/148) |
| C7-07 | gemini-4-argon-medium | 0 | ❌ | 0 | — | – | – | – | – | 30 | 31 | 225* | timeout, no code | not resolved (F2P 0/1, P2P 130/148); first failure: test_non_ascii_dns_non_unicode_email ( |
| C7-08 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P | 4 | 24 | 81 |  | resolved (F2P 2/2, P2P 185/185) |
| C7-08 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P | 8 | 24 | 78 |  | resolved (F2P 2/2, P2P 185/185) |
| C7-08 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P | 6 | 27 | 130 |  | resolved (F2P 2/2, P2P 185/185) |
| C7-08 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P | 12 | 35 | 196 |  | resolved (F2P 2/2, P2P 185/185) |
| C7-08 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P | 3 | 19 | 69 |  | resolved (F2P 2/2, P2P 185/185) |
| C7-08 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P | 11 | 24 | 135 |  | resolved (F2P 2/2, P2P 185/185) |
| C7-09 | gemini-4-argon-low | 0 | ✅ | 1 | 92 | P | A | P | P,P | 39 | 188 | 1522 |  | resolved (F2P 2/2, P2P 214/214) |
| C7-09 | gemini-4-argon-low | 0 | ✅ | 1 | 84 | P | A | A | P,P | 30 | 143 | 1639 |  | resolved (F2P 2/2, P2P 214/214) |
| C7-09 | gemini-4-argon-low | 0 | ✅ | 1 | 84 | P | A | A | P,P | 31 | 173 | 750 |  | resolved (F2P 2/2, P2P 214/214) |
| C7-09 | gemini-4-argon-medium | 0 | ✅ | 1 | 84 | P | A | P | A,P | 78 | 264 | 2200 |  | resolved (F2P 2/2, P2P 214/214) |
| C7-09 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P,P | 60 | 243 | 1783 |  | resolved (F2P 2/2, P2P 214/214) |
| C7-09 | gemini-4-argon-medium | 0 | ✅ | 1 | 84 | P | A | A | P,P | 61 | 268 | 1203 |  | resolved (F2P 2/2, P2P 214/214) |
| C7-10 | gemini-4-argon-low | 0 | ✅ | 1 | 70 | A | A | P | A | 12 | 41 | 134 |  | resolved (F2P 82/82, P2P 6/6) |
| C7-10 | gemini-4-argon-low | 0 | ✅ | 1 | 60 | A | A | A | A | 8 | 35 | 142 |  | resolved (F2P 82/82, P2P 6/6) |
| C7-10 | gemini-4-argon-low | 0 | ✅ | 1 | 70 | A | A | P | A | 18 | 39 | 203 |  | resolved (F2P 82/82, P2P 6/6) |
| C7-10 | gemini-4-argon-medium | 0 | ✅ | 1 | 70 | A | A | P | A | 13 | 34 | 177 |  | resolved (F2P 82/82, P2P 6/6) |
| C7-10 | gemini-4-argon-medium | 0 | ✅ | 1 | 80 | P | A | P | A | 17 | 44 | 443 |  | resolved (F2P 82/82, P2P 6/6) |
| C7-10 | gemini-4-argon-medium | 0 | ✅ | 1 | 60 | A | A | A | A | 33 | 33 | 439 |  | resolved (F2P 82/82, P2P 6/6) |
| C7-11 | gemini-4-argon-low | 0 | ✅ | 1 | 80 | A | A | P | P | 33 | 117 | 726 |  | resolved (F2P 24/24, P2P 599/599) |
| C7-11 | gemini-4-argon-low | 0 | ✅ | 1 | 45 | A | B | A | A | 42 | 96 | 1337 |  | resolved (F2P 24/24, P2P 599/599) |
| C7-11 | gemini-4-argon-low | 0 | ✅ | 1 | 55 | A | B | P | A | 28 | 91 | 665 |  | resolved (F2P 24/24, P2P 599/599) |
| C7-11 | gemini-4-argon-medium | 0 | ✅ | 1 | 45 | A | B | A | A | 29 | 75 | 681 |  | resolved (F2P 24/24, P2P 599/599) |
| C7-11 | gemini-4-argon-medium | 0 | ✅ | 1 | 80 | A | A | P | P | 17 | 97 | 406 |  | resolved (F2P 24/24, P2P 599/599) |
| C7-11 | gemini-4-argon-medium | 0 | ✅ | 1 | 45 | A | B | A | A | 39 | 102 | 944 |  | resolved (F2P 24/24, P2P 599/599) |
