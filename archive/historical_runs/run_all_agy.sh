#!/bin/bash
# HISTORICAL: records the Oct 2026 runs and uses the PRE-restructure IDs (old C6/C7/C8; see
# results/id_mapping.json). For new runs use tools/run_all.sh, which uses the current C6/C7 IDs.
# Detached orchestrator for the full agy run (C7, C8, C6-08), both models x 3 trials.
# Survives logout/laptop close (start with setsid nohup). Writes runs/agy_summary.md at the end.
cd "$(dirname "$0")/.." || exit 1
S=$(date -u +%Y%m%d_%H)
bash scripts/run_agy_queue.sh 4 30 keep c7:C7-07 c7:C7-01 c7:C7-02 c7:C7-03 c7:C7-04 c7:C7-05 c7:C7-06 > runs/agy_queue_c7.log 2>&1 &
bash scripts/run_agy_queue.sh 3 180 keep c8:C8-06 c8:C8-02 c8:C8-05 c8:C8-03 c8:C8-04 c8:C8-01 > runs/agy_queue_c8.log 2>&1 &
bash scripts/run_agy_queue.sh 1 120 keep c6:C6-08 > runs/agy_queue_c6_08.log 2>&1 &
wait
python3 scripts/summarize_agy.py "$S" > runs/agy_summary.md 2>&1
echo "$(date +%T) ALL QUEUES DONE; summary in runs/agy_summary.md"
