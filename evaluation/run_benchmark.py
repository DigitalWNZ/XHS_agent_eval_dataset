"""
XHS Coding Agent Evaluation Benchmark Runner — All Categories

Usage:
    # C1: Requirements Understanding
    python evaluation/run_benchmark.py --category c1 --entry C1-01

    # C2: Technical Design
    python evaluation/run_benchmark.py --category c2 --entry C2-01

    # C3: Code Generation (delegates to run_c3.py logic)
    python evaluation/run_benchmark.py --category c3 --entry C3-06

    # C4: Code Review
    python evaluation/run_benchmark.py --category c4 --entry C4-01

    # C5a: Test Generation
    python evaluation/run_benchmark.py --category c5a --entry C5a-01

    # C5b: Debugging
    python evaluation/run_benchmark.py --category c5b --entry C5b-01

    # Run all entries in a category
    python evaluation/run_benchmark.py --category c4 --all

    # Common options
    --agent agy|claude          (default: agy)
    --model gemini-3.8-flash-high  (default)
    --timeout 30                (minutes, default 30)
    --dry-run                   (show prompt, don't invoke)
"""

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATASET_DIR = BASE_DIR / "dataset"
REPO_DIR = BASE_DIR / "xhs-campaign-service"
RUBRICS_DIR = BASE_DIR / "evaluation" / "rubrics"
RESULTS_DIR = BASE_DIR / "results"


# ── Dataset Loading ───────────────────────────────────────────────────────

def load_entries(category: str, entry_id: str | None = None) -> list[dict]:
    cat_dir = category if category not in ("c5a", "c5b") else "c5"
    prefix = category.upper().replace("C5A", "C5a").replace("C5B", "C5b")
    entries = []
    for f in sorted((DATASET_DIR / cat_dir).glob(f"{prefix}-*.json")):
        data = json.loads(f.read_text())
        if entry_id is None or data["instance_id"] == entry_id:
            entries.append(data)
    if entry_id and not entries:
        raise FileNotFoundError(f"Entry {entry_id} not found in {DATASET_DIR / cat_dir}")
    return entries


def load_rubric(category: str) -> dict:
    cat_key = category.replace("c5a", "c5a").replace("c5b", "c5b")
    rubric_file = RUBRICS_DIR / f"{cat_key}_{get_rubric_suffix(category)}.json"
    if rubric_file.exists():
        return json.loads(rubric_file.read_text())
    return {}


def get_rubric_suffix(category: str) -> str:
    return {
        "c1": "requirements", "c2": "design", "c3": "codegen",
        "c4": "review", "c5a": "testing", "c5b": "debug",
    }[category]


# ── Agent Invocation ──────────────────────────────────────────────────────

def invoke_agent(
    agent: str, model: str, prompt: str, work_dir: Path,
    timeout_minutes: int = 30, need_file_writes: bool = False,
    trajectory_file: Path | None = None,
) -> dict:
    timeout_secs = timeout_minutes * 60

    if agent == "agy":
        cmd = [
            "agy",
            "--input-format", "text",
            "--model", model,
            "--output-format", "stream-json",
            "--dangerously-skip-permissions",
            "--print-timeout", f"{timeout_minutes}m",
        ]
        if need_file_writes:
            cmd.extend(["--mode", "accept-edits", "--add-dir", str(work_dir)])
    elif agent == "claude":
        cmd = [
            "claude", "--print", "-",
            "--model", model,
            "--output-format", "stream-json",
            "--dangerously-skip-permissions",
        ]
    else:
        raise ValueError(f"Unknown agent: {agent}. Supported: agy, claude")

    print(f"  Invoking {agent} (model={model})...")
    start = time.time()

    result = subprocess.run(
        cmd, cwd=work_dir, capture_output=True, text=True,
        input=prompt, timeout=timeout_secs,
        env={**os.environ, "AGY_ADC_AUTH": "true"},
    )

    elapsed = time.time() - start

    # Parse stream-json (NDJSON) output
    trajectory = []
    usage = {}
    response_text = ""
    num_turns = 0
    conversation_id = ""

    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
            trajectory.append(event)

            if event.get("event") == "result":
                r = event.get("result", event)
                response_text = r.get("response", "")
                usage = r.get("usage", {})
                num_turns = r.get("num_turns", 0)
                conversation_id = r.get("conversation_id", "")
        except json.JSONDecodeError:
            trajectory.append({"raw": line})

    # Save full trajectory
    if trajectory_file:
        trajectory_file.parent.mkdir(parents=True, exist_ok=True)
        trajectory_file.write_text(
            "\n".join(json.dumps(e, ensure_ascii=False) for e in trajectory)
        )

    return {
        "returncode": result.returncode,
        "response": response_text,
        "elapsed_seconds": round(elapsed, 1),
        "usage": usage,
        "num_turns": num_turns,
        "conversation_id": conversation_id,
        "trajectory_file": str(trajectory_file) if trajectory_file else None,
        "trajectory_events": len(trajectory),
    }


def extract_agent_response(agent_result: dict) -> str:
    return agent_result.get("response", agent_result.get("stdout", ""))


# ── Git/Worktree Helpers ──────────────────────────────────────────────────

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


