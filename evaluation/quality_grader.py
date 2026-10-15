#!/usr/bin/env python3
"""Coding-quality grader for C6 / C7 / C8 / C9 trials (rubric v3: evaluation/rubrics/coding_quality.json).

Simple model:
  * pass/fail (D1) is the source benchmark's hidden-test verdict, exactly as before;
  * one LLM judge call per trial (Claude Opus 5.5) grades 3 common items (Readability,
    Maintainability, Robustness) + the case's 1-2 items (evaluation/rubrics/tasks/<ID>.json),
    each perfect / accept / bad; quality score = 100 x mean item score;
  * a validity audit (not scored) flags trials that accessed hidden tests / reference solutions /
    the upstream fix or tampered with tests.

Output: <trial_dir>/quality.json (+ judge_v3_<judge>.json cache). Usage:
  python3 evaluation/quality_grader.py --all --jobs 4
  python3 evaluation/quality_grader.py results/c6_runs/C6-01_agy_*
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import fnmatch
import glob
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FRAMEWORK = json.loads((BASE_DIR / "evaluation/rubrics/coding_quality.json").read_text())
LEVEL_SCORE = {k: v["score"] for k, v in FRAMEWORK["levels"].items()}
OVERRIDES_FILE = BASE_DIR / "results" / "quality_overrides.json"
DEFAULT_JUDGE = "claude:claude-opus-5-5"

# ── Entries and run-id mapping ─────────────────────────────────────────────

_ENTRIES: dict[str, dict] = {}



def with_task_rubric(e: dict) -> dict:
    """Attach the case rubric (evaluation/rubrics/tasks/<ID>.json) as e["case_rubric"]."""
    p = BASE_DIR / e.get("task_rubric", f"evaluation/rubrics/tasks/{e['instance_id']}.json")
    if p.exists():
        e = {**e, "case_rubric": json.loads(p.read_text()), "rubric_config": {}}
    return e


_ENTRIES_LOCK = threading.Lock()


def entries() -> dict[str, dict]:
    with _ENTRIES_LOCK:  # graded from several threads; fill once, atomically
        if not _ENTRIES:
            loaded = {}
            for f in glob.glob(str(BASE_DIR / "dataset/c[6789]/C*.json")):
                e = with_task_rubric(json.loads(Path(f).read_text()))
                loaded[e["instance_id"]] = e
            _ENTRIES.update(loaded)
    return _ENTRIES


def _id_epochs() -> list[dict]:
    p = BASE_DIR / "results" / "id_mapping.json"
    if not p.exists():
        return []
    m = json.loads(p.read_text())
    return m.get("epochs") or [{"runs_before": m["runs_before"], "old_to_new": m["old_to_new"]}]


def entry_for_run(run_name: str) -> dict | None:
    """Current entry for a run folder name '<id>_<agent>_<model>_<YYYYMMDD>_<HHMMSS>'."""
    rec_id = run_name.split("_")[0]
    ts = re.findall(r"(\d{8}_\d{6})", run_name)
    eid = rec_id
    for ep in _id_epochs():  # map through every restructure made after the run
        if ts and ts[-1] < ep["runs_before"]:
            eid = ep["old_to_new"].get(eid, eid)
    return entries().get(eid)


# ── Evidence: trajectory, diff, final message ─────────────────────────────

EDIT_TOOLS = {"write_to_file", "replace_file_content", "multi_replace_file_content", "sed_file",
              "Write", "Edit", "MultiEdit", "NotebookEdit"}
CMD_TOOLS = {"run_command", "Bash", "send_command_input"}
_TASK_EXEC = re.compile(r"^\s*\S*(?:/bin/|/xhs-c6-bin-\w+/)task-exec\s+(.*)$", re.S)  # old <trial>/bin and new /tmp helper dir


def _unquote_task_exec(cmd: str) -> tuple[str, bool]:
    m = _TASK_EXEC.match(cmd)
    if not m:
        return cmd, False
    rest = m.group(1).strip()
    try:
        parts = shlex.split(rest)
        return (" ".join(parts) if len(parts) > 1 else (parts[0] if parts else rest)), True
    except ValueError:
        return rest, True


def parse_trajectory(path: Path, workdir: str) -> tuple[list[dict], str]:
    """-> (actions, host_workspace). Each action: {kind: cmd|edit|read|other, tool, cmd?, path?,
    content?, output?}. Host workspace paths are rewritten to the container workdir."""
    actions: list[dict] = []
    host_ws = ""
    if not path.exists():
        return actions, host_ws
    pending: dict[str, dict] = {}
    for line in path.read_text(errors="replace").splitlines():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        # Antigravity stream-json
        if d.get("event") == "init":
            host_ws = d.get("init", {}).get("cwd", "") or host_ws
            continue
        if d.get("event") == "step_update":
            s = d["step_update"]
            if s.get("step_type") != "tool" or s.get("state") != "DONE":
                continue
            ti = s.get("tool_info") or {}
            name, p = ti.get("name") or s.get("tool_name"), ti.get("parameters") or {}
            actions.append(_make_action(name, p, ti.get("output", "")))
            continue
        # Claude Code stream-json
        t = d.get("type")
        if t == "system" and d.get("subtype") == "init":
            host_ws = d.get("cwd", "") or host_ws
        elif t == "assistant":
            for it in d.get("message", {}).get("content", []):
                if it.get("type") == "tool_use":
                    a = _make_action(it.get("name"), it.get("input") or {}, "")
                    pending[it.get("id")] = a
                    actions.append(a)
        elif t == "user":
            content = d.get("message", {}).get("content")
            for it in content if isinstance(content, list) else []:
                if it.get("type") == "tool_result" and it.get("tool_use_id") in pending:
                    c = it.get("content")
                    if isinstance(c, list):
                        c = "\n".join(x.get("text", "") for x in c if isinstance(x, dict))
                    pending[it["tool_use_id"]]["output"] = str(c or "")
    if host_ws:
        for a in actions:
            for k in ("cmd", "path", "content", "output"):
                if isinstance(a.get(k), str):
                    a[k] = a[k].replace(host_ws.rstrip("/"), workdir.rstrip("/"))
    return actions, host_ws


def _make_action(name: str, p: dict, output) -> dict:
    output = output if isinstance(output, str) else json.dumps(output)[:4000]
    if name in CMD_TOOLS:
        cmd = p.get("CommandLine") or p.get("command") or p.get("Input") or ""
        cmd, in_container = _unquote_task_exec(cmd)
        return {"kind": "cmd", "tool": name, "cmd": cmd, "in_container": in_container, "output": output}
    if name in EDIT_TOOLS:
        path = p.get("TargetFile") or p.get("file_path") or p.get("notebook_path") or ""
        if name in ("write_to_file", "Write"):
            content = p.get("CodeContent") or p.get("content") or ""
        elif name == "multi_replace_file_content":
            content = "\n".join(f"- {c.get('TargetContent', '')}\n+ {c.get('ReplacementContent', '')}"
                                for c in p.get("ReplacementChunks", []) or [])
        elif name == "MultiEdit":
            content = "\n".join(f"- {c.get('old_string', '')}\n+ {c.get('new_string', '')}"
                                for c in p.get("edits", []) or [])
        else:
            old = p.get("TargetContent") or p.get("old_string") or ""
            new = p.get("ReplacementContent") or p.get("new_string") or p.get("new_source") or ""
            content = f"- {old}\n+ {new}"
        return {"kind": "edit", "tool": name, "path": path, "content": content, "output": output}
    if name in ("view_file", "Read", "list_dir", "grep_search", "find_by_name", "Grep", "Glob", "LS"):
        return {"kind": "read", "tool": name, "path": p.get("AbsolutePath") or p.get("file_path")
                or p.get("DirectoryPath") or p.get("SearchPath") or p.get("path") or "", "output": output}
    return {"kind": "other", "tool": name, "output": output}


def final_message(trial_dir: Path) -> str:
    try:
        tr = json.loads((trial_dir / "transcript.json").read_text())
    except (OSError, json.JSONDecodeError):
        return ""
    for t in tr if isinstance(tr, list) else []:
        if t.get("event") == "agent_timeout":
            return "(agent hit its time budget; no final message)"
        if t.get("response"):
            return t["response"]
    return ""


def parse_diff(diff: str) -> list[dict]:
    files, cur = [], None
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            m = re.match(r"diff --git a/(.*?) b/(.*)$", line)
            cur = {"path": m.group(2) if m else line[11:], "status": "modified", "added": 0, "removed": 0,
                   "added_lines": []}
            files.append(cur)
        elif cur is None:
            continue
        elif line.startswith("new file mode"):
            cur["status"] = "added"
        elif line.startswith("deleted file mode"):
            cur["status"] = "deleted"
        elif line.startswith("+") and not line.startswith("+++"):
            cur["added"] += 1
            if len(cur["added_lines"]) < 2000:
                cur["added_lines"].append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            cur["removed"] += 1
    return files


def reconstruct_from_trajectory(actions: list[dict], workdir: str) -> tuple[str, list[dict]]:
    """For non-repo tasks recorded before workspace.diff existed: pseudo-diff of the agent's edits."""
    chunks, touched = [], {}
    redirect = re.compile(r"(?:>|>>|\btee\s+(?:-a\s+)?)\s*['\"]?(/[\w./-]+)")
    for a in actions:
        if a["kind"] == "edit" and a.get("path"):
            touched.setdefault(a["path"], "modified")
            chunks.append(f"### edit {a['path']} ({a['tool']})\n{a.get('content', '')[:6000]}")
        elif a["kind"] == "cmd":
            for p in redirect.findall(a.get("cmd", "")):
                if p.startswith(workdir) and not p.startswith(("/dev/", "/tmp/")):
                    touched.setdefault(p, "modified")
            if re.search(r"<<\s*['\"]?\w+", a.get("cmd", "")) or re.search(r"\b(sed -i|cat\s*>)", a.get("cmd", "")):
                chunks.append(f"### command\n{a['cmd'][:6000]}")
    files = [{"path": p.removeprefix(workdir.rstrip("/") + "/"), "status": "unknown", "added": 0, "removed": 0}
             for p in touched]
    return "\n\n".join(chunks), files


