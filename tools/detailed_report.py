#!/usr/bin/env python3
"""Detailed per-case report (every entry x model x trial) for the C6/C7/C8 agent runs -> markdown.

Reads the run summaries (results/c{6,7,8}_<agent>_<model>_<ts>.json), keeping only trials whose
run_dir still exists under results/c*_runs/ (invalidated runs were moved to *_runs_invalid/ and
are therefore excluded). Runs from before the C6/C7 restructure are mapped to the current IDs via
results/id_mapping.json. Usage: detailed_report.py > runs/detailed_results.md
"""
import collections
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from idmap import XHS, current_id  # noqa: E402

AGENTS = {"agy": "Antigravity", "claude": "Claude Code"}
MODEL_ORDER = ["claude-opus-5-5", "gemini-3.6-flash-high", "gemini-3.8-flash-high", "gemini-4-argon-high"]
CATS = ("C6", "C7", "C8")
CAT_NAMES = {"C6": "C6 区分度任务 — Discriminative (model-differentiating)",
             "C7": "C7 日常工作任务 — Daily work (routine engineering)",
             "C8": "C8 高难任务 — Hard (frontier-separating)"}

entries = {}
for f in glob.glob(f"{XHS}/dataset/c[678]/C*.json"):
    e = json.load(open(f))
    entries[e["instance_id"]] = e

trials = collections.defaultdict(list)  # (entry, model) -> [trial dicts]
for f in sorted(glob.glob(f"{XHS}/results/c[678]_*_*_*.json")):
    d = json.load(open(f))
    if d.get("agent") not in AGENTS:
        continue
    for r in d.get("entries", []):
        rd = r.get("run_dir", "")
        if not rd or not os.path.isdir(rd) or "_invalid" in rd:
            continue
        eid = current_id(r["instance_id"], rd)
        for i, t in enumerate(r.get("trials", [])):
            tdir = t.get("trial_dir") or os.path.join(rd, f"trial_{i}")
            if not os.path.exists(os.path.join(tdir, "verdict.json")):
                continue
            trials[(eid, r["model"])].append(
                {**t, "agent": d["agent"], "run": os.path.basename(rd), "tdir": tdir})


def thresh(eid):
    return float(entries[eid]["verification"].get("pass_threshold", 1.0)) if eid in entries else 1.0


def fmt_tokens(u):
    n = (u or {}).get("total_tokens") or 0
    return f"{n / 1000:.0f}K" if n else "?"


def fmt_time(s):
    s = float(s or 0)
    return f"{s / 60:.1f} min" if s >= 60 else f"{s:.0f} s"


def source(e):
    return e["maps_to_journey"].replace("External: ", "")


out = []
models = [m for m in MODEL_ORDER if any(k[1] == m for k in trials)]
out.append("# Detailed results: C6 (discriminative) / C7 (daily work) / C8 (hard) agent runs (all runs)\n")
out.append("Agents: Antigravity (agy) with gemini-3.6-flash-high / gemini-3.8-flash-high / gemini-4-argon-high; "
           "Claude Code with claude-opus-5-5 (Vertex). All recorded runs are pooled (several campaigns, so trial "
           "counts differ; for one campaign use tools/campaign_report.py). P = pass, F = fail. C8-02 has a "
           "continuous score in [0, 1] and passes at >= 0.1. Runs invalidated by harness bugs are excluded (see "
           "results/*_runs_invalid/); trials that later failed the validity audit are NOT excluded here "
           "(see results/README_quality.md).\n")
out.append("Entry IDs follow the current (2026-10-15) layout; *Former ID* is the ID before that restructure; runs are "
           "mapped from the ID they "
           "recorded (raw run folders keep it; mapping in results/id_mapping.json).\n")
out.append("Columns: *Details* = grader verdict (F2P/P2P = fail-to-pass / pass-to-pass tests passed); "
           "*Agent time* = agent wall time (budget-capped); *Tokens* = input+output incl. cache; "
           "*Turns* as reported by the agent CLI (agy reports 1 per session; when agy hits its time "
           "budget, tokens/turns are not reported and show ? / 0).\n")

# Overview
out.append("## Overview\n")
out.append("| Entry | Former ID | Source / task | " + " | ".join(models) + " |")
out.append("|---|---|---|" + "---|" * len(models))
cat_tot = collections.defaultdict(lambda: [0, 0])
for cat in CATS:
    for eid in sorted(k for k in entries if k.startswith(cat)):
        row = []
        for m in models:
            ts = trials.get((eid, m), [])
            p = sum(1 for t in ts if float(t.get("score", t.get("reward", 0)) or 0) >= thresh(eid))
            cat_tot[(cat, m)][0] += p
            cat_tot[(cat, m)][1] += len(ts)
            row.append(f"{p}/{len(ts)}" if ts else "—")
        out.append(f"| {eid} | {entries[eid].get('former_id', '')} | {source(entries[eid])} | "
                   + " | ".join(row) + " |")
    out.append(f"| **{cat} total** | | | " + " | ".join(
        f"**{cat_tot[(cat, m)][0]}/{cat_tot[(cat, m)][1]} "
        f"({100 * cat_tot[(cat, m)][0] / max(cat_tot[(cat, m)][1], 1):.0f}%)**" for m in models) + " |")
allp = {m: sum(cat_tot[(c, m)][0] for c in CATS) for m in models}
alln = {m: sum(cat_tot[(c, m)][1] for c in CATS) for m in models}
out.append("| **All** | | | " + " | ".join(
    f"**{allp[m]}/{alln[m]} ({100 * allp[m] / max(alln[m], 1):.0f}%)**" for m in models) + " |\n")

# Per entry
for cat in CATS:
    out.append(f"## {CAT_NAMES[cat]}\n")
    for eid in sorted(k for k in entries if k.startswith(cat)):
        e = entries[eid]
        out.append(f"### {eid} · {source(e)} (former {e.get('former_id', '—')})\n")
        out.append(f"- **Rednote relevance:** {e.get('rednote_relevance', '—')}")
        if e.get("daily_work_scenario"):
            out.append(f"- **Daily-work scenario:** {e['daily_work_scenario']}")
        v = e["verification"]
        extra = f" (pass at score ≥ {v['pass_threshold']})" if "pass_threshold" in v else ""
        out.append(f"- **Grader:** `{v['type']}`{extra}; agent budget "
                   f"{e['environment'].get('agent_timeout_sec', '?')} s\n")
        out.append("| Model | Trial | Result | Score | Details | Agent time | Tokens | Turns |")
        out.append("|---|---|---|---|---|---|---|---|")
        for m in models:
            for i, t in enumerate(trials.get((eid, m), [])):
                sc = float(t.get("score", t.get("reward", 0)) or 0)
                ok = sc >= thresh(eid)
                reason = (t.get("reason") or "").replace("|", "/").replace("\n", " ")[:160]
                out.append(f"| {m} | {i + 1} | {'✅ P' if ok else '❌ F'} | "
                           f"{sc:.3f} | {reason} | {fmt_time(t.get('elapsed_seconds'))} | "
                           f"{fmt_tokens(t.get('usage'))} | {t.get('num_turns', '?')} |")
        out.append("")
print("\n".join(out))