def capture_agent_patch(work_dir: Path) -> str:
    result = subprocess.run(
        ["git", "diff", "HEAD"], cwd=work_dir, capture_output=True, text=True,
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
            try:
                content = file_path.read_text()
            except (UnicodeDecodeError, ValueError):
                continue
            lines = content.splitlines()
            untracked_diff += f"diff --git a/{f} b/{f}\nnew file mode 100644\n--- /dev/null\n+++ b/{f}\n@@ -0,0 +1,{len(lines)} @@\n"
            for line in lines:
                untracked_diff += f"+{line}\n"

    return tracked_diff + untracked_diff


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


# ── C1/C2: LLM-as-Judge Categories ───────────────────────────────────────

def build_prompt_c1(entry: dict) -> str:
    inp = entry["input"]
    return (
        f"You are a senior software engineer performing requirements analysis.\n\n"
        f"## Context\n"
        f"Role: {inp['role']}\n"
        f"System Context: {inp['context']}\n\n"
        f"## Business Requirement\n"
        f"{inp['requirement_description']}\n\n"
        f"## Task\n"
        f"Produce a structured requirements specification that includes:\n"
        f"1. User stories with detailed acceptance criteria\n"
        f"2. State machine definition (states, transitions, guards)\n"
        f"3. Edge cases with handling strategies\n"
        f"4. Clarifying questions with assumptions if unanswered\n"
        f"5. Non-functional requirements (performance, security, data integrity)\n"
        f"6. Priority classification (P0/P1/P2)\n\n"
        f"Output as structured JSON."
    )


def build_prompt_c2(entry: dict) -> str:
    inp = entry["input"]
    return (
        f"You are a senior software architect designing a technical solution.\n\n"
        f"## Requirements Specification\n"
        f"{json.dumps(inp['requirements_spec'], indent=2, ensure_ascii=False)}\n\n"
        f"## System Context\n"
        f"{inp['system_context']}\n\n"
        f"## Constraints\n"
        f"{json.dumps(inp.get('constraints', {}), indent=2, ensure_ascii=False)}\n\n"
        f"## Task\n"
        f"Produce a technical design document that includes:\n"
        f"1. Module design (components, responsibilities, dependencies)\n"
        f"2. API design (endpoints with method, path, request/response schemas)\n"
        f"3. Data model (tables, fields, types, relationships, indexes)\n"
        f"4. Integration points with external services\n"
        f"5. Key technical decisions with rationale\n"
        f"6. Data flow for primary operations\n\n"
        f"Output as structured JSON."
    )


def run_c1_c2(entry: dict, category: str, agent: str, model: str, timeout: int) -> dict:
    instance_id = entry["instance_id"]
    print(f"\n{'='*60}")
    print(f"Running {instance_id}: {entry.get('maps_to_journey', '')}")

    prompt = build_prompt_c1(entry) if category == "c1" else build_prompt_c2(entry)
    work_dir = Path(tempfile.mkdtemp(prefix=f"{category}-"))

    try:
        traj_file = RESULTS_DIR / "trajectories" / f"{instance_id}_{agent}_{model}.jsonl"
        agent_result = invoke_agent(agent, model, prompt, work_dir, timeout, trajectory_file=traj_file)
        print(f"  Agent finished in {agent_result['elapsed_seconds']}s | {agent_result['trajectory_events']} events | {agent_result['usage'].get('total_tokens', '?')} tokens")

        agent_response = extract_agent_response(agent_result)

        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        output_file = RESULTS_DIR / "outputs" / f"{instance_id}_{agent}_{model}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(agent_response)

        rubric = load_rubric(category)
        judge_result = build_judge_payload(
            category, rubric, entry, agent_response
        )

        result = {
            "instance_id": instance_id,
            "agent": agent,
            "model": model,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_elapsed_seconds": agent_result["elapsed_seconds"],
            "usage": agent_result["usage"],
            "num_turns": agent_result["num_turns"],
            "trajectory_file": agent_result["trajectory_file"],
            "trajectory_events": agent_result["trajectory_events"],
            "agent_output_file": str(output_file),
        }

        # Run LLM-as-judge scoring
        if judge_result.get("judge_prompt"):
            judge_scores = run_judge_scoring(judge_result["judge_prompt"], agent, model, timeout_minutes=5)
            result["judge_raw_response"] = judge_scores.get("raw_response", "")[:2000]
            result["judge_usage"] = judge_scores.get("judge_usage", {})
            result["scores"] = judge_scores.get("parsed_scores") or {"note": "Judge response could not be parsed as JSON"}
            print(f"  Judge scoring complete | {judge_scores.get('judge_usage', {}).get('total_tokens', '?')} tokens")
        else:
            result["scores"] = {"error": "No judge prompt template available"}

        return result
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT after {timeout} minutes")
        return {"instance_id": instance_id, "error": f"Timeout after {timeout}m"}
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def build_judge_payload(category: str, rubric: dict, entry: dict, agent_output: str,
                        extra_replacements: dict = None, judge_dims_only: bool = False) -> dict:
    template = rubric.get("judge_prompt_template", "")
    if not template:
        return {"error": "No judge prompt template in rubric"}

    gold = entry.get("gold_standard_output", entry.get("gold_standard", {}))
    inp = entry.get("input", {})

    dims = rubric.get("dimensions", [])
    if judge_dims_only:
        dims = [d for d in dims if d.get("method", "llm_as_judge") != "automated"]

    dims_text = ""
    for d in dims:
        dims_text += f"\n### {d['id']}: {d['name']} ({d['max_score']} points)\n"
        for t in d.get("tiers", []):
            dims_text += f"- {t['score']} pts: {t['criteria']}\n"

    caps_text = ""
    for cap in rubric.get("hard_caps", []):
        caps_text += f"- {cap.get('rule', cap.get('condition', ''))}: {cap.get('effect', cap.get('action', ''))}\n"
    for d in dims:
        for cap in d.get("hard_caps", []):
            caps_text += f"- [{d['id']}] {cap.get('condition', '')}: {cap.get('effect', '')}\n"

    replacements = {
        "input_requirement": json.dumps(inp, indent=2, ensure_ascii=False),
        "agent_output": agent_output,
        "gold_standard_spec": json.dumps(gold, indent=2, ensure_ascii=False),
        "gold_standard_design": json.dumps(gold, indent=2, ensure_ascii=False),
        "gold_standard_fix": json.dumps(gold, indent=2, ensure_ascii=False),
        "requirements_spec": json.dumps(inp.get("requirements_spec", inp), indent=2, ensure_ascii=False),
        "system_context": inp.get("system_context", ""),
        "calibration_persona": rubric.get("calibration_persona", ""),
        "hard_caps_text": caps_text,
        "dimensions_text": dims_text,
    }
    if extra_replacements:
        replacements.update(extra_replacements)

    filled = template
    for key, val in replacements.items():
        filled = filled.replace("{" + key + "}", str(val))

    return {"judge_prompt": filled, "rubric_file": f"evaluation/rubrics/{category}_{get_rubric_suffix(category)}.json"}


def run_judge_scoring(judge_prompt: str, agent: str, model: str, timeout_minutes: int = 5) -> dict:
    """Send the judge prompt to an LLM and parse the structured scoring response."""
    timeout_secs = timeout_minutes * 60

    if agent == "agy":
        cmd = [
            "agy",
            "--input-format", "text",
            "--model", model,
            "--output-format", "json",
            "--dangerously-skip-permissions",
            "--print-timeout", f"{timeout_minutes}m",
        ]
    elif agent == "claude":
        cmd = [
            "claude", "--print", "-",
            "--model", model,
            "--output-format", "json",
            "--dangerously-skip-permissions",
        ]
    else:
        return {"error": f"Unknown agent: {agent}"}

    print(f"  Running LLM-as-judge ({model})...")
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, input=judge_prompt,
            timeout=timeout_secs,
            env={**os.environ, "AGY_ADC_AUTH": "true"},
        )
    except subprocess.TimeoutExpired:
        print(f"  Judge scoring timed out after {timeout_minutes}m")
        return {"error": f"Judge timeout after {timeout_minutes}m", "raw_response": "", "parsed_scores": None, "judge_usage": {}}

    response_text = result.stdout
    try:
        data = json.loads(response_text)
        response_text = data.get("response", response_text)
        judge_usage = data.get("usage", {})
    except (json.JSONDecodeError, TypeError):
        judge_usage = {}

    import re
    json_text = None
    for pattern in [r'\{[\s\S]*"total_score"[\s\S]*\}', r'\{[\s\S]*"dimension_1"[\s\S]*\}',
                    r'\{[\s\S]*"D1"[\s\S]*\}', r'\{[\s\S]*"dimensions"[\s\S]*\}']:
        m = re.search(pattern, response_text)
        if m:
            json_text = m.group()
            break
    if json_text is None:
        m = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
        if m:
            json_text = m.group(1)

    parsed_scores = None
    if json_text:
        try:
            parsed_scores = json.loads(json_text)
        except json.JSONDecodeError:
            pass

    return {
        "raw_response": response_text,
        "parsed_scores": parsed_scores,
        "judge_usage": judge_usage,
    }


