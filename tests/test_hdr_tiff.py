"""Synthetic HDR TIFF round-trip tests, no Apple fixture required."""

import numpy as np
import pytest
import tifffile

from luvix.hdr.tiff import HDRTIFFError, decode_pq, write_hdr_tiff


def test_float32_linear_preserves_hdr_and_negative(tmp_path):
    rgb = np.array([[[0.0, 1.0, 4.5], [-0.01, 0.25, 12.0]]], dtype=np.float32)
    path = write_hdr_tiff(tmp_path / "linear.tif", rgb, bit_depth=32, transfer="linear")
    actual = tifffile.imread(path)
    assert actual.dtype == np.float32
    np.testing.assert_array_equal(actual, rgb)


def test_pq16_roundtrip(tmp_path):
    rgb = np.array([[[0, 0.1, 1], [2, 4, 10]]], dtype=np.float32)
    path = write_hdr_tiff(
        tmp_path / "pq.tif", rgb, bit_depth=16, transfer="pq", reference_white_nits=203
    )
    actual = tifffile.imread(path)
    assert actual.dtype == np.uint16
    restored = decode_pq(actual.astype(np.float64) / 65535, reference_white_nits=203)
    np.testing.assert_allclose(restored, rgb, atol=0.002, rtol=0.001)


@pytest.mark.parametrize("depth,transfer", [(16, "linear"), (32, "pq")])
def test_reject_unsupported_pair(tmp_path, depth, transfer):
    with pytest.raises(HDRTIFFError):
        write_hdr_tiff(tmp_path / "bad.tif", np.ones((1, 1, 3)), bit_depth=depth, transfer=transfer)


def test_pq_rejects_out_of_range(tmp_path):
    with pytest.raises(HDRTIFFError):
        write_hdr_tiff(
            tmp_path / "bad.tif",
            np.array([[[-1, 0, 1]]]),
            bit_depth=16,
            transfer="pq",
            reference_white_nits=203,
        )


def test_refuse_overwrite(tmp_path):
    path = tmp_path / "exists.tif"
    rgb = np.ones((1, 1, 3), dtype=np.float32)
    write_hdr_tiff(path, rgb, bit_depth=32, transfer="linear")
    with pytest.raises(FileExistsError):
        write_hdr_tiff(path, rgb, bit_depth=32, transfer="linear")


def test_no_silent_clipping(tmp_path):
    with pytest.raises(HDRTIFFError):
        write_hdr_tiff(
            tmp_path / "clipped.tif",
            np.full((1, 1, 3), 100),
            bit_depth=16,
            transfer="pq",
            reference_white_nits=203,
        )
