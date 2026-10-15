"""Build XHS C6-08 (ffmpeg-swscale-rewrite) from FrontierSWE v2.

A "hard tier" C6 entry: re-implement FFmpeg's libswscale (image scaling + pixel-format
conversion) in Zig with portable SIMD; continuous reward from a deterministic instruction-cost
model (callgrind + per-opcode pricing), so it is robust to udocker/host load.

  dataset/c6/envs/C6-08/environment/   verbatim task environment (Dockerfile, workspace, tests)
  dataset/c6/envs/C6-08/solution/      verbatim oracle (placeholder converter; scores 0 by design)
  dataset/c6/C6-08_ffmpeg_swscale_rewrite.json

Images are pinned by digest. udocker cannot pull digests, so load them first:
  python3 scripts/fetch_oci_digest.py <env@sha256> x env.tar && udocker load -i env.tar xhs/ffmpeg-swscale-env
  udocker tag xhs/ffmpeg-swscale-env:<tag> xhs/ffmpeg-swscale-env:fswe-da83f84   (same for verifier)
"""

import json
import pathlib
import shutil
import tomllib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
XHS = ROOT / "sources/xhs"
CASE = ROOT / "deliverables/cases/frontierswe_v2/ffmpeg-swscale-rewrite"
SRC = CASE / "task"
IID, TASK = "C6-08", "ffmpeg-swscale-rewrite"
COMMIT = "da83f84f8fbcec3cbf0f2b17c98ebc811355c2df"
AGENT_BUDGET_SEC = 7200  # FrontierSWE allows 72000 s (20 h); reduced for cost, see entry notes
PASS_THRESHOLD = 0.1     # reward 0.1 ~ correct on every conversion AND ~3.6x less work than ref

meta = tomllib.loads((SRC / "task.toml").read_text())
env_dir = XHS / "dataset/c6/envs" / IID
if env_dir.exists():
  shutil.rmtree(env_dir)
shutil.copytree(SRC / "environment", env_dir / "environment")
shutil.copytree(SRC / "solution", env_dir / "solution")
rel = f"dataset/c6/envs/{IID}"

cand = pd.read_csv(ROOT / "data/candidates.csv")
row = cand[(cand.benchmark == "frontierswe_v2") & (cand.task == TASK)].iloc[0]
scores = pd.read_csv(CASE / "scores.csv").sort_values("score", ascending=False)
e, v = meta["environment"], meta["verifier"]

