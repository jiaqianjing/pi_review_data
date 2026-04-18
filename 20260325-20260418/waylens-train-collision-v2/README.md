# Waylens Train Collision Dataset v2

## Overview

Residual training split after removing the eval set from reviewed clips.

- Total samples: 311
- Positive: 310
- Negative: 1
- Excluded rows: 9 (`Indeterminate Collision Detection`)
- Role: incremental supplement to an existing collision training pool

## Video Spec

- Format: `.mp4`
- FPS: `15`
- Duration: `~10s`
- Trigger: event-centered clip, usually ~5s before and after the trigger
- Local filename: `{env}-{clipid}-{sn}.mp4`

## Positive Distribution

| L2 | L3 | Count |
|----|----|-------|
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

## Negative Distribution

| L2 | Count |
|----|-------|
| Turning Segment | 1 |

## Notes

- All non-excluded rows not selected into eval are assigned to train.
- Negative count is intentionally small because eval consumes almost all reviewed negatives in this batch.
- `Indeterminate Collision Detection` is excluded from both splits.
