"""Experimental Apple HDR HEIC to color-tagged TIFF export."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Literal

import numpy as np

from gaincraft.backends.apple.hdr_raster import render_hdr_raster
from gaincraft.hdr.tiff import HDRTIFFError, write_hdr_tiff


def export_apple_hdr_tiff(
    source: Path,
    output: Path,
    *,
    bit_depth: Literal[16, 32],
    transfer: Literal["pq", "linear"],
    reference_white_nits: float | None = None,
    negative_tolerance: float = 0.005,
    embed_icc: bool = False,
    external_pq_icc: Path | None = None,
) -> dict[str, object]:
    if (bit_depth, transfer) not in {(16, "pq"), (32, "linear")}:
        raise HDRTIFFError("Only 16/pq or 32/linear supported")
    if external_pq_icc is not None and (bit_depth, transfer) != (16, "pq"):
        raise HDRTIFFError("--icc-profile is supported only for 16-bit PQ")
    if external_pq_icc is not None and not embed_icc:
        raise HDRTIFFError("--icc-profile requires ICC embedding")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    if not source.is_file():
        raise FileNotFoundError(source)
    if bit_depth == 16 and reference_white_nits is None:
        raise HDRTIFFError("PQ requires --reference-white")
    with tempfile.TemporaryDirectory(prefix="gaincraft-hdr-") as temp:
        prefix = Path(temp) / "hdr"
        render_hdr_raster(source, prefix)
        info = json.loads(prefix.with_suffix(".json").read_text())
        if info["color_space"] not in {"extendedLinearDisplayP3", "extendedLinearSRGB"}:
            raise HDRTIFFError("Unsupported linear working color space")
        h, w = info["height"], info["width"]
        rgba = np.memmap(prefix.with_suffix(".rgba32f"), dtype="<f4", mode="r", shape=(h, w, 4))
        rgb = np.array(rgba[:, :, :3], dtype=np.float32, copy=True)
        if not np.isfinite(rgb).all():
            raise HDRTIFFError("Non-finite decoded HDR data")
        min_value = float(rgb.min())
        max_value = float(rgb.max())
        negative_count = int(np.count_nonzero(rgb < 0))
        if bit_depth == 16:
            if min_value < -negative_tolerance:
                raise HDRTIFFError(
                    f"PQ cannot encode negative linear RGB; minimum {min_value:.7g} "
                    f"is below tolerance {-negative_tolerance}. Use 32-bit linear instead."
                )
            # Small negative excursions from color transforms cannot be represented by PQ.
            # Report explicitly; do not modify the source image.
            np.maximum(rgb, 0, out=rgb)
        if external_pq_icc is not None:
            from gaincraft.hdr.pq_profile import load_external_pq_icc

            icc_profile = load_external_pq_icc(external_pq_icc, info["source_primaries"])
        elif embed_icc:
            from gaincraft.backends.apple.icc_profile import source_linear_icc

            icc_profile = source_linear_icc(info["color_space"])
            if bit_depth == 16:
                from gaincraft.hdr.pq_icc import make_pq_icc

                icc_profile = make_pq_icc(icc_profile)
        else:
            icc_profile = None
        write_hdr_tiff(
            output,
            rgb,
            bit_depth=bit_depth,
            transfer=transfer,
            primaries=info["source_primaries"],
            reference_white_nits=reference_white_nits,
            icc_profile=icc_profile,
            orientation=info["orientation"],
        )
        return {
            "output": str(output),
            "width": w,
            "height": h,
            "orientation_raw": info["orientation"],
            "bit_depth": bit_depth,
            "transfer": transfer,
            "reference_white_nits": reference_white_nits,
            "min_linear_rgb": min_value,
            "max_linear_rgb": max_value,
            "negative_channels": negative_count,
            "negative_policy": "clamp to zero within tolerance" if bit_depth == 16 else "preserve",
            "icc_embedded": icc_profile is not None,
            "source_primaries": info["source_primaries"],
            "warning": (
                "Experimental PQ ICC: Photoshop HDR appearance and absolute luminance "
                "interpretation remain unverified"
                if bit_depth == 16 and icc_profile
                else "Photoshop HDR appearance remains unverified"
                if icc_profile
                else "Experimental untagged TIFF: Photoshop HDR appearance is not validated"
            ),
        }
