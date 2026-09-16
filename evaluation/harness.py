"""
XHS Coding Agent Evaluation Harness

Usage:
    python evaluation/harness.py --category c3 --entry C3-01 --agent-patch /path/to/patch.diff
    python evaluation/harness.py --category c1 --entry C1-01 --agent-output /path/to/output.md
    python evaluation/harness.py --category c4 --entry C4-01 --agent-output /path/to/findings.json
    python evaluation/harness.py --all --results-dir /path/to/results/

Evaluates agent output against the benchmark dataset.
"""

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATASET_DIR = BASE_DIR / "dataset"
REPO_DIR = BASE_DIR / "xhs-campaign-service"
RUBRICS_DIR = BASE_DIR / "evaluation" / "rubrics"


def load_entry(category: str, entry_id: str) -> dict:
    cat_dir = DATASET_DIR / category
    for f in cat_dir.glob("*.json"):
        d = json.load(open(f))
        if d["instance_id"] == entry_id:
            return d
    raise FileNotFoundError(f"Entry {entry_id} not found in {cat_dir}")


def load_rubric(rubric_path: str) -> dict:
    full_path = BASE_DIR / rubric_path
    return json.load(open(full_path))


# ── C3 Evaluation (Automated) ──────────────────────────────────────────────

def evaluate_c3(entry: dict, agent_patch_path: str) -> dict:
    base_commit = entry["base_commit"]
    gold_patch = entry["gold_patch"]
    test_patch = entry["test_patch"]
    fail_to_pass = entry["FAIL_TO_PASS"]
    pass_to_pass = entry["PASS_TO_PASS"]

    with tempfile.TemporaryDirectory(prefix="c3-eval-") as tmpdir:
        worktree = Path(tmpdir) / "repo"
        subprocess.run(
            ["git", "worktree", "add", str(worktree), base_commit],
            cwd=REPO_DIR, capture_output=True, check=True,
        )

        try:
            _setup_worktree(worktree)

            # Apply agent patch
            agent_patch = Path(agent_patch_path).read_text()
            result = subprocess.run(
                ["git", "apply", "--allow-empty"],
                input=agent_patch, text=True,
                cwd=worktree, capture_output=True,
            )
            if result.returncode != 0:
                return {
                    "error": "Agent patch failed to apply",
                    "details": result.stderr,
                    "scores": _zero_scores("c3"),
                }

            # Apply test patch
            result = subprocess.run(
                ["git", "apply", "--allow-empty"],
                input=test_patch, text=True,
                cwd=worktree, capture_output=True,
            )
            if result.returncode != 0:
                return {
                    "error": "Test patch failed to apply (likely conflicts with agent changes)",
                    "details": result.stderr,
                    "scores": _zero_scores("c3"),
                }

            # Run FAIL_TO_PASS tests
            f2p_results = _run_tests(worktree, fail_to_pass)
            f2p_pass = sum(1 for r in f2p_results.values() if r == "passed")
            f2p_total = len(fail_to_pass)

            # Run PASS_TO_PASS tests
            p2p_results = _run_tests(worktree, pass_to_pass)
            p2p_pass = sum(1 for r in p2p_results.values() if r == "passed")
            p2p_total = len(pass_to_pass)

            # Score D1: Functional Correctness
            f2p_ratio = f2p_pass / f2p_total if f2p_total > 0 else 0
            d1 = _tier_score(f2p_ratio, [(1.0, 25), (0.8, 20), (0.6, 15), (0.3, 10), (0, 0)])

            # Score D2: Regression Safety
            p2p_ratio = p2p_pass / p2p_total if p2p_total > 0 else 0
            d2 = _tier_score(p2p_ratio, [(1.0, 10), (0.9, 7), (0.7, 3), (0, 0)])

            # D3-D7 require LLM-as-judge (placeholder)
            scores = {
                "D1_functional_correctness": {
                    "score": d1,
                    "max": 25,
                    "detail": f"{f2p_pass}/{f2p_total} FAIL_TO_PASS tests passed ({f2p_ratio:.0%})",
                },
                "D2_regression_safety": {
                    "score": d2,
                    "max": 10,
                    "detail": f"{p2p_pass}/{p2p_total} PASS_TO_PASS tests passed ({p2p_ratio:.0%})",
                },
                "D3_readability": {"score": None, "max": 15, "detail": "Requires LLM-as-judge"},
                "D4_maintainability": {"score": None, "max": 15, "detail": "Requires LLM-as-judge"},
                "D5_robustness": {"score": None, "max": 15, "detail": "Requires LLM-as-judge"},
                "D6_convention": {"score": None, "max": 10, "detail": "Requires LLM-as-judge"},
                "D7_minimality": {"score": None, "max": 10, "detail": "Requires LLM-as-judge"},
            }

            # Apply gatekeeper rules
            automated_total = d1 + d2
            if d1 == 0:
                scores["gatekeeper"] = "D1=0: overall capped at 20"
            elif d2 == 0:
                scores["gatekeeper"] = "D2=0: overall capped at 30"

            return {
                "instance_id": entry["instance_id"],
                "scores": scores,
                "f2p_results": f2p_results,
                "p2p_results": p2p_results,
                "automated_subtotal": automated_total,
            }

        finally:
            subprocess.run(
                ["git", "worktree", "remove", str(worktree), "--force"],
                cwd=REPO_DIR, capture_output=True,
            )


