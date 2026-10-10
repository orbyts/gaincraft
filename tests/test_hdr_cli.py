from __future__ import annotations

from typer.testing import CliRunner

from gaincraft.cli import app

runner = CliRunner()


def test_inspect_dispatch(monkeypatch):
    monkeypatch.setattr("gaincraft.cli.run_backend", lambda *args: '{"gain_format":"L008"}')
    result = runner.invoke(app, ["inspect", "test.HEIC"])
    assert result.exit_code == 0
    assert "L008" in result.stdout


def test_extract_dispatch(monkeypatch):
    calls = []
    monkeypatch.setattr("gaincraft.cli.run_backend", lambda *args: calls.append(args) or "ok")
    result = runner.invoke(app, ["extract", "test.HEIC", "--output", "out"])
    assert result.exit_code == 0
    assert calls[0][0] == "extract"


def test_rebuild_requires_edit():
    result = runner.invoke(app, ["rebuild", "--source", "a.HEIC", "--output", "b.HEIC"])
    assert result.exit_code == 2


def test_rebuild_dispatch(monkeypatch):
    calls = []
    monkeypatch.setattr("gaincraft.cli.run_backend", lambda *args: calls.append(args) or "ok")
    result = runner.invoke(
        app, ["rebuild", "--source", "a.HEIC", "--gainmap", "map.png", "--output", "b.HEIC"]
    )
    assert result.exit_code == 0
    assert calls[0][3] == "map.png"


def test_validate_dispatch(monkeypatch):
    monkeypatch.setattr("gaincraft.cli.run_backend", lambda *args: '{"valid":true}')
    result = runner.invoke(app, ["validate", "--source", "a.HEIC", "--output", "b.HEIC"])
    assert result.exit_code == 0
