"""Luvix's bootstrap command-line interface."""

from __future__ import annotations

import json
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.table import Table

from luvix import __version__
from luvix.backends.apple.bridge import BackendError, run_backend
from luvix.doctor import collect_diagnostics

app = typer.Typer(
    name="luvix",
    help="Inspect, extract, rebuild, validate, and convert HDR gain-map images.",
    no_args_is_help=True,
)
console = Console()


def package_version() -> str:
    """Return installed metadata when available, with a source-tree fallback."""
    try:
        return version("luvix")
    except PackageNotFoundError:
        return __version__


def version_callback(value: bool) -> None:
    """Print the package version for Typer's eager option callback."""
    if value:
        typer.echo(f"luvix {package_version()}")
        raise typer.Exit


@app.callback()
def main(
    show_version: Annotated[
        bool,
        typer.Option(
            "--version", callback=version_callback, is_eager=True, help="Show the version."
        ),
    ] = False,
) -> None:
    """Inspect, extract, rebuild, validate, and convert HDR gain-map images."""


def _display_value(value: Any) -> str:
    if value is None:
        return "not available"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


@app.command()
def doctor(
    as_json: Annotated[
        bool,
        typer.Option("--json", help="Emit machine-readable diagnostics."),
    ] = False,
) -> None:
    """Report runtime prerequisites and implemented HDR capabilities."""
    diagnostics = collect_diagnostics(package_version())
    if as_json:
        typer.echo(json.dumps(diagnostics, indent=2, sort_keys=True))
        return

    table = Table(title=f"Luvix {diagnostics['luvix']['version']} doctor")
    table.add_column("Capability")
    table.add_column("Status")
    table.add_row(
        "Python runtime",
        f"{diagnostics['python']['implementation']} {diagnostics['python']['version']}",
    )
    apple = diagnostics["apple_hdr"]
    table.add_row(
        "Apple HDR backend",
        "ready" if apple["runtime_ready"] else "unavailable on this runtime",
    )
    table.add_row("HDR gain-map inspection", "implemented")
    table.add_row("Component extraction", "implemented")
    table.add_row("HEIC reconstruction", "implemented")
    table.add_row("HDR validation", "implemented")
    table.add_row("32-bit linear HDR TIFF", "implemented")
    table.add_row("16-bit PQ HDR TIFF", "implemented")
    table.add_row("16-bit PQ ICC", "external compatible profile required")
    table.add_row("pyvips", _display_value(diagnostics["pyvips"]["version"]))
    table.add_row("libvips", _display_value(diagnostics["libvips"]["version"]))
    table.add_row("uhdrload", _display_value(diagnostics["ultrahdr"]["uhdrload"]))
    table.add_row("uhdrsave", _display_value(diagnostics["ultrahdr"]["uhdrsave"]))
    console.print(table)


def _native(*args: str) -> str:
    try:
        return run_backend(*args)
    except BackendError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc


@app.command()
def inspect(source: Path) -> None:
    """Inspect Apple HEIC HDR base and gain-map layout (macOS)."""
    typer.echo(_native("inspect", str(source)))


@app.command()
def extract(source: Path, output: Annotated[Path, typer.Option("--output", "-o")]) -> None:
    """Extract editable base.png, gainmap.png and manifest.json."""
    typer.echo(_native("extract", str(source), str(output)))


@app.command()
def rebuild(
    source: Annotated[Path, typer.Option("--source")],
    output: Annotated[Path, typer.Option("--output", "-o")],
    base: Annotated[Path | None, typer.Option("--base")] = None,
    gainmap: Annotated[Path | None, typer.Option("--gainmap")] = None,
) -> None:
    """Rebuild Apple HDR HEIC, replacing either or both components."""
    if base is None and gainmap is None:
        typer.echo("Error: specify --base and/or --gainmap", err=True)
        raise typer.Exit(2)
    typer.echo(
        _native(
            "rebuild",
            str(source),
            str(base) if base else "-",
            str(gainmap) if gainmap else "-",
            str(output),
        )
    )


@app.command()
def validate(
    source: Annotated[Path, typer.Option("--source")],
    output: Annotated[Path, typer.Option("--output")],
) -> None:
    """Check core HDR structure against the source (not pixel equivalence)."""
    typer.echo(_native("validate", str(source), str(output)))


@app.command("inspect-hdr")
def inspect_hdr(
    source: Path,
    samples: Annotated[int, typer.Option("--samples", min=1, max=64)] = 16,
) -> None:
    """Probe Apple's HDR-aware decode into extended linear Display P3 (macOS)."""
    from luvix.backends.apple.hdr_probe import run_hdr_probe

    try:
        typer.echo(run_hdr_probe(source, samples))
    except BackendError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc


# M2 experimental TIFF export. Do not claim color-managed Photoshop equivalence.
export_app = typer.Typer(help="Export reconstructed HDR images to high-precision raster formats")
app.add_typer(export_app, name="export")


@export_app.command("tiff")
def export_tiff(
    source: Path,
    output: Annotated[Path, typer.Option("--output", "-o")],
    bit_depth: Annotated[int, typer.Option("--bit-depth")],
    transfer: Annotated[str, typer.Option("--transfer")],
    color_space: Annotated[str, typer.Option("--color-space")] = "source",
    reference_white: Annotated[float | None, typer.Option("--reference-white")] = None,
    icc_profile: Annotated[Path | None, typer.Option("--icc-profile")] = None,
    experimental_untagged: Annotated[
        bool, typer.Option("--experimental-untagged", help="Acknowledge missing PQ/linear ICC")
    ] = False,
) -> None:
    """Export HDR TIFF with source primaries (PQ ICC remains experimental)."""
    from luvix.hdr.export import export_apple_hdr_tiff
    from luvix.hdr.tiff import HDRTIFFError

    if icc_profile is not None and (bit_depth, transfer) != (16, "pq"):
        raise typer.BadParameter("--icc-profile requires --bit-depth 16 --transfer pq")
    if icc_profile is not None and experimental_untagged:
        raise typer.BadParameter("--icc-profile conflicts with --experimental-untagged")
    if color_space != "source":
        raise typer.BadParameter("Only --color-space source is supported")
    try:
        report = export_apple_hdr_tiff(
            source,
            output,
            bit_depth=bit_depth,
            transfer=transfer,
            reference_white_nits=reference_white,
            embed_icc=not experimental_untagged,
            external_pq_icc=icc_profile,
        )
    except (BackendError, HDRTIFFError, OSError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(json.dumps(report, indent=2, sort_keys=True))
