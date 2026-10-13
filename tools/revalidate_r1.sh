#!/bin/bash
# Re-validate under udocker R1 (rootless runc). Usage: revalidate_r1.sh "cat:ENTRY:agents[:rm]" ...
#   e.g. c8:C8-01:gold,empty:rm   -> run gold+empty, then remove the entry's base container.
cd "$(dirname "$0")/../sources/xhs" || exit 1
L=../../runs/validate_r1; mkdir -p $L
for spec in "$@"; do
  IFS=: read -r cat e agents rm <<< "$spec"
  echo "$(date +%T) $e ($(df -h --output=avail $HOME | tail -1 | tr -d ' ') free)"
  for a in ${agents//,/ }; do
    python3 -u evaluation/run_benchmark.py --category "$cat" --entry "$e" --agent "$a" \
      --sandbox udocker > "$L/${e}_$a.log" 2>&1
    echo "  $a: $(grep -h 'trial 0' "$L/${e}_$a.log" | sed 's/^ *trial 0: //' || tail -1 "$L/${e}_$a.log")"
  done
  if [ "$rm" = rm ]; then
    img=$(python3 -c "import json,glob;e=json.load(open(glob.glob('dataset/$cat/$e*.json')[0]))['environment'];print(e.get('udocker_image') or e['prebuilt_image'])")
    name="xhs-base-$(echo "$img" | tr 'A-Z' 'a-z' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')"
    udocker --quiet rm "$name" >/dev/null 2>&1 && echo "  removed $name"
  fi
done
echo "$(date +%T) ALL DONE"
