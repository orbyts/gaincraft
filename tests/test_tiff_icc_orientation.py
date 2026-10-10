"""Regression: an ICC must be present in the actual TIFF, not merely in JSON."""

from pathlib import Path

import numpy as np
import pytest
import tifffile

from luvix.hdr.tiff import HDRTIFFError, write_hdr_tiff


def fake_icc() -> bytes:
    profile = bytearray(128)
    profile[:4] = (128).to_bytes(4, "big")
    profile[36:40] = b"acsp"
    return bytes(profile)


def test_icc_and_orientation_read_back(tmp_path: Path) -> None:
    output = tmp_path / "linear.tif"
    profile = fake_icc()
    rgb = np.full((3, 4, 3), 1.5, dtype=np.float32)
    write_hdr_tiff(
        output,
        rgb,
        bit_depth=32,
        transfer="linear",
        icc_profile=profile,
        orientation=6,
    )
    with tifffile.TiffFile(output) as tif:
        assert bytes(tif.pages[0].tags[34675].value) == profile
        assert int(tif.pages[0].tags[274].value) == 6
        np.testing.assert_array_equal(tif.asarray(), rgb)


def test_invalid_orientation_rejected(tmp_path: Path) -> None:
    with pytest.raises(HDRTIFFError, match="orientation"):
        write_hdr_tiff(
            tmp_path / "bad.tif",
            np.zeros((2, 2, 3), dtype=np.float32),
            bit_depth=32,
            transfer="linear",
            orientation=9,
        )
    assert not (tmp_path / "bad.tif").exists()
