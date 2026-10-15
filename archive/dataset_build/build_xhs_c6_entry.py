"""Write the XHS C6 dataset entry for terminal-bench-2 `polyglot-c-py`.

Output: sources/xhs/dataset/c6/C6-01_polyglot_c_py.json  (env assets already in dataset/c6/envs/C6-01/)
"""

import json
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
XHS = ROOT / "sources/xhs"
CASE = ROOT / "deliverables/cases/terminal_bench_2.0/polyglot-c-py"
ENV = "dataset/c6/envs/C6-01"

instruction = (CASE / "task/instruction.md").read_text()
row = pd.read_csv(ROOT / "data/candidates.csv").query(
    "benchmark == 'terminal_bench_2.0' and task == 'polyglot-c-py'").iloc[0]
scores = pd.read_csv(CASE / "scores.csv").sort_values("score", ascending=False)
fm = pd.read_csv(ROOT / "data/case_studies/polyglot-c-py/trial_failure_modes.csv")

entry = {
    "instance_id": "C6-01",
    "category": "C6",
    "category_name": "环境任务（容器化终端）",
    "task_type": "terminal_task",
    "maps_to_journey": "External: Terminal-Bench 2.0 / polyglot-c-py",
    "problem_statement": instruction,
    "environment": {
        "type": "docker",
        "dockerfile": f"{ENV}/Dockerfile",
        "prebuilt_image": "alexgshaw/polyglot-c-py:20251031",
        "workdir": "/app",
        "cpus": 1,
        "memory": "2g",
        "network": True,
        "agent_timeout_sec": 900,
        "initial_state": "empty /app (no starter files)",
    },
    "verification": {
        "type": "script",
        "script": f"{ENV}/verify.py",
        "container_path": "/tmp/verify.py",
        "command": ["python3", "/tmp/verify.py", "--root", "/app"],
        "timeout_sec": 900,
        "checks_in_order": [
            "/app/polyglot contains exactly one entry: main.py.c (no cmain, no scratch files)",
            "gcc /app/polyglot/main.py.c -o /app/polyglot/cmain exits 0 (warnings OK)",
            "for n in 42, 10, 0: python3 main.py.c n AND ./cmain n exit 0 and print "
            "267914296, 55, 0 (stdout stripped)",
        ],
        "equivalent_to": "original_tests/test_outputs.py::test_fibonacci_polyglot (same checks, same order)",
        "original_tests": f"{ENV}/original_tests/",
    },
    "gold_solution": {"script": f"{ENV}/solve.sh", "run_in": "/app"},
    "evaluation_rubric": "evaluation/rubrics/c6_env.json",
    "source": {
        "benchmark": "Terminal-Bench 2.0",
        "repo": "https://github.com/laude-institute/terminal-bench-2",
        "commit": "69671fbaac6d67a7ef0dfec016cc38a64ef7a77c",
        "path": "polyglot-c-py",
        "author": "Nicholas Carlini",
        "difficulty": "medium",
        "expert_time_estimate_min": 20,
        "original_scoring": "binary reward: 1 iff tests/test_outputs.py passes (pytest via tests/test.sh)",
        "conversion_changes": [
            "problem_statement, Dockerfile, gold solution and original tests copied verbatim",
            "grading uses verify.py (framework-free port of test_outputs.py: same checks/order, "
            "emits a JSON verdict) instead of pytest+uv",
        ],
    },
    "discrimination": {
        "what_it_measures": (
            "Mostly workspace hygiene / implicit-requirement inference rather than polyglot skill: "
            "79% of leaderboard failures leave extra files in /app/polyglot (usually the `cmain` "
            "binary the prompt itself says to build); ~0% produce wrong output."),
        "n_models": int(row["n_models"]),
        "mean_pass_rate": round(float(row["mean"]), 3),
        "std": round(float(row["std"]), 3),
        "disc_r": round(float(row["disc_r"]), 3),
        "frontier_std": round(float(row["frontier_std"]), 3),
        "frontier_disc_r": round(float(row["frontier_disc_r"]), 3),
        "tier": row["tier"],
        "leaderboard_failure_modes": {k: int(v) for k, v in fm.category.value_counts().items()},
    },
    "reference_scores": [
        {"submission": r.model_submission, "agent": r.agent, "model": r.model,
         "pass_rate": round(float(r.score), 3), "n_runs": int(r.n_runs)}
        for r in scores.itertuples()
    ],
}
out = XHS / "dataset/c6/C6-01_polyglot_c_py.json"
out.write_text(json.dumps(entry, indent=2, ensure_ascii=False) + "\n")
print("wrote", out.relative_to(ROOT))
