#!/usr/bin/env python3
"""Fetch a public registry image pinned by digest into a docker-save tarball for `udocker load`.

udocker cannot pull `repo@sha256:...`; this resolves the (amd64) manifest, downloads config +
layers anonymously, and writes manifest.json in docker-save layout with the given tag.

  fetch_oci_digest.py <registry/repo@sha256:...> <local-tag> <out.tar>
"""
import hashlib
import json
import os
import sys
import tarfile
import tempfile
import urllib.request


def main():
    ref, tag, out = sys.argv[1:4]
    repo_full, digest = ref.split("@")
    registry, repo = repo_full.split("/", 1)
    tok = json.load(urllib.request.urlopen(
        f"https://{registry}/v2/token?scope=repository:{repo}:pull"))["token"]

    def get(path, accept=None):
        h = {"Authorization": f"Bearer {tok}"}
        if accept:
            h["Accept"] = accept
        return urllib.request.urlopen(urllib.request.Request(f"https://{registry}/v2/{repo}/{path}",
                                                             headers=h))

    acc = ("application/vnd.oci.image.index.v1+json,application/vnd.oci.image.manifest.v1+json,"
           "application/vnd.docker.distribution.manifest.v2+json,"
           "application/vnd.docker.distribution.manifest.list.v2+json")
    m = json.load(get(f"manifests/{digest}", acc))
    if "manifests" in m:  # index -> amd64/linux manifest
        sub = next(x for x in m["manifests"]
                   if x.get("platform", {}).get("architecture") == "amd64"
                   and x.get("platform", {}).get("os") == "linux")
        m = json.load(get(f"manifests/{sub['digest']}", acc))
    with tempfile.TemporaryDirectory(dir=os.path.dirname(os.path.abspath(out))) as td:
        cfg = m["config"]["digest"].split(":")[1] + ".json"
        cfg_bytes = get(f"blobs/{m['config']['digest']}").read()
        img_cfg = json.loads(cfg_bytes)
        with open(os.path.join(td, cfg), "wb") as f:
            f.write(cfg_bytes)
        layers, parent = [], None
        for i, l in enumerate(m["layers"]):
            # Legacy docker-save layout (what udocker's loader walks): one dir per layer with
            # layer.tar + json {"id", "parent"}. Ids are synthetic and unique because images
            # can repeat a layer digest (e.g. the empty layer).
            lid = hashlib.sha256(f"{i}:{l['digest']}".encode()).hexdigest()
            name = f"{lid}/layer.tar"
            os.makedirs(os.path.join(td, lid), exist_ok=True)
            h = hashlib.sha256()
            with get(f"blobs/{l['digest']}") as r, open(os.path.join(td, name), "wb") as f:
                while chunk := r.read(1 << 20):
                    h.update(chunk)
                    f.write(chunk)
            assert "sha256:" + h.hexdigest() == l["digest"], f"digest mismatch layer {i}"
            meta = {"id": lid}
            if parent:
                meta["parent"] = parent
            # udocker reads Env/WorkingDir/Entrypoint/User from the layer json's `config`.
            meta["config"] = img_cfg.get("config", {})
            with open(os.path.join(td, lid, "json"), "w") as f:
                json.dump(meta, f)
            with open(os.path.join(td, lid, "VERSION"), "w") as f:
                f.write("1.0")
            parent = lid
            layers.append(name)
            print(f"layer {i + 1}/{len(m['layers'])} {l['size'] // 1_000_000} MB", flush=True)
        with open(os.path.join(td, "manifest.json"), "w") as f:
            json.dump([{"Config": cfg, "RepoTags": [tag], "Layers": layers}], f)
        with tarfile.open(out, "w") as t:
            for n in os.listdir(td):
                t.add(os.path.join(td, n), arcname=n)
    print("wrote", out)


if __name__ == "__main__":
    main()