def _setup_worktree(repo_dir: Path) -> None:
    subprocess.run(
        ["python3", "-m", "pip", "install", "-q", "-e", "."],
        cwd=repo_dir, capture_output=True, timeout=60,
    )


def _run_tests(repo_dir: Path, test_names: list[str]) -> dict[str, str]:
    results = {}
    if not test_names:
        return results

    result = subprocess.run(
        ["python3", "-m", "pytest", "--tb=no", "-v"] + test_names,
        cwd=repo_dir, capture_output=True, text=True, timeout=120,
    )

    for line in result.stdout.splitlines():
        line = line.strip()
        if " PASSED" in line:
            test_name = line.split(" PASSED")[0].strip()
            results[test_name] = "passed"
        elif " FAILED" in line:
            test_name = line.split(" FAILED")[0].strip()
            results[test_name] = "failed"
        elif " ERROR" in line:
            test_name = line.split(" ERROR")[0].strip()
            results[test_name] = "error"

    for t in test_names:
        if t not in results:
            results[t] = "not_run"

    return results


def _tier_score(ratio: float, tiers: list[tuple[float, int]]) -> int:
    for threshold, score in tiers:
        if ratio >= threshold:
            return score
    return tiers[-1][1]


def _zero_scores(category: str) -> dict:
    if category == "c3":
        return {
            "D1_functional_correctness": {"score": 0, "max": 25},
            "D2_regression_safety": {"score": 0, "max": 10},
            "D3_readability": {"score": 0, "max": 15},
            "D4_maintainability": {"score": 0, "max": 15},
            "D5_robustness": {"score": 0, "max": 15},
            "D6_convention": {"score": 0, "max": 10},
            "D7_minimality": {"score": 0, "max": 10},
        }
    return {}


# ── C4 Evaluation (Automated matching) ─────────────────────────────────────

def evaluate_c4(entry: dict, agent_findings: list[dict]) -> dict:
    planted = entry["planted_defects"]
    matched_planted = set()
    true_positives = []
    false_positives = []

    for finding in agent_findings:
        agent_file = finding.get("file", "")
        agent_desc = finding.get("description", "")
        best_match = None
        best_score = 0

        for i, defect in enumerate(planted):
            if i in matched_planted:
                continue
            planted_file = defect.get("file", defect.get("expected_location", {}).get("file", ""))
            if not _file_match(agent_file, planted_file):
                continue
            score = _semantic_similarity_heuristic(agent_desc, defect.get("description", ""), defect.get("title", ""))
            if score > best_score:
                best_score = score
                best_match = i

        if best_match is not None and best_score >= 0.3:
            matched_planted.add(best_match)
            true_positives.append({
                "finding": finding,
                "matched_defect": planted[best_match],
                "confidence": best_score,
            })
        else:
            false_positives.append(finding)

    total_planted = len(planted)
    recall = len(matched_planted) / total_planted if total_planted > 0 else 0
    precision = len(true_positives) / len(agent_findings) if agent_findings else 0

    d1 = _tier_score(recall, [(0.9, 25), (0.7, 20), (0.5, 15), (0.3, 10), (0, 5)])
    d2 = _tier_score(precision, [(0.8, 25), (0.6, 20), (0.4, 15), (0.2, 10), (0, 5)])

    return {
        "instance_id": entry["instance_id"],
        "scores": {
            "D1_detection_recall": {"score": d1, "max": 25, "detail": f"Detected {len(matched_planted)}/{total_planted} ({recall:.0%})"},
            "D2_detection_precision": {"score": d2, "max": 25, "detail": f"Precision {len(true_positives)}/{len(agent_findings)} ({precision:.0%})"},
            "D3_localization": {"score": None, "max": 20, "detail": "Requires detailed line matching"},
            "D4_classification": {"score": None, "max": 15, "detail": "Requires category/severity comparison"},
            "D5_explanation_quality": {"score": None, "max": 15, "detail": "Requires LLM-as-judge"},
        },
        "true_positives": true_positives,
        "false_positives": false_positives,
        "undetected": [planted[i] for i in range(total_planted) if i not in matched_planted],
    }


def _file_match(agent_file: str, planted_file: str) -> bool:
    return os.path.basename(agent_file) == os.path.basename(planted_file) or \
           agent_file.endswith(planted_file) or planted_file.endswith(agent_file)


