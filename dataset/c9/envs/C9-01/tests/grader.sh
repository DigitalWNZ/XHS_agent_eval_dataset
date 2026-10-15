#!/bin/bash
# C9-01 grader: hidden Playwright tests against /app/index.html (Chromium from the image, /ms-playwright).
# uv/uvx come from the harness's shared /opt/xhs toolchain; playwright 1.55.0 matches the image's browsers.
mkdir -p /logs/verifier
export PLAYWRIGHT_BROWSERS_PATH=${PLAYWRIGHT_BROWSERS_PATH:-/ms-playwright}
cd /app || exit 1
uvx -p 3.12 \
  -w pytest==8.4.1 \
  -w pytest-json-ctrf==0.3.5 \
  -w playwright==1.55.0 \
  pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA -p no:cacheprovider
if [ $? -eq 0 ]; then echo 1 > /logs/verifier/reward.txt; else echo 0 > /logs/verifier/reward.txt; fi
