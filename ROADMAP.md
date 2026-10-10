# Luvix roadmap

Updated 2026-10-10. This is the project execution plan. Mark tasks complete only with verified evidence.

## Vision

A Swiss Army knife for HDR gain-map images: inspect, split, edit, recombine, validate, flatten to HDR TIFF, and eventually transcode among Apple, ISO and Ultra HDR gain-map representations. Preserve source captures and supported colorimetry. Avoid silent clipping, orientation changes, or format assumptions.

## Verified development progress

- [x] Apple gain-map HEIC inspect/extract/rebuild/validate, manually tested on macOS with L008 fixture.
- [x] Explicit ImageIO HDR decode, with distinct SDR/HDR numerical output.
- [x] 32-bit linear TIFF with matching linear Display P3 ICC and original orientation, user-validated in Photoshop.
- [x] 16-bit PQ TIFF numerical fidelity (mean absolute inverse-PQ error 1.64e-5, maximum 2.81e-4 in one test).
- [x] 16-bit P3 PQ TIFF visually working in Photoshop using **external** Adobe-derived reference ICC.
- [x] 57 Python tests reported passing after external-ICC patch.
- [ ] Verify complete final lint/format/tests and native export on current HEAD.
- [ ] Add automated macOS integration tests for ICC tag 34675, orientation 274, and both TIFF modes.
- [ ] Verify all required Swift resources are bundled in wheel/sdist and work after `uv tool install`.
- [ ] Extend source ICC handling beyond currently tested Display P3 and sRGB.

## Immediate: docs, CI, release

- [x] Draft user guide, architecture, release checklist, and roadmap.
- [ ] Reconcile guide against exact installed `--help` on developer Mac.
- [ ] Remove patch installer leftovers and exclude private ICC/photos from Git.
- [ ] Update README, CHANGELOG, package version, CLI help, and metadata for proposed `0.1.0`.
- [ ] Add real integration tests and wheel-installed smoke tests.
- [ ] Run Ruff, pytest, uv lock, clean build, Twine checks; check for previous metadata 2.5 incompatibility.
- [ ] Commit and push `feature/pq16-color-management`; verify GitHub Actions green.
- [ ] Merge reviewed PR to `main`; verify main CI green.
- [ ] Publish tag/GitHub release and verify configured publishing workflow.
- [ ] Install published artifact locally via uv tool and run smoke tests.
- [ ] Delete both feature branches locally/remotely **only after** successful release verification.

## Next: format support

- [ ] Apple `.jpg`/`.jpeg` gain-map captures: inspect, extract, rebuild, export, test real fixtures. Not every JPEG contains a gain map.
- [ ] ISO 21496-1 gain-map metadata, supported containers, and compatibility tests.
- [ ] Ultra HDR JPEG variants and libultrahdr encode/decode, MPF/XMP metadata.
- [ ] Evaluate libvips `uhdrload`/`uhdrsave` and ImageMagick gain-map capabilities by actual installed version/build.
- [ ] Internal gain-map model for monochrome **and multichannel/color** gain maps, offsets, headroom, and per-format metadata.
- [ ] Cross-format round-trip fidelity and interoperability tests with browsers and Adobe tools.
- [ ] Consider AVIF and additional formats after proven format semantics.

## Next: color management and usability

- [ ] Source-driven ICC support for Rec.2020, Adobe RGB and custom ICC where valid, including linear and PQ output profiles.
- [ ] Replace dependence on external proprietary P3 PQ ICC with legally redistributable validated profile solution.
- [ ] Explicit raw/display orientation handling for both base and gain map during extraction/rebuild.
- [ ] Stronger numerical and perceptual validation, EXIF/GPS preservation, and output visibility.
- [ ] Batch conversion, manifests, clear errors, optional image-processing plugins (Trinity magenta correction stays out of core).

## Release contract

Never overwrite source captures. Do not claim pixel-identical HEIC re-encoding, arbitrary ICC support, or universal gain-map interoperability without tests. Do not commit private photos/GPS or third-party Adobe ICC profiles. Keep 32-bit linear regression-protected while improving 16-bit PQ.

**Next action:** Review docs and current CLI, harden packaging and integration tests, then push and verify CI before merge/release.