# ── C4: Code Review ──────────────────────────────────────────────────────

def build_prompt_c4(entry: dict) -> str:
    inp = entry["input"]
    return (
        f"You are a senior software engineer performing a code review.\n\n"
        f"## Pull Request\n"
        f"**Title:** {inp['pr_title']}\n"
        f"**Description:** {inp['pr_description']}\n\n"
        f"## Diff\n"
        f"```diff\n{inp['bugged_diff']}\n```\n\n"
        f"## Task\n"
        f"Review this pull request for bugs, security issues, performance problems, "
        f"and design concerns. For each finding, provide:\n"
        f"1. file: the file path\n"
        f"2. line: approximate line number in the diff\n"
        f"3. severity: critical/major/minor\n"
        f"4. category: Security/Defect/Performance/Design/Maintainability\n"
        f"5. title: short summary\n"
        f"6. description: detailed explanation of the issue\n"
        f"7. suggestion: how to fix it\n\n"
        f"Output as JSON array of findings. Focus on real bugs — avoid nitpicks."
    )


def run_c4(entry: dict, agent: str, model: str, timeout: int) -> dict:
    instance_id = entry["instance_id"]
    planted = entry["planted_defects"]

    print(f"\n{'='*60}")
    print(f"Running {instance_id}: {entry.get('maps_to_journey', '')}")
    print(f"  Planted defects: {len(planted)}")

    prompt = build_prompt_c4(entry)
    work_dir = Path(tempfile.mkdtemp(prefix=f"c4-"))

    try:
        traj_file = RESULTS_DIR / "trajectories" / f"{instance_id}_{agent}_{model}.jsonl"
        agent_result = invoke_agent(agent, model, prompt, work_dir, timeout, trajectory_file=traj_file)
        print(f"  Agent finished in {agent_result['elapsed_seconds']}s | {agent_result['trajectory_events']} events | {agent_result['usage'].get('total_tokens', '?')} tokens")

        agent_response = extract_agent_response(agent_result)

        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        output_file = RESULTS_DIR / "outputs" / f"{instance_id}_{agent}_{model}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(agent_response)

        findings = parse_findings(agent_response)
        print(f"  Agent findings: {len(findings)}")

        rubric = load_rubric("c4")
        scores = score_c4(planted, findings, rubric=rubric, agent=agent, model=model)
        print(f"  Recall: {scores['recall']:.0%} (D1: {scores['D1']['score']}/25) | Precision: {scores['precision']:.0%} (D2: {scores['D2']['score']}/25) | Match: {scores['match_method']}")

        result = {
            "instance_id": instance_id,
            "agent": agent,
            "model": model,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_elapsed_seconds": agent_result["elapsed_seconds"],
            "usage": agent_result["usage"],
            "num_turns": agent_result["num_turns"],
            "trajectory_file": agent_result["trajectory_file"],
            "trajectory_events": agent_result["trajectory_events"],
            "agent_findings_count": len(findings),
            "scores": scores,
        }

        judge_result = build_judge_payload("c4", rubric, entry, agent_response,
            extra_replacements={
                "code_diff": entry["input"]["bugged_diff"],
                "agent_findings": json.dumps(findings, indent=2, ensure_ascii=False),
                "planted_defects": json.dumps(planted, indent=2, ensure_ascii=False),
            },
            judge_dims_only=True)
        if judge_result.get("judge_prompt"):
            print(f"  Running LLM-as-judge for D3 (localization), D4 (category/severity), D5 (explanation)...")
            judge_scores = run_judge_scoring(judge_result["judge_prompt"], agent, model)
            result["judge_raw_response"] = judge_scores.get("raw_response", "")[:2000]
            result["judge_usage"] = judge_scores.get("judge_usage", {})
            if judge_scores.get("parsed_scores"):
                result["scores"].update(judge_scores["parsed_scores"])
                print(f"  Judge scoring complete | {judge_scores.get('judge_usage', {}).get('total_tokens', '?')} tokens")

        return result
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT after {timeout} minutes")
        return {"instance_id": instance_id, "error": f"Timeout after {timeout}m"}
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def parse_findings(response: str) -> list[dict]:
    try:
        data = json.loads(response)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "findings" in data:
            return data["findings"]
    except json.JSONDecodeError:
        pass

    import re
    json_match = re.search(r'\[[\s\S]*\]', response)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    return []


def _score_c4_d1(recall: float) -> int:
    """D1 Detection Recall (25 pts): tier score from recall ratio."""
    if recall >= 0.9:
        return 25
    if recall >= 0.7:
        return 20
    if recall >= 0.5:
        return 15
    if recall >= 0.3:
        return 10
    return 5


