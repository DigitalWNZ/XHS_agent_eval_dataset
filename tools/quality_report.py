#!/usr/bin/env python3
"""Reports for rubric v3 (pass/fail + LLM-judge code quality) from the per-trial quality.json files.

  tools/quality_report.py results    -> results/README_quality.md      (pass rate, quality, items, validity flags)
  tools/quality_report.py rubric     -> guide/coding_rubric_items.md   (the 3 common + each case's items)
"""
import collections
import glob
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from idmap import current_id  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
XHS = next(p for p in (os.path.join(HERE, ".."), os.path.join(HERE, "..", "sources", "xhs"))
           if os.path.isdir(os.path.join(p, "dataset", "c6")))
XHS = os.path.abspath(XHS)
FW = json.load(open(os.path.join(XHS, "evaluation/rubrics/coding_quality.json")))
MODEL_ORDER = ["claude-opus-5-5", "gemini-3.6-flash-high", "gemini-3.8-flash-high", "gemini-4-argon-high"]
SC = {k: v["score"] for k, v in FW["levels"].items()}
COMMON = [c["id"] for c in FW["common_items"]]


def load_entries():
    out = {}
    for f in sorted(glob.glob(f"{XHS}/dataset/c[678]/C*.json")):
        e = json.load(open(f))
        e["rub"] = json.load(open(os.path.join(XHS, e.get("task_rubric", f"evaluation/rubrics/tasks/{e['instance_id']}.json"))))
        out[e["instance_id"]] = e
    return out


def load_quality():
    out = []
    for f in sorted(glob.glob(f"{XHS}/results/c[678]_runs/*/trial_*/quality.json")):
        q = json.load(open(f))
        if q.get("agent") in ("agy", "claude") and q.get("rubric_version", "").startswith("3"):
            q["entry"] = current_id(q["entry"], q["run"])  # recorded ID -> current ID (results/id_mapping.json)
            out.append(q)
    return out


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def f1(x):
    return "—" if x is None else f"{x:.0f}"


