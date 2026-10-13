#!/usr/bin/env python3
"""Grade a SWE-bench instance from its eval log with the OFFICIAL swebench grading code.

Run with the grader venv's python (swebench==4.1.0), not the harness python:
  ~/.cache/xhs_c6/swebench-venv/bin/python evaluation/swebench_grade.py instance.json eval.log
Prints one JSON object: swebench's report for the instance (resolved, patch_successfully_applied,
tests_status{FAIL_TO_PASS,PASS_TO_PASS}{success,failure}).
"""
import json
import sys

from swebench.harness.grading import get_eval_report
from swebench.harness.test_spec.test_spec import make_test_spec


def main():
    inst = json.load(open(sys.argv[1]))
    spec = make_test_spec(inst)
    pred = {"instance_id": inst["instance_id"], "model_name_or_path": "xhs-c7",
            "model_patch": "(edited in place)"}
    report = get_eval_report(spec, pred, sys.argv[2], include_tests_status=True)
    print(json.dumps(report[inst["instance_id"]]))


if __name__ == "__main__":
    main()
