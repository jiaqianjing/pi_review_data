# Waylens Eval Collision Dataset v2

## Overview

Evaluation dataset for collision detection model benchmarking. Extracted from human-reviewed dashcam clips via stratified sampling.

- **File**: `meta.csv`
- **Total samples**: 5050
- **Positive (Collision Detected)**: 50
- **Negative (Non-Collision Detected)**: 5000
- **Positive/Negative ratio**: 1:100
- **Seed**: `"v2"` (deterministic, reproducible)
- **Source**: `reviewed_clips_2026-04-18.csv` (5370 clips, 9 Indeterminate excluded)

## Video Specification

| Property | Value |
|----------|-------|
| Format | .mp4 |
| FPS | 15 |
| Duration | ~10s |
| Trigger | G-force event (captures ~5s before and after) |
| Storage | AWS S3 (us-east-1 for `api`, us-east-2 for `gpst`) |

## CSV Fields

| # | Field | Description |
|---|-------|-------------|
| 1 | `#` | Row index |
| 2 | `Clip ID` | Unique clip identifier |
| 3 | `Camera SN` | Camera serial number |
| 4 | `Env` | Environment (`api` → us-east-1, `gpst` → us-east-2) |
| 5 | `Region` | AWS S3 region |
| 6 | `S3 URL` | S3 video URL |
| 7 | `Reviewer` | Human reviewer |
| 8 | `Review Time` | Review timestamp |
| 9 | `Label ID` | Hierarchical label ID (e.g. `event_collision_01_003`) |
| 10 | `Label L1` | Primary label: `Collision Detected` or `Non-Collision Detected` |
| 11 | `Label L2` | Sub-category |
| 12 | `Label L3` | Sub-sub-category (collision only) |
| 13 | `Label L4` | Reserved (currently empty) |

## Label Distribution

### Positive Samples (50) — Stratified by L2+L3

| L2 | L3 | Count |
|----|-----|-------|
| Collision - Accident | Animal Strike Collision | 1 |
| Collision - Accident | Head-On Collision | 3 |
| Collision - Accident | Other Collision Accident | 14 |
| Collision - Accident | Rear-End Collision | 9 |
| Collision - Accident | Severe Road Surface Variation | 4 |
| Collision - Accident | Side-Impact Collision | 6 |
| Collision - Accident | Vehicle Rollover | 2 |
| Collision - Accident | Vertical Curb Strike Collision | 1 |
| Collision - Non-Accident | Non-Accident Reverse (Docking/Coupling) | 4 |
| Collision - Non-Accident | Operational Collision (Snow Plowing/Earthwork) | 2 |
| Collision - Non-Accident | Other Non-Accident Scenario | 4 |

### Negative Samples (5000) — Stratified by L2

| L2 | Count |
|----|-------|
| Turning Segment | 1872 |
| No Anomaly | 1735 |
| Rough Road Segment | 753 |
| Dirty Data | 430 |
| Near Miss | 126 |
| Severe Lighting Variation | 84 |

## Sampling Method

1. Exclude `Indeterminate Collision Detection` (9 rows)
2. Positive: stratified by L2+L3 (11 groups), each group ≥ 1 sample, remaining by proportion
3. Negative: stratified by L2 (6 groups), each group ≥ 1 sample, remaining by proportion
4. Deterministic via seed `"v2"` → `md5("v2") mod 2^32`

## Notes

- Negative samples include `Dirty Data` (430) and `Near Miss` (126) — these are intentionally retained as hard negatives
- All 11 collision sub-types are covered; rare types (Animal Strike=1, Vertical Curb Strike=1) are fully included
- 3 negative L2 groups (`Dirty Data`, `Near Miss`, `Severe Lighting Variation`) are fully included due to small group size