def _score_c4_d2(precision: float) -> int:
    """D2 Detection Precision (25 pts): tier score from precision ratio."""
    if precision >= 0.8:
        return 25
    if precision >= 0.6:
        return 20
    if precision >= 0.4:
        return 15
    if precision >= 0.2:
        return 10
    return 5


def score_c4(planted: list[dict], findings: list[dict],
             rubric: dict = None, agent: str = None, model: str = None) -> dict:
    matched = set()
    true_positives = []
    false_positives = []

    semantic_prompt = rubric.get("semantic_match_prompt", "") if rubric else ""
    use_llm = bool(semantic_prompt and agent and model)
    if use_llm:
        print(f"  Using LLM semantic matching for finding-defect pairing...")

    for finding in findings:
        agent_file = finding.get("file", "")
        agent_desc = f"{finding.get('title', '')} {finding.get('description', '')}"
        best_match = None
        best_score = 0

        file_matched_candidates = []
        for i, defect in enumerate(planted):
            if i in matched:
                continue
            planted_file = defect.get("file", "")
            if not _file_match(agent_file, planted_file):
                continue
            file_matched_candidates.append(i)

        if use_llm and file_matched_candidates:
            llm_best_match = None
            llm_best_conf = 0
            for i in file_matched_candidates:
                defect = planted[i]
                result = _semantic_match_llm(finding, defect, semantic_prompt, agent, model)
                if result["is_same_issue"]:
                    conf = {"high": 3, "medium": 2, "low": 1}.get(result["confidence"], 0)
                    if conf > llm_best_conf:
                        llm_best_conf = conf
                        llm_best_match = i

            if llm_best_match is not None:
                matched.add(llm_best_match)
                true_positives.append({
                    "finding": finding,
                    "matched_defect_id": planted[llm_best_match]["id"],
                    "match_method": "semantic_llm",
                    "confidence": ["low", "low", "medium", "high"][llm_best_conf],
                })
                continue

        for i in file_matched_candidates:
            defect = planted[i]
            score = _keyword_overlap(agent_desc, f"{defect.get('title', '')} {defect.get('description', '')} {defect.get('root_cause', '')}")
            if score > best_score:
                best_score = score
                best_match = i

        if best_match is not None and best_score >= 0.25:
            matched.add(best_match)
            true_positives.append({
                "finding": finding,
                "matched_defect_id": planted[best_match]["id"],
                "match_method": "keyword_overlap",
                "confidence": round(best_score, 3),
            })
        else:
            false_positives.append(finding)

    total = len(planted)
    recall = len(matched) / total if total > 0 else 0
    precision = len(true_positives) / len(findings) if findings else 0

    return {
        "recall": round(recall, 3),
        "precision": round(precision, 3),
        "D1": {"score": _score_c4_d1(recall)},
        "D2": {"score": _score_c4_d2(precision)},
        "detected": len(matched),
        "total_planted": total,
        "true_positives": len(true_positives),
        "false_positives": len(false_positives),
        "match_method": "semantic_llm" if use_llm else "keyword_overlap",
        "undetected": [planted[i]["id"] for i in range(total) if i not in matched],
    }


def _file_match(a: str, b: str) -> bool:
    return (os.path.basename(a) == os.path.basename(b)
            or a.endswith(b) or b.endswith(a))


def _keyword_overlap(text_a: str, text_b: str) -> float:
    stop = {"the", "a", "an", "is", "in", "of", "to", "and", "or", "for", "with", "not", "that", "this", "it", "be", "as", "on", "at", "by"}
    words_b = set(text_b.lower().split()) - stop
    if not words_b:
        return 0.0
    return sum(1 for w in words_b if w in text_a.lower()) / len(words_b)


def _semantic_match_llm(finding: dict, defect: dict, prompt_template: str,
                        agent: str, model: str) -> dict:
    """Call LLM to determine if a finding and planted defect describe the same issue."""
    filled = prompt_template
    replacements = {
        "planted_file": defect.get("file", ""),
        "planted_lines": defect.get("line_range_in_diff", ""),
        "planted_category": defect.get("category", ""),
        "planted_description": f"{defect.get('title', '')}. {defect.get('description', '')}",
        "agent_file": finding.get("file", ""),
        "agent_lines": str(finding.get("line_range", finding.get("line", ""))),
        "agent_category": finding.get("category", ""),
        "agent_description": f"{finding.get('title', '')}. {finding.get('description', '')}",
    }
    for key, val in replacements.items():
        filled = filled.replace("{" + key + "}", str(val))

    if agent == "agy":
        cmd = ["agy", "--input-format", "text", "--model", model,
               "--output-format", "json", "--dangerously-skip-permissions",
               "--print-timeout", "2m"]
    elif agent == "claude":
        cmd = ["claude", "--print", "-", "--model", model,
               "--output-format", "json", "--dangerously-skip-permissions"]
    else:
        return {"is_same_issue": False, "confidence": "low", "reasoning": "unknown agent"}

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, input=filled, timeout=120,
            env={**os.environ, "AGY_ADC_AUTH": "true"},
        )
        response_text = result.stdout
        try:
            data = json.loads(response_text)
            response_text = data.get("response", response_text)
        except (json.JSONDecodeError, TypeError):
            pass

        import re
        m = re.search(r'\{[\s\S]*"is_same_issue"[\s\S]*\}', response_text)
        if m:
            parsed = json.loads(m.group())
            return {
                "is_same_issue": bool(parsed.get("is_same_issue", False)),
                "confidence": parsed.get("confidence", "low"),
                "reasoning": parsed.get("reasoning", ""),
            }
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
        print(f"    Semantic match LLM error: {e}")

    return {"is_same_issue": False, "confidence": "low", "reasoning": "LLM call failed"}


# ── C5a: Test Generation ─────────────────────────────────────────────────

def build_prompt_c5a(entry: dict, work_dir: Path) -> str:
    inp = entry["input"]
    impl_content = ""
    for fpath in inp.get("implementation_files", []):
        full = work_dir / fpath
        if full.exists():
            impl_content += f"\n### {fpath}\n```python\n{full.read_text()}\n```\n"

    patterns = ""
    if inp.get("existing_test_patterns"):
        patterns = f"\n## Existing Test Patterns\n{inp['existing_test_patterns']}\n"

    return (
        f"You are a senior QA engineer writing comprehensive tests.\n\n"
        f"## Module Under Test\n{inp['module_under_test']}\n\n"
        f"## Implementation Files\n{impl_content}\n"
        f"{patterns}\n"
        f"## Task\n"
        f"Write a comprehensive pytest test suite for the module. Target file: `{inp['test_target_file']}`\n\n"
        f"Requirements:\n"
        f"1. Cover all public methods/endpoints\n"
        f"2. Test success paths and error paths\n"
        f"3. Test edge cases and boundary conditions\n"
        f"4. Follow the existing test patterns (async, fixtures, httpx)\n"
        f"5. Each test should be independent and self-contained\n\n"
        f"Write the test file directly."
    )


