# Gaincraft Roadmap

Status: working engineering plan, 2026-10-09. This file is the **source of truth for next steps**. Update checkboxes and the decision log after each verified milestone. A checked item requires evidence, not just implemented code.

## Product contract

Gaincraft is a format-aware HDR inspection, component extraction, editing/rebuild, validation, and (next) HDR raster export CLI. Keep the original capture untouched. Keep format-specific logic in backends, not in the CLI. Never silently crop, rotate, resample, change primaries, or replace HDR with SDR. Report lossy re-encoding honestly. The Trinity-specific magenta correction is **out of core scope** and may become an optional module later.

## Priority and sequencing

**Now: M2, HDR TIFF export.** Build 16-bit PQ and 32-bit floating-point linear TIFF from Apple HDR gain-map HEIC, using the native gain-map reconstruction and explicit color management. After the core export path is validated, return to orientation-aware editing and other usability edge cases. No JPEG gain-map support or general-purpose color correction in M2.

### M1 — Apple gain-map component round trip (functional prototype)

- [x] Add `inspect`, `extract`, `rebuild`, `validate` CLI commands without removing `doctor`.
- [x] Run Python unit tests on macOS: 12 passed, Ruff checks passed (user-reported 2026-10-09).
- [x] Compile native Swift ImageIO backend on macOS and inspect private `IMG_8480.HEIC`.
- [x] Confirm inspection reports Display P3, orientation 6, 5712×4284 base, L008 2856×2142 gain map, 3200-byte stride.
- [x] User reports extract/rebuild/validate and visual HDR round trip working on one fixture.
- [ ] Add repeatable automated macOS integration tests for extract, base-only edit, map-only edit, rebuild, and validation. Current unit tests mock backend dispatch.
- [ ] Quantify decoded base/gain-map numerical differences after re-encoding; verify EXIF/GPS and ICC explicitly.
- [ ] Verify and enforce visible output files (clear macOS `hidden` file flag).
- [ ] Harden native backend compilation cache invalidation when Swift source changes.
- [ ] Define unsupported-format errors and validate inputs without modifying sources.

**Known issue:** A Photoshop-edited 4284×5712 portrait PNG was rejected against the 5712×4284 stored base. Orientation 6 needs an explicit policy; do not auto-rotate solely from dimensions. Manual pixel rotation is a temporary workaround.

### M2 — HDR TIFF export (NEXT IMPLEMENTATION)

Goal: convert gain-map-based HDR to a single RGB HDR TIFF suitable for editing, without a separate gain map. `gaincraft export tiff` is **proposed, not yet implemented**.

- [ ] **M2.1 — Reconstruction specification.** Inspect Apple gain-map decoding/reconstruction semantics, including gain-map metadata, headroom, transfer characteristics, white point, and source ICC. Establish a reference decode and numerical test vectors. Do **not** treat raw 8-bit map values as linear stops without calibration.
- [ ] **M2.2 — Shared HDR intermediate.** Reconstruct a high-precision, linear-light RGB buffer with explicitly tagged primaries/white point, normalized reference white, and documented HDR headroom. Keep original pixels untouched.
- [ ] **M2.3 — 32-bit float TIFF, linear.** Export float32 TIFF in source primaries where supported, with a correctly described linear profile/metadata. Preserve values above SDR reference white. Verify Photoshop interpretation, not merely file readability.
- [ ] **M2.4 — 16-bit unsigned TIFF, PQ.** Apply SMPTE ST 2084 PQ to *absolute* luminance with an explicit reference-white/peak-nits policy. Encode source primaries where supported and embed a valid ICC/profile/metadata combination; do not label a conventional Display P3 SDR profile as PQ. Verify Photoshop's actual HDR rendering and editing behavior.
- [ ] **M2.5 — CLI and validation.** Add `gaincraft export tiff SOURCE --bit-depth {16,32} --transfer {pq,linear} --color-space source --output FILE` with enforced valid pairings initially (16/pq, 32/linear). Explicit options for reference-white nits and any tone/gamut mapping policy. No implicit clipping.
- [ ] **M2.6 — Automated fixtures.** Tests for constant/gradient gain maps, black, SDR reference white, highlight >1, gamut boundaries, clipping, metadata, pixel statistics, and error handling. Compare decoded TIFF against the reference reconstructed HDR buffer within specified tolerances.
- [ ] **M2.7 — Real-photo acceptance.** Run private Trinity `IMG_8480.HEIC` through both formats on macOS. Compare appearance on an HDR-capable display in Photoshop and a known reference viewer. Document environment, display headroom, white-level settings, and discrepancies.

