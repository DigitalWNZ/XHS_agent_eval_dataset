"""C6 — Environment (containerized terminal) tasks for the XHS benchmark harness.

An entry describes a task that runs inside its own environment (Docker image) instead of the
xhs-campaign-service git worktree used by C3/C5. Grading is done by a verifier script that runs
inside the same environment after the agent stops (outcome-based, like Terminal-Bench).

Flow per trial (run_trial):
  1. Start a fresh sandbox from the entry's `environment` (docker; udocker = rootless with the
     exact image; bwrap = host toolchain fallback).
  2. Run the agent:
       agent=loop    built-in minimal agent (Gemini API); every shell command it issues runs
                     INSIDE the sandbox. Highest fidelity.
       agent=agy|claude  the repo's usual CLI agents, run on the host (inside bwrap with the
                     benchmark repo hidden, see agent_isolation_prefix) in a workspace directory
                     that is bind-mounted into the sandbox at the task's workdir. They get a
                     `task-exec` helper (outside the repo) to run commands inside the environment.
       agent=gold    runs the entry's gold solution script (validates the task + verifier).
       agent=empty   does nothing (validates that an untouched workspace FAILS).
  3. agy/claude: capture workspace.diff + workspace_files.txt (capture_workspace).
  4. Run the entry's verifier (tb2_pytest / swebench / deepswe / harbor_separate / script) in the
     sandbox -> verdict.json {"reward", "reason", "checks", ...}.
  5. Destroy the sandbox; agy/claude: quality_grader.grade_trial -> quality.json
     (CONFIG["quality"]: off | machine = validity audit | full = + LLM judge).
Entry score: D1 = pass rate over N trials, snapped to the category rubric's D1 tiers.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import uuid
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "results"

# A non-interactive shell starts background jobs (`cmd &`, nohup) with SIGINT ignored, and
# that disposition is inherited by every child (agent, task-exec, udocker, pytest, the
# program under test). Tasks that test Ctrl-C handling would then fail spuriously, so
# restore the default handler: exec'd children then get SIGINT=default again.
import signal  # pylint: disable=g-import-not-at-top,g-bad-import-order
if signal.getsignal(signal.SIGINT) == signal.SIG_IGN:
    signal.signal(signal.SIGINT, signal.default_int_handler)

# Set by run_benchmark.main() from CLI flags.
CONFIG = {"trials": 5, "sandbox": "docker", "dry_run": False,
          "isolate_agent": True,   # run host CLI agents in bwrap with the dataset/results hidden
          "quality": "machine"}    # post-trial quality grading: off | machine (validity audit only) | full (+ LLM judge)

# Neutral git identity for agents: DeepSWE-derived entries grade only COMMITTED work, and neither the host
# nor the task images configure user.name/email, so `git commit` would fail. Host CLI agents
# inherit these via os.environ; containers get them via UdockerSandbox env vars.
GIT_IDENTITY = {"GIT_AUTHOR_NAME": "agent", "GIT_AUTHOR_EMAIL": "agent@example.com",
                "GIT_COMMITTER_NAME": "agent", "GIT_COMMITTER_EMAIL": "agent@example.com"}
for _k, _v in GIT_IDENTITY.items():
    os.environ.setdefault(_k, _v)

CMD_TIMEOUT_SEC = 120
MAX_OUTPUT_CHARS = 8000


# ── Sandboxes ─────────────────────────────────────────────────────────────
#
# All backends expose: workdir, ws (host dir mounted at workdir, or None), exec(cmd),
# exec_argv(argv), put_file(src, dest), put_dir(src, dest), read_file(path), close().
# Graders get a shared toolchain at /opt/xhs: bin/{uv,uvx} + persistent uv caches, so
# the original `uvx -p 3.13 -w pytest ... pytest /tests/test_outputs.py` runs in any image.

TOOLS_DIR = Path(os.environ.get("XHS_C6_CACHE", Path.home() / ".cache" / "xhs_c6"))


def _tools_dir() -> Path:
    """Host dir mounted at /opt/xhs: uv/uvx binaries + uv cache + uv-managed pythons."""
    b = TOOLS_DIR / "opt" / "bin"
    b.mkdir(parents=True, exist_ok=True)
    for tool in ("uv", "uvx"):
        src = shutil.which(tool)
        if src and not (b / tool).exists():
            shutil.copy2(src, b / tool)
    for d in ("uvcache", "uvpython"):
        (TOOLS_DIR / "opt" / d).mkdir(parents=True, exist_ok=True)
    return TOOLS_DIR / "opt"


def _run(argv: list[str], timeout: int) -> subprocess.CompletedProcess:
    """subprocess.run that kills the whole process group on timeout (proot/udocker children)."""
    # stdin=DEVNULL: udocker R1 (runc) hangs in init when it inherits an interactive stdin.
    p = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        # runc (udocker R1) starts the container in its own session, so killpg alone leaves the
        # task's processes running (e.g. an agent's hanging filter.py at 100% CPU). Kill every
        # descendant first, then the group.
        for pid in _descendants(p.pid):
            try:
                os.kill(pid, 9)
            except OSError:
                pass
        try:
            os.killpg(p.pid, 9)
        except OSError:
            pass
        p.communicate()
        raise
    return subprocess.CompletedProcess(argv, p.returncode, out, err)


def _descendants(root: int) -> list[int]:
    """All descendant PIDs of `root` (from /proc), deepest first."""
    children: dict[int, list[int]] = {}
    for d in os.listdir("/proc"):
        if d.isdigit():
            try:
                stat = Path(f"/proc/{d}/stat").read_text()
                ppid = int(stat.rsplit(")", 1)[1].split()[1])
                children.setdefault(ppid, []).append(int(d))
            except (OSError, ValueError, IndexError):
                pass
    out, stack = [], [root]
    while stack:
        for c in children.get(stack.pop(), []):
            out.append(c)
            stack.append(c)
    return out[::-1]


class DockerSandbox:
    """Real Docker (root hosts, e.g. the cloud workers in tools/cloud/): a fresh container per trial from
    the entry's EXACT published image (environment.prebuilt_image; digest refs work), so /tmp, /logs and
    /tests are per-trial by construction. The workdir is seeded from the image into the host workspace
    (shared with host CLI agents) and bind-mounted back. The source benchmark's cpus/memory limits are NOT
    enforced by default, matching the udocker runs all earlier results come from (with them, e.g. C6-01's
    grader exceeds its 900 s timeout); XHS_DOCKER_LIMITS=1 enforces them. A local Dockerfile build is only
    used when no prebuilt image exists.
    `image` overrides the image (verifier containers)."""

    def __init__(self, entry: dict, host_workspace: Path | None = None, image: str | None = None):
        env = entry["environment"]
        self.workdir = env.get("workdir", "/app")
        image = image or env.get("docker_image") or env.get("prebuilt_image")
        if not image:
            image = f"xhs-c6-{entry['instance_id'].lower()}"
            dockerfile = BASE_DIR / env["dockerfile"]
            subprocess.run(["docker", "build", "-q", "-t", image, "-f", str(dockerfile),
                            str(dockerfile.parent)], check=True, capture_output=True)
        elif subprocess.run(["docker", "image", "inspect", image], capture_output=True).returncode:
            subprocess.run(["docker", "pull", "-q", image], check=True, capture_output=True)
        self.image = image
        self.name = f"xhs-{entry['instance_id'].lower()}-{uuid.uuid4().hex[:10]}"
        self.ws = Path(host_workspace or tempfile.mkdtemp(prefix="xhs-c6-ws-"))
        self.own_ws = host_workspace is None
        seed = self.name + "-seed"  # seed the workspace with the image's workdir
        subprocess.run(["docker", "create", "--name", seed, image], check=True, capture_output=True)
        subprocess.run(["docker", "cp", f"{seed}:{self.workdir}/.", str(self.ws)], capture_output=True)
        subprocess.run(["docker", "rm", "-f", seed], capture_output=True)
        cmd = ["docker", "run", "-d", "--name", self.name, "-w", self.workdir, "--entrypoint", "",
               "-v", f"{_tools_dir()}:/opt/xhs", "-v", f"{self.ws}:{self.workdir}",
               "--label", "xhs-trial=1"]
        for k, v in {**GIT_IDENTITY, **env.get("container_env", {})}.items():
            cmd += ["-e", f"{k}={v}"]
        if env.get("cpus") and os.environ.get("XHS_DOCKER_LIMITS", "0") == "1":
            cmd += ["--cpus", str(env["cpus"])]
        if env.get("memory") and os.environ.get("XHS_DOCKER_LIMITS", "0") == "1":
            cmd += ["--memory", str(env["memory"])]
        if env.get("network") is False:
            cmd += ["--network", "none"]
        subprocess.run(cmd + [image, "sleep", "infinity"], check=True, capture_output=True)

    def exec_argv(self, argv: list[str]) -> list[str]:
        return ["docker", "exec", "-w", self.workdir, self.name] + argv

    def exec(self, cmd: str, timeout: int = CMD_TIMEOUT_SEC) -> subprocess.CompletedProcess:
        return _run(self.exec_argv(["bash", "-c", cmd]), timeout)

    def put_file(self, src: Path, dest: str) -> None:
        subprocess.run(["docker", "exec", self.name, "mkdir", "-p", str(Path(dest).parent)],
                       capture_output=True)
        subprocess.run(["docker", "cp", str(src), f"{self.name}:{dest}"], check=True,
                       capture_output=True)

    def put_dir(self, src: Path, dest: str) -> None:
        subprocess.run(["docker", "exec", self.name, "mkdir", "-p", dest], capture_output=True)
        subprocess.run(["docker", "cp", f"{src}/.", f"{self.name}:{dest}"], check=True,
                       capture_output=True)

    def read_file(self, path: str) -> str | None:
        p = subprocess.run(["docker", "exec", self.name, "cat", path], capture_output=True,
                           text=True, errors="replace")
        return p.stdout if p.returncode == 0 else None

    def close(self) -> None:
        subprocess.run(["docker", "rm", "-f", self.name], capture_output=True)
        if self.own_ws:
            shutil.rmtree(self.ws, ignore_errors=True)


_EXECMODE_CACHE: dict[str, str] = {}


def _udocker_desired_execmode() -> str:
    """R1 = rootless runc (user namespaces): no ptrace, so Go/JIT runtimes behave (under the
    default proot mode `go` segfaulted ~70% of the time). Needs unprivileged user namespaces and
    udocker patched for concurrent runs (tools/patch_udocker_r1.py). Else P1 (proot)."""
    if "mode" in _EXECMODE_CACHE:
        return _EXECMODE_CACHE["mode"]
    mode = os.environ.get("XHS_UDOCKER_EXECMODE", "")
    if not mode:
        mode = "P1"
        try:
            ok_ns = subprocess.run(["unshare", "-Ur", "true"], capture_output=True).returncode == 0
            py = Path(shutil.which("udocker") or "").resolve().read_text().splitlines()[0][2:]
            pkg = subprocess.run([py.strip(), "-c", "import udocker,os;print(os.path.dirname("
                                  "udocker.__file__))"], capture_output=True, text=True).stdout
            patched = "xhs patch 2" in (Path(pkg.strip()) / "engine/runc.py").read_text()
            if ok_ns and patched:
                mode = "R1"
            elif ok_ns:
                print("  [udocker] user namespaces OK but udocker is unpatched for concurrent R1 "
                      "runs; run tools/patch_udocker_r1.py. Using P1 (proot).")
        except (OSError, IndexError):
            pass
    _EXECMODE_CACHE["mode"] = mode
    return mode


def _udocker_set_execmode(name: str, cdir: Path, mode: str | None = None) -> None:
    """mode: per-entry override (environment/verification.udocker_execmode), e.g. "P1" for
    tasks whose grader switches users (runuser/setuid), which R1's single-uid mapping can't do."""
    mode = mode or _udocker_desired_execmode()
    f = (cdir / name).resolve() / "execmode"
    current = f.read_text().strip() if f.is_file() else "P1"
    if current != mode:
        subprocess.run(["udocker", "--quiet", "setup", f"--execmode={mode}", name],
                       capture_output=True)


class UdockerSandbox:
    """Rootless fallback with the EXACT task image: udocker (no daemon, no sudo).

    One base container per image is unpacked once (minutes for large images) and reused.
    Per trial, fresh host directories are bind-mounted over the mutable/sensitive paths:
      workdir (/app) - seeded from the image's workdir; shared with host CLI agents
      /tmp, /logs    - scratch + grader output
      /tests         - hidden tests, populated only at verification time
    so trials (and parallel runs) don't see each other's work or the tests. Limits: no
    CPU/memory caps, network shared with the host, proot isolation is not a security
    boundary, and writes outside the bind mounts (e.g. a system-wide pip install) land in
    the shared base container.
    """

    PER_TRIAL = ("/tmp", "/logs", "/tests")

    def __init__(self, entry: dict, host_workspace: Path | None = None, image: str | None = None):
        import fcntl  # pylint: disable=g-import-not-at-top
        env = entry["environment"]
        self.workdir = env.get("workdir", "/app")
        self.ud = ["udocker", "--quiet"]
        cdir = Path(os.environ.get("UDOCKER_DIR", Path.home() / ".udocker")) / "containers"
        # udocker can't pull `repo@sha256:...`: such images are fetched + loaded under a local
        # alias (tools/fetch_oci_digest.py) recorded as environment.udocker_image.
        image = image or env.get("udocker_image") or env["prebuilt_image"]
        self.name = "xhs-base-" + re.sub(r"[^a-z0-9]+", "-", image.lower()).strip("-")
        cdir.mkdir(parents=True, exist_ok=True)
        with open(cdir.parent / f".{self.name}.lock", "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if not (cdir / self.name).exists():
                r = subprocess.run(self.ud + ["inspect", image], capture_output=True)
                if r.returncode != 0:
                    subprocess.run(self.ud + ["pull", image], check=True, capture_output=True)
                subprocess.run(self.ud + ["create", f"--name={self.name}", image], check=True,
                               capture_output=True)
                if env.get("udocker_rmi_after_create"):  # bases don't need the layers
                    subprocess.run(self.ud + ["rmi", image], capture_output=True)
            _udocker_set_execmode(self.name, cdir, env.get("udocker_execmode"))
        self.root = (cdir / self.name).resolve() / "ROOT"
        self.trial = Path(tempfile.mkdtemp(prefix="xhs-c6-trial-"))
        self.mounts = {}
        # environment.per_trial_paths: extra fresh, empty dirs per trial, e.g. "/root" to hide
        # root-only verifier assets from the agent (it runs as fake root under proot), or
        # scratch dirs that would otherwise be written into the shared base container.
        for p in self.PER_TRIAL + tuple(env.get("per_trial_paths", [])):
            d = self.trial / p.strip("/")
            d.mkdir(parents=True, exist_ok=True)
            self.mounts[p] = d
        os.chmod(self.mounts["/tmp"], 0o1777)
        self.env_vars = {**GIT_IDENTITY, **env.get("container_env", {})}
        self.ws = Path(host_workspace or (self.trial / "app"))
        self.ws.mkdir(parents=True, exist_ok=True)
        self.own_ws = host_workspace is None
        seed = self.root / self.workdir.lstrip("/")
        if seed.is_dir():
            shutil.copytree(seed, self.ws, dirs_exist_ok=True, symlinks=True)
        self.tools = _tools_dir()

    def exec_argv(self, argv: list[str]) -> list[str]:
        vols = ["-v", f"{self.ws}:{self.workdir}", "-v", f"{self.tools}:/opt/xhs"]
        for p, d in self.mounts.items():
            vols += ["-v", f"{d}:{p}"]
        envs = [f"--env={k}={v}" for k, v in self.env_vars.items()]
        return (self.ud + ["run", "--nobanner", "-w", self.workdir] + vols + envs + [self.name]
                + argv)

    def exec(self, cmd: str, timeout: int = CMD_TIMEOUT_SEC) -> subprocess.CompletedProcess:
        return _run(self.exec_argv(["bash", "-c", cmd]), timeout)

    def _host_path(self, path: str) -> Path:
        if path == self.workdir or path.startswith(self.workdir.rstrip("/") + "/"):
            return self.ws / os.path.relpath(path, self.workdir)
        for p, d in self.mounts.items():
            if path == p or path.startswith(p + "/"):
                return d / os.path.relpath(path, p)
        return self.root / path.lstrip("/")
    def put_file(self, src: Path, dest: str) -> None:
        d = self._host_path(dest)
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, d)

    def put_dir(self, src: Path, dest: str) -> None:
        shutil.copytree(src, self._host_path(dest), dirs_exist_ok=True)

    def read_file(self, path: str) -> str | None:
        p = self._host_path(path)
        return p.read_text(errors="replace") if p.is_file() else None

    def close(self) -> None:
        # Never `udocker rm` the shared base; only drop this trial's host directories.
        shutil.rmtree(self.trial, ignore_errors=True)



class BwrapSandbox:
    """No-docker fallback: bubblewrap with host /usr read-only, no network, home hidden,
    and a temp dir mounted at the task workdir. Uses HOST toolchains (lower fidelity);
    only suitable for tasks that need nothing beyond the host's tools."""

    def __init__(self, entry: dict, host_workspace: Path | None = None):
        self.workdir = entry["environment"].get("workdir", "/app")
        self.ws = Path(host_workspace or tempfile.mkdtemp(prefix="xhs-c6-ws-"))
        self.own_ws = host_workspace is None
        self.extra = Path(tempfile.mkdtemp(prefix="xhs-c6-extra-"))  # for put_file targets

    def exec_argv(self, argv: list[str]) -> list[str]:
        return ["bwrap", "--unshare-all", "--die-with-parent", "--new-session",
                "--ro-bind", "/usr", "/usr", "--ro-bind", "/etc", "/etc",
                "--tmpfs", "/usr/local/google",  # Cloudtop homes live here: hide them
                "--symlink", "usr/bin", "/bin", "--symlink", "usr/lib", "/lib",
                "--symlink", "usr/lib64", "/lib64", "--symlink", "usr/sbin", "/sbin",
                "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
                "--bind", str(self.ws), self.workdir,
                "--ro-bind", str(self.extra), "/opt/xhs",
                "--chdir", self.workdir, "--clearenv",
                "--setenv", "PATH", "/usr/local/bin:/usr/bin:/bin",
                "--setenv", "HOME", "/tmp"] + argv

    def exec(self, cmd: str, timeout: int = CMD_TIMEOUT_SEC) -> subprocess.CompletedProcess:
        return _run(self.exec_argv(["bash", "-c", cmd]), timeout)

    def put_file(self, src: Path, dest: str) -> str:
        """Files are exposed read-only under /opt/xhs/<basename>; returns that path."""
        shutil.copy2(src, self.extra / Path(dest).name)
        return f"/opt/xhs/{Path(dest).name}"

    def put_dir(self, src: Path, dest: str) -> None:
        raise NotImplementedError("bwrap backend cannot run tb2_pytest graders; use udocker/docker")

    def read_file(self, path: str) -> str | None:
        return None

    def close(self) -> None:
        if self.own_ws:
            shutil.rmtree(self.ws, ignore_errors=True)
        shutil.rmtree(self.extra, ignore_errors=True)


