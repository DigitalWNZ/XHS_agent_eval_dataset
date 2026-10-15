#!/usr/bin/env python3
"""Campaign report: D1 (pass rate) and D2 (LLM-judge code quality) for ONE campaign, i.e. only the run folders
whose timestamp is >= --since (older runs of the same cases are ignored). Entries are reported under their
current IDs/categories (recorded IDs are mapped via results/id_mapping.json, see tools/idmap.py).

  tools/campaign_report.py --category c6 --since 20261014_1032 --until 20261015_0724 --out results/campaign_c6_20261014.md
  (the 2026-10-14 campaign: C6 cases ran from 10:32, C7 cases from 15:54; use --since 20261014_1032 for any category)

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

import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from idmap import XHS, current_id  # noqa: E402  (maps the ID recorded by a run to the current ID)
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


LEVEL = {"perfect": "P", "accept": "A", "bad": "B", "na": "–"}
_METRICS = None


def run_metrics():
    """trial_dir -> {elapsed_seconds, num_turns, usage} from the run summaries results/c*_<agent>_<model>_<ts>.json."""
    global _METRICS
    if _METRICS is None:
        _METRICS = {}
        for f in glob.glob(f"{XHS}/results/c[678]_*_*_*.json"):
            try:
                d = json.load(open(f))
            except (OSError, ValueError):
                continue
            for r in d.get("entries", []) if isinstance(d, dict) else []:
                for t in r.get("trials", []):
                    if t.get("trial_dir"):
                        _METRICS[os.path.abspath(t["trial_dir"])] = t
    return _METRICS


def trajectory_stats(path):
    """(tool calls, summed step tokens) from trajectory.jsonl: Claude stream-json tool_use blocks, or agy
    step_update tool steps (agy step tokens are used only when the run summary has no usage, e.g. timeouts)."""
    calls, toks = 0, 0
    if not os.path.exists(path):
        return None, None
    for line in open(path, errors="replace"):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "assistant":
            calls += sum(1 for x in e.get("message", {}).get("content", []) if x.get("type") == "tool_use")
        su = e.get("step_update") or {}
        if su.get("state") == "DONE":
            if su.get("step_type") == "tool":
                calls += 1
            u = su.get("usage") or {}
            toks += (u.get("input_tokens") or 0) + (u.get("output_tokens") or 0)
    return calls, toks or None


def load(category, since, until="99999999_999999"):
    """Trials of the current category `category` (runs of any results/c*_runs dir, IDs mapped to current)."""
    rows = []
    for d in sorted(glob.glob(f"{XHS}/results/c[678]_runs/*")):
        m = re.search(r"_(\d{8}_\d{6})$", d)
        if not m or not (since <= m.group(1) < until) or not re.search(r"_(agy|claude)_", os.path.basename(d)):
            continue
        for t in sorted(glob.glob(d + "/trial_*")):
            try:
                q = json.load(open(t + "/quality.json"))
                v = json.load(open(t + "/verdict.json"))
            except (OSError, ValueError):
                continue
            q["recorded_entry"] = q["entry"]
            q["entry"] = current_id(q["entry"], os.path.basename(d))
            if q["entry"][:2].lower() != category:
                continue
            tr = json.load(open(t + "/transcript.json")) if os.path.exists(t + "/transcript.json") else []
            diff = os.path.getsize(t + "/workspace.diff") if os.path.exists(t + "/workspace.diff") else None
            patch = v.get("model_patch_bytes")
            q.update(score=float(v.get("reward") or 0), timeout=any(e.get("event") == "agent_timeout" for e in tr),
                     no_code=(diff == 0 and not patch), trial_dir=os.path.relpath(t, XHS))
            if q["no_code"]:  # rubric: no code change -> "na", excluded from D2 (the judge sometimes says "bad")
                q["quality_score"] = None
            mt = run_metrics().get(os.path.abspath(t), {})
            usage = mt.get("usage") or {}
            calls, step_toks = trajectory_stats(t + "/trajectory.jsonl")
            q.update(elapsed=mt.get("elapsed_seconds"), turns=mt.get("num_turns"), tool_calls=calls,
                     tokens=usage.get("total_tokens"), tokens_partial=False, cost=usage.get("cost_usd"))
            if q["tokens"] is None and step_toks:
                q.update(tokens=step_toks, tokens_partial=True)
            rows.append(q)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--category", required=True, choices=["c6", "c7", "c8"])
    ap.add_argument("--since", required=True, help="campaign start, YYYYMMDD_HHMM[SS]")
    ap.add_argument("--until", default="99999999_999999", help="exclusive end, YYYYMMDD_HHMM[SS] (default: no end)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    since = (a.since + "000000")[:15]
    until = (a.until + "000000")[:15]
    qs = load(a.category, since, until)
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
    o = [f"# {C} campaign report (runs ≥ {a.since}" + (f", < {a.until}" if a.until[0] != "9" else "") + ")\n",
         f"{len(qs)} trials, {len(models)} setups, rubric v{FW['version']}. **D1** = pass rate on the source benchmark's "
         "hidden tests (cell tier snapped to 100/67/33/0). **D2** = code quality from the LLM judge (Claude Opus 5.5): "
         "Readability, Maintainability, Robustness + 1–2 case items, perfect 1 / accept 0.6 / bad 0, quality = 100 × mean. "
         "D1 and D2 are not combined. Trials with no code change cannot be judged (na) and are excluded from D2.\n",
         "## Per case (passes/trials · D2 quality)\n",
         "| Case | Former ID | Task | " + " | ".join(models) + " |", "|---|---|---|" + "---|" * len(models)]
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
        o.append(f"| {eid} | {ents[eid].get('former_id', '')} | {task[:60]} | " + " | ".join(row) + " |")
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

    o.append("\n## Run metrics per model (mean per trial)\n")
    o.append("Agent time = wall time of the agent run (capped by the budget). Tool calls are counted from the trajectory. "
             "Tokens = input + output as reported by the agent CLI; agy reports no usage when it hits its time budget, "
             "so for those trials the per-step usage in the saved trajectory is summed (marked * in the per-trial table; "
             "only available for runs after the partial-trajectory fix). Turns: Claude Code reports turns; agy always "
             "reports 1 per session, so use tool calls to compare.\n")
    o.append("| Model | Agent time (min) | Tool calls | Tokens (K) | Turns (Claude) | Cost USD (Claude, total) |")
    o.append("|---|---|---|---|---|---|")
    for m in models:
        ts = [q for q in qs if q["model"] == m]
        cost = sum(t["cost"] or 0 for t in ts)
        turns = mean([t["turns"] for t in ts]) if m.startswith("claude") else None
        o.append(f"| {m} | {f0(mean([t['elapsed'] / 60 if t['elapsed'] else None for t in ts]))} | "
                 f"{f0(mean([t['tool_calls'] for t in ts]))} | {f0(mean([t['tokens'] / 1000 if t['tokens'] else None for t in ts]))} | "
                 f"{f0(turns)} | {f'{cost:.2f}' if cost else '—'} |")
    o.append("\n## Run metrics per case (mean per trial: agent time min · tool calls · tokens K)\n")
    o.append("Same definitions as above, averaged over the trials of one case and model (— = no data, e.g. agy "
             "timeouts before the partial-trajectory fix).\n")
    o.append("| Case | Task | " + " | ".join(models) + " |")
    o.append("|---|---|" + "---|" * len(models))
    for eid in sorted(ents):
        row = []
        for m in models:
            ts = cell.get((eid, m), [])
            if not ts:
                row.append("—")
                continue
            tm = mean([t["elapsed"] / 60 if t["elapsed"] else None for t in ts])
            tc = mean([t["tool_calls"] for t in ts])
            tk = mean([t["tokens"] / 1000 if t["tokens"] else None for t in ts])
            row.append(f"{(f'{tm:.1f}' if tm is not None and tm < 10 else f0(tm))} · {f0(tc)} · {f0(tk)}")
        task = ents[eid].get("maps_to_journey", "").replace("External: ", "")
        o.append(f"| {eid} | {task[:45]} | " + " | ".join(row) + " |")
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
    o.append("Item levels: P = perfect (100), A = accept (60), B = bad (0), – = not applicable. "
             "Read / Maint / Robust = the 3 common items; Case = the case-specific item(s) in order.\n")
    o.append("| Case | Model | Trial | Pass | Score | D2 | Read | Maint | Robust | Case | Time (min) | Tool calls | Tokens (K) | Notes | Verifier reason |")
    o.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for q in sorted(qs, key=lambda q: (q["entry"], models.index(q["model"]), q["trial"])):
        notes = ", ".join(n for n, c in (("timeout", q["timeout"]), ("no code", q["no_code"]),
                                         ("invalid", not q["valid"])) if c)
        lv = {i["id"]: ("–" if q["no_code"] else LEVEL.get(i["level"], "?")) for i in q.get("items", [])}
        case = ",".join(v for k, v in lv.items() if k not in COMMON) or "—"
        tok = "—" if not q["tokens"] else f"{q['tokens'] / 1000:.0f}{'*' if q['tokens_partial'] else ''}"
        o.append(f"| {q['entry']} | {q['model']} | {q['trial'][-1]} | {'✅' if q['verifier_pass'] else '❌'} | "
                 f"{q['score']:.3g} | {f0(q['quality_score'])} | {lv.get('READABILITY', '—')} | {lv.get('MAINTAINABILITY', '—')} | "
                 f"{lv.get('ROBUSTNESS', '—')} | {case} | {f0(q['elapsed'] / 60) if q['elapsed'] else '—'} | "
                 f"{'—' if q['tool_calls'] is None else q['tool_calls']} | {tok} | {notes} | "
                 f"{(q.get('verifier_reason') or '')[:90].replace('|', '/')} |")
    out = a.out if os.path.isabs(a.out) else os.path.join(XHS, a.out)
    open(out, "w").write("\n".join(o) + "\n")
    print(f"wrote {out}: {len(qs)} trials")


if __name__ == "__main__":
    main()
