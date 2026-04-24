# Waylens Train Collision Dataset v3

## Overview

Training split from reviewed clips (2026-04-20 batch).

- Total samples: 704
- Collision Detected (Positive): 5
- Non-Collision Detected (Negative): 699
- Excluded rows: 4 (`Indeterminate Collision Detection`)
- Source environments: api, gpst

## Video Spec

- Format: `.mp4`
- FPS: `15`
- Duration: `~10s–16s`
- Trigger: event-centered clip, usually ~5s before and after the trigger
- Local filename: `{env}-{sn}-{clipid}.mp4`

## Positive Distribution (Collision Detected)

| L2 | Count |
|----|-------|
| Collision - Accident | 3 |
| Collision - Non-Accident | 2 |

## Negative Distribution (Non-Collision Detected)

| L2 | Count |
|----|-------|
| No Anomaly | 346 |
| Turning Segment | 237 |
| Dirty Data | 60 |
| Rough Road Segment | 30 |
| Near Miss | 24 |
| Severe Lighting Variation | 2 |

## Notes

- `Indeterminate Collision Detection` rows are excluded from this dataset.
- Data sourced from api and gpst environments (pi, fcw, severe brake events).
- api environment → AWS region: us-east-1; gpst environment → AWS region: us-east-2.