def make_sandbox(entry: dict, host_workspace: Path | None = None):
    cls = {"docker": DockerSandbox, "udocker": UdockerSandbox,
           "bwrap": BwrapSandbox}[CONFIG["sandbox"]]
    return cls(entry, host_workspace)


# ── Agents ────────────────────────────────────────────────────────────────

LOOP_SYSTEM_PROMPT = """You are an AI assistant solving a command-line task in a Linux environment.
You act by issuing shell commands. Each turn, reply with ONLY a JSON object:
{"analysis": "<what you observed / what you will do>",
 "commands": ["<bash command>", ...],
 "task_complete": <true when you are done, else false>}
Commands run with `bash -c` from the working directory; each command runs in a fresh shell
(no persistent cd/env). You receive each command's exit code, stdout and stderr. When the task
is fully done, reply with task_complete=true and an empty commands list."""


def _gemini(model: str, contents: list, api_key: str) -> tuple[str, dict]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {"systemInstruction": {"parts": [{"text": LOOP_SYSTEM_PROMPT}]},
            "contents": contents,
            "generationConfig": {"temperature": 1.0, "responseMimeType": "application/json"}}
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json",
                                          "x-goog-api-key": api_key})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                d = json.load(r)
            parts = d["candidates"][0]["content"].get("parts", [])
            return ("".join(p.get("text", "") for p in parts if not p.get("thought")),
                    d.get("usageMetadata", {}))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 503) and attempt < 4:
                time.sleep(2 ** attempt * 5)
                continue
            raise RuntimeError(f"Gemini API {e.code}: {e.read().decode()[:500]}") from e
    raise RuntimeError("unreachable")


