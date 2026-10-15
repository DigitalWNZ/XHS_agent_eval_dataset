#!/usr/bin/env python3
"""Fill Sheet1 of the XHS evaluation sheet with the C6 (hill climb) / C7 (daily job) cases and the 2026-10-14
campaign results (4 setups x 3 trials). One row per evaluation criterion; case-level cells merged per case."""
import json
import os
import subprocess
import sys
import urllib.request

SHEET_ID = "1YVIUXym1YD59_iirr18VcJRUeJ9K6s5bGYMKr9sAtqU"
XHS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))  # repo root
sys.path[:0] = [f"{XHS}/tools", os.path.dirname(os.path.abspath(__file__))]
import campaign_report as cr  # noqa: E402
import sheet_texts as T  # noqa: E402

TOKEN = subprocess.check_output(["gcloud", "auth", "application-default", "print-access-token"],
                                env={**os.environ, "CLOUDSDK_CONFIG": os.path.expanduser("~/.cache/sheets-gcloud")}, text=True).strip()


def api(method, path, body=None):
    req = urllib.request.Request(f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}{path}", method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json",
                                          "x-goog-user-project": "cloud-llm-preview1"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read() or b"{}")


MODELS = ["claude-opus-5-5", "gemini-3.8-flash-high", "gemini-4-argon-high", "gemini-3.6-flash-high"]  # sheet column order
FW = json.load(open(f"{XHS}/evaluation/rubrics/coding_quality.json"))
SC = {k: v["score"] for k, v in FW["levels"].items()}
CAT = {"C6": "C6 区分度任务（Hill Climb）", "C7": "C7 日常工作任务（Daily Job）", "C9": "C9 客户提供任务（Customer）"}
TAB = "Coding_Detail"
HILL = {"C6": "Y", "C7": "N", "C9": "N"}
DAILY = {"C6": "N", "C7": "Y", "C9": "N"}
AGG = "D1 = 通过次数 / 3\nD2 = 各评分项平均分 × 100（满分 1 / 合格 0.6 / 不合格 0）\nD1、D2 分开报告，不合成总分"
D1_RUBRIC = {
    "tb2_pytest": "隐藏测试全部通过 = 通过；每个模型跑 3 次。",
    "c9_playwright": "隐藏 Playwright 浏览器测试（33 项，通过 window.shopTestAPI 驱动页面）全部通过 = 通过；每个模型跑 3 次。",
    "swebench": "修复目标测试全部通过且原有测试不回归 = 通过；每个模型跑 3 次。",
    "deepswe": "隐藏测试（新功能 + 原有功能）全部通过 = 通过；每个模型跑 3 次。",
}


def crit_text(c):
    k = c["criteria"]
    out = f"perfect（1.0）：{k.get('perfect', '')}\naccept（0.6）：{k.get('accept', '')}\nbad（0）：{k.get('bad', '')}"
    if c.get("caps"):
        out += "\n上限规则：" + " ".join(c["caps"])
    return out


qs = (cr.load("c6", "20261014_103200", "20261015_072400") + cr.load("c7", "20261014_103200", "20261015_072400")
      + cr.load("c9", "20261015_094600", "20261015_120000"))
cell = {}
for q in qs:
    cell.setdefault((q["entry"], q["model"]), []).append(q)
ents = {}
for cat in ("c6", "c7", "c9"):
    for f in sorted(os.listdir(f"{XHS}/dataset/{cat}")):
        if f.endswith(".json"):
            e = json.load(open(f"{XHS}/dataset/{cat}/{f}"))
            e["rub"] = json.load(open(f"{XHS}/{e['task_rubric']}"))
            ents[e["instance_id"]] = e


def item_score(ts, pred):
    xs = [100 * SC[i["level"]] for t in ts if not t["no_code"] for i in t["items"] if pred(i) and SC.get(i["level"]) is not None]
    return f"{sum(xs) / len(xs):.0f}" if xs else "—"


