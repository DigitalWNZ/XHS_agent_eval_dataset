"""
C3 Code Generation Benchmark Runner

Submits C3 tasks to a coding agent (Antigravity CLI or Claude Code),
captures the agent's patch, and evaluates it against the test suite.

Usage:
    # Run single entry with Antigravity
    python evaluation/run_c3.py --entry C3-01 --agent agy --model gemini-3.8-flash --project cloud-llm-preview1

    # Run single entry with Claude Code
    python evaluation/run_c3.py --entry C3-01 --agent claude --model claude-sonnet-5

    # Run all C3 entries
    python evaluation/run_c3.py --all --agent agy --model gemini-3.8-flash --project cloud-llm-preview1

    # Dry run (show prompt only, don't invoke agent)
    python evaluation/run_c3.py --entry C3-01 --dry-run
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATASET_DIR = BASE_DIR / "dataset" / "c3"
REPO_DIR = BASE_DIR / "xhs-campaign-service"
RESULTS_DIR = BASE_DIR / "results"


def load_entries(entry_id: str | None = None) -> list[dict]:
    entries = []
    for f in sorted(DATASET_DIR.glob("C3-*.json")):
        data = json.loads(f.read_text())
        if entry_id is None or data["instance_id"] == entry_id:
            entries.append(data)
    if entry_id and not entries:
        raise FileNotFoundError(f"Entry {entry_id} not found in {DATASET_DIR}")
    return entries


def setup_worktree(base_commit: str, work_dir: Path) -> None:
    subprocess.run(
        ["git", "worktree", "add", str(work_dir), base_commit],
        cwd=REPO_DIR, capture_output=True, check=True,
    )
    subprocess.run(
        ["pip", "install", "-q", "-e", ".", "--break-system-packages"],
        cwd=work_dir, capture_output=True, timeout=120,
    )


def cleanup_worktree(work_dir: Path) -> None:
    subprocess.run(
        ["git", "worktree", "remove", str(work_dir), "--force"],
        cwd=REPO_DIR, capture_output=True,
    )


def invoke_agent(
    agent: str,
    model: str,
    prompt: str,
    work_dir: Path,
    timeout_minutes: int = 15,
    project: str | None = None,
) -> dict:
    timeout_secs = timeout_minutes * 60

    if agent == "agy":
        cmd = [
            "agy", "-p", prompt,
            "--model", model,
            "--mode", "accept-edits",
            "--output-format", "json",
            "--dangerously-skip-permissions",
            "--add-dir", str(work_dir),
            "--print-timeout", f"{timeout_minutes}m",
        ]
        if project:
            cmd.extend(["--project", project])
    elif agent == "claude":
        cmd = [
            "claude", "--print", prompt,
            "--model", model,
            "--output-format", "json",
            "--dangerously-skip-permissions",
        ]
    else:
        raise ValueError(f"Unknown agent: {agent}. Supported: agy, claude")

    print(f"  Invoking {agent} (model={model})...")
    start = time.time()

    result = subprocess.run(
        cmd,
        cwd=work_dir,
        capture_output=True,
        text=True,
        timeout=timeout_secs,
        env={
            **os.environ,
            "PATH": os.environ.get("PATH", ""),
            "AGY_ADC_AUTH": "true",
        },
    )

    elapsed = time.time() - start

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "elapsed_seconds": round(elapsed, 1),
    }


def capture_agent_patch(work_dir: Path) -> str:
    result = subprocess.run(
        ["git", "diff", "HEAD"],
        cwd=work_dir, capture_output=True, text=True,
    )
    tracked_diff = result.stdout

    result = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=work_dir, capture_output=True, text=True,
    )
    new_files = result.stdout.strip().splitlines()

    untracked_diff = ""
    for f in new_files:
        file_path = work_dir / f
        if file_path.is_file():
            content = file_path.read_text()
            lines = content.splitlines()
            untracked_diff += f"diff --git a/{f} b/{f}\n"
            untracked_diff += f"new file mode 100644\n"
            untracked_diff += f"--- /dev/null\n"
            untracked_diff += f"+++ b/{f}\n"
            untracked_diff += f"@@ -0,0 +1,{len(lines)} @@\n"
            for line in lines:
                untracked_diff += f"+{line}\n"

    return tracked_diff + untracked_diff


def apply_patch_and_test(
    work_dir: Path,
    test_patch: str,
    fail_to_pass: list[str],
    pass_to_pass: list[str],
) -> dict:
    # Extract test file paths from test_patch and remove agent-created versions
    # so test_patch can apply cleanly (SWE-bench convention: harness owns tests)
    for line in test_patch.splitlines():
        if line.startswith("+++ b/"):
            rel_path = line[6:]
            agent_file = work_dir / rel_path
            if agent_file.exists():
                agent_file.unlink()

    result = subprocess.run(
        ["git", "apply", "--allow-empty"],
        input=test_patch, text=True,
        cwd=work_dir, capture_output=True,
    )
    if result.returncode != 0:
        return {
            "test_patch_applied": False,
            "error": result.stderr,
            "f2p_passed": 0, "f2p_total": len(fail_to_pass),
            "p2p_passed": 0, "p2p_total": len(pass_to_pass),
        }

    f2p = run_tests(work_dir, fail_to_pass)
    p2p = run_tests(work_dir, pass_to_pass)

    return {
        "test_patch_applied": True,
        "f2p_passed": sum(1 for v in f2p.values() if v == "passed"),
        "f2p_total": len(fail_to_pass),
        "f2p_details": f2p,
        "p2p_passed": sum(1 for v in p2p.values() if v == "passed"),
        "p2p_total": len(pass_to_pass),
        "p2p_details": p2p,
    }


def run_tests(work_dir: Path, test_names: list[str]) -> dict[str, str]:
    if not test_names:
        return {}
    result = subprocess.run(
        ["python3", "-m", "pytest", "--tb=short", "-v"] + test_names,
        cwd=work_dir, capture_output=True, text=True, timeout=180,
    )
    results = {}
    for line in result.stdout.splitlines():
        line = line.strip()
        if " PASSED" in line:
            results[line.split(" PASSED")[0].strip()] = "passed"
        elif " FAILED" in line:
            results[line.split(" FAILED")[0].strip()] = "failed"
        elif " ERROR" in line:
            results[line.split(" ERROR")[0].strip()] = "error"
    for t in test_names:
        if t not in results:
            results[t] = "not_run"
    return results


def compute_scores(test_results: dict) -> dict:
    f2p_ratio = test_results["f2p_passed"] / test_results["f2p_total"] if test_results["f2p_total"] > 0 else 0
    p2p_ratio = test_results["p2p_passed"] / test_results["p2p_total"] if test_results["p2p_total"] > 0 else 0

    if f2p_ratio >= 1.0:
        d1 = 25
    elif f2p_ratio >= 0.8:
        d1 = 20
    elif f2p_ratio >= 0.6:
        d1 = 15
    elif f2p_ratio >= 0.3:
        d1 = 10
    else:
        d1 = 0

    if p2p_ratio >= 1.0:
        d2 = 10
    elif p2p_ratio >= 0.9:
        d2 = 7
    elif p2p_ratio >= 0.7:
        d2 = 3
    else:
        d2 = 0

    resolved = f2p_ratio >= 1.0 and p2p_ratio >= 1.0

    return {
        "D1_functional_correctness": {"score": d1, "max": 25, "ratio": round(f2p_ratio, 3)},
        "D2_regression_safety": {"score": d2, "max": 10, "ratio": round(p2p_ratio, 3)},
        "resolved": resolved,
        "automated_subtotal": d1 + d2,
    }


def run_entry(entry: dict, agent: str, model: str, timeout_minutes: int, project: str | None = None) -> dict:
    instance_id = entry["instance_id"]
    base_commit = entry["base_commit"]
    problem_statement = entry["problem_statement"]
    test_patch = entry["test_patch"]
    fail_to_pass = entry["FAIL_TO_PASS"]
    pass_to_pass = entry["PASS_TO_PASS"]

    print(f"\n{'='*60}")
    print(f"Running {instance_id}: {entry.get('maps_to_journey', '')}")
    print(f"  Base commit: {base_commit}")
    print(f"  FAIL_TO_PASS: {len(fail_to_pass)} tests")
    print(f"  PASS_TO_PASS: {len(pass_to_pass)} tests")

    tmpdir = tempfile.mkdtemp(prefix=f"c3-{instance_id.lower()}-")
    work_dir = Path(tmpdir) / "repo"

    try:
        print(f"  Setting up worktree at {base_commit}...")
        setup_worktree(base_commit, work_dir)

        agent_result = invoke_agent(agent, model, problem_statement, work_dir, timeout_minutes, project)
        print(f"  Agent finished in {agent_result['elapsed_seconds']}s (exit={agent_result['returncode']})")

        if agent_result["returncode"] != 0:
            print(f"  Agent failed: {agent_result['stderr'][:200]}")

        agent_patch = capture_agent_patch(work_dir)
        patch_lines = len(agent_patch.splitlines())
        print(f"  Agent patch: {patch_lines} lines")

        patch_dir = RESULTS_DIR / "patches"
        patch_dir.mkdir(parents=True, exist_ok=True)
        patch_file = patch_dir / f"{instance_id}_{agent}_{model}.patch"
        patch_file.write_text(agent_patch)

        print(f"  Running test suite...")
        test_results = apply_patch_and_test(work_dir, test_patch, fail_to_pass, pass_to_pass)
        scores = compute_scores(test_results)

        print(f"  FAIL_TO_PASS: {test_results['f2p_passed']}/{test_results['f2p_total']}")
        print(f"  PASS_TO_PASS: {test_results['p2p_passed']}/{test_results['p2p_total']}")
        print(f"  Resolved: {'YES' if scores['resolved'] else 'NO'}")

        return {
            "instance_id": instance_id,
            "agent": agent,
            "model": model,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_elapsed_seconds": agent_result["elapsed_seconds"],
            "agent_exit_code": agent_result["returncode"],
            "patch_lines": patch_lines,
            "patch_file": str(patch_file),
            "test_results": {
                "f2p_passed": test_results["f2p_passed"],
                "f2p_total": test_results["f2p_total"],
                "p2p_passed": test_results["p2p_passed"],
                "p2p_total": test_results["p2p_total"],
            },
            "scores": scores,
        }

    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT after {timeout_minutes} minutes")
        return {
            "instance_id": instance_id,
            "agent": agent,
            "model": model,
            "error": f"Agent timed out after {timeout_minutes} minutes",
            "scores": {"D1_functional_correctness": {"score": 0}, "D2_regression_safety": {"score": 0}, "resolved": False},
        }
    except Exception as e:
        print(f"  ERROR: {e}")
        return {
            "instance_id": instance_id,
            "agent": agent,
            "model": model,
            "error": str(e),
            "scores": {"D1_functional_correctness": {"score": 0}, "D2_regression_safety": {"score": 0}, "resolved": False},
        }
    finally:
        cleanup_worktree(work_dir)
        shutil.rmtree(tmpdir, ignore_errors=True)


def print_summary(results: list[dict]) -> None:
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"{'Entry':<10} {'F2P':>10} {'P2P':>10} {'D1':>5} {'D2':>5} {'Resolved':>10} {'Time':>8}")
    print("-" * 60)

    total_resolved = 0
    for r in results:
        tr = r.get("test_results", {})
        sc = r.get("scores", {})
        f2p = f"{tr.get('f2p_passed', '?')}/{tr.get('f2p_total', '?')}"
        p2p = f"{tr.get('p2p_passed', '?')}/{tr.get('p2p_total', '?')}"
        d1 = sc.get("D1_functional_correctness", {}).get("score", "?")
        d2 = sc.get("D2_regression_safety", {}).get("score", "?")
        resolved = "YES" if sc.get("resolved") else "NO"
        elapsed = f"{r.get('agent_elapsed_seconds', '?')}s"
        if sc.get("resolved"):
            total_resolved += 1
        print(f"{r['instance_id']:<10} {f2p:>10} {p2p:>10} {d1:>5} {d2:>5} {resolved:>10} {elapsed:>8}")

    print("-" * 60)
    print(f"Resolved: {total_resolved}/{len(results)} ({total_resolved/len(results)*100:.0f}%)")


def main():
    parser = argparse.ArgumentParser(description="C3 Code Generation Benchmark Runner")
    parser.add_argument("--entry", help="Single entry ID (e.g., C3-01)")
    parser.add_argument("--all", action="store_true", help="Run all C3 entries")
    parser.add_argument("--agent", default="agy", choices=["agy", "claude"], help="Agent to evaluate")
    parser.add_argument("--model", default="gemini-3.8-flash-high", help="Model to use")
    parser.add_argument("--project", default=None, help="GCP project for Antigravity (e.g., cloud-llm-preview1)")
    parser.add_argument("--timeout", type=int, default=30, help="Agent timeout in minutes")
    parser.add_argument("--dry-run", action="store_true", help="Show prompt only")
    parser.add_argument("--results-dir", type=str, help="Custom results directory")
    args = parser.parse_args()

    if not args.entry and not args.all:
        parser.error("Specify --entry C3-XX or --all")

    global RESULTS_DIR
    if args.results_dir:
        RESULTS_DIR = Path(args.results_dir)

    entries = load_entries(args.entry if not args.all else None)
    print(f"Loaded {len(entries)} C3 entries")
    print(f"Agent: {args.agent} | Model: {args.model} | Project: {args.project or 'N/A'} | Timeout: {args.timeout}m")

    if args.dry_run:
        for entry in entries:
            print(f"\n{'='*60}")
            print(f"{entry['instance_id']}: {entry.get('maps_to_journey', '')}")
            print(f"Base commit: {entry['base_commit']}")
            print(f"FAIL_TO_PASS: {len(entry['FAIL_TO_PASS'])} tests")
            print(f"PASS_TO_PASS: {len(entry['PASS_TO_PASS'])} tests")
            print(f"\n--- PROMPT ---")
            print(entry["problem_statement"][:500] + "..." if len(entry["problem_statement"]) > 500 else entry["problem_statement"])
        return

    results = []
    for entry in entries:
        result = run_entry(entry, args.agent, args.model, args.timeout, args.project)
        results.append(result)

    print_summary(results)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_file = RESULTS_DIR / f"c3_{args.agent}_{args.model}_{ts}.json"
    report = {
        "benchmark": "xhs-agent-eval",
        "category": "C3",
        "agent": args.agent,
        "model": args.model,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entries": results,
        "summary": {
            "total": len(results),
            "resolved": sum(1 for r in results if r.get("scores", {}).get("resolved")),
            "resolve_rate": sum(1 for r in results if r.get("scores", {}).get("resolved")) / len(results) if results else 0,
        },
    }
    report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nResults saved to {report_file}")


if __name__ == "__main__":
    main()
