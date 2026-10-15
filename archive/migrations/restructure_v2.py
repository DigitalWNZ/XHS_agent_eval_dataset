#!/usr/bin/env python3
"""Second restructure of the containerized categories (2026-10-15), based on the full campaign of 2026-10-14
(claude-opus-5-5, gemini-3.6-flash-high, gemini-3.8-flash-high, gemini-4-argon-high; 3 trials each; isolated
harness; results/campaign_c6_20261014.md and results/campaign_c7_20261014.md):

  C6 = 区分度任务 Discriminative: 7 cases where the four setups' pass rates differ but no single setup dominates
  C7 = 日常工作任务 Daily work: 11 cases most setups solve (pass rates 85-100%); D2 quality separates them
  C8 = 高难任务 Hard: 3 cases only the strongest setup solved reliably (or most setups timed out)

Entries are renumbered within each category. `former_id` becomes the ID used until now (2026-10-14 layout) and
`id_history` records every ID the entry had. Env folders move to dataset/<cat>/envs/<new id>/ and task rubrics to
evaluation/rubrics/tasks/<new id>.json (case-item IDs renamed too). Raw run folders are NOT renamed:
results/id_mapping.json gets a second epoch, so tools/idmap.py and quality_grader map recorded IDs by run time.
Each entry also gets discrimination.campaign_2026_10_14 (pass counts and mean D2 per setup).

Run from the XHS repo root:  python3 tools/restructure_v2.py
"""
import glob
import json
import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
DS = ROOT / "dataset"
TASKS = ROOT / "evaluation" / "rubrics" / "tasks"
RUNS_BEFORE = "20261015_072400"   # runs recorded before this use the 2026-10-14 IDs

C6 = ["C6-01", "C6-03", "C6-04", "C6-06", "C7-01", "C7-03", "C7-12"]
C7 = ["C6-02", "C7-04", "C7-05", "C7-06", "C7-07", "C7-08", "C7-09", "C7-10", "C7-11", "C7-13", "C7-14"]
C8 = ["C6-05", "C6-07", "C7-02"]
CATS = {
    "C6": dict(ids=C6, rubric="c6_discriminative", zh="区分度任务（容器化，模型区分）",
               en="Discriminative Tasks (Containerized, Model-Separating)"),
    "C7": dict(ids=C7, rubric="c7_daily", zh="日常工作任务（容器化，贴近日常）",
               en="Daily-Work Tasks (Containerized, Rednote-Relevant)"),
    "C8": dict(ids=C8, rubric="c8_hard", zh="高难任务（容器化，强模型区分）",
               en="Hard Tasks (Containerized, Frontier-Separating)"),
}
NOTES = {
    "C6": "Cases where the four setups' pass rates differ but no single setup dominates (campaign 2026-10-14: "
          "claude-opus-5-5 62%, gemini-3.8 57%, gemini-4-argon 57%, gemini-3.6 29%). Use C6 to rank models.",
    "C7": "Rednote-relevant daily-work cases most setups solve (campaign 2026-10-14 pass rates 85-100%); "
          "D2 (code quality) does most of the separating here.",
    "C8": "Hard cases only the strongest setup solved reliably, or where most setups ran out of time "
          "(campaign 2026-10-14: claude-opus-5-5 8/9, gemini-3.6 3/9, gemini-4-argon 1/9, gemini-3.8 0/9).",
}
mapping = {old: f"{cat}-{i + 1:02d}" for cat, c in CATS.items() for i, old in enumerate(c["ids"])}
assert len(mapping) == 21 and len(set(mapping.values())) == 21
ID_RE = re.compile(r"\bC[678]-\d\d\b")

# campaign numbers per (2026-10-14 ID, model), from the per-trial quality.json files
camp = {}
for f in glob.glob(str(ROOT / "results/c[67]_runs/*/trial_*/quality.json")):
    run = pathlib.Path(f).parents[1].name
    ts = re.findall(r"(\d{8}_\d{6})", run)
    if not ts or ts[-1] < "20261014_103200" or not re.search(r"_(agy|claude)_", run):
        continue
    q = json.load(open(f))
    camp.setdefault((q["entry"], q["model"]), []).append(q)

# 1) load entries (2026-10-14 layout)
old = {}
for f in sorted(DS.glob("c[678]/C*.json")):
    e = json.loads(f.read_text())
    old[e["instance_id"]] = (f, e)
assert set(old) == set(mapping), set(old) ^ set(mapping)

# 2) stage env folders and task rubrics (old and new IDs overlap)
stage = DS / "_restructure_stage"
shutil.rmtree(stage, ignore_errors=True)
(stage / "tasks").mkdir(parents=True)
for oid, (f, e) in old.items():
    src = DS / oid[:2].lower() / "envs" / oid
    if src.exists():
        shutil.move(str(src), stage / oid)
    t = TASKS / f"{oid}.json"
    if t.exists():
        shutil.move(str(t), stage / "tasks" / f"{oid}.json")
    f.unlink()


def rewrite(obj, pairs):
    if isinstance(obj, str):
        for a, b in pairs:
            obj = obj.replace(a, b)
        return obj
    if isinstance(obj, list):
        return [rewrite(x, pairs) for x in obj]
    if isinstance(obj, dict):
        return {k: rewrite(v, pairs) for k, v in obj.items()}
    return obj


