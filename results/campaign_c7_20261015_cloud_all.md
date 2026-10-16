# C7 campaign report (runs ≥ 20261015_183739, < 20261015_234455)

198 trials, 6 setups, rubric v3.0. **D1** = pass rate on the source benchmark's hidden tests (cell tier snapped to 100/67/33/0). **D2** = code quality from the LLM judge (Claude Opus 5.5): Readability, Maintainability, Robustness + 1–2 case items, perfect 1 / accept 0.6 / bad 0, quality = 100 × mean. D1 and D2 are not combined. Trials with no code change cannot be judged (na) and are excluded from D2.

## Per case (passes/trials · D2 quality)

| Case | Former ID | Task | claude-opus-5-5 | gemini-3.6-flash-high | gemini-3.8-flash-high | gemini-4-argon-high | gemini-4-argon-low | gemini-4-argon-medium |
|---|---|---|---|---|---|---|---|---|
| C7-01 | C6-02 | DeepSWE v1.1 / drizzle-orm-window-function-builders | 0/3 · 90 | 3/3 · 72 | 3/3 · 87 | 3/3 · 80 | 3/3 · 87 | 3/3 · 83 |
| C7-02 | C7-04 | Terminal-Bench 2.0 / db-wal-recovery | 3/3 · 55 | 3/3 · 53 | 3/3 · 69 | 3/3 · 76 | 3/3 · 63 | 3/3 · 73 |
| C7-03 | C7-05 | SWE-bench Verified / django__django-15280 | 3/3 · 100 | 3/3 · 53 | 3/3 · 55 | 3/3 · 100 | 3/3 · 73 | 3/3 · 82 |
| C7-04 | C7-06 | SWE-bench Verified / django__django-12965 | 3/3 · 100 | 3/3 · 97 | 3/3 · 90 | 3/3 · 100 | 3/3 · 87 | 3/3 · 100 |
| C7-05 | C7-07 | SWE-bench Verified / django__django-15503 | 3/3 · 100 | 3/3 · 73 | 3/3 · 77 | 3/3 · 100 | 3/3 · 97 | 3/3 · 100 |
| C7-06 | C7-08 | SWE-bench Verified / django__django-14376 | 3/3 · 100 | 3/3 · 97 | 2/3 · 97 | 3/3 · 100 | 3/3 · 100 | 3/3 · 100 |
| C7-07 | C7-09 | SWE-bench Verified / django__django-11532 | 3/3 · 90 | 3/3 · 77 | 3/3 · 60 | 2/3 · 90 ∅1 | 3/3 · 97 | 2/3 · 90 ∅1 |
| C7-08 | C7-10 | SWE-bench Verified / psf__requests-6028 | 3/3 · 100 | 2/3 · 53 | 3/3 · 75 | 3/3 · 93 | 3/3 · 100 | 3/3 · 100 |
| C7-09 | C7-11 | DeepSWE v1.1 / kgateway-consistent-hash-policy | 3/3 · 100 | 1/3 · 65 | 3/3 · 87 | 3/3 · 92 | 3/3 · 87 | 3/3 · 89 |
| C7-10 | C7-13 | DeepSWE v1.1 / onedump-dump-encryption-pipeline | 2/3 · 80 | 2/3 · 55 | 2/3 · 63 | 3/3 · 73 | 3/3 · 67 | 3/3 · 70 |
| C7-11 | C7-14 | DeepSWE v1.1 / geo-shapeindex-serialization | 3/3 · 75 | 2/3 · 50 | 3/3 · 68 | 3/3 · 57 | 3/3 · 60 | 3/3 · 57 |

∅n = n trials ended with no code change (all were agent timeouts); ⚠n = invalid (validity audit).

## Per model

| Model | Trials | Passes | Pass rate | D1 (mean case tier) | D2 quality (graded trials) | No-code trials | Timeouts | Invalid |
|---|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 33 | 29 | 88% | 88 | 90 (n=33) | 0 | 0 | 0 |
| gemini-3.6-flash-high | 33 | 28 | 85% | 85 | 68 (n=33) | 0 | 0 | 0 |
| gemini-3.8-flash-high | 33 | 31 | 94% | 94 | 75 (n=33) | 0 | 2 | 0 |
| gemini-4-argon-high | 33 | 32 | 97% | 97 | 87 (n=32) | 1 | 1 | 0 |
| gemini-4-argon-low | 33 | 33 | 100% | 100 | 83 (n=33) | 0 | 1 | 0 |
| gemini-4-argon-medium | 33 | 32 | 97% | 97 | 86 (n=32) | 1 | 2 | 0 |

## Run metrics per model (mean per trial)

Agent time = wall time of the agent run (capped by the budget). Tool calls are counted from the trajectory. Tokens = input + output as reported by the agent CLI; agy reports no usage when it hits its time budget, so for those trials the per-step usage in the saved trajectory is summed (marked * in the per-trial table; only available for runs after the partial-trajectory fix). Turns: Claude Code reports turns; agy always reports 1 per session, so use tool calls to compare.

| Model | Agent time (min) | Tool calls | Tokens (K) | Turns (Claude) | Cost USD (Claude, total) |
|---|---|---|---|---|---|
| claude-opus-5-5 | 3 | 14 | 666 | 14 | 18.55 |
| gemini-3.6-flash-high | 11 | 73 | 623 | — | — |
| gemini-3.8-flash-high | 21 | 113 | 946 | — | — |
| gemini-4-argon-high | 19 | 72 | 434 | — | — |
| gemini-4-argon-low | 15 | 59 | 398 | — | — |
| gemini-4-argon-medium | 22 | 67 | 503 | — | — |

## Run metrics per case (mean per trial: agent time min · tool calls · tokens K)

Same definitions as above, averaged over the trials of one case and model (— = no data, e.g. agy timeouts before the partial-trajectory fix).