def _score_c5a_d1(pass_count: int, test_count: int, gold_test_count: int) -> int:
    """D1 Coverage (30 pts): tier score from test pass rate and count."""
    if test_count == 0:
        return 6
    pass_rate = pass_count / test_count
    if pass_rate == 1.0 and test_count >= gold_test_count and gold_test_count > 0:
        return 30
    if pass_rate == 1.0:
        return 24
    if pass_rate >= 0.8:
        return 18
    if pass_rate >= 0.5:
        return 12
    return 6


def run_c5a(entry: dict, agent: str, model: str, timeout: int) -> dict:
    instance_id = entry["instance_id"]
    base_commit = entry["base_commit"]

    print(f"\n{'='*60}")
    print(f"Running {instance_id}: {entry.get('maps_to_journey', '')}")

    tmpdir = tempfile.mkdtemp(prefix=f"c5a-{instance_id.lower()}-")
    work_dir = Path(tmpdir) / "repo"

    try:
        setup_worktree(base_commit, work_dir)
        prompt = build_prompt_c5a(entry, work_dir)

        traj_file = RESULTS_DIR / "trajectories" / f"{instance_id}_{agent}_{model}.jsonl"
        agent_result = invoke_agent(agent, model, prompt, work_dir, timeout, need_file_writes=True, trajectory_file=traj_file)
        print(f"  Agent finished in {agent_result['elapsed_seconds']}s | {agent_result['usage'].get('total_tokens', '?')} tokens")

        agent_response = extract_agent_response(agent_result)
        test_target = entry["input"]["test_target_file"]
        test_file = work_dir / test_target

        if not test_file.exists():
            new_files = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                cwd=work_dir, capture_output=True, text=True,
            ).stdout.strip().splitlines()
            test_files = [f for f in new_files if "test" in f]
            print(f"  Target test file not found. Agent created: {test_files}")

        test_count = 0
        pass_count = 0
        if test_file.exists():
            result = subprocess.run(
                ["python3", "-m", "pytest", str(test_file), "-v", "--tb=short"],
                cwd=work_dir, capture_output=True, text=True, timeout=120,
            )
            for line in result.stdout.splitlines():
                if " PASSED" in line:
                    pass_count += 1
                    test_count += 1
                elif " FAILED" in line or " ERROR" in line:
                    test_count += 1
            print(f"  Tests: {pass_count}/{test_count} passed")

        gold_test_count = entry.get("gold_standard_tests", {}).get("test_count", 0)

        test_code = ""
        if test_file.exists():
            test_code = test_file.read_text()

        d1_score = _score_c5a_d1(pass_count, test_count, gold_test_count)
        print(f"  D1 (Coverage): {d1_score}/30")

        result = {
            "instance_id": instance_id,
            "agent": agent,
            "model": model,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_elapsed_seconds": agent_result["elapsed_seconds"],
            "usage": agent_result["usage"],
            "num_turns": agent_result["num_turns"],
            "trajectory_file": agent_result["trajectory_file"],
            "trajectory_events": agent_result["trajectory_events"],
            "scores": {
                "tests_written": test_count,
                "tests_passed": pass_count,
                "gold_test_count": gold_test_count,
                "pass_rate": round(pass_count / test_count, 3) if test_count > 0 else 0,
                "D1": {"score": d1_score},
            },
        }

        rubric = load_rubric("c5a")
        judge_result = build_judge_payload("c5a", rubric, entry, test_code,
            extra_replacements={
                "module_under_test": entry["input"]["module_under_test"],
                "agent_test_code": test_code,
                "test_results_summary": f"{pass_count}/{test_count} tests passed",
            },
            judge_dims_only=True)
        if judge_result.get("judge_prompt"):
            print(f"  Running LLM-as-judge for test quality (D2-D5)...")
            judge_scores = run_judge_scoring(judge_result["judge_prompt"], agent, model)
            result["judge_raw_response"] = judge_scores.get("raw_response", "")[:2000]
            result["judge_usage"] = judge_scores.get("judge_usage", {})
            if judge_scores.get("parsed_scores"):
                result["scores"].update(judge_scores["parsed_scores"])
                print(f"  Judge scoring complete | {judge_scores.get('judge_usage', {}).get('total_tokens', '?')} tokens")

        return result
    except subprocess.TimeoutExpired:
        return {"instance_id": instance_id, "error": f"Timeout after {timeout}m"}
    finally:
        cleanup_worktree(work_dir)
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── C5b: Debugging ───────────────────────────────────────────────────────

def _score_c5b_d2(f2p_passed: int, f2p_total: int, p2p_passed: int, p2p_total: int) -> int:
    """D2 Fix Correctness (35 pts): tier score from test results."""
    if f2p_total == 0:
        return 7
    if f2p_passed == f2p_total and p2p_passed == p2p_total:
        return 35
    if f2p_passed == f2p_total and p2p_total > 0 and p2p_passed >= p2p_total - 1:
        return 28
    if f2p_passed / f2p_total >= 0.7:
        return 21
    if f2p_passed > 0:
        return 14
    return 7


def _count_change_lines(patch: str) -> int:
    """Count added/removed lines in a diff, excluding diff metadata."""
    count = 0
    for line in patch.splitlines():
        if (line.startswith('+') or line.startswith('-')) and not line.startswith('+++') and not line.startswith('---'):
            count += 1
    return count


def _score_c5b_d3(agent_patch: str, gold_fix_diff: str) -> int:
    """D3 Fix Minimality (15 pts): tier score from patch size vs gold fix."""
    agent_changes = _count_change_lines(agent_patch)
    gold_changes = _count_change_lines(gold_fix_diff)
    if gold_changes == 0:
        gold_changes = 1
    ratio = agent_changes / gold_changes
    if ratio <= 2:
        return 15
    if ratio <= 4:
        return 12
    if ratio <= 8:
        return 9
    if ratio <= 15:
        return 6
    return 3