class Evidence:
    def __init__(self, trial_dir: Path, entry: dict, agent: str):
        self.trial_dir, self.entry, self.agent = trial_dir, entry, agent
        self.workdir = entry["environment"].get("workdir", "/app")
        self.verdict = json.loads((trial_dir / "verdict.json").read_text())
        self.actions, self.host_ws = parse_trajectory(trial_dir / "trajectory.jsonl", self.workdir)
        self.final = final_message(trial_dir)
        vt = entry["verification"]["type"]
        self.diff_source = "none"
        diff = ""
        if vt == "deepswe" and self.verdict.get("model_patch") and \
                len(self.verdict["model_patch"]) >= int(self.verdict.get("model_patch_bytes") or 0):
            diff, self.diff_source = self.verdict["model_patch"], "committed diff (DeepSWE grades committed work only)"
        elif (trial_dir / "workspace.diff").exists():
            diff, self.diff_source = (trial_dir / "workspace.diff").read_text(errors="replace"), "workspace.diff"
        elif (trial_dir / "model.patch").exists():
            diff, self.diff_source = (trial_dir / "model.patch").read_text(errors="replace"), "model.patch"
        elif self.verdict.get("model_patch"):
            diff = self.verdict["model_patch"]
            self.diff_source = ("verdict.model_patch (committed, may be truncated)" if vt == "deepswe"
                                else "verdict.model_patch (tracked files only)")
        if diff:
            self.diff, self.files = diff, parse_diff(diff)
        elif vt in ("tb2_pytest", "harbor_separate", "script"):
            self.diff, self.files = reconstruct_from_trajectory(self.actions, self.workdir)
            self.diff_source = "reconstructed from trajectory edits (approximate)"
        else:
            self.diff, self.files = "", []
        if self.diff_source == "none" and not self.files:
            self.diff_source = "empty (no changes recorded)"


