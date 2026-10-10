# M2.1 — HDR reconstruction contract (draft; not yet validated)

Status: **reference specification and transfer-function test vectors only**. No TIFF encoder or Apple HDR RGB reconstruction is implemented by this patch.

## Goal

Produce a linear-light HDR RGB buffer from an Apple gain-map HEIC, with explicit source primaries, transfer function, reference white, and reconstruction policy. Only then encode 32-bit float linear TIFF and 16-bit integer PQ TIFF.

## Known source observations (private Trinity fixture)

- Primary stored raster: 5712 × 4284; EXIF orientation 6; Display P3 ICC.
- Apple auxiliary type: `urn:com:apple:photo:2020:aux:hdrgainmap`.
- Auxiliary decoded format: `L008`, 2856 × 2142, 3200 bytes/row.
- XMP `HDRGainMapHeadroom`: 4.638313; do not interpret this alone as a direct per-pixel multiplier or absolute peak luminance.
- ImageIO extraction/rebuild re-encodes auxiliary values; previous observed mean absolute 8-bit difference ≈ 0.164, maximum 7.

## Required reconstruction reference

1. On macOS, use Apple's **HDR-aware Core Image rendering path** as the initial visual/numerical reference. Determine available APIs and OS behavior empirically rather than assume `L008 / 255 × headroom` is the correct reconstruction equation. Record OS and framework versions.
2. Render a source through an HDR-capable pipeline into an explicitly chosen extended-range, linear-light floating-point working color space. Capture pixel values, channel semantics, and color profile.
3. Compare the rendered HDR output against decoded SDR pixels and the auxiliary map for synthetic and private real-world fixtures. Investigate gamut conversion, offsets, highlight handling, orientation, and interpolation.
4. Establish the reference SDR white mapping in nits (e.g. explicit `--reference-white-nits`) **before** using PQ. Relative gain headroom does not establish absolute scene/display luminance.
5. Validate numerical equivalence within documented tolerances and perform a separate Photoshop HDR display comparison.

## Transfer functions

`luvix.hdr.pq` provides standalone ST 2084 reference encode/decode functions for **absolute luminance** in cd/m². These functions are not gain-map decoders and must not be applied to uncalibrated map bytes or non-linear RGB values as if they were linear luminance.

- PQ maps absolute luminance in [0, 10000] cd/m² to normalized code values in [0, 1].
- PQ is applied to correctly scaled **linear RGB channels** under a defined color encoding. A valid profile must identify both primaries and PQ transfer; the source's SDR Display P3 ICC profile is not valid for PQ-encoded pixels.
- 32-bit linear TIFF must describe linear transfer and retain HDR values above SDR reference white. Avoid implicit clipping.

## Open questions / acceptance gates

- Exact Apple gain-map reconstruction metadata and headroom interpretation for the observed file; do not infer from the grayscale histogram alone.
- Whether the platform's HDR-aware Core Image rendering path matches the intended Apple Photos display across macOS versions and display headroom.
- Whether Photoshop correctly interprets a custom Display P3 + PQ TIFF profile and a Display P3 linear float TIFF profile. This requires real Photoshop tests, not just TIFF tag checks.
- Orientation policy remains raw stored pixel order until M3; record orientation and compare in the same coordinate system.

## M2.1 acceptance

- [x] Explicit reconstruction contract and no implicit `L008`→stops assumption.
- [x] Portable ST 2084 encode/decode implementation and reference tests.
- [ ] Verified macOS HDR-aware reference render of `IMG_8480.HEIC`.
- [ ] Documented reference-white policy and measured test vectors from native HDR render.
- [ ] Numeric and visual cross-checks before implementing TIFF encoders.

Do not mark M2.1 complete until the unchecked gates pass.
