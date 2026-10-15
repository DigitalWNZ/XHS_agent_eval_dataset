#!/usr/bin/env python3
"""XHS cloud worker: runs ONE task (one trial of one entry x model) inside a GCP Batch task.

Started by the Batch runnable on a worker VM built from the `xhs-worker` image (tools/cloud/bake.sh).
Environment (set by the controller, tools/cloud/xhs_cloud.py):
  XHS_BUCKET        GCS bucket (no gs://)
  XHS_RUN_ID        run id; everything lives under gs://$XHS_BUCKET/runs/$XHS_RUN_ID/
  XHS_TASKS_FILE    task list object under the run prefix (default tasks.json); one per Batch job
  BATCH_TASK_INDEX  set by Batch; index into that task list
  XHS_AGY_SECRET    optional Secret Manager secret (projects/.../secrets/NAME) holding the agy ADC JSON
  XHS_VERTEX_PROJECT  project for Claude on Vertex (default: the VM's project)

Flow: download code.tgz + tasks.json -> run evaluation/run_benchmark.py --sandbox docker --trials 1 with a
unique XHS_RUN_TS -> upload the run folder, summary JSON and log to runs/<id>/results/ -> write
runs/<id>/status/t<index>.json. Exit 0 whenever the trial produced a verdict (agent failures are results,
not infrastructure failures); exit 75 (retryable) when the harness itself failed before producing one.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tarfile
import time
import traceback
import urllib.request
from pathlib import Path

BUCKET = os.environ["XHS_BUCKET"]
RUN = os.environ["XHS_RUN_ID"]
IDX = int(os.environ.get("BATCH_TASK_INDEX", "0"))
TASKS_FILE = os.environ.get("XHS_TASKS_FILE", "tasks.json")
PREFIX = f"gs://{BUCKET}/runs/{RUN}"
WORK = Path(f"/work/{RUN}/{TASKS_FILE.removesuffix('.json')}-t{IDX:04d}")
HOST = os.uname().nodename.split(".")[0]
TASK_KEY = f"{TASKS_FILE.removesuffix('.json')}-t{IDX:04d}"
T0 = time.time()


def sh(argv, **kw):
    return subprocess.run(argv, check=False, **kw)


def gcs_cp(src: str, dst: str, recursive: bool = False) -> int:
    argv = ["gcloud", "storage", "cp", "-q"] + (["-r"] if recursive else []) + [src, dst]
    for attempt in range(4):
        r = sh(argv, capture_output=True, text=True)
        if r.returncode == 0:
            return 0
        time.sleep(3 * (attempt + 1))
    print(f"gcs cp failed: {src} -> {dst}: {r.stderr[-500:]}", flush=True)
    return r.returncode


def status(state: str, **extra) -> None:
    doc = {"task": IDX, "key": TASK_KEY, "state": state, "host": HOST, "time": time.time(),
           "elapsed_s": round(time.time() - T0), "attempt": int(os.environ.get("BATCH_TASK_RETRY_ATTEMPT", 0)),
           **extra}
    p = WORK / "status.json"
    p.write_text(json.dumps(doc))
    gcs_cp(str(p), f"{PREFIX}/status/{TASK_KEY}.json")


def metadata(path: str) -> str:
    req = urllib.request.Request(f"http://metadata.google.internal/computeMetadata/v1/{path}",
                                 headers={"Metadata-Flavor": "Google"})
    return urllib.request.urlopen(req, timeout=10).read().decode()


def setup_agy_credentials(env: dict) -> None:
    """agy authenticates with ADC (AGY_ADC_AUTH=true). If XHS_AGY_SECRET is set, the ADC file comes from
    Secret Manager (readable only by the runner SA) and lives on the VM's local disk only."""
    secret = os.environ.get("XHS_AGY_SECRET")
    env["AGY_ADC_AUTH"] = "true"
    if not secret:
        return
    out = WORK / "secrets" / "agy-adc.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(out.parent, 0o700)
    r = sh(["gcloud", "secrets", "versions", "access", "latest", f"--secret={secret}"],
           capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"cannot read agy secret: {r.stderr[-300:]}")
    out.write_text(r.stdout)
    os.chmod(out, 0o600)
    env["GOOGLE_APPLICATION_CREDENTIALS"] = str(out)


