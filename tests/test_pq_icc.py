"""Synthetic matrix ICC tests for PQ curve generation and TIFF embedding."""

import struct

import numpy as np
import pytest
import tifffile

from luvix.hdr.pq_icc import make_pq_icc
from luvix.hdr.tiff import HDRTIFFError, write_hdr_tiff


def matrix_icc() -> bytes:
    names = [b"rXYZ", b"gXYZ", b"bXYZ", b"wtpt", b"rTRC", b"gTRC", b"bTRC"]
    payload = b"XYZ " + b"\0" * 16
    trc = b"curv" + b"\0" * 4 + struct.pack(">I", 1) + b"\xff\xff" + b"\0\0"
    entries = [(name, trc if name.endswith(b"TRC") else payload) for name in names]
    header = bytearray(128)
    header[16:20] = b"RGB "
    header[36:40] = b"acsp"
    table = struct.pack(">I", len(entries))
    body = bytearray()
    for name, value in entries:
        offset = 132 + 12 * len(entries) + len(body)
        table += struct.pack(">4sII", name, offset, len(value))
        body.extend(value)
    profile = header + table + body
    struct.pack_into(">I", profile, 0, len(profile))
    return bytes(profile)


def test_pq_icc_preserves_colorants_and_adds_curve():
    source = matrix_icc()
    result = make_pq_icc(source)
    assert result[36:40] == b"acsp"
    assert struct.unpack_from(">I", result, 0)[0] == len(result)
    tags = {}
    for i in range(struct.unpack_from(">I", result, 128)[0]):
        name, offset, length = struct.unpack_from(">4sII", result, 132 + i * 12)
        tags[name] = result[offset : offset + length]
    assert tags[b"rXYZ"] == b"XYZ " + b"\0" * 16
    assert tags[b"rTRC"] == tags[b"gTRC"] == tags[b"bTRC"]
    assert struct.unpack_from(">I", tags[b"rTRC"], 8)[0] == 4096


def test_pq_tiff_contains_icc_and_orientation(tmp_path):
    icc = make_pq_icc(matrix_icc())
    rgb = np.array([[[0.0, 0.5, 3.0]]], dtype=np.float32)
    path = write_hdr_tiff(
        tmp_path / "pq.tif",
        rgb,
        bit_depth=16,
        transfer="pq",
        reference_white_nits=203,
        icc_profile=icc,
        orientation=6,
    )
    with tifffile.TiffFile(path) as tiff:
        assert bytes(tiff.pages[0].tags[34675].value) == icc
        assert int(tiff.pages[0].tags[274].value) == 6


def test_reject_invalid_icc():
    with pytest.raises(HDRTIFFError):
        make_pq_icc(b"invalid")