def _parse_action(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    try:
        a = json.loads(m.group(0) if m else text, strict=False)
        if not isinstance(a, dict):
            raise ValueError("top-level JSON is not an object")
    except (json.JSONDecodeError, ValueError) as e:
        return {"analysis": text[:500], "commands": [], "task_complete": False,
                "parse_error": str(e)}
    if isinstance(a.get("commands"), str):
        a["commands"] = [a["commands"]]
    a.setdefault("commands", [])
    a.setdefault("task_complete", False)
    return a


def run_loop_agent(sb, prompt: str, model: str, timeout_sec: int, max_turns: int = 200) -> dict:
    """Built-in agent: Gemini proposes shell commands; they run inside the sandbox."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("agent=loop needs GEMINI_API_KEY")
    contents = [{"role": "user", "parts": [{"text": prompt}]}]
    transcript, usage, t0 = [], {"input_tokens": 0, "output_tokens": 0}, time.time()
    for turn in range(max_turns):
        if time.time() - t0 > timeout_sec:
            transcript.append({"event": "agent_timeout"})
            break
        text, u = _gemini(model, contents, api_key)
        usage["input_tokens"] += u.get("promptTokenCount", 0)
        usage["output_tokens"] += u.get("candidatesTokenCount", 0)
        action = _parse_action(text)
        contents.append({"role": "model", "parts": [{"text": text}]})
        results = []
        for cmd in action["commands"]:
            try:
                p = sb.exec(cmd)
                results.append({"cmd": cmd, "rc": p.returncode,
                                "stdout": p.stdout[-MAX_OUTPUT_CHARS:],
                                "stderr": p.stderr[-MAX_OUTPUT_CHARS:]})
            except subprocess.TimeoutExpired:
                results.append({"cmd": cmd, "rc": None, "error": f"timeout {CMD_TIMEOUT_SEC}s"})
        transcript.append({"turn": turn, "action": action, "results": results})
        if action.get("task_complete") and not action["commands"]:
            break
        feedback = json.dumps(results) if results else "No commands were run."
        if action.get("parse_error"):
            feedback = ("Your previous reply was not valid JSON and nothing was executed "
                        f"(parser error: {action['parse_error']}). Reply with a single JSON object.")
        if action.get("task_complete"):
            feedback += "\nYou set task_complete=true; reply again with an empty commands list to finish."
        contents.append({"role": "user", "parts": [{"text": feedback}]})
    usage["total_tokens"] = usage["input_tokens"] + usage["output_tokens"]
    return {"elapsed_seconds": round(time.time() - t0, 1), "num_turns": len(transcript),
            "usage": usage, "transcript": transcript}


def _write_task_exec(sb, bin_dir: Path) -> Path:
    """Helper that runs a command inside the task environment (for host CLI agents)."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    helper = bin_dir / "task-exec"
    prefix = " ".join(shlex.quote(a) for a in sb.exec_argv(["bash", "-c"]))
    helper.write_text(f'#!/bin/bash\nexec {prefix} "$*"\n')
    helper.chmod(0o755)
    return helper


def build_host_agent_prompt(entry: dict, workspace: Path, helper: Path) -> str:
    workdir = entry["environment"].get("workdir", "/app")
    return (f"{entry['problem_statement'].rstrip()}\n\n"
            f"---\nEnvironment notes:\n"
            f"- The task environment is a container. Inside it, `{workdir}` is the task directory.\n"
            f"- On your side, `{workdir}` is mounted from your current working directory "
            f"`{workspace}`: files you create here appear in `{workdir}` inside the container.\n"
            f"- Run commands INSIDE the task environment with: `{helper} '<command>'` "
            f"(e.g. `{helper} 'cd {workdir} && ls -la'`). Use it to compile/test with the "
            f"environment's toolchain.\n"
            f"- Grading happens inside the container after you finish.\n"
            f"- Work only from this task description and the environment. Do not search for or "
            f"download the upstream fix, the original benchmark task, its tests or its reference "
            f"solution (online or on this machine); doing so is treated as a violation.\n")


# ── Agent isolation and workspace capture (coding-quality evidence) ───────

def agent_isolation_prefix(bind_paths: list[Path]) -> list[str]:
    """bwrap prefix for host CLI agents: the whole host stays visible (the agent CLIs need their
    config, credentials and network), but the benchmark repo (dataset with hidden tests and
    reference solutions, results of other runs), the analysis workspace around it and any
    XHS_AGENT_MASK paths are replaced by empty tmpfs, and /tmp is private (other trials'
    workspaces are invisible) except for this trial's own paths."""
    if not CONFIG.get("isolate_agent", True) or not shutil.which("bwrap"):
        return []
    repo = BASE_DIR.resolve()
    masks = {repo}
    if repo.parent.name == "sources":  # analysis workspace layout: <root>/sources/xhs
        masks.add(repo.parent.parent)
    extra = os.environ.get("XHS_AGENT_MASK", "").split(":") + [str(Path.home() / ".gemini" / "jetski" / "brain")]
    masks |= {Path(m).resolve() for m in extra if m and Path(m).exists()}
    args = ["bwrap", "--dev-bind", "/", "/", "--die-with-parent", "--tmpfs", "/tmp"]
    for m in sorted(masks, key=lambda x: len(str(x))):
        args += ["--tmpfs", str(m)]
    for b in bind_paths:  # this trial's workspace, helper and container mounts
        if b and Path(b).exists():
            args += ["--bind", str(b), str(b)]
    return args + ["--"]


def _sandbox_host_paths(sb) -> list[Path]:
    """Host paths under /tmp that the sandbox's exec argv mounts (udocker -v src:dst)."""
    out = []
    for a in sb.exec_argv(["true"]):
        for part in re.split(r"[=\s]", a):
            src = part.split(":", 1)[0]
            if src.startswith("/tmp/") and Path(src).exists():
                out.append(Path(src))
    return out


_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".cache", ".pytest_cache",
              ".mypy_cache", "target", ".gradle"}
