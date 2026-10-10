# Native HDR decode probe (experimental)

`luvix inspect-hdr SOURCE --samples 16` asks ImageIO to decode the same
Apple gain-map HEIC with `kCGImageSourceDecodeToHDR` disabled and enabled.
Each result is rendered into an **extended linear Display P3** float32 bitmap,
then a deterministic grid is sampled and summarized.

This is a diagnostic, **not** a calibrated HDR reconstruction or a TIFF export.
A CGContext conversion may introduce color-management or clamping effects.
The `pixels_above_one` counter counts sampled pixels, not all pixels. Sample
coordinates refer to the stored raster, not display-oriented coordinates.
The default and HDR decode options might produce similar outputs on some OS
versions. Such a result is evidence to investigate, not proof that the image
has no HDR content.

## Local test

```sh
uv run luvix inspect-hdr ~/Desktop/Trinity/IMG_8480.HEIC --samples 16
```

Save the JSON output outside Git and compare the `sdr` and `hdr` sections.
Record macOS version, hardware, and results before claiming the Apple HDR
reconstruction is numerically verified. No private photo is included in CI.
