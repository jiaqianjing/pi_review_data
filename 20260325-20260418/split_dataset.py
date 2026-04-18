"""Dataset splitter for collision detection eval/train sets.

CALLING SPEC:
    python split_dataset.py
    Reads:  reviewed_clips_2026-04-18.csv
    Writes: waylens-eval-collision-v2.csv, waylens-train-collision.csv
    Seed:   "v2" (deterministic)
"""

import csv
import hashlib
import math
import random
from collections import defaultdict
from pathlib import Path

SEED = int(hashlib.md5(b"v2").hexdigest(), 16) % (2**32)
INPUT_FILE = Path(__file__).parent / "reviewed_clips_2026-04-18.csv"
EVAL_POSITIVE = 50
EVAL_NEGATIVE = 5000


def load_rows(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def stratified_sample(rows, n, group_key_fn):
    """Sample n items from rows with stratified allocation by group_key_fn.

    Each group gets at least 1 sample (coverage guarantee).
    Remaining quota allocated proportionally, with largest-remainder rounding.
    """
    groups = defaultdict(list)
    for r in rows:
        groups[group_key_fn(r)].append(r)

    if len(groups) > n:
        raise ValueError(f"Cannot cover {len(groups)} groups with only {n} samples")

    # Step 1: allocate 1 per group
    remaining = n - len(groups)

    # Step 2: proportional allocation of remaining quota
    total = len(rows)
    alloc = {}
    fractional_parts = {}
    for key, members in groups.items():
        exact = remaining * len(members) / total
        alloc[key] = 1 + int(exact)  # 1 base + floor of proportional
        fractional_parts[key] = exact - int(exact)

    # Step 3: largest-remainder method for leftover
    allocated_so_far = sum(alloc.values())
    leftover = n - allocated_so_far
    sorted_keys = sorted(fractional_parts, key=lambda k: -fractional_parts[k])
    for key in sorted_keys[:leftover]:
        alloc[key] += 1

    # Step 4: cap at group size, redistribute overflow to unfilled groups
    overflow = True
    while overflow:
        overflow_count = 0
        for key, members in groups.items():
            if alloc[key] > len(members):
                overflow_count += alloc[key] - len(members)
                alloc[key] = len(members)
        if overflow_count == 0:
            overflow = False
        else:
            # Distribute overflow to groups that still have headroom
            unfilled = [k for k in groups if alloc[k] < len(groups[k])]
            unfilled.sort(key=lambda k: len(groups[k]) - alloc[k], reverse=True)
            for k in unfilled:
                if overflow_count <= 0:
                    break
                headroom = len(groups[k]) - alloc[k]
                give = min(headroom, overflow_count)
                alloc[k] += give
                overflow_count -= give

    # Step 5: sample from each group
    rng = random.Random(SEED)
    sampled = []
    for key, members in groups.items():
        sampled.extend(rng.sample(members, alloc[key]))

    return sampled


def positive_group_key(r):
    return (r["Label L2"], r["Label L3"])


def negative_group_key(r):
    return r["Label L2"]


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    rows = load_rows(INPUT_FILE)
    fieldnames = list(rows[0].keys())

    # Partition by L1
    positive = [r for r in rows if r["Label L1"] == "Collision Detected"]
    negative = [r for r in rows if r["Label L1"] == "Non-Collision Detected"]
    # Indeterminate rows are excluded

    print(f"Total rows: {len(rows)}")
    print(f"Collision Detected: {len(positive)}")
    print(f"Non-Collision Detected: {len(negative)}")
    print(f"Indeterminate (excluded): {len(rows) - len(positive) - len(negative)}")
    print()

    # Stratified sampling
    eval_pos = stratified_sample(positive, EVAL_POSITIVE, positive_group_key)
    eval_neg = stratified_sample(negative, EVAL_NEGATIVE, negative_group_key)

    eval_clip_ids = {r["Clip ID"] for r in eval_pos + eval_neg}

    # Train = everything not in eval, excluding Indeterminate
    train = [r for r in positive + negative if r["Clip ID"] not in eval_clip_ids]

    eval_set = eval_pos + eval_neg
    print(f"Eval set: {len(eval_set)} (positive={len(eval_pos)}, negative={len(eval_neg)})")
    print(f"Train set: {len(train)}")
    print(f"Eval + Train = {len(eval_set) + len(train)}")
    print()

    # Print eval positive distribution
    print("=== Eval positive by L2+L3 ===")
    pos_groups = defaultdict(int)
    for r in eval_pos:
        pos_groups[(r["Label L2"], r["Label L3"])] += 1
    for (l2, l3), c in sorted(pos_groups.items()):
        print(f"  {l2} / {l3}: {c}")

    print()
    print("=== Eval negative by L2 ===")
    neg_groups = defaultdict(int)
    for r in eval_neg:
        neg_groups[r["Label L2"]] += 1
    for l2, c in sorted(neg_groups.items(), key=lambda x: -x[1]):
        print(f"  {l2}: {c}")

    # Write CSVs
    out_dir = Path(__file__).parent
    eval_dir = out_dir / "waylens-eval-collision-v2"
    train_dir = out_dir / "waylens-train-collision-v2"
    eval_dir.mkdir(exist_ok=True)
    train_dir.mkdir(exist_ok=True)
    write_csv(eval_dir / "meta.csv", eval_set, fieldnames)
    write_csv(train_dir / "meta.csv", train, fieldnames)

    print()
    print("Written: waylens-eval-collision-v2/meta.csv")
    print("Written: waylens-train-collision-v2/meta.csv")


if __name__ == "__main__":
    main()