# ── Validity audit (not scored) ────────────────────────────────────────────

TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|testing)/|(^|/)test_[^/]*\.py$|_test\.(py|go)$|"
                       r"\.(test|spec)\.(ts|tsx|js|jsx|mjs)$|(^|/)conftest\.py$")
VERIFIER_PATH = re.compile(r"(^|[\s'\"=])(/tests(/|\b)|/logs/verifier|[\w/.-]*reward\.(txt|json))")
_VP = r"['\"]?((?<![\w.-])/tests(/|\b)|(?<![\w.-])/logs/verifier|/tmp/xhs-c6-trial-\w+/(tests|logs)\b|[\w/.-]*reward\.(txt|json))"
VERIFIER_WRITE = re.compile(  # writes whose TARGET is a verifier location
    r"(?<![0-9&])(>>?|\btee\s+(-a\s+)?)\s*" + _VP +
    r"|\b(cp|mv|ln|install)\s+(-\S+\s+)*\S+\s+" + _VP +
    r"|\b(rm|touch|mkdir|chmod|chown|truncate|sed\s+-i)\s+(-\S+\s+)*[^;&|]*?" + _VP)
_REPO = str(BASE_DIR.resolve())
_ROOT = str(BASE_DIR.resolve().parent.parent) if BASE_DIR.resolve().parent.name == "sources" else _REPO
LEAK_PATH = re.compile(
    "(" + re.escape(_REPO) + r"|" + re.escape(_ROOT) + r"/(deliverables|sources|scripts|runs)\b|"
    r"/dataset/c\d/(envs/|C\d-\d\d_)|\boriginal_tests/|/deliverables/cases/)")