| Case | Task | claude-opus-5-5 | gemini-3.6-flash-high | gemini-3.8-flash-high | gemini-4-argon-high | gemini-4-argon-low | gemini-4-argon-medium |
|---|---|---|---|---|---|---|---|
| C7-01 | DeepSWE v1.1 / drizzle-orm-window-function-bu | 3.8 · 16 · 600 | 19 · 144 · 1242 | 36 · 209 · 1901 | 28 · 126 · 662 | 25 · 113 · 697 | 42 · 121 · 1128 |
| C7-02 | Terminal-Bench 2.0 / db-wal-recovery | 0.4 · 4 · 96 | 2.3 · 40 · 206 | 6.0 · 44 · 242 | 3.7 · 14 · 64 | 1.3 · 8 · 34 | 3.6 · 9 · 54 |
| C7-03 | SWE-bench Verified / django__django-15280 | 2.7 · 17 · 468 | 16 · 88 · 744 | 24 · 124 · 807 | 16 · 43 · 300 | 21 · 57 · 599 | 22 · 54 · 480 |
| C7-04 | SWE-bench Verified / django__django-12965 | 0.5 · 6 · 137 | 11 · 56 · 463 | 13 · 83 · 471 | 9.5 · 42 · 218 | 8.9 · 32 · 119 | 10.0 · 37 · 151 |
| C7-05 | SWE-bench Verified / django__django-15503 | 0.9 · 9 · 230 | 12 · 46 · 527 | 20 · 86 · 852 | 14 · 31 · 269 | 14 · 31 · 148 | 15 · 31 · 313 |
| C7-06 | SWE-bench Verified / django__django-14376 | 0.4 · 7 · 141 | 2.7 · 39 · 259 | 14 · 74 · 678 | 4.3 · 41 · 151 | 2.2 · 20 · 58 | 6.7 · 24 · 91 |
| C7-07 | SWE-bench Verified / django__django-11532 | 0.6 · 7 · 169 | 3.9 · 45 · 333 | 18 · 78 · 654 | 21 · 60 · 307 | 11 · 53 · 262 | 21 · 47 · 420 |
| C7-08 | SWE-bench Verified / psf__requests-6028 | 0.4 · 6 · 103 | 11 · 91 · 710 | 17 · 133 · 782 | 6.1 · 41 · 178 | 6.0 · 25 · 96 | 8.9 · 26 · 133 |
| C7-09 | DeepSWE v1.1 / kgateway-consistent-hash-polic | 11 · 36 · 2976 | 19 · 135 · 1154 | 28 · 159 · 1266 | 48 · 226 · 1316 | 33 · 168 · 1304 | 66 · 258 · 1729 |
| C7-10 | DeepSWE v1.1 / onedump-dump-encryption-pipeli | 3.5 · 14 · 611 | 12 · 55 · 566 | 15 · 82 · 937 | 20 · 38 · 217 | 13 · 38 · 160 | 21 · 37 · 353 |
| C7-11 | DeepSWE v1.1 / geo-shapeindex-serialization | 13 · 33 · 1793 | 11 · 61 · 651 | 40 · 170 · 1810 | 39 · 134 · 1091 | 34 · 101 · 909 | 29 · 91 · 677 |

## D2 item scores per model (mean over judged items, 0–100)

| Model | Readability | Maintainability | Robustness | Case-specific | Quality |
|---|---|---|---|---|---|
| claude-opus-5-5 | 91 | 83 | 90 | 94 | 90 |
| gemini-3.6-flash-high | 75 | 53 | 76 | 69 | 68 |
| gemini-3.8-flash-high | 82 | 64 | 77 | 80 | 75 |
| gemini-4-argon-high | 88 | 78 | 88 | 95 | 87 |
| gemini-4-argon-low | 87 | 75 | 86 | 85 | 83 |
| gemini-4-argon-medium | 86 | 76 | 90 | 90 | 86 |

## Quality among passing vs failing trials

| Model | D2 on passing trials | D2 on failing trials (with code) |
|---|---|---|
| claude-opus-5-5 | 90 | 88 |
| gemini-3.6-flash-high | 71 | 49 |
| gemini-3.8-flash-high | 75 | 76 |
| gemini-4-argon-high | 87 | — |
| gemini-4-argon-low | 83 | — |
| gemini-4-argon-medium | 86 | — |

## Validity findings

