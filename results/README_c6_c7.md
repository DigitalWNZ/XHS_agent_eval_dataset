# Detailed results: C6 (discriminative) / C7 (daily work) / C8 (hard) agent runs (all runs)

Agents: Antigravity (agy) with gemini-3.6-flash-high / gemini-3.8-flash-high / gemini-4-argon-high; Claude Code with claude-opus-5-5 (Vertex). All recorded runs are pooled (several campaigns, so trial counts differ; for one campaign use tools/campaign_report.py). P = pass, F = fail. C8-02 has a continuous score in [0, 1] and passes at >= 0.1. Runs invalidated by harness bugs are excluded (see results/*_runs_invalid/); trials that later failed the validity audit are NOT excluded here (see results/README_quality.md).

Entry IDs follow the current (2026-10-15) layout; *Former ID* is the ID before that restructure; runs are mapped from the ID they recorded (raw run folders keep it; mapping in results/id_mapping.json).

Columns: *Details* = grader verdict (F2P/P2P = fail-to-pass / pass-to-pass tests passed); *Agent time* = agent wall time (budget-capped); *Tokens* = input+output incl. cache; *Turns* as reported by the agent CLI (agy reports 1 per session; when agy hits its time budget, tokens/turns are not reported and show ? / 0).

## Overview

| Entry | Former ID | Source / task | claude-opus-5-5 | gemini-3.6-flash-high | gemini-3.8-flash-high | gemini-4-argon-high |
|---|---|---|---|---|---|---|
| C6-01 | C6-01 | Terminal-Bench 2.0 / filter-js-from-html | 0/6 | 0/6 | 3/6 | 0/3 |
| C6-02 | C6-03 | DeepSWE v1.1 / pebble-durability-wait-apis | 6/6 | 0/6 | 6/6 | 3/3 |
| C6-03 | C6-04 | Terminal-Bench 2.0 / video-processing | 3/6 | 1/6 | 3/6 | 2/3 |
| C6-04 | C6-06 | Terminal-Bench 2.0 / mteb-retrieve | 6/6 | 1/6 | 6/6 | 1/3 |
| C6-05 | C7-01 | Terminal-Bench 2.0 / polyglot-c-py | 5/6 | 3/8 | 9/9 | 3/3 |
| C6-06 | C7-03 | Terminal-Bench 2.0 / cancel-async-tasks | 6/6 | 5/6 | 3/6 | 0/3 |
| C6-07 | C7-12 | DeepSWE v1.1 / query-persist-restored-query-state | 3/6 | 4/6 | 5/6 | 3/3 |
| **C6 total** | | | **29/42 (69%)** | **14/44 (32%)** | **35/45 (78%)** | **12/21 (57%)** |
| C7-01 | C6-02 | DeepSWE v1.1 / drizzle-orm-window-function-builders | 3/6 | 6/6 | 6/6 | 3/3 |
| C7-02 | C7-04 | Terminal-Bench 2.0 / db-wal-recovery | 7/7 | 6/6 | 6/6 | 3/3 |
| C7-03 | C7-05 | SWE-bench Verified / django__django-15280 | 6/6 | 6/6 | 5/6 | 3/3 |
| C7-04 | C7-06 | SWE-bench Verified / django__django-12965 | 6/6 | 6/6 | 3/6 | 3/3 |
| C7-05 | C7-07 | SWE-bench Verified / django__django-15503 | 6/6 | 6/6 | 5/6 | 2/3 |
| C7-06 | C7-08 | SWE-bench Verified / django__django-14376 | 6/6 | 6/6 | 5/6 | 3/3 |
| C7-07 | C7-09 | SWE-bench Verified / django__django-11532 | 6/6 | 6/6 | 6/6 | 1/3 |
| C7-08 | C7-10 | SWE-bench Verified / psf__requests-6028 | 6/6 | 5/6 | 6/6 | 3/3 |
| C7-09 | C7-11 | DeepSWE v1.1 / kgateway-consistent-hash-policy | 6/6 | 3/6 | 6/6 | 3/3 |
| C7-10 | C7-13 | DeepSWE v1.1 / onedump-dump-encryption-pipeline | 6/6 | 5/6 | 6/6 | 3/3 |
| C7-11 | C7-14 | DeepSWE v1.1 / geo-shapeindex-serialization | 6/6 | 3/6 | 6/6 | 3/3 |
| **C7 total** | | | **64/67 (96%)** | **58/66 (88%)** | **60/66 (91%)** | **30/33 (91%)** |
| C8-01 | C6-05 | SWE-bench Verified / django__django-15957 | 6/6 | 0/6 | 3/6 | 0/3 |
| C8-02 | C6-07 | FrontierSWE v2 / ffmpeg-swscale-rewrite | 4/6 | 0/6 | 0/6 | 1/3 |
| C8-03 | C7-02 | Terminal-Bench 2.0 / query-optimize | 4/6 | 5/6 | 2/6 | 0/3 |
| **C8 total** | | | **14/18 (78%)** | **5/18 (28%)** | **5/18 (28%)** | **1/9 (11%)** |
| **All** | | | **107/127 (84%)** | **77/128 (60%)** | **100/129 (78%)** | **43/63 (68%)** |

## C6 区分度任务 — Discriminative (model-differentiating)

### C6-01 · Terminal-Bench 2.0 / filter-js-from-html (former C6-01)

- **Rednote relevance:** UGC safety: sanitizing user-posted rich text / HTML against XSS
- **Grader:** `tb2_pytest`; agent budget 1800 s

| Model | Trial | Result | Score | Details | Agent time | Tokens | Turns |
|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 1 | ❌ F | 0.000 | test_outputs.py::test_clean_html_unchanged: The test failed in the call phase due to an assertion error | 2.7 min | 103K | 5 |
| claude-opus-5-5 | 2 | ❌ F | 0.000 | test_outputs.py::test_clean_html_unchanged: The test failed in the call phase due to an assertion error | 5.1 min | 293K | 12 |
| claude-opus-5-5 | 3 | ❌ F | 0.000 | test_outputs.py::test_clean_html_unchanged: The test failed in the call phase due to an assertion error | 3.3 min | 130K | 6 |
| claude-opus-5-5 | 4 | ❌ F | 0.000 | test_outputs.py::test_clean_html_unchanged: The test failed in the call phase due to an assertion error | 6.2 min | 318K | 9 |
| claude-opus-5-5 | 5 | ❌ F | 0.000 | test_outputs.py::test_clean_html_unchanged: The test failed in the call phase due to an assertion error | 5.9 min | 303K | 8 |
| claude-opus-5-5 | 6 | ❌ F | 0.000 | test_outputs.py::test_clean_html_unchanged: The test failed in the call phase due to an assertion error | 2.7 min | 248K | 9 |
| gemini-3.6-flash-high | 1 | ❌ F | 0.000 | test_outputs.py::test_filter_blocks_xss: The test failed in the call phase due to an assertion error | 9.9 min | 128K | 1 |
| gemini-3.6-flash-high | 2 | ❌ F | 0.000 | test_outputs.py::test_filter_blocks_xss: The test failed in the call phase due to an assertion error | 15.4 min | 249K | 1 |
| gemini-3.6-flash-high | 3 | ❌ F | 0.000 | test_outputs.py::test_filter_blocks_xss: The test failed in the call phase due to an assertion error | 3.4 min | 207K | 1 |
| gemini-3.6-flash-high | 4 | ❌ F | 0.000 | test_outputs.py::test_filter_blocks_xss: The test failed in the call phase due to an assertion error | 4.4 min | 209K | 1 |
| gemini-3.6-flash-high | 5 | ❌ F | 0.000 | test_outputs.py::test_filter_blocks_xss: The test failed in the call phase due to an assertion error | 10.4 min | 270K | 1 |
| gemini-3.6-flash-high | 6 | ❌ F | 0.000 | test_outputs.py::test_filter_blocks_xss: The test failed in the call phase due to an assertion error | 6.1 min | 184K | 1 |
| gemini-3.8-flash-high | 1 | ✅ P | 1.000 | all 2 tests passed | 10.9 min | 336K | 1 |
| gemini-3.8-flash-high | 2 | ✅ P | 1.000 | all 2 tests passed | 8.2 min | 291K | 1 |
| gemini-3.8-flash-high | 3 | ✅ P | 1.000 | all 2 tests passed | 12.0 min | 334K | 1 |
| gemini-3.8-flash-high | 4 | ❌ F | 0.000 | grader rc=None: verifier timeout 900s | 13.2 min | 520K | 1 |
| gemini-3.8-flash-high | 5 | ❌ F | 0.000 | test_outputs.py::test_filter_blocks_xss: The test failed in the call phase due to an assertion error | 15.1 min | 444K | 1 |
| gemini-3.8-flash-high | 6 | ❌ F | 0.000 | test_outputs.py::test_filter_blocks_xss: The test failed in the call phase due to an assertion error | 14.6 min | 441K | 1 |
| gemini-4-argon-high | 1 | ❌ F | 0.000 | test_outputs.py::test_clean_html_unchanged: The test failed in the call phase due to an assertion error | 23.2 min | 592K | 1 |
| gemini-4-argon-high | 2 | ❌ F | 0.000 | test_outputs.py::test_clean_html_unchanged: The test failed in the call phase due to an assertion error | 25.2 min | 923K | 1 |
| gemini-4-argon-high | 3 | ❌ F | 0.000 | test_outputs.py::test_clean_html_unchanged: The test failed in the call phase due to an assertion error | 30.0 min | ? | 0 |

### C6-02 · DeepSWE v1.1 / pebble-durability-wait-apis (former C6-03)

- **Rednote relevance:** Storage infrastructure: notify when a synced write is durable before acking clients or replicating (LSM key-value store, RocksDB-style)
- **Grader:** `deepswe`; agent budget 10800 s

| Model | Trial | Result | Score | Details | Agent time | Tokens | Turns |
|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 1 | ✅ P | 1.000 | resolved (F2P 59/59, P2P 44/44) | 11.1 min | 1483K | 26 |
| claude-opus-5-5 | 2 | ✅ P | 1.000 | resolved (F2P 59/59, P2P 44/44) | 12.4 min | 1364K | 27 |
| claude-opus-5-5 | 3 | ✅ P | 1.000 | resolved (F2P 59/59, P2P 44/44) | 14.3 min | 1084K | 24 |
| claude-opus-5-5 | 4 | ✅ P | 1.000 | resolved (F2P 59/59, P2P 44/44) | 15.6 min | 1760K | 33 |
| claude-opus-5-5 | 5 | ✅ P | 1.000 | resolved (F2P 59/59, P2P 44/44) | 10.8 min | 1512K | 29 |
| claude-opus-5-5 | 6 | ✅ P | 1.000 | resolved (F2P 59/59, P2P 44/44) | 11.4 min | 1377K | 26 |
| gemini-3.6-flash-high | 1 | ❌ F | 0.000 | not resolved (F2P 58/59, P2P 44/44) | 21.7 min | 1576K | 1 |
| gemini-3.6-flash-high | 2 | ❌ F | 0.000 | not resolved (F2P 57/59, P2P 44/44) | 17.5 min | 1239K | 1 |
| gemini-3.6-flash-high | 3 | ❌ F | 0.000 | not resolved (F2P 55/59, P2P 44/44) | 48.8 min | 3258K | 1 |
| gemini-3.6-flash-high | 4 | ❌ F | 0.000 | not resolved (F2P 58/59, P2P 44/44) | 14.7 min | 1237K | 1 |
| gemini-3.6-flash-high | 5 | ❌ F | 0.000 | not resolved (F2P 58/59, P2P 44/44) | 41.1 min | 1728K | 1 |
| gemini-3.6-flash-high | 6 | ❌ F | 0.000 | not resolved (F2P 55/59, P2P 44/44) | 15.5 min | 1474K | 1 |
| gemini-3.8-flash-high | 1 | ✅ P | 1.000 | resolved (F2P 59/59, P2P 44/44) | 40.7 min | 1468K | 1 |
| gemini-3.8-flash-high | 2 | ✅ P | 1.000 | resolved (F2P 59/59, P2P 44/44) | 60.4 min | 2042K | 1 |
| gemini-3.8-flash-high | 3 | ✅ P | 1.000 | resolved (F2P 59/59, P2P 44/44) | 87.8 min | 2834K | 1 |
| gemini-3.8-flash-high | 4 | ✅ P | 1.000 | resolved (F2P 59/59, P2P 44/44) | 67.4 min | 1917K | 1 |
| gemini-3.8-flash-high | 5 | ✅ P | 1.000 | resolved (F2P 59/59, P2P 44/44) | 50.7 min | 1593K | 1 |
| gemini-3.8-flash-high | 6 | ✅ P | 1.000 | resolved (F2P 59/59, P2P 44/44) | 55.5 min | 1673K | 1 |
| gemini-4-argon-high | 1 | ✅ P | 1.000 | resolved (F2P 59/59, P2P 44/44) | 44.0 min | 1171K | 1 |
| gemini-4-argon-high | 2 | ✅ P | 1.000 | resolved (F2P 59/59, P2P 44/44) | 43.6 min | 1385K | 1 |
| gemini-4-argon-high | 3 | ✅ P | 1.000 | resolved (F2P 59/59, P2P 44/44) | 41.2 min | 1373K | 1 |

### C6-03 · Terminal-Bench 2.0 / video-processing (former C6-04)

- **Rednote relevance:** Video-note understanding (detecting events in user videos)
- **Grader:** `tb2_pytest`; agent budget 3600 s

| Model | Trial | Result | Score | Details | Agent time | Tokens | Turns |
|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 1 | ✅ P | 1.000 | all 5 tests passed | 2.2 min | 216K | 9 |
| claude-opus-5-5 | 2 | ✅ P | 1.000 | all 5 tests passed | 2.1 min | 232K | 11 |
| claude-opus-5-5 | 3 | ❌ F | 0.000 | test_outputs.py::test_jump_analyzer_test_video: The test failed in the call phase due to an assertion error | 3.3 min | 277K | 12 |
| claude-opus-5-5 | 4 | ❌ F | 0.000 | test_outputs.py::test_jump_analyzer_test_video: The test failed in the call phase due to an assertion error | 3.0 min | 300K | 17 |
| claude-opus-5-5 | 5 | ❌ F | 0.000 | test_outputs.py::test_jump_analyzer_example_video: The test failed in the call phase due to an assertion error | 4.4 min | 460K | 19 |
| claude-opus-5-5 | 6 | ✅ P | 1.000 | all 5 tests passed | 2.3 min | 272K | 14 |
| gemini-3.6-flash-high | 1 | ❌ F | 0.000 | test_outputs.py::test_jump_analyzer_example_video: The test failed in the call phase due to an assertion error | 25.9 min | 448K | 1 |
| gemini-3.6-flash-high | 2 | ❌ F | 0.000 | test_outputs.py::test_jump_analyzer_test_video: The test failed in the call phase due to an assertion error | 8.8 min | 623K | 1 |
| gemini-3.6-flash-high | 3 | ❌ F | 0.000 | test_outputs.py::test_jump_analyzer_test_video: The test failed in the call phase due to an assertion error | 7.9 min | 535K | 1 |
| gemini-3.6-flash-high | 4 | ❌ F | 0.000 | test_outputs.py::test_jump_analyzer_test_video: The test failed in the call phase due to an assertion error | 17.2 min | 821K | 1 |
| gemini-3.6-flash-high | 5 | ❌ F | 0.000 | test_outputs.py::test_jump_analyzer_test_video: The test failed in the call phase due to an assertion error | 6.5 min | 444K | 1 |
| gemini-3.6-flash-high | 6 | ✅ P | 1.000 | all 5 tests passed | 7.4 min | 396K | 1 |
| gemini-3.8-flash-high | 1 | ✅ P | 1.000 | all 5 tests passed | 27.8 min | 752K | 1 |
| gemini-3.8-flash-high | 2 | ✅ P | 1.000 | all 5 tests passed | 5.5 min | 271K | 1 |
| gemini-3.8-flash-high | 3 | ✅ P | 1.000 | all 5 tests passed | 17.8 min | 542K | 1 |
| gemini-3.8-flash-high | 4 | ❌ F | 0.000 | test_outputs.py::test_jump_analyzer_test_video: The test failed in the call phase due to an assertion error | 22.7 min | 625K | 1 |
| gemini-3.8-flash-high | 5 | ❌ F | 0.000 | test_outputs.py::test_jump_analyzer_test_video: The test failed in the call phase due to an assertion error | 38.2 min | 1001K | 1 |
| gemini-3.8-flash-high | 6 | ❌ F | 0.000 | test_outputs.py::test_jump_analyzer_test_video: The test failed in the call phase due to an assertion error | 25.9 min | 1070K | 1 |
| gemini-4-argon-high | 1 | ❌ F | 0.000 | test_outputs.py::test_jump_analyzer_test_video: The test failed in the call phase due to an assertion error | 7.6 min | 364K | 1 |
| gemini-4-argon-high | 2 | ✅ P | 1.000 | all 5 tests passed | 13.2 min | 296K | 1 |
| gemini-4-argon-high | 3 | ✅ P | 1.000 | all 5 tests passed | 10.1 min | 258K | 1 |

### C6-04 · Terminal-Bench 2.0 / mteb-retrieve (former C6-06)

- **Rednote relevance:** Search / recommendation retrieval with a Chinese embedding model (bge-small-zh)
- **Grader:** `tb2_pytest`; agent budget 1800 s

| Model | Trial | Result | Score | Details | Agent time | Tokens | Turns |
|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 1 | ✅ P | 1.000 | all 2 tests passed | 4.6 min | 109K | 6 |
| claude-opus-5-5 | 2 | ✅ P | 1.000 | all 2 tests passed | 43 s | 51K | 3 |
| claude-opus-5-5 | 3 | ✅ P | 1.000 | all 2 tests passed | 3.8 min | 109K | 6 |
| claude-opus-5-5 | 4 | ✅ P | 1.000 | all 2 tests passed | 2.9 min | 88K | 5 |
| claude-opus-5-5 | 5 | ✅ P | 1.000 | all 2 tests passed | 2.2 min | 148K | 8 |
| claude-opus-5-5 | 6 | ✅ P | 1.000 | all 2 tests passed | 1.5 min | 90K | 5 |
| gemini-3.6-flash-high | 1 | ❌ F | 0.000 | test_outputs.py::test_data_matches: The test failed in the call phase due to an assertion error | 15.7 min | 751K | 1 |
| gemini-3.6-flash-high | 2 | ❌ F | 0.000 | test_outputs.py::test_data_matches: The test failed in the call phase due to an assertion error | 6.8 min | 647K | 1 |
| gemini-3.6-flash-high | 3 | ❌ F | 0.000 | test_outputs.py::test_data_matches: The test failed in the call phase due to an assertion error | 7.6 min | 726K | 1 |
| gemini-3.6-flash-high | 4 | ✅ P | 1.000 | all 2 tests passed | 6.5 min | 532K | 1 |
| gemini-3.6-flash-high | 5 | ❌ F | 0.000 | test_outputs.py::test_data_matches: The test failed in the call phase due to an assertion error | 6.7 min | 470K | 1 |
| gemini-3.6-flash-high | 6 | ❌ F | 0.000 | test_outputs.py::test_data_matches: The test failed in the call phase due to an assertion error | 9.5 min | 376K | 1 |
| gemini-3.8-flash-high | 1 | ✅ P | 1.000 | all 2 tests passed | 15.0 min | 525K | 1 |
| gemini-3.8-flash-high | 2 | ✅ P | 1.000 | all 2 tests passed | 28.3 min | 620K | 1 |
| gemini-3.8-flash-high | 3 | ✅ P | 1.000 | all 2 tests passed | 20.8 min | 439K | 1 |
| gemini-3.8-flash-high | 4 | ✅ P | 1.000 | all 2 tests passed | 11.4 min | 322K | 1 |
| gemini-3.8-flash-high | 5 | ✅ P | 1.000 | all 2 tests passed | 16.5 min | 378K | 1 |
| gemini-3.8-flash-high | 6 | ✅ P | 1.000 | all 2 tests passed | 11.1 min | 470K | 1 |
| gemini-4-argon-high | 1 | ❌ F | 0.000 | test_outputs.py::test_data_matches: The test failed in the call phase due to an assertion error | 23.2 min | 381K | 1 |
| gemini-4-argon-high | 2 | ✅ P | 1.000 | all 2 tests passed | 15.5 min | 373K | 1 |
| gemini-4-argon-high | 3 | ❌ F | 0.000 | test_outputs.py::test_data_matches: The test failed in the call phase due to an assertion error | 19.9 min | 401K | 1 |

### C6-05 · Terminal-Bench 2.0 / polyglot-c-py (former C7-01)

- **Rednote relevance:** —
- **Grader:** `tb2_pytest`; agent budget 900 s

| Model | Trial | Result | Score | Details | Agent time | Tokens | Turns |
|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 1 | ✅ P | 1.000 | all 1 tests passed | 37 s | 72K | 4 |
| claude-opus-5-5 | 2 | ✅ P | 1.000 | all 1 tests passed | 47 s | 96K | 5 |
| claude-opus-5-5 | 3 | ✅ P | 1.000 | all 1 tests passed | 37 s | 74K | 4 |
| claude-opus-5-5 | 4 | ✅ P | 1.000 | all 1 tests passed | 26 s | 35K | 2 |
| claude-opus-5-5 | 5 | ✅ P | 1.000 | all 1 tests passed | 29 s | 54K | 3 |
| claude-opus-5-5 | 6 | ❌ F | 0.000 | test_outputs.py::test_fibonacci_polyglot: The test failed in the call phase due to an assertion error | 55 s | 73K | 4 |
| gemini-3.6-flash-high | 1 | ✅ P | 1.000 | all checks passed | 1.8 min | 77K | 1 |
| gemini-3.6-flash-high | 2 | ✅ P | 1.000 | all checks passed | 2.8 min | 110K | 1 |
| gemini-3.6-flash-high | 3 | ❌ F | 0.000 | Expected only main.py.c, found: ['cmain', 'main.py.c', 'test4.py.c', 'test3.py.c', 'test2.py.c', 'test.py.c'] | 8.3 min | 238K | 1 |
| gemini-3.6-flash-high | 4 | ✅ P | 1.000 | all checks passed | 6.3 min | 156K | 1 |
| gemini-3.6-flash-high | 5 | ❌ F | 0.000 | Expected only main.py.c, found: ['cmain', 'main.py.c'] | 3.0 min | 155K | 1 |
| gemini-3.6-flash-high | 6 | ❌ F | 0.000 | test_outputs.py::test_fibonacci_polyglot: The test failed in the call phase due to an assertion error | 2.3 min | 146K | 1 |
| gemini-3.6-flash-high | 7 | ❌ F | 0.000 | test_outputs.py::test_fibonacci_polyglot: The test failed in the call phase due to an assertion error | 2.8 min | 162K | 1 |
| gemini-3.6-flash-high | 8 | ❌ F | 0.000 | test_outputs.py::test_fibonacci_polyglot: The test failed in the call phase due to an assertion error | 2.5 min | 122K | 1 |
| gemini-3.8-flash-high | 1 | ✅ P | 1.000 | all checks passed | 3.2 min | 128K | 1 |
| gemini-3.8-flash-high | 2 | ✅ P | 1.000 | all checks passed | 4.2 min | 153K | 1 |
| gemini-3.8-flash-high | 3 | ✅ P | 1.000 | all checks passed | 4.2 min | 146K | 1 |
| gemini-3.8-flash-high | 4 | ✅ P | 1.000 | all checks passed | 5.6 min | 183K | 1 |
| gemini-3.8-flash-high | 5 | ✅ P | 1.000 | all checks passed | 3.8 min | 152K | 1 |
| gemini-3.8-flash-high | 6 | ✅ P | 1.000 | all 1 tests passed | 10.6 min | 349K | 1 |
| gemini-3.8-flash-high | 7 | ✅ P | 1.000 | all 1 tests passed | 15.0 min | ? | 0 |
| gemini-3.8-flash-high | 8 | ✅ P | 1.000 | all 1 tests passed | 11.5 min | 271K | 1 |
| gemini-3.8-flash-high | 9 | ✅ P | 1.000 | all 1 tests passed | 10.3 min | 271K | 1 |
| gemini-4-argon-high | 1 | ✅ P | 1.000 | all 1 tests passed | 1.4 min | 28K | 1 |
| gemini-4-argon-high | 2 | ✅ P | 1.000 | all 1 tests passed | 1.7 min | 39K | 1 |
| gemini-4-argon-high | 3 | ✅ P | 1.000 | all 1 tests passed | 1.6 min | 30K | 1 |

### C6-06 · Terminal-Bench 2.0 / cancel-async-tasks (former C7-03)

- **Rednote relevance:** Python async backend services: bounded concurrency and graceful cancellation
- **Grader:** `tb2_pytest`; agent budget 900 s

| Model | Trial | Result | Score | Details | Agent time | Tokens | Turns |
|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 1 | ✅ P | 1.000 | all 6 tests passed | 1.5 min | 112K | 6 |
| claude-opus-5-5 | 2 | ✅ P | 1.000 | all 6 tests passed | 60 s | 73K | 5 |
| claude-opus-5-5 | 3 | ✅ P | 1.000 | all 6 tests passed | 44 s | 91K | 5 |
| claude-opus-5-5 | 4 | ✅ P | 1.000 | all 6 tests passed | 41 s | 71K | 4 |
| claude-opus-5-5 | 5 | ✅ P | 1.000 | all 6 tests passed | 41 s | 74K | 4 |
| claude-opus-5-5 | 6 | ✅ P | 1.000 | all 6 tests passed | 37 s | 91K | 6 |
| gemini-3.6-flash-high | 1 | ✅ P | 1.000 | all 6 tests passed | 3.3 min | 210K | 1 |
| gemini-3.6-flash-high | 2 | ✅ P | 1.000 | all 6 tests passed | 2.8 min | 166K | 1 |
| gemini-3.6-flash-high | 3 | ✅ P | 1.000 | all 6 tests passed | 2.9 min | 111K | 1 |
| gemini-3.6-flash-high | 4 | ❌ F | 0.000 | test_outputs.py::test_tasks_cancel_below_max_concurrent: The test failed in the call phase due to an assertion error | 4.4 min | 208K | 1 |
| gemini-3.6-flash-high | 5 | ✅ P | 1.000 | all 6 tests passed | 6.8 min | 259K | 1 |
| gemini-3.6-flash-high | 6 | ✅ P | 1.000 | all 6 tests passed | 2.0 min | 85K | 1 |
| gemini-3.8-flash-high | 1 | ✅ P | 1.000 | all 6 tests passed | 15.0 min | ? | 0 |
| gemini-3.8-flash-high | 2 | ✅ P | 1.000 | all 6 tests passed | 14.9 min | 514K | 1 |
| gemini-3.8-flash-high | 3 | ❌ F | 0.000 | test_outputs.py::test_run_py_file_exists: The test failed in the call phase due to an assertion error | 15.0 min | ? | 0 |
| gemini-3.8-flash-high | 4 | ❌ F | 0.000 | test_outputs.py::test_tasks_cancel_below_max_concurrent: The test failed in the call phase due to an assertion error | 15.0 min | ? | 0 |
| gemini-3.8-flash-high | 5 | ❌ F | 0.000 | test_outputs.py::test_tasks_cancel_below_max_concurrent: The test failed in the call phase due to an assertion error | 15.0 min | ? | 0 |
| gemini-3.8-flash-high | 6 | ✅ P | 1.000 | all 6 tests passed | 15.0 min | ? | 0 |
| gemini-4-argon-high | 1 | ❌ F | 0.000 | test_outputs.py::test_run_py_file_exists: The test failed in the call phase due to an assertion error | 15.0 min | ? | 0 |
| gemini-4-argon-high | 2 | ❌ F | 0.000 | test_outputs.py::test_run_py_file_exists: The test failed in the call phase due to an assertion error | 15.0 min | ? | 0 |
| gemini-4-argon-high | 3 | ❌ F | 0.000 | test_outputs.py::test_run_py_file_exists: The test failed in the call phase due to an assertion error | 15.0 min | ? | 0 |

### C6-07 · DeepSWE v1.1 / query-persist-restored-query-state (former C7-12)

- **Rednote relevance:** Web/H5 data layer: restoring persisted TanStack Query cache entries with their full state (offline feed restore)
- **Grader:** `deepswe`; agent budget 10800 s

| Model | Trial | Result | Score | Details | Agent time | Tokens | Turns |
|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 1 | ❌ F | 0.000 | not resolved (F2P 7/8, P2P 42/42) | 6.5 min | 1141K | 26 |
| claude-opus-5-5 | 2 | ❌ F | 0.000 | not resolved (F2P 7/8, P2P 42/42) | 9.0 min | 1487K | 29 |
| claude-opus-5-5 | 3 | ✅ P | 1.000 | resolved (F2P 8/8, P2P 42/42) | 9.1 min | 1293K | 25 |
| claude-opus-5-5 | 4 | ✅ P | 1.000 | resolved (F2P 8/8, P2P 42/42) | 14.0 min | 1380K | 27 |
| claude-opus-5-5 | 5 | ❌ F | 0.000 | not resolved (F2P 7/8, P2P 42/42) | 14.1 min | 1692K | 30 |
| claude-opus-5-5 | 6 | ✅ P | 1.000 | resolved (F2P 8/8, P2P 42/42) | 8.0 min | 1008K | 22 |
| gemini-3.6-flash-high | 1 | ❌ F | 0.000 | not resolved (F2P 8/8, P2P 41/42) | 15.7 min | 1202K | 1 |
| gemini-3.6-flash-high | 2 | ✅ P | 1.000 | resolved (F2P 8/8, P2P 42/42) | 98.7 min | 2242K | 1 |
| gemini-3.6-flash-high | 3 | ✅ P | 1.000 | resolved (F2P 8/8, P2P 42/42) | 17.7 min | 1217K | 1 |
| gemini-3.6-flash-high | 4 | ❌ F | 0.000 | not resolved (F2P 8/8, P2P 41/42) | 30.6 min | 1080K | 1 |
| gemini-3.6-flash-high | 5 | ✅ P | 1.000 | resolved (F2P 8/8, P2P 42/42) | 49.3 min | 1260K | 1 |
| gemini-3.6-flash-high | 6 | ✅ P | 1.000 | resolved (F2P 8/8, P2P 42/42) | 18.9 min | 985K | 1 |
| gemini-3.8-flash-high | 1 | ❌ F | 0.000 | not resolved (F2P 7/8, P2P 42/42) | 68.9 min | 1632K | 1 |
| gemini-3.8-flash-high | 2 | ✅ P | 1.000 | resolved (F2P 8/8, P2P 42/42) | 82.6 min | 2540K | 1 |
| gemini-3.8-flash-high | 3 | ✅ P | 1.000 | resolved (F2P 8/8, P2P 42/42) | 141.9 min | 8002K | 1 |
| gemini-3.8-flash-high | 4 | ✅ P | 1.000 | resolved (F2P 8/8, P2P 42/42) | 67.4 min | 1690K | 1 |
| gemini-3.8-flash-high | 5 | ✅ P | 1.000 | resolved (F2P 8/8, P2P 42/42) | 63.9 min | 1780K | 1 |
| gemini-3.8-flash-high | 6 | ✅ P | 1.000 | resolved (F2P 8/8, P2P 42/42) | 54.4 min | 1679K | 1 |
| gemini-4-argon-high | 1 | ✅ P | 1.000 | resolved (F2P 8/8, P2P 42/42) | 115.9 min | 1948K | 1 |
| gemini-4-argon-high | 2 | ✅ P | 1.000 | resolved (F2P 8/8, P2P 42/42) | 94.2 min | 2273K | 1 |
| gemini-4-argon-high | 3 | ✅ P | 1.000 | resolved (F2P 8/8, P2P 42/42) | 175.7 min | 2843K | 1 |

## C7 日常工作任务 — Daily work (routine engineering)

### C7-01 · DeepSWE v1.1 / drizzle-orm-window-function-builders (former C6-02)

- **Rednote relevance:** Ranking / leaderboard / analytics SQL: type-safe window functions in a TypeScript ORM (Node.js BFF services)
- **Grader:** `deepswe`; agent budget 10800 s

| Model | Trial | Result | Score | Details | Agent time | Tokens | Turns |
|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 1 | ✅ P | 1.000 | resolved (F2P 130/130, P2P 566/566) | 10.6 min | 666K | 18 |
| claude-opus-5-5 | 2 | ✅ P | 1.000 | resolved (F2P 130/130, P2P 566/566) | 5.8 min | 679K | 19 |
| claude-opus-5-5 | 3 | ✅ P | 1.000 | resolved (F2P 130/130, P2P 566/566) | 7.8 min | 689K | 19 |
| claude-opus-5-5 | 4 | ❌ F | 0.000 | not resolved (F2P 129/130, P2P 566/566) | 4.4 min | 690K | 20 |
| claude-opus-5-5 | 5 | ❌ F | 0.000 | not resolved (F2P 129/130, P2P 566/566) | 6.5 min | 696K | 19 |
| claude-opus-5-5 | 6 | ❌ F | 0.000 | not resolved (F2P 129/130, P2P 566/566) | 5.9 min | 605K | 19 |
| gemini-3.6-flash-high | 1 | ✅ P | 1.000 | resolved (F2P 130/130, P2P 566/566) | 22.8 min | 1270K | 1 |
| gemini-3.6-flash-high | 2 | ✅ P | 1.000 | resolved (F2P 130/130, P2P 566/566) | 14.0 min | 1295K | 1 |
| gemini-3.6-flash-high | 3 | ✅ P | 1.000 | resolved (F2P 130/130, P2P 566/566) | 10.2 min | 1022K | 1 |
| gemini-3.6-flash-high | 4 | ✅ P | 1.000 | resolved (F2P 130/130, P2P 566/566) | 16.0 min | 1377K | 1 |
| gemini-3.6-flash-high | 5 | ✅ P | 1.000 | resolved (F2P 130/130, P2P 566/566) | 16.8 min | 1317K | 1 |
| gemini-3.6-flash-high | 6 | ✅ P | 1.000 | resolved (F2P 130/130, P2P 566/566) | 14.3 min | 1048K | 1 |
| gemini-3.8-flash-high | 1 | ✅ P | 1.000 | resolved (F2P 130/130, P2P 566/566) | 43.6 min | 1471K | 1 |
| gemini-3.8-flash-high | 2 | ✅ P | 1.000 | resolved (F2P 130/130, P2P 566/566) | 30.3 min | 1113K | 1 |
| gemini-3.8-flash-high | 3 | ✅ P | 1.000 | resolved (F2P 130/130, P2P 566/566) | 38.2 min | 1544K | 1 |
| gemini-3.8-flash-high | 4 | ✅ P | 1.000 | resolved (F2P 130/130, P2P 566/566) | 83.3 min | 2291K | 1 |
| gemini-3.8-flash-high | 5 | ✅ P | 1.000 | resolved (F2P 130/130, P2P 566/566) | 56.3 min | 2240K | 1 |
| gemini-3.8-flash-high | 6 | ✅ P | 1.000 | resolved (F2P 130/130, P2P 566/566) | 61.7 min | 2011K | 1 |
| gemini-4-argon-high | 1 | ✅ P | 1.000 | resolved (F2P 130/130, P2P 566/566) | 20.8 min | 648K | 1 |
| gemini-4-argon-high | 2 | ✅ P | 1.000 | resolved (F2P 130/130, P2P 566/566) | 32.2 min | 1048K | 1 |
| gemini-4-argon-high | 3 | ✅ P | 1.000 | resolved (F2P 130/130, P2P 566/566) | 28.6 min | 917K | 1 |

### C7-02 · Terminal-Bench 2.0 / db-wal-recovery (former C7-04)

- **Rednote relevance:** Data reliability: recovering a corrupted SQLite WAL
- **Grader:** `tb2_pytest`; agent budget 900 s

| Model | Trial | Result | Score | Details | Agent time | Tokens | Turns |
|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 1 | ✅ P | 1.000 | all 7 tests passed | 28 s | 91K | 5 |
| claude-opus-5-5 | 2 | ✅ P | 1.000 | all 7 tests passed | 27 s | 91K | 5 |
| claude-opus-5-5 | 3 | ✅ P | 1.000 | all 7 tests passed | 18 s | 71K | 4 |
| claude-opus-5-5 | 4 | ✅ P | 1.000 | all 7 tests passed | 20 s | 71K | 4 |
| claude-opus-5-5 | 5 | ✅ P | 1.000 | all 7 tests passed | 21 s | 70K | 4 |
| claude-opus-5-5 | 6 | ✅ P | 1.000 | all 7 tests passed | 26 s | 72K | 4 |
| claude-opus-5-5 | 7 | ✅ P | 1.000 | all 7 tests passed | 21 s | 71K | 4 |
| gemini-3.6-flash-high | 1 | ✅ P | 1.000 | all 7 tests passed | 7.7 min | 112K | 1 |
| gemini-3.6-flash-high | 2 | ✅ P | 1.000 | all 7 tests passed | 1.8 min | 98K | 1 |
| gemini-3.6-flash-high | 3 | ✅ P | 1.000 | all 7 tests passed | 2.4 min | 145K | 1 |
| gemini-3.6-flash-high | 4 | ✅ P | 1.000 | all 7 tests passed | 15.0 min | ? | 0 |
| gemini-3.6-flash-high | 5 | ✅ P | 1.000 | all 7 tests passed | 6.9 min | 258K | 1 |
| gemini-3.6-flash-high | 6 | ✅ P | 1.000 | all 7 tests passed | 2.8 min | 254K | 1 |
| gemini-3.8-flash-high | 1 | ✅ P | 1.000 | all 7 tests passed | 4.8 min | 169K | 1 |
| gemini-3.8-flash-high | 2 | ✅ P | 1.000 | all 7 tests passed | 6.1 min | 240K | 1 |
| gemini-3.8-flash-high | 3 | ✅ P | 1.000 | all 7 tests passed | 6.7 min | 218K | 1 |
| gemini-3.8-flash-high | 4 | ✅ P | 1.000 | all 7 tests passed | 4.3 min | 142K | 1 |
| gemini-3.8-flash-high | 5 | ✅ P | 1.000 | all 7 tests passed | 5.7 min | 251K | 1 |
| gemini-3.8-flash-high | 6 | ✅ P | 1.000 | all 7 tests passed | 3.9 min | 166K | 1 |
| gemini-4-argon-high | 1 | ✅ P | 1.000 | all 7 tests passed | 2.9 min | 77K | 1 |
| gemini-4-argon-high | 2 | ✅ P | 1.000 | all 7 tests passed | 2.7 min | 47K | 1 |
| gemini-4-argon-high | 3 | ✅ P | 1.000 | all 7 tests passed | 2.4 min | 51K | 1 |

### C7-03 · SWE-bench Verified / django__django-15280 (former C7-05)

- **Rednote relevance:** ORM performance correctness: deferred fields when prefetching back to the parent
- **Daily-work scenario:** only()/defer() + prefetch_related() used to trim columns on hot read paths
- **Grader:** `swebench`; agent budget 1800 s

| Model | Trial | Result | Score | Details | Agent time | Tokens | Turns |
|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 1 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 85/85) | 2.4 min | 462K | 17 |
| claude-opus-5-5 | 2 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 85/85) | 1.4 min | 141K | 7 |
| claude-opus-5-5 | 3 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 85/85) | 1.5 min | 230K | 9 |
| claude-opus-5-5 | 4 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 85/85) | 1.7 min | 287K | 11 |
| claude-opus-5-5 | 5 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 85/85) | 3.7 min | 247K | 11 |
| claude-opus-5-5 | 6 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 85/85) | 28.7 min | 475K | 16 |
| gemini-3.6-flash-high | 1 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 85/85) | 7.8 min | 520K | 1 |
| gemini-3.6-flash-high | 2 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 85/85) | 13.0 min | 590K | 1 |
| gemini-3.6-flash-high | 3 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 85/85) | 9.8 min | 779K | 1 |
| gemini-3.6-flash-high | 4 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 85/85) | 7.3 min | 655K | 1 |
| gemini-3.6-flash-high | 5 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 85/85) | 7.0 min | 558K | 1 |
| gemini-3.6-flash-high | 6 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 85/85) | 12.7 min | 924K | 1 |
| gemini-3.8-flash-high | 1 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 85/85) | 30.0 min | ? | 0 |
| gemini-3.8-flash-high | 2 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 85/85) | 30.0 min | ? | 0 |
| gemini-3.8-flash-high | 3 | ❌ F | 0.000 | not resolved (F2P 0/1, P2P 83/85); first failure: The prefetched relationship is used rather than populating the reverse | 30.0 min | ? | 0 |
| gemini-3.8-flash-high | 4 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 85/85) | 21.9 min | 882K | 1 |
| gemini-3.8-flash-high | 5 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 85/85) | 19.8 min | 727K | 1 |
| gemini-3.8-flash-high | 6 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 85/85) | 18.6 min | 729K | 1 |
| gemini-4-argon-high | 1 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 85/85) | 16.1 min | 310K | 1 |
| gemini-4-argon-high | 2 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 85/85) | 18.6 min | 527K | 1 |
| gemini-4-argon-high | 3 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 85/85) | 15.2 min | 639K | 1 |

### C7-04 · SWE-bench Verified / django__django-12965 (former C7-06)

- **Rednote relevance:** DB performance regression: bulk delete issuing a subquery (MySQL lock / speed issue)
- **Daily-work scenario:** Model.objects.all().delete() performance on large tables, a routine ops concern
- **Grader:** `swebench`; agent budget 1800 s

| Model | Trial | Result | Score | Details | Agent time | Tokens | Turns |
|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 1 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 52/52) | 1.1 min | 115K | 6 |
| claude-opus-5-5 | 2 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 52/52) | 58 s | 138K | 7 |
| claude-opus-5-5 | 3 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 52/52) | 1.5 min | 135K | 7 |
| claude-opus-5-5 | 4 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 52/52) | 55 s | 115K | 6 |
| claude-opus-5-5 | 5 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 52/52) | 56 s | 114K | 6 |
| claude-opus-5-5 | 6 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 52/52) | 1.6 min | 136K | 7 |
| gemini-3.6-flash-high | 1 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 52/52) | 5.2 min | 417K | 1 |
| gemini-3.6-flash-high | 2 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 52/52) | 10.5 min | 354K | 1 |
| gemini-3.6-flash-high | 3 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 52/52) | 6.8 min | 483K | 1 |
| gemini-3.6-flash-high | 4 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 52/52) | 2.8 min | 282K | 1 |
| gemini-3.6-flash-high | 5 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 52/52) | 7.3 min | 255K | 1 |
| gemini-3.6-flash-high | 6 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 52/52) | 4.0 min | 353K | 1 |
| gemini-3.8-flash-high | 1 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 52/52) | 25.6 min | 615K | 1 |
| gemini-3.8-flash-high | 2 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 52/52) | 25.5 min | 620K | 1 |
| gemini-3.8-flash-high | 3 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 52/52) | 23.4 min | 785K | 1 |
| gemini-3.8-flash-high | 4 | ❌ F | 0.000 | not resolved (F2P 0/1, P2P 52/52); first failure: test_fast_delete_all (delete.tests.FastDeleteTests) | 30.0 min | ? | 0 |
| gemini-3.8-flash-high | 5 | ❌ F | 0.000 | not resolved (F2P 0/1, P2P 52/52); first failure: test_fast_delete_all (delete.tests.FastDeleteTests) | 30.0 min | ? | 0 |
| gemini-3.8-flash-high | 6 | ❌ F | 0.000 | not resolved (F2P 0/1, P2P 52/52); first failure: test_fast_delete_all (delete.tests.FastDeleteTests) | 30.0 min | ? | 0 |
| gemini-4-argon-high | 1 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 52/52) | 9.9 min | 238K | 1 |
| gemini-4-argon-high | 2 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 52/52) | 10.0 min | 311K | 1 |
| gemini-4-argon-high | 3 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 52/52) | 9.6 min | 228K | 1 |

### C7-05 · SWE-bench Verified / django__django-15503 (former C7-07)

- **Rednote relevance:** JSON columns on MySQL/SQLite: has_key lookups with numeric keys
- **Daily-work scenario:** Querying semi-structured note/user attributes stored in JSONField
- **Grader:** `swebench`; agent budget 1800 s

| Model | Trial | Result | Score | Details | Agent time | Tokens | Turns |
|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 1 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 78/78) | 1.9 min | 221K | 10 |
| claude-opus-5-5 | 2 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 78/78) | 56 s | 165K | 8 |
| claude-opus-5-5 | 3 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 78/78) | 48 s | 165K | 8 |
| claude-opus-5-5 | 4 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 78/78) | 1.2 min | 127K | 6 |
| claude-opus-5-5 | 5 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 78/78) | 2.0 min | 319K | 14 |
| claude-opus-5-5 | 6 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 78/78) | 1.0 min | 193K | 9 |
| gemini-3.6-flash-high | 1 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 78/78) | 11.0 min | 518K | 1 |
| gemini-3.6-flash-high | 2 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 78/78) | 9.1 min | 653K | 1 |
| gemini-3.6-flash-high | 3 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 78/78) | 5.7 min | 363K | 1 |
| gemini-3.6-flash-high | 4 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 78/78) | 24.6 min | 988K | 1 |
| gemini-3.6-flash-high | 5 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 78/78) | 6.0 min | 436K | 1 |
| gemini-3.6-flash-high | 6 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 78/78) | 6.1 min | 467K | 1 |
| gemini-3.8-flash-high | 1 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 78/78) | 26.4 min | 929K | 1 |
| gemini-3.8-flash-high | 2 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 78/78) | 23.0 min | 678K | 1 |
| gemini-3.8-flash-high | 3 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 78/78) | 22.0 min | 710K | 1 |
| gemini-3.8-flash-high | 4 | ❌ F | 0.000 | not resolved (F2P 0/2, P2P 78/78); first failure: test_has_key_number (model_fields.test_jsonfield.TestQuerying) | 30.0 min | ? | 0 |
| gemini-3.8-flash-high | 5 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 78/78) | 30.0 min | ? | 0 |
| gemini-3.8-flash-high | 6 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 78/78) | 30.0 min | ? | 0 |
| gemini-4-argon-high | 1 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 78/78) | 14.8 min | 253K | 1 |
| gemini-4-argon-high | 2 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 78/78) | 21.4 min | 280K | 1 |
| gemini-4-argon-high | 3 | ❌ F | 0.000 | not resolved (F2P 2/2, P2P 72/78); first failure: test_key_transform_annotation_expression (model_fields.test_jsonfield.TestQuerying) | 30.0 min | ? | 0 |

### C7-06 · SWE-bench Verified / django__django-14376 (former C7-08)

- **Rednote relevance:** MySQL backend maintenance: deprecated mysqlclient connection kwargs
- **Daily-work scenario:** Keeping the DB driver layer current with library upgrades
- **Grader:** `swebench`; agent budget 1800 s

| Model | Trial | Result | Score | Details | Agent time | Tokens | Turns |
|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 1 | ✅ P | 1.000 | resolved (F2P 3/3, P2P 6/6) | 39 s | 166K | 9 |
| claude-opus-5-5 | 2 | ✅ P | 1.000 | resolved (F2P 3/3, P2P 6/6) | 54 s | 167K | 9 |
| claude-opus-5-5 | 3 | ✅ P | 1.000 | resolved (F2P 3/3, P2P 6/6) | 1.1 min | 187K | 10 |
| claude-opus-5-5 | 4 | ✅ P | 1.000 | resolved (F2P 3/3, P2P 6/6) | 1.3 min | 188K | 11 |
| claude-opus-5-5 | 5 | ✅ P | 1.000 | resolved (F2P 3/3, P2P 6/6) | 1.5 min | 128K | 7 |
| claude-opus-5-5 | 6 | ✅ P | 1.000 | resolved (F2P 3/3, P2P 6/6) | 27 s | 109K | 7 |
| gemini-3.6-flash-high | 1 | ✅ P | 1.000 | resolved (F2P 3/3, P2P 6/6) | 3.4 min | 259K | 1 |
| gemini-3.6-flash-high | 2 | ✅ P | 1.000 | resolved (F2P 3/3, P2P 6/6) | 4.1 min | 281K | 1 |
| gemini-3.6-flash-high | 3 | ✅ P | 1.000 | resolved (F2P 3/3, P2P 6/6) | 3.8 min | 286K | 1 |
| gemini-3.6-flash-high | 4 | ✅ P | 1.000 | resolved (F2P 3/3, P2P 6/6) | 1.6 min | 232K | 1 |
| gemini-3.6-flash-high | 5 | ✅ P | 1.000 | resolved (F2P 3/3, P2P 6/6) | 2.0 min | 204K | 1 |
| gemini-3.6-flash-high | 6 | ✅ P | 1.000 | resolved (F2P 3/3, P2P 6/6) | 1.6 min | 186K | 1 |
| gemini-3.8-flash-high | 1 | ✅ P | 1.000 | resolved (F2P 3/3, P2P 6/6) | 13.7 min | 334K | 1 |
| gemini-3.8-flash-high | 2 | ✅ P | 1.000 | resolved (F2P 3/3, P2P 6/6) | 6.8 min | 289K | 1 |
| gemini-3.8-flash-high | 3 | ✅ P | 1.000 | resolved (F2P 3/3, P2P 6/6) | 8.9 min | 298K | 1 |
| gemini-3.8-flash-high | 4 | ❌ F | 0.000 | not resolved (F2P 0/3, P2P 6/6); first failure: test_options_non_deprecated_keys_preferred (dbshell.test_mysql.MySqlDbshellCommandTestCase) | 30.0 min | ? | 0 |
| gemini-3.8-flash-high | 5 | ✅ P | 1.000 | resolved (F2P 3/3, P2P 6/6) | 9.5 min | 352K | 1 |
| gemini-3.8-flash-high | 6 | ✅ P | 1.000 | resolved (F2P 3/3, P2P 6/6) | 7.5 min | 377K | 1 |
| gemini-4-argon-high | 1 | ✅ P | 1.000 | resolved (F2P 3/3, P2P 6/6) | 5.5 min | 205K | 1 |
| gemini-4-argon-high | 2 | ✅ P | 1.000 | resolved (F2P 3/3, P2P 6/6) | 7.8 min | 225K | 1 |
| gemini-4-argon-high | 3 | ✅ P | 1.000 | resolved (F2P 3/3, P2P 6/6) | 20.0 min | 345K | 1 |

### C7-07 · SWE-bench Verified / django__django-11532 (former C7-09)

- **Rednote relevance:** i18n: email headers crash on non-ASCII (IDN) hostnames
- **Daily-work scenario:** Unicode/i18n robustness for a Chinese-speaking user base and servers
- **Grader:** `swebench`; agent budget 1800 s

| Model | Trial | Result | Score | Details | Agent time | Tokens | Turns |
|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 1 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 148/148) | 1.8 min | 222K | 10 |
| claude-opus-5-5 | 2 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 148/148) | 1.2 min | 141K | 7 |
| claude-opus-5-5 | 3 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 148/148) | 45 s | 139K | 7 |
| claude-opus-5-5 | 4 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 148/148) | 2.2 min | 209K | 10 |
| claude-opus-5-5 | 5 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 148/148) | 1.3 min | 211K | 10 |
| claude-opus-5-5 | 6 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 148/148) | 52 s | 184K | 9 |
| gemini-3.6-flash-high | 1 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 148/148) | 5.6 min | 254K | 1 |
| gemini-3.6-flash-high | 2 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 148/148) | 5.2 min | 401K | 1 |
| gemini-3.6-flash-high | 3 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 148/148) | 6.5 min | 414K | 1 |
| gemini-3.6-flash-high | 4 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 148/148) | 9.6 min | 455K | 1 |
| gemini-3.6-flash-high | 5 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 148/148) | 4.0 min | 317K | 1 |
| gemini-3.6-flash-high | 6 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 148/148) | 3.5 min | 319K | 1 |
| gemini-3.8-flash-high | 1 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 148/148) | 12.1 min | 434K | 1 |
| gemini-3.8-flash-high | 2 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 148/148) | 20.6 min | 704K | 1 |
| gemini-3.8-flash-high | 3 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 148/148) | 19.2 min | 623K | 1 |
| gemini-3.8-flash-high | 4 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 148/148) | 27.7 min | 1081K | 1 |
| gemini-3.8-flash-high | 5 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 148/148) | 22.4 min | 731K | 1 |
| gemini-3.8-flash-high | 6 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 148/148) | 23.6 min | 707K | 1 |
| gemini-4-argon-high | 1 | ❌ F | 0.000 | not resolved (F2P 0/1, P2P 130/148); first failure: test_non_ascii_dns_non_unicode_email (mail.tests.MailTests) | 30.0 min | ? | 0 |
| gemini-4-argon-high | 2 | ❌ F | 0.000 | not resolved (F2P 0/1, P2P 130/148); first failure: test_non_ascii_dns_non_unicode_email (mail.tests.MailTests) | 30.0 min | ? | 0 |
| gemini-4-argon-high | 3 | ✅ P | 1.000 | resolved (F2P 1/1, P2P 148/148) | 25.5 min | 558K | 1 |

### C7-08 · SWE-bench Verified / psf__requests-6028 (former C7-10)

- **Rednote relevance:** Service-to-service HTTP: proxy authentication bug in requests
- **Daily-work scenario:** Calling internal/external APIs through authenticated egress proxies
- **Grader:** `swebench`; agent budget 1800 s

| Model | Trial | Result | Score | Details | Agent time | Tokens | Turns |
|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 1 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 185/185) | 37 s | 91K | 6 |
| claude-opus-5-5 | 2 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 185/185) | 20 s | 54K | 4 |
| claude-opus-5-5 | 3 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 185/185) | 17 s | 54K | 4 |
| claude-opus-5-5 | 4 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 185/185) | 44 s | 72K | 5 |
| claude-opus-5-5 | 5 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 185/185) | 34 s | 72K | 5 |
| claude-opus-5-5 | 6 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 185/185) | 27 s | 54K | 4 |
| gemini-3.6-flash-high | 1 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 185/185) | 9.4 min | 642K | 1 |
| gemini-3.6-flash-high | 2 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 185/185) | 12.0 min | 936K | 1 |
| gemini-3.6-flash-high | 3 | ❌ F | 0.000 | not resolved (F2P 0/2, P2P 185/185); first failure: tests/test_utils.py::test_prepend_scheme_if_needed[http://user:pass@example.com/path?query-http://user:pass@ | 23.4 min | 568K | 1 |
| gemini-3.6-flash-high | 4 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 185/185) | 9.9 min | 686K | 1 |
| gemini-3.6-flash-high | 5 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 185/185) | 26.6 min | 1421K | 1 |
| gemini-3.6-flash-high | 6 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 185/185) | 8.6 min | 450K | 1 |
| gemini-3.8-flash-high | 1 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 185/185) | 15.6 min | 479K | 1 |
| gemini-3.8-flash-high | 2 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 185/185) | 10.4 min | 248K | 1 |
| gemini-3.8-flash-high | 3 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 185/185) | 15.2 min | 458K | 1 |
| gemini-3.8-flash-high | 4 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 185/185) | 17.5 min | 773K | 1 |
| gemini-3.8-flash-high | 5 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 185/185) | 15.5 min | 590K | 1 |
| gemini-3.8-flash-high | 6 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 185/185) | 19.2 min | 706K | 1 |
| gemini-4-argon-high | 1 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 185/185) | 8.8 min | 211K | 1 |
| gemini-4-argon-high | 2 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 185/185) | 7.6 min | 181K | 1 |
| gemini-4-argon-high | 3 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 185/185) | 8.3 min | 238K | 1 |

### C7-09 · DeepSWE v1.1 / kgateway-consistent-hash-policy (former C7-11)

- **Rednote relevance:** API gateway traffic policy: consistent-hash (sticky) routing by header/cookie/query/source IP for cache affinity and sessions across microservices
- **Grader:** `deepswe`; agent budget 10800 s

| Model | Trial | Result | Score | Details | Agent time | Tokens | Turns |
|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 1 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 214/214) | 20.7 min | 1939K | 27 |
| claude-opus-5-5 | 2 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 214/214) | 20.6 min | 2096K | 31 |
| claude-opus-5-5 | 3 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 214/214) | 19.6 min | 2227K | 31 |
| claude-opus-5-5 | 4 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 214/214) | 24.0 min | 2589K | 31 |
| claude-opus-5-5 | 5 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 214/214) | 17.1 min | 2972K | 39 |
| claude-opus-5-5 | 6 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 214/214) | 20.1 min | 3658K | 42 |
| gemini-3.6-flash-high | 1 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 214/214) | 11.3 min | 878K | 1 |
| gemini-3.6-flash-high | 2 | ❌ F | 0.000 | not resolved (F2P 0/2, P2P 214/214) | 12.7 min | 879K | 1 |
| gemini-3.6-flash-high | 3 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 214/214) | 31.1 min | 1292K | 1 |
| gemini-3.6-flash-high | 4 | ❌ F | 0.000 | not resolved (F2P 0/2, P2P 214/214) | 33.5 min | 808K | 1 |
| gemini-3.6-flash-high | 5 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 214/214) | 19.4 min | 1680K | 1 |
| gemini-3.6-flash-high | 6 | ❌ F | 0.000 | not resolved (F2P 0/2, P2P 214/214) | 17.6 min | 868K | 1 |
| gemini-3.8-flash-high | 1 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 214/214) | 55.8 min | 3485K | 1 |
| gemini-3.8-flash-high | 2 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 214/214) | 62.9 min | 2238K | 1 |
| gemini-3.8-flash-high | 3 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 214/214) | 24.9 min | 1175K | 1 |
| gemini-3.8-flash-high | 4 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 214/214) | 38.8 min | 1401K | 1 |
| gemini-3.8-flash-high | 5 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 214/214) | 35.3 min | 1238K | 1 |
| gemini-3.8-flash-high | 6 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 214/214) | 33.5 min | 1047K | 1 |
| gemini-4-argon-high | 1 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 214/214) | 53.3 min | 1252K | 1 |
| gemini-4-argon-high | 2 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 214/214) | 46.9 min | 1293K | 1 |
| gemini-4-argon-high | 3 | ✅ P | 1.000 | resolved (F2P 2/2, P2P 214/214) | 34.8 min | 1287K | 1 |

### C7-10 · DeepSWE v1.1 / onedump-dump-encryption-pipeline (former C7-13)

- **Rednote relevance:** Data security / compliance: streaming AES-256-GCM encryption of database dump backups
- **Grader:** `deepswe`; agent budget 10800 s

| Model | Trial | Result | Score | Details | Agent time | Tokens | Turns |
|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 1 | ✅ P | 1.000 | resolved (F2P 82/82, P2P 6/6) | 3.6 min | 539K | 14 |
| claude-opus-5-5 | 2 | ✅ P | 1.000 | resolved (F2P 82/82, P2P 6/6) | 14.3 min | 789K | 19 |
| claude-opus-5-5 | 3 | ✅ P | 1.000 | resolved (F2P 82/82, P2P 6/6) | 4.9 min | 630K | 16 |
| claude-opus-5-5 | 4 | ✅ P | 1.000 | resolved (F2P 82/82, P2P 6/6) | 4.4 min | 634K | 15 |
| claude-opus-5-5 | 5 | ✅ P | 1.000 | resolved (F2P 82/82, P2P 6/6) | 3.3 min | 644K | 16 |
| claude-opus-5-5 | 6 | ✅ P | 1.000 | resolved (F2P 82/82, P2P 6/6) | 3.4 min | 492K | 12 |
| gemini-3.6-flash-high | 1 | ✅ P | 1.000 | resolved (F2P 82/82, P2P 6/6) | 16.1 min | 560K | 1 |
| gemini-3.6-flash-high | 2 | ✅ P | 1.000 | resolved (F2P 82/82, P2P 6/6) | 19.1 min | 595K | 1 |
| gemini-3.6-flash-high | 3 | ❌ F | 0.000 | not resolved (F2P 76/82, P2P 6/6) | 5.7 min | 542K | 1 |
| gemini-3.6-flash-high | 4 | ✅ P | 1.000 | resolved (F2P 82/82, P2P 6/6) | 8.5 min | 592K | 1 |
| gemini-3.6-flash-high | 5 | ✅ P | 1.000 | resolved (F2P 82/82, P2P 6/6) | 21.5 min | 667K | 1 |
| gemini-3.6-flash-high | 6 | ✅ P | 1.000 | resolved (F2P 82/82, P2P 6/6) | 17.8 min | 529K | 1 |
| gemini-3.8-flash-high | 1 | ✅ P | 1.000 | resolved (F2P 82/82, P2P 6/6) | 26.3 min | 673K | 1 |
| gemini-3.8-flash-high | 2 | ✅ P | 1.000 | resolved (F2P 82/82, P2P 6/6) | 14.4 min | 617K | 1 |
| gemini-3.8-flash-high | 3 | ✅ P | 1.000 | resolved (F2P 82/82, P2P 6/6) | 28.9 min | 698K | 1 |
| gemini-3.8-flash-high | 4 | ✅ P | 1.000 | resolved (F2P 82/82, P2P 6/6) | 14.2 min | 526K | 1 |
| gemini-3.8-flash-high | 5 | ✅ P | 1.000 | resolved (F2P 82/82, P2P 6/6) | 17.9 min | 520K | 1 |
| gemini-3.8-flash-high | 6 | ✅ P | 1.000 | resolved (F2P 82/82, P2P 6/6) | 48.3 min | 1112K | 1 |
| gemini-4-argon-high | 1 | ✅ P | 1.000 | resolved (F2P 82/82, P2P 6/6) | 41.0 min | 626K | 1 |
| gemini-4-argon-high | 2 | ✅ P | 1.000 | resolved (F2P 82/82, P2P 6/6) | 42.9 min | 454K | 1 |
| gemini-4-argon-high | 3 | ✅ P | 1.000 | resolved (F2P 82/82, P2P 6/6) | 22.9 min | 460K | 1 |

### C7-11 · DeepSWE v1.1 / geo-shapeindex-serialization (former C7-14)

- **Rednote relevance:** Location features (nearby notes, POI / local-life search): serialize the S2 spatial ShapeIndex instead of rebuilding it on every load
- **Grader:** `deepswe`; agent budget 10800 s

| Model | Trial | Result | Score | Details | Agent time | Tokens | Turns |
|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 1 | ✅ P | 1.000 | resolved (F2P 24/24, P2P 599/599) | 13.3 min | 76K | 1 |
| claude-opus-5-5 | 2 | ✅ P | 1.000 | resolved (F2P 24/24, P2P 599/599) | 21.6 min | 1795K | 30 |
| claude-opus-5-5 | 3 | ✅ P | 1.000 | resolved (F2P 24/24, P2P 599/599) | 5.7 min | 1383K | 22 |
| claude-opus-5-5 | 4 | ✅ P | 1.000 | resolved (F2P 24/24, P2P 599/599) | 5.8 min | 1107K | 21 |
| claude-opus-5-5 | 5 | ✅ P | 1.000 | resolved (F2P 24/24, P2P 599/599) | 15.2 min | 93K | 1 |
| claude-opus-5-5 | 6 | ✅ P | 1.000 | resolved (F2P 24/24, P2P 599/599) | 19.1 min | 2172K | 35 |
| gemini-3.6-flash-high | 1 | ❌ F | 0.000 | not resolved (F2P 14/24, P2P 599/599) | 11.6 min | 674K | 1 |
| gemini-3.6-flash-high | 2 | ✅ P | 1.000 | resolved (F2P 24/24, P2P 599/599) | 6.0 min | 557K | 1 |
| gemini-3.6-flash-high | 3 | ❌ F | 0.000 | not resolved (F2P 14/24, P2P 599/599) | 15.6 min | 671K | 1 |
| gemini-3.6-flash-high | 4 | ✅ P | 1.000 | resolved (F2P 24/24, P2P 599/599) | 10.3 min | 941K | 1 |
| gemini-3.6-flash-high | 5 | ❌ F | 0.000 | not resolved (F2P 14/24, P2P 599/599) | 23.8 min | 1673K | 1 |
| gemini-3.6-flash-high | 6 | ✅ P | 1.000 | resolved (F2P 24/24, P2P 599/599) | 18.4 min | 873K | 1 |
| gemini-3.8-flash-high | 1 | ✅ P | 1.000 | resolved (F2P 24/24, P2P 599/599) | 20.3 min | 1134K | 1 |
| gemini-3.8-flash-high | 2 | ✅ P | 1.000 | resolved (F2P 24/24, P2P 599/599) | 29.4 min | 1026K | 1 |
| gemini-3.8-flash-high | 3 | ✅ P | 1.000 | resolved (F2P 24/24, P2P 599/599) | 34.8 min | 1154K | 1 |
| gemini-3.8-flash-high | 4 | ✅ P | 1.000 | resolved (F2P 24/24, P2P 599/599) | 49.5 min | 1562K | 1 |
| gemini-3.8-flash-high | 5 | ✅ P | 1.000 | resolved (F2P 24/24, P2P 599/599) | 42.6 min | 1271K | 1 |
| gemini-3.8-flash-high | 6 | ✅ P | 1.000 | resolved (F2P 24/24, P2P 599/599) | 51.4 min | 1526K | 1 |
| gemini-4-argon-high | 1 | ✅ P | 1.000 | resolved (F2P 24/24, P2P 599/599) | 39.4 min | 759K | 1 |
| gemini-4-argon-high | 2 | ✅ P | 1.000 | resolved (F2P 24/24, P2P 599/599) | 40.4 min | 795K | 1 |
| gemini-4-argon-high | 3 | ✅ P | 1.000 | resolved (F2P 24/24, P2P 599/599) | 35.0 min | 682K | 1 |

## C8 高难任务 — Hard (frontier-separating)

### C8-01 · SWE-bench Verified / django__django-15957 (former C6-05)

- **Rednote relevance:** Feed / comment pagination: prefetch the top-N related rows per object (Prefetch + slice)
- **Daily-work scenario:** ORM N+1 avoidance, e.g. 'latest 3 comments for each note in a feed page'
- **Grader:** `swebench`; agent budget 1800 s

| Model | Trial | Result | Score | Details | Agent time | Tokens | Turns |
|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 1 | ✅ P | 1.000 | resolved (F2P 4/4, P2P 89/89) | 1.3 min | 258K | 11 |
| claude-opus-5-5 | 2 | ✅ P | 1.000 | resolved (F2P 4/4, P2P 89/89) | 1.3 min | 274K | 12 |
| claude-opus-5-5 | 3 | ✅ P | 1.000 | resolved (F2P 4/4, P2P 89/89) | 2.0 min | 379K | 14 |
| claude-opus-5-5 | 4 | ✅ P | 1.000 | resolved (F2P 4/4, P2P 89/89) | 1.3 min | 193K | 9 |
| claude-opus-5-5 | 5 | ✅ P | 1.000 | resolved (F2P 4/4, P2P 89/89) | 1.4 min | 209K | 10 |
| claude-opus-5-5 | 6 | ✅ P | 1.000 | resolved (F2P 4/4, P2P 89/89) | 2.1 min | 461K | 19 |
| gemini-3.6-flash-high | 1 | ❌ F | 0.000 | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_related.tests.PrefetchLimitTests) | 3.0 min | 332K | 1 |
| gemini-3.6-flash-high | 2 | ❌ F | 0.000 | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_related.tests.PrefetchLimitTests) | 3.1 min | 299K | 1 |
| gemini-3.6-flash-high | 3 | ❌ F | 0.000 | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_related.tests.PrefetchLimitTests) | 3.8 min | 282K | 1 |
| gemini-3.6-flash-high | 4 | ❌ F | 0.000 | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_related.tests.PrefetchLimitTests) | 3.2 min | 232K | 1 |
| gemini-3.6-flash-high | 5 | ❌ F | 0.000 | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_related.tests.PrefetchLimitTests) | 5.4 min | 427K | 1 |
| gemini-3.6-flash-high | 6 | ❌ F | 0.000 | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_related.tests.PrefetchLimitTests) | 6.0 min | 230K | 1 |
| gemini-3.8-flash-high | 1 | ❌ F | 0.000 | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_related.tests.PrefetchLimitTests) | 11.7 min | 446K | 1 |
| gemini-3.8-flash-high | 2 | ❌ F | 0.000 | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_related.tests.PrefetchLimitTests) | 16.6 min | 639K | 1 |
| gemini-3.8-flash-high | 3 | ❌ F | 0.000 | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_related.tests.PrefetchLimitTests) | 16.8 min | 567K | 1 |
| gemini-3.8-flash-high | 4 | ✅ P | 1.000 | resolved (F2P 4/4, P2P 89/89) | 10.7 min | 280K | 1 |
| gemini-3.8-flash-high | 5 | ✅ P | 1.000 | resolved (F2P 4/4, P2P 89/89) | 12.2 min | 350K | 1 |
| gemini-3.8-flash-high | 6 | ✅ P | 1.000 | resolved (F2P 4/4, P2P 89/89) | 14.9 min | 442K | 1 |
| gemini-4-argon-high | 1 | ❌ F | 0.000 | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_related.tests.PrefetchLimitTests) | 30.0 min | ? | 0 |
| gemini-4-argon-high | 2 | ❌ F | 0.000 | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_related.tests.PrefetchLimitTests) | 30.0 min | ? | 0 |
| gemini-4-argon-high | 3 | ❌ F | 0.000 | not resolved (F2P 0/4, P2P 89/89); first failure: test_foreignkey_reverse (prefetch_related.tests.PrefetchLimitTests) | 30.0 min | ? | 0 |

### C8-02 · FrontierSWE v2 / ffmpeg-swscale-rewrite (former C6-07)

- **Rednote relevance:** Video/image note pipeline: high-performance pixel-format conversion and scaling (thumbnails, transcoding pre-processing) with SIMD
- **Grader:** `harbor_separate` (pass at score ≥ 0.1); agent budget 7200 s

| Model | Trial | Result | Score | Details | Agent time | Tokens | Turns |
|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 1 | ❌ F | 0.096 | score=0.0955; model says 3.501x less work but native runtime is 0.343x - review | 67.2 min | 32149K | 138 |
| claude-opus-5-5 | 2 | ✅ P | 0.130 | score=0.1298; model says 4.346x less work but native runtime is 0.301x - review | 93.0 min | 41876K | 149 |
| claude-opus-5-5 | 3 | ❌ F | 0.085 | score=0.0852; model says 3.240x less work but native runtime is 0.412x - review | 82.3 min | 25872K | 123 |
| claude-opus-5-5 | 4 | ✅ P | 0.153 | score=0.1533; model says 4.909x less work but native runtime is 0.410x - review | 91.7 min | 35158K | 146 |
| claude-opus-5-5 | 5 | ✅ P | 0.145 | score=0.1450; model says 4.711x less work but native runtime is 0.291x - review | 66.6 min | 28421K | 134 |
| claude-opus-5-5 | 6 | ✅ P | 0.103 | score=0.1033; model says 3.696x less work but native runtime is 0.323x - review | 100.4 min | 23064K | 108 |
| gemini-3.6-flash-high | 1 | ❌ F | 0.000 | score=0.0000; the library is not its own implementation | 120.0 min | ? | 0 |
| gemini-3.6-flash-high | 2 | ❌ F | 0.000 | score=0.0000; the library is not its own implementation | 120.0 min | ? | 0 |
| gemini-3.6-flash-high | 3 | ❌ F | 0.000 | score=0.0000; output does not meet the accuracy bars | 120.0 min | ? | 0 |
| gemini-3.6-flash-high | 4 | ❌ F | 0.000 | score=0.0000; output does not meet the accuracy bars | 120.0 min | ? | 0 |
| gemini-3.6-flash-high | 5 | ❌ F | 0.000 | score=0.0000; output does not meet the accuracy bars | 120.0 min | ? | 0 |
| gemini-3.6-flash-high | 6 | ❌ F | 0.000 | score=0.0000; output does not meet the accuracy bars | 120.0 min | ? | 0 |
| gemini-3.8-flash-high | 1 | ❌ F | 0.000 | score=0.0000; output does not meet the accuracy bars | 119.0 min | 3923K | 1 |
| gemini-3.8-flash-high | 2 | ❌ F | 0.000 | score=0.0000; output does not meet the accuracy bars | 116.7 min | 3956K | 1 |
| gemini-3.8-flash-high | 3 | ❌ F | 0.000 | score=0.0000; output does not meet the accuracy bars | 118.4 min | 3965K | 1 |
| gemini-3.8-flash-high | 4 | ❌ F | 0.000 | score=0.0000; output does not meet the accuracy bars | 120.0 min | ? | 0 |
| gemini-3.8-flash-high | 5 | ❌ F | 0.000 | score=0.0000; output does not meet the accuracy bars | 119.9 min | 4751K | 1 |
| gemini-3.8-flash-high | 6 | ❌ F | 0.000 | score=0.0000; output does not meet the accuracy bars | 120.0 min | ? | 0 |
| gemini-4-argon-high | 1 | ❌ F | 0.000 | score=0.0000; the submission did not build | 120.0 min | ? | 0 |
| gemini-4-argon-high | 2 | ❌ F | 0.000 | score=0.0000; output does not meet the accuracy bars | 120.0 min | ? | 0 |
| gemini-4-argon-high | 3 | ✅ P | 0.160 | score=0.1604; model says 5.078x less work but native runtime is 0.550x - review | 117.1 min | 2727K | 1 |

### C8-03 · Terminal-Bench 2.0 / query-optimize (former C7-02)

- **Rednote relevance:** Backend / data-warehouse SQL performance tuning
- **Grader:** `tb2_pytest`; agent budget 900 s

| Model | Trial | Result | Score | Details | Agent time | Tokens | Turns |
|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 1 | ✅ P | 1.000 | all 6 tests passed | 15.0 min | ? | 0 |
| claude-opus-5-5 | 2 | ✅ P | 1.000 | all 6 tests passed | 12.6 min | 297K | 14 |
| claude-opus-5-5 | 3 | ❌ F | 0.000 | test_outputs.py::test_compare_golden_vs_solution_runtime: The test failed in the call phase due to an assertion error | 12.7 min | 102K | 5 |
| claude-opus-5-5 | 4 | ✅ P | 1.000 | all 6 tests passed | 15.0 min | ? | 0 |
| claude-opus-5-5 | 5 | ✅ P | 1.000 | all 6 tests passed | 12.3 min | 26K | 1 |
| claude-opus-5-5 | 6 | ❌ F | 0.000 | grader rc=None: verifier timeout 900s | 15.0 min | ? | 0 |
| gemini-3.6-flash-high | 1 | ❌ F | 0.000 | test_outputs.py::test_compare_golden_vs_solution_runtime: The test failed in the call phase due to an assertion error | 15.0 min | ? | 0 |
| gemini-3.6-flash-high | 2 | ✅ P | 1.000 | all 6 tests passed | 5.5 min | 493K | 1 |
| gemini-3.6-flash-high | 3 | ✅ P | 1.000 | all 6 tests passed | 4.7 min | 320K | 1 |
| gemini-3.6-flash-high | 4 | ✅ P | 1.000 | all 6 tests passed | 11.3 min | 636K | 1 |
| gemini-3.6-flash-high | 5 | ✅ P | 1.000 | all 6 tests passed | 7.9 min | 359K | 1 |
| gemini-3.6-flash-high | 6 | ✅ P | 1.000 | all 6 tests passed | 7.0 min | 402K | 1 |
| gemini-3.8-flash-high | 1 | ❌ F | 0.000 | test_outputs.py::test_compare_golden_vs_solution_runtime: The test failed in the call phase due to an assertion error | 15.0 min | ? | 0 |
| gemini-3.8-flash-high | 2 | ✅ P | 1.000 | all 6 tests passed | 13.8 min | 522K | 1 |
| gemini-3.8-flash-high | 3 | ✅ P | 1.000 | all 6 tests passed | 15.0 min | ? | 0 |
| gemini-3.8-flash-high | 4 | ❌ F | 0.000 | test_outputs.py::test_compare_golden_vs_solution_runtime: The test failed in the call phase due to an assertion error | 15.0 min | ? | 0 |
| gemini-3.8-flash-high | 5 | ❌ F | 0.000 | test_outputs.py::test_compare_golden_vs_solution_runtime: The test failed in the call phase due to an assertion error | 15.0 min | ? | 0 |
| gemini-3.8-flash-high | 6 | ❌ F | 0.000 | grader rc=None: verifier timeout 900s | 13.3 min | 519K | 1 |
| gemini-4-argon-high | 1 | ❌ F | 0.000 | test_outputs.py::test_compare_golden_vs_solution_runtime: The test failed in the call phase due to an assertion error | 15.0 min | ? | 0 |
| gemini-4-argon-high | 2 | ❌ F | 0.000 | test_outputs.py::test_compare_golden_vs_solution_runtime: The test failed in the call phase due to an assertion error | 15.0 min | ? | 0 |
| gemini-4-argon-high | 3 | ❌ F | 0.000 | grader rc=None: verifier timeout 900s | 15.0 min | ? | 0 |