def main() -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    status("starting")
    if gcs_cp(f"{PREFIX}/{TASKS_FILE}", str(WORK / "tasks.json")) or gcs_cp(f"{PREFIX}/code.tgz", str(WORK / "code.tgz")):
        status("infra_error", error="download failed")
        return 75
    task = json.loads((WORK / "tasks.json").read_text())["tasks"][IDX]
    repo = WORK / "xhs"
    with tarfile.open(WORK / "code.tgz") as tf:
        tf.extractall(repo)
    env = dict(os.environ)
    project = metadata("project/project-id")
    env.update({
        "XHS_RUN_TS": task["run_ts"],
        "XHS_VERIFY_SLOTS": os.environ.get("XHS_VERIFY_SLOTS", "2"),
        "CLAUDE_CODE_USE_VERTEX": "1", "CLOUD_ML_REGION": "global",
        "ANTHROPIC_VERTEX_PROJECT_ID": os.environ.get("XHS_VERTEX_PROJECT", project),
        "IS_SANDBOX": "1",  # lets Claude Code use --dangerously-skip-permissions as root on a throwaway VM
        "PYTHONUNBUFFERED": "1",
        "XHS_C6_CACHE": os.environ.get("XHS_C6_CACHE", "/opt/xhs-cache"),
        "XHS_AGENT_MASK": "/work",  # other tasks' repo copies on this VM are hidden from the agent
    })
    if task["agent"] == "agy":
        setup_agy_credentials(env)
    status("running", **{k: task[k] for k in ("category", "entry", "agent", "model", "trial")})
    log = WORK / "run.log"
    argv = [sys.executable, "-u", "evaluation/run_benchmark.py", "--category", task["category"],
            "--entry", task["entry"], "--agent", task["agent"], "--model", task["model"],
            "--sandbox", "docker", "--trials", "1", "--timeout", str(task["timeout_min"]),
            "--quality", task.get("quality", "full")]
    with open(log, "w") as f:
        rc = sh(argv, cwd=repo, env=env, stdout=f, stderr=subprocess.STDOUT).returncode
    # Collect: the run folder(s) written by this task (unique XHS_RUN_TS) and the summary JSON.
    res = repo / "results"
    run_dirs = sorted(res.glob(f"c*_runs/*_{task['run_ts']}"))
    summaries = sorted(res.glob(f"c*_*_{task['run_ts']}.json"))
    verdict = {}
    for d in run_dirs:
        vf = d / "trial_0" / "verdict.json"
        qf = d / "trial_0" / "quality.json"
        if vf.is_file():
            v = json.loads(vf.read_text())
            verdict = {"reward": v.get("reward"), "reason": str(v.get("reason", ""))[:200]}
        if qf.is_file():
            verdict["quality"] = json.loads(qf.read_text()).get("quality_score")
        gcs_cp(str(d), f"{PREFIX}/results/{d.parent.name}/", recursive=True)
    for s in summaries:
        gcs_cp(str(s), f"{PREFIX}/results/{s.name}")
    gcs_cp(str(log), f"{PREFIX}/logs/{TASK_KEY}_{task['entry']}_{task['model']}_trial{task['trial']}.log")
    if not verdict:
        status("infra_error", rc=rc, error=log.read_text(errors="replace")[-800:])
        return 75
    status("done", rc=rc, **verdict, **{k: task[k] for k in ("category", "entry", "agent", "model", "trial")})
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception:  # pylint: disable=broad-except
        WORK.mkdir(parents=True, exist_ok=True)
        status("infra_error", error=traceback.format_exc()[-800:])
        code = 75
    sys.exit(code)
