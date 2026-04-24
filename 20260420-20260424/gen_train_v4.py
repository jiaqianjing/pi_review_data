#!/usr/bin/env python3
"""Generate waylens-train-collision-v4 dataset from reviewed_clips_2026-04-24.csv."""

import csv
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

SRC_CSV = Path(__file__).parent / "reviewed_clips_2026-04-24.csv"
OUT_DIR = Path(__file__).parent / "waylens-train-collision-v4"
VIDEO_DIR = OUT_DIR / "videos"
META_CSV = OUT_DIR / "meta.csv"
README = OUT_DIR / "README.md"

REGION_MAP = {"api": "us-east-1", "gpst": "us-east-2"}
SKIP_LABEL = "Indeterminate Collision Detection"
WORKERS = 32


def download_video(s3_url: str, dest: Path, region: str) -> tuple[bool, str]:
    if dest.exists():
        return True, f"[skip] {dest.name}"
    result = subprocess.run(
        ["aws", "s3", "cp", s3_url, str(dest), "--region", region],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return False, f"[ERROR] {dest.name}: {result.stderr.strip()}"
    return True, f"[ok] {dest.name}"


def main():
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)

    with open(SRC_CSV, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    kept = [r for r in rows if r["Label L1"] != SKIP_LABEL]
    skipped = len(rows) - len(kept)
    print(f"Total: {len(rows)}, kept: {len(kept)}, skipped (indeterminate): {skipped}", flush=True)

    fieldnames = list(rows[0].keys())

    tasks = []
    for row in kept:
        env = row["Env"]
        sn = row["Camera SN"]
        clip_id = row["Clip ID"]
        region = REGION_MAP.get(env, row["Region"])
        s3_url = row["S3 URL"]
        filename = f"{env}-{sn}-{clip_id}.mp4"
        dest = VIDEO_DIR / filename
        tasks.append((row, s3_url, dest, region))

    failed_clips = set()
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {
            pool.submit(download_video, s3_url, dest, region): (row, dest)
            for row, s3_url, dest, region in tasks
        }
        for future in as_completed(futures):
            row, dest = futures[future]
            ok, msg = future.result()
            done += 1
            if done % 100 == 0 or not ok:
                print(f"  [{done}/{len(tasks)}] {msg}", flush=True)
            if not ok:
                failed_clips.add((row["Env"], row["Camera SN"], row["Clip ID"]))

    out_rows = []
    for idx, row in enumerate(kept, 1):
        key = (row["Env"], row["Camera SN"], row["Clip ID"])
        if key in failed_clips:
            continue
        out_row = dict(row)
        out_row["#"] = idx
        out_rows.append(out_row)

    for idx, r in enumerate(out_rows, 1):
        r["#"] = idx

    with open(META_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"\nWrote {len(out_rows)} rows to {META_CSV}", flush=True)
    if failed_clips:
        print(f"Failed downloads: {len(failed_clips)}", flush=True)

    collision = [r for r in out_rows if r["Label L1"] == "Collision Detected"]
    non_collision = [r for r in out_rows if r["Label L1"] == "Non-Collision Detected"]
    c_l2 = Counter(r["Label L2"] for r in collision)
    nc_l2 = Counter(r["Label L2"] for r in non_collision)
    envs = sorted(set(r["Env"] for r in out_rows))

    def l2_table(counter):
        md_rows = "\n".join(f"| {k} | {v} |" for k, v in counter.most_common())
        return f"| L2 | Count |\n|----|-------|\n{md_rows}"

    readme = f"""# Waylens Train Collision Dataset v4

## Overview

Training split from reviewed clips (2026-04-24 batch).

- Total samples: {len(out_rows)}
- Collision Detected (Positive): {len(collision)}
- Non-Collision Detected (Negative): {len(non_collision)}
- Excluded rows: {skipped} (`Indeterminate Collision Detection`)
- Source environments: {", ".join(envs)}

## Video Spec

- Format: `.mp4`
- FPS: `15`
- Duration: `~10s–16s`
- Trigger: event-centered clip, usually ~5s before and after the trigger
- Local filename: `{{env}}-{{sn}}-{{clipid}}.mp4`

## Positive Distribution (Collision Detected)

{l2_table(c_l2)}

## Negative Distribution (Non-Collision Detected)

{l2_table(nc_l2)}

## Notes

- `Indeterminate Collision Detection` rows are excluded from this dataset.
- Data sourced from api and gpst environments (pi, fcw, severe brake events).
- api environment → AWS region: us-east-1; gpst environment → AWS region: us-east-2.
"""
    README.write_text(readme, encoding="utf-8")
    print(f"Wrote {README}", flush=True)


if __name__ == "__main__":
    main()
