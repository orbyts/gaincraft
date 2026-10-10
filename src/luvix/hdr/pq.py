"""SMPTE ST 2084 (PQ) reference transfer functions.

These operate on absolute luminance in cd/m², not gain-map code values.
They do not implement Apple's HDR gain-map reconstruction.
"""

from __future__ import annotations

import math

M1 = 2610 / 16384
M2 = 2523 / 32
C1 = 3424 / 4096
C2 = 2413 / 128
C3 = 2392 / 128
MAX_NITS = 10000.0


def _finite_in_range(value: float, low: float, high: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"{name} must be finite and within [{low}, {high}]")
    return value


def pq_encode(nits: float) -> float:
    """Encode absolute luminance (0..10000 nits) to normalized PQ code (0..1)."""
    luminance = _finite_in_range(nits, 0.0, MAX_NITS, "nits") / MAX_NITS
    power = luminance**M1
    return ((C1 + C2 * power) / (1 + C3 * power)) ** M2


def pq_decode(code: float) -> float:
    """Decode normalized PQ code (0..1) into absolute luminance in nits."""
    code = _finite_in_range(code, 0.0, 1.0, "code")
    power = code ** (1 / M2)
    numerator = max(power - C1, 0.0)
    denominator = C2 - C3 * power
    return MAX_NITS * (numerator / denominator) ** (1 / M1)
