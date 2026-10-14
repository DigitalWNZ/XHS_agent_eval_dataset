"""Shared helpers for the result reports: locate the XHS repo and map run IDs to current entry IDs.

Runs recorded before the C6/C7 restructure (folder timestamp < runs_before in
results/id_mapping.json) use the former IDs (old C6/C7/C8); later runs use the current IDs.
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
RUNS_BEFORE = _m["runs_before"]
OLD_TO_NEW = _m["old_to_new"]
_TS = re.compile(r"(\d{8}_\d{6})")


def run_ts(name: str) -> str:
    """Last YYYYMMDD_HHMMSS timestamp in a run folder / summary file name ('' if none)."""
    found = _TS.findall(os.path.basename(name.rstrip("/")))
    return found[-1] if found else ""


def current_id(entry_id: str, run_name: str) -> str:
    """Map an entry ID as recorded by a run to the current dataset ID."""
    ts = run_ts(run_name)
    if ts and ts < RUNS_BEFORE:
        return OLD_TO_NEW.get(entry_id, entry_id)
    return entry_id