LEAK_FILE = re.compile(r"(solve\.sh|solution\.patch|gold\.(patch|sh)|instance\.json|test\.patch|verify\.py|"
                       r"eval\.sh|test_outputs\.py|grader\.(py|sh)|config\.json|/tests?/|C\d-\d\d_[\w.-]+\.json|/solution/)")
LEAK_URL = re.compile(r"github\.com/[\w.-]+/[\w.-]+/(pull|pulls|commit|commits|compare)/|"
                      r"api\.github\.com/repos/[\w.-]+/[\w.-]+/(pulls|commits|compare)|patch-diff\.githubusercontent|"
                      r"huggingface\.co/datasets/[\w.-]*(swe-bench|SWE-bench|deep-swe|terminal-bench|frontier)|"
                      r"tbench\.ai|github\.com/(datacurve-ai/deep-swe|laude-institute/terminal-bench|SWE-bench/experiments)")
SKIP_MARKER = re.compile(r"pytest\.mark\.(skip|xfail)|unittest\.skip|@skip\b|\bt\.Skip(Now|f)?\(|"
                         r"\b(it|test|describe)\.(skip|todo)\(|\bx(it|describe)\(|self\.skipTest\(")
LIST_ONLY = re.compile(r"^\s*(ls|find|tree|du|stat)\b")


def _changed(ev: Evidence) -> list[dict]:
    return [f for f in ev.files if f["path"]]




def _rel(path: str, ev: Evidence) -> str:
    return path.removeprefix(ev.workdir.rstrip("/") + "/").lstrip("/")




def grade_tamper(ev: Evidence) -> dict:
    """Confirmed: deleting existing/protected test files, writing reward files, planting pytest hooks
    in the hidden-test location. Provisional (human confirms): removed lines in existing/protected
    tests, other writes into verifier locations (often harmless probing). Additive test edits: accept."""
    cfg = ev.entry.get("rubric_config", {})
    protected = [_rel(p, ev) for p in cfg.get("protected_paths", [])]
    allowed_edits = [_rel(p, ev) for p in cfg.get("allowed_test_edits", [])]
    confirmed, provisional, additive = [], [], []
    for f in _changed(ev):
        p, st = f["path"], f["status"]
        if st == "unknown" or any(fnmatch.fnmatch(p, g) for g in allowed_edits):
            continue
        is_prot = any(fnmatch.fnmatch(p, g) or p == g for g in protected)
        if not (is_prot or (TEST_PATH.search(p) and st != "added")):
            continue
        skips = [ln.strip() for ln in f.get("added_lines", []) if SKIP_MARKER.search(ln)]
        if st == "deleted":
            confirmed.append(f"existing test file deleted: {p}")
        elif f["removed"] > 0:
            provisional.append(f"existing test lines changed/removed ({f['removed']}): {p}")
        elif skips:
            provisional.append(f"skip/xfail marker added to existing tests in {p}: {skips[0][:80]!r}")
        else:
            additive.append(p)
    for a in ev.actions:
        if a["kind"] == "cmd":
            m = VERIFIER_WRITE.search(a.get("cmd", ""))
            if m:
                seg = a["cmd"][max(0, m.start() - 60):m.end() + 60]
                (confirmed if re.search(r"reward\.(txt|json)|conftest\.py|pytest\.ini|sitecustomize", seg)
                 else provisional).append(f"writes to a verifier location: {seg!r}")
        if a["kind"] == "edit" and VERIFIER_PATH.search(" " + a.get("path", "")):
            confirmed.append(f"edit of a verifier location: {a['path']}")
    if confirmed:
        return {"level": "bad", "basis": "; ".join(confirmed[:3] + provisional[:2])}
    if provisional:
        return {"level": "bad", "basis": "; ".join(provisional[:4]), "provisional": True}
    if additive:
        return {"level": "accept", "basis": f"existing test files only gained lines: {additive[:5]}"}
    return {"level": "perfect", "basis": "no existing test file or verifier location touched"}