def build_prompt_c5b(entry: dict) -> str:
    inp = entry["input"]
    return (
        f"You are a senior software engineer debugging a production issue.\n\n"
        f"## Bug Report\n{inp['bug_report']}\n\n"
        f"## Stack Trace\n```\n{inp.get('stack_trace', 'N/A')}\n```\n\n"
        f"## Bugged File\n"
        f"The bug is in `{inp['bugged_file']}` in this codebase.\n\n"
        f"## Task\n"
        f"1. Read the file `{inp['bugged_file']}` in the current workspace\n"
        f"2. Identify the root cause of the bug\n"
        f"3. Fix the bug by editing the file directly\n"
        f"4. Make minimal changes — fix only the bug, do not refactor\n"
    )


def run_c5b(entry: dict, agent: str, model: str, timeout: int) -> dict:
    instance_id = entry["instance_id"]
    base_commit = entry["base_commit"]
    gold = entry["gold_standard"]

    print(f"\n{'='*60}")
    print(f"Running {instance_id}")
    print(f"  FAIL_TO_PASS: {len(gold.get('FAIL_TO_PASS', []))} tests")

    tmpdir = tempfile.mkdtemp(prefix=f"c5b-{instance_id.lower()}-")
    work_dir = Path(tmpdir) / "repo"

    try:
        setup_worktree(base_commit, work_dir)

        # Inject the bugged code into the worktree so the agent can find and fix it
        bugged_file = work_dir / entry["input"]["bugged_file"]
        bugged_file.parent.mkdir(parents=True, exist_ok=True)
        bugged_file.write_text(entry["input"]["bugged_code"])

        prompt = build_prompt_c5b(entry)

        traj_file = RESULTS_DIR / "trajectories" / f"{instance_id}_{agent}_{model}.jsonl"
        agent_result = invoke_agent(agent, model, prompt, work_dir, timeout, need_file_writes=True, trajectory_file=traj_file)
        print(f"  Agent finished in {agent_result['elapsed_seconds']}s | {agent_result['usage'].get('total_tokens', '?')} tokens")

        agent_patch = capture_agent_patch(work_dir)
        patch_lines = len(agent_patch.splitlines())
        print(f"  Agent patch: {patch_lines} lines")

        # Apply test_patch if present (injects FAIL_TO_PASS test functions)
        test_patch = entry.get("test_patch", "")
        if test_patch:
            for line in test_patch.splitlines():
                if line.startswith("+++ b/"):
                    conflict_file = work_dir / line[6:]
                    if conflict_file.exists():
                        pass  # appending to existing file, git apply handles it
            tp_result = subprocess.run(
                ["git", "apply", "--allow-empty"],
                input=test_patch, text=True, cwd=work_dir, capture_output=True,
            )
            if tp_result.returncode != 0:
                print(f"  Test patch failed to apply: {tp_result.stderr[:200]}")

        f2p = gold.get("FAIL_TO_PASS", [])
        p2p = gold.get("PASS_TO_PASS", [])

        f2p_results = run_tests(work_dir, f2p)
        p2p_results = run_tests(work_dir, p2p)

        f2p_passed = sum(1 for v in f2p_results.values() if v == "passed")
        p2p_passed = sum(1 for v in p2p_results.values() if v == "passed")

        print(f"  FAIL_TO_PASS: {f2p_passed}/{len(f2p)}")
        print(f"  PASS_TO_PASS: {p2p_passed}/{len(p2p)}")

        resolved = f2p_passed == len(f2p) and p2p_passed == len(p2p) if f2p else False

        # D2: Fix Correctness (35 pts) — tier scoring from test results
        d2_score = _score_c5b_d2(f2p_passed, len(f2p), p2p_passed, len(p2p))

        # D3: Fix Minimality (15 pts) — tier scoring from patch size vs gold fix
        gold_fix_diff = gold.get("fix_diff", "")
        d3_score = _score_c5b_d3(agent_patch, gold_fix_diff)

        print(f"  D2 (Fix Correctness): {d2_score}/35 | D3 (Fix Minimality): {d3_score}/15")

        agent_response = extract_agent_response(agent_result)

        result = {
            "instance_id": instance_id,
            "agent": agent,
            "model": model,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_elapsed_seconds": agent_result["elapsed_seconds"],
            "usage": agent_result["usage"],
            "num_turns": agent_result["num_turns"],
            "trajectory_file": agent_result["trajectory_file"],
            "trajectory_events": agent_result["trajectory_events"],
            "patch_lines": patch_lines,
            "test_results": {
                "f2p_passed": f2p_passed, "f2p_total": len(f2p),
                "p2p_passed": p2p_passed, "p2p_total": len(p2p),
            },
            "scores": {
                "resolved": resolved,
                "D2": {"score": d2_score},
                "D3": {"score": d3_score},
            },
        }

        rubric = load_rubric("c5b")
        judge_result = build_judge_payload("c5b", rubric, entry, agent_response,
            extra_replacements={
                "bug_report": entry["input"]["bug_report"],
                "bugged_code": entry["input"]["bugged_code"],
                "agent_response": agent_response,
                "agent_patch": agent_patch,
                "gold_fix": json.dumps(gold, indent=2, ensure_ascii=False),
            },
            judge_dims_only=True)
        if judge_result.get("judge_prompt"):
            print(f"  Running LLM-as-judge for debug quality (D1, D4)...")
            judge_scores = run_judge_scoring(judge_result["judge_prompt"], agent, model)
            result["judge_raw_response"] = judge_scores.get("raw_response", "")[:2000]
            result["judge_usage"] = judge_scores.get("judge_usage", {})
            if judge_scores.get("parsed_scores"):
                result["scores"].update(judge_scores["parsed_scores"])
                print(f"  Judge scoring complete | {judge_scores.get('judge_usage', {}).get('total_tokens', '?')} tokens")

        return result
    except subprocess.TimeoutExpired:
        return {"instance_id": instance_id, "error": f"Timeout after {timeout}m"}
    finally:
        cleanup_worktree(work_dir)
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── C3: Code Generation (reuse from run_c3.py) ───────────────────────────

