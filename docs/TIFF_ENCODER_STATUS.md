# M2 TIFF raster encoder (experimental)

This patch adds `luvix.hdr.tiff.write_hdr_tiff` and synthetic tests only.
It **does not** add `luvix export tiff` or Apple gain-map reconstruction.

- `32/linear`: float32 RGB TIFF, preserves negative and above-one channel values.
- `16/pq`: uint16 RGB TIFF encoded using SMPTE ST 2084 with explicit `reference_white_nits` (e.g. 203). Values outside the PQ domain fail instead of clipping.
- `primaries` is recorded in TIFF ImageDescription for diagnostics only. **No ICC profile is embedded**. These files are **not yet color-managed deliverables** and must not be represented as visually identical to an Apple HDR HEIC in Photoshop.
- Pixel values are assumed to already be linear RGB in the declared primaries, with 1.0 representing reference white.
- Tests use synthetic values and TIFF round trips. Do not pass decoded ImageIO probe values as validated HDR reconstruction yet.

## Applying to the uv-managed project

Copy the patch files into the repository. Add the runtime dependencies with:

```sh
uv add numpy tifffile
uv run ruff format src/luvix/hdr/tiff.py tests/test_hdr_tiff.py
uv run ruff check .
uv run pytest -q
```

This updates `pyproject.toml` and `uv.lock` in the normal uv workflow.

## Next gates

1. Independently validate Apple HDR reconstruction and its normalization.
2. Embed and verify transfer-specific color profiles and Photoshop behavior.
3. Expose CLI only after these gates, with tests and explicit reference-white policy.
