# Luvix user guide

Luvix is a command-line utility for inspecting HDR gain-map photographs, extracting their components, rebuilding edited Apple HDR captures, and exporting HDR TIFFs for image editing.

> **Current support (v0.1.1):** Apple gain-map HEIC on macOS. Not every HEIC has a gain map. Apple JPEG gain maps, ISO 21496-1, Ultra HDR, and arbitrary color-space conversions are future work.

## Requirements

- macOS for the currently implemented Apple HDR backend.
- Python 3.11 or newer (for Python-based installation).
- Apple Swift compiler (`swiftc`) and Xcode Command Line Tools for on-demand native backend compilation. Install the tools with `xcode-select --install` if needed.
- A compatible external PQ ICC profile for the validated 16-bit P3 PQ workflow.

## Install

**Recommended: uv tool** (isolated application environment):

```bash
uv tool install luvix
luvix --version
luvix --help
```

**Alternative: pipx** (isolated application environment):

```bash
pipx install luvix
luvix --version
```

**Alternative: pip** (install in an activated virtual environment):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install luvix
luvix --version
```

Avoid installing with `pip` into the system Python. The installed command is `luvix`, **not** `uv run luvix`. The latter is for development from a source checkout.

To upgrade a uv-managed installation:

```bash
uv tool upgrade luvix
```

To remove it:

```bash
uv tool uninstall luvix
```

## Quick start

Use your own input file and a writable output directory:

```bash
mkdir -p ~/Pictures/luvix-work
luvix inspect ~/Pictures/photo.HEIC
luvix extract ~/Pictures/photo.HEIC --output ~/Pictures/luvix-work/photo
luvix export tiff ~/Pictures/photo.HEIC \
  --bit-depth 32 --transfer linear --color-space source \
  --output ~/Pictures/luvix-work/photo-linear32.tif
```

Luvix does not modify the original capture. Keep it available for rebuilding edited components.

## Inspect a capture

```bash
luvix inspect ~/Pictures/photo.HEIC
luvix inspect-hdr ~/Pictures/photo.HEIC --samples 16
```

`inspect` reports stored image dimensions, orientation, working color space, and gain-map layout. `inspect-hdr` is a diagnostic comparison of Apple's SDR and HDR decoding paths. For command-specific options:

```bash
luvix inspect --help
luvix inspect-hdr --help
```

## Extract SDR base and HDR gain map

```bash
luvix extract ~/Pictures/photo.HEIC \
  --output ~/Pictures/luvix-work/photo
```

The extraction creates `base.png`, `gainmap.png`, and `manifest.json`. The PNGs can be in **raw pixel orientation**, which may differ from how Photos or Photoshop displays the capture. Keep the source HEIC and manifest. A gain-map preview PNG is not a substitute for the original gain-map metadata.

## Rebuild an edited capture

Replace only the base image:

```bash
luvix rebuild \
  --source ~/Pictures/photo.HEIC \
  --base ~/Pictures/luvix-work/photo/base.png \
  --output ~/Pictures/luvix-work/base-edited.HEIC
```

Replace only the gain map:

```bash
luvix rebuild \
  --source ~/Pictures/photo.HEIC \
  --gainmap ~/Pictures/luvix-work/photo/gainmap.png \
  --output ~/Pictures/luvix-work/map-edited.HEIC
```

Replace both:

```bash
luvix rebuild \
  --source ~/Pictures/photo.HEIC \
  --base ~/Pictures/luvix-work/photo/base.png \
  --gainmap ~/Pictures/luvix-work/photo/gainmap.png \
  --output ~/Pictures/luvix-work/rebuilt.HEIC
```

Validate the rebuilt HEIC:

```bash
luvix validate \
  --source ~/Pictures/photo.HEIC \
  --output ~/Pictures/luvix-work/rebuilt.HEIC
```

**Validation scope:** structural HDR checks, not pixel-perfect identity or visual equivalence. HEIC re-encoding can be lossy. If an editor changes a 5712×4284 raw raster into a 4284×5712 upright raster, the current rebuild may reject it. Do not resample merely to satisfy dimensions. Orientation-aware rebuild remains on the roadmap.

## Export a 32-bit linear HDR TIFF

For a high-precision Photoshop editing master:

```bash
luvix export tiff ~/Pictures/photo.HEIC \
  --bit-depth 32 \
  --transfer linear \
  --color-space source \
  --output ~/Pictures/luvix-work/photo-linear32.tif
```

The validated Display P3 path embeds a matching **linear Display P3** ICC profile, preserves the source orientation tag, and retains floating-point HDR values above 1.0. Source-matched behavior is currently tested for Display P3 and sRGB, not arbitrary ICC profiles. Photoshop rendering can depend on HDR display settings.

## Export a 16-bit PQ HDR TIFF

The validated P3 workflow requires a **compatible external P3-D65 PQ ICC profile**. Luvix does not currently bundle one. Supply a profile you are licensed to use:

```bash
luvix export tiff ~/Pictures/photo.HEIC \
  --bit-depth 16 \
  --transfer pq \
  --color-space source \
  --reference-white 203 \
  --icc-profile ~/ColorProfiles/P3_PQ_Reference.icc \
  --output ~/Pictures/luvix-work/photo-pq16.tif
```

`203` nits is an explicit reference-white convention used in testing, **not** a value inferred from the HEIC. The ICC must describe the same primaries and PQ/ST 2084 encoding as the output. The previously generated experimental linear-named ICC was not Photoshop-compatible. A compatible Adobe-generated P3 PQ ICC was visually validated in one workflow; redistribution rights have not been established.

## Verify the output

With ExifTool installed separately:

```bash
exiftool -G1 -s \
  -ProfileDescription -BitsPerSample -SampleFormat -Orientation \
  ~/Pictures/luvix-work/photo-linear32.tif
```

For the validated 32-bit P3 export, expect three 32-bit floating-point channels, a linear P3 profile, and the original orientation (for example, orientation 6). TIFF ICC profile data is stored in tag 34675 and orientation in tag 274. The metadata check is not a substitute for visual verification.

## Troubleshooting

| Symptom | What to check |
|---|---|
| `luvix: command not found` | Confirm installation and that your uv/pipx executable directory is on `PATH`. |
| `No such command` | Run `luvix --version` and `luvix --help`. |
| `Base dimensions mismatch` | Compare raw and display orientations; do not resize the image. |
| PQ TIFF looks dark | Verify that the embedded profile is PQ, not linear, and that its primaries match. |
| Unsupported color profile | The source working-space implementation is currently limited. |
| Swift compilation fails | Check `swiftc --version` and Xcode Command Line Tools. |
| Output file already exists | Choose a new output filename; Luvix refuses to overwrite existing outputs. |

## Developer workflow

Only when working on the source repository:

```bash
git clone https://github.com/orbyts/luvix.git
cd luvix
uv sync --extra dev
uv run luvix --help
uv run pytest -q
uv run ruff check .
```

For feature requests, current support boundaries, and planned interoperability with Apple JPEG gain maps, ISO 21496-1, libultrahdr, libvips, and ImageMagick, see `ROADMAP.md`.
