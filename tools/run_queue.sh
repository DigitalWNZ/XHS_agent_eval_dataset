#!/bin/bash
# Run an agent (AGENT=agy|claude, MODELS=...) on a queue of entries, both models per entry (3 trials each), at most K entries at
# a time; after both models finish an entry, optionally remove its udocker base (disk).
# Usage: run_queue.sh <K> <timeout_min> <rm|keep> <cat:ENTRY> [<cat:ENTRY> ...]
K=$1; TMO=$2; RM=$3; shift 3
XHS="$(cd "$(dirname "$0")/.." && pwd)"   # this repo (tools/ lives at its top level)
RUNS=${RUNS_DIR:-$XHS/runs}; LOG=${LOG_DIR:-$RUNS/agy}; mkdir -p "$LOG"   # RUNS_DIR / LOG_DIR: where queue logs go
export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.cache/xhs_c6/agy-adc/adc.json
AGENT=${AGENT:-agy}
MODELS=${MODELS:-"gemini-3.6-flash-high gemini-3.8-flash-high"}
TRIALS=${TRIALS:-3}
QUALITY=${QUALITY:-machine}   # off | machine | full (LLM judge inline)

one_entry() {
  local cat=${1%%:*} e=${1##*:}
  cd "$XHS" || return 1
  echo "$(date +%T) start $e"
  for m in $MODELS; do
    python3 -u evaluation/run_benchmark.py --category "$cat" --entry "$e" --agent "$AGENT" --model "$m" \
      --sandbox udocker --trials "$TRIALS" --timeout "$TMO" --quality "$QUALITY" > "$LOG/${e}_$m.log" 2>&1 &
  done
  wait
  for m in $MODELS; do
    echo "$(date +%T) done  $e $m: $(grep -h 'trial [0-9]:' "$LOG/${e}_$m.log" | sed -E 's/^ *trial ([0-9]): reward=([01]).*/\2/' | tr -d '\n')"
  done
  if [ "$RM" = rm ]; then
    local img name
    img=$(python3 -c "import json,glob;v=json.load(open(glob.glob('dataset/$cat/$e*.json')[0]))['environment'];print(v.get('udocker_image') or v['prebuilt_image'])")
    name="xhs-base-$(echo "$img" | tr 'A-Z' 'a-z' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')"
    udocker --quiet rm "$name" >/dev/null 2>&1 && echo "$(date +%T) removed base for $e"
  fi
}
export -f one_entry; export XHS LOG MODELS TRIALS TMO RM AGENT QUALITY
printf '%s\n' "$@" | xargs -P "$K" -I{} bash -c 'one_entry "$@"' _ {}
echo "$(date +%T) QUEUE DONE"
