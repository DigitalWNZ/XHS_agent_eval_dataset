#!/usr/bin/env python3
"""Campaign report: D1 (pass rate) and D2 (LLM-judge code quality) for ONE campaign, i.e. only the run folders
whose timestamp is >= --since (older runs of the same cases are ignored).

  tools/campaign_report.py --category c6 --since 20261014_1032 --out results/campaign_c6_20261014.md

D1 and D2 are reported side by side and never combined (category rubrics: "No combined score").
D1 per cell = passes / trials, snapped to the 100/67/33/0 tier; D2 = mean quality over trials the judge could grade
(trials without any code change are "na" and excluded, but are counted and listed).
"""
import argparse
import collections
import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
XHS = next(os.path.abspath(p) for p in (os.path.join(HERE, ".."), os.path.join(HERE, "..", "sources", "xhs"))
           if os.path.isdir(os.path.join(p, "dataset", "c6")))
FW = json.load(open(os.path.join(XHS, "evaluation/rubrics/coding_quality.json")))
SC = {k: v["score"] for k, v in FW["levels"].items()}
COMMON = [c["id"] for c in FW["common_items"]]
ORDER = ["claude-opus-5-5", "gemini-3.6-flash-high", "gemini-3.8-flash-high", "gemini-4-argon-high"]
TIERS = [100, 67, 33, 0]


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def f0(x):
    return "—" if x is None else f"{x:.0f}"


