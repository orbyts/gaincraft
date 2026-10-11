# Changelog

## [0.1.2] - 2026-10-10

### Changed
- Reworked the user guide around the installed `luvix` CLI instead of
  source-checkout `uv run` commands.
- Added clearer installation and quick-start documentation for PyPI users.
- Updated `luvix doctor` to report the HDR capabilities implemented in Luvix.
- Added macOS and Swift runtime readiness reporting for the Apple HDR backend.
- Clarified that 16-bit PQ export currently requires a compatible external
  PQ ICC profile.

### Fixed
- Removed obsolete bootstrap diagnostics claiming that HDR processing was
  not implemented.
- Removed the outdated "HDR processing begins in Luvix 0.0.2" message.

### Notes
- HDR decoding, reconstruction, TIFF encoding, PQ math, and color-management
  algorithms are unchanged from v0.1.1.



## [0.1.0] - 2026-10-10

### Added
- Apple HDR HEIC inspection and gain-map metadata reporting.
- Independent SDR base and HDR gain-map extraction.
- HDR HEIC reconstruction after editing either component.
- Structural HDR validation.
- Native Apple HDR decoding into extended linear RGB.
- 32-bit floating-point linear HDR TIFF export.
- 16-bit PQ HDR TIFF export with external ICC profile support.
- Source-aware color management for tested Display P3 and sRGB workflows.
- Original image orientation preservation.
- User guide, architecture documentation, and development roadmap.

### Notes
- Apple HDR HEIC is the currently validated input format.
- 32-bit linear TIFF export has been validated in Photoshop.
- 16-bit PQ TIFF export has been validated using an externally supplied
  Adobe-compatible P3 PQ ICC profile.
- Additional input formats, color spaces, and gain-map standards remain
  on the roadmap.



All notable changes to Gaincraft will be documented in this file. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

HDR processing is planned for 0.0.2.

## [0.0.1] - 2026-07-17

### Added

- Initial public Python package and `gaincraft` console entry point.
- `gaincraft --version`.
- Read-only `gaincraft doctor` diagnostics with human-readable and JSON output.
- Packaging, linting, tests, CI, and trusted PyPI publishing configuration.

### Not included

- HDR image processing. Gain-map-aware processing begins in 0.0.2.

[Unreleased]: https://github.com/orbyts/gaincraft/compare/v0.0.1...HEAD
[0.0.1]: https://github.com/orbyts/gaincraft/releases/tag/v0.0.1
