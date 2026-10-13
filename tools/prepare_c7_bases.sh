#!/bin/bash
# Pre-create udocker base containers for the C7 SWE-bench images, one at a time, removing the
# image layers after each create (containers don't depend on them) to keep disk usage low.
# Base names match env_runner.UdockerSandbox: xhs-base-<image lowercased, non-alnum -> '->.
set -u
CDIR=${UDOCKER_DIR:-$HOME/.udocker}/containers
for t in django_1776_django-15957 django_1776_django-15280 django_1776_django-12965 \
         django_1776_django-15503 django_1776_django-14376 django_1776_django-11532; do
  img="swebench/sweb.eval.x86_64.$t:latest"
  name="xhs-base-$(echo "$img" | tr 'A-Z' 'a-z' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')"
  [ -d "$CDIR/$name" ] && { echo "exists $name"; continue; }
  free_gb=$(df -BG --output=avail "$HOME" | tail -1 | tr -dc 0-9)
  if [ "$free_gb" -lt 8 ]; then echo "STOP: only ${free_gb}G free before $t"; exit 1; fi
  (
    flock 9
    echo "$(date +%T) pull $img"; udocker --quiet pull "$img" || exit 1
    echo "$(date +%T) create $name"; udocker --quiet create --name="$name" "$img" >/dev/null || exit 1
    udocker --quiet rmi "$img" >/dev/null 2>&1
    echo "$(date +%T) done $name ($(df -h --output=avail "$HOME" | tail -1) free)"
  ) 9>"${UDOCKER_DIR:-$HOME/.udocker}/.$name.lock"
done
