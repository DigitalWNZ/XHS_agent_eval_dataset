"""Shared helpers for the result reports: locate the XHS repo and map run IDs to current entry IDs.

Raw run folders keep the entry ID used when they ran. results/id_mapping.json lists one epoch per restructure
(2026-10-14: old C6/C7/C8 -> C6/C7; 2026-10-15: C6/C7 -> C6/C7/C8); a run is mapped through every epoch
whose runs_before is later than the run's folder timestamp.
"""
import json
import os
import re

_here = os.path.dirname(os.path.abspath(__file__))
# Works both from <xhs>/tools/ and from a sibling scripts/ dir next to sources/xhs.
XHS = next(p for p in (os.path.join(_here, ".."), os.path.join(_here, "..", "sources", "xhs"))
           if os.path.isdir(os.path.join(p, "dataset", "c6")))
XHS = os.path.abspath(XHS)

_m = json.load(open(os.path.join(XHS, "results", "id_mapping.json")))
# One epoch per restructure; older files may still have the single-epoch format.
EPOCHS = _m.get("epochs") or [{"runs_before": _m["runs_before"], "old_to_new": _m["old_to_new"]}]
_TS = re.compile(r"(\d{8}_\d{6})")


def run_ts(name: str) -> str:
    """Last YYYYMMDD_HHMMSS timestamp in a run folder / summary file name ('' if none)."""
    found = _TS.findall(os.path.basename(name.rstrip("/")))
    return found[-1] if found else ""


def current_id(entry_id: str, run_name: str) -> str:
    """Map an entry ID as recorded by a run to the current dataset ID."""
    ts = run_ts(run_name)
    for ep in EPOCHS:  # apply every later restructure, in order
        if ts and ts < ep["runs_before"]:
            entry_id = ep["old_to_new"].get(entry_id, entry_id)
    return entry_id
