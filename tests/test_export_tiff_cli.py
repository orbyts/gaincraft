"""CLI validation and dispatch without requiring macOS or private photographs."""

from pathlib import Path

from typer.testing import CliRunner

from gaincraft.cli import app

runner = CliRunner()


def test_pq_dispatch_without_untagged_flag(monkeypatch):
    monkeypatch.setattr(
        "gaincraft.hdr.export.export_apple_hdr_tiff",
        lambda *args, **kwargs: {"icc_embedded": True},
    )
    result = runner.invoke(
        app,
        [
            "export",
            "tiff",
            "image.heic",
            "--bit-depth",
            "16",
            "--transfer",
            "pq",
            "--reference-white",
            "203",
            "--output",
            "out.tif",
        ],
    )
    assert result.exit_code == 0, result.output


def test_dispatch_32(monkeypatch, tmp_path):
    calls = []

    def fake(source, output, **kwargs):
        calls.append((source, output, kwargs))
        return {"output": str(output), "icc_embedded": False}

    monkeypatch.setattr("gaincraft.hdr.export.export_apple_hdr_tiff", fake)
    result = runner.invoke(
        app,
        [
            "export",
            "tiff",
            "image.heic",
            "--bit-depth",
            "32",
            "--transfer",
            "linear",
            "--output",
            str(tmp_path / "out.tif"),
            "--experimental-untagged",
        ],
    )
    assert result.exit_code == 0, result.output
    assert calls[0][0] == Path("image.heic")
    assert calls[0][2]["bit_depth"] == 32


def test_reject_other_color_space():
    result = runner.invoke(
        app,
        [
            "export",
            "tiff",
            "image.heic",
            "--bit-depth",
            "32",
            "--transfer",
            "linear",
            "--color-space",
            "rec2020",
            "--output",
            "out.tif",
            "--experimental-untagged",
        ],
    )
    assert result.exit_code != 0
