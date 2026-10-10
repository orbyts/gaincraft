"""External PQ ICC contract tests, no private image fixture required."""

import struct

import pytest

from gaincraft.hdr.pq_profile import load_external_pq_icc
from gaincraft.hdr.tiff import HDRTIFFError


def _profile(cicp: tuple[int, int, int, int]) -> bytes:
    header = bytearray(128)
    header[16:20] = b"RGB "
    header[36:40] = b"acsp"
    blob = b"cicp" + b"\0" * 4 + bytes(cicp)
    directory = struct.pack(">I4sII", 1, b"cicp", 144, len(blob))
    result = header + directory + blob
    struct.pack_into(">I", result, 0, len(result))
    return bytes(result)


def test_accept_p3_pq(tmp_path):
    path = tmp_path / "p3.icc"
    data = _profile((12, 16, 0, 1))
    path.write_bytes(data)
    assert load_external_pq_icc(path, "Display P3") == data


def test_reject_mismatched_primaries(tmp_path):
    path = tmp_path / "p3.icc"
    path.write_bytes(_profile((12, 16, 0, 1)))
    with pytest.raises(HDRTIFFError, match="mismatch"):
        load_external_pq_icc(path, "sRGB")


def test_reject_non_pq_transfer(tmp_path):
    path = tmp_path / "p3.icc"
    path.write_bytes(_profile((12, 1, 0, 1)))
    with pytest.raises(HDRTIFFError, match="mismatch"):
        load_external_pq_icc(path, "Display P3")


def test_reject_missing_signature(tmp_path):
    path = tmp_path / "bad.icc"
    path.write_bytes(b"broken")
    with pytest.raises(HDRTIFFError, match="signature"):
        load_external_pq_icc(path, "Display P3")
