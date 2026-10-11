# Luvix

[![Tests](https://github.com/orbyts/luvix/actions/workflows/test.yml/badge.svg)](https://github.com/orbyts/luvix/actions/workflows/test.yml)

**Luvix** is a CLI toolkit for HDR gain-map images: inspect, split SDR base and gain map, rebuild edited captures, validate, and export flattened HDR TIFFs.

## Current release-candidate scope

The tested backend processes Apple HDR gain-map **HEIC** captures on **macOS** using ImageIO/Core Image and Swift. It supports `inspect`, `extract`, `rebuild`, `validate`, `inspect-hdr`, and `export tiff`. A 32-bit linear float TIFF with matching source-supported ICC has been validated in Photoshop. The 16-bit PQ TIFF was visually validated with an **externally supplied P3 PQ ICC**. General JPEG gain-map input, ISO/Ultra HDR interoperability, and arbitrary ICC source profiles are roadmap items, **not current supported features**.

## Install

Recommended for a command-line application:

```bash
uv tool install luvix
luvix --version
```

Alternatively, use `pipx install luvix`, or install `luvix` with pip inside an activated virtual environment.

The installed command is `luvix`. `uv run luvix` is only for development from a source checkout.

## Quick start

```bash
luvix doctor
luvix inspect ~/Pictures/photo.HEIC
luvix extract ~/Pictures/photo.HEIC --output ~/Pictures/work/photo
luvix export tiff ~/Pictures/photo.HEIC \
  --bit-depth 32 --transfer linear --color-space source \
  --output ~/Pictures/work/photo_linear32.tif
```

For 16-bit PQ output, supply a compatible external PQ ICC and an explicit reference white. See the user guide for the full workflow and current support boundaries.

## Documentation

- [User guide](docs/USER_GUIDE.md): full command walkthrough, output formats, and troubleshooting.
- [Architecture](docs/ARCHITECTURE.md): gain-map model, color handling, and format constraints.
- [Roadmap](ROADMAP.md): planned JPEG, ISO 21496-1, Ultra HDR, multichannel maps, and color-space expansion.
- [Release checklist](docs/RELEASE_CHECKLIST.md): CI, package verification, merge, publish, and install smoke tests.
- [Changelog](CHANGELOG.md)

## Development checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
uv lock --check
uv build
uv run --locked twine check dist/*
```

The native Apple backend requires macOS and `swiftc`. The Python package itself is cross-platform, but this does not imply the Apple HDR features run on Linux.

## License

Apache License 2.0. Do not redistribute proprietary reference ICC profiles or private photographs as part of Luvix.
