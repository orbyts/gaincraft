# Luvix user guide

Luvix inspects HDR gain-map captures, splits their components, rebuilds edited captures, and exports HDR TIFFs. Current tested input is Apple gain-map HEIC on macOS. Do not assume arbitrary HEIC/JPEG or arbitrary ICC color-space support.

Use `uv run luvix` from the source checkout. For an installed CLI, use `luvix` directly. Check `uv run luvix --help` and `uv run luvix export tiff --help` for your exact version.

## Inspect

```bash
uv run luvix doctor
uv run luvix inspect ~/Pictures/IMG_8480.HEIC
uv run luvix inspect-hdr ~/Pictures/IMG_8480.HEIC --samples 16
```

## Split base and gain map

```bash
uv run luvix extract ~/Pictures/IMG_8480.HEIC \
  --output ~/Pictures/work/IMG_8480
```

Outputs: `base.png`, `gainmap.png`, `manifest.json`. Keep the original HEIC: rebuild uses its metadata. The exported PNGs may be in *raw pixel orientation*, not display orientation.

## Rebuild from edited components

```bash
uv run luvix rebuild \
  --source ~/Pictures/IMG_8480.HEIC \
  --base ~/Pictures/work/IMG_8480/base.png \
  --output ~/Pictures/work/base_edited.HEIC

uv run luvix rebuild \
  --source ~/Pictures/IMG_8480.HEIC \
  --gainmap ~/Pictures/work/IMG_8480/gainmap.png \
  --output ~/Pictures/work/map_edited.HEIC

uv run luvix rebuild \
  --source ~/Pictures/IMG_8480.HEIC \
  --base ~/Pictures/work/IMG_8480/base.png \
  --gainmap ~/Pictures/work/IMG_8480/gainmap.png \
  --output ~/Pictures/work/rebuilt.HEIC

uv run luvix validate \
  --source ~/Pictures/IMG_8480.HEIC \
  --output ~/Pictures/work/rebuilt.HEIC
```

`validate` currently checks core structure, not perceptual or pixel identity. Photoshop may rotate orientation-6 captures to upright dimensions (4284x5712) while the raw raster is 5712x4284. Do not resize to correct this. Raw/display orientation-aware rebuild is planned.

## 32-bit float linear HDR TIFF

```bash
uv run luvix export tiff ~/Pictures/IMG_8480.HEIC \
  --bit-depth 32 --transfer linear --color-space source \
  --output ~/Pictures/work/linear32.tif
```

The tested Display P3 path embeds a matching *linear Display P3* ICC profile, preserves source orientation tag, and retains HDR RGB values above 1.0. This was visually validated in Photoshop. `source` does not imply every ICC profile is supported: currently tested source working spaces are Display P3 and sRGB.

## 16-bit unsigned PQ HDR TIFF

The visually validated P3 workflow currently requires an **external compatible P3 PQ ICC**. Do not commit a proprietary ICC to a public repository without rights.

```bash
uv run luvix export tiff ~/Pictures/IMG_8480.HEIC \
  --bit-depth 16 --transfer pq --color-space source \
  --reference-white 203 \
  --icc-profile ~/ColorProfiles/P3_PQ_Reference.icc \
  --output ~/Pictures/work/pq16.tif
```

203 nits is a configurable test convention, not derived from the HEIC. The P3 PQ profile must match source primaries and ST 2084. The old experimental *generated* PQ ICC produced a dark Photoshop image and is not the recommended route. In one real-image test, inverse-PQ vs linear32 had mean absolute error 1.64e-5 and maximum 2.81e-4.

## Verify output

```bash
exiftool -G1 -s -ProfileDescription -BitsPerSample \
  -SampleFormat -Orientation ~/Pictures/work/linear32.tif
```

ICC should be present in TIFF tag 34675; orientation in tag 274. Confirm actual tags, not just a success message. Input files are not modified, but HEIC re-encoding may be lossy.

## Troubleshooting

- `No such command`: verify the CLI version and `--help`.
- `Base dimensions mismatch`: check raw vs display orientation; do not resample.
- Dark PQ TIFF or `Display P3 Linear` profile: PQ pixels need a matching PQ ICC, not a linear ICC.
- Unsupported source profile: no general automatic color conversion is promised yet.
- Native macOS backend fails: verify `swiftc` and Xcode command-line tools.

Apple JPEG gain maps, ISO 21496-1, Ultra HDR JPEG, multichannel gain maps, arbitrary ICC conversions, and Trinity-specific color corrections are **not yet implemented** as general workflows.