- results/c7_runs/C7-03_agy_gemini-3.6-flash-high_20261015_183916/trial_0: test_tampering (provisional) — existing test lines changed/removed (1): tests/defer_regress/tests.py
- results/c7_runs/C7-06_agy_gemini-3.6-flash-high_20261015_183942/trial_0: test_tampering (provisional) — skip/xfail marker added to existing tests in tests/backends/mysql/tests.py: "@unittest.skipUnless(connection.vendor == 'mysql', 'MySQL tests')"
- results/c7_runs/C7-08_agy_gemini-3.6-flash-high_20261015_184000/trial_0: test_tampering (provisional) — existing test lines changed/removed (1): tests/test_utils.py
- results/c7_runs/C7-10_agy_gemini-3.6-flash-high_20261015_183830/trial_0: test_tampering (provisional) — existing test lines changed/removed (4): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go
- results/c7_runs/C7-10_agy_gemini-3.6-flash-high_20261015_183831/trial_0: test_tampering (provisional) — existing test lines changed/removed (4): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go; existing test lines changed/removed (2): storage/dropbox/dropbo
- results/c7_runs/C7-10_agy_gemini-3.6-flash-high_20261015_183832/trial_0: test_tampering (provisional) — existing test lines changed/removed (4): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go
- results/c7_runs/C7-10_agy_gemini-3.8-flash-high_20261015_183824/trial_0: test_tampering (provisional) — existing test lines changed/removed (5): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go
- results/c7_runs/C7-10_agy_gemini-3.8-flash-high_20261015_183825/trial_0: test_tampering (provisional) — existing test lines changed/removed (4): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go
- results/c7_runs/C7-10_agy_gemini-3.8-flash-high_20261015_183826/trial_0: test_tampering (provisional) — existing test lines changed/removed (4): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go
- results/c7_runs/C7-10_agy_gemini-4-argon-high_20261015_183827/trial_0: test_tampering (provisional) — existing test lines changed/removed (4): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go
- results/c7_runs/C7-10_agy_gemini-4-argon-high_20261015_183828/trial_0: test_tampering (provisional) — existing test lines changed/removed (4): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go
- results/c7_runs/C7-10_agy_gemini-4-argon-high_20261015_183829/trial_0: test_tampering (provisional) — existing test lines changed/removed (4): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go
- results/c7_runs/C7-10_agy_gemini-4-argon-low_20261015_234315/trial_0: test_tampering (provisional) — existing test lines changed/removed (4): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go
- results/c7_runs/C7-10_agy_gemini-4-argon-low_20261015_234316/trial_0: test_tampering (provisional) — existing test lines changed/removed (4): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go
- results/c7_runs/C7-10_agy_gemini-4-argon-low_20261015_234317/trial_0: test_tampering (provisional) — existing test lines changed/removed (4): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go
- results/c7_runs/C7-10_agy_gemini-4-argon-medium_20261015_234312/trial_0: test_tampering (provisional) — existing test lines changed/removed (4): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go
- results/c7_runs/C7-10_agy_gemini-4-argon-medium_20261015_234313/trial_0: test_tampering (provisional) — existing test lines changed/removed (4): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go
- results/c7_runs/C7-10_agy_gemini-4-argon-medium_20261015_234314/trial_0: test_tampering (provisional) — existing test lines changed/removed (4): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go
- results/c7_runs/C7-10_claude_claude-opus-5-5_20261015_183759/trial_0: test_tampering (provisional) — existing test lines changed/removed (4): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go
- results/c7_runs/C7-10_claude_claude-opus-5-5_20261015_183800/trial_0: test_tampering (provisional) — existing test lines changed/removed (4): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go
- results/c7_runs/C7-10_claude_claude-opus-5-5_20261015_183801/trial_0: test_tampering (provisional) — existing test lines changed/removed (4): fileutil/fileutil_test.go; existing test lines changed/removed (2): handler/jobhandler_test.go
- results/c7_runs/C7-11_agy_gemini-4-argon-low_20261015_234321/trial_0: test_tampering (provisional) — existing test lines changed/removed (2): s2/shapeutil_edge_iterator_test.go
- results/c7_runs/C7-11_agy_gemini-4-argon-low_20261015_234322/trial_0: test_tampering (provisional) — existing test lines changed/removed (2): s2/shapeutil_edge_iterator_test.go
- results/c7_runs/C7-11_agy_gemini-4-argon-low_20261015_234323/trial_0: test_tampering (provisional) — existing test lines changed/removed (2): s2/shapeutil_edge_iterator_test.go
- results/c7_runs/C7-11_agy_gemini-4-argon-medium_20261015_234319/trial_0: test_tampering (provisional) — existing test lines changed/removed (2): s2/shapeutil_edge_iterator_test.go

## Per trial

Item levels: P = perfect (100), A = accept (60), B = bad (0), – = not applicable. Read / Maint / Robust = the 3 common items; Case = the case-specific item(s) in order.

