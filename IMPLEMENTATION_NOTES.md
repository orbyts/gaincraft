# Apple HDR CLI integration (experimental)

Core commands: `inspect`, `extract`, `rebuild`, `validate`. The Apple backend compiles
ImageIO Swift on macOS on first invocation, cached under `~/.cache/gaincraft`.

Examples:

```sh
uv run gaincraft inspect IMG_8480.HEIC
uv run gaincraft extract IMG_8480.HEIC --output work/8480
uv run gaincraft rebuild --source IMG_8480.HEIC --base work/8480/base.png --output work/8480/rebuilt.HEIC
uv run gaincraft rebuild --source IMG_8480.HEIC --gainmap work/8480/gainmap.png --output work/8480/map-edit.HEIC
uv run gaincraft validate --source IMG_8480.HEIC --output work/8480/rebuilt.HEIC
```

Scope: Apple HEIC + L008 gain maps only. JPEG/Ultra HDR not implemented.
`validate` checks structural fields, not decoded pixels, EXIF equivalence, or display rendering.
Extracted PNG is an editing derivative; native re-encoding is lossy. No TIFF or
Trinity color correction in core. Rebuild refuses overwrite. Preserve originals.

## macOS integration checks still required

1. Run `uv run --extra dev pytest` and `uv run --extra dev ruff check .`.
2. Compile native Swift backend on macOS through `uv run gaincraft inspect ...`.
3. Extract Trinity fixture and verify P3 ICC and orientation.
4. Round trip untouched base and map; compare metadata and decoded gain pixels.
5. Test Photoshop-edited base and map independently.
6. Verify Finder hidden flag cleared and HDR visually displays.

Private Trinity images must not be committed to a public repository.

## Verification performed in this environment

`PYTHONPATH=src pytest -q tests/test_hdr_cli.py tests/test_cli.py tests/test_doctor.py`
passed (12 tests). macOS ImageIO compilation and actual HDR fixture tests remain
unverified because this execution environment is Linux.

The source archive supplied for review omitted LICENSE and `.github`; apply
the patch to your existing checkout rather than replacing it wholesale.