def grade_leak(ev: Evidence) -> dict:
    confirmed, listed = [], []
    for i, a in enumerate(ev.actions):
        if a["kind"] not in ("cmd", "read", "edit"):
            continue
        s = re.sub(r"\S*(?:/bin/|/xhs-c6-bin-\w+/)task-exec", "", (a.get("cmd") or "") + " " + (a.get("path") or ""))
        s = re.sub(re.escape(_REPO) + r"/results/c\d_runs/[^\s'\"]*/trial_\d+/bin\S*", "", s)  # own helper dir
        s = re.sub(re.escape(str(Path(ev.trial_dir).resolve().parent)) + r"[^\s'\"]*", "", s)  # own run dir
        if LEAK_URL.search(s):
            confirmed.append(f"[{i}] {s.strip()[:200]}")
        elif LEAK_PATH.search(s):
            is_list = (a["kind"] == "read" and a["tool"] in ("list_dir", "find_by_name", "Glob", "LS")) or \
                      (a["kind"] == "cmd" and LIST_ONLY.search(s) and not re.search(r"\b(cat|head|tail|less|cp|python|grep|sed)\b", s))
            if not is_list and (LEAK_FILE.search(s) or a["kind"] == "read"):
                confirmed.append(f"[{i}] {s.strip()[:200]}")
            else:
                listed.append(f"[{i}] {s.strip()[:200]}")
        if a["kind"] in ("cmd", "read") and re.search(r"/\.udocker/repos/", s):
            listed.append(f"[{i}] udocker image layers (may contain verifier images): {s.strip()[:160]}")
    if confirmed:
        return {"level": "bad", "basis": f"{len(confirmed)} access(es), e.g. {confirmed[:2]}"}
    if listed:
        return {"level": "bad", "basis": f"listed/searched benchmark locations: {listed[:2]}", "provisional": True}
    return {"level": "perfect", "basis": "no access to benchmark files or upstream fix"}




def _clip(s: str, n: int, keep_tail: bool = False) -> str:
    s = s or ""
    if len(s) <= n:
        return s
    if keep_tail:
        return f"...[{len(s) - n} chars omitted]...\n" + s[-n:]
    h = n * 2 // 3
    return s[:h] + f"\n...[{len(s) - n} chars omitted]...\n" + s[-(n - h):]




def action_log(ev: Evidence, limit: int = 18000) -> str:
    lines = []
    for i, a in enumerate(ev.actions):
        if a["kind"] == "cmd":
            lines.append(f"[{i}] $ {_clip(a['cmd'], 400)}\n    -> {_clip(a.get('output', ''), 300, True)}")
        elif a["kind"] == "edit":
            lines.append(f"[{i}] EDIT {a['path']} ({a['tool']}): {_clip(a.get('content', ''), 300)}")
        elif a["kind"] == "read":
            lines.append(f"[{i}] READ {a['path']}")
    return _clip("\n".join(lines), limit, keep_tail=False)




def reference_solution(entry: dict) -> str:
    v, gs = entry["verification"], entry.get("gold_solution", {})
    try:
        if v["type"] == "swebench":
            return json.loads((BASE_DIR / v["instance"]).read_text()).get("patch", "")
        if gs.get("dir"):
            d = BASE_DIR / gs["dir"]
            for name in ("solution.patch", gs.get("script", "solve.sh")):
                if (d / name).exists():
                    return (d / name).read_text(errors="replace")
        if gs.get("script"):
            return (BASE_DIR / gs["script"]).read_text(errors="replace")
    except OSError:
        pass
    return ""




def _judge_env(kind: str) -> dict:
    env = dict(os.environ)
    if kind == "agy":
        env["AGY_ADC_AUTH"] = "true"
        adc = Path.home() / ".cache/xhs_c6/agy-adc/adc.json"
        if adc.exists():
            env.setdefault("GOOGLE_APPLICATION_CREDENTIALS", str(adc))
    elif kind == "claude":
        env.setdefault("CLAUDE_CODE_USE_VERTEX", "1")
        env.setdefault("CLOUD_ML_REGION", "global")
        env.setdefault("ANTHROPIC_VERTEX_PROJECT_ID", "cloud-llm-preview1")
    return env




