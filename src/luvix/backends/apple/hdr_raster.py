"""Compile and invoke Apple's full-resolution float HDR raster renderer."""

from __future__ import annotations

import hashlib
import platform
import subprocess
from importlib.resources import files
from pathlib import Path

from luvix.backends.apple.bridge import BackendError


def render_hdr_raster(source: Path, prefix: Path) -> None:
    if platform.system() != "Darwin":
        raise BackendError("Apple HDR raster export requires macOS")
    swift = Path(str(files("luvix.backends.apple").joinpath("hdr_raster.swift")))
    digest = hashlib.sha256(swift.read_bytes()).hexdigest()[:16]
    binary = Path.home() / ".cache" / "luvix" / f"hdr-raster-{digest}"
    if not binary.exists():
        binary.parent.mkdir(parents=True, exist_ok=True)
        compiled = subprocess.run(
            ["swiftc", "-O", str(swift), "-o", str(binary)],
            capture_output=True,
            text=True,
            check=False,
        )
        if compiled.returncode:
            raise BackendError(f"Swift compilation failed:\n{compiled.stderr}")
    result = subprocess.run(
        [str(binary), str(source), str(prefix)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise BackendError(result.stderr.strip() or "HDR raster export failed")
