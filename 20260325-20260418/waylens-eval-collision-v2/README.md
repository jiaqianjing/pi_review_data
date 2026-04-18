# Waylens Eval Collision Dataset v2

## Overview

Evaluation split for collision detection benchmarking.

- Total samples: 5050
- Positive: 50
- Negative: 5000
- Positive strata: `Label L2 + Label L3`
- Negative strata: `Label L2`
- Seed: `v2`
- Source rows: 5370
- Excluded rows: 9 (`Indeterminate Collision Detection`)

## Video Spec

- Format: `.mp4`
- FPS: `15`
- Duration: `~10s`
- Trigger: event-centered clip, usually ~5s before and after the trigger
- Local filename: `{env}-{clipid}-{sn}.mp4`

## Metadata Schema

- `Clip ID`: unique clip identifier
- `Camera SN`: camera serial number
- `Env`: storage environment (`api` -> `us-east-1`, `gpst` -> `us-east-2`)
- `Region`: S3 region used for download
- `S3 URL`: source mp4 object
- `Label L1`: top-level class
- `Label L2` / `Label L3` / `Label L4`: scenario tags

## Positive Distribution

| L2 | L3 | Count |
|----|----|-------|
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

## Negative Distribution

| L2 | Count |
|----|-------|
| Turning Segment | 1871 |
| No Anomaly | 1736 |
| Rough Road Segment | 753 |
| Dirty Data | 430 |
| Near Miss | 126 |
| Severe Lighting Variation | 84 |

## Sampling Rules

1. Ignore `Indeterminate Collision Detection` rows.
2. Sample exactly 50 positives and 5000 negatives.
3. Positives: 11 `L2+L3` strata, each stratum gets at least 1 sample, remaining slots are allocated proportionally.
4. Rare positive strata are guaranteed coverage, including fully retaining singletons such as `Animal Strike Collision`.
5. Negatives: 6 `L2` strata, each stratum gets at least 1 sample, remaining slots are allocated proportionally.
6. Sampling is deterministic and reproducible from seed `v2`.

## Notes

- `Dirty Data`, `Near Miss`, and `Severe Lighting Variation` are retained as hard negatives.
- This split is intended for model evaluation quality first, not for class balancing during training.
