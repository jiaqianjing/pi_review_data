#!/usr/bin/env python3
"""Generate HTML report for waylens-eval-collision-v2 eval set (inline SVG, no JS)."""
import csv, random
from collections import Counter

CSV_PATH = "waylens-eval-collision-v2/meta.csv"
OUT_PATH = "waylens-eval-collision-v2/report.html"

rows = []
with open(CSV_PATH) as f:
    for r in csv.DictReader(f):
        rows.append(r)

def pick_cases(subset, n=2):
    random.seed(42)
    samples = random.sample(subset, min(n, len(subset)))
    return [(s["Env"], s["Clip ID"], s["Camera SN"]) for s in samples]

COLORS = ["#4285F4","#EA4335","#FBBC04","#34A853","#FF6D01","#46BDC6","#7B61FF","#F538A0","#00ACC1","#8D6E63","#78909C","#AB47BC"]

def svg_bar_chart(labels, values, width=800, bar_h=28, gap=6):
    max_val = max(values) if values else 1
    n = len(labels)
    label_w = 280
    chart_w = width - label_w - 60
    h = n * (bar_h + gap) + 20
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}" style="font-family:system-ui,sans-serif;font-size:12px">']
    for i, (lb, val) in enumerate(zip(labels, values)):
        y = i * (bar_h + gap) + 10
        bw = max(int(val / max_val * chart_w), 2)
        color = COLORS[i % len(COLORS)]
        lines.append(f'<text x="{label_w - 8}" y="{y + bar_h * 0.7}" text-anchor="end" fill="#333">{lb}</text>')
        lines.append(f'<rect x="{label_w}" y="{y}" width="{bw}" height="{bar_h}" rx="3" fill="{color}" opacity="0.8"/>')
        lines.append(f'<text x="{label_w + bw + 6}" y="{y + bar_h * 0.7}" fill="#555">{val}</text>')
    lines.append('</svg>')
    return '\n'.join(lines)

def dist_section(title, key_fn, data):
    counter = Counter(key_fn(r) for r in data)
    labels = sorted(counter.keys(), key=lambda k: -counter[k])
    values = [counter[k] for k in labels]
    groups = {}
    for r in data:
        groups.setdefault(key_fn(r), []).append(r)
    case_rows = ""
    for lb in labels:
        cases = pick_cases(groups[lb])
        for i, (env, cid, sn) in enumerate(cases):
            span = f' rowspan="{len(cases)}"' if i == 0 else ""
            cat_cell = f"<td{span}>{lb}</td><td{span}>{counter[lb]}</td>" if i == 0 else ""
            case_rows += f"<tr>{cat_cell}<td>{env}</td><td>{cid}</td><td>{sn}</td></tr>\n"
    chart = svg_bar_chart(labels, values)
    return f"<h2>{title}</h2>\n{chart}\n<table>\n<tr><th>Category</th><th>Count</th><th>Env</th><th>Clip ID</th><th>Camera SN</th></tr>\n{case_rows}</table>\n"

pos = [r for r in rows if r["Label L1"] == "Collision Detected"]
neg = [r for r in rows if r["Label L1"] == "Non-Collision Detected"]

sections = f"""<h2>Overview</h2>
<table><tr><th>Metric</th><th>Value</th></tr>
<tr><td>Total Samples</td><td>{len(rows)}</td></tr>
<tr><td>Positive (Collision)</td><td>{len(pos)}</td></tr>
<tr><td>Negative (Non-Collision)</td><td>{len(neg)}</td></tr></table>
"""
sections += dist_section("Label L1 Distribution", lambda r: r["Label L1"], rows)
sections += dist_section("Positive: L2 + L3 Sub-types", lambda r: f'{r["Label L2"]} / {r["Label L3"]}' if r["Label L3"] else r["Label L2"], pos)
sections += dist_section("Negative: L2 Sub-types", lambda r: r["Label L2"], neg)
sections += dist_section("Env Distribution", lambda r: r["Env"], rows)

html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Eval Set Report - waylens-eval-collision-v2</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:960px;margin:40px auto;padding:0 20px;color:#333}}
h1{{border-bottom:2px solid #2196F3;padding-bottom:8px}}
h2{{color:#1976D2;margin-top:32px}}
table{{border-collapse:collapse;width:100%;margin:12px 0}}
th,td{{border:1px solid #ddd;padding:6px 10px;text-align:left;font-size:13px}}
th{{background:#f5f5f5}}
tr:nth-child(even){{background:#fafafa}}
</style></head><body>
<h1>📊 waylens-eval-collision-v2 Report</h1>
<p>Generated from <code>{CSV_PATH}</code></p>
{sections}
</body></html>"""

with open(OUT_PATH, "w") as f:
    f.write(html)
print(f"Report saved to {OUT_PATH}")
