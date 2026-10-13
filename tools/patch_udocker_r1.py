#!/usr/bin/env python3
"""Patch udocker's R1 (rootless runc) engine for concurrent runs of the same container.

Upstream behavior: when the container dir is writable, each `udocker run` writes its OCI spec
(config.json: the command, env, bind mounts) and runc state into the SHARED container dir, so
parallel runs of one container overwrite each other's spec (observed: run 2 executed run 1's
command, run 3 produced nothing). Read-only containers already get a private temp spec dir;
this patch makes every run use one. Idempotent; re-run after reinstalling/upgrading udocker.

Why R1 at all: under the default proot (P1/P2) modes the Go toolchain segfaults intermittently
(~70% of `go version` runs), which broke DeepSWE/C8 Go test suites. R1 uses unprivileged user
namespaces + runc: no ptrace, faster, closer to Docker.

Usage: python3 scripts/patch_udocker_r1.py   (then: udocker setup --execmode=R1 <container>)
"""
import pathlib
import subprocess
import sys

OLD = """            if self.localrepo.iswriteable_container(container_id):
                self._container_specdir = self.container_dir
            else:
                self._container_specdir = FileUtil("SPECDIR").mktmpdir()
                FileUtil(self._container_specdir).register_prefix()"""
NEW = """            # xhs patch: always use a private spec dir so concurrent runs of the same
            # container don't overwrite each other's config.json / runc state.
            self._container_specdir = FileUtil("SPECDIR").mktmpdir()
            FileUtil(self._container_specdir).register_prefix()"""


OLD2 = """        (pmaster, pslave) = os.openpty()
        status = subprocess.Popen(cmd_l, shell=False, close_fds=False,
                                  stdout=pslave, stderr=pslave)"""
NEW2 = """        # xhs patch 2: the spec has terminal=false here, so let runc inherit our stdio instead
        # of relaying a pty byte-by-byte (which crashed on multi-byte UTF-8, could drop the last
        # output and merged stderr into stdout).
        status = subprocess.call(cmd_l, shell=False, close_fds=True)
        self._filebind.finish()
        return status
        (pmaster, pslave) = os.openpty()
        status = subprocess.Popen(cmd_l, shell=False, close_fds=False,
                                  stdout=pslave, stderr=pslave)"""


def main():
    udocker = subprocess.run(["bash", "-c", "readlink -f $(command -v udocker)"],
                             capture_output=True, text=True).stdout.strip()
    py = pathlib.Path(udocker).read_text().splitlines()[0].lstrip("#!").strip()
    pkg = subprocess.run([py, "-c", "import udocker,os;print(os.path.dirname(udocker.__file__))"],
                         capture_output=True, text=True, check=True).stdout.strip()
    f = pathlib.Path(pkg) / "engine" / "runc.py"
    src = f.read_text()
    for name, old, new in (("private spec dir", OLD, NEW), ("stdio pass-through", OLD2, NEW2)):
        if new in src:
            print(f"already patched ({name}):", f)
            continue
        if old not in src:
            print(f"ERROR: expected code not found for {name} (udocker version changed?):", f)
            return 1
        src = src.replace(old, new)
        print(f"patched ({name}):", f)
    f.write_text(src)
    return 0


if __name__ == "__main__":
    sys.exit(main())