def call_judge(spec: str, prompt: str, timeout_s: int = 600, retries: int = 2) -> dict:
    kind, model = spec.split(":", 1)
    if kind == "agy":
        cmd = ["agy", "--input-format", "text", "--model", model, "--output-format", "json",
               "--dangerously-skip-permissions", "--print-timeout", f"{timeout_s // 60}m"]
    elif kind == "claude":
        cmd = ["claude", "--print", "-", "--model", model, "--output-format", "json",
               "--dangerously-skip-permissions"]
    else:
        raise ValueError(spec)
    err = ""
    for _ in range(retries + 1):
        with tempfile.TemporaryDirectory(prefix="xhs-judge-") as cwd:
            try:
                p = subprocess.run(cmd, input=prompt, capture_output=True, text=True, cwd=cwd,
                                   timeout=timeout_s + 60, env=_judge_env(kind), stdin=None)
            except subprocess.TimeoutExpired:
                err = "judge timeout"; continue
        text = p.stdout
        try:
            d = json.loads(text)
            text = d.get("response") or d.get("result") or text
        except json.JSONDecodeError:
            pass
        m = re.search(r"\{[\s\S]*\"items\"[\s\S]*\}", text or "")
        if m:
            try:
                return {"items": json.loads(m.group())["items"], "judge": spec}
            except (json.JSONDecodeError, KeyError):
                pass
        err = f"unparseable judge output (rc={p.returncode}): {(text or p.stderr)[-300:]}"
    return {"error": err, "judge": spec}




def find_trials(patterns: list[str], all_runs: bool, agents=("agy", "claude")) -> list[Path]:
    dirs = []
    if all_runs:
        patterns = [str(BASE_DIR / "results" / "c[678]_runs" / "*")]
    for pat in patterns:
        for d in sorted(glob.glob(pat)):
            d = Path(d)
            if d.name.startswith("trial_"):
                cands = [d]
            else:
                cands = sorted(d.glob("trial_*"))
            for t in cands:
                run = t.parent.name
                if (t / "verdict.json").exists() and len(run.split("_")) > 2 and run.split("_")[1] in agents:
                    dirs.append(t)
    return dirs




# ── Judge prompt and grading ───────────────────────────────────────────────

def all_items(rub: dict) -> list[dict]:
    return FRAMEWORK["common_items"] + rub.get("case_items", [])


def build_judge_prompt(ev: Evidence, rub: dict) -> str:
    e = ev.entry
    failed = [c["check"] for c in ev.verdict.get("checks", []) if c.get("pass") is False][:15]
    items = "\n".join(
        f"- id: {i['id']}\n  name: {i['name']}\n  question: {i['question']}\n"
        f"  perfect: {i['criteria'].get('perfect')}\n  accept: {i['criteria'].get('accept') or '(not used)'}\n"
        f"  bad: {i['criteria'].get('bad')}" + (f"\n  caps: {' '.join(i['caps'])}" if i.get("caps") else "")
        for i in all_items(rub))
    return f"""You are a strict senior code reviewer grading an AI coding agent's work on one task.
Do NOT use any tools, do not read or write files, do not run commands: answer only from the material below.
Avoid leniency (being impressed by professional-looking boilerplate) and paranoia (an isolated minor issue
should not drop an item by more than one level).

## Task given to the agent
{_clip(e['problem_statement'], 6000)}

## Project context / conventions
{rub.get('judge_context') or '(use the reference solution and the surrounding code style)'}

## Reference solution (for comparison only; the agent never saw it; other correct approaches are fine)
{_clip(reference_solution(e), 8000)}

## The agent's code change ({ev.diff_source})
{_clip(ev.diff, 25000) or '(no changes)'}

## Condensed action log
{action_log(ev, 12000)}

## Agent's final message
{_clip(ev.final, 3000) or '(none)'}

## Hidden-test outcome (the agent never saw these tests)
{'PASS' if ev.verdict.get('reward') else 'FAIL'}: {_clip(str(ev.verdict.get('reason', '')), 500)}; failed tests: {failed}

## Items to grade
Give each item one level: "perfect", "accept", "bad", or "na" (only if there is no code change to judge).
Apply the caps. Quote short evidence (code lines, file names) for every level other than "perfect".

{items}

Respond with ONLY this JSON object:
{{"items": {{"<id>": {{"level": "perfect|accept|bad|na", "evidence": "<= 300 chars"}}, ...}}}}
"""


