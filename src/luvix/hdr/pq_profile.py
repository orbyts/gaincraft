"""Validate externally supplied RGB PQ ICC profiles for experimental TIFF export."""

from __future__ import annotations

import struct
from pathlib import Path

from luvix.hdr.tiff import HDRTIFFError

# CICP primaries: 12=P3-D65, 1=BT.709/sRGB, 9=BT.2020.
_EXPECTED_PRIMARIES = {
    "Display P3": 12,
    "sRGB": 1,
}


def load_external_pq_icc(path: Path, source_primaries: str) -> bytes:
    """Read a matching PQ ICC; reject missing/ambiguous color metadata.

    A matching CICP tag does not guarantee that Photoshop will display HDR
    correctly or that a chosen reference-white convention is appropriate.
    """
    data = path.read_bytes()
    if len(data) < 132 or data[36:40] != b"acsp":
        raise HDRTIFFError("Invalid ICC profile signature")
    if struct.unpack_from(">I", data, 0)[0] != len(data):
        raise HDRTIFFError("Invalid ICC profile size")
    if data[16:20] != b"RGB ":
        raise HDRTIFFError("PQ ICC must describe RGB")
    expected = _EXPECTED_PRIMARIES.get(source_primaries)
    if expected is None:
        raise HDRTIFFError(f"Unsupported source primaries for PQ ICC: {source_primaries}")
    count = struct.unpack_from(">I", data, 128)[0]
    if count > 256 or 132 + 12 * count > len(data):
        raise HDRTIFFError("Invalid ICC tag directory")
    cicp = None
    for index in range(count):
        name, offset, size = struct.unpack_from(">4sII", data, 132 + 12 * index)
        if offset < 132 or size > len(data) - offset:
            raise HDRTIFFError("Invalid ICC tag offset")
        if name == b"cicp":
            if size < 12 or data[offset : offset + 4] != b"cicp":
                raise HDRTIFFError("Invalid CICP tag")
            cicp = tuple(data[offset + 8 : offset + 12])
    if cicp is None:
        raise HDRTIFFError("External PQ ICC requires a CICP tag")
    primaries, transfer, matrix, full_range = cicp
    if (primaries, transfer, matrix, full_range) != (expected, 16, 0, 1):
        raise HDRTIFFError(f"PQ ICC CICP mismatch: expected ({expected}, 16, 0, 1), got {cicp}")
    return data
