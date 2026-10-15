#!/bin/bash
# HISTORICAL: records the Oct 2026 runs and uses the PRE-restructure IDs (old C6/C7/C8; see
# results/id_mapping.json). For new runs use tools/run_all.sh, which uses the current C6/C7 IDs.
# Full C6 + C7 + C8 run with Claude Code + Opus 5.5 (Vertex), 3 trials per entry.
# Waits until the Gemini runs (run_all_agy.sh) and the C7-07 rerun have finished.
# Detached-safe (start with setsid nohup). Summary -> runs/claude_summary.md.
cd "$(dirname "$0")/.." || exit 1
echo "$(date +%T) waiting for Gemini runs to finish"
until grep -q "ALL QUEUES DONE" runs/run_all_agy.log 2>/dev/null \
   && grep -q "QUEUE DONE" runs/agy_queue_c7_07_rerun.log 2>/dev/null; do sleep 120; done
echo "$(date +%T) Gemini done; starting Claude"

export AGENT=claude MODELS=claude-opus-5-5 TRIALS=3
export CLAUDE_CODE_USE_VERTEX=1 CLOUD_ML_REGION=global ANTHROPIC_VERTEX_PROJECT_ID=cloud-llm-preview1
export PATH=$HOME/.local/bin:$PATH
S=$(date -u +%Y%m%d_%H)
# Per-entry budgets are capped by each entry's agent_timeout_sec; --timeout only sets the ceiling.
bash scripts/run_queue.sh 2 30  keep c6:C6-01 c6:C6-02 c6:C6-03 c6:C6-04 c6:C6-05 c6:C6-06 c6:C6-07 > runs/claude_queue_c6.log 2>&1 &
bash scripts/run_queue.sh 1 120 keep c6:C6-08 > runs/claude_queue_c6_08.log 2>&1 &
bash scripts/run_queue.sh 2 30  keep c7:C7-01 c7:C7-02 c7:C7-03 c7:C7-04 c7:C7-05 c7:C7-06 c7:C7-07 > runs/claude_queue_c7.log 2>&1 &
bash scripts/run_queue.sh 1 180 keep c8:C8-01 c8:C8-02 c8:C8-03 c8:C8-04 c8:C8-05 c8:C8-06 > runs/claude_queue_c8.log 2>&1 &
wait
python3 scripts/summarize_agy.py "$S" > runs/claude_summary.md 2>&1
python3 scripts/summarize_agy.py 20261013_13 > runs/all_models_summary.md 2>&1
echo "$(date +%T) CLAUDE ALL DONE; see runs/claude_summary.md and runs/all_models_summary.md"
