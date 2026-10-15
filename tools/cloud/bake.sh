#!/bin/bash
# XHS cloud worker image bake (startup script of a temporary VM, see `xhs_cloud.py bake`).
# Installs everything a worker needs and pre-pulls every task image, then reports to GCS and powers off;
# the controller turns the boot disk into an image of family `xhs-worker`.
# Metadata: xhs-bucket, xhs-bake-id, xhs-images (newline-separated image refs).
# Mirror progress to the serial console (readable with get-serial-port-output; SSH may be blocked).
exec > >(tee -a /var/log/xhs-bake.log > /dev/ttyS0) 2>&1
set -x
md() { curl -s -H "Metadata-Flavor: Google" "http://metadata.google.internal/computeMetadata/v1/instance/attributes/$1"; }
B=$(md xhs-bucket); ID=$(md xhs-bake-id)
report() {  # report <state>
  echo "XHS-BAKE: $1"
  echo "{\"state\":\"$1\",\"time\":$(date +%s)}" > /tmp/bake-status.json
  gcloud storage cp -q /tmp/bake-status.json "gs://$B/bake/$ID/status.json" || true
  gcloud storage cp -q /var/log/xhs-bake.log "gs://$B/bake/$ID/bake.log" || true
}
fail() { report "failed: $1"; poweroff; exit 1; }
report installing

export DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a NEEDRESTART_SUSPEND=1
systemctl disable --now unattended-upgrades apt-daily.timer apt-daily-upgrade.timer || true
apt-get update -q || fail apt-update
report apt-install
apt-get install -y -q -o Dpkg::Options::=--force-confold docker.io bubblewrap git python3 python3-venv python3-pip nodejs npm curl jq \
  ca-certificates sqlite3 xxd || fail apt-install
systemctl enable --now docker || fail docker

# Agent CLIs
report agents
timeout 900 npm install -g @anthropic-ai/claude-code || fail claude-code
gcloud storage cp -q "gs://$B/tools/agy" /usr/local/bin/agy && chmod 755 /usr/local/bin/agy || fail agy
# uv / uvx (graders) into /usr/local/bin
curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin INSTALLER_NO_MODIFY_PATH=1 sh || fail uv

# Harness cache dir (XHS_C6_CACHE) with the SWE-bench grader venv
report swebench-venv
C=/opt/xhs-cache; mkdir -p $C/opt/bin $C/opt/uvcache $C/opt/uvpython
cp /usr/local/bin/uv /usr/local/bin/uvx $C/opt/bin/
uv venv -p 3.12 $C/swebench-venv && VIRTUAL_ENV=$C/swebench-venv timeout 900 uv pip install swebench==4.1.0 || fail swebench
cat > /etc/profile.d/xhs.sh <<'EOF'
export XHS_C6_CACHE=/opt/xhs-cache
EOF

# Pre-pull task images (also avoids Docker Hub rate limits from many worker IPs)
report pulling
md xhs-images > /tmp/images.txt
n=0; bad=0
while read -r img || [ -n "$img" ]; do  # last line has no newline
  [ -z "$img" ] && continue
  n=$((n+1))
  report "pulling $n: $img"
  for a in 1 2 3; do timeout 1800 docker pull -q "$img" && break; sleep 10; done || { bad=$((bad+1)); echo "PULL FAILED $img"; }
done < /tmp/images.txt
docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' | sort > /tmp/images-pulled.txt
gcloud storage cp -q /tmp/images-pulled.txt "gs://$B/bake/$ID/images.txt" || true
[ "$bad" -eq 0 ] || fail "pull ($bad of $n failed)"

# Versions for the record
{ docker --version; bwrap --version; uv --version; claude --version; agy --version; node --version; python3 --version; df -h /; } \
  > /tmp/versions.txt 2>&1
gcloud storage cp -q /tmp/versions.txt "gs://$B/bake/$ID/versions.txt" || true

# Clean instance-specific state before imaging
apt-get clean; rm -rf /tmp/* /var/tmp/* /root/.npm
cloud-init clean --logs || true
report done
sync
poweroff
