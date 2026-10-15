"""Build XHS C6 entries (C6-02..C6-07) from Terminal-Bench 2.0 tasks.

For each task:
  dataset/c6/envs/C6-XX/environment/   verbatim Dockerfile + build context (initial /app files)
  dataset/c6/envs/C6-XX/original_tests/ verbatim tests/ (hidden from the agent; run by the grader)
  dataset/c6/envs/C6-XX/solve.sh        verbatim reference solution
  dataset/c6/C6-XX_<task>.json          entry (prompt, environment, verification, provenance,
                                        discrimination stats, leaderboard reference scores)
Grading = the task's own pytest command (from tests/test.sh), type `tb2_pytest`.
"""

import json
import pathlib
import re
import shutil
import tomllib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
XHS = ROOT / "sources/xhs"
TB2 = ROOT / "sources/tb2"
TB2_COMMIT = "69671fbaac6d67a7ef0dfec016cc38a64ef7a77c"

TASKS = [
    ("C6-02", "mteb-retrieve",
     "Search / recommendation retrieval with a Chinese embedding model (bge-small-zh)",
     "Exact use of an embedding stack (model + revision) and correct ranking (5th-highest cosine "
     "similarity), i.e. careful retrieval engineering rather than approximate answers."),
    ("C6-03", "query-optimize",
     "Backend / data-warehouse SQL performance tuning",
     "Rewriting a slow SQLite query to be as fast as a reference while returning identical rows; "
     "graded on exact output equality, runtime (<= 1.05x golden median), single statement, size."),
    ("C6-04", "video-processing",
     "Video-note understanding (detecting events in user videos)",
     "Building a robust classical-CV pipeline (OpenCV/NumPy only) that generalizes from one example "
     "video to a hidden test video (takeoff/landing frame ranges)."),
    ("C6-05", "cancel-async-tasks",
     "Python async backend services: bounded concurrency and graceful cancellation",
     "Correct asyncio concurrency limiting and cleanup on KeyboardInterrupt below/at/above the "
     "concurrency limit (subtle cancellation semantics)."),
    ("C6-06", "filter-js-from-html",
     "UGC safety: sanitizing user-posted rich text / HTML against XSS",
     "Removing all JavaScript execution vectors (verified by a real headless Chromium) while "
     "leaving benign HTML byte-identical; very few systems pass."),
    ("C6-07", "db-wal-recovery",
     "Data reliability: recovering a corrupted SQLite WAL",
     "Diagnosing and repairing a corrupted/obfuscated write-ahead log so all 11 records (base + "
     "WAL changes) are recovered exactly."),
]

cand = pd.read_csv(ROOT / "data/candidates.csv").query("benchmark == 'terminal_bench_2.0'")
alltasks = pd.read_csv(ROOT / "data/all_task_discrimination.csv").query(
    "benchmark == 'terminal_bench_2.0'")
manifest_entries = []

