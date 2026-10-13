#!/usr/bin/env python3
"""Framework-free verifier for terminal-bench-2 task `polyglot-c-py`.

Faithful re-implementation of tests/test_outputs.py::test_fibonacci_polyglot
(terminal-bench-2 @ 69671fbaac6d67a7ef0dfec016cc38a64ef7a77c), without pytest/uv/Harbor.

Checks, in order (all must pass for reward=1):
  1. <root>/polyglot contains EXACTLY one entry: main.py.c   (no cmain, no scratch files)
  2. `gcc <root>/polyglot/main.py.c -o <root>/polyglot/cmain` exits 0 (warnings are OK)
  3. For n in (42, 10, 0): both `python3 main.py.c n` and `./cmain n` exit 0 and print
     (after .strip()) exactly 267914296, 55, 0.

Usage:
  python3 verify.py                 # grades /app (inside the task container / sandbox)
  python3 verify.py --root /tmp/ws  # grades a local directory that mirrors /app
Exit code 0 = pass (reward 1), 1 = fail (reward 0). Prints a JSON verdict on the last line.
"""

import argparse
import json
import os
import subprocess
import sys

TEST_CASES = [(42, "267914296"), (10, "55"), (0, "0")]


def verify(root: str, python: str = "python3", gcc: str = "gcc") -> dict:
  pdir = os.path.join(root, "polyglot")
  src = os.path.join(pdir, "main.py.c")
  binary = os.path.join(pdir, "cmain")
  res = {"reward": 0, "checks": []}

  # 1. Only main.py.c may exist (checked BEFORE compiling, exactly like the original test).
  try:
    files = os.listdir(pdir)
  except FileNotFoundError:
    res["reason"] = f"{pdir} does not exist"
    return res
  ok = files == ["main.py.c"]
  res["checks"].append({"check": "only_main_py_c", "pass": ok, "found": sorted(files)})
  if not ok:
    res["reason"] = f"Expected only main.py.c, found: {files}"
    return res

  # 2. Compile.
  cp = subprocess.run([gcc, src, "-o", binary], capture_output=True, text=True)
  res["checks"].append({"check": "gcc_compile", "pass": cp.returncode == 0,
                        "stderr": cp.stderr[-2000:]})
  if cp.returncode != 0:
    res["reason"] = "gcc failed"
    return res

  # 3. Outputs.
  for n, expected in TEST_CASES:
    py = subprocess.run([python, src, str(n)], capture_output=True, text=True)
    c = subprocess.run([binary, str(n)], capture_output=True, text=True)
    ok = (py.returncode == 0 and c.returncode == 0
          and py.stdout.strip() == expected and c.stdout.strip() == expected)
    res["checks"].append({"check": f"fib({n})", "pass": ok, "expected": expected,
                          "python": py.stdout.strip(), "python_rc": py.returncode,
                          "c": c.stdout.strip(), "c_rc": c.returncode})
    if not ok:
      res["reason"] = (f"f({n}): expected {expected}, got Python={py.stdout.strip()!r} "
                       f"(rc={py.returncode}), C={c.stdout.strip()!r} (rc={c.returncode})")
      return res

  res["reward"] = 1
  res["reason"] = "all checks passed"
  return res


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--root", default="/app")
  ap.add_argument("--python", default="python3")
  ap.add_argument("--gcc", default="gcc")
  a = ap.parse_args()
  verdict = verify(a.root, a.python, a.gcc)
  for c in verdict["checks"]:
    print(("PASS " if c["pass"] else "FAIL ") + c["check"])
  print(json.dumps(verdict))
  sys.exit(0 if verdict["reward"] == 1 else 1)
