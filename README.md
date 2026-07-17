# Gaincraft

[![Tests](https://github.com/orbyts/gaincraft/actions/workflows/test.yml/badge.svg)](https://github.com/orbyts/gaincraft/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/gaincraft.svg)](https://pypi.org/project/gaincraft/)
[![Python](https://img.shields.io/pypi/pyversions/gaincraft.svg)](https://pypi.org/project/gaincraft/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Gaincraft is a public Python CLI project for producing and publishing validated HDR gain-map
image derivatives.

> **Release status:** Gaincraft 0.0.1 is a legitimate bootstrap release that establishes the
> package and diagnostic CLI. **HDR processing begins in 0.0.2.** This release does not inspect,
> resize, crop, validate, or upload images.

## Install

Gaincraft requires Python 3.11 or newer. Once 0.0.1 has been published to PyPI:

```console
pipx install gaincraft
```

For local development with `uv`, keep the project environment outside the repository:

```console
UV_PROJECT_ENVIRONMENT="$HOME/.venvs/gaincraft" uv sync --extra dev
```

## Bootstrap commands

```console
$ gaincraft --version
gaincraft 0.0.1

$ gaincraft doctor
```

`gaincraft doctor` is read-only. It reports the Gaincraft and Python versions, optional pyvips and
libvips availability, the future `uhdrload`/`uhdrsave` capabilities, optional Cloudinary SDK
availability, and whether Cloudinary credentials are configured. It never prints credential
values. Use `gaincraft doctor --json` for machine-readable output.

In 0.0.1, a successful `doctor` exit means the bootstrap CLI ran successfully; it does not certify
HDR readiness. HDR capability enforcement arrives with the processing commands in 0.0.2.

## Development

Run the same checks used by CI:

```console
UV_PROJECT_ENVIRONMENT="$HOME/.venvs/gaincraft" uv run ruff check .
UV_PROJECT_ENVIRONMENT="$HOME/.venvs/gaincraft" uv run ruff format --check .
UV_PROJECT_ENVIRONMENT="$HOME/.venvs/gaincraft" uv run pytest
uv build
UV_PROJECT_ENVIRONMENT="$HOME/.venvs/gaincraft" uv run twine check dist/*
```

The repository's test workflow covers supported Python versions on Linux and macOS. Publishing is
separate: a published GitHub release triggers the trusted PyPI workflow, which uses GitHub OIDC and
the protected `pypi` environment rather than a long-lived API token.

## Roadmap

Version 0.0.2 is the first functional release. Its planned scope includes runtime capability
enforcement and gain-map-aware inspect, resize, rendition, validation, and immutable Cloudinary
upload workflows. No simulated or SDR-substitution processing exists in 0.0.1.

See [CHANGELOG.md](CHANGELOG.md) for release notes.

## License

Licensed under the [Apache License 2.0](LICENSE).
