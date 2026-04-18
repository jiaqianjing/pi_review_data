# Waylens Train Collision Dataset

## Overview

Incremental training data for collision detection model. Contains samples remaining after eval set extraction.

- **File**: `waylens-train-collision.csv`
- **Total samples**: 311
- **Positive (Collision Detected)**: 310
- **Negative (Non-Collision Detected)**: 1
- **Source**: `reviewed_clips_2026-04-18.csv` — residual after eval set (`waylens-eval-collision-v2.csv`) extraction
- **Note**: This is an incremental supplement to existing training data; the small negative count is expected

## Video Specification

| Property | Value |
|----------|-------|
| Format | .mp4 |
| FPS | 15 |
| Duration | ~10s |
| Trigger | G-force event (captures ~5s before and after) |
| Storage | AWS S3 (us-east-1 for `api`, us-east-2 for `gpst`) |

## CSV Fields

Same schema as `waylens-eval-collision-v2.csv`. See that file's documentation for field details.

## Label Distribution

### Positive Samples (310) — by L2+L3

| L2 | L3 | Count |
|----|-----|-------|
| Collision - Accident | Head-On Collision | 16 |
| Collision - Accident | Other Collision Accident | 107 |
| Collision - Accident | Rear-End Collision | 63 |
| Collision - Accident | Severe Road Surface Variation | 22 |
| Collision - Accident | Side-Impact Collision | 40 |
| Collision - Accident | Vehicle Rollover | 8 |
| Collision - Accident | Vertical Curb Strike Collision | 1 |
| Collision - Non-Accident | Non-Accident Reverse (Docking/Coupling) | 25 |
| Collision - Non-Accident | Operational Collision (Snow Plowing/Earthwork) | 7 |
| Collision - Non-Accident | Other Non-Accident Scenario | 21 |

### Negative Samples (1) — by L2

| L2 | Count |
|----|-------|
| No Anomaly | 1 |

## Notes

- 2 rare positive sub-types are absent here because all samples went to eval: `Animal Strike Collision` (1 total), `Operational Collision` fully covered
- Negative samples are minimal (1) — this train set is intended as an incremental addition to a larger existing training pool
- `Indeterminate Collision Detection` (9 rows) excluded from both eval and train
