#!/usr/bin/env python3
"""Generate HTML report for waylens-eval-collision-v2 eval set."""
import csv, json, random
from collections import Counter

CSV_PATH = "waylens-eval-collision-v2/meta.csv"
OUT_PATH = "waylens-eval-collision-v2/report.html"

rows = []
with open(CSV_PATH) as f:
    for r in csv.DictReader(f):
        rows.append(r)

def pick_cases(subset, n=2):
    """Pick up to n sample cases, return list of (env, clipid, sn)."""
    random.seed(42)
    samples = random.sample(subset, min(n, len(subset)))
    return [(s["Env"], s["Clip ID"], s["Camera SN"]) for s in samples]

def dist_section(title, key_fn, data):
    """Build one distribution: chart data + sample table."""
    counter = Counter(key_fn(r) for r in data)
    labels = sorted(counter.keys(), key=lambda k: -counter[k])
    values = [counter[k] for k in labels]
    groups = {}
    for r in data:
        k = key_fn(r)
        groups.setdefault(k, []).append(r)
    case_rows = ""
    for lb in labels:
        cases = pick_cases(groups[lb])
        for i, (env, cid, sn) in enumerate(cases):
            span = f' rowspan="{len(cases)}"' if i == 0 else ""
            cat_cell = f"<td{span}>{lb}</td><td{span}>{counter[lb]}</td>" if i == 0 else ""
            case_rows += f"<tr>{cat_cell}<td>{env}</td><td>{cid}</td><td>{sn}</td></tr>\n"
    chart_id = title.replace(" ", "_").replace("/", "_")
    return f"""
<h2>{title}</h2>
<canvas id="{chart_id}" height="120"></canvas>
<script>
new Chart(document.getElementById('{chart_id}'),{{
  type:'bar',
  data:{{labels:{json.dumps(labels)},datasets:[{{label:'Count',data:{json.dumps(values)},backgroundColor:'rgba(54,162,235,0.6)'}}]}},
  options:{{responsive:true,plugins:{{legend:{{display:false}}}},scales:{{y:{{beginAtZero:true}}}}}}
}});
</script>
<table>
<tr><th>Category</th><th>Count</th><th>Env</th><th>Clip ID</th><th>Camera SN</th></tr>
{case_rows}</table>
"""

# Build sections
total = len(rows)
pos = [r for r in rows if r["Label L1"] == "Collision Detected"]
neg = [r for r in rows if r["Label L1"] == "Non-Collision Detected"]

sections = ""
# Overview
sections += f"""
<h2>Overview</h2>
<table><tr><th>Metric</th><th>Value</th></tr>
<tr><td>Total Samples</td><td>{total}</td></tr>
<tr><td>Positive (Collision)</td><td>{len(pos)}</td></tr>
<tr><td>Negative (Non-Collision)</td><td>{len(neg)}</td></tr></table>
"""
# L1
sections += dist_section("Label L1 Distribution", lambda r: r["Label L1"], rows)
# Positive L2+L3
sections += dist_section("Positive: L2 + L3 Sub-types", lambda r: f'{r["Label L2"]} / {r["Label L3"]}' if r["Label L3"] else r["Label L2"], pos)
# Negative L2
sections += dist_section("Negative: L2 Sub-types", lambda r: r["Label L2"], neg)
# Env
sections += dist_section("Env Distribution", lambda r: r["Env"], rows)

html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Eval Set Report - waylens-eval-collision-v2</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body{{font-family:system-ui,sans-serif;max-width:960px;margin:40px auto;padding:0 20px;color:#333}}
h1{{border-bottom:2px solid #2196F3;padding-bottom:8px}}
h2{{color:#1976D2;margin-top:32px}}
table{{border-collapse:collapse;width:100%;margin:12px 0}}
th,td{{border:1px solid #ddd;padding:6px 10px;text-align:left;font-size:13px}}
th{{background:#f5f5f5}}
tr:nth-child(even){{background:#fafafa}}
canvas{{max-width:100%;margin:12px 0}}
</style></head><body>
<h1>📊 waylens-eval-collision-v2 Report</h1>
<p>Generated from <code>{CSV_PATH}</code></p>
{sections}
</body></html>"""

with open(OUT_PATH, "w") as f:
    f.write(html)
print(f"Report saved to {OUT_PATH}")