entry = {
    "instance_id": IID,
    "category": "C6",
    "category_name": "环境任务（容器化终端）",
    "task_type": "terminal_task",
    "maps_to_journey": f"External: FrontierSWE v2 / {TASK}",
    "rednote_relevance": "Video/image note pipeline: high-performance pixel-format conversion "
                         "and scaling (thumbnails, transcoding pre-processing) with SIMD",
    "problem_statement": (SRC / "instruction.md").read_text(),
    "environment": {
        "type": "docker",
        "dockerfile": f"{rel}/environment/Dockerfile",
        "prebuilt_image": e["docker_image"],
        "udocker_image": "xhs/ffmpeg-swscale-env:fswe-da83f84",
        "workdir": "/app",
        "cpus": e.get("cpus"),
        "memory": f"{e.get('memory_mb', 0) // 1024}g",
        "network": "allowlist (original); host network under udocker",
        "agent_timeout_sec": AGENT_BUDGET_SEC,
        # The agent runs as (fake) root under udocker, unlike FrontierSWE's non-root `agent`
        # user: hide root-only verifier assets (/root/tests, /root/assets) behind an empty
        # per-trial /root. Other per-trial dirs keep scratch writes out of the shared base.
        "per_trial_paths": ["/root", "/sandbox-timer", "/solution", "/home/agent/.cache"],
        "container_env": {"TASK_BUDGET_SECS": str(AGENT_BUDGET_SEC)},
        "init_cmd": "sandbox-timer start >/dev/null 2>&1 || true",
        "udocker_execmode": "P1",  # grader uses runuser/setuid; R1 maps only uid 0
        "initial_state": "image /app: scaffold, perf-check, driver, reference .so; FFmpeg "
                         "sources at /reference/ffmpeg-src",
    },
    "verification": {
        "type": "harbor_separate",
        "verifier_image": v["environment"]["docker_image"],
        "udocker_verifier_image": "xhs/ffmpeg-swscale-verifier:fswe-da83f84",
        "command": "bash /root/tests/test.sh",
        "timeout_sec": int(v.get("timeout_sec", 10800)),
        "artifact_excludes": meta["artifacts"][0]["exclude"],
        "reward": "continuous in [0, 1] = correctness x (2^clamp((s-1)/19, 0, 1) - 1), s = "
                  "geomean work ratio reference/submission over held-out workloads (callgrind "
                  "+ per-opcode pricing); 0 if it does not build, links/wraps FFmpeg, or any "
                  "conversion misses the PSNR bars",
        "pass_threshold": PASS_THRESHOLD,
        "pass_threshold_note": "pass = reward >= 0.1 (correct everywhere and ~3.6x less work); "
                               "mean score over trials is the primary metric",
        "hidden_from_agent": True,
        "udocker_execmode": "P1",
    },
    "gold_solution": {
        "dir": f"{rel}/solution", "script": "solve.sh", "timeout_sec": 1800,
        "expected_reward": 0.0,
        "note": "FrontierSWE ships no reference implementation (oracle_reward_threshold = 0): "
                "solve.sh installs a placeholder converter that reaches every verifier phase "
                "(build, provenance, contract sweep, measurement) and scores 0.0 by design. "
                "Validate via reward_details (build_ok, provenance_ok, correctness, measured).",
    },
    "evaluation_rubric": "evaluation/rubrics/c6_env.json",
    "source": {
        "benchmark": "FrontierSWE v2",
        "repo": "https://github.com/Proximal-Labs/frontier-swe-v2",
        "commit": COMMIT, "path": "tasks/ffmpeg-libswscale-optimization",
        "task_page": "https://www.frontierswe.com/tasks/ffmpeg-swscale-rewrite",
        "difficulty": meta["metadata"].get("difficulty"),
        "category": meta["metadata"].get("category"),
        "original_scoring": "continuous reward, Mean@5 over 5 runs (site reports normalized "
                            "meanFrac)",
        "conversion_changes": [
            "instruction, environment, tests and oracle copied verbatim; images pinned by digest",
            f"agent budget {AGENT_BUDGET_SEC}s instead of 72000s (20h); TASK_BUDGET_SECS set to "
            "match so the agent-visible sandbox-timer is consistent",
            "agent runs as fake root under udocker (original: non-root `agent`); /root is an "
            "empty per-trial dir so verifier assets stay hidden",
            "verifier runs in a disposable container from the verifier image with the /app "
            "artifacts copied in (Harbor environment_mode=separate)",
        ],
    },
    "discrimination": {
        "what_it_measures": "Long-horizon systems/SIMD engineering against a strict correctness "
                            "contract (58 conversions, PSNR bars) and a deterministic cost model",
        "n_models": int(row["n_models"]), "mean_score": round(float(row["mean"]), 3),
        "std": round(float(row["std"]), 3), "disc_r": round(float(row["disc_r"]), 3),
        "frontier_mean": round(float(row["frontier_mean"]), 3),
        "frontier_std": round(float(row["frontier_std"]), 3),
        "tier": row["tier"],
        "caveat": "reference scores were obtained with a 20h budget; scores under the 2h budget "
                  "here are not directly comparable",
    },
    "reference_scores": [
        {"model": r.model, "agent": r.agent, "score": round(float(r.score), 3),
         "raw_mean": round(float(r.raw_mean), 4), "n_runs": int(r.n_runs),
         "mean_hours": round(float(r.mean_hours), 2), "mean_cost_usd": round(float(r.mean_cost_usd), 1)}
        for r in scores.itertuples()],
}
out = XHS / f"dataset/c6/{IID}_{TASK.replace('-', '_')}.json"
out.write_text(json.dumps(entry, indent=2, ensure_ascii=False) + "\n")

m_path = XHS / "dataset/manifest.json"
m = json.loads(m_path.read_text())
c6 = m["categories"]["C6"]
c6["entries"] = [x for x in c6["entries"] if x["instance_id"] != IID] + [
    {"instance_id": IID, "file": str(out.relative_to(XHS)), "maps_to_journey": entry["maps_to_journey"]}]
c6["entry_count"] = len(c6["entries"])
m["total_entries"] = sum(c["entry_count"] for c in m["categories"].values())
m_path.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
print(out.relative_to(XHS), "| C6 entries:", c6["entry_count"], "| total:", m["total_entries"])