_SNAP_MAX_FILE, _SNAP_MAX_TOTAL, _SNAP_MAX_FILES = 512 * 1024, 100 * 1024 * 1024, 20000


def _walk(root: Path):
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in _SKIP_DIRS]
        for fn in fns:
            fp = Path(dp) / fn
            if fp.is_file() and not fp.is_symlink():
                yield fp


def snapshot_workspace(ws: Path) -> dict | None:
    """Before the agent runs: remember a non-git workspace (copies of small files, stat of the rest)."""
    if ws is None or (ws / ".git").exists():
        return None
    snap_dir, total, files = Path(tempfile.mkdtemp(prefix="xhs-c6-snap-")), 0, {}
    for i, fp in enumerate(_walk(ws)):
        if i >= _SNAP_MAX_FILES:
            break
        rel, st = str(fp.relative_to(ws)), fp.stat()
        files[rel] = (st.st_size, int(st.st_mtime))
        if st.st_size <= _SNAP_MAX_FILE and total + st.st_size <= _SNAP_MAX_TOTAL:
            (snap_dir / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(fp, snap_dir / rel)
            total += st.st_size
    return {"dir": snap_dir, "files": files}


def capture_workspace(entry: dict, ws: Path, snap: dict | None, trial_dir: Path) -> None:
    """After the agent, before grading: write <trial>/workspace.diff (git-style) with every change
    the agent made in its workdir: for git repos all committed + uncommitted + untracked changes vs
    the base commit (temporary index, the repo itself is not touched); otherwise a before/after
    diff of the snapshot."""
    import difflib
    trial_dir.mkdir(parents=True, exist_ok=True)
    out = []
    try:
        if (ws / ".git").exists():
            v = entry["verification"]
            base = v.get("base_commit")
            if not base and v.get("instance"):
                base = json.loads((BASE_DIR / v["instance"]).read_text()).get("base_commit")
            idx = Path(tempfile.mkdtemp(prefix="xhs-c6-idx-")) / "index"
            env = {**os.environ, "GIT_INDEX_FILE": str(idx)}
            g = ["git", "-c", "core.fileMode=false", "-c", f"safe.directory={ws}", "-C", str(ws)]
            subprocess.run(g + ["read-tree", "HEAD"], env=env, capture_output=True, timeout=300)
            subprocess.run(g + ["add", "-A"], env=env, capture_output=True, timeout=600)
            d = subprocess.run(g + ["diff", "--cached", base or "HEAD"], env=env, capture_output=True,
                               text=True, errors="replace", timeout=600)
            shutil.rmtree(idx.parent, ignore_errors=True)
            out.append(d.stdout)
        elif snap is not None:
            before, after = snap["files"], {}
            for fp in _walk(ws):
                st = fp.stat()
                after[str(fp.relative_to(ws))] = (st.st_size, int(st.st_mtime))
            for rel in sorted(set(before) | set(after)):
                old_p, new_p = snap["dir"] / rel, ws / rel
                if rel in before and rel in after:
                    if before[rel] == after[rel] and (not old_p.exists() or old_p.read_bytes() == new_p.read_bytes()):
                        continue
                    if old_p.exists() and old_p.read_bytes() == new_p.read_bytes():
                        continue
                    status = "modified"
                else:
                    status = "added" if rel in after else "deleted"
                head = [f"diff --git a/{rel} b/{rel}"] + (["new file mode 100644"] if status == "added" else
                                                         ["deleted file mode 100644"] if status == "deleted" else [])
                def text(p):
                    try:
                        return p.read_text() if p.exists() and p.stat().st_size <= _SNAP_MAX_FILE else None
                    except (UnicodeDecodeError, OSError):
                        return None
                a = text(old_p) if status != "added" else ""
                b = text(new_p) if status != "deleted" else ""
                if a is None or b is None:
                    out.append("\n".join(head + [f"Binary or large file {status}: {rel}"]) + "\n")
                    continue
                body = difflib.unified_diff(a.splitlines(), b.splitlines(),
                                            "/dev/null" if status == "added" else f"a/{rel}",
                                            "/dev/null" if status == "deleted" else f"b/{rel}", lineterm="")
                out.append("\n".join(head + list(body)) + "\n")
    except (OSError, subprocess.SubprocessError) as e:
        out.append(f"# workspace capture failed: {e}\n")
    finally:
        if snap is not None:
            shutil.rmtree(snap["dir"], ignore_errors=True)
    try:  # final listing of the workdir (for "deliverable consists of exactly ..." rules)
        listing = sorted(str(fp.relative_to(ws)) for fp in _walk(ws))[:_SNAP_MAX_FILES]
        (trial_dir / "workspace_files.txt").write_text("\n".join(listing) + "\n")
    except OSError:
        pass
    diff = "".join(out)
    if len(diff) > 2_000_000:
        diff = diff[:2_000_000] + "\n# ... truncated at 2 MB\n"
    (trial_dir / "workspace.diff").write_text(diff)


# ── Verification ──────────────────────────────────────────────────────────

def verify_in_sandbox(sb, entry: dict) -> dict:
    """Grade the sandbox. Concurrent graders are limited host-wide by a file-lock semaphore
    (XHS_VERIFY_SLOTS, default 3): several tasks have timing-sensitive tests, which become flaky
    when many graders run at once. Slot 0 is the historical single `verify.lock`."""
    import fcntl  # pylint: disable=g-import-not-at-top
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    slots = max(1, int(os.environ.get("XHS_VERIFY_SLOTS", "3")))
    names = [f"verify.lock.{i}" for i in range(1, slots)] + ["verify.lock"]  # slot 0 last
    while True:
        for name in names:
            lock = open(TOOLS_DIR / name, "w")
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                lock.close()
                continue
            try:
                return _verify_unlocked(sb, entry)
            finally:
                lock.close()
        time.sleep(5)


def _verify_unlocked(sb, entry: dict) -> dict:
    v = entry["verification"]
    if v["type"] == "tb2_pytest":
        return _verify_tb2_pytest(sb, entry)
    if v["type"] == "swebench":
        return _verify_swebench(sb, entry)
    if v["type"] == "harbor_separate":
        return _verify_harbor_separate(sb, entry)
    if v["type"] == "deepswe":
        return _verify_deepswe(sb, entry)
    if v["type"] != "script":
        raise ValueError(f"Unsupported verification type: {v['type']}")
    script = BASE_DIR / v["script"]
    dest = v.get("container_path", "/tmp/verify.py")
    placed = sb.put_file(script, dest) or dest
    cmd = " ".join(shlex.quote(c.replace(dest, placed)) for c in v["command"])
    p = sb.exec(cmd, timeout=v.get("timeout_sec", 900))
    lines = [ln for ln in p.stdout.strip().splitlines() if ln.strip()]
    try:
        verdict = json.loads(lines[-1])
    except (IndexError, json.JSONDecodeError):
        verdict = {"reward": 0, "reason": f"verifier produced no JSON verdict "
                                          f"(rc={p.returncode}): {p.stderr[-500:]}"}
    verdict["verifier_rc"] = p.returncode
    return verdict


def _verify_tb2_pytest(sb, entry: dict) -> dict:
    """Run the source benchmark's own pytest suite (hidden from the agent) in the sandbox.

    Mirrors Terminal-Bench's tests/test.sh: tests are copied to /tests only now, the exact
    `uvx -p <py> -w pytest ... pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py`
    command runs from the workdir, and reward = 1 iff pytest exits 0. uv/uvx come from the
    shared /opt/xhs toolchain (instead of curl-installing uv each time).
    """
    v = entry["verification"]
    workdir = entry["environment"].get("workdir", "/app")
    sb.put_dir(BASE_DIR / v["tests_dir"], "/tests")
    cmd = ("mkdir -p /logs/verifier && "
           "export PATH=/opt/xhs/bin:$PATH UV_CACHE_DIR=/opt/xhs/uvcache "
           "UV_PYTHON_INSTALL_DIR=/opt/xhs/uvpython && "
           f"cd {shlex.quote(workdir)} && {v['command']}")
    try:
        p = sb.exec(cmd, timeout=v.get("timeout_sec", 900))
        rc, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        rc, out, err = None, "", f"verifier timeout {v.get('timeout_sec', 900)}s"
    checks, reason = [], None
    raw = sb.read_file("/logs/verifier/ctrf.json")
    if raw:
        try:
            for t in json.loads(raw).get("results", {}).get("tests", []):
                ok = t.get("status") == "passed"
                checks.append({"check": t.get("name"), "pass": ok, "status": t.get("status"),
                               "message": (t.get("message") or "")[:500]})
                if not ok and reason is None:
                    reason = f"{t.get('name')}: {(t.get('message') or t.get('status'))[:300]}"
        except json.JSONDecodeError:
            pass
    reward_txt = (sb.read_file("/logs/verifier/reward.txt") or "").strip()
    if reward_txt in ("0", "1"):
        reward = int(reward_txt)  # Terminal-Bench semantics: written by test.sh
    else:
        reward = 1 if rc == 0 and checks and all(c["pass"] for c in checks) else 0
    if reward:
        reason = f"all {len(checks)} tests passed"
    elif reason is None:
        reason = f"grader rc={rc}: {(err or out)[-400:]}"
    return {"reward": reward, "reason": reason, "checks": checks, "verifier_rc": rc,
            "reward_txt": reward_txt, "pytest_tail": out[-3000:]}


SWEBENCH_PY = Path(os.environ.get("XHS_SWEBENCH_PY",
                                  TOOLS_DIR / "swebench-venv" / "bin" / "python"))


def _verify_swebench(sb, entry: dict) -> dict:
    """SWE-bench grading (C7): run the instance's official eval.sh in the instance image on the
    agent-edited repo, then grade the combined log on the host with swebench's own parser and
    FAIL_TO_PASS / PASS_TO_PASS report (evaluation/swebench_grade.py, swebench==4.1.0).

    eval.sh resets the files touched by the hidden test patch to base_commit, applies the test
    patch, runs the test command between the '>>>>> Start/End Test Output' markers (printed by
    `set -x`, hence stderr is merged like the official harness does), then resets them again.
    """
    v = entry["verification"]
    workdir = entry["environment"].get("workdir", "/testbed")
    inst = json.loads((BASE_DIR / v["instance"]).read_text())
    diff = sb.exec(f"cd {shlex.quote(workdir)} && git -c core.fileMode=false diff "
                   f"{inst['base_commit']}", timeout=300).stdout
    sb.put_file(BASE_DIR / v["eval_script"], "/tests/eval.sh")
    # Official SWE-bench grades in a FRESH container. The agent's own test runs can leave temp
    # files that change test outcomes (e.g. requests' extract_zipped_paths only extracts into
    # /tmp if the file isn't there yet -> stale copy fails test_zipped_paths_extracted), so
    # grade with an empty /tmp.
    sb.exec("find /tmp -mindepth 1 -delete 2>/dev/null; true", timeout=120)
    try:
        p = sb.exec("bash /tests/eval.sh 2>&1", timeout=v.get("timeout_sec", 1800))
        rc, log = p.returncode, p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        rc, log = None, ">>>>> Tests Timed Out\n"
    with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False) as f:
        f.write(log)
        log_path = f.name
    try:
        g = subprocess.run([str(SWEBENCH_PY), str(BASE_DIR / "evaluation" / "swebench_grade.py"),
                            str(BASE_DIR / v["instance"]), log_path],
                           capture_output=True, text=True, timeout=300)
        report = json.loads(g.stdout.strip().splitlines()[-1]) if g.returncode == 0 else None
    finally:
        os.unlink(log_path)
    if report is None:
        return {"reward": 0, "reason": f"swebench grader failed: {g.stderr[-500:]}",
                "verifier_rc": rc, "eval_log_tail": log[-3000:], "model_patch": diff}
    ts = report.get("tests_status", {})
    checks = []
    for kind in ("FAIL_TO_PASS", "PASS_TO_PASS"):
        for res, ok in (("success", True), ("failure", False)):
            checks += [{"check": f"{kind}::{t}", "pass": ok} for t in ts.get(kind, {}).get(res, [])]
    f2p, p2p = ts.get("FAIL_TO_PASS", {}), ts.get("PASS_TO_PASS", {})
    counts = (f"F2P {len(f2p.get('success', []))}/{len(inst['FAIL_TO_PASS'])}, "
              f"P2P {len(p2p.get('success', []))}/{len(inst['PASS_TO_PASS'])}")
    if report.get("resolved"):
        reason = f"resolved ({counts})"
    elif not report.get("patch_successfully_applied"):
        reason = "eval did not run cleanly (test patch failed to apply / reset error / timeout)"
    else:
        first = (f2p.get("failure") or p2p.get("failure") or ["?"])[0]
        reason = f"not resolved ({counts}); first failure: {first}"
    return {"reward": int(bool(report.get("resolved"))), "reason": reason, "checks": checks,
            "verifier_rc": rc, "swebench_report": report, "model_patch": diff,
            "eval_log_tail": log[-3000:]}


