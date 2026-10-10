"""Synthetic TIFF ICC tests; native ICC extraction is macOS-only."""

import numpy as np
import pytest
import tifffile

from gaincraft.hdr.tiff import HDRTIFFError, write_hdr_tiff


def fake_icc() -> bytes:
    data = bytearray(128)
    data[:4] = (128).to_bytes(4, "big")
    data[36:40] = b"acsp"
    return bytes(data)


def test_float_tiff_embeds_icc_without_changing_pixels(tmp_path):
    pixels = np.array([[[0.2, 1.3, -0.001], [2.0, 0.5, 0.1]]], dtype=np.float32)
    path = tmp_path / "linear.tif"
    write_hdr_tiff(path, pixels, bit_depth=32, transfer="linear", icc_profile=fake_icc())
    with tifffile.TiffFile(path) as tif:
        assert bytes(tif.pages[0].tags[34675].value) == fake_icc()
        np.testing.assert_array_equal(tif.asarray(), pixels)


def test_reject_invalid_icc(tmp_path):
    with pytest.raises(HDRTIFFError, match="ICC"):
        write_hdr_tiff(
            tmp_path / "invalid.tif",
            np.ones((1, 1, 3), dtype=np.float32),
            bit_depth=32,
            transfer="linear",
            icc_profile=b"invalid",
        )


def test_reject_invalid_pq_icc(tmp_path):
    with pytest.raises(HDRTIFFError, match="ICC"):
        write_hdr_tiff(
            tmp_path / "invalid.tif",
            np.ones((1, 1, 3), dtype=np.float32),
            bit_depth=16,
            transfer="pq",
            reference_white_nits=203,
            icc_profile=b"invalid",
        )
