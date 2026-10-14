#!/usr/bin/env python3
"""Summarize agent (agy / claude) results per entry/model (P/F per trial) for C6/C7 run dirs -> markdown.

Pre-restructure runs (old C6/C7/C8 IDs) are mapped to the current IDs via results/id_mapping.json.
Usage: summarize_agy.py [SINCE_TS]   (e.g. 20261013_13 to only count newer runs)
"""
import collections
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from idmap import XHS, current_id, run_ts  # noqa: E402

since = sys.argv[1] if len(sys.argv) > 1 else ""
res = collections.defaultdict(list)
THRESH = {}
reasons = collections.defaultdict(list)
for f in sorted(glob.glob(f"{XHS}/results/c[678]_runs/*_*_*/trial_*/verdict.json")):
    run = f.split("/")[-3]
    rec_entry, agent, model = run.split("_")[:3]
    if agent not in ("agy", "claude"):  # skip gold/empty validation runs
        continue
    if since and run_ts(run) < since:
        continue
    entry = current_id(rec_entry, run)
    v = json.load(open(f))
    if entry not in THRESH:  # continuous-score entries (e.g. C6-07) pass at pass_threshold
        ef = glob.glob(f"{XHS}/dataset/c[67]/{entry}_*.json")
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
for cat in sorted({e[:2] for e in entries}):
    for e in (x for x in entries if x.startswith(cat)):
        cells = []
        for m in models:
            t = res.get((e, m), [])
            tot[(cat, m, "p")] += t.count("P")
            tot[(cat, m, "n")] += len(t)
            cells.append(f"{''.join(t)} ({t.count('P')}/{len(t)})" if t else "—")
        out.append(f"| {e} | " + " | ".join(cells) + " |")
    out.append(f"| **{cat} total** | " + " | ".join(
        f"**{tot[(cat, m, 'p')]}/{tot[(cat, m, 'n')]}**" for m in models) + " |")
out.append("| **Total** | " + " | ".join(
    f"**{sum(v for k, v in tot.items() if k[1] == m and k[2] == 'p')}/"
    f"{sum(v for k, v in tot.items() if k[1] == m and k[2] == 'n')}**" for m in models) + " |")
out.append("\nFailure reasons:")
for k, rs in sorted(reasons.items()):
    out.append(f"- {k[0]} {k[1]}: " + " ; ".join(rs))
print("\n".join(out))
