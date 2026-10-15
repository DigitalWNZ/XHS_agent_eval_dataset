#!/bin/bash
# Full C6 (discriminative) + C7 (daily work) run on the current IDs, 3 trials per entry and model.
#   AGENT=agy    MODELS="gemini-3.6-flash-high gemini-3.8-flash-high"   (default)
#   AGENT=claude MODELS=claude-opus-5-5  (also export CLAUDE_CODE_USE_VERTEX=1 CLOUD_ML_REGION=global
#                                         ANTHROPIC_VERTEX_PROJECT_ID=<project>)
# Assumes the analysis-workspace layout (<root>/scripts/run_queue.sh, <root>/sources/xhs).
# Detached-safe: setsid nohup bash scripts/run_all.sh > runs/run_all.log 2>&1 < /dev/null & disown
cd "$(dirname "$0")/.." || exit 1
mkdir -p runs
export AGENT=${AGENT:-agy} TRIALS=${TRIALS:-3}
S=$(date -u +%Y%m%d_%H)
# --timeout caps each entry's own budget (harness uses min(--timeout, agent_timeout_sec)):
# Terminal-Bench 15-60 min (C6-04 = 60), SWE-bench 30 min, FrontierSWE 2 h, DeepSWE 3 h.
bash scripts/run_queue.sh 2 60  keep c6:C6-01 c6:C6-04 c6:C6-05 c6:C6-06 \
  c7:C7-01 c7:C7-02 c7:C7-03 c7:C7-04 > "runs/${AGENT}_queue_tb2.log" 2>&1 &
bash scripts/run_queue.sh 2 30  keep c7:C7-05 c7:C7-06 c7:C7-07 c7:C7-08 c7:C7-09 c7:C7-10 \
  > "runs/${AGENT}_queue_swebench.log" 2>&1 &
bash scripts/run_queue.sh 1 180 keep c6:C6-02 c6:C6-03 c7:C7-11 c7:C7-12 c7:C7-13 c7:C7-14 \
  > "runs/${AGENT}_queue_deepswe.log" 2>&1 &
bash scripts/run_queue.sh 1 120 keep c6:C6-07 > "runs/${AGENT}_queue_c6_07.log" 2>&1 &
wait
python3 scripts/summarize_agy.py "$S" > "runs/${AGENT}_summary.md" 2>&1
echo "$(date +%T) ALL QUEUES DONE; summary in runs/${AGENT}_summary.md"
