"""One-off: build rubric v3 (simple) from the v1 backup.
- evaluation/rubrics/coding_quality.json: pass/fail stays as D1; 3 common LLM-judge items (Readability,
  Maintainability, Robustness; meanings from C3 D3-D5) with perfect/accept/bad criteria.
- evaluation/rubrics/tasks/<ID>.json: 1-2 case-specific LLM-judge items per case (picked from the v1
  task-specific judge items) + the case's maintainability notes as judge context.
Provenance only: it writes the task rubrics under the 2026-10-14 IDs. The current files were then renamed by
tools/restructure_v2.py (2026-10-15 layout); don't re-run this on the current dataset."""
import json
import pathlib
import sys

X = pathlib.Path("/usr/local/google/home/wangez/agent_eval_dataset/sources/xhs")
V1 = pathlib.Path(sys.argv[1])  # backup dir with the v1 tasks/*.json

PICK = {  # case -> v1 judge item ids (1-2), chosen for being task-specific and not overlapping the common items
    "C6-01": ["C6-01-E1", "C6-01-R2"], "C6-02": ["C6-02-R2"], "C6-03": ["C6-03-R2"],
    "C6-04": ["C6-04-E2", "C6-04-R2"], "C6-05": ["C6-05-E2"], "C6-06": ["C6-06-E1"],
    "C6-07": ["C6-07-E1", "C6-07-R2"], "C7-01": ["C7-01-E1", "C7-01-R1"], "C7-02": ["C7-02-E1"],
    "C7-03": ["C7-03-E2", "C7-03-R2"], "C7-04": ["C7-04-E2", "C7-04-S1"], "C7-05": ["C7-05-E1"],
    "C7-06": ["C7-06-E1"], "C7-07": ["C7-07-E1"], "C7-08": ["C7-08-F2", "C7-08-R2"], "C7-09": ["C7-09-E1"],
    "C7-10": ["C7-10-R2"], "C7-11": ["C7-11-F2", "C7-11-E1"], "C7-12": ["C7-12-F2", "C7-12-R2"],
    "C7-13": ["C7-13-R2"], "C7-14": ["C7-14-R2"],
}

