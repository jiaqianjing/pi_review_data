"""Build Waylens collision detection eval/train datasets.

CALLING SPEC:
    Inputs:
        - reviewed_clips_2026-04-18.csv
    Outputs:
        - waylens-eval-collision-v2/meta.csv
        - waylens-eval-collision-v2/README.md
        - waylens-eval-collision-v2/videos/
        - waylens-train-collision-v2/meta.csv
        - waylens-train-collision-v2/README.md
        - waylens-train-collision-v2/videos/
    Side effects:
        - Creates output directories
        - Optionally downloads mp4 files from S3 with AWS CLI
    Usage:
        - python split_dataset.py
        - python split_dataset.py --download all --workers 8
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import shutil
import subprocess
from collections import defaultdict
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

SEED_TEXT = "v2"
INPUT_FILE = Path(__file__).parent / "reviewed_clips_2026-04-18.csv"
EVAL_POSITIVE = 50
EVAL_NEGATIVE = 5000
EXCLUDED_LABEL = "Indeterminate Collision Detection"
POSITIVE_LABEL = "Collision Detected"
NEGATIVE_LABEL = "Non-Collision Detected"
EVAL_DIR = Path(__file__).parent / "waylens-eval-collision-v2"
TRAIN_DIR = Path(__file__).parent / "waylens-train-collision-v2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split reviewed clips into Waylens eval/train datasets.",
    )
    parser.add_argument(
        "--download",
        choices=["none", "eval", "train", "all"],
        default="none",
        help="Download dataset videos with AWS CLI after writing metadata.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Concurrent video downloads when --download is enabled.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-download videos even if the local file already exists.",
    )
    return parser.parse_args()


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for index, row in enumerate(rows):
        row["_source_index"] = str(index)
    return rows


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    serializable_rows = [
        {field: row.get(field, "") for field in fieldnames}
        for row in rows
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(serializable_rows)


def stable_int(value: str) -> int:
    return int(hashlib.md5(value.encode("utf-8")).hexdigest(), 16)


def positive_group_key(row: dict[str, str]) -> tuple[str, str]:
    return (row["Label L2"], row["Label L3"])


def negative_group_key(row: dict[str, str]) -> str:
    return row["Label L2"]


def build_groups(
    rows: list[dict[str, str]],
    group_key_fn,
) -> dict[object, list[dict[str, str]]]:
    groups: dict[object, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[group_key_fn(row)].append(row)
    return dict(groups)


def allocate_group_counts(
    groups: dict[object, list[dict[str, str]]],
    target_count: int,
) -> dict[object, int]:
    if not groups:
        raise ValueError("Cannot allocate samples for empty groups")
    if sum(len(rows) for rows in groups.values()) < target_count:
        raise ValueError(f"Requested {target_count} samples, but only {sum(len(rows) for rows in groups.values())} available")
    if len(groups) > target_count:
        raise ValueError(f"Cannot guarantee coverage for {len(groups)} groups with only {target_count} slots")

    allocation = {key: 1 for key in groups}
    remaining = target_count - len(groups)
    total_rows = sum(len(rows) for rows in groups.values())

    remainders: list[tuple[float, int, str, object]] = []
    for key, rows in groups.items():
        exact = remaining * len(rows) / total_rows
        extra = math.floor(exact)
        allocation[key] += extra
        remainders.append(
            (
                exact - extra,
                len(rows),
                str(key),
                key,
            )
        )

    leftover = target_count - sum(allocation.values())
    for _, _, _, key in sorted(remainders, reverse=True)[:leftover]:
        allocation[key] += 1

    overflow = True
    while overflow:
        overflow = False
        surplus = 0
        for key, rows in groups.items():
            if allocation[key] > len(rows):
                surplus += allocation[key] - len(rows)
                allocation[key] = len(rows)
                overflow = True
        if surplus == 0:
            continue
        candidates = sorted(
            (
                (len(groups[key]) - allocation[key], len(groups[key]), str(key), key)
                for key in groups
                if allocation[key] < len(groups[key])
            ),
            reverse=True,
        )
        for _, _, _, key in candidates:
            if surplus == 0:
                break
            allocation[key] += 1
            surplus -= 1
        if surplus:
            raise ValueError(f"Could not redistribute {surplus} overflow samples")

    if sum(allocation.values()) != target_count:
        raise ValueError("Allocation did not reach target sample count")
    return allocation


def sample_rows_from_groups(
    groups: dict[object, list[dict[str, str]]],
    allocation: dict[object, int],
    sample_scope: str,
) -> list[dict[str, str]]:
    sampled: list[dict[str, str]] = []
    for key in sorted(groups, key=str):
        ranked_rows = sorted(
            groups[key],
            key=lambda row: (
                stable_int(
                    f"{SEED_TEXT}|{sample_scope}|{key}|{row['Clip ID']}|{row['Camera SN']}"
                ),
                int(row["_source_index"]),
            ),
        )
        sampled.extend(ranked_rows[: allocation[key]])
    return sampled


def stratified_sample(
    rows: list[dict[str, str]],
    target_count: int,
    group_key_fn,
    sample_scope: str,
) -> tuple[list[dict[str, str]], dict[object, int]]:
    groups = build_groups(rows, group_key_fn)
    allocation = allocate_group_counts(groups, target_count)
    sampled_rows = sample_rows_from_groups(groups, allocation, sample_scope)
    return sort_rows_by_source(sampled_rows), allocation


def sort_rows_by_source(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(rows, key=lambda row: int(row["_source_index"]))


def count_by_label(rows: list[dict[str, str]]) -> tuple[int, int, int]:
    positive = sum(1 for row in rows if row["Label L1"] == POSITIVE_LABEL)
    negative = sum(1 for row in rows if row["Label L1"] == NEGATIVE_LABEL)
    excluded = sum(1 for row in rows if row["Label L1"] == EXCLUDED_LABEL)
    return positive, negative, excluded


def distribution_by_group(
    rows: list[dict[str, str]],
    group_key_fn,
) -> dict[object, int]:
    counts: dict[object, int] = defaultdict(int)
    for row in rows:
        counts[group_key_fn(row)] += 1
    return dict(counts)


def ensure_output_dirs() -> None:
    for path in (
        EVAL_DIR,
        EVAL_DIR / "videos",
        TRAIN_DIR,
        TRAIN_DIR / "videos",
    ):
        path.mkdir(parents=True, exist_ok=True)


def build_video_filename(row: dict[str, str]) -> str:
    return f"{row['Env']}-{row['Clip ID']}-{row['Camera SN']}.mp4"


def dataset_rows_for_download(
    download_mode: str,
    eval_rows: list[dict[str, str]],
    train_rows: list[dict[str, str]],
) -> list[tuple[str, list[dict[str, str]], Path]]:
    targets: list[tuple[str, list[dict[str, str]], Path]] = []
    if download_mode in {"eval", "all"}:
        targets.append(("eval", eval_rows, EVAL_DIR / "videos"))
    if download_mode in {"train", "all"}:
        targets.append(("train", train_rows, TRAIN_DIR / "videos"))
    return targets


def download_one_video(
    row: dict[str, str],
    output_dir: Path,
    overwrite: bool,
) -> tuple[str, str]:
    output_path = output_dir / build_video_filename(row)
    if output_path.exists() and output_path.stat().st_size > 0 and not overwrite:
        return "skipped", output_path.name

    command = [
        "aws",
        "s3",
        "cp",
        row["S3 URL"],
        str(output_path),
        "--region",
        row["Region"],
        "--only-show-errors",
    ]
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        error = result.stderr.strip() or result.stdout.strip() or "unknown aws s3 cp error"
        return "failed", f"{output_path.name}: {error}"
    return "downloaded", output_path.name


def download_videos(
    dataset_name: str,
    rows: list[dict[str, str]],
    output_dir: Path,
    workers: int,
    overwrite: bool,
) -> None:
    if not rows:
        print(f"{dataset_name}: no rows to download")
        return
    if shutil.which("aws") is None:
        raise RuntimeError("AWS CLI is required for --download, but `aws` was not found in PATH")
    if workers < 1:
        raise ValueError("--workers must be >= 1")

    print(f"{dataset_name}: downloading {len(rows)} videos into {output_dir}")
    downloaded = 0
    skipped = 0
    failures: list[str] = []

    def submit_chunk(executor: ThreadPoolExecutor, row_batch: list[dict[str, str]]):
        return {
            executor.submit(download_one_video, row, output_dir, overwrite): row
            for row in row_batch
        }

    rows_by_source = sort_rows_by_source(rows)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        in_flight = submit_chunk(executor, rows_by_source[:workers])
        next_index = workers
        while in_flight:
            done, _ = wait(in_flight, return_when=FIRST_COMPLETED)
            for future in done:
                status, message = future.result()
                in_flight.pop(future, None)
                if status == "downloaded":
                    downloaded += 1
                elif status == "skipped":
                    skipped += 1
                else:
                    failures.append(message)
                processed = downloaded + skipped + len(failures)
                if processed % 50 == 0 or processed == len(rows_by_source):
                    print(
                        f"{dataset_name}: processed {processed}/{len(rows_by_source)} "
                        f"(downloaded={downloaded}, skipped={skipped}, failed={len(failures)})"
                    )
                if next_index < len(rows_by_source):
                    row = rows_by_source[next_index]
                    in_flight[executor.submit(download_one_video, row, output_dir, overwrite)] = row
                    next_index += 1

    if failures:
        raise RuntimeError(
            f"{dataset_name}: {len(failures)} downloads failed. "
            f"First failures: {failures[:5]}"
        )
    print(f"{dataset_name}: completed (downloaded={downloaded}, skipped={skipped})")


def verify_split_counts(
    eval_rows: list[dict[str, str]],
    train_rows: list[dict[str, str]],
    positive_rows: list[dict[str, str]],
    negative_rows: list[dict[str, str]],
) -> None:
    eval_positive, eval_negative, _ = count_by_label(eval_rows)
    train_positive, train_negative, train_excluded = count_by_label(train_rows)
    if eval_positive != EVAL_POSITIVE:
        raise ValueError(f"Eval positive count mismatch: expected {EVAL_POSITIVE}, got {eval_positive}")
    if eval_negative != EVAL_NEGATIVE:
        raise ValueError(f"Eval negative count mismatch: expected {EVAL_NEGATIVE}, got {eval_negative}")
    if train_excluded != 0:
        raise ValueError("Train set unexpectedly contains excluded rows")

    original_clip_ids = {row["Clip ID"] for row in positive_rows + negative_rows}
    split_clip_ids = {row["Clip ID"] for row in eval_rows + train_rows}
    if split_clip_ids != original_clip_ids:
        missing = original_clip_ids - split_clip_ids
        extra = split_clip_ids - original_clip_ids
        raise ValueError(f"Split clip ids mismatch. Missing={len(missing)}, extra={len(extra)}")
    if len(split_clip_ids) != len(eval_rows) + len(train_rows):
        raise ValueError("Eval/train clip ids overlap")
    print(
        f"Verified split counts: eval={len(eval_rows)} "
        f"(positive={eval_positive}, negative={eval_negative}), "
        f"train={len(train_rows)} (positive={train_positive}, negative={train_negative})"
    )


def format_positive_distribution(rows: list[dict[str, str]]) -> list[str]:
    distribution = distribution_by_group(rows, positive_group_key)
    lines = ["| L2 | L3 | Count |", "|----|----|-------|"]
    for (l2, l3), count in sorted(distribution.items()):
        lines.append(f"| {l2} | {l3} | {count} |")
    return lines


def format_negative_distribution(rows: list[dict[str, str]]) -> list[str]:
    distribution = distribution_by_group(rows, negative_group_key)
    lines = ["| L2 | Count |", "|----|-------|"]
    for l2, count in sorted(distribution.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| {l2} | {count} |")
    return lines


def build_eval_readme(source_rows: list[dict[str, str]], eval_rows: list[dict[str, str]]) -> str:
    total_rows = len(source_rows)
    _, _, excluded = count_by_label(source_rows)
    positive_count, negative_count, _ = count_by_label(eval_rows)
    content = [
        "# Waylens Eval Collision Dataset v2",
        "",
        "## Overview",
        "",
        "Evaluation split for collision detection benchmarking.",
        "",
        f"- Total samples: {len(eval_rows)}",
        f"- Positive: {positive_count}",
        f"- Negative: {negative_count}",
        "- Positive strata: `Label L2 + Label L3`",
        "- Negative strata: `Label L2`",
        f"- Seed: `{SEED_TEXT}`",
        f"- Source rows: {total_rows}",
        f"- Excluded rows: {excluded} (`{EXCLUDED_LABEL}`)",
        "",
        "## Video Spec",
        "",
        "- Format: `.mp4`",
        "- FPS: `15`",
        "- Duration: `~10s`",
        "- Trigger: event-centered clip, usually ~5s before and after the trigger",
        "- Local filename: `{env}-{clipid}-{sn}.mp4`",
        "",
        "## Metadata Schema",
        "",
        "- `Clip ID`: unique clip identifier",
        "- `Camera SN`: camera serial number",
        "- `Env`: storage environment (`api` -> `us-east-1`, `gpst` -> `us-east-2`)",
        "- `Region`: S3 region used for download",
        "- `S3 URL`: source mp4 object",
        "- `Label L1`: top-level class",
        "- `Label L2` / `Label L3` / `Label L4`: scenario tags",
        "",
        "## Positive Distribution",
        "",
        *format_positive_distribution(
            [row for row in eval_rows if row["Label L1"] == POSITIVE_LABEL]
        ),
        "",
        "## Negative Distribution",
        "",
        *format_negative_distribution(
            [row for row in eval_rows if row["Label L1"] == NEGATIVE_LABEL]
        ),
        "",
        "## Sampling Rules",
        "",
        "1. Ignore `Indeterminate Collision Detection` rows.",
        "2. Sample exactly 50 positives and 5000 negatives.",
        "3. Positives: 11 `L2+L3` strata, each stratum gets at least 1 sample, remaining slots are allocated proportionally.",
        "4. Rare positive strata are guaranteed coverage, including fully retaining singletons such as `Animal Strike Collision`.",
        "5. Negatives: 6 `L2` strata, each stratum gets at least 1 sample, remaining slots are allocated proportionally.",
        "6. Sampling is deterministic and reproducible from seed `v2`.",
        "",
        "## Notes",
        "",
        "- `Dirty Data`, `Near Miss`, and `Severe Lighting Variation` are retained as hard negatives.",
        "- This split is intended for model evaluation quality first, not for class balancing during training.",
    ]
    return "\n".join(content) + "\n"


def build_train_readme(source_rows: list[dict[str, str]], train_rows: list[dict[str, str]]) -> str:
    _, _, excluded = count_by_label(source_rows)
    positive_count, negative_count, _ = count_by_label(train_rows)
    content = [
        "# Waylens Train Collision Dataset v2",
        "",
        "## Overview",
        "",
        "Residual training split after removing the eval set from reviewed clips.",
        "",
        f"- Total samples: {len(train_rows)}",
        f"- Positive: {positive_count}",
        f"- Negative: {negative_count}",
        f"- Excluded rows: {excluded} (`{EXCLUDED_LABEL}`)",
        "- Role: incremental supplement to an existing collision training pool",
        "",
        "## Video Spec",
        "",
        "- Format: `.mp4`",
        "- FPS: `15`",
        "- Duration: `~10s`",
        "- Trigger: event-centered clip, usually ~5s before and after the trigger",
        "- Local filename: `{env}-{clipid}-{sn}.mp4`",
        "",
        "## Positive Distribution",
        "",
        *format_positive_distribution(
            [row for row in train_rows if row["Label L1"] == POSITIVE_LABEL]
        ),
        "",
        "## Negative Distribution",
        "",
        *format_negative_distribution(
            [row for row in train_rows if row["Label L1"] == NEGATIVE_LABEL]
        ),
        "",
        "## Notes",
        "",
        "- All non-excluded rows not selected into eval are assigned to train.",
        "- Negative count is intentionally small because eval consumes almost all reviewed negatives in this batch.",
        "- `Indeterminate Collision Detection` is excluded from both splits.",
    ]
    return "\n".join(content) + "\n"


def write_readmes(source_rows: list[dict[str, str]], eval_rows: list[dict[str, str]], train_rows: list[dict[str, str]]) -> None:
    (EVAL_DIR / "README.md").write_text(
        build_eval_readme(source_rows, eval_rows),
        encoding="utf-8",
    )
    (TRAIN_DIR / "README.md").write_text(
        build_train_readme(source_rows, train_rows),
        encoding="utf-8",
    )


def build_splits(
    source_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    filtered_rows = [
        row
        for row in source_rows
        if row["Label L1"] in {POSITIVE_LABEL, NEGATIVE_LABEL}
    ]
    positive_rows = [row for row in filtered_rows if row["Label L1"] == POSITIVE_LABEL]
    negative_rows = [row for row in filtered_rows if row["Label L1"] == NEGATIVE_LABEL]

    eval_positive_rows, _ = stratified_sample(
        positive_rows,
        EVAL_POSITIVE,
        positive_group_key,
        sample_scope="eval-positive",
    )
    eval_negative_rows, _ = stratified_sample(
        negative_rows,
        EVAL_NEGATIVE,
        negative_group_key,
        sample_scope="eval-negative",
    )

    eval_clip_ids = {row["Clip ID"] for row in eval_positive_rows + eval_negative_rows}
    train_rows = sort_rows_by_source(
        [row for row in filtered_rows if row["Clip ID"] not in eval_clip_ids]
    )
    eval_rows = sort_rows_by_source(eval_positive_rows + eval_negative_rows)

    verify_split_counts(eval_rows, train_rows, positive_rows, negative_rows)
    return eval_rows, train_rows


def print_split_summary(source_rows: list[dict[str, str]], eval_rows: list[dict[str, str]], train_rows: list[dict[str, str]]) -> None:
    source_positive, source_negative, source_excluded = count_by_label(source_rows)
    eval_positive, eval_negative, _ = count_by_label(eval_rows)
    train_positive, train_negative, _ = count_by_label(train_rows)
    print(f"Source rows: {len(source_rows)}")
    print(f"  {POSITIVE_LABEL}: {source_positive}")
    print(f"  {NEGATIVE_LABEL}: {source_negative}")
    print(f"  {EXCLUDED_LABEL}: {source_excluded}")
    print()
    print(f"Eval rows: {len(eval_rows)}")
    print(f"  positives: {eval_positive}")
    print(f"  negatives: {eval_negative}")
    print(f"Train rows: {len(train_rows)}")
    print(f"  positives: {train_positive}")
    print(f"  negatives: {train_negative}")


def main() -> None:
    args = parse_args()
    ensure_output_dirs()
    source_rows = load_rows(INPUT_FILE)
    fieldnames = [field for field in source_rows[0].keys() if not field.startswith("_")]

    eval_rows, train_rows = build_splits(source_rows)
    write_csv(EVAL_DIR / "meta.csv", eval_rows, fieldnames)
    write_csv(TRAIN_DIR / "meta.csv", train_rows, fieldnames)
    write_readmes(source_rows, eval_rows, train_rows)
    print_split_summary(source_rows, eval_rows, train_rows)

    for dataset_name, rows, output_dir in dataset_rows_for_download(
        args.download,
        eval_rows,
        train_rows,
    ):
        download_videos(dataset_name, rows, output_dir, args.workers, args.overwrite)


if __name__ == "__main__":
    main()
