#!/usr/bin/env python3
"""One-time restructure of the containerized categories (2026-10-14):

  C6 = 区分度任务 Discriminative tasks: the 7 cases that best separated the models
       (agy + gemini-3.6-flash / gemini-3.8-flash, Claude Code + opus-5-5; 3 trials each)
  C7 = 日常工作任务 Daily-work tasks: the other 14 (Rednote-relevant, low model separation)
  C8 is dissolved into C6/C7.

Entries are renumbered within each category; the previous ID is kept as `former_id`.
Environment folders move to dataset/<cat>/envs/<new id>/ and every path in the entry is rewritten.
Raw run folders under results/ are NOT renamed; results/id_mapping.json maps the IDs used by runs
made before the restructure (run timestamp < RUNS_BEFORE) to the new IDs.

Run from the XHS repo root:  python3 tools/restructure_c6_c7.py
"""
import json
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[2]  # archive/migrations -> repo root
DS = ROOT / "dataset"
RUNS_BEFORE = "20261014_070000"

C6 = ["C6-06", "C8-03", "C8-02", "C6-04", "C7-01", "C6-02", "C6-08"]  # rank order
C7 = ["C6-01", "C6-03", "C6-05", "C6-07", "C7-02", "C7-03", "C7-04", "C7-05", "C7-06",
      "C7-07", "C8-01", "C8-04", "C8-05", "C8-06"]
NAMES = {
    "C6": ("区分度任务（容器化，模型区分）", "Discriminative Tasks (Containerized, Model-Separating)"),
    "C7": ("日常工作任务（容器化，贴近日常）", "Daily-Work Tasks (Containerized, Rednote-Relevant)"),
}
mapping = {old: f"C6-{i + 1:02d}" for i, old in enumerate(C6)}
mapping.update({old: f"C7-{i + 1:02d}" for i, old in enumerate(C7)})
assert len(mapping) == 21 and len(set(mapping.values())) == 21

# 1) load all current entries (old layout)
old_entries = {}
for f in sorted(DS.glob("c[678]/C*.json")):
    e = json.loads(f.read_text())
    old_entries[e["instance_id"]] = (f, e)
assert set(old_entries) == set(mapping), set(old_entries) ^ set(mapping)

# 2) move env folders via a staging dir (old and new IDs overlap)
stage = DS / "_restructure_stage"
if stage.exists():
    shutil.rmtree(stage)
stage.mkdir()
for old, (f, e) in old_entries.items():
    src = DS / old[:2].lower() / "envs" / old
    if src.exists():
        shutil.move(str(src), stage / old)
    f.unlink()


def rewrite(obj, old_prefix, new_prefix):
    if isinstance(obj, str):
        return obj.replace(old_prefix, new_prefix)
    if isinstance(obj, list):
        return [rewrite(x, old_prefix, new_prefix) for x in obj]
    if isinstance(obj, dict):
        return {k: rewrite(v, old_prefix, new_prefix) for k, v in obj.items()}
    return obj


manifest_entries = {"C6": [], "C7": []}
for old, (f, e) in old_entries.items():
    new = mapping[old]
    cat = new[:2]
    old_prefix = f"dataset/{old[:2].lower()}/envs/{old}"
    new_prefix = f"dataset/{cat.lower()}/envs/{new}"
    e = rewrite(e, old_prefix, new_prefix)
    e = {"instance_id": new, "former_id": old, **{k: v for k, v in e.items() if k != "instance_id"}}
    e["category"] = cat
    e["category_name"] = NAMES[cat][0]
    e["evaluation_rubric"] = f"evaluation/rubrics/{cat.lower()}_{'discriminative' if cat == 'C6' else 'daily'}.json"
    (DS / cat.lower() / "envs").mkdir(parents=True, exist_ok=True)
    if (stage / old).exists():
        shutil.move(str(stage / old), DS / cat.lower() / "envs" / new)
    slug = f.name.split("_", 1)[1]  # keep the task slug from the old file name
    out = DS / cat.lower() / f"{new}_{slug}"
    out.write_text(json.dumps(e, indent=2, ensure_ascii=False) + "\n")
    manifest_entries[cat].append({"instance_id": new, "former_id": old,
                                  "file": str(out.relative_to(ROOT)),
                                  "maps_to_journey": e["maps_to_journey"]})
shutil.rmtree(stage)
if (DS / "c8").exists() and not any((DS / "c8").rglob("*.json")):
    shutil.rmtree(DS / "c8")

# 3) manifest
m_path = DS / "manifest.json"
m = json.loads(m_path.read_text())
m["categories"].pop("C8", None)
m["categories"]["C6"] = {
    "name": NAMES["C6"][1], "name_zh": NAMES["C6"][0],
    "method": "Automated (each entry's source-benchmark verifier in its container; pass rate over trials)",
    "dimensions": 1, "in_composite": False,
    "note": "The 7 cases that best separated agy + gemini-3.6-flash / gemini-3.8-flash and Claude "
            "Code + opus-5-5 (3 trials each, 2026-10-13). Sources: Terminal-Bench 2.0, DeepSWE v1.1, "
            "SWE-bench Verified, FrontierSWE v2.",
    "entry_count": len(manifest_entries["C6"]),
    "entries": sorted(manifest_entries["C6"], key=lambda x: x["instance_id"]),
}
m["categories"]["C7"] = {
    "name": NAMES["C7"][1], "name_zh": NAMES["C7"][0],
    "method": "Automated (each entry's source-benchmark verifier in its container; pass rate over trials)",
    "dimensions": 1, "in_composite": False,
    "note": "Rednote-relevant tasks where the three model setups scored similarly (daily-work sanity "
            "check). Sources: Terminal-Bench 2.0, SWE-bench Verified, DeepSWE v1.1.",
    "entry_count": len(manifest_entries["C7"]),
    "entries": sorted(manifest_entries["C7"], key=lambda x: x["instance_id"]),
}
m["total_entries"] = sum(c["entry_count"] for c in m["categories"].values())
m_path.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")

# 4) id mapping for pre-restructure results
(ROOT / "results" / "id_mapping.json").write_text(json.dumps({
    "description": "Runs whose folder timestamp is earlier than runs_before use the former IDs; "
                   "map them with old_to_new. Later runs use the new IDs directly.",
    "runs_before": RUNS_BEFORE,
    "old_to_new": dict(sorted(mapping.items())),
}, indent=2, ensure_ascii=False) + "\n")
for old, new in sorted(mapping.items(), key=lambda kv: kv[1]):
    print(f"{old} -> {new}")
print("manifest total:", m["total_entries"])