def load(category, since):
    rows = []
    for d in sorted(glob.glob(f"{XHS}/results/{category}_runs/*")):
        m = re.search(r"_(\d{8}_\d{6})$", d)
        if not m or m.group(1) < since or not re.search(r"_(agy|claude)_", os.path.basename(d)):
            continue
        for t in sorted(glob.glob(d + "/trial_*")):
            try:
                q = json.load(open(t + "/quality.json"))
                v = json.load(open(t + "/verdict.json"))
            except (OSError, ValueError):
                continue
            tr = json.load(open(t + "/transcript.json")) if os.path.exists(t + "/transcript.json") else []
            diff = os.path.getsize(t + "/workspace.diff") if os.path.exists(t + "/workspace.diff") else None
            patch = v.get("model_patch_bytes")
            q.update(score=float(v.get("reward") or 0), timeout=any(e.get("event") == "agent_timeout" for e in tr),
                     no_code=(diff == 0 and not patch), trial_dir=os.path.relpath(t, XHS))
            if q["no_code"]:  # rubric: no code change -> "na", excluded from D2 (the judge sometimes says "bad")
                q["quality_score"] = None
            rows.append(q)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--category", required=True, choices=["c6", "c7"])
    ap.add_argument("--since", required=True, help="campaign start, YYYYMMDD_HHMM[SS]")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    since = (a.since + "000000")[:15]
    qs = load(a.category, since)
    ents = {}
    for f in sorted(glob.glob(f"{XHS}/dataset/{a.category}/C*.json")):
        e = json.load(open(f))
        ents[e["instance_id"]] = e
    models = [m for m in ORDER if any(q["model"] == m for q in qs)] + \
             sorted({q["model"] for q in qs} - set(ORDER))
    cell = collections.defaultdict(list)
    for q in qs:
        cell[(q["entry"], q["model"])].append(q)
    C = a.category.upper()
    o = [f"# {C} campaign report (runs ≥ {a.since})\n",
         f"{len(qs)} trials, {len(models)} setups, rubric v{FW['version']}. **D1** = pass rate on the source benchmark's "
         "hidden tests (cell tier snapped to 100/67/33/0). **D2** = code quality from the LLM judge (Claude Opus 5.5): "
         "Readability, Maintainability, Robustness + 1–2 case items, perfect 1 / accept 0.6 / bad 0, quality = 100 × mean. "
         "D1 and D2 are not combined. Trials with no code change cannot be judged (na) and are excluded from D2.\n",
         "## Per case (passes/trials · D2 quality)\n",
         "| Case | Task | " + " | ".join(models) + " |", "|---|---|" + "---|" * len(models)]
    for eid in sorted(ents):
        row = []
        for m in models:
            ts = cell.get((eid, m), [])
            if not ts:
                row.append("—")
                continue
            p = sum(bool(t["verifier_pass"]) for t in ts)
            flag = "".join([f" ⚠{sum(not t['valid'] for t in ts)}" if any(not t["valid"] for t in ts) else "",
                            f" ∅{sum(t['no_code'] for t in ts)}" if any(t["no_code"] for t in ts) else ""])
            row.append(f"{p}/{len(ts)} · {f0(mean([t['quality_score'] for t in ts]))}{flag}")
        task = ents[eid].get("maps_to_journey", "").replace("External: ", "")
        o.append(f"| {eid} | {task[:60]} | " + " | ".join(row) + " |")
    o.append("\n∅n = n trials ended with no code change (all were agent timeouts); ⚠n = invalid (validity audit).\n")

    o.append("## Per model\n")
    o.append("| Model | Trials | Passes | Pass rate | D1 (mean case tier) | D2 quality (graded trials) | No-code trials | Timeouts | Invalid |")
    o.append("|---|---|---|---|---|---|---|---|---|")
    for m in models:
        ts = [q for q in qs if q["model"] == m]
        tiers = []
        for eid in ents:
            c = cell.get((eid, m), [])
            if c:
                tiers.append(min(TIERS, key=lambda t: abs(t - 100 * sum(bool(x["verifier_pass"]) for x in c) / len(c))))
        graded = [t["quality_score"] for t in ts if t["quality_score"] is not None]
        p = sum(bool(t["verifier_pass"]) for t in ts)
        o.append(f"| {m} | {len(ts)} | {p} | {100 * p / len(ts):.0f}% | {f0(mean(tiers))} | {f0(mean(graded))} (n={len(graded)}) | "
                 f"{sum(t['no_code'] for t in ts)} | {sum(t['timeout'] for t in ts)} | {sum(not t['valid'] for t in ts)} |")

    o.append("\n## D2 item scores per model (mean over judged items, 0–100)\n")
    o.append("| Model | Readability | Maintainability | Robustness | Case-specific | Quality |")
    o.append("|---|---|---|---|---|---|")
    for m in models:
        ts = [q for q in qs if q["model"] == m]
        col = lambda pred: f0(mean([100 * SC[i["level"]] if SC.get(i["level"]) is not None else None
                                    for t in ts if not t["no_code"] for i in t["items"] if pred(i)]))
        o.append(f"| {m} | " + " | ".join(col(lambda i, k=k: i["id"] == k) for k in COMMON)
                 + f" | {col(lambda i: not i['common'])} | {f0(mean([t['quality_score'] for t in ts]))} |")

    o.append("\n## Quality among passing vs failing trials\n")
    o.append("| Model | D2 on passing trials | D2 on failing trials (with code) |")
    o.append("|---|---|---|")
    for m in models:
        ts = [q for q in qs if q["model"] == m]
        o.append(f"| {m} | {f0(mean([t['quality_score'] for t in ts if t['verifier_pass']]))} | "
                 f"{f0(mean([t['quality_score'] for t in ts if not t['verifier_pass']]))} |")

    o.append("\n## Validity findings\n")
    flags = [(q, fl) for q in qs for fl in q.get("validity_flags", [])]
    o.append("none" if not flags else "\n".join(
        f"- {q['trial_dir']}: {fl['check']} ({fl['status']}) — {fl['basis'][:200]}" for q, fl in flags))

    o.append("\n## Per trial\n")
    o.append("| Case | Model | Trial | Pass | Score | D2 | Notes | Verifier reason |")
    o.append("|---|---|---|---|---|---|---|---|")
    for q in sorted(qs, key=lambda q: (q["entry"], models.index(q["model"]), q["trial"])):
        notes = ", ".join(n for n, c in (("timeout", q["timeout"]), ("no code", q["no_code"]),
                                         ("invalid", not q["valid"])) if c)
        o.append(f"| {q['entry']} | {q['model']} | {q['trial'][-1]} | {'✅' if q['verifier_pass'] else '❌'} | "
                 f"{q['score']:.3g} | {f0(q['quality_score'])} | {notes} | {(q.get('verifier_reason') or '')[:110].replace('|', '/')} |")
    out = a.out if os.path.isabs(a.out) else os.path.join(XHS, a.out)
    open(out, "w").write("\n".join(o) + "\n")
    print(f"wrote {out}: {len(qs)} trials")


if __name__ == "__main__":
    main()
