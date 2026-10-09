"""Gaincraft's bootstrap command-line interface."""

from __future__ import annotations

import json
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.table import Table

from gaincraft import __version__
from gaincraft.backends.apple.bridge import BackendError, run_backend
from gaincraft.doctor import HDR_NOTICE, collect_diagnostics

app = typer.Typer(
    name="gaincraft",
    help="Prepare for validated HDR gain-map workflows. HDR processing begins in 0.0.2.",
    no_args_is_help=True,
)
console = Console()


def package_version() -> str:
    """Return installed metadata when available, with a source-tree fallback."""
    try:
        return version("gaincraft")
    except PackageNotFoundError:
        return __version__


def version_callback(value: bool) -> None:
    """Print the package version for Typer's eager option callback."""
    if value:
        typer.echo(f"gaincraft {package_version()}")
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
    """Gaincraft 0.0.1 is a bootstrap release; HDR processing begins in 0.0.2."""


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
    """Report bootstrap and future HDR runtime capabilities without modifying files."""
    diagnostics = collect_diagnostics(package_version())
    if as_json:
        typer.echo(json.dumps(diagnostics, indent=2, sort_keys=True))
        return

    table = Table(title=f"Gaincraft {diagnostics['gaincraft']['version']} doctor")
    table.add_column("Capability")
    table.add_column("Status")
    table.add_row("Bootstrap CLI", "ready")
    table.add_row(
        "Python",
        f"{diagnostics['python']['implementation']} {diagnostics['python']['version']}",
    )
    table.add_row("pyvips", _display_value(diagnostics["pyvips"]["version"]))
    table.add_row("pyvips importable", _display_value(diagnostics["pyvips"]["importable"]))
    table.add_row("libvips", _display_value(diagnostics["libvips"]["version"]))
    table.add_row("uhdrload", _display_value(diagnostics["ultrahdr"]["uhdrload"]))
    table.add_row("uhdrsave", _display_value(diagnostics["ultrahdr"]["uhdrsave"]))
    table.add_row(
        "libultrahdr discoverable",
        _display_value(diagnostics["ultrahdr"]["library_discoverable"]),
    )
    table.add_row("Cloudinary SDK", _display_value(diagnostics["cloudinary"]["sdk_version"]))
    table.add_row(
        "Cloudinary credentials configured",
        _display_value(diagnostics["cloudinary"]["credentials_configured"]),
    )
    table.add_row("HDR processing", "not implemented")
    console.print(table)
    console.print(HDR_NOTICE)


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