def results_report():
    ents, qs = load_entries(), load_quality()
    models = [m for m in MODEL_ORDER if any(q["model"] == m for q in qs)]
    cell = collections.defaultdict(list)
    for q in qs:
        cell[(q["entry"], q["model"])].append(q)
    o = ["# Results: pass rate and code quality (C6 / C7 / C8)\n",
         f"Rubric `evaluation/rubrics/coding_quality.json` v{FW['version']}. **Pass** = the source benchmark's hidden tests "
         "(unchanged). **Quality** = LLM judge (Claude Opus 5.5) on Readability, Maintainability, Robustness + 1–2 "
         "case-specific items; perfect 1 / accept 0.6 / bad 0; quality = 100 × mean. Trials with a confirmed validity "
         "finding (access to hidden tests / solutions, or test tampering) are counted as **invalid** (⚠); provisional "
         "findings are only listed below.\n",
         "## Overview (pass · quality)\n",
         "| Entry | Source / task | " + " | ".join(models) + " |", "|---|---|" + "---|" * len(models)]
    cat = collections.defaultdict(list)
    for eid in sorted(ents):
        row = []
        for m in models:
            ts = cell.get((eid, m), [])
            if not ts:
                row.append("—"); continue
            cat[(eid[:2], m)] += ts
            inv = sum(not t["valid"] for t in ts)
            row.append(f"{sum(t['verifier_pass'] for t in ts)}/{len(ts)} · {f1(mean([t['quality_score'] for t in ts]))}"
                       + (f" ⚠{inv} invalid" if inv else ""))
        o.append(f"| {eid} | {ents[eid]['maps_to_journey'].replace('External: ', '')} | " + " | ".join(row) + " |")
    for c in ("C6", "C7", "C8"):
        row = []
        for m in models:
            ts = cat.get((c, m), [])
            inv = sum(not t["valid"] for t in ts)
            row.append(f"**{sum(t['verifier_pass'] for t in ts)}/{len(ts)} · {f1(mean([t['quality_score'] for t in ts]))}**"
                       + (f" ⚠{inv}" if inv else ""))
        o.append(f"| **{c} total** | | " + " | ".join(row) + " |")
    o.append("\n## Item scores (mean over trials, 0–100)\n")
    o.append("| Category | Model | 可读性 Readability | 可维护性 Maintainability | 健壮性 Robustness | Case-specific | Quality |")
    o.append("|---|---|---|---|---|---|---|")
    for c in ("C6", "C7", "C8"):
        for m in models:
            ts = cat.get((c, m), [])
            col = lambda pred: f1(mean([100 * SC[i["level"]] if SC[i["level"]] is not None else None
                                        for t in ts for i in t["items"] if pred(i)]))
            o.append(f"| {c} | {m} | " + " | ".join(col(lambda i, k=k: i["id"] == k) for k in COMMON)
                     + f" | {col(lambda i: not i['common'])} | {f1(mean([t['quality_score'] for t in ts]))} |")
    o.append("\n## Invalid trials (validity audit; re-run recommended)\n")
    o.append("| Run / trial | Entry | Model | Hidden tests | Flag | Evidence |")
    o.append("|---|---|---|---|---|---|")
    n = 0
    for q in qs:
        for fl in q["validity_flags"]:
            n += 1
            o.append(f"| {q['run']}/{q['trial']} | {q['entry']} | {q['model']} | {'pass' if q['verifier_pass'] else 'fail'} | "
                     f"{fl['check']} ({fl['status']}) | {fl['basis'][:150].replace('|', '/')} |")
    if not n:
        o.append("| — | | | | | none |")
    sample = [(q, i) for q in qs for i in q["items"] if i["level"] != "na"]
    sample = random.Random(20261014).sample(sample, max(1, len(sample) // 20)) if sample else []
    o.append("\n## Human spot-check sample (5% of judge answers)\n")
    o.append("Record corrections in `results/quality_overrides.json`, then re-run `evaluation/quality_grader.py --all` "
             "(judge answers are cached) and this report.\n")
    o.append("| Run / trial | Item | Level | Judge evidence |")
    o.append("|---|---|---|---|")
    for q, i in sample:
        o.append(f"| {q['run']}/{q['trial']} | {i['id']} | {i['level']} | {i['evidence'][:150].replace('|', '/')} |")
    out = os.path.join(XHS, "results", "README_quality.md")
    open(out, "w").write("\n".join(o) + "\n")
    print(f"wrote {out}: {len(qs)} trials, {n} validity flags")


def rubric_doc():
    ents = load_entries()
    cl = lambda s: (s or "—").replace("|", "/").replace("\n", " ")
    o = ["# Code-quality rubric per case (C6 / C7 / C8)\n",
         "Pass/fail is unchanged (the source benchmark's hidden tests). Code quality is graded by one LLM judge "
         "(Claude Opus 5.5) on the 3 common items below plus each case's 1–2 items. Levels: perfect 1.0 / accept 0.6 / "
         "bad 0; quality = 100 × mean.\n",
         "## Common items (every case; meanings from C3 D3–D5)\n",
         "| Item | 评分项 | Question | Perfect | Accept | Bad | Caps |", "|---|---|---|---|---|---|---|"]
    for c in FW["common_items"]:
        k = c["criteria"]
        o.append(f"| {c['id']} | {c['name_zh']} | {cl(c['question'])} | {cl(k['perfect'])} | {cl(k['accept'])} | {cl(k['bad'])} | {cl(' '.join(c.get('caps', [])))} |")
    for cat, title in (("C6", "C6 区分度任务 Discriminative"), ("C7", "C7 日常工作任务 Daily work"), ("C8", "C8 高难任务 Hard")):
        o.append(f"\n## {title}: case-specific items\n")
        o.append("| Case | Item | 评分项 | Question | Perfect | Accept | Bad |")
        o.append("|---|---|---|---|---|---|---|")
        for eid in sorted(k for k in ents if k.startswith(cat)):
            for it in ents[eid]["rub"]["case_items"]:
                k = it["criteria"]
                o.append(f"| {eid} | {it['id']}<br>{it['name']} | {it['name_zh']} | {cl(it['question'])} | {cl(k.get('perfect'))} | "
                         f"{cl(k.get('accept'))} | {cl(k.get('bad'))} |")
    out = os.path.join(XHS, "guide", "coding_rubric_items.md")
    open(out, "w").write("\n".join(o) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    (rubric_doc if (sys.argv[1:] or ["results"])[0] == "rubric" else results_report)()
