#!/bin/bash
# Full C6 (discriminative, 7) + C7 (daily work, 11) + C8 (hard, 3) + C9 (customer-provided, 1) run on the current IDs (2026-10-15 layout),
# 3 trials per entry and model, with the LLM-judge quality grading inline (QUALITY=full).
#   AGENT=agy    MODELS="gemini-3.6-flash-high gemini-3.8-flash-high"   (default)
#   AGENT=claude MODELS=claude-opus-5-5  (also export CLAUDE_CODE_USE_VERTEX=1 CLOUD_ML_REGION=global
#                                         ANTHROPIC_VERTEX_PROJECT_ID=<project>)
# Run from anywhere; queue logs go to $RUNS_DIR (default <repo>/runs, git-ignored).
# Detached-safe: setsid nohup bash tools/run_all.sh > /tmp/run_all.log 2>&1 < /dev/null & disown
T="$(cd "$(dirname "$0")" && pwd)"
export RUNS_DIR=${RUNS_DIR:-$(dirname "$T")/runs}; R=$RUNS_DIR
mkdir -p "$R"
export AGENT=${AGENT:-agy} TRIALS=${TRIALS:-3} QUALITY=${QUALITY:-full}
S=$(date -u +%Y%m%d_%H)
# --timeout caps each entry's own budget (harness uses min(--timeout, agent_timeout_sec)):
# Terminal-Bench 15-60 min (C6-03 = 60), SWE-bench 30 min, FrontierSWE 2 h, DeepSWE 3 h.
bash "$T/run_queue.sh" 2 60  keep c6:C6-01 c6:C6-03 c6:C6-04 c6:C6-05 c6:C6-06 c7:C7-02 c8:C8-03 \
  > "$R/${AGENT}_queue_tb2.log" 2>&1 &
bash "$T/run_queue.sh" 2 30  keep c7:C7-03 c7:C7-04 c7:C7-05 c7:C7-06 c7:C7-07 c7:C7-08 c8:C8-01 \
  > "$R/${AGENT}_queue_swebench.log" 2>&1 &
bash "$T/run_queue.sh" 1 180 keep c6:C6-02 c6:C6-07 c7:C7-01 c7:C7-09 c7:C7-10 c7:C7-11 \
  > "$R/${AGENT}_queue_deepswe.log" 2>&1 &
bash "$T/run_queue.sh" 1 120 keep c8:C8-02 > "$R/${AGENT}_queue_frontierswe.log" 2>&1 &
bash "$T/run_queue.sh" 1 60  keep c9:C9-01 > "$R/${AGENT}_queue_customer.log" 2>&1 &
wait
python3 "$T/summarize_agy.py" "$S" > "$R/${AGENT}_summary.md" 2>&1
echo "$(date +%T) ALL QUEUES DONE; summary in $R/${AGENT}_summary.md"