def _semantic_similarity_heuristic(agent_desc: str, planted_desc: str, planted_title: str) -> float:
    agent_lower = agent_desc.lower()
    planted_lower = (planted_desc + " " + planted_title).lower()

    keywords = set(planted_lower.split()) - {"the", "a", "an", "is", "in", "of", "to", "and", "or", "for", "with", "not", "that", "this"}
    if not keywords:
        return 0.0

    matches = sum(1 for kw in keywords if kw in agent_lower)
    return matches / len(keywords)


# ── C5b Evaluation (Automated) ─────────────────────────────────────────────

def evaluate_c5b(entry: dict, agent_patch_path: str) -> dict:
    gold = entry["gold_standard"]
    fail_to_pass = gold.get("FAIL_TO_PASS", [])
    pass_to_pass = gold.get("PASS_TO_PASS", [])
    base_commit = entry["base_commit"]

    with tempfile.TemporaryDirectory(prefix="c5b-eval-") as tmpdir:
        worktree = Path(tmpdir) / "repo"
        subprocess.run(
            ["git", "worktree", "add", str(worktree), base_commit],
            cwd=REPO_DIR, capture_output=True, check=True,
        )

        try:
            _setup_worktree(worktree)

            agent_patch = Path(agent_patch_path).read_text()
            result = subprocess.run(
                ["git", "apply", "--allow-empty"],
                input=agent_patch, text=True,
                cwd=worktree, capture_output=True,
            )
            if result.returncode != 0:
                return {"error": "Agent patch failed to apply", "details": result.stderr}

            f2p_results = _run_tests(worktree, fail_to_pass)
            f2p_pass = sum(1 for r in f2p_results.values() if r == "passed")

            p2p_results = _run_tests(worktree, pass_to_pass)
            p2p_pass = sum(1 for r in p2p_results.values() if r == "passed")

            f2p_ratio = f2p_pass / len(fail_to_pass) if fail_to_pass else 0
            p2p_ratio = p2p_pass / len(pass_to_pass) if pass_to_pass else 1.0

            if f2p_ratio >= 1.0 and p2p_ratio >= 1.0:
                d2 = 35
            elif f2p_ratio >= 1.0 and p2p_ratio >= 0.9:
                d2 = 28
            elif f2p_ratio >= 0.7:
                d2 = 21
            elif f2p_ratio > 0:
                d2 = 14
            else:
                d2 = 7

            return {
                "instance_id": entry["instance_id"],
                "scores": {
                    "D1_root_cause": {"score": None, "max": 30, "detail": "Requires LLM-as-judge"},
                    "D2_fix_correctness": {"score": d2, "max": 35, "detail": f"F2P: {f2p_pass}/{len(fail_to_pass)}, P2P: {p2p_pass}/{len(pass_to_pass)}"},
                    "D3_fix_minimality": {"score": None, "max": 15, "detail": "Requires diff analysis"},
                    "D4_explanation": {"score": None, "max": 20, "detail": "Requires LLM-as-judge"},
                },
                "f2p_results": f2p_results,
                "p2p_results": p2p_results,
            }

        finally:
            subprocess.run(
                ["git", "worktree", "remove", str(worktree), "--force"],
                cwd=REPO_DIR, capture_output=True,
            )


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="XHS Agent Evaluation Harness")
    parser.add_argument("--category", choices=["c1", "c2", "c3", "c4", "c5a", "c5b"])
    parser.add_argument("--entry", help="Entry ID (e.g., C3-01)")
    parser.add_argument("--agent-patch", help="Path to agent's patch file (C3, C5b)")
    parser.add_argument("--agent-output", help="Path to agent's output file (C1, C2, C4, C5a)")
    parser.add_argument("--output", help="Path to write evaluation results JSON")
    args = parser.parse_args()

    if not args.category or not args.entry:
        parser.error("--category and --entry are required")

    cat_dir = args.category
    if args.category in ("c5a", "c5b"):
        cat_dir = "c5"
    entry = load_entry(cat_dir, args.entry)

    if args.category == "c3":
        if not args.agent_patch:
            parser.error("--agent-patch is required for C3")
        result = evaluate_c3(entry, args.agent_patch)

    elif args.category == "c4":
        if not args.agent_output:
            parser.error("--agent-output is required for C4")
        findings = json.load(open(args.agent_output))
        result = evaluate_c4(entry, findings)

    elif args.category == "c5b":
        if not args.agent_patch:
            parser.error("--agent-patch is required for C5b")
        result = evaluate_c5b(entry, args.agent_patch)

    elif args.category in ("c1", "c2", "c5a"):
        result = {
            "instance_id": entry["instance_id"],
            "note": f"{args.category.upper()} evaluation requires LLM-as-judge. Use the prompt template from the rubric file.",
            "rubric": entry.get("evaluation_rubric"),
        }

    else:
        parser.error(f"Unknown category: {args.category}")

    output = json.dumps(result, indent=2, ensure_ascii=False, default=str)
    if args.output:
        Path(args.output).write_text(output)
        print(f"Results written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
