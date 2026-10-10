"""Experimental HDR TIFF raster encoders for *already reconstructed* linear RGB.

These functions do not decode Apple gain maps or assert Photoshop HDR compatibility.
They intentionally refuse to label a TIFF with an incorrect ICC profile.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import numpy as np
import tifffile

# ST 2084 constants, per SMPTE ST 2084.
_M1 = 2610 / 16384
_M2 = 2523 / 32
_C1 = 3424 / 4096
_C2 = 2413 / 128
_C3 = 2392 / 128


class HDRTIFFError(ValueError):
    """Invalid HDR raster or encoding configuration."""


def _linear_rgb(rgb: np.ndarray) -> np.ndarray:
    arr = np.asarray(rgb)
    if arr.ndim != 3 or arr.shape[-1] != 3 or min(arr.shape[:2]) < 1:
        raise HDRTIFFError("Expected nonempty HxWx3 RGB array")
    if not np.issubdtype(arr.dtype, np.number):
        raise HDRTIFFError("RGB must contain numeric values")
    arr = arr.astype(np.float32, copy=False)
    if not np.isfinite(arr).all():
        raise HDRTIFFError("RGB contains NaN or infinity")
    return arr


def encode_pq(rgb_linear: np.ndarray, *, reference_white_nits: float) -> np.ndarray:
    """Encode nonnegative linear RGB relative to reference white as ST 2084 PQ.

    Output is floating PQ code values in [0,1], before 16-bit quantization.
    Values above the 10,000-nit PQ range are rejected, never silently clipped.
    """
    rgb = _linear_rgb(rgb_linear)
    if not np.isfinite(reference_white_nits) or reference_white_nits <= 0:
        raise HDRTIFFError("reference_white_nits must be positive and finite")
    nits = rgb.astype(np.float64) * reference_white_nits
    if (nits < 0).any() or (nits > 10000).any():
        raise HDRTIFFError("PQ requires RGB values within 0-10000 nits")
    x = np.power(nits / 10000, _M1)
    return np.power((_C1 + _C2 * x) / (1 + _C3 * x), _M2)


def decode_pq(encoded: np.ndarray, *, reference_white_nits: float) -> np.ndarray:
    """Decode PQ code values into linear RGB relative to reference white."""
    values = np.asarray(encoded, dtype=np.float64)
    if not np.isfinite(reference_white_nits) or reference_white_nits <= 0:
        raise HDRTIFFError("reference_white_nits must be positive and finite")
    if not np.isfinite(values).all() or (values < 0).any() or (values > 1).any():
        raise HDRTIFFError("PQ code values must be finite within [0,1]")
    p = np.power(values, 1 / _M2)
    num = np.maximum(p - _C1, 0)
    den = _C2 - _C3 * p
    return np.power(num / den, 1 / _M1) * (10000 / reference_white_nits)


def write_hdr_tiff(
    output: str | Path,
    rgb_linear: np.ndarray,
    *,
    bit_depth: Literal[16, 32],
    transfer: Literal["pq", "linear"],
    primaries: str = "Display P3",
    reference_white_nits: float | None = None,
    icc_profile: bytes | None = None,
    orientation: int = 1,
) -> Path:
    """Write a numerically testable HDR TIFF, without claiming color-managed playback.

    32/linear supports negative and >1 RGB values. 16/pq requires an explicit
    reference-white scale and only nonnegative values in the PQ domain.
    TIFF ImageDescription documents intent, but is NOT an ICC color profile.
    """
    rgb = _linear_rgb(rgb_linear)
    if (bit_depth, transfer) not in {(32, "linear"), (16, "pq")}:
        raise HDRTIFFError("Only 32/linear and 16/pq combinations are supported")
    if not primaries.strip():
        raise HDRTIFFError("primaries must be specified")
    if bit_depth == 32:
        if reference_white_nits is not None:
            raise HDRTIFFError("reference_white_nits is only used for PQ")
        raster = rgb
    else:
        if reference_white_nits is None:
            raise HDRTIFFError("16-bit PQ requires reference_white_nits")
        encoded = encode_pq(rgb, reference_white_nits=reference_white_nits)
        raster = np.rint(encoded * 65535).astype(np.uint16)
    if icc_profile is not None:
        if len(icc_profile) < 128 or icc_profile[36:40] != b"acsp":
            raise HDRTIFFError("Invalid ICC profile signature")
        if int.from_bytes(icc_profile[:4], "big") != len(icc_profile):
            raise HDRTIFFError("Invalid ICC profile size")
    if orientation not in range(1, 9):
        raise HDRTIFFError("TIFF orientation must be 1..8")
    destination = Path(output)
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    description = json.dumps(
        {
            "luvix": "experimental-hdr-tiff-v1",
            "primaries": primaries,
            "transfer": transfer,
            "reference_white_nits": reference_white_nits,
            "color_management": (
                "embedded ICC (PQ interpretation experimental)"
                if icc_profile and transfer == "pq"
                else "embedded linear source ICC"
                if icc_profile
                else "UNVERIFIED: no ICC profile embedded"
            ),
        },
        sort_keys=True,
    )
    tifffile.imwrite(
        destination,
        raster,
        photometric="rgb",
        metadata=None,
        description=description,
        iccprofile=icc_profile,
        extratags=[(274, "H", 1, orientation, False)],
    )
    try:
        with tifffile.TiffFile(destination) as result:
            page = result.pages[0]
            stored_orientation = page.tags.get(274)
            if stored_orientation is None or int(stored_orientation.value) != orientation:
                raise HDRTIFFError("TIFF orientation read-back verification failed")
            tag = page.tags.get(34675)
            if icc_profile is not None and (tag is None or bytes(tag.value) != icc_profile):
                raise HDRTIFFError("ICC read-back verification failed")
            if icc_profile is None and tag is not None:
                raise HDRTIFFError("Unexpected embedded ICC profile")
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return destination
