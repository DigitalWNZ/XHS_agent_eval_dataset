#!/usr/bin/env python3
"""Summarize agent (agy / claude) results per entry/model (P/F per trial) for C6/C7/C8 run dirs -> markdown."""
import collections
import glob
import json
import os
import sys

XHS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sources", "xhs")
since = sys.argv[1] if len(sys.argv) > 1 else ""  # e.g. 20261013_13 to only count new runs
res = collections.defaultdict(list)
THRESH = {}
reasons = collections.defaultdict(list)
for f in sorted(glob.glob(f"{XHS}/results/c[678]_runs/*_*_*/trial_*/verdict.json")):
    run = f.split("/")[-3]
    entry, agent, model, day, tod = run.split("_")[:5]
    if agent not in ("agy", "claude"):  # skip gold/empty validation runs
        continue
    if since and f"{day}_{tod}" < since:
        continue
    v = json.load(open(f))
    if entry not in THRESH:  # continuous-score entries (e.g. C6-08) pass at pass_threshold
        ef = glob.glob(f"{XHS}/dataset/c*/{entry}_*.json")
        THRESH[entry] = float(json.load(open(ef[0]))["verification"].get("pass_threshold", 1.0)) if ef else 1.0
    score = float(v.get("reward", 0) or 0)
    ok = score >= THRESH[entry]
    res[(entry, model)].append("P" if ok else "F")
    if not ok:
        reasons[(entry, model)].append((v.get("reason") or "")[:90])
models = sorted({m for _, m in res})
entries = sorted({e for e, _ in res})
out = ["| Entry | " + " | ".join(models) + " |", "|---|" + "---|" * len(models)]
tot = collections.Counter()
for e in entries:
    cells = []
    for m in models:
        t = res.get((e, m), [])
        tot[(m, "p")] += t.count("P")
        tot[(m, "n")] += len(t)
        cells.append(f"{''.join(t)} ({t.count('P')}/{len(t)})" if t else "—")
    out.append(f"| {e} | " + " | ".join(cells) + " |")
out.append("| **Total** | " + " | ".join(
    f"**{tot[(m, 'p')]}/{tot[(m, 'n')]}**" for m in models) + " |")
out.append("\nFailure reasons:")
for k, rs in sorted(reasons.items()):
    out.append(f"- {k[0]} {k[1]}: " + " ; ".join(rs))
print("\n".join(out))
