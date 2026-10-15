"""Build XHS C8 entries (feature development in real repos) from DeepSWE v1.1.

Six DeepSWE tasks close to Rednote's business (gateway, storage, ORM/SQL, web data caching,
encrypted backups, geo index). They were reported to separate Antigravity + gemini-3.8-flash
(pass) from Antigravity + gemini-3.6-flash (fail) in a DeepSWE run on another machine.

For each task (source: github.com/datacurve-ai/deep-swe, Harbor task format v1.3):
  dataset/c8/envs/C8-XX/environment/  verbatim Dockerfile (image provenance)
  dataset/c8/envs/C8-XX/tests/        verbatim hidden verifier: test.sh, test.patch, grader.py,
                                      config.json (+ the verifier Dockerfile)
  dataset/c8/envs/C8-XX/solution/     verbatim reference solution (solution.patch + solve.sh)
  dataset/c8/C8-XX_<task>.json        entry
Grading = DeepSWE's own flow (verification.type = deepswe): collect the committed diff, apply it
in a fresh container of the same image, run the original tests/test.sh -> reward.json.
"""

import json
import pathlib
import shutil
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[4]  # <workspace>/sources/xhs/archive/dataset_build -> workspace root
XHS = ROOT / "sources/xhs"
SRC = ROOT / "sources/deepswe/tasks"
DEEPSWE_COMMIT = "0b9fabbb63b9104d678fe965e1632f2dd9eaa2ea"

TASKS = [
    ("C8-01", "kgateway-consistent-hash-policy",
     "API gateway traffic policy: consistent-hash (sticky) routing by header/cookie/query/source "
     "IP for cache affinity and sessions across microservices"),
    ("C8-02", "pebble-durability-wait-apis",
     "Storage infrastructure: notify when a synced write is durable before acking clients or "
     "replicating (LSM key-value store, RocksDB-style)"),
    ("C8-03", "drizzle-orm-window-function-builders",
     "Ranking / leaderboard / analytics SQL: type-safe window functions in a TypeScript ORM "
     "(Node.js BFF services)"),
    ("C8-04", "query-persist-restored-query-state",
     "Web/H5 data layer: restoring persisted TanStack Query cache entries with their full state "
     "(offline feed restore)"),
    ("C8-05", "onedump-dump-encryption-pipeline",
     "Data security / compliance: streaming AES-256-GCM encryption of database dump backups"),
    ("C8-06", "geo-shapeindex-serialization",
     "Location features (nearby notes, POI / local-life search): serialize the S2 spatial "
     "ShapeIndex instead of rebuilding it on every load"),
]

