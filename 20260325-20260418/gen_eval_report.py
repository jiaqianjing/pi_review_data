#!/usr/bin/env python3
"""Generate HTML report for eval/train sets (inline SVG, no JS)."""
import csv, random, sys
from collections import Counter

COLORS = ["#4285F4","#EA4335","#FBBC04","#34A853","#FF6D01","#46BDC6","#7B61FF","#F538A0","#00ACC1","#8D6E63","#78909C","#AB47BC"]

def pick_cases(subset, n=2):
    random.seed(42)
    return [(s["Env"], s["Clip ID"], s["Camera SN"]) for s in random.sample(subset, min(n, len(subset)))]

def svg_bar_chart(labels, values, width=800, bar_h=28, gap=6):
    max_val = max(values) if values else 1
    label_w, chart_w = 280, width - 340
    h = len(labels) * (bar_h + gap) + 20
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}" style="font-family:system-ui,sans-serif;font-size:12px">']
    for i, (lb, val) in enumerate(zip(labels, values)):
        y = i * (bar_h + gap) + 10
        bw = max(int(val / max_val * chart_w), 2)
        c = COLORS[i % len(COLORS)]
        lines.append(f'<text x="{label_w-8}" y="{y+bar_h*0.7}" text-anchor="end" fill="#333">{lb}</text>')
        lines.append(f'<rect x="{label_w}" y="{y}" width="{bw}" height="{bar_h}" rx="3" fill="{c}" opacity="0.8"/>')
        lines.append(f'<text x="{label_w+bw+6}" y="{y+bar_h*0.7}" fill="#555">{val}</text>')
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
    return f"<h2>{title}</h2>\n{svg_bar_chart(labels, values)}\n<table>\n<tr><th>Category</th><th>Count</th><th>Env</th><th>Clip ID</th><th>Camera SN</th></tr>\n{case_rows}</table>\n"

def generate(csv_path, out_path, dataset_name):
    rows = []
    with open(csv_path, newline='') as f:
        for r in csv.DictReader(f):
            rows.append({k.strip(): v.strip() for k, v in r.items()})
    pos = [r for r in rows if r["Label L1"] == "Collision Detected"]
    neg = [r for r in rows if r["Label L1"] == "Non-Collision Detected"]
    s = f"""<h2>Overview</h2>
<table><tr><th>Metric</th><th>Value</th></tr>
<tr><td>Total</td><td>{len(rows)}</td></tr>
<tr><td>Positive (Collision)</td><td>{len(pos)}</td></tr>
<tr><td>Negative (Non-Collision)</td><td>{len(neg)}</td></tr></table>\n"""
    s += dist_section("Label L1 Distribution", lambda r: r["Label L1"], rows)
    if pos:
        s += dist_section("Positive: L2 + L3 Sub-types", lambda r: f'{r["Label L2"]} / {r["Label L3"]}' if r.get("Label L3") else r["Label L2"], pos)
    if neg:
        s += dist_section("Negative: L2 Sub-types", lambda r: r["Label L2"], neg)
    s += dist_section("Env Distribution", lambda r: r["Env"], rows)
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{dataset_name} Report</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:960px;margin:40px auto;padding:0 20px;color:#333}}
h1{{border-bottom:2px solid #2196F3;padding-bottom:8px}}
h2{{color:#1976D2;margin-top:32px}}
table{{border-collapse:collapse;width:100%;margin:12px 0}}
th,td{{border:1px solid #ddd;padding:6px 10px;text-align:left;font-size:13px}}
th{{background:#f5f5f5}}
tr:nth-child(even){{background:#fafafa}}
</style></head><body>
<h1>📊 {dataset_name} Report</h1>
<p>Generated from <code>{csv_path}</code></p>
{s}
</body></html>"""
    with open(out_path, "w") as f:
        f.write(html)
    print(f"Report saved to {out_path}")

generate("waylens-eval-collision-v2/meta.csv", "waylens-eval-collision-v2/report.html", "waylens-eval-collision-v2")
generate("waylens-train-collision-v2/meta.csv", "waylens-train-collision-v2/report.html", "waylens-train-collision-v2")