def _score_c3_d1(f2p_passed: int, f2p_total: int) -> int:
    """D1 Functional Correctness (25 pts): tier score from FAIL_TO_PASS results."""
    if f2p_total == 0:
        return 0
    rate = f2p_passed / f2p_total
    if rate == 1.0:
        return 25
    if rate >= 0.8:
        return 20
    if rate >= 0.6:
        return 15
    if rate >= 0.3:
        return 10
    return 0


def _score_c3_d2(p2p_passed: int, p2p_total: int) -> int:
    """D2 Regression Safety (10 pts): tier score from PASS_TO_PASS results."""
    if p2p_total == 0:
        return 10
    rate = p2p_passed / p2p_total
    if rate == 1.0:
        return 10
    if rate >= 0.9:
        return 7
    if rate >= 0.7:
        return 3
    return 0


def run_c3(entry: dict, agent: str, model: str, timeout: int) -> dict:
    instance_id = entry["instance_id"]
    base_commit = entry["base_commit"]

    print(f"\n{'='*60}")
    print(f"Running {instance_id}: {entry.get('maps_to_journey', '')}")
    print(f"  FAIL_TO_PASS: {len(entry['FAIL_TO_PASS'])} tests | PASS_TO_PASS: {len(entry['PASS_TO_PASS'])} tests")

    tmpdir = tempfile.mkdtemp(prefix=f"c3-{instance_id.lower()}-")
    work_dir = Path(tmpdir) / "repo"

    try:
        setup_worktree(base_commit, work_dir)

        traj_file = RESULTS_DIR / "trajectories" / f"{instance_id}_{agent}_{model}.jsonl"
        agent_result = invoke_agent(agent, model, entry["problem_statement"], work_dir, timeout, need_file_writes=True, trajectory_file=traj_file)
        print(f"  Agent finished in {agent_result['elapsed_seconds']}s | {agent_result['usage'].get('total_tokens', '?')} tokens")

        agent_patch = capture_agent_patch(work_dir)
        patch_lines = len(agent_patch.splitlines())
        print(f"  Agent patch: {patch_lines} lines")

        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        patch_dir = RESULTS_DIR / "patches"
        patch_dir.mkdir(parents=True, exist_ok=True)
        (patch_dir / f"{instance_id}_{agent}_{model}.patch").write_text(agent_patch)

        # Remove agent-created test files before applying test_patch
        test_patch = entry["test_patch"]
        for line in test_patch.splitlines():
            if line.startswith("+++ b/"):
                conflict_file = work_dir / line[6:]
                if conflict_file.exists():
                    conflict_file.unlink()

        result = subprocess.run(
            ["git", "apply", "--allow-empty"],
            input=test_patch, text=True, cwd=work_dir, capture_output=True,
        )
        if result.returncode != 0:
            print(f"  Test patch failed to apply: {result.stderr[:200]}")
            return {
                "instance_id": instance_id, "error": "test_patch conflict",
                "scores": {"resolved": False, "D1": {"score": 0}, "D2": {"score": 0}},
            }

        f2p = run_tests(work_dir, entry["FAIL_TO_PASS"])
        p2p = run_tests(work_dir, entry["PASS_TO_PASS"])

        f2p_passed = sum(1 for v in f2p.values() if v == "passed")
        p2p_passed = sum(1 for v in p2p.values() if v == "passed")
        f2p_total = len(entry["FAIL_TO_PASS"])
        p2p_total = len(entry["PASS_TO_PASS"])

        print(f"  FAIL_TO_PASS: {f2p_passed}/{f2p_total}")
        print(f"  PASS_TO_PASS: {p2p_passed}/{p2p_total}")

        resolved = f2p_passed == f2p_total and p2p_passed == p2p_total

        d1_score = _score_c3_d1(f2p_passed, f2p_total)
        d2_score = _score_c3_d2(p2p_passed, p2p_total)
        print(f"  D1 (Functional Correctness): {d1_score}/25 | D2 (Regression Safety): {d2_score}/10")

        result = {
            "instance_id": instance_id,
            "agent": agent,
            "model": model,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_elapsed_seconds": agent_result["elapsed_seconds"],
            "usage": agent_result["usage"],
            "num_turns": agent_result["num_turns"],
            "trajectory_file": agent_result["trajectory_file"],
            "trajectory_events": agent_result["trajectory_events"],
            "patch_lines": patch_lines,
            "test_results": {
                "f2p_passed": f2p_passed, "f2p_total": f2p_total,
                "p2p_passed": p2p_passed, "p2p_total": p2p_total,
            },
            "scores": {
                "resolved": resolved,
                "D1": {"score": d1_score},
                "D2": {"score": d2_score},
            },
        }

        rubric = load_rubric("c3")
        judge_result = build_judge_payload("c3", rubric, entry, agent_patch,
            extra_replacements={
                "task_description": entry["problem_statement"],
                "agent_patch": agent_patch,
            },
            judge_dims_only=True)
        if judge_result.get("judge_prompt"):
            print(f"  Running LLM-as-judge for code quality (D3-D7)...")
            judge_scores = run_judge_scoring(judge_result["judge_prompt"], agent, model)
            result["judge_raw_response"] = judge_scores.get("raw_response", "")[:2000]
            result["judge_usage"] = judge_scores.get("judge_usage", {})
            if judge_scores.get("parsed_scores"):
                result["scores"].update(judge_scores["parsed_scores"])
                print(f"  Judge scoring complete | {judge_scores.get('judge_usage', {}).get('total_tokens', '?')} tokens")

        return result
    except subprocess.TimeoutExpired:
        return {"instance_id": instance_id, "error": f"Timeout after {timeout}m", "scores": {"resolved": False}}
    finally:
        cleanup_worktree(work_dir)
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── Dispatch & Reporting ──────────────────────────────────────────────────

RUNNERS = {
    "c1": lambda e, a, m, t: run_c1_c2(e, "c1", a, m, t),
    "c2": lambda e, a, m, t: run_c1_c2(e, "c2", a, m, t),
    "c3": run_c3,
    "c4": run_c4,
    "c5a": run_c5a,
    "c5b": run_c5b,
}