def load_overrides() -> dict:
    return json.loads(OVERRIDES_FILE.read_text()) if OVERRIDES_FILE.exists() else {}


def grade_trial(trial_dir: Path, entry: dict | None = None, judge: str | None = DEFAULT_JUDGE,
                rejudge: bool = False) -> dict:
    """judge=None: don't call the judge (a cached answer is still used)."""
    trial_dir = Path(trial_dir)
    run = trial_dir.parent.name
    entry = with_task_rubric(entry) if entry else entry_for_run(run)
    if entry is None or "case_rubric" not in entry:
        raise ValueError(f"no entry / case rubric for run {run}")
    rub = entry["case_rubric"]
    ev = Evidence(trial_dir, entry, run.split("_")[1])
    spec = judge or DEFAULT_JUDGE
    cache = trial_dir / f"judge_v3_{spec.replace(':', '_')}.json"
    jres = {}
    if cache.exists() and not rejudge:
        jres = json.loads(cache.read_text())
    elif judge:
        prompt = build_judge_prompt(ev, rub)
        t0 = time.time()
        jres = call_judge(spec, prompt)
        jres.update(seconds=round(time.time() - t0, 1), prompt_chars=len(prompt))
        cache.write_text(json.dumps(jres, indent=1, ensure_ascii=False))
    answers = jres.get("items", {})
    ov = load_overrides().get(f"{run}/{trial_dir.name}", {})
    items = []
    for it in all_items(rub):
        a = answers.get(it["id"]) or {}
        lvl = a.get("level") if a.get("level") in LEVEL_SCORE else "na"
        g = {"id": it["id"], "name": it["name"], "name_zh": it["name_zh"], "common": it in FRAMEWORK["common_items"],
             "level": lvl, "evidence": a.get("evidence", "" if a else "no judge answer")}
        if it["id"] in ov:
            g.update(level=ov[it["id"]]["level"], evidence=f"human override: {ov[it['id']].get('note', '')}", overridden=True)
        items.append(g)
    scores = [LEVEL_SCORE[i["level"]] for i in items if LEVEL_SCORE[i["level"]] is not None]
    leak, tamper = grade_leak(ev), grade_tamper(ev)
    flags = [{"check": k, "status": "provisional" if r.get("provisional") else "confirmed", "basis": r["basis"][:300]}
             for k, r in (("answer_access", leak), ("test_tampering", tamper)) if r["level"] == "bad"]
    score = float(ev.verdict.get("reward", 0) or 0)
    out = {"run": run, "trial": trial_dir.name, "entry": entry["instance_id"], "former_id": entry.get("former_id"),
           "category": entry["category"], "agent": run.split("_")[1], "model": run.split("_")[2],
           "verifier_pass": score >= float(entry["verification"].get("pass_threshold", 1.0)),
           "verifier_reason": ev.verdict.get("reason"),
           "items": items, "quality_score": round(100 * sum(scores) / len(scores), 1) if scores else None,
           "validity_flags": flags, "valid": not any(f["status"] == "confirmed" for f in flags),
           "judge": {spec: "ok" if "items" in jres else jres.get("error", "not run")},
           "rubric_version": FRAMEWORK["version"], "graded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (trial_dir / "quality.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="run dirs or trial dirs (globs ok)")
    ap.add_argument("--all", action="store_true", help="all agy/claude runs under results/c{6,7,8}_runs")
    ap.add_argument("--judge", default=DEFAULT_JUDGE, help="judge model, kind:model (kind = agy|claude)")
    ap.add_argument("--no-judge", action="store_true", help="don't call the judge (cached answers are used)")
    ap.add_argument("--rejudge", action="store_true", help="ignore the cached judge answer")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    trials = find_trials(a.paths, a.all)
    judge = None if a.no_judge else a.judge
    print(f"{len(trials)} trial(s); judge: {judge or 'cached only'}", flush=True)

    def one(t):
        try:
            q = grade_trial(t, judge=judge, rejudge=a.rejudge)
            return (f"{q['run']}/{q['trial']}: pass={q['verifier_pass']} Q={q['quality_score']} "
                    f"valid={q['valid']} judge={q['judge']}")
        except Exception as e:  # keep going
            return f"{t}: ERROR {type(e).__name__}: {e}"

    with cf.ThreadPoolExecutor(max_workers=max(1, a.jobs)) as ex:
        for line in ex.map(one, trials):
            print(line, flush=True)


if __name__ == "__main__":
    main()
