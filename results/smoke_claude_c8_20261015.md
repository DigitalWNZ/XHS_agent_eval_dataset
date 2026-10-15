# C8 campaign report (runs ≥ 20261015_0845, < 20261015_0946)

3 trials, 1 setups, rubric v3.0. **D1** = pass rate on the source benchmark's hidden tests (cell tier snapped to 100/67/33/0). **D2** = code quality from the LLM judge (Claude Opus 5.5): Readability, Maintainability, Robustness + 1–2 case items, perfect 1 / accept 0.6 / bad 0, quality = 100 × mean. D1 and D2 are not combined. Trials with no code change cannot be judged (na) and are excluded from D2.

## Per case (passes/trials · D2 quality)

| Case | Former ID | Task | claude-opus-5-5 |
|---|---|---|---|
| C8-01 | C6-05 | SWE-bench Verified / django__django-15957 | 1/1 · 100 |
| C8-02 | C6-07 | FrontierSWE v2 / ffmpeg-swscale-rewrite | 1/1 · 68 |
| C8-03 | C7-02 | Terminal-Bench 2.0 / query-optimize | 0/1 · 45 |

∅n = n trials ended with no code change (all were agent timeouts); ⚠n = invalid (validity audit).

## Per model

| Model | Trials | Passes | Pass rate | D1 (mean case tier) | D2 quality (graded trials) | No-code trials | Timeouts | Invalid |
|---|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 3 | 2 | 67% | 67 | 71 (n=3) | 0 | 0 | 0 |

## Run metrics per model (mean per trial)

Agent time = wall time of the agent run (capped by the budget). Tool calls are counted from the trajectory. Tokens = input + output as reported by the agent CLI; agy reports no usage when it hits its time budget, so for those trials the per-step usage in the saved trajectory is summed (marked * in the per-trial table; only available for runs after the partial-trajectory fix). Turns: Claude Code reports turns; agy always reports 1 per session, so use tool calls to compare.

| Model | Agent time (min) | Tool calls | Tokens (K) | Turns (Claude) | Cost USD (Claude, total) |
|---|---|---|---|---|---|
| claude-opus-5-5 | 26 | 49 | 9950 | 50 | 11.84 |

## Run metrics per case (mean per trial: agent time min · tool calls · tokens K)

Same definitions as above, averaged over the trials of one case and model (— = no data, e.g. agy timeouts before the partial-trajectory fix).

| Case | Task | claude-opus-5-5 |
|---|---|---|
| C8-01 | SWE-bench Verified / django__django-15957 | 1.7 · 13 · 358 |
| C8-02 | FrontierSWE v2 / ffmpeg-swscale-rewrite | 64 · 128 · 29347 |
| C8-03 | Terminal-Bench 2.0 / query-optimize | 13 · 6 · 146 |

## D2 item scores per model (mean over judged items, 0–100)

| Model | Readability | Maintainability | Robustness | Case-specific | Quality |
|---|---|---|---|---|---|
| claude-opus-5-5 | 53 | 73 | 73 | 80 | 71 |

## Quality among passing vs failing trials

| Model | D2 on passing trials | D2 on failing trials (with code) |
|---|---|---|
| claude-opus-5-5 | 84 | 45 |

## Validity findings

none

## Per trial

Item levels: P = perfect (100), A = accept (60), B = bad (0), – = not applicable. Read / Maint / Robust = the 3 common items; Case = the case-specific item(s) in order.

| Case | Model | Trial | Pass | Score | D2 | Read | Maint | Robust | Case | Time (min) | Tool calls | Tokens (K) | Notes | Verifier reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C8-01 | claude-opus-5-5 | 0 | ✅ | 1 | 100 | P | P | P | P | 2 | 13 | 358 |  | resolved (F2P 4/4, P2P 89/89) |
| C8-02 | claude-opus-5-5 | 0 | ✅ | 0.114 | 68 | A | A | A | A,P | 64 | 128 | 29347 |  | score=0.1140; model says 3.959x less work but native runtime is 0.372x - review |
| C8-03 | claude-opus-5-5 | 0 | ❌ | 0 | 45 | B | A | A | A | 13 | 6 | 146 |  | grader rc=None: verifier timeout 900s |