| Case | Model | Trial | Pass | Score | D2 | Read | Maint | Robust | Case | Time (min) | Tool calls | Tokens (K) | Notes | Verifier reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C7-01 | claude-opus-5-5 | 0 | ❌ | 0 | 90 | P | P | A | P | 4 | 15 | 533 |  | not resolved (F2P 129/130, P2P 566/566) |
| C7-01 | claude-opus-5-5 | 0 | ❌ | 0 | 90 | P | P | A | P | 4 | 17 | 637 |  | not resolved (F2P 129/130, P2P 566/566) |
| C7-01 | claude-opus-5-5 | 0 | ❌ | 0 | 90 | P | P | A | P | 4 | 16 | 630 |  | not resolved (F2P 129/130, P2P 566/566) |
| C7-01 | gemini-3.6-flash-high | 0 | ✅ | 1 | 80 | A | A | P | P | 18 | 161 | 1391 |  | resolved (F2P 130/130, P2P 566/566) |
| C7-01 | gemini-3.6-flash-high | 0 | ✅ | 1 | 80 | A | A | P | P | 26 | 125 | 1098 |  | resolved (F2P 130/130, P2P 566/566) |
| C7-01 | gemini-3.6-flash-high | 0 | ✅ | 1 | 55 | A | B | P | A | 13 | 146 | 1236 |  | resolved (F2P 130/130, P2P 566/566) |
| C7-01 | gemini-3.8-flash-high | 0 | ✅ | 1 | 80 | P | A | P | A | 48 | 210 | 2479 |  | resolved (F2P 130/130, P2P 566/566) |
| C7-01 | gemini-3.8-flash-high | 0 | ✅ | 1 | 90 | P | A | P | P | 23 | 197 | 990 |  | resolved (F2P 130/130, P2P 566/566) |
| C7-01 | gemini-3.8-flash-high | 0 | ✅ | 1 | 90 | P | A | P | P | 38 | 220 | 2234 |  | resolved (F2P 130/130, P2P 566/566) |
| C7-01 | gemini-4-argon-high | 0 | ✅ | 1 | 80 | A | A | P | P | 25 | 112 | 632 |  | resolved (F2P 130/130, P2P 566/566) |
| C7-01 | gemini-4-argon-high | 0 | ✅ | 1 | 80 | A | A | P | P | 34 | 154 | 947 |  | resolved (F2P 130/130, P2P 566/566) |
| C7-01 | gemini-4-argon-high | 0 | ✅ | 1 | 80 | A | A | P | P | 24 | 113 | 409 |  | resolved (F2P 130/130, P2P 566/566) |
| C7-01 | gemini-4-argon-low | 0 | ✅ | 1 | 90 | P | A | P | P | 17 | 115 | 343 |  | resolved (F2P 130/130, P2P 566/566) |
| C7-01 | gemini-4-argon-low | 0 | ✅ | 1 | 80 | P | A | P | A | 39 | 119 | 1195 |  | resolved (F2P 130/130, P2P 566/566) |
| C7-01 | gemini-4-argon-low | 0 | ✅ | 1 | 90 | P | A | P | P | 18 | 106 | 553 |  | resolved (F2P 130/130, P2P 566/566) |
| C7-01 | gemini-4-argon-medium | 0 | ✅ | 1 | 80 | A | A | P | P | 42 | 111 | 1729 |  | resolved (F2P 130/130, P2P 566/566) |
| C7-01 | gemini-4-argon-medium | 0 | ✅ | 1 | 90 | P | A | P | P | 37 | 122 | 596 |  | resolved (F2P 130/130, P2P 566/566) |
| C7-01 | gemini-4-argon-medium | 0 | ✅ | 1 | 80 | A | A | P | P | 46 | 131 | 1057 |  | resolved (F2P 130/130, P2P 566/566) |
| C7-02 | claude-opus-5-5 | 0 | ✅ | 1 | 76 | A | A | A | P,P | 0 | 4 | 89 |  | all 7 tests passed |
| C7-02 | claude-opus-5-5 | 0 | ✅ | 1 | 68 | A | A | A | P,A | 0 | 4 | 90 |  | all 7 tests passed |
| C7-02 | claude-opus-5-5 | 0 | ✅ | 1 | 20 | B | B | B | P,B | 1 | 5 | 109 |  | all 7 tests passed |
| C7-02 | gemini-3.6-flash-high | 0 | ✅ | 1 | 56 | A | A | A | P,B | 3 | 46 | 234 |  | all 7 tests passed |
| C7-02 | gemini-3.6-flash-high | 0 | ✅ | 1 | 48 | A | A | A | A,B | 2 | 33 | 167 |  | all 7 tests passed |
| C7-02 | gemini-3.6-flash-high | 0 | ✅ | 1 | 56 | A | A | A | P,B | 2 | 41 | 217 |  | all 7 tests passed |
| C7-02 | gemini-3.8-flash-high | 0 | ✅ | 1 | 76 | A | A | A | P,P | 7 | 40 | 248 |  | all 7 tests passed |
| C7-02 | gemini-3.8-flash-high | 0 | ✅ | 1 | 76 | A | A | A | P,P | 5 | 37 | 177 |  | all 7 tests passed |
| C7-02 | gemini-3.8-flash-high | 0 | ✅ | 1 | 56 | A | A | A | P,B | 6 | 54 | 302 |  | all 7 tests passed |
| C7-02 | gemini-4-argon-high | 0 | ✅ | 1 | 76 | A | A | A | P,P | 4 | 13 | 56 |  | all 7 tests passed |
| C7-02 | gemini-4-argon-high | 0 | ✅ | 1 | 76 | A | A | A | P,P | 3 | 13 | 75 |  | all 7 tests passed |
| C7-02 | gemini-4-argon-high | 0 | ✅ | 1 | 76 | A | A | A | P,P | 5 | 15 | 62 |  | all 7 tests passed |
| C7-02 | gemini-4-argon-low | 0 | ✅ | 1 | 56 | A | A | A | P,B | 1 | 6 | 28 |  | all 7 tests passed |
| C7-02 | gemini-4-argon-low | 0 | ✅ | 1 | 76 | A | A | A | P,P | 1 | 8 | 32 |  | all 7 tests passed |
| C7-02 | gemini-4-argon-low | 0 | ✅ | 1 | 56 | A | A | A | P,B | 2 | 11 | 41 |  | all 7 tests passed |
| C7-02 | gemini-4-argon-medium | 0 | ✅ | 1 | 76 | A | A | A | P,P | 3 | 8 | 35 |  | all 7 tests passed |
| C7-02 | gemini-4-argon-medium | 0 | ✅ | 1 | 68 | A | A | A | P,A | 5 | 11 | 82 |  | all 7 tests passed |
| C7-02 | gemini-4-argon-medium | 0 | ✅ | 1 | 76 | A | A | A | P,P | 2 | 7 | 43 |  | all 7 tests passed |
| C7-03 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P | 4 | 25 | 682 |  | resolved (F2P 1/1, P2P 85/85) |
| C7-03 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P | 3 | 14 | 385 |  | resolved (F2P 1/1, P2P 85/85) |
| C7-03 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P | 1 | 12 | 339 |  | resolved (F2P 1/1, P2P 85/85) |
| C7-03 | gemini-3.6-flash-high | 0 | ✅ | 1 | 15 | A | B | B | B | 15 | 96 | 726 |  | resolved (F2P 1/1, P2P 85/85) |
| C7-03 | gemini-3.6-flash-high | 0 | ✅ | 1 | 45 | A | A | A | B | 17 | 74 | 791 |  | resolved (F2P 1/1, P2P 85/85) |
| C7-03 | gemini-3.6-flash-high | 0 | ✅ | 1 | 100 | P | P | P | P | 16 | 95 | 715 |  | resolved (F2P 1/1, P2P 85/85) |
| C7-03 | gemini-3.8-flash-high | 0 | ✅ | 1 | 30 | A | B | A | B | 25 | 175 | 976 |  | resolved (F2P 1/1, P2P 85/85) |
| C7-03 | gemini-3.8-flash-high | 0 | ✅ | 1 | 90 | P | A | P | P | 30 | 100 | 834* | timeout | resolved (F2P 1/1, P2P 85/85) |
| C7-03 | gemini-3.8-flash-high | 0 | ✅ | 1 | 45 | A | A | A | B | 19 | 98 | 611 |  | resolved (F2P 1/1, P2P 85/85) |
| C7-03 | gemini-4-argon-high | 0 | ✅ | 1 | 100 | P | P | P | P | 18 | 54 | 314 |  | resolved (F2P 1/1, P2P 85/85) |
| C7-03 | gemini-4-argon-high | 0 | ✅ | 1 | 100 | P | P | P | P | 15 | 33 | 256 |  | resolved (F2P 1/1, P2P 85/85) |
| C7-03 | gemini-4-argon-high | 0 | ✅ | 1 | 100 | P | P | P | P | 15 | 43 | 329 |  | resolved (F2P 1/1, P2P 85/85) |
| C7-03 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P | 19 | 42 | 452 |  | resolved (F2P 1/1, P2P 85/85) |
| C7-03 | gemini-4-argon-low | 0 | ✅ | 1 | 90 | P | P | P | A | 30 | 79 | 746* | timeout | resolved (F2P 1/1, P2P 85/85) |
| C7-03 | gemini-4-argon-low | 0 | ✅ | 1 | 30 | A | A | B | B | 15 | 50 | 598 |  | resolved (F2P 1/1, P2P 85/85) |
| C7-03 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P | 23 | 47 | 514 |  | resolved (F2P 1/1, P2P 85/85) |
| C7-03 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P | 30 | 39 | 464* | timeout | resolved (F2P 1/1, P2P 85/85) |
| C7-03 | gemini-4-argon-medium | 0 | ✅ | 1 | 45 | A | A | A | B | 14 | 76 | 460 |  | resolved (F2P 1/1, P2P 85/85) |
| C7-04 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P | 1 | 6 | 138 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-04 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P | 0 | 6 | 136 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-04 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P | 0 | 6 | 136 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-04 | gemini-3.6-flash-high | 0 | ✅ | 1 | 100 | P | P | P | P | 12 | 50 | 426 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-04 | gemini-3.6-flash-high | 0 | ✅ | 1 | 100 | P | P | P | P | 11 | 54 | 409 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-04 | gemini-3.6-flash-high | 0 | ✅ | 1 | 90 | A | P | P | P | 9 | 65 | 552 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-04 | gemini-3.8-flash-high | 0 | ✅ | 1 | 70 | P | A | A | A | 13 | 89 | 492 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-04 | gemini-3.8-flash-high | 0 | ✅ | 1 | 100 | P | P | P | P | 12 | 78 | 431 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-04 | gemini-3.8-flash-high | 0 | ✅ | 1 | 100 | P | P | P | P | 14 | 83 | 491 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-04 | gemini-4-argon-high | 0 | ✅ | 1 | 100 | P | P | P | P | 11 | 46 | 312 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-04 | gemini-4-argon-high | 0 | ✅ | 1 | 100 | P | P | P | P | 12 | 49 | 208 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-04 | gemini-4-argon-high | 0 | ✅ | 1 | 100 | P | P | P | P | 6 | 30 | 135 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-04 | gemini-4-argon-low | 0 | ✅ | 1 | 60 | A | A | A | A | 15 | 42 | 190 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-04 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P | 3 | 28 | 80 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-04 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P | 9 | 26 | 86 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-04 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P | 8 | 36 | 123 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-04 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P | 12 | 44 | 161 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-04 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P | 10 | 32 | 168 |  | resolved (F2P 1/1, P2P 52/52) |
| C7-05 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P | 1 | 6 | 146 |  | resolved (F2P 2/2, P2P 78/78) |
| C7-05 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P | 1 | 12 | 310 |  | resolved (F2P 2/2, P2P 78/78) |
| C7-05 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P | 1 | 10 | 234 |  | resolved (F2P 2/2, P2P 78/78) |
| C7-05 | gemini-3.6-flash-high | 0 | ✅ | 1 | 80 | P | A | P | A | 11 | 49 | 399 |  | resolved (F2P 2/2, P2P 78/78) |
| C7-05 | gemini-3.6-flash-high | 0 | ✅ | 1 | 70 | P | A | A | A | 10 | 34 | 514 |  | resolved (F2P 2/2, P2P 78/78) |
| C7-05 | gemini-3.6-flash-high | 0 | ✅ | 1 | 70 | A | A | P | A | 14 | 55 | 667 |  | resolved (F2P 2/2, P2P 78/78) |
| C7-05 | gemini-3.8-flash-high | 0 | ✅ | 1 | 70 | A | A | A | P | 30 | 76 | 749* | timeout | resolved (F2P 2/2, P2P 78/78) |
| C7-05 | gemini-3.8-flash-high | 0 | ✅ | 1 | 90 | P | A | P | P | 15 | 87 | 632 |  | resolved (F2P 2/2, P2P 78/78) |
| C7-05 | gemini-3.8-flash-high | 0 | ✅ | 1 | 70 | P | A | A | A | 15 | 94 | 1176 |  | resolved (F2P 2/2, P2P 78/78) |
| C7-05 | gemini-4-argon-high | 0 | ✅ | 1 | 100 | P | P | P | P | 16 | 36 | 248 |  | resolved (F2P 2/2, P2P 78/78) |
| C7-05 | gemini-4-argon-high | 0 | ✅ | 1 | 100 | P | P | P | P | 12 | 23 | 177 |  | resolved (F2P 2/2, P2P 78/78) |
| C7-05 | gemini-4-argon-high | 0 | ✅ | 1 | 100 | P | P | P | P | 14 | 35 | 383 |  | resolved (F2P 2/2, P2P 78/78) |
| C7-05 | gemini-4-argon-low | 0 | ✅ | 1 | 90 | P | P | A | P | 11 | 35 | 143 |  | resolved (F2P 2/2, P2P 78/78) |
| C7-05 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P | 26 | 32 | 190 |  | resolved (F2P 2/2, P2P 78/78) |
| C7-05 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P | 6 | 27 | 110 |  | resolved (F2P 2/2, P2P 78/78) |
| C7-05 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P | 12 | 31 | 159 |  | resolved (F2P 2/2, P2P 78/78) |
| C7-05 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P | 21 | 32 | 335 |  | resolved (F2P 2/2, P2P 78/78) |
| C7-05 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P | 12 | 31 | 445 |  | resolved (F2P 2/2, P2P 78/78) |
| C7-06 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P,P | 0 | 7 | 130 |  | resolved (F2P 3/3, P2P 6/6) |
| C7-06 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P,P | 0 | 8 | 166 |  | resolved (F2P 3/3, P2P 6/6) |
| C7-06 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P,P | 0 | 6 | 126 |  | resolved (F2P 3/3, P2P 6/6) |
| C7-06 | gemini-3.6-flash-high | 0 | ✅ | 1 | 100 | P | P | P | P,P | 4 | 41 | 225 |  | resolved (F2P 3/3, P2P 6/6) |
| C7-06 | gemini-3.6-flash-high | 0 | ✅ | 1 | 92 | P | A | P | P,P | 2 | 41 | 301 |  | resolved (F2P 3/3, P2P 6/6) |
| C7-06 | gemini-3.6-flash-high | 0 | ✅ | 1 | 100 | P | P | P | P,P | 2 | 36 | 252 |  | resolved (F2P 3/3, P2P 6/6) |
| C7-06 | gemini-3.8-flash-high | 0 | ✅ | 1 | 100 | P | P | P | P,P | 14 | 78 | 467 |  | resolved (F2P 3/3, P2P 6/6) |
| C7-06 | gemini-3.8-flash-high | 0 | ❌ | 0 | 92 | P | A | P | P,P | 13 | 76 | 816 |  | not resolved (F2P 0/3, P2P 6/6); first failure: test_options_non_deprecated_keys_preferred |
| C7-06 | gemini-3.8-flash-high | 0 | ✅ | 1 | 100 | P | P | P | P,P | 13 | 67 | 753 |  | resolved (F2P 3/3, P2P 6/6) |
| C7-06 | gemini-4-argon-high | 0 | ✅ | 1 | 100 | P | P | P | P,P | 4 | 39 | 183 |  | resolved (F2P 3/3, P2P 6/6) |
| C7-06 | gemini-4-argon-high | 0 | ✅ | 1 | 100 | P | P | P | P,P | 4 | 42 | 138 |  | resolved (F2P 3/3, P2P 6/6) |
| C7-06 | gemini-4-argon-high | 0 | ✅ | 1 | 100 | P | P | P | P,P | 5 | 43 | 132 |  | resolved (F2P 3/3, P2P 6/6) |
| C7-06 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P,P | 3 | 18 | 59 |  | resolved (F2P 3/3, P2P 6/6) |
| C7-06 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P,P | 2 | 19 | 61 |  | resolved (F2P 3/3, P2P 6/6) |
| C7-06 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P,P | 2 | 22 | 53 |  | resolved (F2P 3/3, P2P 6/6) |
| C7-06 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P,P | 7 | 26 | 96 |  | resolved (F2P 3/3, P2P 6/6) |
| C7-06 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P,P | 5 | 21 | 106 |  | resolved (F2P 3/3, P2P 6/6) |
| C7-06 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P,P | 7 | 26 | 70 |  | resolved (F2P 3/3, P2P 6/6) |
| C7-07 | claude-opus-5-5 | 0 | ✅ | 1 | 90 | P | A | P | P | 1 | 9 | 211 |  | resolved (F2P 1/1, P2P 148/148) |
| C7-07 | claude-opus-5-5 | 0 | ✅ | 1 | 90 | P | A | P | P | 0 | 6 | 139 |  | resolved (F2P 1/1, P2P 148/148) |
| C7-07 | claude-opus-5-5 | 0 | ✅ | 1 | 90 | P | A | P | P | 0 | 7 | 157 |  | resolved (F2P 1/1, P2P 148/148) |
| C7-07 | gemini-3.6-flash-high | 0 | ✅ | 1 | 70 | A | A | P | A | 3 | 45 | 316 |  | resolved (F2P 1/1, P2P 148/148) |
| C7-07 | gemini-3.6-flash-high | 0 | ✅ | 1 | 80 | P | A | P | A | 4 | 38 | 272 |  | resolved (F2P 1/1, P2P 148/148) |
| C7-07 | gemini-3.6-flash-high | 0 | ✅ | 1 | 80 | P | A | P | A | 4 | 51 | 410 |  | resolved (F2P 1/1, P2P 148/148) |
| C7-07 | gemini-3.8-flash-high | 0 | ✅ | 1 | 60 | A | A | A | A | 23 | 78 | 542 |  | resolved (F2P 1/1, P2P 148/148) |
| C7-07 | gemini-3.8-flash-high | 0 | ✅ | 1 | 60 | A | A | A | A | 17 | 70 | 616 |  | resolved (F2P 1/1, P2P 148/148) |
| C7-07 | gemini-3.8-flash-high | 0 | ✅ | 1 | 60 | A | A | A | A | 14 | 87 | 803 |  | resolved (F2P 1/1, P2P 148/148) |
| C7-07 | gemini-4-argon-high | 0 | ✅ | 1 | 90 | P | A | P | P | 17 | 66 | 283 |  | resolved (F2P 1/1, P2P 148/148) |
| C7-07 | gemini-4-argon-high | 0 | ❌ | 0 | — | – | – | – | – | 30 | 35 | 115* | timeout, no code | not resolved (F2P 0/1, P2P 130/148); first failure: test_non_ascii_dns_non_unicode_email ( |
| C7-07 | gemini-4-argon-high | 0 | ✅ | 1 | 90 | P | A | P | P | 16 | 79 | 522 |  | resolved (F2P 1/1, P2P 148/148) |
| C7-07 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P | 11 | 52 | 295 |  | resolved (F2P 1/1, P2P 148/148) |
| C7-07 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P | 10 | 47 | 134 |  | resolved (F2P 1/1, P2P 148/148) |
| C7-07 | gemini-4-argon-low | 0 | ✅ | 1 | 90 | P | A | P | P | 13 | 60 | 357 |  | resolved (F2P 1/1, P2P 148/148) |
| C7-07 | gemini-4-argon-medium | 0 | ✅ | 1 | 90 | P | P | P | A | 10 | 51 | 514 |  | resolved (F2P 1/1, P2P 148/148) |
| C7-07 | gemini-4-argon-medium | 0 | ✅ | 1 | 90 | P | A | P | P | 23 | 58 | 522 |  | resolved (F2P 1/1, P2P 148/148) |
| C7-07 | gemini-4-argon-medium | 0 | ❌ | 0 | — | – | – | – | – | 30 | 31 | 225* | timeout, no code | not resolved (F2P 0/1, P2P 130/148); first failure: test_non_ascii_dns_non_unicode_email ( |
| C7-08 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P | 0 | 6 | 110 |  | resolved (F2P 2/2, P2P 185/185) |
| C7-08 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P | 0 | 5 | 91 |  | resolved (F2P 2/2, P2P 185/185) |
| C7-08 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P | 0 | 6 | 110 |  | resolved (F2P 2/2, P2P 185/185) |
| C7-08 | gemini-3.6-flash-high | 0 | ❌ | 0 | 55 | P | A | A | B | 12 | 92 | 762 |  | not resolved (F2P 0/2, P2P 185/185); first failure: tests/test_utils.py::test_prepend_sche |
| C7-08 | gemini-3.6-flash-high | 0 | ✅ | 1 | 60 | A | A | A | A | 10 | 72 | 541 |  | resolved (F2P 2/2, P2P 185/185) |
| C7-08 | gemini-3.6-flash-high | 0 | ✅ | 1 | 45 | A | A | A | B | 11 | 109 | 828 |  | resolved (F2P 2/2, P2P 185/185) |
| C7-08 | gemini-3.8-flash-high | 0 | ✅ | 1 | 45 | A | A | A | B | 13 | 148 | 832 |  | resolved (F2P 2/2, P2P 185/185) |
| C7-08 | gemini-3.8-flash-high | 0 | ✅ | 1 | 100 | P | P | P | P | 21 | 119 | 823 |  | resolved (F2P 2/2, P2P 185/185) |
| C7-08 | gemini-3.8-flash-high | 0 | ✅ | 1 | 80 | A | P | A | P | 15 | 133 | 692 |  | resolved (F2P 2/2, P2P 185/185) |
| C7-08 | gemini-4-argon-high | 0 | ✅ | 1 | 90 | P | P | A | P | 6 | 41 | 199 |  | resolved (F2P 2/2, P2P 185/185) |
| C7-08 | gemini-4-argon-high | 0 | ✅ | 1 | 100 | P | P | P | P | 6 | 37 | 162 |  | resolved (F2P 2/2, P2P 185/185) |
| C7-08 | gemini-4-argon-high | 0 | ✅ | 1 | 90 | P | P | A | P | 7 | 44 | 173 |  | resolved (F2P 2/2, P2P 185/185) |
| C7-08 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P | 4 | 24 | 81 |  | resolved (F2P 2/2, P2P 185/185) |
| C7-08 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P | 8 | 24 | 78 |  | resolved (F2P 2/2, P2P 185/185) |
| C7-08 | gemini-4-argon-low | 0 | ✅ | 1 | 100 | P | P | P | P | 6 | 27 | 130 |  | resolved (F2P 2/2, P2P 185/185) |
| C7-08 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P | 12 | 35 | 196 |  | resolved (F2P 2/2, P2P 185/185) |
| C7-08 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P | 3 | 19 | 69 |  | resolved (F2P 2/2, P2P 185/185) |
| C7-08 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P | 11 | 24 | 135 |  | resolved (F2P 2/2, P2P 185/185) |
| C7-09 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P,P | 13 | 38 | 3170 |  | resolved (F2P 2/2, P2P 214/214) |
| C7-09 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P,P | 10 | 34 | 2676 |  | resolved (F2P 2/2, P2P 214/214) |
| C7-09 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P,P | 10 | 37 | 3083 |  | resolved (F2P 2/2, P2P 214/214) |
| C7-09 | gemini-3.6-flash-high | 0 | ❌ | 0 | 56 | A | B | A | P,A | 24 | 89 | 873 |  | not resolved (F2P 0/2, P2P 214/214) |
| C7-09 | gemini-3.6-flash-high | 0 | ✅ | 1 | 92 | P | A | P | P,P | 12 | 108 | 953 |  | resolved (F2P 2/2, P2P 214/214) |
| C7-09 | gemini-3.6-flash-high | 0 | ❌ | 0 | 48 | A | B | A | A,A | 21 | 207 | 1638 |  | not resolved (F2P 0/2, P2P 214/214) |
| C7-09 | gemini-3.8-flash-high | 0 | ✅ | 1 | 92 | P | A | P | P,P | 35 | 191 | 1780 |  | resolved (F2P 2/2, P2P 214/214) |
| C7-09 | gemini-3.8-flash-high | 0 | ✅ | 1 | 92 | P | A | P | P,P | 24 | 160 | 1170 |  | resolved (F2P 2/2, P2P 214/214) |
| C7-09 | gemini-3.8-flash-high | 0 | ✅ | 1 | 76 | A | A | A | P,P | 25 | 127 | 846 |  | resolved (F2P 2/2, P2P 214/214) |
| C7-09 | gemini-4-argon-high | 0 | ✅ | 1 | 84 | P | A | A | P,P | 33 | 170 | 1136 |  | resolved (F2P 2/2, P2P 214/214) |
| C7-09 | gemini-4-argon-high | 0 | ✅ | 1 | 92 | P | P | A | P,P | 63 | 258 | 1339 |  | resolved (F2P 2/2, P2P 214/214) |
| C7-09 | gemini-4-argon-high | 0 | ✅ | 1 | 100 | P | P | P | P,P | 48 | 250 | 1475 |  | resolved (F2P 2/2, P2P 214/214) |
| C7-09 | gemini-4-argon-low | 0 | ✅ | 1 | 92 | P | A | P | P,P | 39 | 188 | 1522 |  | resolved (F2P 2/2, P2P 214/214) |
| C7-09 | gemini-4-argon-low | 0 | ✅ | 1 | 84 | P | A | A | P,P | 30 | 143 | 1639 |  | resolved (F2P 2/2, P2P 214/214) |
| C7-09 | gemini-4-argon-low | 0 | ✅ | 1 | 84 | P | A | A | P,P | 31 | 173 | 750 |  | resolved (F2P 2/2, P2P 214/214) |
| C7-09 | gemini-4-argon-medium | 0 | ✅ | 1 | 84 | P | A | P | A,P | 78 | 264 | 2200 |  | resolved (F2P 2/2, P2P 214/214) |
| C7-09 | gemini-4-argon-medium | 0 | ✅ | 1 | 100 | P | P | P | P,P | 60 | 243 | 1783 |  | resolved (F2P 2/2, P2P 214/214) |
| C7-09 | gemini-4-argon-medium | 0 | ✅ | 1 | 84 | P | A | A | P,P | 61 | 268 | 1203 |  | resolved (F2P 2/2, P2P 214/214) |
| C7-10 | claude-opus-5-5 | 0 | ✅ | 1 | 80 | P | A | P | A | 4 | 14 | 574 |  | resolved (F2P 82/82, P2P 6/6) |
| C7-10 | claude-opus-5-5 | 0 | ❌ | 0 | 80 | P | A | P | A | 3 | 15 | 659 |  | not resolved (F2P 76/82, P2P 6/6) |
| C7-10 | claude-opus-5-5 | 0 | ✅ | 1 | 80 | A | P | P | A | 3 | 14 | 600 |  | resolved (F2P 82/82, P2P 6/6) |
| C7-10 | gemini-3.6-flash-high | 0 | ✅ | 1 | 60 | A | A | A | A | 14 | 59 | 584 |  | resolved (F2P 82/82, P2P 6/6) |
| C7-10 | gemini-3.6-flash-high | 0 | ✅ | 1 | 60 | A | A | A | A | 13 | 51 | 569 |  | resolved (F2P 82/82, P2P 6/6) |
| C7-10 | gemini-3.6-flash-high | 0 | ❌ | 0 | 45 | A | B | A | A | 9 | 54 | 546 |  | not resolved (F2P 71/82, P2P 6/6) |
| C7-10 | gemini-3.8-flash-high | 0 | ❌ | 0 | 60 | A | A | A | A | 18 | 91 | 805 |  | not resolved (F2P 80/82, P2P 6/6) |
| C7-10 | gemini-3.8-flash-high | 0 | ✅ | 1 | 70 | P | A | A | A | 15 | 82 | 511 |  | resolved (F2P 82/82, P2P 6/6) |
| C7-10 | gemini-3.8-flash-high | 0 | ✅ | 1 | 60 | A | A | A | A | 12 | 72 | 1494 |  | resolved (F2P 82/82, P2P 6/6) |
| C7-10 | gemini-4-argon-high | 0 | ✅ | 1 | 60 | A | A | A | A | 17 | 36 | 222 |  | resolved (F2P 82/82, P2P 6/6) |
| C7-10 | gemini-4-argon-high | 0 | ✅ | 1 | 80 | A | A | P | P | 14 | 36 | 190 |  | resolved (F2P 82/82, P2P 6/6) |
| C7-10 | gemini-4-argon-high | 0 | ✅ | 1 | 80 | P | A | P | A | 28 | 43 | 239 |  | resolved (F2P 82/82, P2P 6/6) |
| C7-10 | gemini-4-argon-low | 0 | ✅ | 1 | 70 | A | A | P | A | 12 | 41 | 134 |  | resolved (F2P 82/82, P2P 6/6) |
| C7-10 | gemini-4-argon-low | 0 | ✅ | 1 | 60 | A | A | A | A | 8 | 35 | 142 |  | resolved (F2P 82/82, P2P 6/6) |
| C7-10 | gemini-4-argon-low | 0 | ✅ | 1 | 70 | A | A | P | A | 18 | 39 | 203 |  | resolved (F2P 82/82, P2P 6/6) |
| C7-10 | gemini-4-argon-medium | 0 | ✅ | 1 | 70 | A | A | P | A | 13 | 34 | 177 |  | resolved (F2P 82/82, P2P 6/6) |
| C7-10 | gemini-4-argon-medium | 0 | ✅ | 1 | 80 | P | A | P | A | 17 | 44 | 443 |  | resolved (F2P 82/82, P2P 6/6) |
| C7-10 | gemini-4-argon-medium | 0 | ✅ | 1 | 60 | A | A | A | A | 33 | 33 | 439 |  | resolved (F2P 82/82, P2P 6/6) |
| C7-11 | claude-opus-5-5 | 0 | ✅ | 1 | 65 | A | B | P | P | 13 | 33 | 2010 |  | resolved (F2P 24/24, P2P 599/599) |
| C7-11 | claude-opus-5-5 | 0 | ✅ | 1 | 80 | P | A | A | P | 13 | 40 | 3282 |  | resolved (F2P 24/24, P2P 599/599) |
| C7-11 | claude-opus-5-5 | 0 | ✅ | 1 | 80 | A | A | P | P | 14 | 25 | 87 |  | resolved (F2P 24/24, P2P 599/599) |
| C7-11 | gemini-3.6-flash-high | 0 | ✅ | 1 | 55 | A | B | A | P | 7 | 64 | 853 |  | resolved (F2P 24/24, P2P 599/599) |
| C7-11 | gemini-3.6-flash-high | 0 | ✅ | 1 | 55 | A | B | A | P | 16 | 65 | 645 |  | resolved (F2P 24/24, P2P 599/599) |
| C7-11 | gemini-3.6-flash-high | 0 | ❌ | 0 | 40 | A | B | B | P | 11 | 53 | 455 |  | not resolved (F2P 14/24, P2P 599/599) |
| C7-11 | gemini-3.8-flash-high | 0 | ✅ | 1 | 80 | A | A | P | P | 57 | 218 | 2587 |  | resolved (F2P 24/24, P2P 599/599) |
| C7-11 | gemini-3.8-flash-high | 0 | ✅ | 1 | 55 | P | B | A | A | 22 | 141 | 1342 |  | resolved (F2P 24/24, P2P 599/599) |
| C7-11 | gemini-3.8-flash-high | 0 | ✅ | 1 | 70 | P | A | A | A | 41 | 151 | 1500 |  | resolved (F2P 24/24, P2P 599/599) |
| C7-11 | gemini-4-argon-high | 0 | ✅ | 1 | 45 | A | B | A | A | 44 | 146 | 1086 |  | resolved (F2P 24/24, P2P 599/599) |
| C7-11 | gemini-4-argon-high | 0 | ✅ | 1 | 80 | P | A | P | A | 40 | 149 | 1200 |  | resolved (F2P 24/24, P2P 599/599) |
| C7-11 | gemini-4-argon-high | 0 | ✅ | 1 | 45 | A | B | A | A | 32 | 108 | 987 |  | resolved (F2P 24/24, P2P 599/599) |
| C7-11 | gemini-4-argon-low | 0 | ✅ | 1 | 80 | A | A | P | P | 33 | 117 | 726 |  | resolved (F2P 24/24, P2P 599/599) |
| C7-11 | gemini-4-argon-low | 0 | ✅ | 1 | 45 | A | B | A | A | 42 | 96 | 1337 |  | resolved (F2P 24/24, P2P 599/599) |
| C7-11 | gemini-4-argon-low | 0 | ✅ | 1 | 55 | A | B | P | A | 28 | 91 | 665 |  | resolved (F2P 24/24, P2P 599/599) |
| C7-11 | gemini-4-argon-medium | 0 | ✅ | 1 | 45 | A | B | A | A | 29 | 75 | 681 |  | resolved (F2P 24/24, P2P 599/599) |
| C7-11 | gemini-4-argon-medium | 0 | ✅ | 1 | 80 | A | A | P | P | 17 | 97 | 406 |  | resolved (F2P 24/24, P2P 599/599) |
| C7-11 | gemini-4-argon-medium | 0 | ✅ | 1 | 45 | A | B | A | A | 39 | 102 | 944 |  | resolved (F2P 24/24, P2P 599/599) |
