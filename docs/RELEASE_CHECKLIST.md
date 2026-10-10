# Release runbook (candidate v0.1.0)

This document does not claim a release has occurred. Run commands in order and stop on failure. Verify exact GitHub workflow names in `.github/workflows/`.

## 1. Clean and verify feature branch

```bash
cd "$PACKAGES/gaincraft"
git status --short --branch
git diff --check
git diff --cached --check
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
uv lock --check
uv run gaincraft export tiff --help
```

Review untracked files individually; exclude temporary `apply.py`, extracted patch directories, private HEICs, and third-party ICC profiles. Do not use indiscriminate `git add .` or `git clean -fd`.

## 2. Confirm release contents

- [ ] CLI documentation matches actual options and defaults.
- [ ] Source ICC restrictions and external-PQ-ICC requirement are explicit.
- [ ] Real HEIC `inspect`, `extract`, `rebuild`, `validate`, float32 TIFF and PQ16 TIFF work on macOS.
- [ ] Both TIFFs contain correct ICC tag 34675 and orientation tag 274.
- [ ] Native Swift files (`imageio.swift`, `hdr_probe.swift`, `hdr_raster.swift`, `icc_profile.swift`) are included in built wheel/sdist and installed runtime. Check current `pyproject.toml` force-include configuration, which previously only included `imageio.swift`.
- [ ] No proprietary ICC, private image, GPS, or patch installer in distribution.
- [ ] Version in `pyproject.toml`, `src/gaincraft/__init__.py`, CLI help, README, and CHANGELOG is consistent.

## 3. Clean package build and installed smoke test

```bash
rm -rf dist
uv build
uv run --locked twine check dist/*
uv run python - <<'PY'
from pathlib import Path
from zipfile import ZipFile
wheel = next(Path('dist').glob('*.whl'))
with ZipFile(wheel) as z:
    swift = sorted(n for n in z.namelist() if n.endswith('.swift'))
    print('\n'.join(swift))
    required = {'imageio.swift','hdr_probe.swift','hdr_raster.swift','icc_profile.swift'}
    assert required <= {Path(n).name for n in swift}, 'Missing Swift resources'
PY
```

Install built wheel in a **separate uv-managed tool environment**, not the existing project environment. Example after selecting the built wheel:

```bash
uv tool install --force dist/gaincraft-0.1.0-py3-none-any.whl
uv tool run --from dist/gaincraft-0.1.0-py3-none-any.whl gaincraft --help
```

Adjust wheel name to the actual version. Check whether a preexisting `gaincraft` tool install needs preservation before using `--force`. On macOS, smoke-test the installed executable with a private HEIC; don't publish that fixture.

## 4. Push and verify CI

```bash
git add README.md ROADMAP.md CHANGELOG.md docs pyproject.toml uv.lock src tests
git diff --cached --stat
git diff --cached --check
git commit -m 'docs(release): document HDR workflows and prepare first functional release'
git push -u origin feature/pq16-color-management
gh run list --branch feature/pq16-color-management --limit 5
gh run watch
```

Wait for latest CI **success**; investigate `gh run view --log-failed` if red. Don't merge based only on local tests.

## 5. Merge and release

Create a PR from `feature/pq16-color-management` into `main` (which also incorporates the previously pushed `feature/apple-hdr-roundtrip` changes). Review diff and merge only after checks pass.

```bash
gh pr create --base main --head feature/pq16-color-management \
  --title 'Gaincraft HDR gain-map workflows and TIFF export' \
  --body 'Documented HEIC round-trip, 32-bit linear HDR TIFF and experimental external-ICC PQ16 TIFF.'
```

After PR merge, check `main` CI. Confirm release publishing workflow and whether it triggers from a GitHub release, tag, or manual dispatch before tagging. Avoid double-publishing. Example **only after** version is bumped, main is green, and publishing configuration reviewed:

```bash
git switch main
git pull --ff-only
git tag -a v0.1.0 -m 'Gaincraft v0.1.0'
git push origin v0.1.0
gh release create v0.1.0 --title 'Gaincraft v0.1.0' --generate-notes
```

If release automation requires a different order, follow that workflow. Verify published artifact and install it with `uv tool install gaincraft==0.1.0` once available. Test `gaincraft --version`, `gaincraft doctor`, and a private macOS HEIC smoke workflow.

## 6. Delete branches only after verification

```bash
git branch -d feature/pq16-color-management
git branch -d feature/apple-hdr-roundtrip
git push origin --delete feature/pq16-color-management
git push origin --delete feature/apple-hdr-roundtrip
```

Delete only branches actually merged and no longer needed; verify current branch is `main` and clean first.