**Important constraint:** “Non-destructive” means the original remains unchanged and conversion is reproducible. A 16-bit PQ TIFF and a 32-bit linear TIFF cannot be guaranteed bit-identical to a gain-map HEIC or visually identical across apps/displays. Acceptance requires defined numerical tolerances and color-managed perceptual checks. PQ requires an absolute luminance scale; gain-map headroom alone does not specify one.

### M3 — Orientation-aware extraction/rebuild and robustness

- [ ] Add explicit `raw` versus `display` extraction orientation modes and record the policy in the manifest.
- [ ] Invert display transforms correctly for both base and gain map on rebuild; reject ambiguous or mismatched edits.
- [ ] Handle Photoshop ICC/metadata changes, orientation tags, and pixel dimensions deterministically.
- [ ] Strengthen `validate`: compare source/output metadata, gain-map metadata, decoded-pixel metrics, and output visibility. Clearly separate structure, fidelity, and visual checks.
- [ ] Test multiple HEIC photos and macOS versions, missing/corrupt auxiliary items, and failure cleanup.

### M4 — Format expansion and optional processing

- [ ] Inspect JPEG gain-map variants (Apple and Ultra HDR) and define per-format backends. Not every JPEG has a gain map.
- [ ] Add more input/output formats only with verified metadata and color handling.
- [ ] Consider optional `corrections/` plugin/module for the Trinity-specific magenta/purple cast removal; keep its presets and subject masking separate from HDR I/O.
- [ ] Revisit original roadmap items (resize/rendition, Cloudinary publishing) after the core HDR paths are stable.

## Suggested CLI contracts (not all implemented)

```sh
uv run gaincraft inspect INPUT.HEIC
uv run gaincraft extract INPUT.HEIC --output WORKDIR
uv run gaincraft rebuild --source INPUT.HEIC --base WORKDIR/base.png --gainmap WORKDIR/gainmap.png --output RESULT.HEIC
uv run gaincraft validate --source INPUT.HEIC --output RESULT.HEIC

# M2 proposals (NOT IMPLEMENTED):
uv run gaincraft export tiff INPUT.HEIC --bit-depth 16 --transfer pq --color-space source --output HDR_PQ.tif
uv run gaincraft export tiff INPUT.HEIC --bit-depth 32 --transfer linear --color-space source --output HDR_LINEAR.tif
```

## Tests and fixture privacy

Keep Trinity captures and GPS metadata outside the public Git repository. Add opt-in local integration tests via an environment variable or explicit fixture path; use synthetic, metadata-sanitized fixtures in CI. Never commit a private photo merely to make tests pass.

## Progress protocol

1. Start each work session by reading `ROADMAP.md`, checking `git status`, and running existing tests.
2. Work on the earliest unchecked item in the active milestone, unless an explicit blocker changes order.
3. Add or update tests alongside the feature; distinguish Python unit tests from macOS native and visual validation.
4. Run `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest -v`, and relevant native integration tests.
5. Record the actual test result, blockers, and next action here. Do not mark an item done solely because code was written.
6. Keep changes reviewable via `git diff`; do not commit or publish without explicit approval.

## Decision log

- **2026-10-09:** Prioritize 16-bit PQ and 32-bit linear TIFF export **before** orientation UX refinement.
- **2026-10-09:** Keep `inspect`, `extract`, `rebuild`, `validate` as core commands; add TIFF export as a separate command group.
- **2026-10-09:** Preserve source color primaries where possible; specify transfer function separately. Do not assume Display P3's SDR profile describes PQ.
- **2026-10-09:** Defer Trinity-specific SDR color correction and additional format support.
- **2026-10-09:** M1 Python checks and native `inspect` verified on user's Mac; extraction/rebuild reported successful, but complete automated fidelity coverage remains outstanding.

**Next action:** Run the M2.1 native macOS HDR-aware reference-render investigation and capture numerical vectors. `docs/HDR_RECONSTRUCTION.md` and `gaincraft.hdr.pq` provide the initial spec and PQ tests; M2.1 is not yet complete.

- **2026-10-09 (M2.1 patch):** Added reconstruction contract and standalone ST 2084 reference math/tests. Native Apple HDR rendering and TIFF export are still pending.

- **M2 native probe (experimental):** Added `inspect-hdr` diagnostic; macOS compilation and HDR numerical results are **not yet verified**. Do not mark M2.1 complete until the native probe is validated.

- **2026-10-09 (experimental PQ ICC):** 16-bit PQ TIFF now embeds a sampled matrix/TRC ICC derived from the source linear ICC. Numerical/ICC tag tests are included. Photoshop HDR equivalence remains unverified; M2.4 is not complete.
