# `split_dataset.py`

## Purpose

Build the `waylens-eval-collision-v2` and `waylens-train-collision-v2` datasets from `reviewed_clips_2026-04-18.csv`.

## Inputs

- `reviewed_clips_2026-04-18.csv`

## Outputs

- `waylens-eval-collision-v2/meta.csv`
- `waylens-eval-collision-v2/README.md`
- `waylens-eval-collision-v2/videos/`
- `waylens-train-collision-v2/meta.csv`
- `waylens-train-collision-v2/README.md`
- `waylens-train-collision-v2/videos/`

## Rules Implemented

- Ignore `Indeterminate Collision Detection`.
- Eval set must contain exactly 50 positives and 5000 negatives.
- Positives are stratified by `Label L2 + Label L3`.
- Negatives are stratified by `Label L2`.
- Every stratum gets at least 1 sample when included in eval.
- Remaining eval quota is allocated proportionally.
- Sampling is deterministic with seed string `v2`.
- Train set receives every non-excluded row not selected into eval.
- Downloaded video filenames use `{env}-{clipid}-{sn}.mp4`.

## Usage

Write metadata and READMEs only:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python split_dataset.py
```

Write metadata/READMEs and download both eval/train videos:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python split_dataset.py --download all --workers 8
```

Re-download files even if they already exist locally:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python split_dataset.py --download all --workers 8 --overwrite
```

## Notes

- The script requires `aws` CLI in `PATH` for `--download`.
- Local video download depends on the current machine IAM role having access to the source S3 objects.
