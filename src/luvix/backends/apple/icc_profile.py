"""Get an Apple-supplied extended-linear Display P3 ICC profile."""

from __future__ import annotations

import hashlib
import platform
import subprocess
from importlib.resources import files
from pathlib import Path
from tempfile import TemporaryDirectory

from luvix.backends.apple.bridge import BackendError


def linear_display_p3_icc() -> bytes:
    if platform.system() != "Darwin":
        raise BackendError("Linear Display P3 ICC extraction requires macOS")
    swift = Path(str(files("luvix.backends.apple").joinpath("icc_profile.swift")))
    digest = hashlib.sha256(swift.read_bytes()).hexdigest()[:16]
    binary = Path.home() / ".cache" / "luvix" / f"icc-profile-{digest}"
    if not binary.exists():
        binary.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["swiftc", "-O", str(swift), "-o", str(binary)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            raise BackendError(f"ICC Swift compilation failed:\n{result.stderr}")
    with TemporaryDirectory(prefix="luvix-icc-") as directory:
        destination = Path(directory) / "linear-display-p3.icc"
        result = subprocess.run(
            [str(binary), str(destination)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            raise BackendError(result.stderr.strip() or "ICC extraction failed")
        return destination.read_bytes()


def source_linear_icc(working_space: str) -> bytes:
    """Return the matching Apple linear ICC; unsupported spaces fail closed."""
    if working_space not in {"extendedLinearDisplayP3", "extendedLinearSRGB"}:
        raise BackendError(f"Unsupported working space: {working_space}")
    return (
        linear_display_p3_icc()
        if working_space == "extendedLinearDisplayP3"
        else _linear_srgb_icc()
    )


def _linear_srgb_icc() -> bytes:
    import hashlib
    import subprocess
    from importlib.resources import files
    from tempfile import TemporaryDirectory

    swift = Path(str(files("luvix.backends.apple").joinpath("icc_profile.swift")))
    digest = hashlib.sha256(swift.read_bytes()).hexdigest()[:16]
    binary = Path.home() / ".cache" / "luvix" / f"icc-profile-{digest}"
    if not binary.exists():
        binary.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["swiftc", "-O", str(swift), "-o", str(binary)], capture_output=True, text=True
        )
        if result.returncode:
            raise BackendError(result.stderr)
    with TemporaryDirectory(prefix="luvix-icc-") as directory:
        destination = Path(directory) / "linear-srgb.icc"
        result = subprocess.run(
            [str(binary), str(destination), "srgb"], capture_output=True, text=True
        )
        if result.returncode:
            raise BackendError(result.stderr.strip())
        return destination.read_bytes()
