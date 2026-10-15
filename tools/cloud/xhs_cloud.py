#!/usr/bin/env python3
"""xhs_cloud: run the XHS benchmark on elastic GCP capacity (GCP Batch + Docker workers).

  bake     build the worker VM image (family xhs-worker): Docker, bwrap, uv, Claude Code, agy, SWE-bench
           grader venv and every task image pre-pulled.
  run      expand cases x models x trials into one task per trial, submit Batch jobs, watch status,
           collect results into results/ and tear everything down (also on Ctrl-C / error).
  status   print the status of a run (from any shell).
  collect  download a run's results into results/ (also done by `run`).
  down     delete a run's Batch jobs, leftover VMs and GCS prefix.
  gc       delete every finished/failed xhs-runner job and orphaned worker VM in the project.

Auth: the caller's ADC (`gcloud auth application-default print-access-token`; set CLOUDSDK_CONFIG to pick a
config). Workers use the `xhs-runner` service account: agy (AGY_ADC_AUTH=true) and Claude Code both call
Vertex AI in the worker project, so no user credential leaves this machine.

Examples:
  python3 tools/cloud/xhs_cloud.py bake
  python3 tools/cloud/xhs_cloud.py run --cases c9:C9-01 c6:C6-05 --agent agy \\
      --models gemini-3.8-flash-high,gemini-4-argon-high --trials 3
  python3 tools/cloud/xhs_cloud.py run --cases all --agent claude --models claude-opus-5-5 --trials 3 --detach
  python3 tools/cloud/xhs_cloud.py status <run-id>
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import math
import os
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
XHS = HERE.parent.parent
PROJECT = os.environ.get("XHS_CLOUD_PROJECT", "gcr-evaluation-hub")
REGION = os.environ.get("XHS_CLOUD_REGION", "us-central1")
ZONE = os.environ.get("XHS_CLOUD_ZONE", f"{REGION}-a")
BUCKET = os.environ.get("XHS_CLOUD_BUCKET", "gcr-evaluation-hub-xhs-runs")
SA = os.environ.get("XHS_CLOUD_SA", f"xhs-runner@{PROJECT}.iam.gserviceaccount.com")
IMAGE_FAMILY = "xhs-worker"
LABELS = {"owner": os.environ.get("USER", "unknown").lower()[:60], "purpose": "xhs-runner"}
STATE_DIR = Path(os.environ.get("RUNS_DIR", XHS / "runs")) / "cloud"
# On-demand / Spot USD per hour (us-central1, approx.) for the cost estimate shown in status.
PRICE = {"e2-standard-8": (0.27, 0.08), "n2d-standard-8": (0.34, 0.09), "n2-standard-8": (0.39, 0.12), "n2-standard-16": (0.78, 0.25), "n2-standard-32": (1.55, 0.50),
         "n2d-standard-16": (0.68, 0.17), "e2-standard-16": (0.54, 0.16)}
DISK_PRICE_GB_H = 0.10 / 730


# ── GCP plumbing (REST + gcloud storage) ─────────────────────────────────

_TOKEN = {"v": None, "t": 0.0}


def token() -> str:
    if not _TOKEN["v"] or time.time() - _TOKEN["t"] > 1200:
        _TOKEN["v"] = subprocess.run(["gcloud", "auth", "application-default", "print-access-token"],
                                     capture_output=True, text=True, check=True).stdout.strip()
        _TOKEN["t"] = time.time()
    return _TOKEN["v"]


def api(method: str, url: str, body: dict | None = None, ok404: bool = False):
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {token()}", "Content-Type": "application/json",
                                          "x-goog-user-project": PROJECT})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
                return json.loads(data) if data else {}
        except urllib.error.HTTPError as e:
            if e.code == 404 and ok404:
                return None
            if e.code in (429, 500, 502, 503) and attempt < 4:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"{method} {url}: {e.code} {e.read().decode()[:600]}") from None
        except urllib.error.URLError:
            if attempt < 4:
                time.sleep(2 ** attempt)
                continue
            raise


def gcloud_env() -> dict:
    return {**os.environ, "CLOUDSDK_AUTH_ACCESS_TOKEN": token(), "CLOUDSDK_CORE_PROJECT": PROJECT,
            "CLOUDSDK_CORE_DISABLE_PROMPTS": "1",
            "CLOUDSDK_METRICS_ENVIRONMENT": (os.environ.get("CLOUDSDK_METRICS_ENVIRONMENT", "") + " xhs-cloud").strip()}


def gsutil(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run(["gcloud", "storage", *args], env=gcloud_env(), capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError(f"gcloud storage {' '.join(args)}: {r.stderr[-600:]}")
    return r


def gcs_list(prefix: str) -> list[dict]:
    items, page = [], None
    while True:
        q = {"prefix": prefix, "fields": "items(name,updated,size,generation),nextPageToken"}
        if page:
            q["pageToken"] = page
        r = api("GET", f"https://storage.googleapis.com/storage/v1/b/{BUCKET}/o?" + urllib.parse.urlencode(q))
        items += r.get("items", [])
        page = r.get("nextPageToken")
        if not page:
            return items


def gcs_read(name: str) -> bytes | None:
    url = f"https://storage.googleapis.com/storage/v1/b/{BUCKET}/o/{urllib.parse.quote(name, safe='')}?alt=media"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token()}"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code not in (429, 500, 502, 503) or attempt == 4:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == 4:
                raise
        time.sleep(2 ** attempt)
    return None


def gcs_download(prefix: str, dest: Path) -> tuple[int, list[str]]:
    """Download every object under `prefix` into dest/<relative path> (JSON API, 16 threads).
    Returns (files downloaded, failed object names)."""
    import concurrent.futures as cf  # pylint: disable=g-import-not-at-top
    items = [i for i in gcs_list(prefix) if not i["name"].endswith("/")]

    def one(it):
        rel = it["name"][len(prefix):].lstrip("/")
        data = gcs_read(it["name"])
        if data is None:
            return it["name"]
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        return None
    failed = []
    with cf.ThreadPoolExecutor(16) as ex:
        for r in ex.map(one, items):
            if r:
                failed.append(r)
    return len(items) - len(failed), failed


def gcs_write(name: str, data: bytes, ctype: str = "application/json") -> None:
    url = (f"https://storage.googleapis.com/upload/storage/v1/b/{BUCKET}/o?uploadType=media&name="
           + urllib.parse.quote(name, safe=""))
    req = urllib.request.Request(url, method="POST", data=data,
                                 headers={"Authorization": f"Bearer {token()}", "Content-Type": ctype})
    urllib.request.urlopen(req, timeout=300).read()


COMPUTE = f"https://compute.googleapis.com/compute/v1/projects/{PROJECT}"
BATCH = f"https://batch.googleapis.com/v1/projects/{PROJECT}/locations/{REGION}"


def wait_zone_op(op: dict, zone: str = ZONE) -> None:
    while op.get("status") != "DONE":
        time.sleep(3)
        op = api("GET", f"{COMPUTE}/zones/{zone}/operations/{op['name']}")
    if op.get("error"):
        raise RuntimeError(json.dumps(op["error"])[:600])


def wait_global_op(op: dict) -> None:
    while op.get("status") != "DONE":
        time.sleep(5)
        op = api("GET", f"{COMPUTE}/global/operations/{op['name']}")
    if op.get("error"):
        raise RuntimeError(json.dumps(op["error"])[:600])


def instances_with_label(key: str, value: str) -> list[dict]:
    flt = urllib.parse.quote(f"labels.{key}={value}")
    r = api("GET", f"{COMPUTE}/aggregated/instances?filter={flt}")
    return [i for z in r.get("items", {}).values() for i in z.get("instances", [])]


# ── Dataset helpers ──────────────────────────────────────────────────────

def entries() -> dict[str, dict]:
    out = {}
    for f in sorted(glob.glob(str(XHS / "dataset" / "c[6789]" / "*.json"))):
        e = json.load(open(f))
        out[e["instance_id"]] = e
    return out


def task_images() -> list[str]:
    imgs = []
    for e in entries().values():
        env, v = e.get("environment", {}), e.get("verification", {})
        for img in (env.get("docker_image") or env.get("prebuilt_image"), v.get("docker_verifier_image") or v.get("verifier_image")):
            if img and img not in imgs:
                imgs.append(img)
    return imgs


def budget(e: dict) -> tuple[int, int]:
    """(agent minutes, task maxRunDuration seconds) for one trial of entry e."""
    env, v = e.get("environment", {}), e.get("verification", {})
    agent_s = int(env.get("agent_timeout_sec") or e.get("timeout_sec") or 3600)
    verify_s = int(v.get("timeout_sec") or 1800)
    # agent + verifier + LLM judge (~10 min) + setup/upload margin (15 min)
    return math.ceil(agent_s / 60), agent_s + verify_s + 25 * 60


# ── bake ─────────────────────────────────────────────────────────────────

def cmd_bake(a) -> int:
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    bake_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    name = f"xhs-bake-{bake_id}"
    if not gcs_list("tools/agy"):
        print("uploading agy binary ...")
        gsutil("cp", str(Path(subprocess.run(["which", "agy"], capture_output=True, text=True).stdout.strip())),
               f"gs://{BUCKET}/tools/agy")
    imgs = task_images()
    print(f"bake {name}: {len(imgs)} task images, disk {a.disk_gb} GB")
    body = {
        "name": name, "machineType": "",
        "labels": {**LABELS, "xhs-role": "bake"},
        "disks": [{"boot": True, "autoDelete": True, "initializeParams": {
            "sourceImage": "projects/ubuntu-os-cloud/global/images/family/ubuntu-2404-lts-amd64",
            "diskSizeGb": str(a.disk_gb), "diskType": "pd-ssd"}}],
        "networkInterfaces": [{"network": "global/networks/default",
                               "accessConfigs": [{"type": "ONE_TO_ONE_NAT", "name": "External NAT"}]}],
        "serviceAccounts": [{"email": SA, "scopes": ["https://www.googleapis.com/auth/cloud-platform"]}],
        "metadata": {"items": [{"key": "startup-script", "value": (HERE / "bake.sh").read_text()},
                               {"key": "xhs-bucket", "value": BUCKET}, {"key": "xhs-bake-id", "value": bake_id},
                               {"key": "xhs-images", "value": "\n".join(imgs)}]},
        "scheduling": {"maxRunDuration": {"seconds": 3 * 3600}, "instanceTerminationAction": "STOP"},
    }
    zone = None
    for z in [ZONE] + [f"{REGION}-{s}" for s in "abcf" if f"{REGION}-{s}" != ZONE]:
        body["machineType"] = f"zones/{z}/machineTypes/{a.machine_type}"
        body["disks"][0]["initializeParams"]["diskType"] = f"zones/{z}/diskTypes/pd-ssd"
        try:
            wait_zone_op(api("POST", f"{COMPUTE}/zones/{z}/instances", body), z)
            zone = z
            break
        except RuntimeError as e:
            if "EXHAUSTED" not in str(e) and "unavailable" not in str(e):
                raise
            print(f"  {z}: no capacity, trying next zone")
    if not zone:
        print("no zone had capacity")
        return 1
    print(f"  bake VM {name} in {zone}")
    try:
        t0, last = time.time(), ""
        while True:
            time.sleep(30)
            st = json.loads(gcs_read(f"bake/{bake_id}/status.json") or b'{"state":"booting"}')["state"]
            inst = api("GET", f"{COMPUTE}/zones/{zone}/instances/{name}")
            line = f"  {int(time.time() - t0) // 60:3d} min  vm={inst['status']:<11} bake={st}"
            if line != last:
                print(line, flush=True)
                last = line
            if st.startswith("failed"):
                print((gcs_read(f"bake/{bake_id}/bake.log") or b"")[-3000:].decode(errors="replace"))
                return 1
            if st == "done" and inst["status"] == "TERMINATED":
                break
            if time.time() - t0 > 3 * 3600:
                print("bake timed out")
                return 1
        img = f"xhs-worker-{bake_id}"
        print(f"creating image {img} (family {IMAGE_FAMILY}) ...", flush=True)
        wait_global_op(api("POST", f"{COMPUTE}/global/images", {
            "name": img, "family": IMAGE_FAMILY, "labels": LABELS,
            "sourceDisk": f"zones/{zone}/disks/{name}",
            "description": f"XHS worker: {len(imgs)} task images; tools see gs://{BUCKET}/bake/{bake_id}/versions.txt"}))
        print((gcs_read(f"bake/{bake_id}/versions.txt") or b"").decode())
        print(f"image ready: projects/{PROJECT}/global/images/{img}")
        return 0
    finally:
        print(f"deleting bake VM {name}")
        try:
            wait_zone_op(api("DELETE", f"{COMPUTE}/zones/{zone}/instances/{name}"), zone)
        except RuntimeError as e:
            print(f"  WARNING: could not delete {name}: {e}")


# ── run ──────────────────────────────────────────────────────────────────

def package_code(dest: Path) -> None:
    """Working tree (uncommitted changes included) minus results/archive/runs; keeps results/id_mapping.json."""
    def flt(ti: tarfile.TarInfo):
        n = ti.name
        if any(p in n.split("/") for p in (".git", "__pycache__", "runs", "archive", ".venv")):
            return None
        if n.startswith("results/") and n != "results/id_mapping.json":
            return None
        return ti
    with tarfile.open(dest, "w:gz") as tf:
        for top in ("dataset", "evaluation", "tools", "results/id_mapping.json"):
            tf.add(XHS / top, arcname=top, filter=flt)


WORKER_SCRIPT = """set -u
export HOME=/root XHS_C6_CACHE=/opt/xhs-cache PATH=/usr/local/bin:/usr/bin:/bin:/snap/bin
F=/tmp/xhs-worker-$XHS_RUN_ID.py
[ -f $F ] || gcloud storage cp -q gs://$XHS_BUCKET/runs/$XHS_RUN_ID/worker.py $F
exec python3 $F
"""


def plan_tasks(a, ents: dict) -> list[dict]:
    if a.cases == ["all"]:
        cases = [(e["category"].lower(), iid) for iid, e in ents.items()]
    else:
        cases = []
        for c in a.cases:
            cat, iid = c.split(":")
            if iid not in ents:
                sys.exit(f"unknown case {c}")
            cases.append((cat, iid))
    tasks = []
    for cat, iid in cases:
        agent_min, max_s = budget(ents[iid])
        for m in a.models.split(","):
            for t in range(a.trials):
                tasks.append({"category": cat, "entry": iid, "agent": a.agent, "model": m, "trial": t,
                              "timeout_min": agent_min, "max_run_s": max_s, "quality": a.quality})
    return tasks


def job_spec(a, run_id: str, tasks_file: str, n: int, max_run_s: int, spot: bool, model: str) -> dict:
    vcpus = int(a.machine_type.rsplit("-", 1)[1])
    mem_mib = vcpus * 4 * 1024
    return {
        "taskGroups": [{
            "taskCount": n, "parallelism": min(n, a.parallelism), "taskCountPerNode": a.per_vm,
            "taskSpec": {
                "runnables": [{"script": {"text": WORKER_SCRIPT}}],
                "computeResource": {"cpuMilli": vcpus * 1000 // a.per_vm - 500,
                                    "memoryMib": mem_mib // a.per_vm - 1024},
                "maxRunDuration": f"{max_run_s}s", "maxRetryCount": 2,
                "environment": {"variables": {"XHS_BUCKET": BUCKET, "XHS_RUN_ID": run_id,
                                              "XHS_TASKS_FILE": tasks_file, "XHS_VERIFY_SLOTS": str(max(2, a.per_vm)),
                                              **dict(kv.split("=", 1) for kv in (a.env or []))}},
            }}],
        "allocationPolicy": {
            "location": {"allowedLocations": [f"regions/{REGION}"]},
            "instances": [{"policy": {
                "machineType": a.machine_type, "provisioningModel": "SPOT" if spot else "STANDARD",
                "bootDisk": {"image": f"projects/{PROJECT}/global/images/family/{IMAGE_FAMILY}",
                             "sizeGb": str(a.disk_gb), "type": "pd-balanced"}}}],
            "serviceAccount": {"email": SA},
            "labels": {**LABELS, "xhs-run": run_id},
        },
        "labels": {**LABELS, "xhs-run": run_id, "xhs-model": model.replace(".", "-")[:60]},
        "logsPolicy": {"destination": "CLOUD_LOGGING"},
    }


def save_state(run_id: str, st: dict) -> None:
    d = STATE_DIR / run_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "state.json").write_text(json.dumps(st, indent=1))


def load_state(run_id: str) -> dict:
    p = STATE_DIR / run_id / "state.json"
    if p.is_file():
        return json.loads(p.read_text())
    raw = gcs_read(f"runs/{run_id}/state.json")
    if raw:
        return json.loads(raw)
    sys.exit(f"no state for run {run_id}")


def cmd_run(a) -> int:
    ents = entries()
    tasks = plan_tasks(a, ents)
    base = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    run_id = "xhs-" + base.strftime("%Y%m%d-%H%M%S")
    for i, t in enumerate(tasks):  # unique run timestamps: merged run folders never collide
        t["run_ts"] = (base + dt.timedelta(seconds=i)).strftime("%Y%m%d_%H%M%S")
    since = tasks[0]["run_ts"]
    until = (base + dt.timedelta(seconds=len(tasks))).strftime("%Y%m%d_%H%M%S")
    # one Batch job per (model, provisioning class): per-model concurrency cap and Spot only for short tasks
    groups: dict[tuple[str, bool], list[dict]] = {}
    for t in tasks:
        spot = a.spot == "all" or (a.spot == "auto" and t["max_run_s"] - 25 * 60 <= 75 * 60)
        groups.setdefault((t["model"], spot), []).append(t)
    print(f"run {run_id}: {len(tasks)} trials in {len(groups)} Batch job(s); machine {a.machine_type} x "
          f"{a.per_vm} trials/VM; parallelism {a.parallelism} per job")
    tmp = Path(tempfile.mkdtemp())
    package_code(tmp / "code.tgz")
    prefix = f"runs/{run_id}"
    gsutil("cp", str(tmp / "code.tgz"), f"gs://{BUCKET}/{prefix}/code.tgz")
    gsutil("cp", str(HERE / "worker.py"), f"gs://{BUCKET}/{prefix}/worker.py")
    jobs = []
    for gi, ((model, spot), ts) in enumerate(sorted(groups.items())):
        tf = f"tasks-{gi}.json"
        gcs_write(f"{prefix}/{tf}", json.dumps({"tasks": ts}).encode())
        job_id = f"{run_id}-{gi}{'s' if spot else 'o'}"
        spec = job_spec(a, run_id, tf, len(ts), max(t["max_run_s"] for t in ts), spot, model)
        api("POST", f"{BATCH}/jobs?job_id={job_id}", spec)
        jobs.append({"job": job_id, "tasks_file": tf, "n": len(ts), "spot": spot, "model": model})
        print(f"  submitted {job_id}: {len(ts)} trials of {model} ({'Spot' if spot else 'on-demand'})")
    st = {"run_id": run_id, "agent": a.agent, "created": base.isoformat(), "since": since, "until": until, "jobs": jobs,
          "machine_type": a.machine_type, "per_vm": a.per_vm, "disk_gb": a.disk_gb,
          "categories": sorted({t["category"] for t in tasks}), "n_tasks": len(tasks),
          "tasks": {f"tasks-{i}-t{k:04d}": t for i, j in enumerate(jobs)
                    for k, t in enumerate(json.loads(gcs_read(f"{prefix}/{j['tasks_file']}"))["tasks"])}}
    save_state(run_id, st)
    gcs_write(f"{prefix}/state.json", json.dumps(st).encode())
    if a.detach:
        print(f"detached. Follow with:  python3 {Path(__file__).relative_to(XHS)} status {run_id} --watch")
        return 0
    return watch_and_finish(run_id, a.keep_gcs, a.interval)


def watch_and_finish(run_id: str, keep_gcs: bool, interval: int) -> int:
    def on_signal(signum, _frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, on_signal)
    ok = False
    try:
        while True:
            done = print_status(run_id)
            if done:
                break
            time.sleep(interval)
        ok = collect(run_id)
        return 0 if ok else 1
    except KeyboardInterrupt:
        print("\ninterrupted: collecting what finished, then tearing down")
        try:
            ok = collect(run_id)
        except Exception as e:  # pylint: disable=broad-except
            print(f"collect failed: {e}")
        return 130
    except Exception as e:  # pylint: disable=broad-except
        print(f"error: {e}")
        return 1
    finally:
        # never delete the only copy of results that didn't make it to results/
        teardown(run_id, keep_gcs or not ok)


def job_states(st: dict) -> dict[str, dict]:
    out = {}
    for j in st["jobs"]:
        r = api("GET", f"{BATCH}/jobs/{j['job']}", ok404=True)
        out[j["job"]] = r or {"status": {"state": "DELETED"}}
    return out


def read_statuses(run_id: str) -> dict[str, dict]:
    out = {}
    for it in gcs_list(f"runs/{run_id}/status/"):
        raw = gcs_read(it["name"])
        if raw:
            d = json.loads(raw)
            out[d.get("key") or Path(it["name"]).stem] = d
    return out


def print_status(run_id: str) -> bool:
    st = load_state(run_id)
    js = job_states(st)
    stat = read_statuses(run_id)
    tasks = st["tasks"]
    counts = {"pending": 0, "starting": 0, "running": 0, "done": 0, "infra_error": 0}
    cell: dict[tuple[str, str], list] = {}
    for key, t in tasks.items():
        s = stat.get(key, {})
        state = s.get("state", "pending")
        counts[state] = counts.get(state, 0) + 1
        c = cell.setdefault((t["entry"], t["model"]), [0, 0, 0])  # passed, done, total
        c[2] += 1
        if state == "done":
            c[1] += 1
            c[0] += 1 if (s.get("reward") or 0) >= 1 else 0
    vms = instances_with_label("xhs-run", run_id)
    running_vms = [v for v in vms if v["status"] in ("RUNNING", "STAGING", "PROVISIONING")]
    created = dt.datetime.fromisoformat(st["created"])
    elapsed_h = (dt.datetime.now(dt.timezone.utc) - created).total_seconds() / 3600
    now = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"\n[{now}] {run_id}  elapsed {elapsed_h * 60:.0f} min  VMs running {len(running_vms)}  "
          + "  ".join(f"{k}={v}" for k, v in counts.items() if v))
    for j in st["jobs"]:
        s = js[j["job"]].get("status", {})
        tg = next(iter(s.get("taskGroups", {}).values()), {}).get("counts", {})
        print(f"  job {j['job']:<34} {s.get('state', '?'):<10} {j['model']:<24} "
              + " ".join(f"{k.lower()}={v}" for k, v in sorted(tg.items())))
        ev = s.get("statusEvents", [])
        if ev and s.get("state") in ("QUEUED", "SCHEDULED") and not running_vms:
            print(f"      last event: {ev[-1].get('description', '')[:200]}")  # e.g. zone capacity stockout
    models = sorted({t["model"] for t in tasks.values()})
    ents_ = sorted({t["entry"] for t in tasks.values()})
    print("  " + "case".ljust(8) + "".join(m[:22].ljust(24) for m in models))
    for e in ents_:
        row = "  " + e.ljust(8)
        for m in models:
            p, d, n = cell.get((e, m), [0, 0, 0])
            row += (f"{p}/{d} done of {n}" if n else "-").ljust(24)
        print(row)
    errs = [(k, s) for k, s in stat.items() if s.get("state") == "infra_error"]
    for k, s in errs[:5]:
        print(f"  infra_error {k} (attempt {s.get('attempt')}): {str(s.get('error', ''))[-160:]!r}")
    terminal = {"SUCCEEDED", "FAILED", "DELETED", "CANCELLED"}
    all_jobs_done = all(js[j["job"]].get("status", {}).get("state") in terminal for j in st["jobs"])
    # integrate VM-hours across polls (state file), so the estimate survives VMs being deleted at the end
    now_s = time.time()
    if st.get("_last_poll"):
        st["vm_hours"] = st.get("vm_hours", 0.0) + len(running_vms) * (now_s - st["_last_poll"]) / 3600
    st["_last_poll"] = now_s
    save_state(run_id, st)
    print(f"  VM-hours so far {st.get('vm_hours', 0.0):.2f}  est. compute cost ~${vm_cost(st, st.get('vm_hours', 0.0)):.2f}")
    return all_jobs_done


def vm_cost(st: dict, vm_hours: float) -> float:
    od, spot = PRICE.get(st["machine_type"], (0.8, 0.25))
    n_spot = sum(j["n"] for j in st["jobs"] if j["spot"])
    frac_spot = n_spot / max(1, st["n_tasks"])
    rate = (od * (1 - frac_spot) + spot * frac_spot) + st["disk_gb"] * DISK_PRICE_GB_H
    return rate * vm_hours


def collect(run_id: str) -> bool:
    """Download results into results/ (+ logs/status into $RUNS_DIR/cloud/<run>/). True if complete."""
    st = load_state(run_id)
    res = XHS / "results"
    tmp = Path(tempfile.mkdtemp(prefix="xhs-collect-"))
    n, failed = gcs_download(f"runs/{run_id}/results/", tmp)
    print(f"collected {n} result files" + (f", {len(failed)} FAILED" if failed else ""))
    for p in sorted(tmp.iterdir()):
        dst = res / p.name
        if p.is_dir():  # c*_runs/<run folder>
            dst.mkdir(parents=True, exist_ok=True)
            for rd in p.iterdir():
                target = dst / rd.name
                if target.exists():
                    shutil.rmtree(target)
                shutil.move(str(rd), str(target))  # /tmp may be another filesystem
        else:
            shutil.move(str(p), str(dst))
    logs = STATE_DIR / run_id / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    _, lfail = gcs_download(f"runs/{run_id}/logs/", logs)
    failed += lfail
    stat = read_statuses(run_id)
    (STATE_DIR / run_id / "status.json").write_text(json.dumps(stat, indent=1))
    for cat in st["categories"] if st.get("agent") in ("agy", "claude") else []:
        out = res / f"cloud_{run_id}_{cat}.md"
        r = subprocess.run([sys.executable, str(XHS / "tools" / "campaign_report.py"), "--category", cat,
                            "--since", st["since"], "--until", st["until"], "--out", str(out)],
                           capture_output=True, text=True)
        print(f"  report {cat}: {(r.stdout or r.stderr).strip().splitlines()[-1] if (r.stdout or r.stderr) else out}")
    return not failed


def teardown(run_id: str, keep_gcs: bool) -> None:
    st = load_state(run_id)
    for j in st["jobs"]:
        try:
            if api("GET", f"{BATCH}/jobs/{j['job']}", ok404=True):
                api("DELETE", f"{BATCH}/jobs/{j['job']}")
                print(f"  deleted job {j['job']}")
        except RuntimeError as e:
            print(f"  WARNING job {j['job']}: {e}")
    # wait until the jobs are really gone (running tasks may still upload while a job is deleting)
    for _ in range(40):
        if not any(api("GET", f"{BATCH}/jobs/{j['job']}", ok404=True) for j in st["jobs"]):
            break
        time.sleep(15)
    # Batch removes its VMs when a job ends or is deleted; remove anything left behind.
    for _ in range(20):
        left = instances_with_label("xhs-run", run_id)
        if not left:
            break
        for v in left:
            zone = v["zone"].rsplit("/", 1)[1]
            try:
                api("DELETE", f"{COMPUTE}/zones/{zone}/instances/{v['name']}")
            except RuntimeError:
                pass
        time.sleep(15)
    left = instances_with_label("xhs-run", run_id)
    print(f"  worker VMs left: {len(left)}" + (" (Batch is still deleting them)" if left else ""))
    if keep_gcs:
        print(f"  kept gs://{BUCKET}/runs/{run_id}/ (collect again with: collect {run_id}; then down {run_id})")
    else:
        names = [i["name"] for i in gcs_list(f"runs/{run_id}/")]
        for nm in names:
            try:
                api("DELETE", f"https://storage.googleapis.com/storage/v1/b/{BUCKET}/o/{urllib.parse.quote(nm, safe='')}", ok404=True)
            except RuntimeError:
                pass
        print(f"  removed gs://{BUCKET}/runs/{run_id}/ ({len(names)} objects)")


def cmd_status(a) -> int:
    if a.watch:
        while not print_status(a.run_id):
            time.sleep(a.interval)
        return 0
    print_status(a.run_id)
    return 0


def cmd_collect(a) -> int:
    collect(a.run_id)
    return 0


def cmd_down(a) -> int:
    ok = True if a.no_collect else collect(a.run_id)
    teardown(a.run_id, a.keep_gcs or not ok)
    return 0


def cmd_gc(a) -> int:
    jobs, page = [], None
    while True:  # the Batch list filter doesn't support labels: filter client-side
        r = api("GET", f"{BATCH}/jobs?pageSize=200" + (f"&pageToken={page}" if page else ""))
        jobs += [j for j in r.get("jobs", []) if j.get("labels", {}).get("purpose") == "xhs-runner"]
        page = r.get("nextPageToken")
        if not page:
            break
    r = {"jobs": jobs}
    for j in r.get("jobs", []):
        state = j.get("status", {}).get("state")
        name = j["name"].rsplit("/", 1)[1]
        if state in ("SUCCEEDED", "FAILED", "CANCELLED") or a.all:
            api("DELETE", f"https://batch.googleapis.com/v1/{j['name']}")
            print(f"deleted job {name} ({state})")
        else:
            print(f"kept   job {name} ({state}); use --all to delete running jobs")
    live_runs = {j.get("labels", {}).get("xhs-run") for j in r.get("jobs", [])
                 if j.get("status", {}).get("state") not in ("SUCCEEDED", "FAILED", "CANCELLED")} if not a.all else set()
    for v in instances_with_label("purpose", "xhs-runner"):
        run = v.get("labels", {}).get("xhs-run")
        if run and run in live_runs:
            continue
        zone = v["zone"].rsplit("/", 1)[1]
        api("DELETE", f"{COMPUTE}/zones/{zone}/instances/{v['name']}")
        print(f"deleted VM {v['name']}")
    if a.gcs:  # objects of runs without a live job (e.g. late uploads after a teardown)
        stale = [i["name"] for i in gcs_list("runs/") if i["name"].split("/")[1] not in live_runs]
        for nm in stale:
            api("DELETE", f"https://storage.googleapis.com/storage/v1/b/{BUCKET}/o/{urllib.parse.quote(nm, safe='')}", ok404=True)
        print(f"deleted {len(stale)} stale objects under gs://{BUCKET}/runs/")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("bake")
    b.add_argument("--machine-type", default="n2-standard-8")
    b.add_argument("--disk-gb", type=int, default=400)
    r = sub.add_parser("run")
    r.add_argument("--cases", nargs="+", required=True, help="cat:ENTRY ... or 'all' (C6-C9)")
    r.add_argument("--agent", required=True, choices=["agy", "claude", "gold", "empty"])
    r.add_argument("--models", required=True, help="comma-separated")
    r.add_argument("--trials", type=int, default=3)
    r.add_argument("--quality", default="full", choices=["off", "machine", "full"])
    r.add_argument("--parallelism", type=int, default=40, help="max concurrent trials per model")
    r.add_argument("--per-vm", type=int, default=2, help="concurrent trials per VM")
    r.add_argument("--machine-type", default="n2-standard-16")
    r.add_argument("--disk-gb", type=int, default=400)
    r.add_argument("--spot", default="none", choices=["none", "auto", "all"],
                   help="default none = on-demand VMs only (no preemption); auto: Spot for trials with "
                        "<= 75 min agent + verifier budget; all: Spot for everything")
    r.add_argument("--env", action="append", metavar="KEY=VAL",
                   help="extra environment for the harness on workers, e.g. XHS_DOCKER_LIMITS=0")
    r.add_argument("--interval", type=int, default=60)
    r.add_argument("--detach", action="store_true", help="submit and exit (then: status/collect/down)")
    r.add_argument("--keep-gcs", action="store_true")
    s = sub.add_parser("status")
    s.add_argument("run_id")
    s.add_argument("--watch", action="store_true")
    s.add_argument("--interval", type=int, default=60)
    c = sub.add_parser("collect")
    c.add_argument("run_id")
    d = sub.add_parser("down")
    d.add_argument("run_id")
    d.add_argument("--keep-gcs", action="store_true")
    d.add_argument("--no-collect", action="store_true")
    g = sub.add_parser("gc")
    g.add_argument("--all", action="store_true", help="also delete running jobs and their VMs")
    g.add_argument("--gcs", action="store_true", help="also delete GCS objects of runs without a live job "
                   "(uncollected results are lost)")
    a = p.parse_args()
    return {"bake": cmd_bake, "run": cmd_run, "status": cmd_status, "collect": cmd_collect,
            "down": cmd_down, "gc": cmd_gc}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