manifest_entries = {c: [] for c in CATS}
for oid, (f, e) in old.items():
    new = mapping[oid]
    cat = new[:2]
    pairs = [(f"dataset/{oid[:2].lower()}/envs/{oid}", f"dataset/{cat.lower()}/envs/{new}"),
             (f"evaluation/rubrics/tasks/{oid}.json", f"evaluation/rubrics/tasks/{new}.json")]
    e = rewrite(e, pairs)
    hist = {"2026-10-13": e.get("former_id", oid), "2026-10-14": oid}
    e = {"instance_id": new, "former_id": oid, "id_history": hist,
         **{k: v for k, v in e.items() if k not in ("instance_id", "former_id", "id_history")}}
    e["category"] = cat
    e["category_name"] = CATS[cat]["zh"]
    e["evaluation_rubric"] = f"evaluation/rubrics/{CATS[cat]['rubric']}.json"
    d = e.setdefault("discrimination", {})
    d.pop("selected_for_c6", None)
    d["selected_for_category"] = f"{cat} in the 2026-10-15 restructure, from the 2026-10-14 campaign (see below)"
    stats = {}
    for (eid, m), ts in sorted(camp.items()):
        if eid == oid:
            qs = [t["quality_score"] for t in ts if t["quality_score"] is not None]
            stats[m] = {"pass": f"{sum(bool(t['verifier_pass']) for t in ts)}/{len(ts)}",
                        "mean_quality": round(sum(qs) / len(qs)) if qs else None}
    d["campaign_2026_10_14"] = {"per_setup": stats, "id_in_campaign": oid,
                                "report": f"results/campaign_{oid[:2].lower()}_20261014.md"}
    (DS / cat.lower() / "envs").mkdir(parents=True, exist_ok=True)
    if (stage / oid).exists():
        shutil.move(str(stage / oid), DS / cat.lower() / "envs" / new)
    slug = f.name.split("_", 1)[1]
    out = DS / cat.lower() / f"{new}_{slug}"
    out.write_text(json.dumps(e, indent=2, ensure_ascii=False) + "\n")
    manifest_entries[cat].append({"instance_id": new, "former_id": oid, "file": str(out.relative_to(ROOT)),
                                  "maps_to_journey": e["maps_to_journey"]})
    tsrc = stage / "tasks" / f"{oid}.json"
    if tsrc.exists():
        tr = json.loads(tsrc.read_text())
        tr = json.loads(ID_RE.sub(lambda m_: new if m_.group(0) == oid else m_.group(0), json.dumps(tr, ensure_ascii=False)))
        tr = {"format": tr.get("format", "v3"), "instance_id": new, "former_id": oid, "id_history": hist,
              **{k: v for k, v in tr.items() if k not in ("format", "instance_id", "former_id", "id_history")}}
        tr["category"] = cat
        (TASKS / f"{new}.json").write_text(json.dumps(tr, indent=2, ensure_ascii=False) + "\n")
shutil.rmtree(stage)

# 3) category rubrics: C8 starts as a copy of C6 (same D1/D2 definition)
rub_dir = ROOT / "evaluation" / "rubrics"
c6r = json.loads((rub_dir / "c6_discriminative.json").read_text())
for cat, c in CATS.items():
    p = rub_dir / f"{c['rubric']}.json"
    r = json.loads(p.read_text()) if p.exists() else json.loads(json.dumps(c6r))
    r["category"] = cat
    r["category_name"] = c["en"]
    r["category_name_zh"] = c["zh"].split("（")[0]
    notes = [n for n in r.get("score_synthesis", {}).get("notes", [])
             if not n.startswith(("C6 entries were picked", "C7 entries", "C8 entries", "Each entry keeps"))]
    notes += [f"{cat} entries (2026-10-15 restructure): {NOTES[cat]}",
              "Each entry keeps its previous ID in former_id and all IDs in id_history (see results/id_mapping.json)."]
    r.setdefault("score_synthesis", {})["notes"] = notes
    p.write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n")

# 4) manifest
m_path = DS / "manifest.json"
man = json.loads(m_path.read_text())
base = {k: v for k, v in man["categories"]["C6"].items() if k in ("method", "dimensions", "in_composite")}
for cat, c in CATS.items():
    man["categories"][cat] = {"name": c["en"], "name_zh": c["zh"], **base, "note": NOTES[cat],
                              "entry_count": len(manifest_entries[cat]),
                              "entries": sorted(manifest_entries[cat], key=lambda x: x["instance_id"])}
man["total_entries"] = sum(v["entry_count"] for v in man["categories"].values())
m_path.write_text(json.dumps(man, indent=2, ensure_ascii=False) + "\n")

# 5) id mapping: add an epoch (older runs are mapped through every later epoch, in order)
idp = ROOT / "results" / "id_mapping.json"
im = json.loads(idp.read_text())
epochs = im.get("epochs") or [{"runs_before": im["runs_before"], "old_to_new": im["old_to_new"],
                               "note": "2026-10-14 restructure (old C6/C7/C8 -> C6/C7)"}]
epochs.append({"runs_before": RUNS_BEFORE, "old_to_new": dict(sorted(mapping.items())),
               "note": "2026-10-15 restructure (C6/C7 -> C6/C7/C8)"})
idp.write_text(json.dumps({
    "description": "Raw run folders keep the entry ID used when they ran. For a run with folder timestamp ts, "
                   "apply old_to_new of every epoch with ts < runs_before, in order, to get the current ID.",
    "epochs": epochs}, indent=2, ensure_ascii=False) + "\n")
for o, n in sorted(mapping.items(), key=lambda kv: kv[1]):
    print(f"{o} -> {n}")
print("manifest total:", man["total_entries"])
