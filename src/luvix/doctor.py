"""Read-only runtime and HDR capability diagnostics."""

from __future__ import annotations

import os
import platform
import shutil
from ctypes.util import find_library
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from typing import Any


def _distribution_version(distribution: str) -> str | None:
    try:
        return version(distribution)
    except PackageNotFoundError:
        return None


def _cloudinary_credentials_configured() -> bool:
    if os.environ.get("CLOUDINARY_URL"):
        return True
    return all(
        os.environ.get(name)
        for name in ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET")
    )


def _operation_available(pyvips: Any, operation: str) -> bool:
    try:
        return bool(pyvips.type_find("VipsOperation", operation))
    except (AttributeError, TypeError):
        return False


def _pyvips_capabilities() -> tuple[dict[str, Any], dict[str, Any], dict[str, bool]]:
    pyvips_version = _distribution_version("pyvips")
    pyvips_result: dict[str, Any] = {
        "installed": pyvips_version is not None,
        "importable": False,
        "version": pyvips_version,
    }
    libvips_result: dict[str, Any] = {"available": False, "version": None}
    operations = {"uhdrload": False, "uhdrsave": False}
    if pyvips_version is None:
        return pyvips_result, libvips_result, operations
    try:
        pyvips = import_module("pyvips")
        libvips_version = ".".join(str(pyvips.version(index)) for index in range(3))
    except (ImportError, OSError, AttributeError, TypeError):
        return pyvips_result, libvips_result, operations
    pyvips_result["importable"] = True
    libvips_result.update(available=True, version=libvips_version)
    operations = {
        operation: _operation_available(pyvips, operation) for operation in ("uhdrload", "uhdrsave")
    }
    return pyvips_result, libvips_result, operations


def collect_diagnostics(luvix_version: str) -> dict[str, Any]:
    """Collect diagnostics without modifying files or revealing credential values."""
    pyvips, libvips, operations = _pyvips_capabilities()
    cloudinary_version = _distribution_version("cloudinary")
    ultrahdr_library = find_library("ultrahdr")
    is_macos = platform.system() == "Darwin"
    swift_available = shutil.which("swiftc") is not None
    return {
        "luvix": {"release": "functional", "version": luvix_version},
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
        },
        "apple_hdr": {
            "implemented": True,
            "platform_supported": is_macos,
            "swift_compiler_available": swift_available,
            "runtime_ready": is_macos and swift_available,
        },
        "hdr_processing": {
            "implemented": True,
            "inspection": True,
            "extraction": True,
            "rebuild": True,
            "validation": True,
            "linear32_tiff": True,
            "pq16_tiff": True,
            "pq16_external_icc_required": True,
        },
        "pyvips": pyvips,
        "libvips": libvips,
        "ultrahdr": {
            "library_discoverable": ultrahdr_library is not None,
            "uhdrload": operations["uhdrload"],
            "uhdrsave": operations["uhdrsave"],
        },
        "cloudinary": {
            "credentials_configured": _cloudinary_credentials_configured(),
            "sdk_installed": cloudinary_version is not None,
            "sdk_version": cloudinary_version,
        },
    }