for iid, task, rednote, measures in TASKS:
  src = TB2 / task
  meta = tomllib.loads((src / "task.toml").read_text())
  env_dir = XHS / "dataset/c6/envs" / iid
  if env_dir.exists():
    shutil.rmtree(env_dir)
  shutil.copytree(src / "environment", env_dir / "environment")
  shutil.copytree(src / "tests", env_dir / "original_tests")
  shutil.copy2(src / "solution/solve.sh", env_dir / "solve.sh")

  # grader.sh = the original tests/test.sh minus the lines that install curl and uv
  # (uv/uvx are provided at /opt/xhs/bin by the harness). Everything else is verbatim.
  test_sh = (src / "tests/test.sh").read_text()
  drop = (r"^\s*apt-get update\s*$", r"^\s*apt-get install -y curl\s*$",
          r"astral\.sh/uv", r"^\s*source \$HOME/\.local/bin/env\s*$")
  kept = [ln for ln in test_sh.splitlines() if not any(re.search(d, ln) for d in drop)]
  removed = [ln for ln in test_sh.splitlines() if any(re.search(d, ln) for d in drop)]
  (env_dir / "original_tests" / "grader.sh").write_text(
      "# Derived from tests/test.sh: only the curl/uv installation lines were removed.\n"
      + "\n".join(kept) + "\n")
  cmd = "bash /tests/grader.sh"

  row = cand[cand.task == task]
  row = (row if len(row) else alltasks[alltasks.task == task]).iloc[0]
  scores = pd.read_csv(ROOT / f"deliverables/cases/terminal_bench_2.0/{task}/scores.csv")
  env, agent, ver = meta.get("environment", {}), meta.get("agent", {}), meta.get("verifier", {})
  md = meta.get("metadata", {})
  rel = f"dataset/c6/envs/{iid}"

  entry = {
      "instance_id": iid,
      "category": "C6",
      "category_name": "环境任务（容器化终端）",
      "task_type": "terminal_task",
      "maps_to_journey": f"External: Terminal-Bench 2.0 / {task}",
      "rednote_relevance": rednote,
      "problem_statement": (src / "instruction.md").read_text(),
      "environment": {
          "type": "docker",
          "dockerfile": f"{rel}/environment/Dockerfile",
          "prebuilt_image": env.get("docker_image"),
          "workdir": "/app",
          "cpus": env.get("cpus"),
          "memory": str(env.get("memory", "")).lower() or None,
          "network": True,
          "agent_timeout_sec": int(agent.get("timeout_sec", 900)),
          "initial_state": "image /app as built by the Dockerfile (COPY'd task files, if any)",
      },
      "verification": {
          "type": "tb2_pytest",
          "tests_dir": f"{rel}/original_tests",
          "command": cmd,
          "timeout_sec": int(ver.get("timeout_sec", 900)),
          "reward": "1 iff /logs/verifier/reward.txt == 1 (written by the original test.sh when "
                    "pytest exits 0); per-test results recorded from the CTRF report",
          "grader_derivation": {"from": "tests/test.sh", "removed_lines": removed},
          "hidden_from_agent": True,
          "tests": re.findall(r"^def (test_\w+)", (src / "tests/test_outputs.py").read_text(), re.M),
      },
      "gold_solution": {"script": f"{rel}/solve.sh", "run_in": "/app"},
      "evaluation_rubric": "evaluation/rubrics/c6_env.json",
      "source": {
          "benchmark": "Terminal-Bench 2.0",
          "repo": "https://github.com/laude-institute/terminal-bench-2",
          "commit": TB2_COMMIT, "path": task,
          "author": md.get("author_name"), "difficulty": md.get("difficulty"),
          "category": md.get("category"),
          "expert_time_estimate_min": md.get("expert_time_estimate_min"),
          "original_scoring": "binary reward: 1 iff tests/test_outputs.py passes (tests/test.sh)",
          "conversion_changes": [
              "instruction, Dockerfile + build context, tests and solution copied verbatim",
              "grader runs the original tests/test.sh (as grader.sh) with only the curl/uv "
              "installation lines removed; uv/uvx are pre-provisioned by the harness",
          ],
      },
      "discrimination": {
          "what_it_measures": measures,
          "n_models": int(row["n_models"]), "mean_pass_rate": round(float(row["mean"]), 3),
          "std": round(float(row["std"]), 3), "disc_r": round(float(row["disc_r"]), 3),
          "frontier_std": round(float(row.get("frontier_std", float("nan"))), 3),
          "frontier_disc_r": round(float(row.get("frontier_disc_r", float("nan"))), 3),
          "tier": row.get("tier", "n/a (below selection thresholds)") if isinstance(
              row.get("tier"), str) else "n/a (below selection thresholds)",
      },
      "reference_scores": [
          {"submission": r.model_submission, "agent": r.agent, "model": r.model,
           "pass_rate": round(float(r.score), 3), "n_runs": int(r.n_runs)}
          for r in scores.sort_values("score", ascending=False).itertuples()],
  }
  out = XHS / f"dataset/c6/{iid}_{task.replace('-', '_')}.json"
  out.write_text(json.dumps(entry, indent=2, ensure_ascii=False) + "\n")
  manifest_entries.append({"instance_id": iid, "file": str(out.relative_to(XHS)),
                           "maps_to_journey": entry["maps_to_journey"]})
  print(f"{iid} {task:22} image={entry['environment']['prebuilt_image']} "
        f"agent_timeout={entry['environment']['agent_timeout_sec']}s tests={len(entry['verification']['tests'])}")

m_path = XHS / "dataset/manifest.json"
m = json.loads(m_path.read_text())
c6 = m["categories"]["C6"]
keep = [e for e in c6["entries"] if e["instance_id"] == "C6-01"]
c6["entries"] = keep + manifest_entries
c6["entry_count"] = len(c6["entries"])
m["total_entries"] = sum(c["entry_count"] for c in m["categories"].values())
m_path.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
print("manifest C6 entries:", c6["entry_count"], "| total:", m["total_entries"])
