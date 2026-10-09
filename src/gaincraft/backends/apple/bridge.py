"""Compile and execute the macOS ImageIO backend on demand."""

from __future__ import annotations

import hashlib
import platform
import subprocess
from importlib.resources import files
from pathlib import Path


class BackendError(RuntimeError):
    """Native backend failed."""


def backend_binary() -> Path:
    if platform.system() != "Darwin":
        raise BackendError("Apple HDR backend requires macOS; no portable backend yet")
    source = Path(str(files("gaincraft.backends.apple").joinpath("imageio.swift")))
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
    target = Path.home() / ".cache" / "gaincraft" / f"imageio-{digest}"
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["swiftc", "-O", str(source), "-o", str(target)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            raise BackendError(f"Swift compilation failed:\n{result.stderr}")
    return target


def run_backend(*args: str) -> str:
    result = subprocess.run(
        [str(backend_binary()), *map(str, args)], capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise BackendError(
            result.stderr.strip() or result.stdout.strip() or "Native backend failed"
        )
    return result.stdout.strip()