def _verify_harbor_separate(sb, entry: dict) -> dict:
    """Harbor `environment_mode = "separate"` (FrontierSWE): the verifier runs clean-room in a
    disposable container from the task's VERIFIER image. Only the [[artifacts]] (the agent's
    /app minus the task's excludes) are copied in; the verifier may delete files (e.g. FFmpeg's
    reference sources), so it never touches the agent's base container. Reward is continuous in
    [0, 1] (/logs/verifier/reward.txt); details from reward_details.json."""
    import fnmatch  # pylint: disable=g-import-not-at-top
    import uuid  # pylint: disable=g-import-not-at-top
    v = entry["verification"]
    if isinstance(sb, DockerSandbox):
        return _verify_harbor_separate_docker(sb, entry)
    if not isinstance(sb, UdockerSandbox):
        raise NotImplementedError("harbor_separate is implemented for --sandbox udocker|docker")
    image = v.get("udocker_verifier_image") or v["verifier_image"]
    name = f"xhs-ver-{uuid.uuid4().hex[:12]}"
    work = Path(tempfile.mkdtemp(prefix="xhs-ver-"))
    app, logs = work / "app", work / "logs"
    logs.mkdir()
    # Harbor artifact excludes are `**/<name>` or `**/<dir>/**`: match on the basename.
    names_ex = [pat.removeprefix("**/").removesuffix("/**") for pat in
                v.get("artifact_excludes", [])]

    def _ignore(_d, names):
        return [n for n in names if any(fnmatch.fnmatch(n, pat) for pat in names_ex)]
    shutil.copytree(sb.ws, app, symlinks=True, ignore=_ignore)
    ud = ["udocker", "--quiet"]
    try:
        subprocess.run(ud + ["create", f"--name={name}", image], check=True, capture_output=True)
        _udocker_set_execmode(name, Path(os.environ.get("UDOCKER_DIR", Path.home() / ".udocker"))
                              / "containers", v.get("udocker_execmode")
                              or entry["environment"].get("udocker_execmode"))
        envs = [f"--env={k}={val}" for k, val in v.get("env", {}).items()]
        if getattr(sb, "oracle_flag", None):
            envs.append(f"--env=HARBOR_ORACLE_FLAG={sb.oracle_flag}")
        argv = (ud + ["run", "--nobanner", "-w", "/app", "-v", f"{app}:/app", "-v",
                      f"{logs}:/logs"] + envs + [name, "bash", "-c", v["command"]])
        try:
            p = _run(argv, v.get("timeout_sec", 10800))
            rc, out = p.returncode, (p.stdout + p.stderr)
        except subprocess.TimeoutExpired:
            rc, out = None, f"verifier timeout {v.get('timeout_sec', 10800)}s"
        vdir = logs / "verifier"
        txt = (vdir / "reward.txt").read_text().strip() if (vdir / "reward.txt").is_file() else ""
        details = {}
        if (vdir / "reward_details.json").is_file():
            details = json.loads((vdir / "reward_details.json").read_text())
        vlog = (vdir / "verifier.log").read_text(errors="replace") if (
            vdir / "verifier.log").is_file() else ""
    finally:
        subprocess.run(ud + ["rm", name], capture_output=True)
        shutil.rmtree(work, ignore_errors=True)
    return _harbor_result(rc, out, txt, details, vlog)


