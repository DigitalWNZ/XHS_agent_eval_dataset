# XHS-Agent-Bench Results Report

- **Agent**: agy
- **Model**: gemini-3.8-flash-high
- **Timeout**: 30 minutes
- **Date**: 2026-09-18
- **Entries**: 34 (0 timeouts)

## Summary

| Category | Entries | Avg Score |
|----------|---------|-----------|
| C1 — Requirements Analysis | 5 | 97.0 |
| C2 — Technical Design | 5 | 99.2 |
| C3 — Code Generation | 8 | 90.5 |
| C4 — Code Review | 8 | 81.1 |
| C5a — Test Generation | 5 | 96.8 |
| C5b — Debugging | 3 | 89.0 |
| **Overall** | **34** | **91.3** |

## Detailed Results

### C1 — Requirements Analysis

| Entry | F2P | P2P | Tokens | Time | Score |
|-------|-----|-----|--------|------|-------|
| C1-01 | - | - | 19.4K | 72s | 95 |
| C1-02 | - | - | 55.3K | 177s | 100 |
| C1-03 | - | - | 463.4K | 678s | 100 |
| C1-04 | - | - | 20.0K | 75s | 90 |
| C1-05 | - | - | 23.7K | 110s | 100 |
| | | | | **avg** | **97.0** |

### C2 — Technical Design

| Entry | F2P | P2P | Tokens | Time | Score |
|-------|-----|-----|--------|------|-------|
| C2-01 | - | - | 486.0K | 396s | 100 |
| C2-02 | - | - | 36.9K | 138s | 96 |
| C2-03 | - | - | 215.1K | 267s | 100 |
| C2-04 | - | - | 744.1K | 826s | 100 |
| C2-05 | - | - | 596.9K | 654s | 100 |
| | | | | **avg** | **99.2** |

### C3 — Code Generation

| Entry | F2P | P2P | Tokens | Time | Score |
|-------|-----|-----|--------|------|-------|
| C3-01 | 23/23 | 13/13 | 695.3K | 677s | 84 |
| C3-02 | 13/13 | 13/13 | 428.6K | 652s | 90 |
| C3-03 | 13/13 | 13/13 | 473.5K | 604s | 84 |
| C3-04 | 12/12 | 13/13 | 555.8K | 505s | 92 |
| C3-05 | 14/14 | 13/13 | 818.9K | 958s | 97 |
| C3-06 | 10/10 | 82/82 | 382.7K | 529s | 89 |
| C3-07 | 8/8 | 82/82 | 652.1K | 459s | 91 |
| C3-08 | 8/8 | 82/82 | 432.4K | 455s | 97 |
| | | | | **avg** | **90.5** |

### C4 — Code Review

| Entry | Found | Recall/Precision | Tokens | Time | Score |
|-------|-------|------------------|--------|------|-------|
| C4-01 | 3/3 | 100%R / 25%P | 217.2K | 219s | 85 |
| C4-02 | 1/3 | 33%R / 8%P | 204.5K | 303s | 57 |
| C4-03 | 2/3 | 67%R / 22%P | 180.1K | 346s | 75 |
| C4-04 | 3/3 | 100%R / 100%P | 135.3K | 145s | 100 |
| C4-05 | 3/3 | 100%R / 38%P | 94.5K | 212s | 85 |
| C4-06 | 2/2 | 100%R / 33%P | 119.1K | 151s | 85 |
| C4-07 | 2/2 | 100%R / 25%P | 29.6K | 115s | 85 |
| C4-08 | 2/2 | 100%R / 33%P | 19.8K | 77s | 77 |
| | | | | **avg** | **81.1** |

### C5a — Test Generation

| Entry | Tests Passed | Coverage (D1) | Tokens | Time | Score |
|-------|-------------|---------------|--------|------|-------|
| C5a-01 | 114/114 | 30/30 | 579.9K | 548s | 100 |
| C5a-02 | 85/85 | 30/30 | 461.3K | 443s | 92 |
| C5a-03 | 82/82 | 30/30 | 534.9K | 618s | 100 |
| C5a-04 | 53/53 | 30/30 | 492.7K | 641s | 100 |
| C5a-05 | 52/52 | 30/30 | 287.9K | 350s | 92 |
| | | | | **avg** | **96.8** |

### C5b — Debugging

| Entry | F2P | P2P | Tokens | Time | Score |
|-------|-----|-----|--------|------|-------|
| C5b-01 | 1/1 | 7/7 | 405.1K | 318s | 90 |
| C5b-02 | 1/1 | 7/7 | 181.4K | 177s | 90 |
| C5b-03 | 1/1 | 8/8 | 156.7K | 143s | 87 |
| | | | | **avg** | **89.0** |

## Efficiency Metrics

| Category | Total Time | Total Tokens | Turns |
|----------|-----------|-------------|-------|
| C1 | 1,112s | 581.8K | 5 |
| C2 | 2,282s | 2.1M | 5 |
| C3 | 4,838s | 4.4M | 8 |
| C4 | 1,568s | 1.0M | 8 |
| C5a | 2,599s | 2.4M | 5 |
| C5b | 638s | 743.2K | 3 |
| **Total** | **13,037s** | **11.2M** | **34** |

## Notes

- All 34 entries completed within the 30-minute timeout (previous run at 15m had 6 timeouts)
- C3: 8/8 fully resolved (100% F2P and P2P pass rates)
- C4: 6/8 achieved 100% recall; C4-02 remains the hardest entry (33% recall)
- C5a: 100% test pass rate across all entries, full coverage (30/30 D1)
- C5b: 3/3 fully resolved (all F2P and P2P passing)
