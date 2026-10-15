"""Build XHS C7 entries (backend daily-work bug fixes) from SWE-bench Verified.

C7 = "close to Rednote engineers' daily work" (Django ORM / MySQL / JSON fields / email i18n,
HTTP clients behind proxies), not selected for model discrimination.

For each instance:
  dataset/c7/envs/C7-XX/eval.sh        official SWE-bench eval script (swebench.make_test_spec):
                                       resets the test files, applies the hidden test patch, runs
                                       the instance's test command, prints the log markers
  dataset/c7/envs/C7-XX/instance.json  the SWE-bench Verified row (graded with the official
                                       swebench log parser + FAIL_TO_PASS / PASS_TO_PASS report)
  dataset/c7/envs/C7-XX/gold.sh        applies the gold patch (validation only)
  dataset/c7/C7-XX_<id>.json           entry (prompt, environment, verification, provenance,
                                       reference scores from SWE-bench submissions)

Requires the swebench package (grader venv): ~/.cache/xhs_c6/swebench-venv
  uv venv ~/.cache/xhs_c6/swebench-venv && VIRTUAL_ENV=... uv pip install swebench==4.1.0
Run with that venv's python (pandas + pyarrow come with swebench's datasets dependency).
"""

import json
import pathlib
import shutil

import pandas as pd
from swebench.harness.test_spec.test_spec import make_test_spec

ROOT = pathlib.Path(__file__).resolve().parents[1]
XHS = ROOT / "sources/xhs"
SWEBENCH_VERSION = "4.1.0"

TASKS = [
    ("C7-01", "django__django-15957",
     "Feed / comment pagination: prefetch the top-N related rows per object (Prefetch + slice)",
     "ORM N+1 avoidance, e.g. 'latest 3 comments for each note in a feed page'"),
    ("C7-02", "django__django-15280",
     "ORM performance correctness: deferred fields when prefetching back to the parent",
     "only()/defer() + prefetch_related() used to trim columns on hot read paths"),
    ("C7-03", "django__django-12965",
     "DB performance regression: bulk delete issuing a subquery (MySQL lock / speed issue)",
     "Model.objects.all().delete() performance on large tables, a routine ops concern"),
    ("C7-04", "django__django-15503",
     "JSON columns on MySQL/SQLite: has_key lookups with numeric keys",
     "Querying semi-structured note/user attributes stored in JSONField"),
    ("C7-05", "django__django-14376",
     "MySQL backend maintenance: deprecated mysqlclient connection kwargs",
     "Keeping the DB driver layer current with library upgrades"),
    ("C7-06", "django__django-11532",
     "i18n: email headers crash on non-ASCII (IDN) hostnames",
     "Unicode/i18n robustness for a Chinese-speaking user base and servers"),
    ("C7-07", "psf__requests-6028",
     "Service-to-service HTTP: proxy authentication bug in requests",
     "Calling internal/external APIs through authenticated egress proxies"),
]

PROMPT = """You are working in the `{repo}` repository, checked out at `/testbed` (commit {commit}).

Resolve the following issue by editing the source code in `/testbed`. Do not modify existing
tests; hidden tests will be run after you finish to check the fix and that nothing else broke.

<issue>
{issue}
</issue>
"""


def image_name(iid: str) -> str:
  return f"swebench/sweb.eval.x86_64.{iid.replace('__', '_1776_')}:latest"


df = pd.read_parquet(ROOT / "sources/swebench_verified/tasks.parquet")
disc = pd.read_csv(ROOT / "data/swebench_verified/task_discrimination_recent.csv")
per = pd.read_csv(ROOT / "data/swebench_verified/per_task_model_recent.csv")
manifest_entries = []
(XHS / "dataset/c7").mkdir(parents=True, exist_ok=True)