def _harbor_result(rc, out: str, txt: str, details: dict, vlog: str) -> dict:
    try:
        reward = max(0.0, min(1.0, float(txt)))
    except ValueError:
        reward = 0.0
    reason = details.get("reason") or "; ".join(details.get("notes") or []) or (
        f"reward {reward}" if txt else f"no reward written (rc={rc}): {out[-300:]}")
    keys = ("valid", "speedup", "correctness", "build_ok", "provenance_ok", "measured",
            "expected", "wall_ratio")
    return {"reward": reward, "reason": f"score={reward:.4f}; {reason}"[:600],
            "checks": [{"check": k, "pass": bool(details.get(k)), "value": details.get(k)}
                       for k in keys if k in details],
            "verifier_rc": rc, "reward_txt": txt, "reward_details": details,
            "verifier_log_tail": vlog[-4000:]}


def _verify_harbor_separate_docker(sb, entry: dict) -> dict:
    """harbor_separate under real Docker: same artifact copy and clean-room verifier as the udocker
    path, but the verifier image is used directly (digest refs work, no local alias needed)."""
    import fnmatch  # pylint: disable=g-import-not-at-top
    v = entry["verification"]
    image = v.get("docker_verifier_image") or v["verifier_image"]
    if subprocess.run(["docker", "image", "inspect", image], capture_output=True).returncode:
        subprocess.run(["docker", "pull", "-q", image], check=True, capture_output=True)
    work = Path(tempfile.mkdtemp(prefix="xhs-ver-"))
    app, logs = work / "app", work / "logs"
    logs.mkdir()
    names_ex = [pat.removeprefix("**/").removesuffix("/**") for pat in v.get("artifact_excludes", [])]

    def _ignore(_d, names):
        return [n for n in names if any(fnmatch.fnmatch(n, pat) for pat in names_ex)]
    shutil.copytree(sb.ws, app, symlinks=True, ignore=_ignore)
    name = f"xhs-ver-{uuid.uuid4().hex[:12]}"
    envs = []
    for k, val in v.get("env", {}).items():
        envs += ["-e", f"{k}={val}"]
    if getattr(sb, "oracle_flag", None):
        envs += ["-e", f"HARBOR_ORACLE_FLAG={sb.oracle_flag}"]
    argv = (["docker", "run", "--name", name, "--entrypoint", "", "-w", "/app", "-v", f"{app}:/app",
             "-v", f"{logs}:/logs", "--label", "xhs-trial=1"] + envs + [image, "bash", "-c", v["command"]])
    try:
        try:
            p = _run(argv, v.get("timeout_sec", 10800))
            rc, out = p.returncode, (p.stdout + p.stderr)
        except subprocess.TimeoutExpired:
            rc, out = None, f"verifier timeout {v.get('timeout_sec', 10800)}s"
        vdir = logs / "verifier"
        txt = (vdir / "reward.txt").read_text().strip() if (vdir / "reward.txt").is_file() else ""
        details = json.loads((vdir / "reward_details.json").read_text()) if (
            vdir / "reward_details.json").is_file() else {}
        vlog = (vdir / "verifier.log").read_text(errors="replace") if (vdir / "verifier.log").is_file() else ""
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
        shutil.rmtree(work, ignore_errors=True)
    return _harbor_result(rc, out, txt, details, vlog)


