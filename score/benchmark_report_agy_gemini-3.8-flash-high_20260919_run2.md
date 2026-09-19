# XHS-Agent-Bench — Benchmark Report

**Date:** 2026-09-19
**Agent:** agy
**Model:** gemini-3.8-flash-high
**Timeout:** 30 minutes per entry

## Summary

| Category | Entries | Avg Score | Pct |
|----------|---------|-----------|-----|
| C1 — Requirements Analysis | 5 | 93.0/100 | 93.0% |
| C2 — Technical Design | 5 | 99.6/100 | 99.6% |
| C3 — Code Generation | 8 | 91.5/100 | 91.5% |
| C4 — Code Review | 8 | 84.6/100 | 84.6% |
| C5a — Test Generation | 5 | 100.0/100 | 100.0% |
| C5b — Debugging | 3 | 88.7/100 | 88.7% |
| **OVERALL** | **34** | | **92.9%** |

**Wall time:** 3.5h | **Total tokens:** 13.7M | **Entries:** 34

---

## C1 — Requirements Analysis (0/100 auto/judge)

| Entry | Completeness (25) | Edge Cases (25) | Clarifying Qs (20) | Spec Quality (15) | NFRs (15) | Score | Time | Tokens |
|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| C1-01 | 20 | 20 | 20 | 15 | 15 | 90 | 61s | 17.2K |
| C1-02 | 20 | 20 | 20 | 15 | 15 | 90 | 89s | 22.0K |
| C1-03 | 20 | 20 | 20 | 15 | 15 | 90 | 62s | 16.9K |
| C1-04 | 25 | 20 | 20 | 15 | 15 | 95 | 107s | 23.5K |
| C1-05 | 25 | 25 | 20 | 15 | 15 | 100 | 242s | 275.2K |
| **Avg** | | | | | | **93.0** | | |

---

## C2 — Technical Design (0/100 auto/judge)

| Entry | Architecture (25) | API Design (20) | Data Model (20) | Constraints (20) | Trade-offs (15) | Score | Time | Tokens |
|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| C2-01 | 25 | 20 | 20 | 20 | 15 | 100 | 498s | 771.4K |
| C2-02 | 25 | 20 | 20 | 20 | 15 | 99 | 589s | 760.8K |
| C2-03 | 25 | 20 | 20 | 20 | 15 | 100 | 690s | 720.6K |
| C2-04 | 25 | 20 | 20 | 20 | 15 | 99 | 648s | 668.8K |
| C2-05 | 25 | 20 | 20 | 20 | 15 | 100 | 506s | 524.5K |
| **Avg** | | | | | | **99.6** | | |

---

## C3 — Code Generation (70/30 auto/judge)

| Entry | F2P | P2P | Functional C (50) | Regression S (20) | Readability (7) | Maintainabil (7) | Robustness (7) | Convention A (5) | Change Minim (4) | Score | Time | Tokens |
|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| C3-01 | 23/23 | 13/13 | 50 | 20 | 5 | 4 | 5 | 5 | 4 | 93 | 531s | 362.7K |
| C3-02 | 13/13 | 13/13 | 50 | 20 | 5 | 4 | 7 | 5 | 3 | 94 | 617s | 680.1K |
| C3-03 | 13/13 | 13/13 | 50 | 20 | 5 | 4 | 5 | 4 | 3 | 91 | 747s | 833.4K |
| C3-04 | 12/12 | 13/13 | 50 | 20 | — | — | — | — | — | 70† | 448s | 505.1K |
| C3-05 | 14/14 | 13/13 | 50 | 20 | 7 | 7 | 7 | 5 | 4 | 100 | 651s | 692.8K |
| C3-06 | 10/10 | 82/82 | 50 | 20 | 7 | 7 | 7 | 4 | 3 | 98 | 513s | 810.7K |
| C3-07 | 8/8 | 82/82 | 50 | 20 | 5 | 5 | 5 | 4 | 3 | 92 | 394s | 526.5K |
| C3-08 | 8/8 | 82/82 | 50 | 20 | 5 | 5 | 7 | 4 | 3 | 94 | 336s | 258.4K |
| **Avg** | | | | | | | | | | **91.5** | | |

> † C3-04: LLM judge timed out after 3 attempts; score reflects auto dimensions only (D1+D2 = 70/70). All F2P/P2P tests passed.

---

## C4 — Code Review (50/50 auto/judge)

| Entry | Recall | Prec | TP | VNP | FP | Localization (20) | Category & S (15) | Explanation  (15) | Score | Time | Tokens |
|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| C4-01 | 100% | 100% | 3 | 9 | 0 | 20 | 15 | 15 | 100 | 290s | 139.0K |
| C4-02 | 0% | 0% | 0 | 0 | 0 | 4 | 3 | 3 | 20 | 377s | 434.5K |
| C4-03 | 67% | 89% | 2 | 6 | 1 | 20 | 15 | 15 | 90 | 302s | 314.3K |
| C4-04 | 100% | 70% | 3 | 4 | 3 | 20 | 12 | 15 | 92 | 356s | 301.5K |
| C4-05 | 100% | 78% | 3 | 4 | 2 | 20 | 15 | 15 | 95 | 97s | 60.4K |
| C4-06 | 100% | 62% | 2 | 3 | 3 | 20 | 15 | 15 | 95 | 110s | 51.5K |
| C4-07 | 100% | 38% | 2 | 1 | 5 | 20 | 15 | 15 | 85 | 192s | 103.6K |
| C4-08 | 100% | 100% | 2 | 5 | 0 | 20 | 15 | 15 | 100 | 79s | 18.2K |
| **Avg** | | | | | | | | | **84.6** | | |

> C4-02: Agent produced 0 findings (missed all 3 planted defects).

## C5a — Test Generation (50/50 auto/judge)

| Entry | Written | Passed | Rate | Assertion Qu (18) | Edge Case Co (14) | Test Indepen (11) | Convention A (7) | Score | Time | Tokens |
|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| C5a-01 | 66 | 66 | 100% | 18 | 14 | 11 | 7 | 100 | 602s | 871.6K |
| C5a-02 | 84 | 84 | 100% | 18 | 14 | 11 | 7 | 100 | 541s | 643.5K |
| C5a-03 | 96 | 96 | 100% | 18 | 14 | 11 | 7 | 100 | 577s | 639.2K |
| C5a-04 | 53 | 53 | 100% | 18 | 14 | 11 | 7 | 100 | 587s | 675.7K |
| C5a-05 | 60 | 60 | 100% | 18 | 14 | 11 | 7 | 100 | 222s | 274.7K |
| **Avg** | | | | | | | | **100.0** | | |

---

## C5b — Debugging (70/30 auto/judge)

| Entry | F2P | P2P | Root Cause I (20) | Fix Correctn (50) | Fix Minimali (20) | Explanation  (10) | Score | Time | Tokens |
|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| C5b-01 | 1/1 | 7/7 | 20 | 50 | 12 | 8 | 90 | 217s | 347.1K |
| C5b-02 | 1/1 | 7/7 | 20 | 50 | 12 | 8 | 90 | 97s | 166.6K |
| C5b-03 | 1/1 | 8/8 | 20 | 50 | 8 | 8 | 86 | 130s | 149.5K |
| **Avg** | | | | | | | **88.7** | | |

---

*Generated on 2026-09-19 11:10*
