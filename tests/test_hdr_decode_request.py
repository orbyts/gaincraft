"""Guard the ImageIO decode request contract against regression."""

from pathlib import Path


def test_explicit_imageio_decode_request_key() -> None:
    swift = (
        Path(__file__).resolve().parents[1] / "src/gaincraft/backends/apple/hdr_probe.swift"
    ).read_text()
    assert "[kCGImageSourceDecodeRequest: decodeMode]" in swift
    assert "hdr ? kCGImageSourceDecodeToHDR : kCGImageSourceDecodeToSDR" in swift
    assert "[kCGImageSourceDecodeToHDR: hdr]" not in swift