def _verify_deepswe(sb, entry: dict) -> dict:
    """DeepSWE v1.1 grading (DeepSWE-derived entries; verifier type deepswe), mirroring Harbor's flow for these tasks:
      1. collect: in the agent's sandbox, `git diff --binary <base> HEAD > model.patch`
         (only COMMITTED work counts, as the task instructions say);
      2. verify: a FRESH sandbox of the same image (pristine /app at base_commit), with
         model.patch at /logs/artifacts and the hidden tests (test.sh, test.patch, grader.py,
         config.json) at /tests; run the original `bash /tests/test.sh`.
    grader.py applies model.patch + test.patch, runs the suites and writes reward.json:
    reward = 1 iff every FAIL_TO_PASS test passes and no PASS_TO_PASS test fails.
    reward.txt == -1 is the tests' own crash sentinel (infrastructure error)."""
    v = entry["verification"]
    c = sb.exec(v["collect_command"], timeout=300)
    patch = sb.read_file("/logs/artifacts/model.patch") or ""
    vsb = make_sandbox(entry)
    try:
        vsb.put_dir(BASE_DIR / v["tests_dir"], "/tests")
        with tempfile.NamedTemporaryFile("w", suffix=".patch", delete=False) as f:
            f.write(patch)
            pf = f.name
        vsb.put_file(Path(pf), "/logs/artifacts/model.patch")
        os.unlink(pf)
        try:
            p = vsb.exec("bash /tests/test.sh", timeout=v.get("timeout_sec", 1800))
            rc, out = p.returncode, p.stdout + p.stderr
        except subprocess.TimeoutExpired:
            rc, out = None, f"verifier timeout {v.get('timeout_sec', 1800)}s"
        raw = vsb.read_file("/logs/verifier/reward.json")
        txt = (vsb.read_file("/logs/verifier/reward.txt") or "").strip()
        ctrf_raw = vsb.read_file("/logs/verifier/ctrf.json")  # grader.py: "[f2p] <id>" / "[p2p] <id>"
    finally:
        vsb.close()
    per_test = []
    if ctrf_raw:
        try:
            for t in json.loads(ctrf_raw).get("results", {}).get("tests", []):
                m = re.match(r"\[(f2p|p2p)\] (.*)$", t.get("name", ""), re.S)
                if m:
                    kind = "FAIL_TO_PASS" if m.group(1) == "f2p" else "PASS_TO_PASS"
                    per_test.append({"check": f"{kind}::{m.group(2)}", "pass": t.get("status") == "passed"})
        except json.JSONDecodeError:
            pass
    rj = {}
    if raw:
        try:
            rj = json.loads(raw)
        except json.JSONDecodeError:
            pass
    reward = int(rj.get("reward", 0) == 1)
    counts = (f"F2P {rj.get('f2p_passed', '?')}/{rj.get('f2p_total', '?')}, "
              f"P2P {rj.get('p2p_passed', '?')}/{rj.get('p2p_total', '?')}")
    if not patch.strip():
        reason = f"no committed changes (empty model.patch); {counts}"
    elif rj.get("apply_failed"):
        reason = "model.patch failed to apply"
    elif not rj:
        reason = f"verifier crashed (reward.txt={txt or 'missing'}, rc={rc}): {out[-300:]}"
    else:
        reason = f"{'resolved' if reward else 'not resolved'} ({counts})"
    return {"reward": reward, "reason": reason,
            "checks": [{"check": k, "pass": None, "value": rj[k]} for k in
                       ("f2p", "p2p", "partial") if k in rj] + per_test,
            "verifier_rc": rc, "reward_json": rj, "reward_txt": txt,
            "collect_rc": c.returncode, "model_patch_bytes": len(patch),
            "model_patch": patch[:400000], "test_stdout_tail": out[-4000:]}


# ── Trial + entry runners ─────────────────────────────────────────────────

