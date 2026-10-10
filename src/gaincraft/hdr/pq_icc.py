"""Experimental matrix/TRC ICC representation of PQ in source RGB primaries.

The ICC TRC encodes PQ's inverse transfer, normalized to the 10,000-nit
PQ domain. ICC profiles alone do not specify Photoshop HDR display behavior.
"""

from __future__ import annotations

import struct

import numpy as np

from gaincraft.hdr.tiff import HDRTIFFError


def _u32(data: bytes, offset: int) -> int:
    return struct.unpack_from(">I", data, offset)[0]


def _curve(samples: int = 4096) -> bytes:
    x = np.linspace(0.0, 1.0, samples, dtype=np.float64)
    m1 = 2610 / 16384
    m2 = 2523 / 32
    c1 = 3424 / 4096
    c2 = 2413 / 128
    c3 = 2392 / 128
    p = x ** (1 / m2)
    y = (np.maximum(p - c1, 0) / (c2 - c3 * p)) ** (1 / m1)
    values = np.rint(np.clip(y, 0, 1) * 65535).astype(">u2")
    return b"curv" + b"\0" * 4 + struct.pack(">I", samples) + values.tobytes()


def make_pq_icc(linear_icc: bytes) -> bytes:
    """Replace RGB tone curves of an Apple linear matrix ICC with PQ curves.

    Retains its primaries, adapted white point, and remaining tags. Raises
    for LUT-based/non-matrix profiles rather than misrepresenting primaries.
    """
    data = bytes(linear_icc)
    if len(data) < 132 or data[36:40] != b"acsp" or _u32(data, 0) != len(data):
        raise HDRTIFFError("Invalid source ICC header")
    count = _u32(data, 128)
    if count > 256 or 132 + count * 12 > len(data):
        raise HDRTIFFError("Invalid ICC tag table")
    tags: list[tuple[bytes, bytes]] = []
    names: set[bytes] = set()
    for i in range(count):
        name, offset, length = struct.unpack_from(">4sII", data, 132 + 12 * i)
        if offset + length > len(data) or offset < 128:
            raise HDRTIFFError("Invalid ICC tag offsets")
        names.add(name)
        tags.append((name, data[offset : offset + length]))
    needed = {b"rXYZ", b"gXYZ", b"bXYZ", b"wtpt", b"rTRC", b"gTRC", b"bTRC"}
    if not needed.issubset(names) or data[16:20] != b"RGB ":
        raise HDRTIFFError("PQ ICC requires matrix RGB source profile")
    curve = _curve()
    tags = [(name, curve if name in {b"rTRC", b"gTRC", b"bTRC"} else blob) for name, blob in tags]
    # Preserve shared tag payload offsets, including the three shared TRCs.
    header = bytearray(data[:128])
    header[84:100] = b"\0" * 16  # Invalidate original profile ID.
    table = bytearray(struct.pack(">I", len(tags)))
    body = bytearray()
    locations: dict[bytes, tuple[int, int]] = {}
    start = 128 + 4 + 12 * len(tags)
    for name, blob in tags:
        if blob not in locations:
            offset = start + len(body)
            locations[blob] = (offset, len(blob))
            body.extend(blob)
            body.extend(b"\0" * (-len(body) % 4))
        offset, length = locations[blob]
        table.extend(struct.pack(">4sII", name, offset, length))
    result = header + table + body
    struct.pack_into(">I", result, 0, len(result))
    return bytes(result)