rows, blocks = [], []
for eid in sorted(ents):
    e = ents[eid]
    cat = eid[:2]
    vtype = "c9_playwright" if cat == "C9" else e["verification"]["type"]
    crits = [("D1 任务通过率（隐藏测试）\nTask success", "Machine", D1_RUBRIC[vtype], None)]
    for c in FW["common_items"]:
        crits.append((f"D2 {c['name_zh']}（{c['name']}）", "LLM", T.COMMON_SHORT[c["id"]], c["id"]))
    for c in e["rub"]["case_items"]:
        crits.append((f"D2 用例专项：{c['name_zh']}", "LLM", T.CASE_SHORT[c["id"]], c["id"]))
    start = len(rows)
    for k, (name, method, rubric, iid) in enumerate(crits):
        r = [""] * 19
        if k == 0:
            r[0:7] = [CAT[cat], eid, "N", HILL[cat], DAILY[cat], T.DESC[eid],
                      T.INPUT_SUMMARY.get(eid, e["problem_statement"].strip())]
            r[10] = AGG
        r[7], r[8], r[9] = name, method, rubric
        for j, m in enumerate(MODELS):
            ts = cell.get((eid, m), [])
            if iid is None:
                p = sum(bool(t["verifier_pass"]) for t in ts)
                r[11 + 2 * j] = f"{round(100 * p / len(ts))}% ({p}/{len(ts)})" if ts else "—"
            else:
                r[11 + 2 * j] = item_score(ts, lambda i, iid=iid: i["id"] == iid)
            if k == 0 and ts:
                p = sum(bool(t["verifier_pass"]) for t in ts)
                g = [t["quality_score"] for t in ts if t["quality_score"] is not None]
                r[12 + 2 * j] = f"D1 {round(100 * p / len(ts))}% · D2 {sum(g) / len(g):.0f}" if g else f"D1 {round(100 * p / len(ts))}% · D2 —"
        rows.append(r)
    blocks.append((start, len(rows)))

FIRST = 3  # data starts at row 3 (rows 1-2 are headers)
api("POST", f"/values/{TAB}!A3:S1000:clear", {})
meta = api("GET", "?fields=sheets.properties")
sid = next(s["properties"]["sheetId"] for s in meta["sheets"] if s["properties"]["title"] == TAB)
api("POST", ":batchUpdate", {"requests": [{"unmergeCells": {"range": {"sheetId": sid, "startRowIndex": FIRST - 1, "endRowIndex": 1000,
                                                                      "startColumnIndex": 0, "endColumnIndex": 19}}}]})
api("PUT", f"/values/{TAB}!A{FIRST}:S{FIRST + len(rows) - 1}?valueInputOption=RAW",
    {"range": f"{TAB}!A{FIRST}:S{FIRST + len(rows) - 1}", "majorDimension": "ROWS", "values": rows})
reqs = []
for a, b in blocks:
    for col in (0, 1, 2, 3, 4, 5, 6, 10, 12, 14, 16, 18):
        reqs.append({"mergeCells": {"mergeType": "MERGE_ALL", "range": {"sheetId": sid, "startRowIndex": FIRST - 1 + a,
                     "endRowIndex": FIRST - 1 + b, "startColumnIndex": col, "endColumnIndex": col + 1}}})
reqs.append({"repeatCell": {"range": {"sheetId": sid, "startRowIndex": FIRST - 1, "endRowIndex": FIRST - 1 + len(rows),
             "startColumnIndex": 0, "endColumnIndex": 19},
             "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP", "verticalAlignment": "TOP"}},
             "fields": "userEnteredFormat(wrapStrategy,verticalAlignment)"}})
for a, _ in blocks:  # light border between cases
    reqs.append({"updateBorders": {"range": {"sheetId": sid, "startRowIndex": FIRST - 1 + a, "endRowIndex": FIRST + a,
                 "startColumnIndex": 0, "endColumnIndex": 19}, "top": {"style": "SOLID", "width": 1}}})
api("POST", ":batchUpdate", {"requests": reqs})
print(f"wrote {len(rows)} rows for {len(blocks)} cases (rows {FIRST}-{FIRST + len(rows) - 1})")