def run_trial(entry: dict, agent: str, model: str, timeout_min: int, trial_dir: Path) -> dict:
    env = entry["environment"]
    timeout_sec = min(timeout_min * 60, env.get("agent_timeout_sec", timeout_min * 60))
    host_ws = Path(tempfile.mkdtemp(prefix="xhs-c6-host-")) if agent in ("agy", "claude") else None
    helper_dir = Path(tempfile.mkdtemp(prefix="xhs-c6-bin-")) if host_ws else None
    sb = make_sandbox(entry, host_ws)
    snap = None
    try:
        if env.get("init_cmd"):  # e.g. FrontierSWE: anchor the agent-visible sandbox-timer
            sb.exec(env["init_cmd"], timeout=120)
        if agent == "loop":
            ar = run_loop_agent(sb, entry["problem_statement"], model, timeout_sec)
        elif agent == "gold":
            t0 = time.time()
            gs = entry["gold_solution"]
            if gs.get("dir"):
                # Solution shipped as a directory (script + sources), run as Harbor's oracle
                # stage: copied to /solution, HARBOR_ORACLE_FLAG set for solve.sh + verifier.
                sb.oracle_flag = "xhs-oracle"
                sb.put_dir(BASE_DIR / gs["dir"], "/solution")
                cmd = f"export HARBOR_ORACLE_FLAG={sb.oracle_flag}; bash /solution/{gs['script']}"
            else:
                cmd = (BASE_DIR / gs["script"]).read_text()
            p = sb.exec(cmd, timeout=gs.get("timeout_sec", 600))
            ar = {"elapsed_seconds": round(time.time() - t0, 1), "num_turns": 0, "usage": {},
                  "transcript": [{"gold_rc": p.returncode, "stdout": p.stdout[-2000:],
                                  "stderr": p.stderr[-2000:]}]}
        elif agent == "empty":
            ar = {"elapsed_seconds": 0, "num_turns": 0, "usage": {}, "transcript": []}
        elif agent in ("agy", "claude"):
            from run_benchmark import invoke_agent  # lazy: avoid circular import
            # The helper lives outside the repo so its path doesn't lead the agent to the dataset.
            helper = _write_task_exec(sb, helper_dir)
            prompt = build_host_agent_prompt(entry, host_ws, helper)
            budget_min = max(1, timeout_sec // 60)
            snap = snapshot_workspace(host_ws)
            prefix = agent_isolation_prefix([host_ws, helper_dir] + _sandbox_host_paths(sb))
            t0 = time.time()
            try:
                r = invoke_agent(agent, model, prompt, host_ws, budget_min, need_file_writes=True,
                                 trajectory_file=trial_dir / "trajectory.jsonl", cmd_prefix=prefix)
                ar = {"elapsed_seconds": r["elapsed_seconds"], "num_turns": r["num_turns"],
                      "usage": r["usage"], "transcript": [{"response": r["response"],
                                                           "returncode": r["returncode"]}]}
            except subprocess.TimeoutExpired:
                # Benchmark semantics: the agent ran out of time; grade whatever it left.
                ar = {"elapsed_seconds": round(time.time() - t0, 1), "num_turns": 0,
                      "usage": {}, "transcript": [{"event": "agent_timeout",
                                                   "budget_sec": budget_min * 60}]}
        else:
            raise ValueError(f"Unknown agent for C6: {agent}")
        if host_ws:
            capture_workspace(entry, host_ws, snap, trial_dir)
            snap = None
        verdict = verify_in_sandbox(sb, entry)
    finally:
        sb.close()
        if host_ws:
            shutil.rmtree(host_ws, ignore_errors=True)
            shutil.rmtree(helper_dir, ignore_errors=True)
        if snap is not None:
            shutil.rmtree(snap["dir"], ignore_errors=True)
    trial_dir.mkdir(parents=True, exist_ok=True)
    (trial_dir / "transcript.json").write_text(json.dumps(ar["transcript"], indent=1,
                                                          ensure_ascii=False))
    (trial_dir / "verdict.json").write_text(json.dumps(verdict, indent=1, ensure_ascii=False))
    # Binary verifiers give 0/1. Continuous ones (reward in [0, 1]) pass at the entry's
    # verification.pass_threshold; the raw value is kept as `score`.
    score = float(verdict.get("reward", 0) or 0)
    passed = int(score >= float(entry["verification"].get("pass_threshold", 1.0)))
    quality = None
    if agent in ("agy", "claude") and CONFIG.get("quality", "machine") != "off":
        try:
            import quality_grader  # pylint: disable=g-import-not-at-top
            judge = CONFIG.get("judge", quality_grader.DEFAULT_JUDGE) if CONFIG.get("quality") == "full" else None
            q = quality_grader.grade_trial(trial_dir, entry, judge=judge)
            quality = {"quality_score": q["quality_score"], "valid": q["valid"],
                       "items": {i["id"]: i["level"] for i in q["items"]}}
        except Exception as e:  # quality grading must never break a run
            quality = {"error": f"{type(e).__name__}: {e}"}
    return {"reward": passed, "score": round(score, 6), "reason": verdict.get("reason"), "quality": quality,
            "elapsed_seconds": ar["elapsed_seconds"], "num_turns": ar["num_turns"],
            "usage": ar["usage"], "trial_dir": str(trial_dir)}


def _pass_at_k(n: int, c: int, k: int) -> float:
    if n - c < k:
        return 1.0
    prod = 1.0
    for i in range(n - c + 1, n + 1):
        prod *= 1 - k / i
    return round(1 - prod, 4)


def run_c6(entry: dict, agent: str, model: str, timeout: int) -> dict:
    """Run N trials of a containerized entry (C6 environment tasks, C7 SWE-bench repos)."""
    from run_benchmark import _get_tiers, _snap_to_tier  # lazy: avoid circular import
    iid = entry["instance_id"]
    cat = entry.get("category", "C6").lower()
    # gold/empty are deterministic (the verifier is deterministic), so one trial suffices.
    # Real agents are stochastic: use CONFIG["trials"] (default 5).
    n = 1 if agent in ("gold", "empty") else CONFIG["trials"]
    print(f"\n{'='*60}\nRunning {iid}: {entry.get('maps_to_journey', '')}")
    print(f"  sandbox={CONFIG['sandbox']} | agent={agent} | model={model} | trials={n}")
    # XHS_RUN_TS: fixed run timestamp (cloud workers get a unique one per task so run folders from
    # many machines never collide when merged into results/).
    ts = os.environ.get("XHS_RUN_TS") or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = RESULTS_DIR / f"{cat}_runs" / f"{iid}_{agent}_{model}_{ts}"
    trials = []
    for i in range(n):
        try:
            t = run_trial(entry, agent, model, timeout, run_dir / f"trial_{i}")
        except Exception as e:  # infra failure: record, count as 0, keep going
            t = {"reward": 0, "score": 0.0, "reason": f"infra_error: {e}", "elapsed_seconds": 0,
                 "num_turns": 0, "usage": {}, "infra_error": True}
        trials.append(t)
        print(f"  trial {i}: reward={t['reward']} score={t.get('score')} | "
              f"{str(t['reason'])[:110]}")
    passed = sum(t["reward"] for t in trials)
    rate = passed / n
    mean_score = sum(t.get("score", t["reward"]) for t in trials) / n
    d1 = _snap_to_tier(round(100 * rate), _get_tiers(cat, "D1"))
    usage = {k: sum(t["usage"].get(k, 0) or 0 for t in trials)
             for k in ("input_tokens", "output_tokens", "total_tokens")}
    return {
        "instance_id": iid, "agent": agent, "model": model,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sandbox": CONFIG["sandbox"],
        "agent_elapsed_seconds": round(sum(t["elapsed_seconds"] for t in trials), 1),
        "usage": usage,
        "num_turns": sum(t["num_turns"] for t in trials),
        "test_results": {"passed": passed, "total": n},
        "trials": trials,
        "scores": {"resolved": passed == n, "pass_rate": round(rate, 4),
                   "mean_score": round(mean_score, 4),
                   "pass_at_k": {str(k): _pass_at_k(n, passed, k) for k in (1, 3, 5) if k <= n},
                   "D1": {"score": d1}, "total_score": d1},
        "run_dir": str(run_dir),
    }
