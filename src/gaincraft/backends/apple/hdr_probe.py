"""Build and run the isolated macOS HDR decode diagnostic."""

from __future__ import annotations

import hashlib
import platform
import subprocess
from importlib.resources import files
from pathlib import Path

from gaincraft.backends.apple.bridge import BackendError


def run_hdr_probe(source: Path, samples: int) -> str:
    """Return JSON from the native HDR-aware decode probe."""
    if platform.system() != "Darwin":
        raise BackendError("HDR-aware ImageIO decoding requires macOS")
    swift = Path(str(files("gaincraft.backends.apple").joinpath("hdr_probe.swift")))
    digest = hashlib.sha256(swift.read_bytes()).hexdigest()[:16]
    binary = Path.home() / ".cache" / "gaincraft" / f"hdr-probe-{digest}"
    if not binary.exists():
        binary.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["swiftc", "-O", str(swift), "-o", str(binary)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            raise BackendError(f"Swift compilation failed:\n{result.stderr}")
    result = subprocess.run(
        [str(binary), "inspect-hdr", str(source), str(samples)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise BackendError(result.stderr.strip() or "HDR probe failed")
    return result.stdout.strip()