def format_tokens(n) -> str:
    if not n or n == "?":
        return "?"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def print_summary(category: str, results: list[dict]) -> None:
    print(f"\n{'='*80}")
    print(f"SUMMARY — {category.upper()}")
    print(f"{'='*80}")

    if category == "c3":
        print(f"{'Entry':<10} {'F2P':>8} {'P2P':>8} {'Resolved':>9} {'Time':>7} {'Tokens':>8} {'Turns':>6}")
        print("-" * 60)
        for r in results:
            tr = r.get("test_results", {})
            u = r.get("usage", {})
            print(f"{r['instance_id']:<10} {tr.get('f2p_passed','?')}/{tr.get('f2p_total','?'):>5} {tr.get('p2p_passed','?')}/{tr.get('p2p_total','?'):>5} {'YES' if r.get('scores',{}).get('resolved') else 'NO':>9} {r.get('agent_elapsed_seconds','?'):>6}s {format_tokens(u.get('total_tokens')):>8} {r.get('num_turns','?'):>6}")

    elif category == "c4":
        print(f"{'Entry':<10} {'Recall':>8} {'Prec':>8} {'Found':>8} {'Time':>7} {'Tokens':>8} {'Turns':>6}")
        print("-" * 60)
        for r in results:
            sc = r.get("scores", {})
            u = r.get("usage", {})
            print(f"{r['instance_id']:<10} {sc.get('recall',0):>7.0%} {sc.get('precision',0):>7.0%} {sc.get('detected','?')}/{sc.get('total_planted','?'):>4} {r.get('agent_elapsed_seconds','?'):>6}s {format_tokens(u.get('total_tokens')):>8} {r.get('num_turns','?'):>6}")

    elif category in ("c5b", "c3"):
        print(f"{'Entry':<10} {'F2P':>8} {'P2P':>8} {'Resolved':>9} {'Time':>7} {'Tokens':>8} {'Turns':>6}")
        print("-" * 60)
        for r in results:
            tr = r.get("test_results", {})
            u = r.get("usage", {})
            print(f"{r['instance_id']:<10} {tr.get('f2p_passed','?')}/{tr.get('f2p_total','?'):>5} {tr.get('p2p_passed','?')}/{tr.get('p2p_total','?'):>5} {'YES' if r.get('scores',{}).get('resolved') else 'NO':>9} {r.get('agent_elapsed_seconds','?'):>6}s {format_tokens(u.get('total_tokens')):>8} {r.get('num_turns','?'):>6}")

    elif category == "c5a":
        print(f"{'Entry':<10} {'Written':>8} {'Passed':>8} {'Rate':>8} {'Time':>7} {'Tokens':>8} {'Turns':>6}")
        print("-" * 60)
        for r in results:
            sc = r.get("scores", {})
            u = r.get("usage", {})
            print(f"{r['instance_id']:<10} {sc.get('tests_written','?'):>8} {sc.get('tests_passed','?'):>8} {sc.get('pass_rate',0):>7.0%} {r.get('agent_elapsed_seconds','?'):>6}s {format_tokens(u.get('total_tokens')):>8} {r.get('num_turns','?'):>6}")

    else:  # c1, c2
        print(f"{'Entry':<10} {'Time':>7} {'Tokens':>8} {'Turns':>6} {'Score':>8}")
        print("-" * 45)
        for r in results:
            u = r.get("usage", {})
            sc = r.get("scores", {})
            total = "?"
            if isinstance(sc, dict) and "dimensions" in sc:
                total = sum(d.get("score", 0) for d in sc["dimensions"].values() if isinstance(d, dict))
            elif isinstance(sc, dict) and any(k.startswith("D") for k in sc):
                total = sum(v.get("score", 0) for k, v in sc.items() if k.startswith("D") and isinstance(v, dict))
            print(f"{r['instance_id']:<10} {r.get('agent_elapsed_seconds','?'):>6}s {format_tokens(u.get('total_tokens')):>8} {r.get('num_turns','?'):>6} {total:>8}")

    # Cost/efficiency summary
    print(f"\n--- Efficiency Metrics ---")
    total_time = sum(r.get("agent_elapsed_seconds", 0) for r in results)
    total_tokens = sum(r.get("usage", {}).get("total_tokens", 0) for r in results)
    total_input = sum(r.get("usage", {}).get("input_tokens", 0) for r in results)
    total_output = sum(r.get("usage", {}).get("output_tokens", 0) for r in results)
    total_thinking = sum(r.get("usage", {}).get("thinking_tokens", 0) for r in results)
    total_turns = sum(r.get("num_turns", 0) for r in results)
    print(f"Total time: {total_time:.0f}s | Total tokens: {format_tokens(total_tokens)} (in:{format_tokens(total_input)} out:{format_tokens(total_output)} think:{format_tokens(total_thinking)}) | Total turns: {total_turns}")
    print(f"{'='*80}")


def main():
    parser = argparse.ArgumentParser(description="XHS Agent Evaluation Benchmark Runner")
    parser.add_argument("--category", required=True, choices=["c1", "c2", "c3", "c4", "c5a", "c5b"])
    parser.add_argument("--entry", help="Single entry ID (e.g., C3-01)")
    parser.add_argument("--all", action="store_true", help="Run all entries in category")
    parser.add_argument("--agent", default="agy", choices=["agy", "claude"])
    parser.add_argument("--model", default="gemini-3.8-flash-high")
    parser.add_argument("--timeout", type=int, default=30, help="Agent timeout in minutes")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.entry and not args.all:
        parser.error("Specify --entry or --all")

    entries = load_entries(args.category, args.entry if not args.all else None)
    print(f"Loaded {len(entries)} {args.category.upper()} entries")
    print(f"Agent: {args.agent} | Model: {args.model} | Timeout: {args.timeout}m")

    if args.dry_run:
        for entry in entries:
            print(f"\n{'='*60}")
            print(f"{entry['instance_id']}: {entry.get('maps_to_journey', '')}")
            if args.category == "c1":
                print(build_prompt_c1(entry)[:500])
            elif args.category == "c2":
                print(build_prompt_c2(entry)[:500])
            elif args.category == "c4":
                print(build_prompt_c4(entry)[:500])
        return

    runner = RUNNERS[args.category]
    results = []
    for entry in entries:
        result = runner(entry, args.agent, args.model, args.timeout)
        results.append(result)

    print_summary(args.category, results)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_file = RESULTS_DIR / f"{args.category}_{args.agent}_{args.model}_{ts}.json"
    report = {
        "benchmark": "xhs-agent-eval",
        "category": args.category.upper(),
        "agent": args.agent,
        "model": args.model,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entries": results,
    }
    report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    print(f"\nResults saved to {report_file}")


if __name__ == "__main__":
    main()