framework = {
    "name": "Coding quality rubric (C6 / C7 / C8 / C9)",
    "name_zh": "编码质量评分标准（C6 / C7 / C8 / C9）",
    "version": "3.0",
    "applies_to": ["C6", "C7"],
    "summary": ("Pass/fail stays exactly as before (D1: the source benchmark's hidden tests). On top, an LLM judge "
                "grades 3 common items (Readability, Maintainability, Robustness; meanings from C3 D3-D5) and 1-2 "
                "case-specific items per case (evaluation/rubrics/tasks/<ID>.json), each perfect / accept / bad."),
    "pass_fail": "D1, unchanged: a trial passes iff the source benchmark's hidden-test verifier passes (FrontierSWE: score >= pass_threshold).",
    "judge": {"model": "claude-opus-5-5 (Claude Code CLI via Vertex)", "calls": "one per trial; answers all items",
              "sees": "task prompt, reference solution (for comparison only), the agent's code change, a condensed action log, its final message, the hidden-test outcome"},
    "levels": {"perfect": {"score": 1.0, "zh": "完美"}, "accept": {"score": 0.6, "zh": "可接受"},
               "bad": {"score": 0.0, "zh": "不合格"}, "na": {"score": None, "zh": "不适用", "meaning": "no basis (e.g. no code change); excluded"}},
    "common_items": [
        {"id": "READABILITY", "name": "Readability", "name_zh": "可读性", "method": "llm_judge", "red_line": False,
         "source": "C3 D3 Readability",
         "question": "Is the agent's code easy to read: intent-revealing names, formatting consistent with the existing code, docstrings/comments where logic is non-obvious?",
         "criteria": {"perfect": "Intent-revealing naming that reads like natural language; formatting consistent with the existing codebase; public interfaces documented; complex logic has inline comments (minor documentation gaps on non-obvious logic are still perfect).",
                      "accept": "Mostly readable, but some cryptic names (temp, data1, v) or complex logic without comments.",
                      "bad": "Inconsistent naming/casing, large undocumented blocks, confusing layout, or cryptic naming throughout."},
         "caps": ["Single-letter variable names in business logic (not loop counters) -> at most accept."]},
        {"id": "MAINTAINABILITY", "name": "Maintainability", "name_zh": "可维护性", "method": "llm_judge", "red_line": False,
         "source": "C3 D4 Maintainability",
         "question": "Is the change well structured and easy to change later: separation of concerns, short single-responsibility functions, reuse of existing helpers, no copy-pasted logic, no dead code / debug leftovers?",
         "criteria": {"perfect": "Clear separation of concerns; short single-responsibility functions (mostly < 30 lines); reuses existing helpers and patterns; loose coupling; no copy-pasted logic, dead code or debug output.",
                      "accept": "Standard structure, but some details leak across layers, a few functions are monolithic, there is some duplicated logic, or leftover dead code / debug output.",
                      "bad": "Monolithic functions (> 80 lines), high complexity or deep nesting (4+ levels), systemic copy-paste, global mutable state, or tight coupling."},
         "caps": ["A single new file > 500 lines -> at most accept.", "A single function > 100 lines -> bad."]},
        {"id": "ROBUSTNESS", "name": "Robustness", "name_zh": "健壮性", "method": "llm_judge", "red_line": False,
         "source": "C3 D5 Robustness",
         "question": "Is the code defensive: specific exceptions handled, resources managed safely, inputs validated at boundaries, no magic constants, errors never silently swallowed?",
         "criteria": {"perfect": "Defensive throughout: specific exceptions handled, safe resource management, input validation at boundaries, no (or < 2 minor) magic constants, concurrency-safe where relevant.",
                      "accept": "Errors are handled, but generic catch-all blocks are common, some magic constants, or 1-2 edge cases lack validation.",
                      "bad": "Errors silently swallowed (bare except / except Exception: pass), resource-leak risks, no input validation, or hardcoded credentials."},
         "caps": ["Bare except: / except Exception: pass in business logic -> at most accept.",
                  "Errors silently swallowed on data-mutation paths -> bad.", "Hardcoded secrets/credentials -> bad."]},
    ],
    "case_items": "1-2 per case in evaluation/rubrics/tasks/<ID>.json: task-specific questions (e.g. edge cases the tests don't cover, API compatibility), LLM judge, perfect / accept / bad.",
    "aggregation": {"quality_score": "100 * mean of the item scores (3 common + 1-2 case items, equal weight; n/a excluded)",
                    "per_case_model": "pass rate (D1) and mean quality score over the trials"},
    "validity_audit": ("Not a rubric item: the grader also flags trials whose action log shows access to the hidden tests / "
                       "reference solution or the upstream fix, or tampering with tests. Such trials are marked invalid in the "
                       "report; their pass/fail is unreliable and they should be re-run."),
    "human_review": "Spot-check a sample of judge answers; overrides in results/quality_overrides.json ({\"<run>/<trial>\": {\"<item id>\": {\"level\": ..., \"reviewer\": ..., \"note\": ...}}}).",
}
(X / "evaluation/rubrics/coding_quality.json").write_text(json.dumps(framework, ensure_ascii=False, indent=2) + "\n")

for eid, ids in PICK.items():
    v1 = json.loads((V1 / f"{eid}.json").read_text())
    by = {i["id"]: i for i in v1["rubric_items"]}
    items = []
    for n, old in enumerate(ids, 1):
        i = by[old]
        items.append({"id": f"{eid}-CASE{n}", "name": i["name"], "name_zh": i["name_zh"], "method": "llm_judge",
                      "red_line": False, "question": i["judge_question"], "criteria": i["criteria"], "v1_id": old})
    out = {"format": "v3", "instance_id": eid, "former_id": v1.get("former_id"), "category": v1["category"],
           "task": v1["task"], "framework": "evaluation/rubrics/coding_quality.json",
           "judge_context": v1.get("rubric_config", {}).get("maintainability_notes", ""),
           "case_items": items}
    (X / f"evaluation/rubrics/tasks/{eid}.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print(eid, [f"{i['id']}: {i['name']}" for i in items])
