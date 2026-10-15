#!/usr/bin/env python3
"""Fill Coding_Summary_Internal: one row per C6 / C7 case + a group-average row after each category.
Per model: D1 (pass rate), D2 (mean quality), avg duration (min), avg number of turns (agent tool calls), avg tokens (K).
Data: 2026-10-14 campaign (4 setups x 3 trials), 2026-10-15 layout."""
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request

SHEET_ID = "1YVIUXym1YD59_iirr18VcJRUeJ9K6s5bGYMKr9sAtqU"
TAB = "Coding_Summary_Internal"
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


MODELS = ["claude-opus-5-5", "gemini-3.8-flash-high", "gemini-4-argon-high", "gemini-3.6-flash-high"]  # sheet order
CAT = {"C6": "C6 区分度任务（Hill Climb）", "C7": "C7 日常工作任务（Daily Job）", "C9": "C9 客户提供任务（Customer）"}
HILL = {"C6": "Y", "C7": "N", "C9": "N"}
DAILY = {"C6": "N", "C7": "Y", "C9": "N"}


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


qs = (cr.load("c6", "20261014_103200", "20261015_072400") + cr.load("c7", "20261014_103200", "20261015_072400")
      + cr.load("c9", "20261015_094600", "20261015_120000"))
cell = {}
for q in qs:
    cell.setdefault((q["entry"], q["model"]), []).append(q)
ids = sorted({q["entry"] for q in qs})


def metrics(ts):
    if not ts:
        return [None] * 5
    d1 = sum(bool(t["verifier_pass"]) for t in ts) / len(ts)
    d2 = mean([t["quality_score"] for t in ts])
    dur = mean([t["elapsed"] / 60 if t["elapsed"] else None for t in ts])
    turns = mean([t["tool_calls"] for t in ts])
    tok = mean([t["tokens"] / 1000 if t["tokens"] else None for t in ts])
    return [d1, d2, dur, turns, tok]


def fmt(vals):
    d1, d2, dur, turns, tok = vals
    return [("" if d1 is None else round(d1, 4)), ("—" if d2 is None else round(d2, 1)), ("—" if dur is None else round(dur, 1)),
            ("—" if turns is None else round(turns, 1)), ("—" if tok is None else round(tok))]


rows, avg_rows = [], []
for cat in ("C6", "C7", "C9"):
    per_case = {}
    for eid in [i for i in ids if i.startswith(cat)]:
        r = [CAT[cat], eid, "N", HILL[cat], DAILY[cat], T.DESC[eid]]
        for m in MODELS:
            v = metrics(cell.get((eid, m), []))
            per_case.setdefault(m, []).append(v)
            r += fmt(v)
        rows.append(r)
    r = [CAT[cat], f"{cat} 组平均（{len(per_case[MODELS[0]])} 个用例）", "", "", "", "各用例数值的平均（宏平均）"]
    for m in MODELS:
        r += fmt([mean([v[k] for v in per_case[m]]) for k in range(5)])
    avg_rows.append(len(rows))
    rows.append(r)
note_row = len(rows) + 1
rows.append([])
rows.append(["说明", "数据：C6 / C7 为 2026-10-14 评测，C9 为 2026-10-15 评测（每个模型每个用例 3 次独立试验，隔离环境）；用例编号为 2026-10-15 新分组。"
             "D1 = 通过率（隐藏测试全部通过的试验数 / 3）；D2 = 代码质量分（LLM 评审，0–100，无代码改动的试验不计入）；"
             "Avg Duration = 平均智能体运行时长（分钟，受时间上限约束）；Avg Num of Turns = 平均工具调用次数（Antigravity CLI 每次会话只报 1 轮，"
             "故统一用工具调用次数衡量）；Avg Token = 平均输入 + 输出 token（千）。— 表示无数据（如 2026-10-14 早期超时的 Gemini 试验未保存轨迹）。"])

FIRST = 3
meta = api("GET", "?fields=sheets.properties")
sid = next(s["properties"]["sheetId"] for s in meta["sheets"] if s["properties"]["title"] == TAB)
rng = urllib.parse.quote(f"{TAB}!A3:Z200")
api("POST", f"/values/{rng}:clear", {})
api("POST", ":batchUpdate", {"requests": [{"unmergeCells": {"range": {"sheetId": sid, "startRowIndex": FIRST - 1, "endRowIndex": 200,
                                                                      "startColumnIndex": 0, "endColumnIndex": 26}}}]})
end = FIRST + len(rows) - 1
api("PUT", f"/values/{urllib.parse.quote(f'{TAB}!A{FIRST}:Z{end}')}?valueInputOption=RAW",
    {"range": f"{TAB}!A{FIRST}:Z{end}", "majorDimension": "ROWS", "values": rows})
fmt_req = []
data_end = FIRST - 1 + avg_rows[-1] + 1
for j in range(4):  # per model: D1 percent, D2 / duration / turns 1 decimal, tokens integer
    base = 6 + 5 * j
    for off, pattern in ((0, "0%"), (1, "0.0"), (2, "0.0"), (3, "0.0"), (4, "#,##0")):
        fmt_req.append({"repeatCell": {"range": {"sheetId": sid, "startRowIndex": FIRST - 1, "endRowIndex": data_end,
                        "startColumnIndex": base + off, "endColumnIndex": base + off + 1},
                        "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": pattern}, "horizontalAlignment": "RIGHT"}},
                        "fields": "userEnteredFormat(numberFormat,horizontalAlignment)"}})
fmt_req.append({"repeatCell": {"range": {"sheetId": sid, "startRowIndex": FIRST - 1, "endRowIndex": data_end, "startColumnIndex": 0, "endColumnIndex": 6},
                "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP", "verticalAlignment": "TOP"}}, "fields": "userEnteredFormat(wrapStrategy,verticalAlignment)"}})
for a in avg_rows:  # bold + shaded group-average rows
    fmt_req.append({"repeatCell": {"range": {"sheetId": sid, "startRowIndex": FIRST - 1 + a, "endRowIndex": FIRST + a, "startColumnIndex": 0, "endColumnIndex": 26},
                    "cell": {"userEnteredFormat": {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.93, "green": 0.94, "blue": 1.0}}},
                    "fields": "userEnteredFormat(textFormat,backgroundColor)"}})
nr = FIRST - 1 + note_row
fmt_req.append({"mergeCells": {"mergeType": "MERGE_ALL", "range": {"sheetId": sid, "startRowIndex": nr, "endRowIndex": nr + 1, "startColumnIndex": 1, "endColumnIndex": 26}}})
fmt_req.append({"repeatCell": {"range": {"sheetId": sid, "startRowIndex": nr, "endRowIndex": nr + 1, "startColumnIndex": 0, "endColumnIndex": 26},
                "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP", "verticalAlignment": "TOP", "textFormat": {"italic": True}}},
                "fields": "userEnteredFormat(wrapStrategy,verticalAlignment,textFormat)"}})
api("POST", ":batchUpdate", {"requests": fmt_req})
print(f"wrote {len(rows)} rows to {TAB} (rows {FIRST}-{end}); average rows at {[FIRST + a for a in avg_rows]}")