for cid, iid, rednote, scenario in TASKS:
  row = df[df.instance_id == iid].iloc[0].to_dict()
  inst = {k: (v if not hasattr(v, "tolist") else v.tolist()) for k, v in row.items()}
  for k in ("FAIL_TO_PASS", "PASS_TO_PASS"):
    if isinstance(inst[k], str):
      inst[k] = json.loads(inst[k])
  spec = make_test_spec(inst)
  env_dir = XHS / "dataset/c7/envs" / cid
  if env_dir.exists():
    shutil.rmtree(env_dir)
  env_dir.mkdir(parents=True)
  (env_dir / "eval.sh").write_text(spec.eval_script)
  (env_dir / "instance.json").write_text(json.dumps(inst, indent=1, ensure_ascii=False) + "\n")
  (env_dir / "gold.patch").write_text(inst["patch"])
  (env_dir / "gold.sh").write_text(
      "#!/bin/bash\n# Validation only: apply the SWE-bench gold patch.\nset -e\ncd /testbed\n"
      "git apply -v - <<'XHS_GOLD_PATCH_EOF'\n" + inst["patch"].rstrip("\n")
      + "\nXHS_GOLD_PATCH_EOF\n")
  rel = f"dataset/c7/envs/{cid}"
  d = disc[disc.task == iid]
  d = d.iloc[0].to_dict() if len(d) else {}
  scores = per[per.task == iid] if "task" in per.columns else per.iloc[0:0]

  entry = {
      "instance_id": cid,
      "category": "C7",
      "category_name": "日常后端缺陷修复（容器化仓库）",
      "task_type": "repo_bugfix",
      "maps_to_journey": f"External: SWE-bench Verified / {iid}",
      "rednote_relevance": rednote,
      "daily_work_scenario": scenario,
      "problem_statement": PROMPT.format(repo=inst["repo"], commit=inst["base_commit"][:12],
                                         issue=inst["problem_statement"].strip()),
      "environment": {
          "type": "docker",
          "prebuilt_image": image_name(iid),
          "workdir": "/testbed",
          "network": True,
          "agent_timeout_sec": 1800,
          "udocker_rmi_after_create": True,
          "initial_state": f"{inst['repo']} at base_commit {inst['base_commit']} with the "
                           "instance's conda env 'testbed' (official SWE-bench eval image)",
      },
      "verification": {
          "type": "swebench",
          "eval_script": f"{rel}/eval.sh",
          "instance": f"{rel}/instance.json",
          "timeout_sec": 1800,
          "reward": "1 iff resolved: every FAIL_TO_PASS and PASS_TO_PASS test passes (official "
                    "swebench log parser + get_eval_report, run on the eval.sh output)",
          "hidden_from_agent": True,
          "fail_to_pass": inst["FAIL_TO_PASS"],
          "pass_to_pass_count": len(inst["PASS_TO_PASS"]),
      },
      "gold_solution": {"script": f"{rel}/gold.sh", "run_in": "/testbed"},
      "evaluation_rubric": "evaluation/rubrics/c7_swe.json",
      "source": {
          "benchmark": "SWE-bench Verified",
          "dataset": "princeton-nlp/SWE-bench_Verified",
          "instance_id": iid, "repo": inst["repo"], "version": inst["version"],
          "base_commit": inst["base_commit"], "created_at": str(inst["created_at"]),
          "difficulty": inst.get("difficulty"),
          "swebench_harness_version": SWEBENCH_VERSION,
          "conversion_changes": [
              "issue text verbatim, wrapped in a short instruction (repo, path, don't edit tests)",
              "eval.sh generated by swebench.make_test_spec (unchanged); runs on the agent's "
              "edited /testbed instead of a diff applied to a fresh container",
          ],
          "contamination_note": "public since 2024; the gold fix is in upstream history",
      },
      "discrimination": {
          "selected_for": "daily-work relevance (not discrimination)",
          "n_systems": int(d["n_models"]) if "n_models" in d else None,
          "mean_resolve_rate": round(float(d["mean"]), 3) if "mean" in d else None,
          "disc_r": round(float(d["disc_r"]), 3) if "disc_r" in d else None,
      },
      "reference_scores": [
          {"submission": r["model"], "resolved": int(r["score"])}
          for r in scores.to_dict("records")
          if any(k in str(r["model"]).lower() for k in ("gemini", "claude", "gpt"))
      ][:30],
  }
  out = XHS / f"dataset/c7/{cid}_{iid}.json"
  out.write_text(json.dumps(entry, indent=2, ensure_ascii=False) + "\n")
  manifest_entries.append({"instance_id": cid, "file": str(out.relative_to(XHS)),
                           "maps_to_journey": entry["maps_to_journey"]})
  print(f"{cid} {iid:24} image={entry['environment']['prebuilt_image']} "
        f"F2P={len(inst['FAIL_TO_PASS'])} P2P={len(inst['PASS_TO_PASS'])}")

m_path = XHS / "dataset/manifest.json"
m = json.loads(m_path.read_text())
m["categories"]["C7"] = {
    "name": "Daily Backend Bug Fixes (Containerized Repos)",
    "name_zh": "日常后端缺陷修复（容器化仓库）",
    "method": "Automated (official SWE-bench eval script + hidden FAIL_TO_PASS/PASS_TO_PASS "
              "tests in the instance image, pass rate over trials)",
    "dimensions": 1,
    "in_composite": False,
    "note": "SWE-bench Verified issues close to Rednote backend daily work (Django ORM, MySQL, "
            "JSONField, i18n, HTTP proxies). Selected for relevance, not discrimination. Not part "
            "of the composite score.",
    "entry_count": len(manifest_entries),
    "entries": manifest_entries,
}
m["total_entries"] = sum(c["entry_count"] for c in m["categories"].values())
m_path.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
print("manifest C7 entries:", len(manifest_entries), "| total:", m["total_entries"])