manifest_entries = []
(XHS / "dataset/c8").mkdir(parents=True, exist_ok=True)
for cid, task, rednote in TASKS:
  src = SRC / task
  meta = tomllib.loads((src / "task.toml").read_text())
  md, env, ver, agent = meta["metadata"], meta["environment"], meta["verifier"], meta["agent"]
  cfg = json.loads((src / "tests/config.json").read_text())
  env_dir = XHS / "dataset/c8/envs" / cid
  if env_dir.exists():
    shutil.rmtree(env_dir)
  for d in ("environment", "tests", "solution"):
    shutil.copytree(src / d, env_dir / d)
  rel = f"dataset/c8/envs/{cid}"
  entry = {
      "instance_id": cid,
      "category": "C8",
      "category_name": "功能开发（DeepSWE 容器化仓库）",
      "task_type": "repo_feature",
      "maps_to_journey": f"External: DeepSWE v1.1 / {task}",
      "rednote_relevance": rednote,
      "title": md.get("display_title"),
      "problem_statement": (src / "instruction.md").read_text(),
      "environment": {
          "type": "docker",
          "dockerfile": f"{rel}/environment/Dockerfile",
          "prebuilt_image": env["docker_image"],
          "workdir": "/app",
          "cpus": env.get("cpus"),
          "memory": f"{env.get('memory_mb', 0) // 1024}g",
          "network": "no-network (original); host network under udocker",
          "agent_timeout_sec": int(agent.get("timeout_sec", 10800)),
          "udocker_rmi_after_create": True,
          "initial_state": f"{md['repository_url']} at base commit {md['base_commit_hash']} on the "
                           "default branch (future history removed), deps pre-fetched",
      },
      "verification": {
          "type": "deepswe",
          "tests_dir": f"{rel}/tests",
          "verifier_dockerfile": f"{rel}/tests/Dockerfile",
          "base_commit": md["base_commit_hash"],
          "collect_command": ver["collect"][0]["command"] if ver.get("collect") else
                             meta["verifier"]["collect"][0]["command"],
          "command": "bash /tests/test.sh",
          "timeout_sec": int(ver.get("timeout_sec", 1800)),
          "reward": "1 iff every FAIL_TO_PASS test passes and no PASS_TO_PASS test fails "
                    "(DeepSWE grader.py -> /logs/verifier/reward.json); only committed work "
                    "counts (model.patch = git diff <base> HEAD)",
          "hidden_from_agent": True,
          "fail_to_pass_count": len(cfg["f2p_node_ids"]),
          "pass_to_pass_count": len(cfg["p2p_node_ids"]),
          "report_format": cfg["grade"]["tool_label"],
      },
      "gold_solution": {"dir": f"{rel}/solution", "script": "solve.sh", "timeout_sec": 600},
      "evaluation_rubric": "evaluation/rubrics/c8_feature.json",
      "source": {
          "benchmark": "DeepSWE v1.1 (Datacurve)",
          "repo": "https://github.com/datacurve-ai/deep-swe",
          "commit": DEEPSWE_COMMIT, "path": f"tasks/{task}",
          "task_id": md.get("task_id"), "ext_id": md.get("ext_id"),
          "upstream_repo": md.get("repository_url"), "base_commit": md.get("base_commit_hash"),
          "language": md.get("language"), "category": md.get("category"),
          "original_title": md.get("original_title"),
          "original_scoring": "binary reward from tests/grader.py (reward.json), Harbor "
                              "environment_mode=separate, verifier image = task image + tests",
          "conversion_changes": [
              "instruction, Dockerfiles, tests and solution copied verbatim; agent and verifier "
              "use the published task image",
              "verifier image is not rebuilt: a fresh container of the task image gets the "
              "tests copied to /tests (identical content to tests/Dockerfile's COPY lines)",
              "agent and verifier have host network under udocker (original: no-network)",
          ],
      },
      "discrimination": {
          "selected_for": "Rednote relevance + observed model separation",
          "observed": "reported by the user from a DeepSWE run on another machine: Antigravity + "
                      "gemini-3.8-flash passed, Antigravity + gemini-3.6-flash failed",
      },
  }
  out = XHS / f"dataset/c8/{cid}_{task.replace('-', '_')}.json"
  out.write_text(json.dumps(entry, indent=2, ensure_ascii=False) + "\n")
  manifest_entries.append({"instance_id": cid, "file": str(out.relative_to(XHS)),
                           "maps_to_journey": entry["maps_to_journey"]})
  print(f"{cid} {task:38} {md.get('language'):10} F2P={len(cfg['f2p_node_ids'])} "
        f"P2P={len(cfg['p2p_node_ids'])} image={env['docker_image'].split(':')[-1]}")

m_path = XHS / "dataset/manifest.json"
m = json.loads(m_path.read_text())
m["categories"]["C8"] = {
    "name": "Feature Development (DeepSWE, Containerized Repos)",
    "name_zh": "功能开发（DeepSWE 容器化仓库）",
    "method": "Automated (DeepSWE grader: committed diff applied in a fresh task container, hidden "
              "FAIL_TO_PASS/PASS_TO_PASS suites, pass rate over trials)",
    "dimensions": 1,
    "in_composite": False,
    "note": "DeepSWE v1.1 feature tasks close to Rednote's business; reported to separate "
            "gemini-3.8-flash from gemini-3.6-flash with Antigravity. Not part of the composite.",
    "entry_count": len(manifest_entries),
    "entries": manifest_entries,
}
m["total_entries"] = sum(c["entry_count"] for c in m["categories"].values())
m_path.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
print("manifest C8 entries:", len(manifest_entries), "| total:", m["total_entries"])
